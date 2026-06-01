# Diagram Alur -- Jemuran Dashboard

Diagram berikut menjelaskan cara kerja sistem dari sisi software.

---

## Alur Utama

```mermaid
flowchart TD
    subgraph start["1. Menjalankan Sistem"]
        A1["Terminal 1:<br/>python app.py"]
        A2["Terminal 2:<br/>python serial_reader.py"]
    end

    subgraph backend["2. Backend (Laptop)"]
        B1["Flask Server<br/>port 5000"]
        B2["Serial Reader<br/>baca data Arduino via USB"]
        B3[("SQLite<br/>jemuran.db")]
    end

    subgraph arduino["3. Sumber Data"]
        C1["Arduino + Sensor<br/>Kirim JSON tiap 2 detik"]
    end

    subgraph browser["4. Tampilan (Browser)"]
        D1["Dashboard UI<br/>localhost:5000"]
        D2["Ambil data terbaru<br/>tiap 3 detik"]
        D3["Tampilkan ke layar"]
    end

    A1 --> B1
    A2 --> B2

    C1 -- "USB Serial" --> B2
    B2 -- "INSERT" --> B3

    B1 -- "Baca" --> B3
    B1 -- "GET /api/*" --> D1
    D2 -- "fetch /api/latest<br/>fetch /api/logs<br/>fetch /api/events" --> B1
    B1 -- "JSON response" --> D2
    D2 --> D3
```

---

## Alur Data Detail

```mermaid
flowchart LR
    subgraph source["Sumber Data"]
        S1["Arduino<br/>(JSON via Serial)"]
        S2["Demo Seed<br/>(/api/demo/seed)"]
    end

    subgraph store["Penyimpanan"]
        DB[("jemuran.db")]
    end

    subgraph serve["API Server"]
        E1["GET /api/latest"]
        E2["GET /api/logs"]
        E3["GET /api/events"]
        E4["POST /api/override"]
        E5["GET /api/health"]
    end

    subgraph ui["Dashboard"]
        U1["Status Banner"]
        U2["Ring Gauge"]
        U3["Progress Bar"]
        U4["Line Chart"]
        U5["Event Timeline"]
        U6["Tombol Kontrol"]
    end

    S1 --> DB
    S2 --> DB
    DB --> E1 --> U1
    DB --> E1 --> U2
    DB --> E1 --> U3
    DB --> E2 --> U4
    DB --> E3 --> U5
    U6 -- "POST" --> E4 --> DB
```

---

## Alur Status Banner

```mermaid
flowchart TD
    START["Data sensor terbaru<br/>dari /api/latest"] --> CHECK_RAIN{"rain >= 400?"}

    CHECK_RAIN -- "Ya" --> DANGER["Merah<br/>Hujan Terdeteksi<br/>Jemuran Masuk"]
    CHECK_RAIN -- "Tidak" --> CHECK_HUM{"humidity > 75?"}

    CHECK_HUM -- "Ya" --> WARN["Kuning<br/>Kelembapan Tinggi<br/>Waspada"]
    CHECK_HUM -- "Tidak" --> SAFE["Hijau<br/>Cuaca Aman<br/>Jemuran di Luar"]

    DANGER --> DONE["Tampilkan di layar"]
    WARN --> DONE
    SAFE --> DONE
```

---

## Alur Manual Override

```mermaid
flowchart TD
    USER["User klik tombol<br/>Paksa Masuk / Paksa Keluar / Mode Otomatis"]
    SEND["Kirim POST /api/override<br/>{action: 'IN' | 'OUT' | 'AUTO'}"]
    INSERT["Simpan ke tabel events<br/>event_type: servo_override<br/>trigger: manual"]
    RESP["Response: {status: 'ok'}"]
    TOAST["Toast muncul 3 detik<br/>'Servo masuk -- berhasil'"]
    LOG["Tercatat di timeline<br/>Event terbaru"]

    USER --> SEND --> INSERT --> RESP --> TOAST
    INSERT --> LOG
```

---

## Alur Demo Mode

```mermaid
flowchart TD
    NO_HW["Tidak ada Arduino"]
    OPEN["Buka /api/demo/seed"]
    GEN["Generate 60 baris data sensor<br/>Generate 5 event"]
    SHOW["Dashboard langsung terisi<br/>Grafik, ring gauge, timeline"]
    PITCH["Cocok untuk presentasi<br/>atau testing"]

    NO_HW --> OPEN --> GEN --> SHOW --> PITCH
```

---

## Dua Proses Berjalan Bersamaan

```mermaid
flowchart TD
    subgraph proc1["Proses 1: app.py"]
        P1["Init database"]
        P2["Jalankan Flask di port 5000"]
        P3["Layani 7 endpoint API"]
        P4["Sajikan halaman dashboard"]
    end

    subgraph proc2["Proses 2: serial_reader.py"]
        Q1["Init database"]
        Q2["Hubungkan ke Arduino via USB"]
        Q3["Baca JSON tiap baris"]
        Q4["Simpan ke sensor_logs"]
        Q5["Log event connect/disconnect"]
    end

    DB2[("jemuran.db")]

    P1 --> P2 --> P3
    P2 --> P4
    P3 -. "baca/tulis" .-> DB2

    Q1 --> Q2 --> Q3 --> Q4
    Q5 -. "INSERT event" .-> DB2
    Q4 --> DB2

    NOTE["Kedua proses independen.<br/>Satu mati tidak mematikan yang lain."]
```

---

## Catatan

- Semua diagram menggunakan [Mermaid](https://mermaid.js.org). GitHub akan merender diagram ini langsung di halaman repo.
- Buka `FLOWCHART.md` di GitHub untuk melihat diagram dalam bentuk visual.
