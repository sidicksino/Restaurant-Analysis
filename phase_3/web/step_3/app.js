// ========================================================
// TablePulse Step 3: Live Floor & SQLite History Dashboard
// ========================================================

const stream = document.getElementById("stream");
const livePill = document.getElementById("live-pill");
const liveText = document.getElementById("live-text");
const uptimeText = document.getElementById("uptime-text");
const clock = document.getElementById("clock");
const fullscreenBtn = document.getElementById("fullscreen");
const viewport = document.getElementById("viewport");

// Navigation & Views
const tabFloor = document.getElementById("tab-floor");
const tabHistory = document.getElementById("tab-history");
const viewFloor = document.getElementById("view-floor");
const viewHistory = document.getElementById("view-history");

// Header / Footer elements
const cameraVideoName = document.getElementById("camera-video-name");
const footerVideo = document.getElementById("footer-video");
const footerAddress = document.getElementById("footer-address");

// Stat card elements (Live Floor)
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

// History elements
const historySummary = document.getElementById("history-summary");
const rangeSelector = document.getElementById("range-selector");
const occupiedChartRangeLabel = document.getElementById("occupied-chart-range-label");

const chartGuests = document.getElementById("chart-guests");
const chartTables = document.getElementById("chart-tables");
const chartXStart = document.getElementById("chart-x-start");
const chartTablesXStart = document.getElementById("chart-tables-x-start");
const tooltipGuests = document.getElementById("tooltip-guests");
const tooltipTables = document.getElementById("tooltip-tables");

const tableSummaryBody = document.getElementById("table-summary-body");
const tableRecentBody = document.getElementById("table-recent-body");

let currentRange = "5m";
let currentView = "floor";
let historySnapshotsData = [];

// Seat positions around a table (0=Right, 1=Bottom, 2=Left, 3=Top)
const SEAT_POSITIONS = ["right", "bottom", "left", "top"];

// Maintain floor table DOM elements in memory to prevent flicker
const tableNodes = {};

// --------- Navigation Tab Switching ---------
function setView(viewName) {
    currentView = viewName;
    if (viewName === "history") {
        tabFloor.classList.remove("active");
        tabHistory.classList.add("active");
        viewFloor.style.display = "none";
        viewHistory.style.display = "flex";
        fetchHistory();
    } else {
        tabHistory.classList.remove("active");
        tabFloor.classList.add("active");
        viewHistory.style.display = "none";
        viewFloor.style.display = "grid";
    }
}

function handleHashChange() {
    const hash = window.location.hash.toLowerCase();
    if (hash === "#history") {
        setView("history");
    } else {
        setView("floor");
    }
}

window.addEventListener("hashchange", handleHashChange);
handleHashChange();

tabFloor.addEventListener("click", (e) => {
    e.preventDefault();
    window.location.hash = "floor";
});

tabHistory.addEventListener("click", (e) => {
    e.preventDefault();
    window.location.hash = "history";
});

// --------- Clock in Camera Bar ---------
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

function formatUptime(seconds) {
    if (seconds < 60) return `${seconds}s`;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}m ${s}s`;
}

function formatDuration(seconds) {
    if (seconds < 60) return `${seconds}s`;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}m ${s}s`;
}

function formatTableNum(name) {
    const num = name.replace(/\D/g, "");
    return num ? num.padStart(2, "0") : name;
}

// --------- Floor Plan DOM Rendering ---------
function updateFloorPlan(tables, seatsPerTable = 4) {
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
            const wrapper = document.createElement("div");
            wrapper.className = "table-wrapper";

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

// --------- Polling Live Stats (/stats) ---------
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

        if (uptimeText) uptimeText.textContent = `Running: ${formatUptime(data.uptime || 0)}`;
        if (data.video) {
            const cleanVideoName = data.video.replace(/[-_]/g, " ");
            if (cameraVideoName) cameraVideoName.textContent = cleanVideoName;
            if (footerVideo) footerVideo.textContent = cleanVideoName;
        }
        if (data.address && footerAddress) {
            footerAddress.textContent = data.address;
        }

        // Live Floor metrics
        const occupied = data.occupied_tables || 0;
        const total = data.total_tables || 6;
        if (statOccupied) statOccupied.textContent = occupied;
        if (statTotalTables) statTotalTables.textContent = total;
        if (statWalkins) statWalkins.textContent = `${total - occupied} available for walk-ins`;

        const guests = data.guests || 0;
        const seats = data.seats || 24;
        const capacityPct = seats > 0 ? Math.round((guests / seats) * 100) : 0;
        if (statGuests) statGuests.textContent = guests;
        if (statTotalSeats) statTotalSeats.textContent = seats;
        if (statCapacity) statCapacity.textContent = `${capacityPct}% dining capacity`;

        if (statUtilization) statUtilization.textContent = `${capacityPct}%`;
        if (statSeatsFree) statSeatsFree.textContent = `${Math.max(0, seats - guests)} seats free`;

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

        updateFloorPlan(tables, data.seats_per_table || 4);
    } catch (err) {
        setLiveStatus(false);
    }
}

