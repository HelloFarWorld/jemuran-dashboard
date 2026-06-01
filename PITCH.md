# Jemuran Dashboard -- Software Pitch

---

## 1. The Problem

Indonesia is a tropical country. Rain can arrive in minutes. A clothesline left exposed means rewashing, delayed drying, or fabric damage from sudden downpours. Most households solve this reactively -- someone notices the rain, runs outside, and pulls the clothes in. That requires a person to be home, awake, and paying attention.

---

## 2. What We Built

Jemuran Dashboard is the software layer of an automated clothesline system. It connects physical sensors on an Arduino to a live web dashboard, giving users real-time visibility into weather conditions at their clothesline.

**Three-word summary:** Sense. Decide. Display.

- Sensors detect rain, light, and humidity
- Arduino decides whether to retract or extend the clothesline
- The dashboard shows everything -- current state, history, and manual controls

---

## 3. System Architecture

```
 ARDUINO                    LAPTOP                     BROWSER
+------------------+       +------------------------+  +------------------+
| Rain sensor (A0) |       |  serial_reader.py       |  |  Dashboard UI    |
| Lux sensor  (A1) |--USB->|  (reads JSON, writes DB)|  |  (Chart.js,      |
| DHT11       (D2) |       |                         |  |   auto-refresh   |
| Servo motor (D9) |       |  app.py                 |  |   3s interval)   |
+------------------+       |  (Flask REST API)       |<-|                  |
                           |  (SQLite database)       |  +------------------+
                           +------------------------+
```

**Three independent components running simultaneously:**

| Component | Language | Role |
|-----------|----------|------|
| Serial Reader | Python (pyserial) | Bridge between Arduino USB and SQLite database |
| REST API Server | Python (Flask) | Serves data to the browser via HTTP endpoints |
| Dashboard UI | HTML/CSS/JS (Chart.js) | Real-time visualization, polling every 3 seconds |

Each can be started, stopped, or restarted independently without affecting the others.

---

## 4. Data Flow (Step by Step)

1. Arduino reads four sensors every 2 seconds
2. Arduino prints one JSON line via USB Serial
3. `serial_reader.py` receives the line, parses JSON, inserts a row into SQLite
4. `app.py` exposes the data through 7 REST endpoints
5. The browser polls `/api/latest`, `/api/logs`, `/api/events` every 3 seconds
6. The dashboard re-renders: status banner, ring gauge, progress bars, chart, timeline

---

## 5. Key Technical Decisions

### Why SQLite?
- Zero configuration. No database server to install.
- Single file database (`jemuran.db`). Portable, backup-friendly.
- Reads are indexed by timestamp. 60-minute window query returns instantly.
- Perfect for single-machine deployment. This is not a multi-tenant cloud service.

### Why Flask + Vanilla JS (no React/framework)?
- Deployment target is a laptop, not a data center.
- One command to run: `python app.py`.
- No `npm install`, no `node_modules`, no build step.
- Dashboard is a single HTML file. Anyone can open and read it.
- Chart.js via CDN -- no dependency to manage.

### Why two separate processes (serial_reader.py + app.py)?
- Separation of concerns. Serial reader can crash or restart without taking the dashboard down.
- The dashboard works without Arduino (demo mode via `/api/demo/seed`).
- Each process is debuggable independently. Log output is not mixed.

### Why polling (not WebSockets)?
- 3-second interval is sufficient for this use case. Weather does not change in milliseconds.
- Simpler error handling. A failed fetch shows "Offline" -- no reconnection logic needed.
- No additional library dependencies.

---

## 6. Dashboard UI Design Rationale

The UI follows a "glanceable HMI" pattern -- borrowed from industrial control panels and Grafana monitoring dashboards. The principle: **a user should understand the system state in under 2 seconds, without scrolling.**

### Layout Hierarchy

```
+----------------------------------------------------+
| TOPBAR: Title, connection status, last update time  |  <- Always visible
+------+---------------------------------------------+
| LEFT | STATUS BANNER: safe/warning/danger           |  <- Immediate status
|      +---------------------------------------------+
| Ring | Rain [============      ] 320 / 1023         |  <- Quick metrics
| Gauge| Lux  [==============    ] 680 / 1023 lx      |
| (Rain| Hum  [========          ] 55%                |
| val) +---------------------------------------------+
|      | CHART: 1-hour history (Rain, Lux, Humidity)  |  <- Trend analysis
| Servo+-----------------------+---------------------+
| State| EVENT TIMELINE        | CONTROL PANEL       |  <- Logs + actions
| IN/  | (last 8 events)       | (override buttons)  |
| OUT  |                       | (threshold slider)  |
+------+-----------------------+---------------------+
```

