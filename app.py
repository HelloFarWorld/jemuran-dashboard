import random
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from database import init_db, get_recent_logs, get_recent_events, insert_event, insert_sensor_log

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/logs")
def api_logs():
    logs = get_recent_logs()
    return jsonify(
        [
            {
                "id": r[0],
                "timestamp": r[1],
                "rain_value": r[2],
                "lux_value": r[3],
                "humidity": r[4],
                "servo_state": r[5],
            }
            for r in logs
        ]
    )


@app.route("/api/events")
def api_events():
    events = get_recent_events()
    return jsonify(
        [
            {
                "id": e[0],
                "timestamp": e[1],
                "event_type": e[2],
                "trigger": e[3],
                "description": e[4],
            }
            for e in events
        ]
    )


@app.route("/api/latest")
def api_latest():
    rows = get_recent_logs(limit=1)
    if not rows:
        return jsonify(None)
    r = rows[0]
    return jsonify(
        {
            "id": r[0],
            "timestamp": r[1],
            "rain_value": r[2],
            "lux_value": r[3],
            "humidity": r[4],
            "servo_state": r[5],
        }
    )


@app.route("/api/override", methods=["POST"])
def api_override():
    data = request.get_json()
    action = data.get("action", "AUTO") if data else "AUTO"
    insert_event("servo_override", "manual", f"Manual override: {action}")
    return jsonify({"status": "ok", "action": action})


@app.route("/api/demo/seed")
def api_demo_seed():
    now = datetime.now()
    for i in range(60):
        ts = now - timedelta(minutes=59 - i)
        rain = random.randint(100, 900)
        lux = random.randint(50, 900)
        hum = round(random.uniform(45, 85), 1)
        servo = "IN" if rain > 500 else "OUT"
        insert_sensor_log(rain, lux, hum, servo, timestamp=ts.strftime('%Y-%m-%d %H:%M:%S'))

    demo_events = [
        ("system", "auto", "Sensor online"),
        ("servo_in", "auto", "Rain detected, servo IN"),
        ("servo_out", "auto", "Sunny, servo OUT"),
        ("servo_override", "manual", "Manual override: IN"),
        ("servo_override", "manual", "Manual override: AUTO"),
    ]
    for ev in demo_events:
        insert_event(*ev)

    return jsonify({"seeded": 60})


@app.route("/api/health")
def api_health():
    logs_count = len(get_recent_logs(minutes=1440, limit=1))
    return jsonify({"status": "ok", "db": "connected" if logs_count is not None else "error"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
