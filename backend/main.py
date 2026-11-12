import os
import time
import uuid
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import cv2
import numpy as np

from backend.model_loader import load_ai_model, get_model_info, get_model
from backend.detection import run_image_detection, validate_image_file, get_color_for_class
from backend.alert_manager import check_and_generate_alerts, VIOLATION_CLASSES
from backend.video_processor import create_video_job, get_job, VIDEOS_DIR
from backend.database import (
    init_db, log_incident, get_incidents, get_incident_by_id,
    get_incidents_filtered, update_incident_status, get_incident_statistics,
    get_surveillance_summary_stats, get_analytics_overview,
    get_violations_by_category, get_incidents_trend, get_severity_distribution,
    get_source_distribution, get_all_settings, update_system_setting,
    log_generated_report, get_reports_list, get_report_by_id, log_detection_event
)
from backend.reports import generate_csv_report, generate_pdf_report, REPORTS_DIR

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
(EVIDENCE_DIR / "images").mkdir(parents=True, exist_ok=True)
(EVIDENCE_DIR / "videos").mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Live monitoring session tracker
_live_session = {
    "active": False,
    "started_at": None,
    "frames_analyzed": 0,
    "total_detections": 0,
    "total_violations": 0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">>> Starting Industrial Safety AI Surveillance Backend (Phase 1, 2 & 3)...")
    init_db()
    load_ai_model()
    yield
    print(">>> Shutting down Industrial Safety AI Backend...")

