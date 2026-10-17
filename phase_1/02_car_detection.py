# Here in this code we are detecting Car and Truck

import cv2
from ultralytics import YOLO

VIDEO_PATH = "videos/highway.mp4"
DISPLAY_SIZE = (960, 540)

# 1. Two settings
CAR_CLASS_ID = 2
TRUCK_CLASS_ID = 7

CONFIDENCE = 0.3

model = YOLO("models/yolo11l.pt")

cap = cv2.VideoCapture(VIDEO_PATH)

while True:
    ok, frame = cap.read()
    if not ok:
        break  # end of the video

    # 2. Ask for car and truck (use device="mps" if on Apple Silicon Mac)
    result = model(
        frame,
        classes=[CAR_CLASS_ID, TRUCK_CLASS_ID],
        conf=CONFIDENCE,
        verbose=False,
        device="mps",
    )[0]

    # 3. Draw each box ourselves
    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        confidence = float(box.conf)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"car truck {confidence:.2f}",
            (x1, y1 - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    resized_frame = cv2.resize(frame, DISPLAY_SIZE)
    cv2.imshow("Part 2 - Car and Truck detection (press Q to quit)", resized_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()