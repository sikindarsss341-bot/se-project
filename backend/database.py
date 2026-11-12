import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

DB_PATH = Path(__file__).resolve().parent / "data" / "surveillance.db"

def get_connection():
    """Create and return a SQLite database connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables and run safe migrations with indexing."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Incidents / Alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT UNIQUE NOT NULL,
            violation_category TEXT NOT NULL,
            violations_list TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            severity TEXT NOT NULL,
            evidence_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'NEW',
            video_timestamp TEXT,
            details TEXT,
            resolved_at TEXT,
            resolution_notes TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_id ON incidents(incident_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_ts ON incidents(timestamp)")

    # Migration check for existing incidents table
    cursor.execute("PRAGMA table_info(incidents)")
    existing_cols = [r["name"] for r in cursor.fetchall()]
    if "resolved_at" not in existing_cols:
        cursor.execute("ALTER TABLE incidents ADD COLUMN resolved_at TEXT")
    if "resolution_notes" not in existing_cols:
        cursor.execute("ALTER TABLE incidents ADD COLUMN resolution_notes TEXT")

    # 2. Video processing summary audit table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            duration_seconds REAL DEFAULT 0,
            total_frames INTEGER DEFAULT 0,
            frames_processed INTEGER DEFAULT 0,
            total_detections INTEGER DEFAULT 0,
            total_violations INTEGER DEFAULT 0,
            compliance_rate REAL DEFAULT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_status ON video_records(status)")

    # 3. Detection events table (for true object-level compliance analytics)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            compliant_count INTEGER DEFAULT 0,
            violation_count INTEGER DEFAULT 0,
            class_counts TEXT DEFAULT '{}'
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_ts ON detection_events(timestamp)")

    # 4. Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            category TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Populate default system settings if empty
    cursor.execute("SELECT COUNT(*) as count FROM settings")
    if cursor.fetchone()["count"] == 0:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        default_settings = [
            ("model_confidence_threshold", "0.15", "model", now_str),
            ("video_frame_stride", "4", "detection", now_str),
            ("alert_cooldown_seconds", "5.0", "detection", now_str),
            ("min_severity_alert", "MEDIUM", "detection", now_str),
            ("evidence_capture_mode", "violations_only", "detection", now_str),
            ("app_name", "Industrial Safety AI Surveillance", "application", now_str),
            ("facility_name", "Main Manufacturing Plant", "application", now_str),
            ("retention_days", "90", "storage", now_str)
        ]
        cursor.executemany("INSERT INTO settings (key, value, category, updated_at) VALUES (?, ?, ?, ?)", default_settings)

    # 5. Reports history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE NOT NULL,
            report_type TEXT NOT NULL,
            title TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            total_incidents INTEGER DEFAULT 0,
            format TEXT NOT NULL,
            file_path TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_id ON reports_history(report_id)")

    conn.commit()
    conn.close()


# ============================================================================
# INCIDENT / ALERT FUNCTIONS
# ============================================================================
def log_incident(
    incident_id: str,
    violation_category: str,
    violations_list: list,
    confidence: float,
    source: str,
    severity: str,
    evidence_path: str,
    video_timestamp: Optional[str] = None,
    details: Optional[dict] = None
) -> dict:
    """Insert a new safety violation incident into SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    violations_json = json.dumps(violations_list)
    details_json = json.dumps(details or {})

    cursor.execute("""
        INSERT INTO incidents (
            incident_id, violation_category, violations_list, confidence,
            timestamp, source, severity, evidence_path, status, video_timestamp, details
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?)
    """, (
        incident_id,
        violation_category,
        violations_json,
        round(confidence, 2),
        now_str,
        source,
        severity,
        evidence_path,
        video_timestamp,
        details_json
    ))
    conn.commit()
    conn.close()

    return {
        "incident_id": incident_id,
        "violation_category": violation_category,
        "confidence": confidence,
        "timestamp": now_str,
        "source": source,
        "severity": severity,
        "evidence_path": evidence_path,
        "status": "NEW"
    }

