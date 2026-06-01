# Jemuran Dashboard

Real-time monitoring dashboard for an automated clothesline system. Reads sensor data from Arduino over USB serial, stores it in SQLite, and displays live metrics through a browser-based UI. Refresh interval: 3 seconds.

---

## Quickstart (Basic Hardware)

### What you need

- 1x Arduino Uno/Nano/Mega
- 1x Rain sensor (analog)
- 1x LDR light sensor (analog)
- 1x DHT11 humidity sensor (digital)
- 1x Servo motor (SG90 or similar)
- 1x USB cable (Arduino to laptop)
- 1x Laptop with Python 3.8+

### Step 1: Wire the hardware

```
Rain sensor   → Arduino A0
LDR sensor    → Arduino A1
DHT11 data    → Arduino D2
Servo signal  → Arduino D9
All VCC → 5V, All GND → GND
```

### Step 2: Upload the Arduino sketch

Open Arduino IDE, paste the sketch from the "Arduino Sketch" section below, select your board and COM port, then click Upload.

**Verify:** Open Serial Monitor (9600 baud). You should see JSON lines output every 2 seconds:
```
{"rain":320,"lux":680,"humidity":55.2,"servo":"OUT"}
```

**Close Serial Monitor before proceeding** — the serial port can only be used by one program at a time.

### Step 3: Install Python dependencies

```bash
cd jemuran-dashboard
pip install -r requirements.txt
```

### Step 4: Find your COM port

- **Windows:** Open Device Manager > "Ports (COM & LPT)". Look for "Arduino Uno" — note the COM number (e.g. `COM3`).
- **Linux:** `ls /dev/ttyUSB*` or `ls /dev/ttyACM*` (e.g. `/dev/ttyUSB0`).
- **Mac:** `ls /dev/cu.usbmodem*` (e.g. `/dev/cu.usbmodem14101`).

### Step 5: Run both programs

Open **two terminals** in the `jemuran-dashboard` folder.

**Terminal 1 — Serial reader (reads Arduino, writes database):**
```bash
python serial_reader.py --port COM3
```
Replace `COM3` with your actual port. You should see:
```
[serial_reader] Database ready.
[serial_reader] Connecting to Arduino on COM3 @ 9600 baud ...
[serial_reader] Connected. Waiting for data ...
[serial_reader] <- {"rain":320,"lux":680,"humidity":55.2,"servo":"OUT"}
[serial_reader] OK stored | rain=320 lux=680 hum=55.2 servo=OUT
```

**Terminal 2 — Flask server (serves dashboard and API):**
```bash
python app.py
```
You should see:
```
 * Running on http://0.0.0.0:5000
```

### Step 6: Open the dashboard

Open `http://localhost:5000` in any browser on the same laptop.

To view from another device (phone, tablet) on the same WiFi network, use the laptop's IP address:
```
http://192.168.1.10:5000
```
Find your IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac).

### Step 7: Stop the system

Press **Ctrl+C** in both terminals.

---

### What if I don't have Arduino hardware yet?

No problem. The dashboard works with demo data:

```bash
python app.py                         # Terminal 1
```
Then visit `http://localhost:5000/api/demo/seed` in a browser. This fills the database with 60 minutes of synthetic data. Open `http://localhost:5000` to see the dashboard in action.

---

## Project Structure

```
jemuran-dashboard/
├── app.py              Flask server, REST API, demo data generator
├── serial_reader.py    Arduino USB serial reader and database writer
├── database.py         SQLite schema, init, and query functions
├── requirements.txt    Python dependencies
├── templates/
│   └── index.html      Browser dashboard (HTML/CSS/JS + Chart.js)
├── static/             Static assets (reserved for future use)
└── jemuran.db          SQLite database (auto-created on first run)
```

## Requirements

- Python 3.8+
- Arduino board with sensors (optional; dashboard works with demo data)
- Dependencies listed in `requirements.txt`:
  - `flask` — web server and API
  - `flask-cors` — cross-origin request support
  - `pyserial` — USB serial communication with Arduino

## Installation

```bash
cd jemuran-dashboard
pip install -r requirements.txt
```

Initialize the database:

```bash
python database.py
```

This creates `jemuran.db` with the required tables. The database file is stored in the project root and is auto-created by `app.py` and `serial_reader.py` on startup if missing.

## Running the System

The system has two independent processes that can run together or separately.

