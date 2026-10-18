import sqlite3
from datetime import datetime, timedelta

DB_PATH = "restaurant.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # Make the tables. IF NOT EXISTS makes it safe to run on every start.
    with get_connection() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id           INTEGER PRIMARY KEY,
                table_name   TEXT,
                started      TEXT,
                ended        TEXT,
                seconds      INTEGER,
                guests       INTEGER
            )""")
        db.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id               INTEGER PRIMARY KEY,
                time             TEXT,
                occupied_tables  INTEGER,
                guests           INTEGER
            )""")


def save_visit(table_name, seconds, guests, started=None, ended=None):
    # Save a finished visit to the database.
    now = datetime.now()
    if ended is None:
        ended = now.strftime("%Y-%m-%d %H:%M:%S")
    if started is None:
        started = (now - timedelta(seconds=int(seconds))).strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as db:
        db.execute("""
            INSERT INTO visits (table_name, started, ended, seconds, guests)
            VALUES (?, ?, ?, ?, ?)
        """, (table_name, started, ended, int(seconds), int(guests)))


def save_snapshot(occupied_tables, guests, timestamp=None):
    # Save a snapshot of the dining room (how busy it was at this moment).
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as db:
        db.execute("""
            INSERT INTO snapshots (time, occupied_tables, guests)
            VALUES (?, ?, ?)
        """, (timestamp, int(occupied_tables), int(guests)))


def get_history_data(range_str="5m"):
    # Read summary, per-table stats, recent visits, and time-series snapshots.
    init_db()
    with get_connection() as db:
        total_visits = db.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        total_snapshots = db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]

        # Table performance summary
        table_rows = db.execute("""
            SELECT table_name,
                   COUNT(*)               AS visits,
                   ROUND(AVG(seconds))    AS average_seconds,
                   MAX(seconds)           AS max_seconds,
                   ROUND(AVG(guests))     AS average_guests
            FROM visits
            GROUP BY table_name
            ORDER BY table_name
        """).fetchall()

        tables = []
        for row in table_rows:
            tables.append({
                "table_name": row["table_name"],
                "visits": row["visits"],
                "average_seconds": int(row["average_seconds"] or 0),
                "max_seconds": int(row["max_seconds"] or 0),
                "average_guests": int(row["average_guests"] or 0),
            })

        # Recent visits list
        recent_rows = db.execute("""
            SELECT ended, table_name, seconds, guests
            FROM visits
            ORDER BY id DESC
            LIMIT 20
        """).fetchall()

        recent_visits = []
        for row in recent_rows:
            recent_visits.append({
                "ended": row["ended"],
                "table_name": row["table_name"],
                "seconds": row["seconds"],
                "guests": row["guests"],
            })

        # Filter snapshots based on selected range
        now = datetime.now()
        since = None
        if range_str == "5m":
            since = (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        elif range_str == "1h":
            since = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        elif range_str == "24h":
            since = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        if since:
            snapshot_rows = db.execute("""
                SELECT time, occupied_tables, guests
                FROM snapshots
                WHERE time >= ?
                ORDER BY time ASC
            """, (since,)).fetchall()
        else:
            snapshot_rows = db.execute("""
                SELECT time, occupied_tables, guests
                FROM snapshots
                ORDER BY time ASC
            """).fetchall()

        snapshots = []
        for row in snapshot_rows:
            snapshots.append({
                "time": row["time"],
                "occupied_tables": row["occupied_tables"],
                "guests": row["guests"],
            })

    return {
        "total_visits": total_visits,
        "total_snapshots": total_snapshots,
        "tables": tables,
        "recent_visits": recent_visits,
        "snapshots": snapshots,
    }


# Ensure tables exist on import
init_db()
