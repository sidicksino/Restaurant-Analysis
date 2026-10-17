import sys
sys.path.append(".")  # so Python can find the utils folder in the project root[cite: 41]

import json

import cv2
import numpy as np
from ultralytics import YOLO
from utils.duplicates import remove_duplicates
from utils.standing_filter import remove_standing
from utils.tables import draw_table_tops, people_at_table

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
TABLES_PATH = "tables.json"
TABLE_TOPS_PATH = "table_tops.json"
DISPLAY_SIZE = (960, 540)
PERSON_CLASS_ID = 0
CONFIDENCE = 0.2        # low on purpose so half-hidden seated guests are found
POSE_CONFIDENCE = 0.3
TOTAL_SEATS = 24        # 6 tables x 4 chairs in the restaurant

RED = (0, 0, 255)       # occupied
GREEN = (0, 255, 0)     # free
OCCUPY_SECONDS = 1
FREE_SECONDS = 1

model = YOLO("models/yolo11s.pt")
pose_model = YOLO("models/yolo11s-pose.pt")

with open(TABLES_PATH) as f:
    tables = json.load(f)
with open(TABLE_TOPS_PATH) as f:
    table_tops = json.load(f)

cap = cv2.VideoCapture(VIDEO_PATH)

fps = cap.get(cv2.CAP_PROP_FPS)
occupy_frames = OCCUPY_SECONDS * fps
free_frames = FREE_SECONDS * fps

present_frames = {name: 0 for name in tables}
empty_frames = {name: 0 for name in tables}

while True:
    ok, frame = cap.read()
    if not ok:
        break

    result = model(frame, classes=[PERSON_CLASS_ID], conf=CONFIDENCE, verbose=False, device="mps")[0]
    pose_result = pose_model(frame, conf=POSE_CONFIDENCE, verbose=False, device="mps")[0]

    # Filter out standing people (waiters / passersby), then eliminate duplicates
    people = remove_standing(result.boxes, pose_result)
    people = remove_duplicates(people)

    centers = []
    for box in people:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        center = ((x1 + x2) // 2, (y1 + y2) // 2)
        centers.append(center)

    colors = {}
    counts = {}
    occupied_count = 0
    total_guests = 0

    for name, points in tables.items():
        count = people_at_table(points, centers)
        counts[name] = count

        if count > 0:
            present_frames[name] += 1
            empty_frames[name] = 0
        else:
            empty_frames[name] += 1
            if empty_frames[name] > free_frames:
                present_frames[name] = 0

        # Mark table occupied only after someone sits long enough
        if present_frames[name] >= occupy_frames:
            occupied_count += 1
            total_guests += count
            colors[name] = RED
        else:
            colors[name] = GREEN

    # Highlight table tops with tint
    frame = draw_table_tops(frame, table_tops, colors)

    # Draw the occupant count in the center of occupied tables
    for name, points in table_tops.items():
        if colors[name] == RED and counts[name] > 0:
            x, y = np.array(points).mean(axis=0).astype(int)
            cv2.putText(
                frame,
                str(counts[name]),
                (x - 12, y + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                3,
            )

    # Top-left status HUD banner
    cv2.rectangle(frame, (10, 10), (320, 90), (0, 0, 0), -1)
    cv2.putText(
        frame,
        f"Occupied: {occupied_count} / {len(tables)} tables",
        (20, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        f"Guests: {total_guests} / {TOTAL_SEATS} seats",
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    cv2.imshow("Restaurant Analysis", cv2.resize(frame, DISPLAY_SIZE))
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()