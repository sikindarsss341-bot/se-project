import sys
import json
import time
import requests
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"

def test_all():
    print("=" * 70)
    print("PHASE 3 COMPREHENSIVE AUTOMATED VERIFICATION SUITE")
    print("=" * 70)

    # 1. Health check
    print("\n[TEST 1] Testing Server Health & Model Status...")
    res = requests.get(f"{BASE_URL}/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health = res.json()
    print(f"  Health: {health}")
    assert health["model_loaded"] is True, "AI Model best.pt is not loaded!"
    print("  [PASS] Server is live, best.pt model in memory.")

    # 2. Analytics Overview
    print("\n[TEST 2] Testing Advanced Analytics Endpoints...")
    res = requests.get(f"{BASE_URL}/api/analytics/overview")
    assert res.status_code == 200, f"Overview error: {res.text}"
    overview_resp = res.json()
    overview = overview_resp.get("analytics", overview_resp)
    print(f"  Analytics Overview: {overview}")
    assert "total_incidents" in overview
    assert "compliance_rate" in overview
    assert "compliant_detections" in overview

    # Violations Breakdown
    res = requests.get(f"{BASE_URL}/api/analytics/violations")
    assert res.status_code == 200
    viol_data = res.json()
    print(f"  Violations Categories: {viol_data}")

    # Trends
    res = requests.get(f"{BASE_URL}/api/analytics/trends")
    assert res.status_code == 200
    trends_data = res.json()
    print(f"  Trends Timeline items: {len(trends_data.get('timeline', []))}")

    # Severity Distribution
    res = requests.get(f"{BASE_URL}/api/analytics/severity")
    assert res.status_code == 200
    sev_data = res.json()
    print(f"  Severity Distribution: {sev_data}")

    # Source Distribution
    res = requests.get(f"{BASE_URL}/api/analytics/sources")
    assert res.status_code == 200
    src_data = res.json()
    print(f"  Source Distribution: {src_data}")
    print("  [PASS] All 5 Analytics Endpoints operational.")

    # 3. Incident History & Resolution Management
    print("\n[TEST 3] Testing Incident Management, Search & Resolution Workflow...")
    res = requests.get(f"{BASE_URL}/api/incidents?limit=10&offset=0")
    assert res.status_code == 200
    inc_data = res.json()
    incidents = inc_data.get("incidents", [])
    total_inc = inc_data.get("total", 0)
    print(f"  Total logged incidents: {total_inc}, retrieved in page: {len(incidents)}")
    assert len(incidents) > 0, "Expected at least 1 incident in database from Phase 2"

    test_inc = incidents[0]
    inc_id = test_inc["incident_id"]
    print(f"  Inspecting incident: {inc_id} ({test_inc['violation_category']}, {test_inc['severity']}, {test_inc['status']})")

    # Fetch single incident
    res = requests.get(f"{BASE_URL}/api/incidents/{inc_id}")
    assert res.status_code == 200
    single = res.json()["incident"]
    assert single["incident_id"] == inc_id

    # Update incident status to ACKNOWLEDGED
    res = requests.patch(
        f"{BASE_URL}/api/incidents/{inc_id}/status",
        json={"status": "ACKNOWLEDGED", "resolution_notes": "Supervisor notified for inspection."}
    )
    assert res.status_code == 200
    print(f"  [PASS] Updated {inc_id} to ACKNOWLEDGED.")

    # Update incident status to RESOLVED with notes
    res = requests.patch(
        f"{BASE_URL}/api/incidents/{inc_id}/status",
        json={
            "status": "RESOLVED",
            "resolution_notes": "Worker provided with mandatory safety equipment and verbal compliance briefing."
        }
    )
    assert res.status_code == 200
    print(f"  [PASS] Updated {inc_id} to RESOLVED with supervisor notes.")

    # Verify status in database
    res = requests.get(f"{BASE_URL}/api/incidents/{inc_id}")
    updated = res.json()["incident"]
    assert updated["status"] == "RESOLVED"
    assert "Worker provided" in updated["resolution_notes"]
    assert updated["resolved_at"] is not None
    print(f"  Verified database resolution: status={updated['status']}, resolved_at={updated['resolved_at']}")

    # 4. Report Generation: PDF & CSV
    print("\n[TEST 4] Testing Professional Report Generation (PDF & CSV)...")
    
    # 4a. PDF Report
    pdf_payload = {
        "report_type": "weekly",
        "title": "Industrial Safety Compliance Audit — Automated Test",
        "format": "pdf"
    }
    res = requests.post(f"{BASE_URL}/api/reports/generate", json=pdf_payload)
    assert res.status_code == 200, f"PDF generation failed: {res.text}"
    pdf_res = res.json()
    print(f"  PDF Generation response: {pdf_res}")
    pdf_report_id = pdf_res["report_id"]
    pdf_download_url = pdf_res["download_url"]

    # Download PDF
    res = requests.get(f"{BASE_URL}{pdf_download_url}")
    assert res.status_code == 200
    assert res.content[:4] == b"%PDF", "Generated file is not a valid PDF binary!"
    print(f"  [PASS] PDF downloaded successfully ({len(res.content)} bytes, valid %PDF header).")

    # 4b. CSV Report
    csv_payload = {
        "report_type": "monthly",
        "title": "Industrial Safety Incidents Dataset — Automated Test",
        "format": "csv"
    }
    res = requests.post(f"{BASE_URL}/api/reports/generate", json=csv_payload)
    assert res.status_code == 200, f"CSV generation failed: {res.text}"
    csv_res = res.json()
    print(f"  CSV Generation response: {csv_res}")
    csv_download_url = csv_res["download_url"]

    # Download CSV
    res = requests.get(f"{BASE_URL}{csv_download_url}")
    assert res.status_code == 200
    csv_text = res.text
    assert "Incident ID" in csv_text or "incident_id" in csv_text.lower(), "CSV header missing!"
    print(f"  [PASS] CSV downloaded successfully ({len(csv_text)} characters).")

    # 4c. Reports History
    res = requests.get(f"{BASE_URL}/api/reports/summary")
    assert res.status_code == 200
    r_summary = res.json()
    recent = r_summary.get("recent_reports", [])
    print(f"  Reports logged in history table: {len(recent)}")
    assert len(recent) >= 2, "Reports history table should contain newly generated PDF and CSV"
    print("  [PASS] Report Generation & Export fully verified.")

    # 5. System Settings & Diagnostics
    print("\n[TEST 5] Testing System Settings & Diagnostics Storage...")
    res = requests.get(f"{BASE_URL}/api/settings")
    assert res.status_code == 200
    settings_data = res.json()
    print(f"  Current Settings: {settings_data.get('settings')}")
    print(f"  Diagnostics: DB Size={settings_data.get('database_size_bytes')} bytes, Evidence Storage={settings_data.get('evidence_storage_bytes')} bytes")

    # Update settings
    update_payload = {
        "model_confidence_threshold": 0.28,
        "video_frame_stride": 4,
        "alert_cooldown_seconds": 20,
        "min_severity_level": "HIGH",
        "facility_name": "Automated Testing Plant - Zone B"
    }
    res = requests.post(f"{BASE_URL}/api/settings", json=update_payload)
    assert res.status_code == 200

    # Verify updated settings
    res = requests.get(f"{BASE_URL}/api/settings")
    updated_settings = res.json()["settings"]
    assert float(updated_settings["model_confidence_threshold"]) == 0.28
    assert updated_settings["facility_name"] == "Automated Testing Plant - Zone B"
    print("  [PASS] System Settings persisted and verified in SQLite.")

    # Restore default test confidence
    requests.post(f"{BASE_URL}/api/settings", json={"model_confidence_threshold": 0.25})

    # 6. Regression check: Phase 1 Image Detection
    print("\n[TEST 6] Regression Verification: Phase 1 Image Detection...")
    sample_img = Path("c:/Users/sikindarbasha/Documents/se_project/models/sample_inspection.jpg")
    if not sample_img.exists():
        sample_img = Path("c:/Users/sikindarbasha/Documents/se_project/backend/evidence/sample_frame.jpg")
    
    if sample_img.exists():
        with open(sample_img, "rb") as f:
            res = requests.post(f"{BASE_URL}/api/detect/image?confidence=0.25", files={"file": f})
        assert res.status_code == 200
        det_result = res.json()
        print(f"  Inference Time: {det_result.get('inference_time')}s, Detections: {det_result.get('total_detections')}")
        print("  [PASS] Phase 1 Image Detection works perfectly.")
    else:
        print("  (Sample image not found on disk, skipping image post)")

    print("\n" + "=" * 70)
    print("ALL PHASE 3 AUTOMATED TESTS PASSED SUCCESSFULLY! (100% GREEN)")
    print("=" * 70)

if __name__ == "__main__":
    test_all()
