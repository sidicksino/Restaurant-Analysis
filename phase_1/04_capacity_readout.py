import cv2
from ultralytics import YOLO

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
DISPLAY_SIZE = (960, 540)  # window size (width, height), so the video fits on the screen
PERSON_CLASS_ID = 0
CONFIDENCE = 0.3
TOTAL_SEATS = 24  # 6 tables x 4 chairs in this restaurant

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

    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    people_count = len(result.boxes)

    # How full is the restaurant? Cap at 100% in case we count more people than seats.
    percent_full = min(people_count / TOTAL_SEATS, 1.0) * 100

    # Dark panel with the text and a fill bar.
    cv2.rectangle(frame, (10, 10), (430, 95), (0, 0, 0), -1)
    cv2.putText(
        frame,
        f"{people_count} / {TOTAL_SEATS} seats, {percent_full:.0f}% full",
        (20, 46),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )

    bar_x1, bar_y1, bar_x2, bar_y2 = 20, 62, 420, 82
    fill_x2 = bar_x1 + int((bar_x2 - bar_x1) * percent_full / 100)
    cv2.rectangle(frame, (bar_x1, bar_y1), (fill_x2, bar_y2), (0, 200, 0), -1)
    cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (255, 255, 255), 1)

    cv2.imshow("Part 4 - Capacity readout (press Q to quit)", cv2.resize(frame, DISPLAY_SIZE))
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()