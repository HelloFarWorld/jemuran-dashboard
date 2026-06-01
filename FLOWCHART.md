# Diagram Alur -- Jemuran Dashboard

Diagram berikut menjelaskan keseluruhan cara kerja sistem dalam satu alur terpadu.

```mermaid
flowchart TD
    START["Mulai"]

    START --> TERMINAL{"Dua terminal
    dijalankan bersamaan"}

    TERMINAL --> T1["Terminal 1:
    python app.py"]
    TERMINAL --> T2["Terminal 2:
    python serial_reader.py"]

    T1 --> INIT1["init_db()
    Buat tabel jika belum ada"]
    T2 --> INIT2["init_db()
    Buat tabel jika belum ada"]

    INIT1 --> FLASK["Flask server
    berjalan di port 5000"]

    INIT2 --> CONNECT{"Arduino
    terhubung?"}

    CONNECT -->|"Ya"| READ["Baca JSON
    dari Serial USB
    tiap 2 detik"]
    CONNECT -->|"Tidak"| RETRY["Coba lagi
    tiap 3 detik"]
    RETRY --> CONNECT

    READ --> PARSE["Parse JSON:
    rain, lux, humidity, servo"]
    PARSE -->|"JSON valid"| INSERT_LOG["INSERT ke
    sensor_logs"]
    PARSE -->|"JSON rusak"| SKIP["Abaikan baris,
    lanjut baca"]
    SKIP --> READ

    INSERT_LOG --> DB[("SQLite
    jemuran.db")]

    FLASK --> ROUTE{"HTTP Request
    dari Browser"}

    ROUTE -->|"GET /"| HTML["Sajikan
    halaman dashboard"]

    ROUTE -->|"GET /api/latest"| LATEST["Ambil 1 baris
    terbaru dari DB"]
    ROUTE -->|"GET /api/logs"| LOGS["Ambil data
    60 menit terakhir"]
    ROUTE -->|"GET /api/events"| EVENTS["Ambil 20
    event terbaru"]
    ROUTE -->|"POST /api/override"| OVERRIDE["Terima action:
    IN / OUT / AUTO"]
    ROUTE -->|"GET /api/demo/seed"| SEED["Generate 60 baris
    data dummy untuk testing"]

    LATEST --> DB
    LOGS --> DB
    EVENTS --> DB
    SEED --> DB

    LATEST --> JSON1["JSON: rain, lux,
    humidity, servo"]
    LOGS --> JSON2["JSON array:
    60 baris sensor"]
    EVENTS --> JSON3["JSON array:
    20 baris event"]
    OVERRIDE --> INSERT_EVT["INSERT ke events
    trigger: manual"]
    INSERT_EVT --> DB
    INSERT_EVT --> JSON4["JSON: {status: 'ok'}"]
    SEED --> JSON5["JSON: {seeded: 60}"]

    HTML --> BROWSER["Browser render
    dashboard UI"]

    JSON1 --> BROWSER
    JSON2 --> BROWSER
    JSON3 --> BROWSER
    JSON4 --> BROWSER
    JSON5 --> BROWSER

    BROWSER --> POLL["Tiap 3 detik:
    fetch ulang /api/latest,
    /api/logs, /api/events"]

    POLL --> DECIDE{"Data terbaru:
    rain >= 400?"}

    DECIDE -->|"Ya"| RED["Banner Merah
    Hujan Terdeteksi
    Jemuran Masuk"]
    DECIDE -->|"Tidak"| HUMCHECK{"humidity > 75?"}

    HUMCHECK -->|"Ya"| AMBER["Banner Kuning
    Kelembapan Tinggi
    Waspada"]
    HUMCHECK -->|"Tidak"| GREEN["Banner Hijau
    Cuaca Aman
    Jemuran di Luar"]

    RED --> RENDER["Update semua
    komponen UI"]
    AMBER --> RENDER
    GREEN --> RENDER

    RENDER --> RING["Ring Gauge: rain value"]
    RENDER --> BARS["Progress Bar: rain, lux, hum"]
    RENDER --> CHART["Line Chart: 60 menit histori"]
    RENDER --> TIMELINE["Timeline: 8 event terbaru"]
    RENDER --> SERVO["Servo indicator: IN / OUT"]

    RING --> LOOP["Kembali polling
    setelah 3 detik"]
    BARS --> LOOP
    CHART --> LOOP
    TIMELINE --> LOOP
    SERVO --> LOOP

    LOOP --> POLL

    BROWSER -->|"User klik
    tombol kontrol"| BTN{"Tombol mana?"}

    BTN -->|"Paksa Masuk"| POST_IN["POST /api/override
    {action: 'IN'}"]
    BTN -->|"Paksa Keluar"| POST_OUT["POST /api/override
    {action: 'OUT'}"]
    BTN -->|"Mode Otomatis"| POST_AUTO["POST /api/override
    {action: 'AUTO'}"]

    POST_IN --> INSERT_EVT
    POST_OUT --> INSERT_EVT
    POST_AUTO --> INSERT_EVT

    POST_IN --> TOAST["Toast: berhasil,
    hilang setelah 3 detik"]
    POST_OUT --> TOAST
    POST_AUTO --> TOAST
```

---

## Cara Membaca Diagram

Diagram dibaca dari atas ke bawah, dibagi menjadi beberapa zona:

| Zona | Warna | Isi |
|------|-------|-----|
| Startup | Node atas | Dua terminal, init database |
| Data Masuk | Kiri | Arduino -> serial_reader -> SQLite |
| API Server | Tengah | Flask melayani 7 endpoint |
| Browser | Kanan | Dashboard polling + render UI |
| Kontrol | Bawah kanan | User override via tombol |
| Status | Tengah bawah | Decision tree: rain dan humidity |

Panah menunjukkan arah aliran data. Kotak belah ketupat adalah titik keputusan (if/else). Silinder adalah database.