### Color System (Grafana-inspired, accessibility-conscious)

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Safe | Green | `#73bf69` | Status banner (rain < 400), servo OUT |
| Warning | Amber | `#e5a43c` | Status banner (humidity > 75) |
| Danger | Red | `#e24d4c` | Status banner (rain >= 400), servo IN |
| Rain metric | Blue | `#5794f2` | Ring gauge, progress bar, chart line |
| Lux metric | Amber | `#e5a43c` | Progress bar, chart line |
| Humidity metric | Green | `#73bf69` | Progress bar, chart line (dashed) |

Colors are distinct enough to be told apart at a glance, with sufficient contrast ratios for readability. No color pair is the sole differentiator -- text labels and icons always accompany.

### State Logic

| Sensor Reading | Banner | Meaning |
|---------------|--------|---------|
| Rain < 400, Hum <= 75% | Green: Cuaca Aman | Safe. Clothesline extended. |
| Rain < 400, Hum > 75% | Amber: Kelembapan Tinggi | Warning. High humidity. |
| Rain >= 400 | Red: Hujan Terdeteksi | Danger. Clothesline retracted. |

Rain takes priority over humidity. If it is raining, humidity is not shown -- the user needs to know about the rain first.

---

## 7. REST API Design

7 endpoints. All responses are JSON. No authentication (local network only).

```
GET  /                  Dashboard HTML page
GET  /api/latest        Most recent sensor reading (or null)
GET  /api/logs          Last 60 minutes of sensor data
GET  /api/events        Last 20 events
GET  /api/health        Server + database status check
POST /api/override      Manual servo control {"action": "IN"|"OUT"|"AUTO"}
GET  /api/demo/seed     Generate 60 rows of test data
```

Design principles:
- Read operations are GET, write operations are POST
- `/api/latest` is separate from `/api/logs` -- the dashboard needs one row fast, not 60 rows unnecessarily
- `/api/override` accepts three actions only, validated at the database layer with CHECK constraints
- `/api/demo/seed` is intentionally idempotent and additive -- it can be called multiple times

---

## 8. Database Design

Two tables. Minimal. Each row has a purpose.

```
sensor_logs:  id | timestamp | rain_value | lux_value | humidity | servo_state
events:       id | timestamp | event_type | trigger   | description
```

Design decisions:
- Timestamps are explicit (Python `datetime.now()`) rather than SQLite `CURRENT_TIMESTAMP` -- avoids UTC/local mismatch
- `servo_state` has a CHECK constraint (`'IN'` or `'OUT'`) -- invalid data never enters the database
- `events.trigger` has a CHECK constraint (`'auto'` or `'manual'`) -- every event is attributable
- No foreign keys between tables. They serve different purposes and are queried independently.

---

## 9. Error Handling Strategy

| Failure | Behavior |
|---------|----------|
| Arduino disconnected | Serial reader retries connection every 3 seconds. Last data remains visible on dashboard. |
| Serial reader process dies | Dashboard continues showing last data. Connection indicator turns red. |
| Flask server dies | Browser shows "Offline" badge. Page does not crash (fetch errors are caught). |
| Database corrupted | Delete `jemuran.db`, restart. Tables are auto-created. |
| Invalid JSON from Arduino | Serial reader logs a warning, skips the line, continues. |
| Port already in use | Flask fails fast with clear error. User changes port in `app.py`. |

The system degrades gracefully. No single failure takes everything down.

---

## 10. What This Software Demonstrates

For a technical audience:
- Multi-process Python architecture (serial I/O + web server)
- Clean separation of data layer (database.py) from transport layer (serial_reader) from presentation layer (Flask + frontend)
- SQLite with explicit timestamp management and CHECK constraints
- REST API design with 7 focused endpoints
- Real-time dashboard with sampled chart data for legibility
- Graceful degradation and error recovery patterns

For a general audience:
- Real-time weather monitoring for an automated household system
- Live dashboard accessible from any device on the home network
- Manual override controls with instant feedback
- One hour of scrollable history
- Works with or without hardware connected (demo mode)

---

## 11. File Count and Scale

| Metric | Count |
|--------|-------|
| Python files | 3 (`app.py`, `serial_reader.py`, `database.py`) |
| HTML template | 1 (`templates/index.html`) |
| Configuration | 1 (`requirements.txt`) |
| Total Python lines | ~250 |
| Total frontend lines | ~450 |
| API endpoints | 7 |
| Database tables | 2 |
| External dependencies | 3 (flask, flask-cors, pyserial) |
| Frontend dependencies | 2 (Chart.js CDN, Inter font CDN) |

---

## 12. Future Extensions (Not Implemented)

These are documented to show architectural awareness, not scope creep:

- **WiFi module (ESP32)**: Replace USB serial with HTTP POST from the microcontroller. Eliminates the serial reader process.
- **Camera snapshot**: Periodic photo of the clothesline area embedded in the dashboard.
- **Telegram/WhatsApp notifications**: Alert when rain is detected and the user is not home.
- **Multi-user access**: Authentication layer if exposed beyond the local network.
- **Data export**: CSV download of historical sensor data for analysis.