def get_incidents_filtered(
    search: Optional[str] = None,
    violation: Optional[str] = None,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Retrieve filtered, searched, sorted, and paginated incident records."""
    conn = get_connection()
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if search:
        conditions.append("(incident_id LIKE ? OR violation_category LIKE ? OR source LIKE ? OR resolution_notes LIKE ?)")
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if violation and violation.upper() != "ALL":
        conditions.append("violation_category = ?")
        params.append(violation)

    if severity and severity.upper() != "ALL":
        conditions.append("severity = ?")
        params.append(severity.upper())

    if source and source.upper() != "ALL":
        conditions.append("source LIKE ?")
        params.append(f"%{source}%")

    if status and status.upper() != "ALL":
        conditions.append("status = ?")
        params.append(status.upper())

    if start_date:
        conditions.append("timestamp >= ?")
        params.append(f"{start_date} 00:00:00")

    if end_date:
        conditions.append("timestamp <= ?")
        params.append(f"{end_date} 23:59:59")

    where_clause = " AND ".join(conditions)

    # Count total matching rows
    cursor.execute(f"SELECT COUNT(*) as count FROM incidents WHERE {where_clause}", params)
    total_count = cursor.fetchone()["count"]

    # Allowed sort columns to avoid SQL injection
    allowed_sort_cols = {
        "timestamp": "timestamp",
        "confidence": "confidence",
        "severity": "severity",
        "status": "status",
        "incident_id": "incident_id"
    }
    col = allowed_sort_cols.get(sort_by, "id")
    direction = "DESC" if sort_order.lower() == "desc" else "ASC"

    # Query rows
    query = f"SELECT * FROM incidents WHERE {where_clause} ORDER BY {col} {direction} LIMIT ? OFFSET ?"
    query_params = list(params)
    query_params.extend([limit, offset])

    cursor.execute(query, query_params)
    rows = cursor.fetchall()
    conn.close()

    items = []
    for r in rows:
        item = dict(r)
        try:
            item["violations_list"] = json.loads(item["violations_list"])
        except Exception:
            item["violations_list"] = [item["violation_category"]]
        try:
            item["details"] = json.loads(item["details"]) if item.get("details") else {}
        except Exception:
            item["details"] = {}
        items.append(item)

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "incidents": items
    }

def get_incidents(limit: int = 50, offset: int = 0, status: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Backward compatible incident list."""
    res = get_incidents_filtered(status=status, severity=severity, limit=limit, offset=offset)
    return res["incidents"]

def get_incident_by_id(incident_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full details for a single incident."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    try:
        item["violations_list"] = json.loads(item["violations_list"])
    except Exception:
        item["violations_list"] = [item["violation_category"]]
    try:
        item["details"] = json.loads(item["details"]) if item.get("details") else {}
    except Exception:
        item["details"] = {}
    return item

def update_incident_status(incident_id: str, new_status: str, notes: Optional[str] = None) -> bool:
    """Update status (NEW, ACKNOWLEDGED, RESOLVED) and resolution notes for an incident."""
    conn = get_connection()
    cursor = conn.cursor()
    status_upper = new_status.upper()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if status_upper == "RESOLVED":
        cursor.execute("""
            UPDATE incidents 
            SET status = ?, resolved_at = ?, resolution_notes = COALESCE(?, resolution_notes)
            WHERE incident_id = ?
        """, (status_upper, now_str, notes, incident_id))
    elif status_upper == "NEW":
        cursor.execute("""
            UPDATE incidents 
            SET status = ?, resolved_at = NULL
            WHERE incident_id = ?
        """, (status_upper, incident_id))
    else:
        cursor.execute("""
            UPDATE incidents 
            SET status = ?, resolution_notes = COALESCE(?, resolution_notes)
            WHERE incident_id = ?
        """, (status_upper, notes, incident_id))

    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_incident_statistics() -> Dict[str, int]:
    """Return counts for incident & alert KPI badges."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high,
            SUM(CASE WHEN severity = 'MEDIUM' THEN 1 ELSE 0 END) as medium,
            SUM(CASE WHEN status = 'NEW' THEN 1 ELSE 0 END) as unacknowledged,
            SUM(CASE WHEN status = 'ACKNOWLEDGED' THEN 1 ELSE 0 END) as acknowledged,
            SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved
        FROM incidents
    """)
    row = cursor.fetchone()
    conn.close()
    return {
        "total": row["total"] or 0,
        "critical": row["critical"] or 0,
        "high": row["high"] or 0,
        "medium": row["medium"] or 0,
        "unacknowledged": row["unacknowledged"] or 0,
        "acknowledged": row["acknowledged"] or 0,
        "resolved": row["resolved"] or 0
    }


# ============================================================================
# DETECTION EVENTS & COMPLIANCE LOGGING
# ============================================================================
def log_detection_event(source: str, compliant_count: int, violation_count: int, class_counts: dict) -> None:
    """Log an object detection summary event for long-term compliance analytics."""
    conn = get_connection()
    cursor = conn.cursor()
    event_id = f"evt_{int(datetime.now().timestamp() * 1000)}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO detection_events (event_id, source, timestamp, compliant_count, violation_count, class_counts)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        source,
        now_str,
        compliant_count,
        violation_count,
        json.dumps(class_counts)
    ))
    conn.commit()
    conn.close()

