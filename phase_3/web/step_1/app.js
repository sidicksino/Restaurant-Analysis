const stream = document.getElementById("stream");

// --------- Live / offline badge ---------

function setLive(isLive, text) {
    document.getElementById("live-pill").className = "live-pill" + (isLive ? "" : " offline");
    document.getElementById("live-text").textContent = text;
}

// Once a second: if the image has a size, at least one frame has arrived from the server.
setInterval(() => {
    if (stream.naturalWidth > 0) setLive(true, "Live");
}, 1000);

// If the server stops, the picture fails. Say so, then keep trying to reconnect.
stream.addEventListener("error", () => {
    setLive(false, "Offline");
    setTimeout(() => { stream.src = "/video?retry=" + Date.now(); }, 2000);
});

// Clock in the camera bar
const clock = document.getElementById("clock");
if (clock) {
    setInterval(() => {
        clock.textContent = new Date().toLocaleTimeString();
    }, 1000);
}

// Fullscreen button
const fullscreenBtn = document.getElementById("fullscreen");
const viewport = document.getElementById("viewport");
if (fullscreenBtn && viewport) {
    fullscreenBtn.addEventListener("click", () => {
        if (!document.fullscreenElement) {
            viewport.requestFullscreen().catch(err => alert(err.message));
        } else {
            document.exitFullscreen();
        }
    });
}