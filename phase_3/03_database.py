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
import utils.database as database

VIDEO_PATH = "videos/Cctv-Resturant-Demo.mp4"
WEB_FOLDER = "phase_3/web/step_3"  # index.html, style.css and app.js live here
PORT = 8000
JPEG_QUALITY = 80                  # 0-100. Lower = smaller pictures, faster over Wi-Fi
SNAPSHOT_SECONDS = 5               # how often to record dining room metrics in the database

app = FastAPI()

latest = {"jpeg": None, "number": 0, "info": None, "processing_fps": 0}
server_started = time.time()


def process_video():
    # Runs in the background for as long as the server is running.
    # Tracks guest visits to tables and periodically records room snapshots into SQLite.
    visits = {}
    last_snapshot = 0

    while True:
        started = time.time()
        last_second = int(started)
        frames_this_second = 0

        for frame_count, (frame, info) in enumerate(run_pipeline(VIDEO_PATH)):
            ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            latest["jpeg"] = jpeg.tobytes()
            latest["info"] = info
            latest["number"] += 1

            # 2. Spot the end of a visit
            # A table that had guests a moment ago and is free now: that visit is finished.
            for name, table in info["tables"].items():
                if table["occupied"] and table["guests"] > 0:
                    visits[name] = {"guests": table["guests"], "seconds": table["seconds"]}
                elif not table["occupied"] and name in visits:
                    visit = visits.pop(name)
                    database.save_visit(name, visit["seconds"], visit["guests"])

            # 3. A snapshot every 5 seconds
            # Two numbers and the time. Enough to draw how busy the room was.
            if time.time() - last_snapshot >= SNAPSHOT_SECONDS:
                database.save_snapshot(info["occupied_tables"], info["guests"])
                last_snapshot = time.time()

            # Measure real processing FPS once a second
            frames_this_second += 1
            if int(time.time()) != last_second:
                latest["processing_fps"] = frames_this_second
                frames_this_second = 0
                last_second = int(time.time())

            # Synchronize playback speed
            ahead = frame_count / info["fps"] - (time.time() - started)
            if ahead > 0:
                time.sleep(ahead)


def video_frames():
    sent = 0
    while True:
        if latest["number"] == sent:
            time.sleep(0.005)
            continue
        sent = latest["number"]
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + latest["jpeg"] + b"\r\n"


def local_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
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
    # Returns the live frame status for the Live Floor view
    if latest["info"] is None:
        return {"ready": False}
    return {
        "ready": True,
        **latest["info"],
        "processing_fps": latest["processing_fps"],
        "uptime": int(time.time() - server_started),
        "video": VIDEO_PATH.split("/")[-1],
        "address": f"http://{local_address()}:{PORT}",
    }


@app.get("/history")
def history(range: str = "5m"):
    # Returns historical table visits and room snapshots from the database
    return database.get_history_data(range_str=range)


app.mount("/step_3", StaticFiles(directory=WEB_FOLDER), name="static")


if __name__ == "__main__":
    threading.Thread(target=process_video, daemon=True).start()

    print(f"\n  On this computer:       http://localhost:{PORT}")
    print(f"  On the same Wi-Fi:      http://{local_address()}:{PORT}\n")

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning", timeout_graceful_shutdown=1)