def record_video_job_completion(
    job_id: str,
    filename: str,
    duration_seconds: float,
    total_frames: int,
    frames_processed: int,
    total_detections: int,
    total_violations: int,
    compliance_rate: Optional[float]
):
    """Save completed video processing statistics to audit table."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT OR REPLACE INTO video_records (
            job_id, filename, duration_seconds, total_frames,
            frames_processed, total_detections, total_violations,
            compliance_rate, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
    """, (
        job_id,
        filename,
        round(duration_seconds, 2),
        total_frames,
        frames_processed,
        total_detections,
        total_violations,
        round(compliance_rate, 1) if compliance_rate is not None else None,
        now_str
    ))
    conn.commit()
    conn.close()


# ============================================================================
# SURVEILLANCE & ADVANCED ANALYTICS QUERIES
# ============================================================================
def get_surveillance_summary_stats() -> Dict[str, Any]:
    """Calculate dynamic surveillance statistics from actual database records."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) as videos_analyzed,
            COALESCE(SUM(total_detections), 0) as total_detections,
            COALESCE(SUM(total_violations), 0) as total_violations
        FROM video_records 
        WHERE status = 'completed'
    """)
    row = cursor.fetchone()

    # Also count incidents from incidents table
    cursor.execute("SELECT COUNT(*) as incident_count FROM incidents")
    inc_row = cursor.fetchone()
    conn.close()

    videos_count = row["videos_analyzed"] if row else 0
    total_dets = row["total_detections"] if row else 0
    total_viols = (row["total_violations"] if row else 0) + (inc_row["incident_count"] if inc_row else 0)

    if total_dets > 0:
        compliance_pct = round(max(0.0, (total_dets - total_viols) / total_dets) * 100, 1)
        compliance_display = f"{compliance_pct}%"
    else:
        compliance_display = "Not enough data"

    return {
        "videos_analyzed": videos_count,
        "total_detections": total_dets,
        "safety_violations": total_viols,
        "total_violations": total_viols,
        "compliance_rate": compliance_display
    }

