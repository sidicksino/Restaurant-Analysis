import json
from collections import deque

import cv2
import numpy as np
from ultralytics import YOLO
from utils.duplicates import remove_duplicates
from utils.standing_filter import remove_standing
from utils.locked_count import update_locked_count
from utils.seats import find_seats, steady_seats

# This file is the last Phase 2 script (07_table_timer.py) turned into a function.
# Instead of showing each frame in a window, it hands the frame back to whoever asked for it,
# so a web server (or anything else) can decide what to do with it.

TABLES_PATH = "tables.json"         # area around each table, made with utils/select_table_points
TABLE_TOPS_PATH = "table_tops.json" # outline of each table top, made with utils/select_table_tops
PERSON_CLASS_ID = 0

# The numbers we used to write at the top of every script. They now live in a dictionary,
# so the settings page can change them while the video is running.
DEFAULT_SETTINGS = {
    "confidence": 0.2,       # Low, so small and partly hidden guests are still found
    "pose_confidence": 0.3,
    "occupy_seconds": 1,     # someone must be at the table this long before it counts as occupied
    "free_seconds": 1,       # the table must be empty this long before it counts as free again
    "up_seconds": 2,         # a higher guest count must be the most common one for this long before we accept
    "down_seconds": 10,      # a lower guest count is only accepted if the old count was not seen once in this long
    "seats_per_table": 4,
}

# Two models. The detection model finds people, the pose model tells us who is standing.
model = YOLO("models/yolo11s.pt")
pose_model = YOLO("models/yolo11s-pose.pt")


def run_pipeline(video_path, settings=DEFAULT_SETTINGS):
    # Goes through the video frame by frame. For every frame it gives back:
    #   frame = the picture with the tables, guest counts and timers drawn on it
    #   info  = the same facts as plain numbers (for the page and the database)
    # `yield` is like `return`, but the function continues where it stopped when asked for the next frame.
    # `settings` is read again on every frame, so a change takes effect straight away.
    with open(TABLES_PATH) as f:
        tables = json.load(f)
    with open(TABLE_TOPS_PATH) as f:
        table_tops = json.load(f)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    # A web page can use this to place its own label on top of the video, whatever size the video is shown at.
    # We also guess the shape: a round table top needs many points to draw, a square one only four.
    positions = {}
    shapes = {}
    table_centers = {}  # the middle of each table top in pixels, for working out who sits on which seat
    for name, points in table_tops.items():
        x, y = np.array(points).mean(axis=0)
        table_centers[name] = (x, y)
        positions[name] = [round(x / width, 4), round(y / height, 4)]
        shapes[name] = "round" if len(points) > 6 else "square"

    present_frames = {name: 0 for name in tables}  # frames with someone at the table
    empty_frames = {name: 0 for name in tables}    # frames in a row with nobody at the table
    recent_counts = {name: deque([0], maxlen=int(settings["down_seconds"] * fps)) for name in tables}
    locked_count = {name: 0 for name in tables}
    occupied_since = {name: None for name in tables}
    free_since = {name: 0 for name in tables}
    seat_scores = {name: [] for name in tables}
    frame_number = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_number += 1

        occupy_frames = settings["occupy_seconds"] * fps
        free_frames = settings["free_seconds"] * fps
        up_frames = max(1, int(settings["up_seconds"] * fps))
        down_frames = max(1, int(settings["down_seconds"] * fps))

        result = model(frame, classes=[PERSON_CLASS_ID], conf=settings["confidence"], verbose=False)[0]
        pose_result = pose_model(frame, conf=settings["pose_confidence"], verbose=False)[0]

        # Drop the people who are standing (waiters, people walking past), then the duplicates.
        people = remove_standing(result.boxes, pose_result)
        people = remove_duplicates(people)

        centers = []
        for box in people:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            centers.append(((x1 + x2) // 2, (y1 + y2) // 2))

        overlay = frame.copy()
        info = {"tables": {}}

        for name, points in tables.items():
            polygon = np.array(points, np.int32)
            seated = [center for center in centers if cv2.pointPolygonTest(polygon, center, False) >= 0]
            count = len(seated)

            if count > 0:
                present_frames[name] += 1
                empty_frames[name] = 0
            else:
                empty_frames[name] += 1
                if empty_frames[name] > free_frames:
                    present_frames[name] = 0
                    locked_count[name] = 0

            if recent_counts[name].maxlen != down_frames:
                old = list(recent_counts[name])[-down_frames:]
                recent_counts[name] = deque([0] * (down_frames - len(old)) + old, maxlen=down_frames)
            recent_counts[name].append(count)
            locked_count[name] = update_locked_count(locked_count[name], recent_counts[name], up_frames)

            if present_frames[name] >= occupy_frames:
                if occupied_since[name] is None:
                    occupied_since[name] = frame_number
                seconds = int((frame_number - occupied_since[name]) / fps)
                info["tables"][name] = {"occupied": True, "guests": locked_count[name], "seconds": seconds}
                color = (0, 0, 255)
            else:
                if occupied_since[name] is not None:
                    free_since[name] = frame_number
                    occupied_since[name] = None
                seconds = int((frame_number - free_since[name]) / fps)
                info["tables"][name] = {"occupied": False, "guests": 0, "seconds": seconds}
                color = (0, 255, 0)

            info["tables"][name]["position"] = positions[name]
            info["tables"][name]["shape"] = shapes[name]

            seat_count = settings["seats_per_table"]
            if locked_count[name] == 0 or len(seat_scores[name]) != seat_count:
                seat_scores[name] = [0.0] * seat_count
            taken_now = find_seats(table_centers[name], seated, seat_count)
            info["tables"][name]["seats_taken"] = steady_seats(seat_scores[name], taken_now, info["tables"][name]["guests"])

            if settings.get("draw_tables", True):
                table_top = np.array(table_tops[name], np.int32)
                cv2.fillPoly(overlay, [table_top], color)
                cv2.polylines(frame, [table_top], True, color, 2)

        frame = cv2.addWeighted(overlay, 0.4, frame, 0.6, 0)

        for name, points in table_tops.items():
            table = info["tables"][name]
            if table["guests"] == 0 or not settings.get("draw_labels", True):
                continue

            x, y = np.array(points).mean(axis=0).astype(int)
            text = str(table["guests"])
            time_text = f"{table['seconds'] // 60}:{table['seconds'] % 60:02d}"
            (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3)
            (time_width, time_height), _ = cv2.getTextSize(time_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

            gap = 6
            top = y - (text_height + gap + time_height) // 2
            cv2.putText(frame, text, (x - text_width // 2, top + text_height),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
            cv2.putText(frame, time_text, (x - time_width // 2, top + text_height + gap + time_height),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        info["occupied_tables"] = sum(table["occupied"] for table in info["tables"].values())
        info["total_tables"] = len(tables)
        info["guests"] = sum(table["guests"] for table in info["tables"].values())
        info["seats_per_table"] = settings["seats_per_table"]
        info["seats"] = settings["seats_per_table"] * len(tables)
        info["fps"] = fps

        yield frame, info

    cap.release()