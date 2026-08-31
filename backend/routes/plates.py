import os
import logging
import sqlite3
from flask import Blueprint, jsonify, request, send_from_directory

logger = logging.getLogger("navonmesh.plates")
plates_bp = Blueprint("plates", __name__)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVIDENCE_DIR = os.path.join(PROJECT_DIR, "evidence")
OUTPUTS_DIR = os.path.join(PROJECT_DIR, "outputs")


def _get_db_path():
    return os.path.join(PROJECT_DIR, "database", "navonmesh.db")


def _dict_from_row(row, columns):
    return {col: row[i] for i, col in enumerate(columns)}


@plates_bp.route("/plates")
def plates_page():
    from flask import render_template
    return render_template("detected_plates.html")


@plates_bp.route("/api/plates", methods=["GET"])
def list_plates():
    try:
        confidence_filter = request.args.get("confidence", "all")
        search = request.args.get("search", "").strip()

        conn = sqlite3.connect(_get_db_path())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        query = """
            SELECT
                pr.id,
                pr.plate_text,
                pr.raw_text,
                pr.ocr_confidence,
                pr.plate_bbox,
                pr.crop_path,
                pr.vehicle_local_id,
                pr.detected_at,
                pr.detection_id,
                pr.camera_id,
                d.frame_index,
                d.timestamp,
                d.vehicle_class,
                d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2,
                d.confidence AS det_confidence,
                v.global_id,
                v.plate_text AS vehicle_plate,
                v.id AS vehicle_db_id,
                j.job_id,
                j.video_filename
            FROM plate_reads pr
            LEFT JOIN detections d ON pr.detection_id = d.id
            LEFT JOIN vehicles v ON pr.vehicle_id = v.id
            LEFT JOIN processing_jobs j ON d.job_id = j.id
            WHERE pr.plate_text IS NOT NULL AND pr.plate_text != ''
        """
        params = []

        if search:
            query += " AND (pr.plate_text LIKE ? OR v.global_id LIKE ? OR pr.raw_text LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s])

        if confidence_filter == "high":
            query += " AND pr.ocr_confidence >= 0.85"
        elif confidence_filter == "medium":
            query += " AND pr.ocr_confidence >= 0.60 AND pr.ocr_confidence < 0.85"
        elif confidence_filter == "low":
            query += " AND pr.ocr_confidence < 0.60"

        query += " ORDER BY pr.ocr_confidence DESC"

        cur.execute(query, params)
        rows = cur.fetchall()

        plates = []
        for row in rows:
            crop_path = row["crop_path"] or ""
            crop_filename = os.path.basename(crop_path) if crop_path else None
            job_id = row["job_id"] or ""

            vehicle_bbox = None
            if row["bbox_x1"] is not None:
                vehicle_bbox = [row["bbox_x1"], row["bbox_y1"], row["bbox_x2"], row["bbox_y2"]]

            plates.append({
                "id": row["id"],
                "plateText": row["plate_text"],
                "rawText": row["raw_text"],
                "ocrConfidence": round(row["ocr_confidence"], 2),
                "plateBbox": row["plate_bbox"],
                "trackId": row["vehicle_local_id"],
                "cameraId": row["camera_id"],
                "globalId": row["global_id"],
                "vehiclePlate": row["vehicle_plate"],
                "vehicleDbId": row["vehicle_db_id"],
                "vehicleClass": row["vehicle_class"] or "Unknown",
                "vehicleBbox": vehicle_bbox,
                "detConfidence": round(row["det_confidence"], 2) if row["det_confidence"] else None,
                "frameIndex": row["frame_index"],
                "timestamp": round(row["timestamp"], 2) if row["timestamp"] else 0,
                "detectedAt": row["detected_at"],
                "jobId": job_id,
                "videoFilename": row["video_filename"],
                "evidenceCrop": f"/api/evidence/{job_id}/{crop_filename}" if crop_filename else None,
                "evidenceFrame": f"/api/evidence/{job_id}/vehicle_track{row['vehicle_local_id']}_{crop_filename.split('_')[-1]}" if crop_filename and row["vehicle_local_id"] else None,
            })

        conn.close()
        return jsonify(plates)

    except Exception as e:
        logger.error(f"Failed to list plates: {e}", exc_info=True)
        return jsonify([]), 200


@plates_bp.route("/api/plates/summary", methods=["GET"])
def plates_summary():
    try:
        conn = sqlite3.connect(_get_db_path())
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM plate_reads WHERE plate_text IS NOT NULL AND plate_text != ''")
        total_with_text = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT plate_text) FROM plate_reads WHERE plate_text IS NOT NULL AND plate_text != ''")
        unique_plates = cur.fetchone()[0]

        cur.execute("SELECT AVG(ocr_confidence) FROM plate_reads WHERE plate_text IS NOT NULL AND plate_text != ''")
        avg_conf = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM plate_reads WHERE plate_text IS NOT NULL AND ocr_confidence >= 0.85")
        high_conf = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM plate_reads WHERE plate_text IS NOT NULL AND ocr_confidence >= 0.60 AND ocr_confidence < 0.85")
        med_conf = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM plate_reads WHERE plate_text IS NOT NULL AND ocr_confidence < 0.60")
        low_conf = cur.fetchone()[0]

        cur.execute("""
            SELECT DISTINCT v.global_id, v.plate_text, v.ocr_confidence
            FROM vehicles v
            WHERE v.plate_text IS NOT NULL AND v.plate_text != ''
        """)
        vehicles_with_plates = [{"globalId": r[0], "plate": r[1], "conf": round(r[2], 2)} for r in cur.fetchall()]

        conn.close()

        return jsonify({
            "totalReads": total_with_text,
            "uniquePlates": unique_plates,
            "avgConfidence": round(avg_conf, 2),
            "highConfidence": high_conf,
            "mediumConfidence": med_conf,
            "lowConfidence": low_conf,
            "vehiclesWithPlates": vehicles_with_plates,
        })

    except Exception as e:
        logger.error(f"Failed to get plate summary: {e}")
        return jsonify({}), 200