// --------- History Range Buttons ---------
if (rangeSelector) {
    rangeSelector.querySelectorAll(".range-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            rangeSelector.querySelectorAll(".range-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            currentRange = btn.getAttribute("data-range");

            const labels = {
                "5m": "Last 5 min",
                "1h": "Last 1 hour",
                "24h": "Last 24 hours",
                all: "All saved visits",
            };
            if (occupiedChartRangeLabel) {
                occupiedChartRangeLabel.textContent = labels[currentRange] || "Last 5 min";
            }

            const xStartLabels = {
                "5m": "5m 0s ago",
                "1h": "1h 0m ago",
                "24h": "24h ago",
                all: "Start",
            };
            if (chartXStart) chartXStart.textContent = xStartLabels[currentRange] || "5m 0s ago";
            if (chartTablesXStart) chartTablesXStart.textContent = xStartLabels[currentRange] || "5m 0s ago";

            fetchHistory();
        });
    });
}

// --------- Polling History (/history) ---------
async function fetchHistory() {
    try {
        const response = await fetch(`/history?range=${currentRange}`, { cache: "no-store" });
        if (!response.ok) return;

        const data = await response.json();

        // 1. Header summary line
        if (historySummary) {
            historySummary.textContent = `Saved in the database: ${data.total_visits} visits and ${data.total_snapshots} snapshots`;
        }

        // 2. Tables summary
        renderTableSummary(data.tables || []);

        // 3. Recent visits
        renderRecentVisits(data.recent_visits || []);

        // 4. Render SVG Charts
        historySnapshotsData = data.snapshots || [];
        renderChart(chartGuests, historySnapshotsData, "guests", 4, tooltipGuests);
        renderChart(chartTables, historySnapshotsData, "occupied_tables", 6, tooltipTables);
    } catch (err) {
        console.error("Failed to fetch history:", err);
    }
}

function renderTableSummary(tables) {
    if (!tableSummaryBody) return;
    if (tables.length === 0) {
        tableSummaryBody.innerHTML = `<tr><td colspan="5" class="empty-state">No visits recorded yet.</td></tr>`;
        return;
    }

    tableSummaryBody.innerHTML = tables
        .map(
            (t) => `
        <tr>
            <td><strong>${t.table_name}</strong></td>
            <td>${t.visits}</td>
            <td>${formatDuration(t.average_seconds)}</td>
            <td>${formatDuration(t.max_seconds)}</td>
            <td>${t.average_guests}</td>
        </tr>
    `
        )
        .join("");
}

function renderRecentVisits(visits) {
    if (!tableRecentBody) return;
    if (visits.length === 0) {
        tableRecentBody.innerHTML = `<tr><td colspan="2" class="empty-state">No completed visits recorded yet.</td></tr>`;
        return;
    }

    tableRecentBody.innerHTML = visits
        .map(
            (v) => `
        <tr>
            <td>${v.ended}</td>
            <td><strong>${v.table_name}</strong></td>
        </tr>
    `
        )
        .join("");
}

