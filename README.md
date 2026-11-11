# 🏭 AI-Based Intelligent Industrial Safety Surveillance System

> An advanced real-time AI safety monitoring platform for industrial environments, powered by YOLO object detection, FastAPI, and a modern web dashboard.

---

## 🚀 Features

### Phase 1 — PPE Detection & Image Analysis
- 📸 **Image Upload Detection** — Detect PPE compliance in uploaded images
- 🎥 **Video Upload Detection** — Analyze video files frame-by-frame
- 🤖 **YOLO AI Model** — Custom-trained `best.pt` model for 10-class PPE detection
- 📊 **Detection Results** — Annotated bounding boxes with confidence scores

### Phase 2 — Live Surveillance & Automatic Alerts
- 🔴 **Live Webcam Monitoring** — Real-time PPE detection from camera feeds
- 🚨 **Automatic Alerts** — Instant violation alerts with cooldown management
- 📷 **Evidence Capture** — Automatic snapshot saving on violations
- 📡 **WebSocket Streaming** — Low-latency live feed processing

### Phase 3 — Analytics, Reporting & Management
- 📈 **Advanced Analytics Dashboard** — 6 KPIs, compliance trends, violation heatmaps
- 🗂️ **Incident History & Management** — Filter, paginate, resolve incidents with workflow states
- 📄 **Report Generation** — PDF audit reports and CSV exports via ReportLab
- ⚙️ **System Settings** — Confidence threshold tuning, alert cooldowns, storage diagnostics

---

## 🧠 AI Model

| Property | Value |
|---|---|
| Framework | Ultralytics YOLO |
| Model File | `models/best.pt` |
| Classes | 10 (5 compliant + 5 violations) |

**Detected Classes:**
- Compliant: `Hardhat`, `Safety Vest`, `Mask`, `Gloves`, `Goggles`
- Violations: `NO-Hardhat`, `NO-Safety Vest`, `NO-Mask`, `NO-Gloves`, `NO-Goggles`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript, Chart.js |
| Backend | Python, FastAPI, Uvicorn |
| AI/ML | Ultralytics YOLO, PyTorch, OpenCV |
| Database | SQLite (WAL mode) |
| Reports | ReportLab (PDF), CSV |

---

## 📁 Project Structure

```
se_project/
├── backend/
│   ├── main.py              # FastAPI application & all API routes
│   ├── database.py          # SQLite schema & query functions
│   ├── utils/
│   │   └── report_generator.py   # PDF/CSV report generation
│   ├── evidence/            # Auto-captured violation snapshots
│   └── reports/             # Generated report files
├── frontend/
│   ├── index.html           # Main SPA entry point
│   ├── css/
│   │   └── style.css        # Complete design system & styles
│   └── js/
│       └── script.js        # Frontend controllers & API calls
├── models/
│   └── best.pt              # Trained YOLO model weights
├── tests/
│   └── test_phase3_full.py  # Comprehensive test suite
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/se-project.git
cd se-project
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open the dashboard
Navigate to: **http://localhost:8000**

---

## Running Tests

```bash
python -m pytest tests/test_phase3_full.py -v
```

---

## License

This project is developed for academic/research purposes.

---

## Author

Built as a Software Engineering capstone project — AI-Based Intelligent Industrial Safety Surveillance System.
