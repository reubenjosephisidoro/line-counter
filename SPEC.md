# SPEC - Vehicle Counting System

"Submitted for your approval: a 1997 Corolla, ID 3, last seen at y=397. It will cross no line.   
It will register no event. It has entered... the Twilight Zone."

*Last updated: 2026-09-07*

This document details the high-level scope of this project. It aims to identify what  
the delivarible is, what it is not, foundational parameters, architectural constraints,   
and a concrete and realistic finish line. Establishing these early keeps the project away   
from scope creep and guides database and tracking decisions. It will also define acceptable   
accuracy thresholds before development begins.  


## 1. Output

**Given:**
- A recorded video file from a fixed camera
- A user-defined line specified in config

The system produces one event per vehicle that crosses the line.

### 1.1 Event schema

Each event records:

| Field | Type | Description |
|---|---|---|
| `event_id` | int | Primary key |
| `source_video` | text | Filename or identifier of the clip |
| `line_id` | text | Which configured line was crossed |
| `vehicle_id` | int | Tracker-assigned identity (unique within a clip only) |
| `frame_number` | int | The exact frame in which the crossing was detected |
| `timestamp` | float | Seconds relative to the start of the video |
| `direction` | text | `A --> B` or `B --> A` |
| `class` | text | car, truck, bus, or motorcycle |

Events are written to a single database table. This table is shared across all processed video clips     
and will be the system's single source of truth. It writes each crossing (event) to the database   
as it happens, and when you ask for a total, it counts the rows. Every reported figure is a query    
over stored events.  

All reporting is derived from the table:  

- **Per-direction totals:** Event counts grouped by `direction`, scoped to  
  a `source_video` and `line_id`.z

- **Counts aggregated per unit time:** Events grouped into fixed time buckets   
(60 seconds by default but configurable). It produces a count per time interval   
for each direction to give a flow-over-time series, giving us a clear view of   
how traffic volume varies across the clip. For example:    

  | Bucket | A --> B | B --> A |
  |---|---|---|
  | 0:00–1:00 | 12 | 17 |
  | 1:00-2:00 | 15 | 14 |
  | 2:00-3:00 | 27 | 30 |

- **Class breakdown:** Event counts grouped by `class`. Reported as a  
secondary metric only (see accuracy scope). Class labels are reported    
but are not part of the headline accuracy claim.  

Reprocessing a clip replaces that clip's existing events in the database   
rather than adding to them, so re-running the pipeline after a config     
change does not inflate counts.

## 2. Accuracy Target

Accuracy is measured using manually-counted ground truth on a held-out   
evaluation dataset (a separate held out segment of video clips).   
Three metrics are reported per clip:  

| Metric | Definition | Target |
|---|---|---|
| Net count error | \|system total − true total\| ÷ true total | ≤ 5% |
| Direction accuracy | Events with correct direction ÷ true total | ≥ 95% |
| Gross error rate | (misses (FNs) + phantom counts (FPs)) ÷ true total | ≤ 10% |

- **Why three.** Looking at net count error alone could mislead. For example,      
a clip where the system misses five vehicles but phantom counts another   
five vehicles scores a perfect 0% while hiding the mistakes it made.  
Gross error rate catches that by counting individual mistakes (misses + phantom counts).   
Direction accuracy is tracked separately because ID swaps (when objects get too close)   
change ID directions without affecting totals.  

- **Class breakdown is not taken into account in accuracy claims.** Class labels are    
reported but not scored. Class confusion (e.g., car/truck confusion) is expected and   
correcting it is not a project goal.  

- **Reporting.** These metrics are reported for each clip, not averaged into a  
single headline number. Accuracy can vary substantially with traffic density,  
angle of the camera setup, and occlusion, and a single average would hide this.  
The targets shown above is expected to be met on clear, moderate-density daytime  
footage. Degradation on harder clips is documented and shown (not hidden). 

- **Revision note.** These targets were set before any implementation and    
are provisional. If they prove unachievable, they will be revised with a  
recorded reason.

### 2.1 Evaluation Clip Standards

All evaluation clips are approximately 4 minutes long with (+25, -25) second wiggle room.  
The clips are trimmed from traffic footages that are longer in duration using ffmpeg with     
no re-encoding (no quality change). A minimum of 4 evaluation clips are required, covering   
at least two different camera angles and two different traffic conditions. These clips are   
completely separate from development clips that will be used for tuning.  

Traffic density is measured over the full clip duration: 

- (total vehicles counted) / (duration in minutes, ~4) / number of lanes at the counting line.

