def detect_vehicles(frame, model, agnos_nms=True):

    results = model.predict(frame, 
                            classes=[2,3,5,7],
                            conf=0.25,  
                            agnostic_nms=agnos_nms,
                            verbose=False)

    boxes = results[0].boxes.xyxy
    conf_scores = results[0].boxes.conf
    cls_ids = results[0].boxes.cls

    detections = []
    for box, score, cls_id in zip(boxes, conf_scores, cls_ids):

        prediction = {"box": box.tolist(),
                      "conf_score": score.item(),
                      "cls_id": cls_id.item()}

        detections.append(prediction)
    
    return detections


def track_vehicles(frame, model, agnos_nms=True, track_file="bytetrack.yaml"):
    """
    Detect and track vehicles in a single frame and return a list of dicts 
    (one dict per tracked vehicle). Call it on consecutive frames with the same 
    model and tracker config so that track IDs carry over from frame to frame.

    Args:
        frame (np.ndarray): A single BGR video frame.
        model (YOLO): A loaded Ultralytics YOLO model.
        agnos_nms (bool): If True, boxes of different classes that 
                          overlap suppress each other, so one vehicle 
                          cannot have two boxes with different labels.
        track_file (str): Tracker config file passed to Ultralytics.

    Returns:
        A list of dicts, one per tracked vehicle, with keys:
            "box": [x1, y1, x2, y2] in pixels
            "conf_score": detection confidence
            "cls_id": COCO class ID (2 car, 3 motorcycle, 5 bus, 7 truck)
            "track_id": ID assigned by the tracker
        Returns an empty list if the frame has no tracked vehicles.
    """

    # Detect COCO classes that are vehicles only 
    # Also, keep tracker state between calls
    results = model.track(frame, 
                          classes=[2,3,5,7],
                          conf=0.25,
                          agnostic_nms=agnos_nms,
                          verbose=False,
                          persist=True, 
                          tracker=track_file)

    track_ids = results[0].boxes.id

    if track_ids is None:
        return []

    boxes = results[0].boxes.xyxy
    conf_scores = results[0].boxes.conf
    cls_ids = results[0].boxes.cls

    # Convert the tensors into one plain dict per tracked vehicle
    tracked_detections = []
    for box, score, cls_id, tr_id in zip(boxes, conf_scores, cls_ids, track_ids):

        prediction = {"box": box.tolist(),
                      "conf_score": score.item(),
                      "cls_id": cls_id.item(),
                      "track_id": tr_id.item()}

        tracked_detections.append(prediction)
    
    return tracked_detections
