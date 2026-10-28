**This log is for my personal reference but I placed it here because it will show the actual process of completing the project (even though it's messier than the README)

## *Last Update: 2026-10-28*

### DONE

- Increased `track_buffer` from 30 (default) to 60 and ran the tracker on a moderate traffic clip, recorded findings.
- Decided to keep `track_buffer=60` as the working setting. No visible downside observed while providing imrovements in track maintenance
- Created `bytetrack_w_buffer60.yaml` config variant. Other than `track_buffer=60`, all parameters use default values
- Built `track_vehicles()` function in `src/tracking.py` (`tracking.py` renamed to `detection.py`). An interface for the counting logic to use
- Dropped `detection-notes.md` as redundant (observations are already recorded in the experiment notebooks)

### STILL BROKEN

- Congested lane cascading ID transfers persist at `track_buffer=60`. 
- The cascade is an IoU matching problem between active tracks, not a buffer timing issue. Could still be improved with ReID

### LEARNINGS

- Confirmed `track_buffer=60` helps with brief occlusions (track stays alive to reclaim its detection) but does not fix the congestion cascade
- An evidence of this is the 5% drop of unique IDs (from 348 to 331). Fewer tracks were lost and more vehicles kept their IDs through occlusion.
- Confirmed ghost tracks are not a concern for clips with overhead camera angles since vehicles enter and exit on separate lanes
- Most ID issues occur between live, overlapping tracks. The exception is track fragmentation, which is exactly what the longer buffer can help prevent
- We only tested `track_buffer=60` on an overhead angle with moderate-to-heavy traffic but roadside views with frequent occlusions should benefit as well.
- The default NMS IoU threshold of 0.7 should mean it is rare for NMS to suppress a vehicle's box during occlusion.
- For most cases, NMS will only suppress duplicate, different-class boxes on the same vehicle, instead of separate vehicles occluding each other.
- And if the occluded vehicle’s box does survive, it likely survives NMS too. 

### FOR THE NEXT SESSION

- Place counting line in the reliable detection zone and implement crossing logic
- Define the event schema and begin writing crossing events


## *Last Update: 2026-10-21*

### DONE

- Ran detector on full dev clips with class filter (vehicles only except bicycles) and `agnostic_nms=True`, produced annotated output videos
- Recorded processing speed on a single T4 GPU
- Completed experiment found in `detection-running-video-analysis` notebook 
- Documented detection instabilities (detection dropout, class oscillation, merged detections, duplicate different-class boxes, far zone issues)
- Decided to stick with COCO pretrained weights (no fine-tuning needed and detection quality is sufficient) for now. May tune the model later if needed 
- Decided to implement ByteTrack for tracking (via ultralytics built-in and no ReID). Not final as we might switch to an algorithm with ReID
- Documented ByteTrack default configs: `track_high_thresh: 0.25`, `track_low_thresh: 0.1`, `new_track_thresh: 0.25`, `track_buffer: 30`, `match_thresh: 0.8`
- Ran tracking on `dev_overhead_medium_congest_01.mp4` with `agnostic_nms=True` (Tracking experiment 1)
- Identified and documented ID transfers, cascading transfer effects, and detection merge + ID inheritance in congested lane
- Ran experiment 2: `agnostic_nms=True` vs `False` comparison. Unique IDs jumped from 348 to 470 (+35%) with it off.   
- Congested lane behavior identical whether agnostic NMS is enabled or not. Confirmed that `agnostic_nms=True` is the correct setting
- Ran Experiment 3: Confirmed track IDs are stable in the reliable detection zone for both incoming and outgoing lanes
- Built tracking instabilities reference table (for ID transfer, track fragmentation, ghost track, premature termination, cascading ID transfers)
- Updated `SPEC.md`: refined "Scene" conditions, "Known Limitations" with details specific to the tracker
- Set up output video hosting (unlisted YouTube links for notebooks) and added Drive link in README for dev clips

### STILL BROKEN (FIX IN PROGRESS)

- Congested lane cascading ID transfers remain a known tracker limitation because IoU-based matching cannot reliably distinguish tightly packed vehicles. 
- Not fixable by tuning detection as it is a tracker-side problem. Could be improved with a change in tracker that employs ReID

### LEARNINGS

- `new_track_thresh: 0.25` matches `conf=0.25`, so that every detection surviving the confidence score filter is immediately assigned a track ID
- `track_high_thresh: 0.25`, intentionally lower that the paper's τ=0.6 can effectively reduce the two-pass design to a single pass
- The reliable detection zone (close to the camera forward mid-frame) produces stable tracking. 
- This reinforces the reliable zone as the ideal region for positioning the counting line since it is where detection and tracking are most trustworthy.
- ID transfers are one-directional (vehicle A’s ID is transferred to B). True ID swaps (A and B exchange IDs) were not observed
- Cascading ID transfers happen when one bad IoU match propagates through the Hungarian algorithm, which conducts global assignments. Each wrong pairing can distort the rest
- Setting `agnostic_nms=False` provided no meaningful improvement in maintaining tracks through congestion and in general
- Detection quality remains reliable. As mentioned, performance decline in congestion is a tracker-side problem.
- Outgoing vehicles entering the view often start with oversized bounding boxes that are corrected just after a few frames

### FOR THE NEXT SESSION

- Run tracking on all dev clips and compare behavior across different traffic densities
- Determine and implement crossing logic then place the counting line


## *Last Update: 2026-10-11*

### DONE

- Cut 4 dev clips (two more than the initial planned): 2 overhead-heavy, 1 overhead-medium w/ congestion, 1 roadside-heavy w/ congestion
- Set up Kaggle notebook (T4 GPU) with ultralytics for detection work
- Chose YOLOv8m as working model. T4 has 16GB VRAM, medium is the accuracy-speed sweet spot
- Ran detector on sampled frames across all 4 dev clips, observations recorded in `detection-per-frame-analysis` notebook
- Tested confidence thresholds at 0.1, 0.25, 0.5, 0.8 — settled on 0.25 as starting threshold (revisit after tracker)
- Note: no hallucinations observed at 0.25 across all dev clips
- Identified different-class duplicate box pattern (truck/car, bus/truck overlaps on same vehicle)
- Decided which COCO class IDs to keep [car(2), truck(7), bus(5), motorcycle(3)]. Filtering the next round of detections

### STILL BROKEN (FIX IN PROGRESS)
- None for now

### LEARNINGS
- Detection quality degrades with distance consistently across all dev clips
- The reliable zone (detection zone boundary) is roughly mid-road forward
- Misclassifications cluster at greater depth where vehicles are smaller and less distinct
- False positive = box on a non-vehicle (relative to our task).
- Misclassification = real vehicle, wrong label.
- Hallucination = box on literally nothing
- NMS is per-class by default. Overlapping boxes of different classes both survive, risking double-counts at the tracker. agnostic_nms=True should resolve this
- COCO has no "van" class. Vans get labeled car or truck depending on angle
- Confidence threshold and class filtering solve different problems. 
- Threshold removes hallucinations, filtering removes correctly-detected non-vehicles

### FOR THE NEXT SESSION
- Apply vehicle class filter (car, truck, bus, motorcycle)
- Run detector on full dev clip, produce output video with bounding boxes
- Record processing speed (FPS on T4)
- Make decision whether to fine-tune YOLOv8m on our own dataset or stick with the COCO pretrained weights as-is.


## *Last Update: 2026-09-09*

### DONE
- Wrote SPEC.md detailing the planned output schema, accuracy targets, operating conditions, out-of-scope items, and what a "finished project" means
- Set up repo structure with config, src, data, notebooks, outputs, tests
- .gitignore in place before first commit covering video files, model weights, db, venv
- Created venv on Python 3.12
- Defined what light, medium, heavy traffic conditions are for reporting accuracy under these conditions (see SPEC.md) 
- Installed ffmpeg binary and added to PATH
- Installed yt-dlp and downloaded a full traffic footage camera playlist
- Reviewed all traffic footage videos to extract ~4 minute clips to be used in evaluation
- Quick hand-count on each 4-minute timestamp intervals just to gauge traffic density and label the eval clips (light, medium, or heavy traffic)
- Settled with 4 clips in total. 3 overhead camera angle (low, medium, and heavy traffic) and 1 roadside angle (low or medium traffic)

### STILL BROKEN (FIX IN PROGRESS)
- Nothing for now

### LEARNINGS
- Event-based counting (one row per crossing) dictates the whole design (database, API, dashboard, and counting logic). 
- The configurable dead zone/hysteresis will prevent phantom counts caused by jittering detection boxes
- ID swaps (when two objects get too close to each other) are harmless for totals but they corrupt per-direction accuracy
- Ground truth for this project is hand-counting. No complex annotations required (e.g., bbox annotating)
- If we pick a clip with roadside camera angle + heavy traffic condition, it will be difficult to tell which condition (angle or traffic volume) caused an accuracy drop.
- Eval clips must be separate from dev clips (same leakage principle as with typical train/test split)
- With camera perspective, a single horizontal line provides different effective depth for each direction. 
- With two lines, we can place each at an optimal location for each direction (incoming and outgoing have two separate lines).

### FOR THE NEXT SESSION
- Find a low-traffic segment and a congestion segment for dev clips
- Film own footage if time and location allow