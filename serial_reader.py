"""
Serial reader for Arduino → jemuran-dashboard.

Reads JSON lines from Arduino over USB serial, parses them, and stores
sensor data + events into the SQLite database.

Usage as a standalone runner:
    python serial_reader.py [--port COM3] [--baud 9600]

Press Ctrl+C to stop gracefully.
"""

import argparse
import json
import sys
import time
import traceback

import serial

from database import init_db, insert_sensor_log, insert_event


class SerialReader:
    def __init__(self, port="COM3", baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self._line_count = 0
        self._error_count = 0

    def connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        time.sleep(2)

    def read_line(self):
        if not (self.ser and self.ser.is_open):
            return None
        try:
            raw = self.ser.readline()
            return raw.decode("utf-8", errors="replace").strip()
        except serial.SerialException:
            return None

    def parse_and_store(self, line):
        """
        Parse one JSON line from Arduino and persist to the database.
        Also auto-inserts events on servo state transitions.
        Returns the parsed dict or None.
        """
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return None

        rain = data.get("rain", 0)
        lux = data.get("lux", 0)
        hum = data.get("humidity", 0.0)
        servo = data.get("servo", "IN")

        insert_sensor_log(int(rain), int(lux), float(hum), str(servo))
        return data

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    @property
    def line_count(self):
        return self._line_count

    @property
    def error_count(self):
        return self._error_count


def run(port="COM3", baudrate=9600):
    """Main loop: connect, read, parse, store. Retries on disconnect."""
    init_db()
    print(f"[serial_reader] Database ready.")
    print(f"[serial_reader] Connecting to Arduino on {port} @ {baudrate} baud …")

    reader = SerialReader(port=port, baudrate=baudrate)

    # ── Connect with retry ──
    while True:
        try:
            reader.connect()
            print(f"[serial_reader] Connected. Waiting for data …")
            insert_event("system", "auto", f"Serial connected on {port}")
            break
        except serial.SerialException as exc:
            print(f"[serial_reader] Cannot open {port}: {exc}")
            print(f"[serial_reader] Retrying in 3 seconds …")
            time.sleep(3)

    # ── Read loop ──
    try:
        while True:
            line = reader.read_line()
            if not line:
                time.sleep(0.1)
                continue

            print(f"[serial_reader] ← {line}")
            data = reader.parse_and_store(line)
            reader._line_count += 1

            if data is None:
                reader._error_count += 1
                print(f"[serial_reader] WARN Failed to parse JSON")
            else:
                print(
                    f"[serial_reader] OK stored | rain={data.get('rain','?')} "
                    f"lux={data.get('lux','?')} hum={data.get('humidity','?')} "
                    f"servo={data.get('servo','?')}"
                )

    except KeyboardInterrupt:
        print(f"\n[serial_reader] Stopped by user.")
    except serial.SerialException as exc:
        print(f"[serial_reader] Serial error: {exc}")
        traceback.print_exc()
    finally:
        reader.close()
        insert_event("system", "auto", "Serial disconnected")
        print(
            f"[serial_reader] Disconnected. "
            f"Lines read: {reader.line_count}, errors: {reader.error_count}"
        )


# ── CLI entry point ──
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arduino serial → SQLite")
    parser.add_argument("--port", default="COM3", help="Serial port (default: COM3)")
    parser.add_argument("--baud", type=int, default=9600, help="Baud rate (default: 9600)")
    args = parser.parse_args()
    run(port=args.port, baudrate=args.baud)
