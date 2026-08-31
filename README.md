# NAVONMESH Sightlines — SIH26127

**City-Wide AI Engine for Multi-Camera ANPR Trajectory Tracking and Urban Traffic Analytics**

---

## Architecture

```
CCTV Video Upload
       ↓
  Flask Upload API
       ↓
  Background Worker Thread
       ↓
  OpenCV Frame Extraction
       ↓
  YOLO Vehicle Detection
       ↓
  Local Track ID (distance matching)
       ↓
  License Plate Detection (YOLO)
       ↓
  PaddleOCR
       ↓
  Temporal OCR Voting (per-track)
       ↓
  Re-ID Embedding (appearance)
       ↓
  Cross-Camera Matching → Global Vehicle ID
       ↓
  PostgreSQL Database
       ↓
  Flask REST API
       ↓
  HTML + CSS + JS + Leaflet + Chart.js
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, Flask, SQLAlchemy, Flask-SocketIO |
| Database | SQLite (auto-configured) / PostgreSQL |
| Cache | Redis (optional) |
| AI Detection | Ultralytics YOLO |
| OCR | PaddleOCR |
| Re-ID | OSNet / appearance-based |
| Map | Leaflet.js |
| Charts | Chart.js |
| Frontend | HTML5, CSS3, Vanilla JavaScript |

## Quick Start

```bash
python run.py
```

That's it. `run.py` automatically:
1. Detects your Python environment
2. Checks and installs all missing dependencies
3. Creates required directories
4. Downloads AI model weights if available
5. Initializes SQLite database (no PostgreSQL setup needed)
6. Seeds 4 default cameras
7. Starts the Flask server

Open http://127.0.0.1:5000

## Requirements

- Python 3.9+
- That's all — everything else is handled automatically

### Optional

For full AI processing, install these in the background (auto-detected):
- `ultralytics` — YOLO vehicle/plate detection
- `paddleocr` + `paddlepaddle` — OCR engine
- CUDA-capable GPU — GPU acceleration

### Docker (alternative)

```bash
docker compose up --build
```

## AI Models

### Vehicle Detection (YOLO)
The system expects a YOLO model for vehicle detection. By default it uses `yolov8n.pt` which will be auto-downloaded by Ultralytics on first use.

Set in `.env`:
```
YOLO_VEHICLE_MODEL=yolov8n.pt
```

### License Plate Detection
Requires a YOLO model trained on license plates. Set:
```
YOLO_PLATE_MODEL=license_plate.pt
```

If the model file does not exist, plate detection is marked as `MISSING_MODEL` and the pipeline runs without OCR.

### PaddleOCR
Install PaddlePaddle and PaddleOCR:
```
pip install paddlepaddle paddleocr
```

If unavailable, OCR is marked as `MISSING_MODEL`.

### Re-ID
Optional appearance-based re-identification. Set:
```
REID_MODEL_PATH=osnet_x1_0.pth
```

If unavailable, the system uses appearance-based histogram fallback.

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | KPIs, GIS map, cameras, recent detections, alerts |
| Live Cameras | `/cameras` | Camera grid with status and stats |
| Vehicle Tracking | `/tracking` | Plate search, vehicle profile, camera history |
| Trajectory Map | `/trajectory` | Leaflet map with camera-to-camera path |
| Traffic Analytics | `/analytics` | Charts: hourly, vehicle mix, routes, heatmap |
| Alerts | `/alerts` | Active alerts with acknowledge/resolve |
| Blacklist | `/blacklist` | CRUD for blacklisted plates |
| Upload | `/upload` | Video upload and processing jobs |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | Dashboard KPI values |
| GET | `/api/system/status` | System health check |
| GET | `/api/cameras` | List all cameras |
| POST | `/api/cameras` | Register a camera |
| PUT | `/api/cameras/<id>` | Update camera |
| DELETE | `/api/cameras/<id>` | Delete camera |
| POST | `/api/upload` | Upload video file |
| GET | `/api/jobs` | List processing jobs |
| GET | `/api/jobs/<job_id>` | Job status |
| GET | `/api/vehicles/search?q=` | Search by plate |
| GET | `/api/vehicles` | List vehicles |
| GET | `/api/vehicles/<id>` | Vehicle detail |
| GET | `/api/detections` | Recent detections |
| GET | `/api/detections/recent` | Recent detections with plate reads |
| GET | `/api/trajectories/<plate>` | Vehicle trajectory |
| GET | `/api/analytics/stats` | Analytics data |
| GET | `/api/alerts` | List alerts |
| PUT | `/api/alerts/<id>/acknowledge` | Acknowledge alert |
| PUT | `/api/alerts/<id>/resolve` | Resolve alert |
| GET | `/api/alerts/active-count` | Active alert count |
| GET | `/api/blacklist` | List blacklist entries |
| POST | `/api/blacklist` | Add to blacklist |
| PUT | `/api/blacklist/<id>` | Update entry |
| DELETE | `/api/blacklist/<id>` | Remove entry |

## Demo Workflow

1. Start the application
2. Open http://127.0.0.1:5000
3. Register cameras (4 cameras are auto-seeded)
4. Go to Upload page
5. Select a camera and upload an MP4 video
6. Processing begins in background
7. Dashboard shows detections in real-time
8. Search plates in Vehicle Tracking
9. View trajectory on Leaflet map
10. Add a detected plate to Blacklist
11. Detect it again → real alert generated
12. Resolve alert from Alerts page
13. Restart Flask → data persists in PostgreSQL

## Project Structure

```
navonmesh-sightlines-main/
├── run.py                    # Entry point
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker orchestration
├── Dockerfile                # Container build
├── .env.example              # Environment template
├── backend/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration
│   ├── extensions.py         # db, socketio, redis
│   ├── models/               # SQLAlchemy models
│   │   ├── camera.py
│   │   ├── vehicle.py
│   │   ├── detection.py
│   │   ├── plate_read.py
│   │   ├── sighting.py
│   │   ├── transition.py
│   │   ├── trajectory.py
│   │   ├── blacklist.py
│   │   ├── alert.py
│   │   ├── analytics.py
│   │   └── job.py
│   ├── routes/               # Flask Blueprints
│   │   ├── dashboard.py
│   │   ├── cameras.py
│   │   ├── upload.py
│   │   ├── vehicles.py
│   │   ├── detections.py
│   │   ├── trajectories.py
│   │   ├── analytics.py
│   │   ├── alerts.py
│   │   ├── blacklist.py
│   │   └── system.py
│   └── services/             # Business logic
│       ├── ai_models.py      # YOLO, PaddleOCR, Re-ID
│       └── video_processor.py # Background video processing
├── templates/                # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── cameras.html
│   ├── tracking.html
│   ├── trajectory.html
│   ├── analytics.html
│   ├── alerts.html
│   ├── blacklist.html
│   └── upload.html
├── static/
│   ├── css/style.css         # Dark command-center theme
│   └── js/
│       ├── api.js            # REST API client
│       └── app.js            # Global initialization
└── uploads/                  # Video upload storage
```

## Database Tables

| Table | Description |
|-------|-------------|
| `cameras` | Camera definitions with GPS coordinates |
| `vehicles` | Global vehicle identities |
| `detections` | YOLO detection records |
| `plate_reads` | OCR results per detection |
| `vehicle_sightings` | Camera-level vehicle appearances |
| `camera_transitions` | Camera-to-camera transitions |
| `trajectories` | Reconstructed vehicle paths |
| `blacklist` | Blacklisted plates |
| `alerts` | System-generated alerts |
| `analytics_snapshots` | Hourly/daily analytics |
| `processing_jobs` | Video processing job state |

## Database

By default, the application uses SQLite (zero configuration). The database file is stored at `database/navonmesh.db`.

To use PostgreSQL instead, set the `DATABASE_URL` environment variable:
```
DATABASE_URL=postgresql://user:password@localhost:5432/navonmesh_sightlines
```
| `REDIS_URL` | | Redis connection (optional) |
| `SECRET_KEY` | dev-key | Flask secret key |
| `DEMO_MODE` | false | Enable demo mode |
| `YOLO_VEHICLE_MODEL` | yolov8n.pt | Vehicle detection model |
| `YOLO_PLATE_MODEL` | license_plate.pt | Plate detection model |
| `REID_MODEL_PATH` | osnet_x1_0.pth | Re-ID model |
| `FRAME_SKIP` | 3 | Process every Nth frame |
| `UPLOAD_FOLDER` | uploads | Video upload directory |

## Known Limitations

- License plate detection requires a custom YOLO model (`license_plate.pt`)
- PaddleOCR requires PaddlePaddle installation
- Re-ID model (OSNet) is optional; histogram-based fallback is used
- Camera transition timing uses SQLite timestamps; GPS-based distance is estimated via Haversine formula
- Real-time WebSocket updates are implemented via Flask-SocketIO but require eventlet

## Team

Team Navonmesh — SIH26127
