

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

    results = model.track(frame, 
                          persist=True, 
                          classes=[2,3,5,7],
                          conf=0.25,
                          agnostic_nms=agnos_nms,
                          verbose=False,
                          tracker=track_file)

    track_ids = results[0].boxes.id

    if track_ids is None:
        return []

    boxes = results[0].boxes.xyxy
    conf_scores = results[0].boxes.conf
    cls_ids = results[0].boxes.cls

    detections_and_tracks = []
    for box, score, cls_id, tr_id in zip(boxes, conf_scores, cls_ids, track_ids):

        prediction = {"box": box.tolist(),
                      "conf_score": score.item(),
                      "cls_id": cls_id.item(),
                      "track_id": tr_id.item()}

        detections_and_tracks.append(prediction)
    
    return detections_and_tracks