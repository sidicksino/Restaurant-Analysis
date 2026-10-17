import sys
sys.path.append(".")  # so Python can find the utils folder in the project root

import json

import cv2
import numpy as np
from ultralytics import YOLO
from utils.duplicates import remove_duplicates
from utils.tables import draw_table_tops, people_at_table

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
TABLES_PATH = "tables.json"          # area around each table, made with utils/select_table_point
TABLE_TOPS_PATH = "table_tops.json"  # outline of each table top, made with utils/select_table_to
DISPLAY_SIZE = (960, 540)            # window size (width, height), so the video fits on the screen
PERSON_CLASS_ID = 0
CONFIDENCE = 0.3
RED = (0, 0, 255)                    # occupied. OpenCV writes colors as (blue, green, red)
GREEN = (0, 255, 0)                  # free
OCCUPY_SECONDS = 3  # someone must be at the table this long before it counts as occupied
FREE_SECONDS = 2    # the table must be empty this long before it counts as free again

model = YOLO("models/yolo11m.pt")

with open(TABLES_PATH) as f:
    tables = json.load(f)
with open(TABLE_TOPS_PATH) as f:
    table_tops = json.load(f)

cap = cv2.VideoCapture(VIDEO_PATH)

# The video has a fixed number of frames per second, so we can measure time by counting frames.
fps = cap.get(cv2.CAP_PROP_FPS)
occupy_frames = OCCUPY_SECONDS * fps
free_frames = FREE_SECONDS * fps

# Two counters for every table.
present_frames = {name: 0 for name in tables}  # frames with someone at the table
empty_frames = {name: 0 for name in tables}    # frames in a row with nobody at the table

while True:
    ok, frame = cap.read()
    if not ok:
        break

    result = model(frame, classes=[PERSON_CLASS_ID], conf=CONFIDENCE, verbose=False, device="mps")[0]
    people = remove_duplicates(result.boxes)

    centers = []
    for box in people:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        center = ((x1 + x2) // 2, (y1 + y2) // 2)
        centers.append(center)

    colors = {}  # table name -> the color of its table top
    occupied_count = 0

    for name, points in tables.items():
        someone_here = people_at_table(points, centers) > 0

        if someone_here:
            present_frames[name] += 1
            empty_frames[name] = 0
        else:
            empty_frames[name] += 1
            # A short gap is ignored (YOLO may miss a person for a few frames).
            # Only after a long gap do we forget the table and start counting from zero.
            if empty_frames[name] > free_frames:
                present_frames[name] = 0

        # Red = occupied (someone has been there long enough), green = free.
        if present_frames[name] >= occupy_frames:
            occupied_count += 1
            colors[name] = RED
        else:
            colors[name] = GREEN

    frame = draw_table_tops(frame, table_tops, colors)

    for name, points in table_tops.items():
        x, y = np.array(points).mean(axis=0).astype(int)
        cv2.putText(frame, name, (x - 40, y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.rectangle(frame, (10, 10), (330, 60), (0, 0, 0), -1)
    cv2.putText(frame, f"Occupied: {occupied_count} / {len(tables)}", (20, 46),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    cv2.imshow("Phase 2 - Occupancy timer (press Q to quit)", cv2.resize(frame, DISPLAY_SIZE))
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()