@plates_bp.route("/api/plates/<int:plate_id>", methods=["GET"])
def get_plate_detail(plate_id):
    try:
        conn = sqlite3.connect(_get_db_path())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT
                pr.id,
                pr.plate_text,
                pr.raw_text,
                pr.ocr_confidence,
                pr.plate_bbox,
                pr.crop_path,
                pr.vehicle_local_id,
                pr.detected_at,
                pr.detection_id,
                d.frame_index,
                d.timestamp,
                d.vehicle_class,
                d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2,
                d.confidence AS det_confidence,
                v.global_id,
                v.plate_text AS vehicle_plate,
                v.id AS vehicle_db_id,
                v.first_seen AS v_first_seen,
                v.last_seen AS v_last_seen,
                j.job_id,
                j.video_filename
            FROM plate_reads pr
            LEFT JOIN detections d ON pr.detection_id = d.id
            LEFT JOIN vehicles v ON pr.vehicle_id = v.id
            LEFT JOIN processing_jobs j ON d.job_id = j.id
            WHERE pr.id = ?
        """, (plate_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return jsonify({"error": "Plate not found"}), 404

        crop_path = row["crop_path"] or ""
        crop_filename = os.path.basename(crop_path) if crop_path else None
        job_id = row["job_id"] or ""

        vehicle_bbox = None
        if row["bbox_x1"] is not None:
            vehicle_bbox = [row["bbox_x1"], row["bbox_y1"], row["bbox_x2"], row["bbox_y2"]]

        # Get all OCR observations for this track
        observations = []
        if row["vehicle_local_id"] and row["job_id"]:
            cur.execute("""
                SELECT pr.plate_text, pr.ocr_confidence, pr.detected_at,
                       d.frame_index, d.timestamp
                FROM plate_reads pr
                LEFT JOIN detections d ON pr.detection_id = d.id
                WHERE pr.vehicle_local_id = ?
                  AND pr.plate_text IS NOT NULL
                ORDER BY pr.ocr_confidence DESC
            """, (row["vehicle_local_id"],))
            for obs in cur.fetchall():
                observations.append({
                    "plateText": obs[0],
                    "ocrConfidence": round(obs[1], 2),
                    "detectedAt": obs[2],
                    "frameIndex": obs[3],
                    "timestamp": round(obs[4], 2) if obs[4] else 0,
                })

        # Get total observations for this track
        cur.execute("""
            SELECT COUNT(*) FROM plate_reads
            WHERE vehicle_local_id = ?
        """, (row["vehicle_local_id"],))
        total_obs = cur.fetchone()[0]

        # Find vehicle evidence
        vehicle_evidence = None
        if job_id and row["vehicle_local_id"]:
            ev_dir = os.path.join(EVIDENCE_DIR, job_id)
            if os.path.isdir(ev_dir):
                for f in os.listdir(ev_dir):
                    if f.startswith(f"vehicle_track{row['vehicle_local_id']}_") or f.startswith(f"vehicle_no_plate_track{row['vehicle_local_id']}_"):
                        vehicle_evidence = f"/api/evidence/{job_id}/{f}"
                        break

        conn.close()

        return jsonify({
            "id": row["id"],
            "plateText": row["plate_text"],
            "rawText": row["raw_text"],
            "ocrConfidence": round(row["ocr_confidence"], 2),
            "plateBbox": row["plate_bbox"],
            "trackId": row["vehicle_local_id"],
            "globalId": row["global_id"],
            "vehiclePlate": row["vehicle_plate"],
            "vehicleDbId": row["vehicle_db_id"],
            "vehicleClass": row["vehicle_class"] or "Unknown",
            "vehicleBbox": vehicle_bbox,
            "detConfidence": round(row["det_confidence"], 2) if row["det_confidence"] else None,
            "frameIndex": row["frame_index"],
            "timestamp": round(row["timestamp"], 2) if row["timestamp"] else 0,
            "detectedAt": row["detected_at"],
            "vehicleFirstSeen": row["v_first_seen"],
            "vehicleLastSeen": row["v_last_seen"],
            "totalObservations": total_obs,
            "jobId": job_id,
            "videoFilename": row["video_filename"],
            "evidenceCrop": f"/api/evidence/{job_id}/{crop_filename}" if crop_filename else None,
            "evidenceFrame": vehicle_evidence,
            "observations": observations,
        })

    except Exception as e:
        logger.error(f"Failed to get plate detail: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