This gives a vehicles-per-minute/lane figure comparable across all eval clips.

| Label  | Vehicles per lane per minute | Description                        |
|--------|-----------------------------|------------------------------------|
| Light  | 1–6                        | Clear gaps between vehicles        |
| Medium | 7–16                       | Steady flow, gaps under ~2 seconds |
| Heavy  | 17+                        | Near-continuous flow, minimal gaps  |

Note that these "Light, Medium, Heavy" labels are only for organizing evaluation clips and   
are based on observation, not from any formal traffic engineering classifications.   
They are defined so that we can report accuracy per condition rather than as a single average.  

If traffic density varies noticeably within a clip (e.g., light for 3 mins then heavy for one),    
the clip is labeled by its average but a note will be included describing the variation.

## 3. What is Out of Scope

The following are deliberately excluded from v1. Items marked *(later)* are  
candidate extensions that we will consider once the core system meets the set   
accuracy target. Other than these, the rest is out of scope for this project.  

**Input**
- Live camera or stream ingestion (batch processing of recorded files for now) *(later)*
- Multiple simultaneous cameras
- Moving or handheld cameras (system assumes fixed viewpoint)
- Night footage, rain, fog, or low-visibility conditions (not testing under these conditions)

**Analysis**
- Speed or distance estimation (this requires camera calibration)
- Vehicle re-identification across cameras or across clips
- License plate detection or recognition (can result in a privacy liability)
- Trajectory or turning-movement analysis at intersections
- Automatic line placement (lines are configured by hand for now) *(later)*

**Interface and deployment**
- User authentication, multi-user support, or access control
- Cloud or public deployment (runs locally via Docker Compose for now) *(later)*
- Mobile app or responsive design (dashboard is desktop-only)
- Interactive line drawing in a UI. Config file only *(later)*

**Software engineering**
- Horizontal scaling, queuing, or distributed processing
- CI/CD pipelines
- Model training from scratch (pretrained detectors with optional fine-tuning only)

**Rationale.** This is a solo build. Every item above is either a separate project or   
a source of complexity that does not improve the core aim, which is accurate, verifiable   
vehicle counts from recorded footage.

## 4. Explicit Operating Conditions

The system is designed and evaluated for the specific conditions stated below.   
Performance outside these conditions is currently untested. However, it does not   
entail that these conditions are entirely unsupported or will not be in the future.  

**Camera**
- Fixed and stationary for the entire duration of the clip. No panning, tilting, 
zooming, or handheld footage
- Elevated viewpoint (overbridge, pole, upper-floor window) looking down
  at the roadway, not at the road level
- Vehicles visible for at least ~1 second before and after the counting
  line, so the tracker can establish a side on both ends

**Footage**
- Recorded video files in common formats that are readable by OpenCV
- Daylight conditions that can be clear to overcast skies
- Resolution 720p minimum 
- Frame rate at minimum 15 fps
- Clip length from around 1 minute to several hours

**Scene**
- Vehicles are the objects of interest
- Pedestrians and cyclists are filtered out by class
- Traffic is light to moderate in density where vehicles are generally
  distinguishable rather than mostly overlapping
- No persistent obstruction (e.g., poles, signs, overpass) crossing the counting
  line

**Hardware**
- Runs on CPU but a CUDA-capable GPU is optional and improves throughput
- *[Actual machine specs placed here later]*
- *[Throughput figures reported later are relative to this hardware specs]*

**Known degradation.** Accuracy is expected to decline as: 
- Traffic density rises
- The camera angle flattens toward road level 
- As vehicles become smaller in frame. 

These are documented per clip rather than averaged away in one metric.

## 5. Definition of Done

We point the system at a config file and a 10-minute traffic clip. The system then  
processes the video from start to finish via a single command. Events are accumulated  
in memory as the clip is processed, then written in the database at the end as a single   
transaction. Upon opening the dashboard, we see info such as per-direction totals     
and a counts-per-minute chart for that clip. We can switch the dashboard to a second clip   
which is an entirely different road (and camera angle). This second clip has a different   
config but uses the same system (no code changes) displaying similar results and metrics.   
Alongside each clip's dashboard view, the annotated output video plays with boxes, IDs,   
the crossing line, and a running tally, so anyone watching can verify the count by eye.

The whole thing runs from `docker compose up` on a clean machine.

The project is complete when we can perform this in under five minutes for  
someone who has never seen it, and state a measured accuracy figure for  
each clip against hand-counted ground truth.