app = FastAPI(
    title="AI-Based Intelligent Industrial Safety Surveillance System",
    description="Phase 1 (Image), Phase 2 (Video & Live), Phase 3 (Analytics, Incidents, Reports, Settings)",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mounts
app.mount("/results", StaticFiles(directory=str(RESULTS_DIR)), name="results")
app.mount("/evidence", StaticFiles(directory=str(EVIDENCE_DIR)), name="evidence")

if (FRONTEND_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
if (FRONTEND_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================
class IncidentStatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None

class SettingUpdate(BaseModel):
    key: str
    value: Any

class ReportGenerateRequest(BaseModel):
    report_type: str = "daily"  # daily, weekly, monthly, custom, violation, summary
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    violation_category: Optional[str] = "ALL"
    severity: Optional[str] = "ALL"
    source: Optional[str] = "ALL"
    format: str = "pdf"  # pdf or csv


# ============================================================================
# PHASE 1: CORE IMAGE & MODEL SPECIFICATION ENDPOINTS
# ============================================================================
@app.get("/api/health")
async def health_check():
    """Health check endpoint: returns backend status and model readiness."""
    info = get_model_info()
    return {
        "status": "online",
        "phase": "Phase 3 (Enterprise Platform)",
        "model_status": info.get("status", "Unknown"),
        "model_loaded": info.get("status") == "Ready",
        "device": info.get("device", "CPU (Optimized)"),
        "error": info.get("error")
    }

@app.get("/api/model-info")
async def model_info():
    """Return model details, architecture, actual class names, and device."""
    info = get_model_info()
    classes = info.get("classes", {})
    class_names = list(classes.values()) if isinstance(classes, dict) else classes

    # Clearly report which PPE items are and are not supported by this model
    supported = sorted([c for c in class_names if not c.startswith("no-")])
    violations = sorted([c for c in class_names if c.startswith("no-")])
    unsupported_note = (
        "MASK is NOT a class in this model. "
        "The trained model supports: boots, gloves, goggles, helmet, vest "
        "and their no- violation counterparts. "
        "Mask detection requires a differently trained model."
    )

    return {
        "success": True,
        "model_name": info.get("model_name", "best.pt"),
        "architecture": info.get("architecture", "YOLO DetectionModel"),
        "task": info.get("task", "detect"),
        "status": info.get("status", "Unknown"),
        "total_classes": info.get("total_classes", 0),
        "classes": classes,
        "supported_ppe": supported,
        "violation_classes": violations,
        "unsupported_classes": ["mask"],
        "unsupported_note": unsupported_note,
        "device": info.get("device", "CPU (Optimized)"),
        "device_type": info.get("device_type", "cpu"),
        "default_confidence_threshold": 0.15,
        "model_path": info.get("model_path"),
        "error": info.get("error")
    }

@app.post("/api/detect/image")
def detect_image(
    file: UploadFile = File(...),
    confidence: float = Query(0.15, ge=0.05, le=1.0)
):
    """
    Phase 1: Accept uploaded image, execute real YOLO inference in threadpool,
    log detection events for compliance analytics, and generate safety alert if violations exist.
    """
    contents = file.file.read()
    file_size = len(contents)

    is_valid, error_msg = validate_image_file(file.filename, file_size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    result = run_image_detection(contents, file.filename, conf_threshold=confidence)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Inference failed."))

    # Count compliant vs violation items
    detections = result.get("detections", [])
    compliants = [d for d in detections if not d["class_name"].startswith("no-")]
    violations = [d for d in detections if d["class_name"].startswith("no-")]
    class_counts = {}
    for d in detections:
        c = d["class_name"]
        class_counts[c] = class_counts.get(c, 0) + 1

    # Log to detection_events table for long-term analytics
    log_detection_event(
        source=f"Image: {file.filename}",
        compliant_count=len(compliants),
        violation_count=len(violations),
        class_counts=class_counts
    )

    # Generate safety alert if violations are present in uploaded image
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is not None and violations:
        alert = check_and_generate_alerts(
            frame_bgr=img_bgr,
            detections=detections,
            source=f"Image: {file.filename}"
        )
        if alert:
            result["alert_generated"] = True
            result["incident_id"] = alert["incident_id"]

    return JSONResponse(content=result)


# ============================================================================
# PHASE 2: VIDEO SURVEILLANCE & LIVE MONITORING ENDPOINTS
# ============================================================================
ALLOWED_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

@app.post("/api/detect/video")
async def upload_and_detect_video(
    file: UploadFile = File(...),
    confidence: float = Query(0.15, ge=0.05, le=1.0),
    frame_stride: int = Query(4, ge=1, le=15)
):
    """Accept uploaded video and initiate background asynchronous YOLO processing job."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{ext}'. Allowed: MP4, AVI, MOV, MKV, WEBM"
        )

    unique_name = f"orig_{int(time.time())}_{uuid.uuid4().hex[:6]}{ext}"
    saved_path = VIDEOS_DIR / unique_name

    with open(str(saved_path), "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job = create_video_job(
        filepath=str(saved_path),
        filename=file.filename,
        conf_threshold=confidence,
        frame_stride=frame_stride
    )

    return JSONResponse(content={
        "success": True,
        "message": "Video uploaded and analysis started.",
        "job_id": job.job_id,
        "job": job.to_dict()
    })

@app.get("/api/video/status/{job_id}")
async def get_video_status(job_id: str):
    """Poll progress, status, and metrics for a video processing job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found.")
    return JSONResponse(content={"success": True, "job": job.to_dict()})

@app.post("/api/video/pause/{job_id}")
async def pause_video_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found.")
    job.pause()
    return JSONResponse(content={"success": True, "message": "Job paused.", "job": job.to_dict()})

@app.post("/api/video/resume/{job_id}")
async def resume_video_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found.")
    job.resume()
    return JSONResponse(content={"success": True, "message": "Job resumed.", "job": job.to_dict()})

@app.post("/api/video/stop/{job_id}")
async def stop_video_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found.")
    job.stop()
    return JSONResponse(content={"success": True, "message": "Job stopped.", "job": job.to_dict()})

@app.post("/api/live/start")
async def start_live_session():
    global _live_session
    _live_session = {
        "active": True,
        "started_at": time.time(),
        "frames_analyzed": 0,
        "total_detections": 0,
        "total_violations": 0
    }
    return {"success": True, "message": "Live monitoring session started."}

@app.post("/api/live/stop")
async def stop_live_session():
    global _live_session
    _live_session["active"] = False
    return {"success": True, "message": "Live monitoring session stopped."}

@app.get("/api/live/status")
async def get_live_status():
    global _live_session
    elapsed = round(time.time() - _live_session["started_at"], 1) if _live_session["active"] and _live_session["started_at"] else 0
    return {
        "active": _live_session["active"],
        "elapsed_seconds": elapsed,
        "frames_analyzed": _live_session["frames_analyzed"],
        "total_detections": _live_session["total_detections"],
        "total_violations": _live_session["total_violations"]
    }

@app.post("/api/live/detect-frame")
def detect_live_frame(
    file: UploadFile = File(...),
    confidence: float = Query(0.15, ge=0.05, le=1.0)
):
    """
    Process single webcam frame in threadpool: executes YOLO inference,
    updates session metrics, and generates rate-limited safety alerts without blocking event loop.
    """
    global _live_session
    model = get_model()
    if model is None:
        raise HTTPException(status_code=503, detail="AI Model is not ready.")

    contents = file.file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame_bgr is None:
        raise HTTPException(status_code=400, detail="Invalid camera frame.")

    start_time = time.time()
    results = model.predict(
        source=frame_bgr,
        conf=confidence,
        iou=0.45,
        imgsz=640,
        device="cpu",
        verbose=False,
        agnostic_nms=False,
        max_det=100
    )
    inference_time = round(time.time() - start_time, 3)

    detections = []
    violations = []
    
    for r in results:
        names = r.names
        for box in r.boxes:
            cls_id = int(box.cls[0].item())
            cls_name = names.get(cls_id, f"class_{cls_id}")
            conf = round(float(box.conf[0].item()), 2)
            coords = [int(v) for v in box.xyxy[0].tolist()]

            det_item = {
                "class_id": cls_id,
                "class_name": cls_name,
                "confidence": conf,
                "bbox": coords,
                "color": get_color_for_class(cls_name)
            }
            detections.append(det_item)

            if cls_name in VIOLATION_CLASSES:
                violations.append(det_item)

    # Check and generate safety alerts with cooldown protection
    alert = None
    if violations:
        alert = check_and_generate_alerts(
            frame_bgr=frame_bgr,
            detections=detections,
            source="Live Webcam"
        )

    # Update live session metrics
    if _live_session["active"]:
        _live_session["frames_analyzed"] += 1
        _live_session["total_detections"] += len(detections)
        _live_session["total_violations"] += len(violations)

    return JSONResponse(content={
        "success": True,
        "inference_time": inference_time,
        "total_detections": len(detections),
        "total_violations": len(violations),
        "detections": detections,
        "violations": violations,
        "alert_generated": alert is not None,
        "new_alert": alert
    })

@app.get("/api/surveillance/stats")
def get_surveillance_stats():
    """Retrieve dynamic aggregated metrics from SQLite for videos and compliance."""
    stats = get_surveillance_summary_stats()
    return JSONResponse(content={"success": True, "stats": stats})


# ============================================================================
# PHASE 3: ADVANCED ANALYTICS ENDPOINTS
# ============================================================================
@app.get("/api/analytics/overview")
def api_analytics_overview(
    time_range: str = Query("30d"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category: Optional[str] = Query("ALL"),
    severity: Optional[str] = Query("ALL"),
    source: Optional[str] = Query("ALL")
):
    """Retrieve summary KPIs, violation counts, and compliance rate across filters."""
    stats = get_analytics_overview(
        time_range=time_range,
        start_date=start_date,
        end_date=end_date,
        category=category,
        severity=severity,
        source=source
    )
    return JSONResponse(content={"success": True, "analytics": stats, **stats})

@app.get("/api/analytics/violations")
def api_analytics_violations(
    time_range: str = Query("30d"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Return violation counts categorized by PPE type."""
    data = get_violations_by_category(time_range=time_range, start_date=start_date, end_date=end_date)
    return JSONResponse(content={"success": True, "violations": data})

@app.get("/api/analytics/trends")
def api_analytics_trends(days: int = Query(14, ge=1, le=90)):
    """Return daily trend of recorded incidents for line charts."""
    trends = get_incidents_trend(days=days)
    return JSONResponse(content={"success": True, "trends": trends})

@app.get("/api/analytics/severity")
def api_analytics_severity():
    """Return breakdown of incidents grouped by severity priority."""
    dist = get_severity_distribution()
    return JSONResponse(content={"success": True, "severity_distribution": dist})

@app.get("/api/analytics/sources")
def api_analytics_sources():
    """Return incident distribution by detection origin."""
    dist = get_source_distribution()
    return JSONResponse(content={"success": True, "source_distribution": dist})


# ============================================================================
# PHASE 3: INCIDENT MANAGEMENT ENDPOINTS
# ============================================================================
@app.get("/api/incidents")
def list_incidents_filtered(
    search: Optional[str] = Query(None),
    violation: Optional[str] = Query("ALL"),
    category: Optional[str] = Query("ALL"),
    severity: Optional[str] = Query("ALL"),
    source: Optional[str] = Query("ALL"),
    status: Optional[str] = Query("ALL"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    sort_by: str = Query("timestamp"),
    sort_order: str = Query("desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Retrieve filtered, searched, and paginated incident records from SQLite."""
    eff_violation = category if (category and category != "ALL") else violation
    res = get_incidents_filtered(
        search=search,
        violation=eff_violation,
        severity=severity,
        source=source,
        status=status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    return JSONResponse(content={"success": True, **res})

@app.get("/api/incidents/{incident_id}")
def get_single_incident(incident_id: str):
    """Retrieve full detail for an incident."""
    inc = get_incident_by_id(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return JSONResponse(content={"success": True, "incident": inc})

@app.patch("/api/incidents/{incident_id}/status")
@app.post("/api/incidents/{incident_id}/status")
def update_status(incident_id: str, payload: IncidentStatusUpdate):
    """Update status (NEW, ACKNOWLEDGED, RESOLVED) and optional resolution notes."""
    success = update_incident_status(
        incident_id=incident_id,
        new_status=payload.status,
        notes=payload.resolution_notes
    )
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return {"success": True, "message": f"Incident {incident_id} updated to {payload.status.upper()}."}


# ============================================================================
# ALERTS & INCIDENT AUDIT ENDPOINTS
# ============================================================================
@app.get("/api/alerts")
def list_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None)
):
    """Retrieve safety violation alerts and incident logs from SQLite."""
    incidents = get_incidents(limit=limit, offset=offset, status=status, severity=severity)
    stats = get_incident_statistics()
    return JSONResponse(content={
        "success": True,
        "incidents": incidents,
        "statistics": stats
    })

@app.post("/api/alerts/{incident_id}/acknowledge")
def acknowledge_alert(incident_id: str):
    """Mark an incident alert as acknowledged."""
    success = update_incident_status(incident_id, "ACKNOWLEDGED")
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return {"success": True, "message": f"Incident {incident_id} acknowledged."}

@app.post("/api/alerts/{incident_id}/resolve")
def resolve_alert(incident_id: str, notes: Optional[str] = Body(None, embed=True)):
    """Mark an incident alert as resolved with resolution notes."""
    success = update_incident_status(incident_id, "RESOLVED", notes=notes)
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return {"success": True, "message": f"Incident {incident_id} resolved."}

@app.post("/api/alerts/{incident_id}/dismiss")
def dismiss_alert(incident_id: str):
    """Mark an incident alert as dismissed (archived)."""
    success = update_incident_status(incident_id, "DISMISSED")
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return {"success": True, "message": f"Incident {incident_id} dismissed."}

@app.get("/api/evidence")
def list_evidence(limit: int = 40):
    """Retrieve evidence snapshots saved from safety violations."""
    incidents = get_incidents(limit=limit, status="ALL")
    evidence_items = [
        {
            "incident_id": inc["incident_id"],
            "violation": inc["violation_category"],
            "severity": inc["severity"],
            "confidence": inc["confidence"],
            "timestamp": inc["timestamp"],
            "source": inc["source"],
            "evidence_url": inc["evidence_path"],
            "status": inc["status"]
        }
        for inc in incidents if inc.get("evidence_path")
    ]
    return JSONResponse(content={"success": True, "evidence": evidence_items})

@app.get("/api/evidence/{incident_id}")
def get_incident_evidence(incident_id: str):
    inc = get_incident_by_id(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return JSONResponse(content={"success": True, "incident": inc})


# ============================================================================
# PHASE 3: REPORT GENERATION & EXPORT ENDPOINTS
# ============================================================================
@app.get("/api/reports/summary")
def get_reports_summary():
    """Retrieve history of recently generated reports and quick stats."""
    history = get_reports_list(limit=25)
    total_incidents = get_incident_statistics().get("total", 0)
    return JSONResponse(content={
        "success": True,
        "recent_reports": history,
        "total_logged_incidents": total_incidents
    })

@app.post("/api/reports/generate")
def generate_report_endpoint(req: ReportGenerateRequest):
    """Generate professional PDF or CSV report based on filtered real database records."""
    # Compute date ranges if not explicitly provided
    start_date = req.start_date
    end_date = req.end_date
    now = datetime.now()
    if not start_date:
        if req.report_type == "daily":
            start_date = now.strftime("%Y-%m-%d 00:00:00")
            end_date = now.strftime("%Y-%m-%d 23:59:59")
        elif req.report_type == "weekly":
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
            end_date = now.strftime("%Y-%m-%d 23:59:59")
        elif req.report_type == "monthly":
            start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
            end_date = now.strftime("%Y-%m-%d 23:59:59")

    # 1. Fetch filtered incident records
    res = get_incidents_filtered(
        violation=req.violation_category,
        severity=req.severity,
        source=req.source,
        start_date=start_date,
        end_date=end_date,
        limit=500
    )
    incidents = res.get("incidents", [])

    # 2. Get analytics overview for report stats banner
    overview = get_analytics_overview(
        start_date=start_date,
        end_date=end_date,
        category=req.violation_category,
        severity=req.severity,
        source=req.source
    )

    title = req.title or f"Industrial Safety Audit Report — {req.report_type.capitalize()}"

    # 3. Generate file in requested format
    fmt = req.format.lower()
    if fmt == "csv":
        filepath = generate_csv_report(
            incidents=incidents,
            report_type=req.report_type,
            title=title,
            start_date=start_date,
            end_date=end_date
        )
    else:
        filepath = generate_pdf_report(
            incidents=incidents,
            report_type=req.report_type,
            title=title,
            start_date=start_date,
            end_date=end_date,
            stats=overview
        )

    report_id = Path(filepath).stem
    log_generated_report(
        report_id=report_id,
        report_type=req.report_type,
        title=title,
        start_date=start_date or "Earliest",
        end_date=end_date or "Present",
        total_incidents=len(incidents),
        fmt=fmt,
        file_path=str(filepath)
    )

    download_url = f"/api/reports/download/{report_id}"
    return JSONResponse(content={
        "success": True,
        "message": f"{fmt.upper()} report generated successfully.",
        "report_id": report_id,
        "format": fmt,
        "records_count": len(incidents),
        "download_url": download_url
    })

@app.get("/api/reports/download/{report_id}")
def download_report_file(report_id: str):
    """Download generated report file (PDF or CSV)."""
    rpt = get_report_by_id(report_id)
    if not rpt:
        # Check direct filesystem if not in db
        potential_pdf = REPORTS_DIR / f"{report_id}.pdf"
        potential_csv = REPORTS_DIR / f"{report_id}.csv"
        if potential_pdf.exists():
            return FileResponse(str(potential_pdf), media_type="application/pdf", filename=f"{report_id}.pdf")
        elif potential_csv.exists():
            return FileResponse(str(potential_csv), media_type="text/csv", filename=f"{report_id}.csv")
        raise HTTPException(status_code=404, detail="Report file not found.")

    filepath = Path(rpt["file_path"])
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Report file does not exist on disk.")

    media_type = "application/pdf" if rpt["format"] == "pdf" else "text/csv"
    return FileResponse(str(filepath), media_type=media_type, filename=filepath.name)


# ============================================================================
# PHASE 3: SYSTEM SETTINGS ENDPOINTS
# ============================================================================
@app.get("/api/settings")
def get_system_settings():
    """Retrieve system configuration and storage diagnostics."""
    settings = get_all_settings()
    
    # Calculate evidence directory disk storage
    evidence_size_bytes = 0
    images_count = 0
    videos_count = 0
    reports_count = 0

    if EVIDENCE_DIR.exists():
        for p in EVIDENCE_DIR.rglob("*"):
            if p.is_file():
                evidence_size_bytes += p.stat().st_size
                if p.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    images_count += 1
                elif p.suffix.lower() in (".mp4", ".avi", ".mov"):
                    videos_count += 1
                elif p.suffix.lower() in (".pdf", ".csv"):
                    reports_count += 1

    db_size_bytes = 0
    from backend.database import DB_PATH
    if DB_PATH.exists():
        db_size_bytes = DB_PATH.stat().st_size

    model_info = get_model_info()
    inc_stats = get_incident_statistics()

    return JSONResponse(content={
        "success": True,
        "settings": settings,
        "database_size_bytes": db_size_bytes,
        "evidence_storage_bytes": evidence_size_bytes,
        "total_logged_incidents": inc_stats.get("total", 0),
        "evidence_counts": {
            "images": images_count,
            "videos": videos_count,
            "reports": reports_count
        },
        "system_info": {
            "app_version": "3.0.0",
            "phase": "Phase 3: Advanced Analytics, Incidents, Reports & Settings",
            "model_name": model_info.get("model_name", "best.pt"),
            "model_status": model_info.get("status", "Ready"),
            "device": model_info.get("device", "CPU (Optimized)"),
            "database_status": "Connected (SQLite WAL)",
            "database_size_kb": round(db_size_bytes / 1024, 1),
            "evidence_storage_mb": round(evidence_size_bytes / (1024 * 1024), 2),
            "total_evidence_images": images_count,
            "total_evidence_videos": videos_count,
            "total_generated_reports": reports_count
        }
    })

@app.post("/api/settings")
@app.put("/api/settings")
def save_system_setting(payload: Dict[str, Any] = Body(...)):
    """Update and persist one or more system configuration settings."""
    alias_map = {
        "min_severity_level": "min_severity_alert",
    }
    allowed_keys = {
        "model_confidence_threshold", "video_frame_stride",
        "alert_cooldown_seconds", "min_severity_alert",
        "evidence_capture_mode", "app_name", "facility_name",
        "retention_days"
    }

    # Case 1: single key-value format {"key": "...", "value": "..."}
    if "key" in payload and "value" in payload and len(payload) == 2:
        k = alias_map.get(payload["key"], payload["key"])
        if k in allowed_keys:
            update_system_setting(k, payload["value"])
            return {"success": True, "message": f"Setting '{k}' updated.", "key": k, "value": payload["value"]}

    # Case 2: dictionary of multiple settings
    updated = {}
    for k, v in payload.items():
        eff_k = alias_map.get(k, k)
        if eff_k in allowed_keys:
            update_system_setting(eff_k, v)
            updated[eff_k] = v

    return {"success": True, "message": f"Updated {len(updated)} settings.", "updated": updated}


# ============================================================================
# PRIMARY APPLICATION ROUTE
# ============================================================================
@app.get("/")
async def serve_index():
    """Serve the primary Single Page Application."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "Frontend not found at frontend/index.html"}, status_code=404)
