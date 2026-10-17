import sys
sys.path.append(".")  # so Python can find the utils folder in the project root

import socket
import threading
import time

import cv2
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from utils.pipeline import run_pipeline

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
WEB_FOLDER = "phase_3/web/step_1"  # index.html, style.css and app.js live here
PORT = 8020
JPEG_QUALITY = 80  # 0-100. Lower = smaller pictures, faster over Wi-Fi, but blurrier

app = FastAPI()

# The newest finished frame, already packed as a JPEG picture. The video thread writes it,
# the web server reads it. "number" goes up by one for every new frame.
latest = {"jpeg": None, "number": 0}


def process_video():
    # Runs in the background for as long as the server is running.
    # run_pipeline is the last Phase 2 script as a function: it hands us one frame at a time.
    # When the video ends we start it again from the beginning.
    while True:
        started = time.time()
        for frame_count, (frame, info) in enumerate(run_pipeline(VIDEO_PATH)):
            ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            latest["jpeg"] = jpeg.tobytes()
            latest["number"] += 1

            # If the computer is faster than the video, wait so the video plays at its normal speed.
            ahead = frame_count / info["fps"] - (time.time() - started)
            if ahead > 0:
                time.sleep(ahead)


def video_frames():
    # Sends the newest frame to one browser, again and again, for as long as the connection is open.
    # The browser replaces the picture every time a new one arrives, which makes it look like a video.
    sent = 0
    while True:
        if latest["number"] == sent:
            time.sleep(0.005)  # no new frame yet
            continue
        sent = latest["number"]
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + latest["jpeg"] + b"\r\n"


def local_address():
    # The address of this computer on the Wi-Fi, so other devices know what to open.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # nothing is sent, this only picks the right network card
        return s.getsockname()[0]
    except OSError:
        return "localhost"
    finally:
        s.close()


@app.get("/", response_class=HTMLResponse)
def page():
    # The page has two blanks, {{video}} and {{address}}, that we fill in before sending it.
    with open(f"{WEB_FOLDER}/index.html", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{video}}", VIDEO_PATH.split("/")[-1])
    return html.replace("{{address}}", f"http://{local_address()}:{PORT}")


@app.get("/video")
def video():
    return StreamingResponse(video_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


# style.css and app.js are plain files, served as they are. The address has this step's name in it
# so the browser never mixes them up with the files of another step it has seen before.
app.mount("/step_1", StaticFiles(directory=WEB_FOLDER), name="static")


if __name__ == "__main__":
    threading.Thread(target=process_video, daemon=True).start()

    print(f"\n  On this computer:       http://localhost:{PORT}")
    print(f"  On the same Wi-Fi:      http://{local_address()}:{PORT}\n")

    # host="0.0.0.0" lets other devices on the network connect, not only this computer.
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning", timeout_graceful_shutdown=1)