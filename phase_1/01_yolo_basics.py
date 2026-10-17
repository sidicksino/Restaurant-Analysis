# Here in this code we detect all object

import cv2
from ultralytics import YOLO

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
DISPLAY_SIZE = (960, 540)

model = YOLO("models/yolo11l.pt")

cap = cv2.VideoCapture(VIDEO_PATH)

while True:
    ok, frame = cap.read()
    if not ok:
        break  # end of the video

    results = model(frame, verbose=False, device="mps")
    result = results[0]

    annotated = result.plot()
    annotated_resized = cv2.resize(annotated, DISPLAY_SIZE)

    cv2.imshow("Part 1 - YOLO basics (press Q to quit)", annotated_resized)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()