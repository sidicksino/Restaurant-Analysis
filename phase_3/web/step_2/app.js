const stream = document.getElementById("stream");
const livePill = document.getElementById("live-pill");
const liveText = document.getElementById("live-text");
const uptimeText = document.getElementById("uptime-text");
const clock = document.getElementById("clock");
const fullscreenBtn = document.getElementById("fullscreen");
const viewport = document.getElementById("viewport");

const cameraVideoName = document.getElementById("camera-video-name");
const footerVideo = document.getElementById("footer-video");
const footerAddress = document.getElementById("footer-address");

// Stat card elements
const statOccupied = document.getElementById("stat-occupied");
const statTotalTables = document.getElementById("stat-total-tables");
const statWalkins = document.getElementById("stat-walkins");

const statGuests = document.getElementById("stat-guests");
const statTotalSeats = document.getElementById("stat-total-seats");
const statCapacity = document.getElementById("stat-capacity");

const statUtilization = document.getElementById("stat-utilization");
const statSeatsFree = document.getElementById("stat-seats-free");

const statAvgTime = document.getElementById("stat-avg-time");
const statAvgUnit = document.getElementById("stat-avg-unit");
const statLongest = document.getElementById("stat-longest");

// Floor plan elements
const fpTableCount = document.getElementById("fp-table-count");
const floorBlueprint = document.getElementById("floor-blueprint");

// Seat positions around a table:
// 0: 0 deg (East / Right)
// 1: 90 deg (South / Bottom)
// 2: 180 deg (West / Left)
// 3: 270 deg (North / Top)
const SEAT_POSITIONS = ["right", "bottom", "left", "top"];

// --------- Clock in camera bar ---------
if (clock) {
    setInterval(() => {
        clock.textContent = new Date().toLocaleTimeString();
    }, 1000);
    clock.textContent = new Date().toLocaleTimeString();
}

// --------- Fullscreen Toggle ---------
if (fullscreenBtn && viewport) {
    fullscreenBtn.addEventListener("click", () => {
        if (!document.fullscreenElement) {
            viewport.requestFullscreen().catch((err) => alert(err.message));
        } else {
            document.exitFullscreen();
        }
    });
}

// --------- Live Stream Health Check ---------
function setLiveStatus(isLive, fps = 30) {
    if (isLive) {
        livePill.className = "live-pill";
        liveText.textContent = `Live ${fps}fps`;
    } else {
        livePill.className = "live-pill offline";
        liveText.textContent = "Offline";
    }
}

if (stream) {
    stream.addEventListener("error", () => {
        setLiveStatus(false);
        setTimeout(() => {
            stream.src = "/video?retry=" + Date.now();
        }, 2000);
    });
}