### 1. Flask Server (Dashboard + API)

```bash
python app.py
```

Starts on `http://localhost:5000`. Opens the dashboard UI at `/` and serves all API endpoints. The database is initialized automatically on startup.

### 2. Serial Reader (Arduino Data Ingestion)

```bash
python serial_reader.py --port COM3 --baud 9600
```

Arguments:

| Argument | Default | Description |
|----------|---------|-------------|
| `--port` | `COM3` | Serial port. On Linux/Mac use `/dev/ttyUSB0` or `/dev/ttyACM0`. |
| `--baud` | `9600` | Baud rate. Must match the Arduino sketch. |

The reader will:
1. Initialize the database if not already done.
2. Attempt to connect to the serial port. Retries every 3 seconds on failure.
3. Read one JSON line at a time from Arduino.
4. Parse and insert each reading into `sensor_logs`.
5. Log a `system` event on connect and disconnect.
6. Print every line received and a confirmation of each stored record.
7. On Ctrl+C, close the serial port gracefully and print a line/error summary.

### Running Both Together

Terminal 1:
```bash
python app.py
```

Terminal 2:
```bash
python serial_reader.py --port COM3
```

Open `http://localhost:5000` in any browser.

## Testing Without Arduino (Demo Mode)

The demo seed endpoint populates the database with 60 minutes of synthetic sensor data and 5 sample events. This lets you test the full dashboard with no hardware connected.

```bash
python app.py
```

Then visit `http://localhost:5000/api/demo/seed` in a browser, or:

```bash
curl http://localhost:5000/api/demo/seed
```

Returns `{"seeded": 60}`. Refresh the dashboard to see the data.

## Arduino Integration

### Wiring

Connect the following to your Arduino board:

| Sensor | Arduino Pin | Notes |
|--------|-------------|-------|
| Rain sensor | A0 | Analog output, range 0-1023 |
| LDR / Lux sensor | A1 | Analog output, range 0-1023 |
| DHT11 / DHT22 | Digital 2 | Humidity and temperature |
| Servo motor | Digital 9 | Pulls clothesline in/out |

### Arduino Sketch Requirements

The Arduino sketch must output exactly one JSON object per line via `Serial.println()`. The serial reader expects this format:

```json
{"rain": 320, "lux": 680, "humidity": 55.2, "servo": "OUT"}
```

Field specification:

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `rain` | Integer | 0-1023 | Rain sensor reading. Higher = more rain detected. |
| `lux` | Integer | 0-1023 | Light intensity from LDR/photoresistor. |
| `humidity` | Float | 0-100 | Relative humidity percentage from DHT sensor. |
| `servo` | String | `"IN"` or `"OUT"` | Current servo position. `"IN"` = clothesline retracted (rain protection). `"OUT"` = clothesline extended. |

The serial reader auto-detects the servo state from Arduino. The decision logic (when to move the servo IN or OUT) should run on the Arduino itself for low-latency response to rain. The dashboard and `/api/override` endpoint are for manual override and monitoring.

### Example Arduino Sketch

```cpp
#include <DHT.h>
#include <Servo.h>

#define RAIN_PIN  A0
#define LUX_PIN   A1
#define DHTPIN    2
#define SERVO_PIN 9
#define DHTTYPE   DHT11

DHT dht(DHTPIN, DHTTYPE);
Servo servo;

void setup() {
    Serial.begin(9600);
    dht.begin();
    servo.attach(SERVO_PIN);
}

void loop() {
    int rain = analogRead(RAIN_PIN);
    int lux  = analogRead(LUX_PIN);
    float hum = dht.readHumidity();

    // Decide servo position based on rain threshold
    if (rain > 400) {
        servo.write(0);   // IN
    } else {
        servo.write(180); // OUT
    }

    // Send one JSON line to serial
    Serial.print("{\"rain\":");
    Serial.print(rain);
    Serial.print(",\"lux\":");
    Serial.print(lux);
    Serial.print(",\"humidity\":");
    Serial.print(hum);
    Serial.print(",\"servo\":\"");
    Serial.print(rain > 400 ? "IN" : "OUT");
    Serial.println("\"}");

    delay(2000);
}
```

## REST API Reference

Base URL: `http://localhost:5000`

### GET /

Returns the dashboard HTML page. Content-Type: `text/html`.

### GET /api/latest

