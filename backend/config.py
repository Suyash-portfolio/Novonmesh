import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "navonmesh-dev-key-change-in-production")

    _db_url = os.environ.get("DATABASE_URL", "")
    if not _db_url:
        _db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "database", "navonmesh.db"
        )
        os.makedirs(os.path.dirname(_db_path), exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{_db_path}"
    else:
        SQLALCHEMY_DATABASE_URI = _db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 2 * 1024 * 1024 * 1024))
    REDIS_URL = os.environ.get("REDIS_URL", "")
    DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

    YOLO_VEHICLE_MODEL = os.environ.get("YOLO_VEHICLE_MODEL", "yolov8n.pt")
    YOLO_PLATE_MODEL = os.environ.get("YOLO_PLATE_MODEL", "license_plate.pt")
    REID_MODEL_PATH = os.environ.get("REID_MODEL_PATH", "osnet_x1_0.pth")

    CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.4"))
    OCR_CONFIDENCE_THRESHOLD = float(os.environ.get("OCR_CONFIDENCE_THRESHOLD", "0.5"))
    FRAME_SKIP = int(os.environ.get("FRAME_SKIP", "3"))
