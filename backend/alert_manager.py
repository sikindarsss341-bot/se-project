import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import cv2
import numpy as np

from backend.database import log_incident
from backend.detection import draw_sleek_annotations

EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence" / "images"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Violation categories defined in the model
VIOLATION_CLASSES = {"no-boots", "no-gloves", "no-goggles", "no-helmet", "no-vest"}

# In-memory cooldown tracker: (source, violation_key) -> last_alert_epoch_seconds
_alert_cooldowns: Dict[str, float] = {}
COOLDOWN_SECONDS = 5.0

def determine_severity(violations: List[str]) -> str:
    """
    Determine alert severity based on detected violations:
    - CRITICAL: Multiple violations in the same frame
    - HIGH: no-helmet or no-vest (high injury / fatal risk)
    - MEDIUM: no-gloves, no-goggles, or no-boots
    """
    if len(violations) > 1:
        return "CRITICAL"
    
    v = violations[0]
    if v in ("no-helmet", "no-vest"):
        return "HIGH"
    return "MEDIUM"

def save_evidence_frame(frame_bgr: np.ndarray, detections: List[Dict[str, Any]], incident_id: str) -> str:
    """Save an annotated evidence snapshot with bounding boxes to disk."""
    annotated = draw_sleek_annotations(frame_bgr, detections)
    filename = f"evidence_{incident_id}.jpg"
    filepath = EVIDENCE_DIR / filename
    cv2.imwrite(str(filepath), annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    return f"/evidence/images/{filename}"

def check_and_generate_alerts(
    frame_bgr: np.ndarray,
    detections: List[Dict[str, Any]],
    source: str = "Live Webcam",
    video_timestamp: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Evaluate detections for safety violations.
    If violations are present and cooldown has elapsed, generates an alert,
    persists evidence snapshot, and logs the incident in the SQLite database.
    """
    violations = [d for d in detections if d.get("class_name") in VIOLATION_CLASSES]
    if not violations:
        return None

    violation_names = sorted(list(set(d["class_name"] for d in violations)))
    violation_key = f"{source}:{'-'.join(violation_names)}"

    now = time.time()
    last_time = _alert_cooldowns.get(violation_key, 0.0)
    
    if (now - last_time) < COOLDOWN_SECONDS:
        # Cooldown active; skip duplicate alert generation
        return None

    _alert_cooldowns[violation_key] = now

    incident_id = f"INC-{int(now)}-{uuid.uuid4().hex[:6].upper()}"
    severity = determine_severity(violation_names)
    primary_category = ", ".join(violation_names)
    highest_conf = max(d["confidence"] for d in violations)

    evidence_url = save_evidence_frame(frame_bgr, detections, incident_id)

    incident_record = log_incident(
        incident_id=incident_id,
        violation_category=primary_category,
        violations_list=violation_names,
        confidence=highest_conf,
        source=source,
        severity=severity,
        evidence_path=evidence_url,
        video_timestamp=video_timestamp,
        details={
            "total_detections_in_frame": len(detections),
            "violation_details": violations
        }
    )

    return incident_record