Returns the most recent sensor reading, or `null` if the database is empty.

**Response 200 (with data):**
```json
{
    "id": 127,
    "timestamp": "2026-05-30 14:32:00",
    "rain_value": 320,
    "lux_value": 680,
    "humidity": 55.2,
    "servo_state": "OUT"
}
```

**Response 200 (empty database):**
```json
null
```

### GET /api/logs

Returns sensor readings from the last 60 minutes, ordered newest first. Maximum 60 entries (1 per minute from demo seed; variable rate from Arduino).

**Response 200:**
```json
[
    {
        "id": 127,
        "timestamp": "2026-05-30 14:32:00",
        "rain_value": 320,
        "lux_value": 680,
        "humidity": 55.2,
        "servo_state": "OUT"
    }
]
```

### GET /api/events

Returns the 20 most recent events, ordered newest first.

**Response 200:**
```json
[
    {
        "id": 15,
        "timestamp": "2026-05-30 14:30:05",
        "event_type": "servo_override",
        "trigger": "manual",
        "description": "Manual override: IN"
    }
]
```

### GET /api/health

Health check endpoint for monitoring and debugging.

**Response 200:**
```json
{"status": "ok", "db": "connected"}
```

### POST /api/override

Sends a manual servo override command. Logs the action as an event with `trigger: "manual"` and `event_type: "servo_override"`.

**Request:**
```json
{"action": "IN"}
{"action": "OUT"}
{"action": "AUTO"}
```

Valid actions:

| Action | Meaning |
|--------|---------|
| `"IN"` | Retract clothesline |
| `"OUT"` | Extend clothesline |
| `"AUTO"` | Return to automatic/sensor-driven mode |

**Response 200:**
```json
{"status": "ok", "action": "IN"}
```

**curl example:**
```bash
curl -X POST http://localhost:5000/api/override \
     -H "Content-Type: application/json" \
     -d '{"action":"IN"}'
```

### GET /api/demo/seed

Generates 60 rows of synthetic sensor data (1 per minute, counting backwards from now) and 5 sample events. Used for testing the dashboard without Arduino hardware.

**Response 200:**
```json
{"seeded": 60}
```

## Database Schema

SQLite database file: `jemuran.db`. Auto-created in the project root. Two tables:

### Table: `sensor_logs`

Stores every sensor reading received from Arduino.

```sql
CREATE TABLE sensor_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   DATETIME NOT NULL,
    rain_value  INTEGER NOT NULL,
    lux_value   INTEGER NOT NULL,
    humidity    REAL NOT NULL,
    servo_state TEXT NOT NULL CHECK (servo_state IN ('IN', 'OUT'))
);
```

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTO | Auto-increment row ID |
| `timestamp` | DATETIME | NOT NULL | `YYYY-MM-DD HH:MM:SS` local time, set explicitly |
| `rain_value` | INTEGER | NOT NULL | Rain sensor reading, 0-1023 |
| `lux_value` | INTEGER | NOT NULL | Light sensor reading, 0-1023 |
| `humidity` | REAL | NOT NULL | Relative humidity, 0-100 |
| `servo_state` | TEXT | NOT NULL | `'IN'` or `'OUT'` |

### Table: `events`

Logs all system events, state changes, and manual overrides.

```sql
CREATE TABLE events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   DATETIME NOT NULL,
    event_type  TEXT NOT NULL,
    trigger     TEXT NOT NULL CHECK (trigger IN ('auto', 'manual')),
    description TEXT
);
```

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTO | Auto-increment row ID |
| `timestamp` | DATETIME | NOT NULL | `YYYY-MM-DD HH:MM:SS` local time |
| `event_type` | TEXT | NOT NULL | Event category (e.g. `system`, `servo_in`, `servo_out`, `servo_override`) |
| `trigger` | TEXT | NOT NULL | `'auto'` (sensor-driven) or `'manual'` (user override) |
| `description` | TEXT | NULLABLE | Human-readable event detail |

## Python Module Reference

### `database.py`