// Format seconds into "35s" or "1m 15s"
function formatUptime(seconds) {
    if (seconds < 60) return `${seconds}s`;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}m ${s}s`;
}

// Helper to format table numbers to two digits (e.g. "Table 1" -> "01")
function formatTableNum(name) {
    const num = name.replace(/\D/g, "");
    return num ? num.padStart(2, "0") : name;
}

// Maintain table DOM elements in memory so we don't recreate them every second
const tableNodes = {};

function updateFloorPlan(tables, seatsPerTable = 4) {
    // Sort tables by natural number order (Table 1, Table 2, ...)
    const tableEntries = Object.entries(tables).sort((a, b) => {
        const numA = parseInt(a[0].replace(/\D/g, "") || "0", 10);
        const numB = parseInt(b[0].replace(/\D/g, "") || "0", 10);
        return numA - numB;
    });

    if (fpTableCount) {
        fpTableCount.textContent = tableEntries.length;
    }

    tableEntries.forEach(([name, t]) => {
        const shapeType = t.shape === "round" ? "round" : "square";
        const isOccupied = !!t.occupied;
        const numText = formatTableNum(name);

        let node = tableNodes[name];

        if (!node) {
            // Create wrapper
            const wrapper = document.createElement("div");
            wrapper.className = "table-wrapper";

            // Create table shape
            const tableShape = document.createElement("div");
            tableShape.className = `table-shape ${shapeType} ${isOccupied ? "occupied" : "free"}`;

            const numSpan = document.createElement("span");
            numSpan.className = "table-num";
            numSpan.textContent = numText;

            const statusSpan = document.createElement("span");
            statusSpan.className = "table-status";

            const timeSpan = document.createElement("span");
            timeSpan.className = "table-time";

            tableShape.appendChild(numSpan);
            tableShape.appendChild(statusSpan);
            tableShape.appendChild(timeSpan);
            wrapper.appendChild(tableShape);

            // Create seat pills
            const seatEls = [];
            for (let i = 0; i < seatsPerTable; i++) {
                const pos = SEAT_POSITIONS[i % SEAT_POSITIONS.length];
                const seat = document.createElement("div");
                seat.className = `seat ${pos}`;
                wrapper.appendChild(seat);
                seatEls.push(seat);
            }

            floorBlueprint.appendChild(wrapper);

            node = {
                wrapper,
                tableShape,
                numSpan,
                statusSpan,
                timeSpan,
                seatEls,
                shapeType,
            };
            tableNodes[name] = node;
        }

        // Update classes & text
        node.tableShape.className = `table-shape ${node.shapeType} ${isOccupied ? "occupied" : "free"}`;
        node.numSpan.textContent = numText;

        if (isOccupied) {
            node.statusSpan.textContent = `${t.guests}/${seatsPerTable}`;
            node.timeSpan.textContent = `${t.seconds}s`;
            node.timeSpan.style.display = "block";
        } else {
            node.statusSpan.textContent = "Free";
            node.timeSpan.textContent = "";
            node.timeSpan.style.display = "none";
        }

        // Update seats
        const seatsTaken = t.seats_taken || [];
        node.seatEls.forEach((seatEl, i) => {
            if (seatsTaken[i]) {
                seatEl.classList.add("taken");
            } else {
                seatEl.classList.remove("taken");
            }
        });
    });
}

// --------- Fetch Stats from Server ---------
async function fetchStats() {
    try {
        const response = await fetch("/stats", { cache: "no-store" });
        if (!response.ok) {
            setLiveStatus(false);
            return;
        }

        const data = await response.json();
        if (!data.ready) return;

        setLiveStatus(true, data.processing_fps || 30);

        // Uptime & Header/Footer Info
        if (uptimeText) uptimeText.textContent = `Running: ${formatUptime(data.uptime || 0)}`;
        if (data.video) {
            const cleanVideoName = data.video.replace(/[-_]/g, " ");
            if (cameraVideoName) cameraVideoName.textContent = cleanVideoName;
            if (footerVideo) footerVideo.textContent = cleanVideoName;
        }
        if (data.address && footerAddress) {
            footerAddress.textContent = data.address;
        }

        // 1. Occupied Tables
        const occupied = data.occupied_tables || 0;
        const total = data.total_tables || 6;
        if (statOccupied) statOccupied.textContent = occupied;
        if (statTotalTables) statTotalTables.textContent = total;
        if (statWalkins) statWalkins.textContent = `${total - occupied} available for walk-ins`;

        // 2. Guests Seated
        const guests = data.guests || 0;
        const seats = data.seats || 24;
        const capacityPct = seats > 0 ? Math.round((guests / seats) * 100) : 0;
        if (statGuests) statGuests.textContent = guests;
        if (statTotalSeats) statTotalSeats.textContent = seats;
        if (statCapacity) statCapacity.textContent = `${capacityPct}% dining capacity`;

        // 3. Seat Utilization
        if (statUtilization) statUtilization.textContent = `${capacityPct}%`;
        if (statSeatsFree) statSeatsFree.textContent = `${Math.max(0, seats - guests)} seats free`;

        // 4. Average Seated Time
        const tables = data.tables || {};
        const occupiedList = Object.entries(tables).filter(([_, t]) => t.occupied);

        if (occupiedList.length > 0) {
            const avgSeconds = Math.round(
                occupiedList.reduce((acc, [_, t]) => acc + (t.seconds || 0), 0) / occupiedList.length
            );

            if (avgSeconds >= 60) {
                if (statAvgTime) statAvgTime.textContent = Math.floor(avgSeconds / 60);
                if (statAvgUnit) statAvgUnit.textContent = "min";
            } else {
                if (statAvgTime) statAvgTime.textContent = avgSeconds;
                if (statAvgUnit) statAvgUnit.textContent = "sec";
            }

            const longest = occupiedList.reduce(
                (max, curr) => ((curr[1].seconds || 0) > (max[1].seconds || 0) ? curr : max),
                occupiedList[0]
            );
            if (statLongest) {
                statLongest.textContent = `Longest: ${longest[0]} • ${longest[1].seconds || 0}s`;
            }
        } else {
            if (statAvgTime) statAvgTime.textContent = "0";
            if (statAvgUnit) statAvgUnit.textContent = "sec";
            if (statLongest) statLongest.textContent = "No occupied tables";
        }

        // 5. Floor Plan
        updateFloorPlan(tables, data.seats_per_table || 4);
    } catch (err) {
        setLiveStatus(false);
    }
}

// Start polling
setInterval(fetchStats, 1000);
fetchStats();
