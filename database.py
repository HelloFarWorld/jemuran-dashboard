import sqlite3
from datetime import datetime, timedelta

DB = "jemuran.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        """CREATE TABLE IF NOT EXISTS sensor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            rain_value INTEGER NOT NULL,
            lux_value INTEGER NOT NULL,
            humidity REAL NOT NULL,
            servo_state TEXT NOT NULL CHECK (servo_state IN ('IN', 'OUT'))
        )"""
    )

    cur.execute(
        """CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            event_type TEXT NOT NULL,
            trigger TEXT NOT NULL CHECK (trigger IN ('auto', 'manual')),
            description TEXT
        )"""
    )

    conn.commit()
    conn.close()


def insert_sensor_log(rain, lux, hum, servo, timestamp=None):
    conn = sqlite3.connect(DB)
    ts = timestamp if timestamp else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        "INSERT INTO sensor_logs (timestamp, rain_value, lux_value, humidity, servo_state) "
        "VALUES (?, ?, ?, ?, ?)",
        (ts, rain, lux, hum, servo),
    )
    conn.commit()
    conn.close()


def get_recent_logs(minutes=60, limit=None):
    since = (datetime.now() - timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB)
    query = (
        "SELECT * FROM sensor_logs WHERE timestamp >= ? ORDER BY timestamp DESC"
    )
    params = [since]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def insert_event(type_, trigger, desc):
    conn = sqlite3.connect(DB)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        "INSERT INTO events (timestamp, event_type, trigger, description) "
        "VALUES (?, ?, ?, ?)",
        (ts, type_, trigger, desc),
    )
    conn.commit()
    conn.close()


def get_recent_events(limit=20):
    conn = sqlite3.connect(DB)
    rows = (
        conn.execute(
            "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        .fetchall()
    )
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