Core data layer. All functions use explicit local timestamps (`YYYY-MM-DD HH:MM:SS`) for compatibility with SQLite.

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `init_db()` | none | none | Creates tables if they do not exist. Idempotent. |
| `insert_sensor_log(rain, lux, hum, servo, timestamp=None)` | `rain`: int, `lux`: int, `hum`: float, `servo`: str (`"IN"`/`"OUT"`), `timestamp`: str or None | none | Inserts one sensor reading. If `timestamp` is None, uses current local time. |
| `get_recent_logs(minutes=60, limit=None)` | `minutes`: int (default 60), `limit`: int or None | `list[tuple]` | Returns rows within time window, newest first. Use `limit=1` for latest only. |
| `insert_event(type_, trigger, desc)` | `type_`: str, `trigger`: str (`"auto"`/`"manual"`), `desc`: str | none | Inserts one event with current local timestamp. |
| `get_recent_events(limit=20)` | `limit`: int (default 20) | `list[tuple]` | Returns most recent events, newest first. |

Standalone usage: `python database.py` — calls `init_db()` and prints confirmation.

### `serial_reader.py`

Bridges Arduino USB serial output to the SQLite database.

**Class `SerialReader`**

| Method | Description |
|--------|-------------|
| `__init__(port, baudrate, timeout)` | Configures serial parameters. `port` defaults to `"COM3"`, `baudrate` to `9600`. |
| `connect()` | Opens the serial port and waits 2 seconds for Arduino reset. |
| `read_line()` | Reads one line from serial. Returns a decoded UTF-8 string or `None` on error/empty. |
| `parse_and_store(line)` | Parses a JSON string and calls `insert_sensor_log()`. Returns the parsed dict or `None` on invalid JSON. |
| `close()` | Closes the serial port if open. |

**Function `run(port, baudrate)`**

Main loop. Connects to Arduino (with infinite retry on failure), reads lines in a loop, and handles Ctrl+C gracefully. Logs connect/disconnect events to the `events` table.

**Properties**

| Property | Description |
|----------|-------------|
| `line_count` | Total lines successfully read from serial |
| `error_count` | Total lines that failed JSON parsing |

**CLI:**
```
python serial_reader.py --port COM3 --baud 9600
```

### `app.py`

Flask web application. Serves the dashboard UI and REST API.

**Initialization:** Calls `init_db()` on startup. Enables CORS for all origins.

**All routes:**

| Route | Methods | Function | Description |
|-------|---------|----------|-------------|
| `/` | GET | `index()` | Renders `templates/index.html` |
| `/api/latest` | GET | `api_latest()` | Returns most recent sensor row |
| `/api/logs` | GET | `api_logs()` | Returns last 60 minutes of sensor data |
| `/api/events` | GET | `api_events()` | Returns 20 most recent events |
| `/api/override` | POST | `api_override()` | Accepts `{"action": "IN"/"OUT"/"AUTO"}` |
| `/api/demo/seed` | GET | `api_demo_seed()` | Seeds 60 dummy sensor rows + 5 events |
| `/api/health` | GET | `api_health()` | Returns server and database status |

**Port:** 5000 (change via `port=` in `app.run()`).

## Dashboard UI

The dashboard at `http://localhost:5000` is a single-page application using vanilla HTML, CSS, and JavaScript with Chart.js 4.4.1 loaded from CDN. It polls three API endpoints (`/api/latest`, `/api/logs`, `/api/events`) every 3 seconds.

### Layout Components

| Component | Position | Content |
|-----------|----------|---------|
| Topbar | Full-width top, 48px | Title "Jemuran Otomatis", connection status dot + label, last update timestamp |
| Left panel | 260px fixed | Ring gauge (rain value 0-1023), servo state indicator (IN: red / OUT: green) |
| Status hero | Right area top | Condition-dependent banner: safe (green), warning (amber, humidity > 75), danger (red, rain >= 400) |
| Metric bars | Right area | Three horizontal progress bars: Rain (blue, 0-1023), Lux (amber, 0-1023), Humidity (green, 0-100%) |
| History chart | Right area center | 300px line chart: Rain and Lux on left Y-axis, Humidity on right Y-axis (0-100%). Max 20 data points displayed. |
| Event timeline | Bottom-left | Last 8 events with color-coded dots: green for auto-triggered, amber for manual |
| Control panel | Bottom-right | Three servo override buttons (IN/OUT/AUTO) + rain threshold slider (100-900) |

### State Logic

The status hero banner changes based on the latest sensor reading:

| Condition | Banner Color | Title | Subtitle |
|-----------|-------------|-------|----------|
| `rain < 400` and `humidity <= 75` | Green | Cuaca Aman | Jemuran di Luar |
| `rain < 400` and `humidity > 75` | Amber | Kelembapan Tinggi | Waspada |
| `rain >= 400` | Red | Hujan Terdeteksi | Jemuran Masuk |