// --------- Interactive SVG Area & Step Chart Renderer ---------
function renderChart(svgEl, snapshots, key, defaultMaxY, tooltipEl) {
    if (!svgEl) return;

    const width = 540;
    const height = 180;
    const paddingLeft = 32;
    const paddingRight = 36;
    const paddingTop = 20;
    const paddingBottom = 24;

    const plotW = width - paddingLeft - paddingRight;
    const plotH = height - paddingTop - paddingBottom;

    // Calculate maximum Y value
    const maxVal = snapshots.reduce((m, d) => Math.max(m, d[key] || 0), defaultMaxY);
    const maxY = Math.max(maxVal, 2);

    // SVG grid lines & Y labels (3 horizontal ticks: 0, mid, top)
    const midY = maxY / 2;
    const ticks = [
        { val: 0, y: paddingTop + plotH },
        { val: Number.isInteger(midY) ? midY : midY.toFixed(1), y: paddingTop + plotH / 2 },
        { val: maxY, y: paddingTop },
    ];

    let gridSvg = "";
    ticks.forEach((tick) => {
        gridSvg += `
            <line x1="${paddingLeft}" y1="${tick.y}" x2="${width - paddingRight + 4}" y2="${tick.y}" 
                  stroke="rgba(0,0,0,0.06)" stroke-width="1" stroke-dasharray="3,3" />
            <text x="${paddingLeft - 8}" y="${tick.y + 3}" text-anchor="end" 
                  font-size="10" font-family="JetBrains Mono" fill="#887364">${tick.val}</text>
        `;
    });

    if (snapshots.length < 2) {
        // Draw baseline at 0
        const zeroY = paddingTop + plotH;
        svgEl.innerHTML = `
            ${gridSvg}
            <line x1="${paddingLeft}" y1="${zeroY}" x2="${paddingLeft + plotW}" y2="${zeroY}" 
                  stroke="#8d4b00" stroke-width="2" />
            <circle cx="${paddingLeft + plotW}" cy="${zeroY}" r="3.5" fill="#8d4b00" />
            <text x="${paddingLeft + plotW + 8}" y="${zeroY + 4}" font-size="11" font-weight="700" 
                  font-family="JetBrains Mono" fill="#8d4b00">• 0</text>
        `;
        return;
    }

    // Map data points into coordinates
    const points = snapshots.map((d, i) => {
        const x = paddingLeft + (i / (snapshots.length - 1)) * plotW;
        const y = paddingTop + plotH - ((d[key] || 0) / maxY) * plotH;
        return { x, y, val: d[key] || 0, time: d.time || "" };
    });

    // Generate stepped line and closed area fill
    let areaPath = `M ${points[0].x} ${paddingTop + plotH} L ${points[0].x} ${points[0].y}`;
    let strokePath = `M ${points[0].x} ${points[0].y}`;

    for (let i = 1; i < points.length; i++) {
        const prev = points[i - 1];
        const curr = points[i];
        // Horizontal step then vertical step
        areaPath += ` L ${curr.x} ${prev.y} L ${curr.x} ${curr.y}`;
        strokePath += ` L ${curr.x} ${prev.y} L ${curr.x} ${curr.y}`;
    }

    const lastPt = points[points.length - 1];
    areaPath += ` L ${lastPt.x} ${paddingTop + plotH} Z`;

    const markerSvg = `
        <circle cx="${lastPt.x}" cy="${lastPt.y}" r="3.5" fill="#8d4b00" />
        <text x="${lastPt.x + 8}" y="${lastPt.y + 4}" font-size="11" font-weight="700" 
              font-family="JetBrains Mono" fill="#8d4b00">• ${lastPt.val}</text>
    `;

    svgEl.innerHTML = `
        ${gridSvg}
        <path d="${areaPath}" fill="rgba(141, 75, 0, 0.08)" />
        <path d="${strokePath}" fill="none" stroke="#8d4b00" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        ${markerSvg}
    `;

    // Interactive hover tooltip
    if (tooltipEl) {
        svgEl.onmousemove = (e) => {
            const rect = svgEl.getBoundingClientRect();
            const mouseX = ((e.clientX - rect.left) / rect.width) * width;

            // Find closest data point
            let closest = points[0];
            let minDist = Math.abs(points[0].x - mouseX);
            for (let i = 1; i < points.length; i++) {
                const dist = Math.abs(points[i].x - mouseX);
                if (dist < minDist) {
                    minDist = dist;
                    closest = points[i];
                }
            }

            const timeParts = closest.time.split(" ");
            const timeOnly = timeParts.length > 1 ? timeParts[1] : closest.time;
            const unit = key === "guests" ? "guests" : "occupied";
            tooltipEl.textContent = `${closest.val} ${unit} • ${timeOnly}`;

            const percentX = (closest.x / width) * 100;
            const percentY = (closest.y / height) * 100;

            tooltipEl.style.left = `${percentX}%`;
            tooltipEl.style.top = `${percentY}%`;
            tooltipEl.style.opacity = "1";
        };

        svgEl.onmouseleave = () => {
            tooltipEl.style.opacity = "0";
        };
    }
}

// --------- Intervals ---------
setInterval(fetchStats, 1000);
fetchStats();

setInterval(() => {
    if (currentView === "history") {
        fetchHistory();
    }
}, 3000);
