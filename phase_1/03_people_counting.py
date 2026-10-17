import cv2
from ultralytics import YOLO

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
DISPLAY_SIZE = (960, 540)

PERSON_CLASS_ID = 0
CONFIDENCE = 0.3

model = YOLO("models/yolo11l.pt")

cap = cv2.VideoCapture(VIDEO_PATH)

while True:
    ok, frame = cap.read()
    if not ok:
        break  # end of the video

    result = model(
        frame,
        classes=[PERSON_CLASS_ID],
        conf=CONFIDENCE,
        verbose=False,
        device="mps",
    )[0]

    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        confidence = float(box.conf)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"person {confidence:.2f}",
            (x1, y1 - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    # 1. Count
    people_count = len(result.boxes)

    # 2. Show it
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

    resized_frame = cv2.resize(frame, DISPLAY_SIZE)
    cv2.imshow("Part 3 - People counting (press Q to quit)", resized_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()