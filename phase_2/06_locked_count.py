import sys
sys.path.append(".")  # so Python can find the utils folder in the project root[cite: 47]

import json
from collections import deque

import cv2
import numpy as np
from ultralytics import YOLO
from utils.duplicates import remove_duplicates
from utils.standing_filter import remove_standing
from utils.locked_count import update_locked_count
from utils.tables import draw_table_tops, people_at_table

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
TABLES_PATH = "tables.json"              # area around each table, made with utils/select_table_point
TABLE_TOPS_PATH = "table_tops.json"      # outline of each table top, made with utils/select_table_to
DISPLAY_SIZE = (960, 540)                # window size (width, height), so the video fits on screen
PERSON_CLASS_ID = 0
CONFIDENCE = 0.2                         # low, so small and partly hidden guests are still found
POSE_CONFIDENCE = 0.3
RED = (0, 0, 255)                        # occupied. OpenCV writes colors as (blue, green, red)
GREEN = (0, 255, 0)                      # free
OCCUPY_SECONDS = 1                       # someone must be at the table this long before it counts as occupied
FREE_SECONDS = 1                         # the table must be empty this long before it counts as free again
UP_SECONDS = 2                           # a higher guest count must be the most common one for this long before we accept
DOWN_SECONDS = 10                        # a lower guest count is only accepted if the old count was not seen once in this long
SEATS_PER_TABLE = 4

# Two models. The detection model finds people best, so we count with it.
# The pose model misses some small or hidden people, so we only use it to tell who is standing.
model = YOLO("models/yolo11s.pt")
pose_model = YOLO("models/yolo11s-pose.pt")  # a small pose model is enough to tell who is standing

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

up_frames = int(UP_SECONDS * fps)
down_frames = int(DOWN_SECONDS * fps)

# The guest count of every recent frame, for every table. A deque with maxlen forgets the oldest
# count by itself when a new one is added. It starts full of zeros (empty tables).
recent_counts = {name: deque([0] * down_frames, maxlen=down_frames) for name in tables}

# The guest count we show for every table. Once set, it is hard to change.
locked_count = {name: 0 for name in tables}

while True:
    ok, frame = cap.read()
    if not ok:
        break

    result = model(frame, classes=[PERSON_CLASS_ID], conf=CONFIDENCE, verbose=False, device="mps")[0]
    pose_result = pose_model(frame, conf=POSE_CONFIDENCE, verbose=False, device="mps")[0]

    # Drop the people who are standing (waiters, people walking past), then the duplicates.
    # The order matters: a waiter's box can cover a guest's box, and removing duplicates
    # first would throw the guest away with the waiter.
    people = remove_standing(result.boxes, pose_result)
    people = remove_duplicates(people)

    centers = []
    for box in people:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        center = ((x1 + x2) // 2, (y1 + y2) // 2)
        centers.append(center)

    colors = {}  # table name -> the color of its table top
    occupied_count = 0
    guests = {}  # table name -> number of guests shown for that table

    for name, points in tables.items():
        # How many sitting people are at this table in this frame?
        count = people_at_table(points, centers)

        if count > 0:
            present_frames[name] += 1
            empty_frames[name] = 0
        else:
            empty_frames[name] += 1
            # A short gap is ignored (YOLO may miss a person for a few frames).
            # Only after a long gap do we forget the table and start counting from zero.
            if empty_frames[name] > free_frames:
                present_frames[name] = 0
                locked_count[name] = 0  # everyone left, so the next guests start a new count

        # YOLO misses a person now and then, so the count of a single frame jumps around.[cite: 52]
        # The locked count goes up easily but only goes down after a long gap without the higher number.[cite: 52]
        recent_counts[name].append(count)
        locked_count[name] = update_locked_count(locked_count[name], recent_counts[name], up_frames)

        # Red = occupied (someone has been sitting there long enough), green = free.[cite: 53]
        if present_frames[name] >= occupy_frames:
            occupied_count += 1
            guests[name] = locked_count[name]
            colors[name] = RED
        else:
            guests[name] = 0
            colors[name] = GREEN

    frame = draw_table_tops(frame, table_tops, colors)

    # Write the number of guests in the middle of each occupied table, as one big number.[cite: 53, 55]
    for name, points in table_tops.items():
        if guests[name] == 0:
            continue
        x, y = np.array(points).mean(axis=0).astype(int)
        text = str(guests[name])
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 4)
        cv2.putText(frame, text, (x - text_width // 2, y + text_height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4)

    total_guests = sum(guests.values())
    total_seats = SEATS_PER_TABLE * len(tables)

    cv2.rectangle(frame, (10, 10), (400, 100), (0, 0, 0), -1)
    cv2.putText(frame, f"Occupied: {occupied_count} / {len(tables)} tables", (20, 44),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    cv2.putText(frame, f"Guests: {total_guests} / {total_seats} seats", (20, 84),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    cv2.imshow("Phase 2 - Locked count (press Q to quit)", cv2.resize(frame, DISPLAY_SIZE))
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()