Priority: rain check first, then humidity. If rain >= 400, humidity is ignored.

### Chart Dataset

All three metrics are plotted on the same chart. Data is sampled to a maximum of 20 points for legibility.

| Dataset | Color | Y-Axis | Line Style |
|---------|-------|--------|------------|
| Rain (0-1023) | `#5794f2` blue | Left | Solid, 2px |
| Lux (0-1023) | `#e5a43c` amber | Left | Solid, 2px |
| Humidity (0-100%) | `#73bf69` green | Right (0-100%) | Dashed, 2px |

Chart animation is disabled to prevent jitter on each refresh. The legend is positioned top-center with point-style indicators.

### Manual Override

Each button sends a `POST /api/override` with the corresponding action:
- **Paksa Masuk**: `{"action": "IN"}`
- **Paksa Keluar**: `{"action": "OUT"}`
- **Mode Otomatis**: `{"action": "AUTO"}`

A toast notification appears in the bottom-right corner for 3 seconds on success or failure. The override is recorded in the `events` table with `trigger: "manual"`.

### Responsive Behavior

| Breakpoint | Layout Change |
|------------|--------------|
| > 900px | Full layout: left panel + right content, two-column bottom |
| 769-900px | Bottom row collapses to single column |
| <= 768px | Single-column stack: topbar, horizontal left panel (compact ring + servo), vertical right content |

### Color Palette

Grafana-inspired dark theme. All colors are defined as CSS custom properties in `:root`.

```
Background:         #111217
Surface cards:      #181b1f
Surface elevated:   #1f2329
Border:             #2a2e35
Primary text:       #d8d9da
Secondary text:     #8e9199
Tertiary text:      #5c5f66

Blue (Rain):        #5794f2  bg: #132033
Amber (Lux):        #e5a43c  bg: #251e10
Green (Humidity):   #73bf69  bg: #152818
Red (Danger):       #e24d4c  bg: #2b1416
```

### Dependencies (Frontend)

| Resource | Source |
|----------|--------|
| Inter font (400, 500, 600) | Google Fonts CDN |
| Chart.js 4.4.1 | cdnjs.cloudflare.com |

All CSS and JavaScript are inline in `index.html`. No build step, no bundler.

## Troubleshooting

### Dashboard shows no data

1. Run `/api/demo/seed` first if testing without Arduino:
   ```
   http://localhost:5000/api/demo/seed
   ```
2. Verify data exists: `http://localhost:5000/api/latest` should return an object, not `null`.
3. If using Arduino, check that `serial_reader.py` is running and printing "OK stored" lines.

### Serial port not found

1. Check available ports:
   - Windows: `mode` in Command Prompt, or check Device Manager under "Ports (COM & LPT)"
   - Linux/Mac: `ls /dev/tty*`
2. Try a different port: `python serial_reader.py --port COM4`
3. Ensure no other program (Arduino IDE Serial Monitor, PuTTY) is using the port.

### Database errors

1. Delete `jemuran.db` and regenerate:
   ```bash
   python database.py
   ```
2. Inspect the database directly:
   ```bash
   sqlite3 jemuran.db "SELECT COUNT(*) FROM sensor_logs;"
   sqlite3 jemuran.db "SELECT * FROM sensor_logs ORDER BY timestamp DESC LIMIT 5;"
   ```

### Port 5000 already in use

Change the port in `app.py`, line 110:
```python
app.run(debug=True, host="0.0.0.0", port=5050)
```

### Chart displays but is too dense to read

This is expected behavior when more than ~20 data points are loaded. The frontend automatically samples the chart dataset to 20 evenly-spaced points for legibility. If you need more detail, hover over data points; tooltips show exact values at each timestamp.

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend runtime | Python 3.8+ |
| Web framework | Flask 3.x |
| CORS | flask-cors |
| Database | SQLite 3 (stdlib `sqlite3`) |
| Serial communication | pyserial |
| Frontend | Vanilla HTML5, CSS3, ES6 JavaScript |
| Chart library | Chart.js 4.4.1 (CDN, no npm) |
| Typography | Inter (Google Fonts) |
| Hardware interface | Arduino over USB Serial (9600 baud, 8N1) |