def get_analytics_overview(
    time_range: str = "30d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    source: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate dynamic analytics metrics across incidents, video runs, and detection events.
    Formula:
    Compliance Rate = (Compliant Detections / Total Detections) * 100
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Determine date range
    now = datetime.now()
    if time_range == "today":
        computed_start = now.strftime("%Y-%m-%d 00:00:00")
    elif time_range == "7d":
        computed_start = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
    elif time_range == "90d":
        computed_start = (now - timedelta(days=90)).strftime("%Y-%m-%d 00:00:00")
    elif time_range == "custom" and start_date:
        computed_start = f"{start_date} 00:00:00"
    else:  # 30d default
        computed_start = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")

    computed_end = f"{end_date} 23:59:59" if (time_range == "custom" and end_date) else now.strftime("%Y-%m-%d 23:59:59")

    # Incidents query with filters
    inc_conds = ["timestamp >= ? AND timestamp <= ?"]
    inc_params = [computed_start, computed_end]

    if category and category.upper() != "ALL":
        inc_conds.append("violation_category = ?")
        inc_params.append(category)
    if severity and severity.upper() != "ALL":
        inc_conds.append("severity = ?")
        inc_params.append(severity.upper())
    if source and source.upper() != "ALL":
        inc_conds.append("source LIKE ?")
        inc_params.append(f"%{source}%")

    inc_where = " AND ".join(inc_conds)

    cursor.execute(f"""
        SELECT 
            COUNT(*) as total_incidents,
            SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_incidents,
            SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved_incidents,
            SUM(CASE WHEN status = 'ACKNOWLEDGED' THEN 1 ELSE 0 END) as acknowledged_incidents,
            SUM(CASE WHEN status = 'NEW' THEN 1 ELSE 0 END) as open_incidents
        FROM incidents
        WHERE {inc_where}
    """, inc_params)
    inc_stats = cursor.fetchone()

    # Detections query (detection events + video records)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(compliant_count), 0) as compliant_detections,
            COALESCE(SUM(violation_count), 0) as violation_detections
        FROM detection_events
        WHERE timestamp >= ? AND timestamp <= ?
    """, (computed_start, computed_end))
    det_stats = cursor.fetchone()

    # Also pull detections from video records
    cursor.execute("""
        SELECT 
            COALESCE(SUM(total_detections), 0) as video_total_dets,
            COALESCE(SUM(total_violations), 0) as video_total_viols
        FROM video_records
        WHERE status = 'completed' AND created_at >= ? AND created_at <= ?
    """, (computed_start, computed_end))
    vid_stats = cursor.fetchone()

    total_incidents = inc_stats["total_incidents"] or 0
    critical_incidents = inc_stats["critical_incidents"] or 0
    resolved_incidents = inc_stats["resolved_incidents"] or 0
    open_incidents = inc_stats["open_incidents"] or 0

    # Aggregate compliant vs violation detections
    compliant_dets = (det_stats["compliant_detections"] or 0) + max(0, (vid_stats["video_total_dets"] or 0) - (vid_stats["video_total_viols"] or 0))
    violation_dets = (det_stats["violation_detections"] or 0) + (vid_stats["video_total_viols"] or 0) + total_incidents
    total_dets = compliant_dets + violation_dets

    if total_dets > 0:
        compliance_pct = round((compliant_dets / total_dets) * 100, 1)
        compliance_str = f"{compliance_pct}%"
    else:
        compliance_pct = None
        compliance_str = "Not enough data"

    conn.close()

    return {
        "time_range": time_range,
        "start_date": computed_start,
        "end_date": computed_end,
        "total_incidents": total_incidents,
        "critical_incidents": critical_incidents,
        "resolved_incidents": resolved_incidents,
        "open_incidents": open_incidents,
        "compliant_detections": compliant_dets,
        "violation_detections": violation_dets,
        "total_detections": total_dets,
        "compliance_rate": compliance_str,
        "compliance_percentage": compliance_pct,
        "formula": "(Compliant PPE Detections / Total PPE Detections) * 100"
    }

def get_violations_by_category(time_range: str = "30d", start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return count of incidents per PPE violation category."""
    conn = get_connection()
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []
    if start_date:
        conditions.append("timestamp >= ?")
        params.append(f"{start_date} 00:00:00")
    if end_date:
        conditions.append("timestamp <= ?")
        params.append(f"{end_date} 23:59:59")

    where_str = " AND ".join(conditions)

    cursor.execute(f"""
        SELECT violation_category, COUNT(*) as count 
        FROM incidents 
        WHERE {where_str}
        GROUP BY violation_category
        ORDER BY count DESC
    """, params)
    rows = cursor.fetchall()
    conn.close()

    categories = ["no-helmet", "no-vest", "no-gloves", "no-goggles", "no-boots"]
    cat_counts = {c: 0 for c in categories}
    for r in rows:
        cat = r["violation_category"]
        if cat in cat_counts:
            cat_counts[cat] += r["count"]
        else:
            cat_counts[cat] = r["count"]

    return [{"category": k, "count": v} for k, v in cat_counts.items()]

def get_incidents_trend(days: int = 14) -> List[Dict[str, Any]]:
    """Return daily trend of recorded incidents for line chart."""
    conn = get_connection()
    cursor = conn.cursor()

    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
    cursor.execute("""
        SELECT SUBSTR(timestamp, 1, 10) as day, COUNT(*) as incident_count
        FROM incidents
        WHERE timestamp >= ?
        GROUP BY day
        ORDER BY day ASC
    """, (start_date,))
    rows = cursor.fetchall()
    conn.close()

    data_map = {r["day"]: r["incident_count"] for r in rows}
    result = []
    for i in range(days + 1):
        d_str = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
        result.append({
            "date": d_str,
            "count": data_map.get(d_str, 0)
        })
    return result

def get_severity_distribution() -> Dict[str, int]:
    """Return counts per severity level for doughnut chart."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT severity, COUNT(*) as count
        FROM incidents
        GROUP BY severity
    """)
    rows = cursor.fetchall()
    conn.close()

    dist = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
    for r in rows:
        sev = r["severity"].upper()
        dist[sev] = r["count"]
    return dist

