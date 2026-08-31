import os
import logging
from flask import Flask
from backend.config import Config
from backend.extensions import db, migrate, socketio, redis_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("navonmesh")


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"),
    )
    app.config.from_object(config_class)

    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_dir

    db.init_app(app)
    migrate.init_app(app, db)

    async_mode = "threading"
    try:
        import eventlet  # noqa: F401
        async_mode = "eventlet"
    except ImportError:
        pass
    socketio.init_app(app, async_mode=async_mode, cors_allowed_origins="*")

    if app.config.get("REDIS_URL"):
        try:
            import redis as redis_lib
            redis_client.client = redis_lib.from_url(app.config["REDIS_URL"], decode_responses=True)
            redis_client.client.ping()
            logger.info("Redis connected")
        except Exception:
            redis_client.client = None
    else:
        redis_client.client = None

    from backend.routes.dashboard import dashboard_bp
    from backend.routes.cameras import cameras_bp
    from backend.routes.upload import upload_bp
    from backend.routes.vehicles import vehicles_bp
    from backend.routes.detections import detections_bp
    from backend.routes.trajectories import trajectories_bp
    from backend.routes.analytics import analytics_bp
    from backend.routes.alerts import alerts_bp
    from backend.routes.blacklist import blacklist_bp
    from backend.routes.system import system_bp
    from backend.routes.videos import videos_bp
    from backend.routes.evidence import evidence_bp
    from backend.routes.plates import plates_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(cameras_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(detections_bp)
    app.register_blueprint(trajectories_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(blacklist_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(videos_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(plates_bp)

    with app.app_context():
        from backend.models import (
            Camera, Vehicle, Detection, PlateRead, VehicleSighting,
            CameraTransition, Trajectory, BlacklistEntry, Alert, AnalyticsSnapshot,
            ProcessingJob,
        )
        db.create_all()

    logger.info("NAVONMESH Sightlines application created")
    return app
