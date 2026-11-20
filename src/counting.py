import cv2
import numpy as np


def in_roi(roi, anchor_point):
    """Return True if anchor_point lies inside or on the edge of the polygon roi."""
    polygon = np.array(roi, dtype=np.int32)
    return cv2.pointPolygonTest(polygon, anchor_point, False) >= 0


CLASS_MAP = {2:"car", 3:"motorcycle", 5:"bus", 7:"truck"}


def in_roi(roi, anchor_point):
    """Return True if anchor_point lies 
    inside or on the edge of the polygon roi."""
    polygon = np.array(roi, dtype=np.int32)
    return cv2.pointPolygonTest(polygon, anchor_point, False) >= 0
    

class LineCrossingCounter:
    """
    Counts vehicles crossing a single counting line. The counter 
    keeps track of which side of the line each track is on and records
    a crossing when a track moves to the other side and stays there for
    hys_n consecutive sightings. Only vehicles inside the line's ROI are
    considered. Create one counter per line.

    Args:
        source (str): Filename of the clip
        fps (float): Clip frame rate, used to compute event timestamps.
        line_id (str): Name of this line recorded in each event.
        line (list[list]): Two points [[x1, y1], [x2, y2]], drawn left to right.
        roi (list[tuple]): Polygon as a list of points covering this line's ROI.
        dir_labels (dict): Maps the side a vehicle arrives on to a direction label,
                           e.g. {"positive": "B --> A", "negative": "A --> B"}.
        cooldown (int): Frames during which the same track cannot be counted again
                        after a crossing.
        hys_n (int): Consecutive sightings a track must stay on the new side
                     before the crossing is confirmed/counted.

    Attributes:
        counts (dict): Number of crossings per direction label.
        events (list[dict]): One dict per counted crossing.
        track_sides (str): Confirmed side ("positive", "negative") of each track.
    """

    def __init__(self, source, fps, line_id, 
                 line, roi, dir_labels, cooldown=30,
                 hys_n=5):
        
        self.source = source
        self.fps = fps
        self.line_id = line_id
        self.line = line
        self.roi = roi
        self.dir_labels = dir_labels
        self.cooldown = cooldown
        self.last_crossed = {}
        self.tentative_crossed = {}
        self.track_sides = {}
        self.hys_n = hys_n

        self.counts = {self.dir_labels["positive"]:0, 
                       self.dir_labels["negative"]:0}

        self.events = []

    def update(self, tracked_detections, frame_number):

        for detection in tracked_detections:

            box = detection["box"]
            x_anchor = (box[0] + box[2]) /2
            y_anchor = box[3]

            # Check first if the anchor point lies within the roi or along its edges
            # If it does, proceed with the rest of the sequence, else skip the 
            # anchor point entirely from being recorded and counted relative to this line
            if not in_roi(self.roi, (x_anchor, y_anchor)):
                continue

            x1, x2 = self.line[0][0], self.line[1][0]
            y1, y2 = self.line[0][1], self.line[1][1]
            cross_product = (x2 - x1) * (y_anchor - y1) - (y2 - y1) * (x_anchor - x1)

            # The sign of the cross-product tells which 
            # side of the line the anchor is on
            sign = "positive" if cross_product > 0 else "negative"
            track_id = detection["track_id"]

            # The track is new so its current side 
            # immediately becomes its confirmed side
            if track_id not in self.track_sides:
                self.track_sides[track_id] = sign
                continue

            # The track is still on its confirmed side 
            # so a pending flip is cancelled
            if sign == self.track_sides[track_id]:
                self.tentative_crossed.pop(track_id, None)
                continue

            # The track is on the other side 
            # Start or continue a pending flip
            if track_id not in self.tentative_crossed:
                self.tentative_crossed[track_id] = {"flip_frame": frame_number,
                                                    "flip_cls": detection["cls_id"], 
                                                    "count": 0}

            # Add 1 to count for one more sighting on the other side
            self.tentative_crossed[track_id]["count"] += 1

            # If number of frames remained on the new side is 
            # less than hys_n, wait for the next frame
            if self.tentative_crossed[track_id]["count"] < self.hys_n:
                continue 

            # The flip held for hys_n frames so it is committed
            pending = self.tentative_crossed.pop(track_id)
            flip_frame = pending["flip_frame"]
            self.track_sides[track_id] = sign

            # Skip the count if this track already crossed 
            # within the last `cooldown` frames
            if track_id in self.last_crossed:
                if flip_frame - self.last_crossed[track_id] <= self.cooldown:
                    continue

            # Count the crossing and date it at the 
            # crossing frame where the flip started
            self.last_crossed[track_id] = flip_frame
            self.counts[self.dir_labels[sign]] += 1

            # Build the event log and append to the event list
            event = {
                "source_video": self.source,
                "line_id": self.line_id,
                "vehicle_id": track_id, 
                "frame_number": flip_frame,
                "timestamp": flip_frame / self.fps,
                "direction": self.dir_labels[sign],
                "class": CLASS_MAP[pending["flip_cls"]]}

            self.events.append(event)