def get_source_distribution() -> Dict[str, int]:
    """Return breakdown of incident sources (Image, Video, Live Monitoring)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN source LIKE '%Image%' THEN 1 ELSE 0 END) as image_count,
            SUM(CASE WHEN source LIKE '%Video%' THEN 1 ELSE 0 END) as video_count,
            SUM(CASE WHEN source LIKE '%Live%' OR source LIKE '%Webcam%' THEN 1 ELSE 0 END) as live_count
        FROM incidents
    """)
    row = cursor.fetchone()
    conn.close()
    return {
        "Image Detection": row["image_count"] or 0,
        "Video Detection": row["video_count"] or 0,
        "Live Monitoring": row["live_count"] or 0
    }


# ============================================================================
# SYSTEM SETTINGS FUNCTIONS
# ============================================================================
def get_all_settings() -> Dict[str, Any]:
    """Retrieve all current system settings from database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value, category FROM settings")
    rows = cursor.fetchall()
    conn.close()

    result = {}
    for r in rows:
        val = r["value"]
        # Parse numbers if applicable
        try:
            if "." in val:
                val = float(val)
            else:
                val = int(val)
        except ValueError:
            pass
        result[r["key"]] = val
    return result

def update_system_setting(key: str, value: Any) -> bool:
    """Save an updated setting to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO settings (key, value, category, updated_at)
        VALUES (?, ?, 'custom', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
    """, (key, str(value), now_str))
    conn.commit()
    conn.close()
    return True


# ============================================================================
# REPORT LOGGING FUNCTIONS
# ============================================================================
def log_generated_report(report_id: str, report_type: str, title: str, start_date: str, end_date: str, total_incidents: int, fmt: str, file_path: str):
    """Log generated report metadata."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO reports_history (report_id, report_type, title, start_date, end_date, total_incidents, format, file_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id, report_type, title, start_date, end_date, total_incidents, fmt, file_path, now_str
    ))
    conn.commit()
    conn.close()

def get_reports_list(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve history of generated reports."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    """Find report record by unique report_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports_history WHERE report_id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# Auto-initialize database schema on module import
init_db()
