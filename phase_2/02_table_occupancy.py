import sys
sys.path.append(".")  # so Python can find the utils folder in the project root

import json
import cv2
import numpy as np
from ultralytics import YOLO
from utils.duplicates import remove_duplicates
from utils.tables import draw_table_tops, people_at_table

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
TABLES_PATH = "tables.json"           # area around each table, made with utils/select_table_point
TABLE_TOPS_PATH = "table_tops.json"   # outline of each table top, made with utils/select_table_to
DISPLAY_SIZE = (960, 540)             # window size (width, height), so the video fits on screen
PERSON_CLASS_ID = 0
CONFIDENCE = 0.3
RED = (0, 0, 255)                     # occupied. OpenCV writes colors as (blue, green, red)
GREEN = (0, 255, 0)                   # free

model = YOLO("models/yolo11l.pt")

# Each table has two shapes, both saved as a list of corner points:
# - the area around it (table plus chairs), which decides if the table is occupied
# - the table top itself, which we only use to highlight the table on screen
with open(TABLES_PATH) as f:
    tables = json.load(f)
with open(TABLE_TOPS_PATH) as f:
    table_tops = json.load(f)

cap = cv2.VideoCapture(VIDEO_PATH)

while True:
    ok, frame = cap.read()
    if not ok:
        break

    result = model(frame, classes=[PERSON_CLASS_ID], conf=CONFIDENCE, verbose=False)[0]
    people = remove_duplicates(result.boxes)

    # We describe each person by one point: the centre of their box.
    centers = []
    for box in people:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        center = ((x1 + x2) // 2, (y1 + y2) // 2)
        centers.append(center)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
        cv2.circle(frame, center, 5, (255, 255, 255), -1)

    colors = {}  # table name -> the color of its table top
    occupied_count = 0

    for name, points in tables.items():
        # A table is occupied if at least one person is at it.
        if people_at_table(points, centers) > 0:
            occupied_count += 1
            colors[name] = RED
        else:
            colors[name] = GREEN

    # Highlight every table top in its color. The area around the table is not highlighted.
    frame = draw_table_tops(frame, table_tops, colors)

    # Write each table's name in the middle of its table top.
    for name, points in table_tops.items():
        x, y = np.array(points).mean(axis=0).astype(int)
        cv2.putText(frame, name, (x - 40, y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.rectangle(frame, (10, 10), (330, 60), (0, 0, 0), -1)
    cv2.putText(frame, f"Occupied: {occupied_count} / {len(tables)}", (20, 46),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    cv2.imshow("Phase 2 - Table occupancy (press Q to quit)", cv2.resize(frame, DISPLAY_SIZE))
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()