import sys
sys.path.append(".")  # so Python can find the utils folder in the project root

import cv2
from ultralytics import YOLO
from utils.duplicates import remove_duplicates

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
DISPLAY_SIZE = (960, 540)  # window size (width, height), so the video fits on the screen
PERSON_CLASS_ID = 0
CONFIDENCE = 0.3

model = YOLO("models/yolo11l.pt")

cap = cv2.VideoCapture(VIDEO_PATH)

while True:
    ok, frame = cap.read()
    if not ok:
        break

    result = model(
        frame,
        classes=[PERSON_CLASS_ID],
        conf=CONFIDENCE,
        verbose=False,
    )[0]

    # YOLO sometimes puts two boxes on one person. We only want one box per person.
    people = remove_duplicates(result.boxes)

    # Red = every box YOLO returned. Green is drawn on top for the boxes we kept,
    # so any red box still visible is a duplicate that was removed.
    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

    for box in people:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Count the people we kept, not the boxes YOLO returned.
    people_count = len(people)

    cv2.rectangle(frame, (10, 10), (250, 60), (0, 0, 0), -1)
    cv2.putText(
        frame,
        f"People: {people_count}",
        (20, 46),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (255, 255, 255),
        2,
    )

    cv2.imshow("Phase 2 - Remove duplicates (press Q to quit)", cv2.resize(frame, DISPLAY_SIZE))
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()