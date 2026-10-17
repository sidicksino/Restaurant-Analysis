import sys
sys.path.append(".")

import socket
import threading
import time

import cv2
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from utils.pipeline import run_pipeline

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
WEB_FOLDER = "phase_3/web/step_2"  # index.html, style.css and app.js live here
PORT = 8000
JPEG_QUALITY = 80  # 0-100. Lower = smaller pictures, faster over Wi-Fi, but blurrier

app = FastAPI()

# Shared between the video thread (writes) and the web server (reads).
#   jpeg, number   = the newest finished frame, as in step 1
#   info           = NEW: the facts about that frame as plain numbers (tables, guests, seats, time)
#   processing_fps = NEW: how many frames per second we manage to process
latest = {"jpeg": None, "number": 0, "info": None, "processing_fps": 0}
server_started = time.time()


def process_video():
    # Runs in the background for as long as the server is running.
    # When the video ends we start it again from the beginning.
    while True:
        started = time.time()
        last_second = int(started)
        frames_this_second = 0

        for frame_count, (frame, info) in enumerate(run_pipeline(VIDEO_PATH)):
            ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            latest["jpeg"] = jpeg.tobytes()
            latest["info"] = info  # in step 1 we threw this away, now we keep it for the page
            latest["number"] += 1

            # Once a second, note how many frames we processed in that second.
            frames_this_second += 1
            if int(time.time()) != last_second:
                latest["processing_fps"] = frames_this_second
                frames_this_second = 0
                last_second = int(time.time())

            # If the computer is faster than the video, wait so the video plays at its normal speed.
            ahead = frame_count / info["fps"] - (time.time() - started)
            if ahead > 0:
                time.sleep(ahead)


def video_frames():
    # Sends the newest frame to one browser, again and again, for as long as the page is open.
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


@app.get("/")
def page():
    return FileResponse(f"{WEB_FOLDER}/index.html", headers={"Cache-Control": "no-store"})


@app.get("/video")
def video():
    return StreamingResponse(video_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/stats")
def stats():
    # NEW in step 2. The page asks for this once a second and redraws its numbers and floor plan.
    # FastAPI turns the dictionary we return into JSON, a text format JavaScript can read.
    if latest["info"] is None:
        return {"ready": False}  # the first frame is not finished yet
    return {
        "ready": True,
        **latest["info"],  # everything run_pipeline told us about the newest frame
        "processing_fps": latest["processing_fps"],
        "uptime": int(time.time() - server_started),
        "video": VIDEO_PATH.split("/")[-1],
        "address": f"http://{local_address()}:{PORT}",
    }


# style.css and app.js are plain files, served as they are. The address has this step's name in it
# so the browser never mixes them up with the files of another step it has seen before.
app.mount("/step_2", StaticFiles(directory=WEB_FOLDER), name="static")


if __name__ == "__main__":
    threading.Thread(target=process_video, daemon=True).start()

    print(f"\n  On this computer:       http://localhost:{PORT}")
    print(f"  On the same Wi-Fi:      http://{local_address()}:{PORT}\n")

    # host="0.0.0.0" lets other devices on the network connect, not only this computer.
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning", timeout_graceful_shutdown=1)