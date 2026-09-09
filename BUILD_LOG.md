**This log is for my personal reference but I placed it here because it will show the actual process of completing the project (even though it's less polished and messier than the README)

## Last Update: 2026-09-09

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
- Begin formal hand-counting on eval clips (count twice, compare)
- Film own footage if time and location allow