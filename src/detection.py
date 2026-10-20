

def detect_vehicles(frame, model):

    results = model.predict(frame, 
                            classes=[2,3,5,7],
                            conf=0.25,  
                            agnostic_nms=True,
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