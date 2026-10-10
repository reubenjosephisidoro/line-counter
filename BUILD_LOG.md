**This log is for my personal reference but I placed it here because it will show the actual process of completing the project (even though it's less polished and messier than the README)

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