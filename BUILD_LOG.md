**This log is for my personal reference but I placed it here because it will show the actual process of completing the project (even though it's messier than the README)


## *Last Update: 2026-11-28*

### DONE

- Planned the evaluation. 
  - Each eval clip gets its own study clip (footage from the same recording but outside the eval clip) for setting ideal lines, zones and `hys_n`. 
  - Each eval clip will then be run once. There will be no changes in the settings after the results are seen (this is for the next session)
- Cut study clips for all four eval clips: 
  - `study_eval_overhead_heavy_01` 
  - `study_eval_overhead_medium_01`
  - `study_eval_roadside_medium_01` (only 1:15 long, because the source recording is short) 
  - `study_eval_roadside_medium_02` (60 fps)
- Added `generate_detections` to make a tracked detection video of a study clip and save its detections for replays. 
  - Each annotated study clip output is used to find suitable counting lines, zones, and hysteresis M and N (`hys_n`) for the eval clip
  - This is similar to an operator first looking at past footage and drawing detections on objects prior to defining settings for that camera
  - `track_vehicles` now also returns the raw results for drawing (within `generate_detections`)
- Updated `draw_annotations`
  - Detections whose anchor points fall outside every counting zone are drawn as thin gray boxes with no label
  - The count overlay now has a background the fits the text
  - Note that the text and background styles, sizes, colors, or any overlay interface elements are not final and will change in the final interface
- Made `cooldown` and `track_buffer` follow each clip's frame rate
  - `cooldown = round(1.2 × fps)` and `track_buffer = round(2.4 × fps)`, so both cover the same time on every clip
  - `cooldown` is always 1.2 seconds while `track_buffer` is 2.4 seconds whether the clip runs at 25, 30 or 60 fps
  - One tracker config file per frame rate (25, 30 and 60 fps), since Ultralytics `model.track()` only reads tracker settings from a file
  - Dev clips are all 25 fps, so their settings and results are unchanged
- Replaced the per-line `directions` config in the YAML config file with a `DIR_LABELS` constant in the code
  - This is because labels are the same for every line. A positive crossing is always "B --> A" and negative "A --> B"
- Set up all four study clips (these are setup numbers, NOT EVAL RESULTS):
  - `study_eval_overhead_heavy_01`: moving the outgoing line further from the camera recovered 5 hidden cars and removed 2 split detections. GER 0.2%
  - `study_eval_overhead_medium_01`: GER 0.7%
  - `study_eval_roadside_medium_01`: incoming 18 of 18, outgoing 6 of 7 
    - Moving the outgoing line to catch that one vehicle would mean fitting it to one car rather than the road. 
    - We keep the line where most vehicles show a steady box
  - `study_eval_roadside_medium_02`: GER 4.1% (still below 10%)
- Wrote `counting_lines_eval.yaml` with the lines, zones and `hys_n=1` for all four eval clips (triggering this repo update)
  - Committed before running any eval clip, so the history shows every setting was fixed before system performance was measured on the eval clips
  - This means no setting can be changed after seeing eval results. This avoids leaking eval information, which can be used to improve the settings
  - All settings and final placements were set from the study clips

### STILL BROKEN

- Trucks with trailers are still split into two or more boxes. All 4 phantoms on `study_eval_roadside_medium_02` were split detections
- Vehicles hidden behind other vehicles are still missed. This is more frequent on the roadside clips
- Motorcycles are still missed by the detector
- On `study_eval_roadside_medium_02`, a few large trucks close to the camera have boxes whose anchor points falls outside the incoming zone. 
  - It did not affect counting quality (these vehicles did not cause misses or phantom counts)
  - We have to accept this because the zone cannot be extended further past the road's median barrier
- The outgoing setup for `eval_roadside_medium_01` study clip relied only on 7 vehicles (1 of which is missed due to dropout)
- `src` still lags behind the notebooks

### LEARNINGS

- An eval clip only measures the system fairly if nothing was tuned on it. Watching the road to place lines is fine, but placing them around the system's errors, or around the detector's output on the scored frames, is tuning
- Study clips play the role of the past footage a real operator would watch before setting up a new camera
- Split detections happen mostly close to the camera. Moving a line further away removed them on one clip, but on another they started too far out for that to help
- Settings counted in frames last less time at higher frame rates: at 60 fps, `cooldown=30` lasts 0.5 s and `track_buffer=60` lasts 1 s. Vehicles move less between frames, but an occlusion uses up the buffer more than twice as fast
- Ultralytics only reads tracker settings from a YAML file, not from a dict
- A counting line measures the traffic at its location. A merge lane that joins further down the road is left out of the counting zone and the hand count
- Line-crossing counting tolerates ID switches: a vehicle can change IDs many times, as long as exactly one ID crosses the line
- An object in front of the traffic, like a pole, can hide vehicles. One behind the traffic can't
- Saved detections belong to one specific video and are tracked with whatever tracker settings were used when they were made. A wrong video path made the boxes misalign with the frames
- YAML has no tuples: points written with parentheses load as strings. `cv2.line` needs whole-number coordinates
- A 2025 paper on nonlinear count lines ([Machine Vision and Applications](https://link.springer.com/article/10.1007/s00138-025-01668-x)) places count lines automatically from past tracks to avoid occlusion. A reference for automatic line placement later

### FOR THE NEXT SESSION

- Double-check the eval lines and zones, then commit `counting_lines_eval.yaml` before running any eval clip
- Decide whether the targets apply per clip or per line, and update `SPEC.md` (also the eval clip list if it no longer matches: currently 2 overhead and 2 roadside)
- Run each eval clip once: hand count, label events, score, and record each error's cause
- Bring `src` in line with the notebooks (`hys_n` from config, `DIR_LABELS`, frame-rate scaling, tracker files, `flip_class`, `get_span`, `get_scores`)
- Settle the loose ends from earlier: the eval clip 3 timestamp mismatch, eval clip 4's camera-angle label, and the missing lane counts


## *Last Update: 2026-11-20*

### DONE

- Started the `counting-tuning-dev-clips` notebook for the remaining three dev clips
- Renamed `hyst_n` to `hys_n`
- Updated `process_clip` to either run model inference (and pickle the detections) or simply replay saved detections without the model. 
- Separated the annotation writing mechanism from `process_clip` into its own function `draw_annotations`
- Updated `draw_annotations` to also show each detection's confidence score in addition to track ID, class ID, and sign
- `event` class is now taken at the crossing frame (`flip_class` in `tentative_crossed`), not at the frame where `hys_n` is reached. 
  - Before this, a car/truck flicker could change the recorded class depending on `hys_n` (hysteresis N)
- Rewrote `get_span` to count sightings only for tracks that went through a fresh crossing first (was seen on the other side of the line first) 
- Added `get_scores` for displaying per-line and total net count error, gross error rate, phantom counts, and misses
- Renamed the config key `coords` to `line` and added `counting_zone` for each line
- Decided to drop direction accuracy as a metric. Only net count error and gross error rate remain
- Tuned all four dev clips. All meet the targets (net count error ≤ 5%, gross error rate ≤ 10%) for each line and each clip
  - `dev_overhead_heavy_01`: incoming `hys_n=11`, outgoing `hys_n=1`. GER 6.0%
  - `dev_overhead_heavy_02`: `hys_n=1` on both lines. NCE and GER 1.0%, the best clip so far
  - `dev_roadside_heavy_congest_01`: moved the incoming line closer to the camera, `hys_n=1` on both lines. GER 5.1%
- Compared runs by merging (outer join) their `event` lists instead of manually recounting the video by hand
- Added the `scratchpad.ipynb` notebook to gitignore

### STILL BROKEN

- Many vehicles with trailers are still detected as two or three boxes (split detection). This is the main source of phantom counts (detector-related issue)
- Vehicles hidden behind large trucks are missed entirely, especially in the far lanes of the roadside clip. Also saw one case of merged detection causing a miss
- Motorcycles are still missed by the detector. Higher `imgsz` and a low-confidence check have not been tried yet (to know if they are being detected at all) 
- `dev_overhead_heavy_01` incoming `hys_n=11` has no margin. The two fastest real cars were seen exactly 11 times after crossing
  - The actual M is 4, not 12. We did this deliberately to remove 7 phantom counts at the expense of 3 real crossings (improving gross error rate).
- Moving the roadside incoming line brought its NCE to 0%, but only because 3 phantoms cancel out 3 misses. GER did not improve

### LEARNINGS

- net count error can hide errors that cancel out. gross error rate adds up every phantom and every miss, so it is the more reliable number, especially for clip totals
- When the system total equals the true total, either the system counted perfectly or misses and phantoms are equal, cancelling out
- Direction accuracy turned out to be redundant. 
  - The cross-product already provides a real crossing with its actual direction and side, so wrong-direction events are always phantoms, which GER already counts
- A crossing is counted when its sightings on the new side reach `hys_n`, and the crossing frame counts as the first sighting
- M has to come from real crossings only, including vehicles whose ID was lost right after crossing (`span` cannot spot this and hysteresis ignores gaps anyway)
- Raising `hys_n` can reduce phantom counts but add misses. 
  - It only lowers GER if it removes more phantoms than real crossings, so the low-`count` crossings have to be checked in the video first if they are real or not
- Moving a counting line changes the true total.
  - A vehicle that is already past the old line when the clip starts can now cross the new line
  - OR a vehicle that reaches the old line cannot reach the new one before the clip ends
  - In both cases, vehicels are counted at one line position but not the other
- `CAP_PROP_FRAME_COUNT` comes from the file's metadata, which is not always the same as actual. 
  - One one clip (ffmpeg cut without re-encoding), `CAP_PROP_FRAME_COUNT` reported 2892 frames but only 2880 could be read
- Detector settings (model, input size, confidence threshold, and tracker algorithm) apply to the whole system. 
  - Only line coordinates, counting zone coordinates, `hys_n` and `cooldown` are set per clip
- Our targets hold up against published ones. 
  - For instance, a 5% NCE target matches the [Virginia DOT acceptance framework](https://vtrc.virginia.gov/reports/all-reports/26-r53/)
  - In addition, GER is stricter than the WAPE metric agencies use
    - WAPE adds up the error of each time interval (for example, every 15 minutes), so a phantom and a miss in the same interval still cancel each other out. 
    - Gross error rate, on the other hand, counts every phantom and every miss in the numerator, so nothing cancels.
- Side-view occlusion is a [known limit of a roadside camera position](https://link.springer.com/article/10.1007/s00138-025-01668-x). We can look into automatic line placement as later extension.

### FOR THE NEXT SESSION

- Decide whether the targets apply per clip or per line 
- Try a higher input size and the motorcycle low-confidence check, if at all, before the eval clips. 
- Move `hys_n` and `cooldown` into the config file
- Freeze the system and run the eval clips. Place lines and zones using the same rules, hand count, run once, label events


## *Last Update: 2026-11-14*

### DONE

- Completed the `counting-analysis` notebook on `dev_overhead_medium_congest_01.mp4` (first counting run through to a working setup)
- Defined the counting line config in `config/counting_lines.yaml`. One entry per clip, with the line ID (e.g., `incoming`, `outgoing`) as the key
- Settled with the cross product sign as the means to determine which side of the counting line a vehicle's anchor point is on
- Set the counting line conventions. All line vectors drawn left to right and A is always the positive side and B negative 
- For directions, `B --> A` positive (since A corresponds to positive) while `A --> B` negative
- Decided that the bottom-center of a detection box will serve as the anchor point that will cross-product with the corresponding line
- Built `LineCrossingCounter` in `src/counting.py`. Cross-product side test, per-direction counts, per-track `cooldown=30`, and events that adhere to `SPEC.md`
- The first counting run showed cross-lane contamination. Added region-gated counting (one ROI polygon per lane to be checked with `in_roi()` function)
- Built `FrameLogger` to record every detection on every frame into a DataFrame (frame number, `track ID`, `box (xyxy)`, `box_area`, anchor point, sign per line)
- Saved the tracked detections once (pickle) and added a replay path to `process_clip`, so counting changes can be tested without model inference. Replay reproduced the full run.
- Moved the drawing code out of `process_clip` into `draw_annotations()`
- Implemented hysteresis in `LineCrossingCounter` (`hyst_n`). A side flip must hold for `hyst_n` consecutive sightings before it is counted (event is logged at crossing frame)
- Moved the incoming line a short distance further from the camera to give vehicles more frames after crossing (M went from 4 to 6). 
- Set `hyst_n=5` for incoming and `hyst_n=4` for outgoing for `dev_overhead_medium_congest_01.mp4`
- Recorded the final result on this clip. Incoming 83 vs 81 by hand, outgoing 70 vs 71 by hand, with no wrong-direction counts

### STILL BROKEN

- Incoming is over by 2. An van with a trailer towing two cars was detected as separate boxes, and each box crossed and was counted
- Outgoing is under by 1. One motorcycle object was not able to be detected, so there is nothing to count
- Both are detector-side errors and cannot be fixed in the counting logic (only by changing or possibly tuning the detector)
- Congested lane cascading ID transfers are still present (tracker limitation), though the counting errors from this clip did not originate from them
- Settings are tuned on one dev clip only. The margin on the both lines is just one frame (inc: M=6, `hyst_n=5`, out: M=5, `hyst_n=4`)

### LEARNINGS

- The cross-product treats the counting line as infinite. This means a vehicle in another lane can change sides based on it. 
- A counting line needs an ROI (region of interest) gating to capture which vehicles belong to it
- A close system total can hide errors. The pre-hysteresis outgoing count was 72 vs 71, but it contained three different errors that nearly cancelled out
- Cooldown and hysteresis overlap but they still differ in purpose. Cooldown blocks repeat counts after a crossing is counted. 
- Hysteresis, on the other hand, stops a false flip from being counted in the first place
- Hysteresis alone fixed the occluded stationary truck (its box was pushed across the line but vanished before `hyst_n` sightings). 
- Box-change rejection was planned to be added but found unneccessary, at least on this clip
- `hyst_n` has a ceiling (M). This is the fewest frames a real vehicle is seen after crossing. M is different for each line.
- M has to be measured from a log taken from a run without hysteresis, to ensure signs flip exactly upon crossing
- A higher hysteresis N can remove real crossings. A van on the outgoing line was missed because its detection dropped out before `hyst_n`
- Placing the line close to the camera gives better detections at the crossing but has the downside of leaving fewer frames after it
- In earlier versions of `LineCrossingCounter`, a flip blocked by the cooldown will skip the side update and leave a stale side. 
- Upon modifying `LineCrossingCounter`, the side now updates whenever a flip is confirmed (`> hyst_n`), whether or not it is counted
- Inference is deterministic on the same hardware and settings (with same boxes and IDs every run). 
- Still, track IDs can change when tracker settings change, so problem vehicles are identified by position
  - I forgot to set `track_buffer=60` (from 30) during the first few runs so I reran and got different IDs paired to detections
  - While changing `track_buffer` renumbered the tracks, it did not change detections in all frames
- Model inference is the slow part of the pipeline. Counting logic can be replayed on saved detections in a fraction of the time

### FOR THE NEXT SESSION

- Start the `tuning-system-on-dev-clips` notebook for the remaining three dev clips
- For each clip, place the lines and ROIs, save the detections, measure M per line, set `hyst_n`, and repeat
- Record every run as one row in a results table (settings used and the resulting counts), then write a short summary once each clip is done
- Move the ROI polygons, `hyst_n`, and `cooldown` into the config file


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