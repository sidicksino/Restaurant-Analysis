import json
import os

import cv2
import numpy as np

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
TABLES_PATH = "tables.json"
DISPLAY_SIZE = (960, 540)  # window size (width, height), so the video fits on the screen
WINDOW = "Select table points"

# Use the first frame of the video as the picture to click on.
cap = cv2.VideoCapture(VIDEO_PATH)
ok, first_frame = cap.read()
cap.release()

# The window is smaller than the video, so a click must be scaled back up to video pixels.
scale = first_frame.shape[1] / DISPLAY_SIZE[0]

# Start from the tables that are already saved, if there are any.
tables = {}  # table name -> list of [x, y] points
if os.path.exists(TABLES_PATH) and os.path.getsize(TABLES_PATH) > 0:
    try:
        with open(TABLES_PATH) as f:
            tables = json.load(f)
    except json.JSONDecodeError:
        tables = {}

current_points = []  # points of the table being drawn right now


def on_mouse(event, x, y, flags, param):
    # Every Left click adds one corner to the table being drawn.
    if event == cv2.EVENT_LBUTTONDOWN:
        current_points.append([int(x * scale), int(y * scale)])


cv2.namedWindow(WINDOW)
cv2.setMouseCallback(WINDOW, on_mouse)

while True:
    frame = first_frame.copy()

    # Saved tables in green.
    for name, points in tables.items():
        cv2.polylines(frame, [np.array(points, np.int32)], True, (0, 255, 0), 2)
        cv2.putText(frame, name, tuple(points[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # The table being drawn in yellow.
    for point in current_points:
        cv2.circle(frame, tuple(point), 5, (0, 255, 255), -1)
    if len(current_points) > 1:
        cv2.polylines(frame, [np.array(current_points, np.int32)], False, (0, 255, 255), 2)

    cv2.rectangle(frame, (0, 0), (1280, 40), (0, 0, 0), -1)
    cv2.putText(frame, "Click = add corner   N = next table   U = undo   C = clear all   S = save & quit   Q = quit",
                (10, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow(WINDOW, cv2.resize(frame, DISPLAY_SIZE))
    key = cv2.waitKey(20) & 0xFF

    if key == ord("n") and len(current_points) >= 3:
        # Finish this table and start the next one.
        tables[f"Table {len(tables) + 1}"] = current_points
        current_points = []
    elif key == ord("u") and current_points:
        current_points.pop()
    elif key == ord("c"):
        tables = {}
        current_points = []
    elif key == ord("s"):
        with open(TABLES_PATH, "w") as f:
            json.dump(tables, f, indent=4)
        print(f"Saved {len(tables)} tables to {TABLES_PATH}")
        break
    elif key == ord("q"):
        break

cv2.destroyAllWindows()