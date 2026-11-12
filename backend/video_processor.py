import os
import time
import uuid
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import cv2
import numpy as np

from backend.model_loader import get_model
from backend.detection import get_color_for_class
from backend.alert_manager import check_and_generate_alerts, VIOLATION_CLASSES
from backend.database import record_video_job_completion

VIDEOS_DIR = Path(__file__).resolve().parent / "evidence" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_CLASSES = [
    "boots", "gloves", "goggles", "helmet", "vest",
    "no-boots", "no-gloves", "no-goggles", "no-helmet", "no-vest"
]

def draw_fast_annotations_cv2(image_bgr: np.ndarray, detections: list) -> np.ndarray:
    """High-performance native OpenCV annotation rendering without PIL overhead."""
    if not detections:
        return image_bgr
    out_img = image_bgr.copy()
    for det in detections:
        bbox = det["bbox"]
        class_name = det["class_name"]
        conf = det["confidence"]
        color = det.get("color", (79, 70, 229))  # RGB
        # Convert RGB to BGR for OpenCV
        bgr_color = (int(color[2]), int(color[1]), int(color[0]))
        
        x1, y1, x2, y2 = bbox
        # Draw bounding box
        cv2.rectangle(out_img, (x1, y1), (x2, y2), bgr_color, 2)
        
        # Draw clean label banner
        label = f"{class_name} {int(conf * 100)}%"
        (w, h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        bg_y1 = max(0, y1 - h - 6)
        cv2.rectangle(out_img, (x1, bg_y1), (x1 + w + 8, bg_y1 + h + 6), bgr_color, -1)
        cv2.putText(out_img, label, (x1 + 4, bg_y1 + h + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    return out_img


# Active video processing jobs repository: job_id -> dict
video_jobs: Dict[str, Any] = {}
_jobs_lock = threading.Lock()

class VideoJob:
    def __init__(self, job_id: str, input_path: str, filename: str, conf_threshold: float = 0.25, frame_stride: int = 4):
        self.job_id = job_id
        self.input_path = input_path
        self.filename = filename
        self.conf_threshold = conf_threshold
        self.frame_stride = frame_stride
        
        self.status = "queued"  # queued, processing, paused, completed, stopped, failed
        self.progress = 0.0
        self.current_frame = 0
        self.total_frames = 0
        self.processing_fps = 0.0
        self.elapsed_time = 0.0
        self.total_detections = 0
        self.total_violations = 0
        self.class_counts: Dict[str, int] = {c: 0 for c in MODEL_CLASSES}
        self.violations_summary = []
        
        self.output_path = str(VIDEOS_DIR / f"annotated_{job_id}.mp4")
        self.output_url = f"/evidence/videos/annotated_{job_id}.mp4"
        self.original_url = f"/evidence/videos/{Path(input_path).name}"
        self.error_msg = None
        
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Unpaused by default
        self.thread: Optional[threading.Thread] = None

    def to_dict(self) -> Dict[str, Any]:
        compliance = None
        if self.total_detections > 0:
            compliance = round(max(0.0, min(100.0, ((self.total_detections - self.total_violations) / self.total_detections) * 100.0)), 1)

        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "status": self.status,
            "progress": round(self.progress, 1),
            "current_frame": self.current_frame,
            "total_frames": self.total_frames,
            "processing_fps": round(self.processing_fps, 1),
            "elapsed_time": round(self.elapsed_time, 2),
            "total_detections": self.total_detections,
            "total_violations": self.total_violations,
            "compliance_rate": compliance,
            "class_counts": self.class_counts,
            "violations_summary": self.violations_summary,
            "annotated_video_url": self.output_url if self.status == "completed" else None,
            "original_video_url": self.original_url,
            "error": self.error_msg
        }

    def start(self):
        self.thread = threading.Thread(target=self._run_processing, daemon=True)
        self.thread.start()

    def pause(self):
        if self.status == "processing":
            self.status = "paused"
            self._pause_event.clear()

    def resume(self):
        if self.status == "paused":
            self.status = "processing"
            self._pause_event.set()

    def stop(self):
        self.status = "stopped"
        self._stop_event.set()
        self._pause_event.set()  # Unblock if paused

    def _run_processing(self):
        model = get_model()
        if model is None:
            self.status = "failed"
            self.error_msg = "Model failed to load."
            return

        cap = cv2.VideoCapture(self.input_path)
        if not cap.isOpened():
            self.status = "failed"
            self.error_msg = "Failed to open video file."
            return

        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Downscale oversized frames for CPU efficiency
        max_dim = 960
        scale = 1.0
        if max(width, height) > max_dim:
            scale = max_dim / max(width, height)
            width = int(width * scale)
            height = int(height * scale)

        # VideoWriter configuration (mp4v codec)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, orig_fps, (width, height))

        self.status = "processing"
        start_time = time.time()
        last_detections = []
        frame_idx = 0

        try:
            while cap.isOpened() and not self._stop_event.is_set():
                # Check for pause
                self._pause_event.wait()
                if self._stop_event.is_set():
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                if scale != 1.0:
                    frame = cv2.resize(frame, (width, height))

                frame_idx += 1
                self.current_frame = frame_idx
                self.progress = min(100.0, (frame_idx / self.total_frames) * 100)

                # Format video timestamp (MM:SS)
                seconds = int(frame_idx / orig_fps)
                timestamp_str = f"{seconds // 60:02d}:{seconds % 60:02d}"

                # Run inference on sampled frames (frame stride optimization)
                if frame_idx % self.frame_stride == 1 or self.frame_stride == 1:
                    # Run inference with optimised settings:
                    # iou=0.45  : standard NMS, avoids merging adjacent PPE items
                    # max_det=100: allow many workers per frame
                    # imgsz=640  : model's native input resolution
                    results = model.predict(
                        source=frame,
                        conf=self.conf_threshold,
                        iou=0.45,
                        imgsz=640,
                        device="cpu",
                        verbose=False,
                        agnostic_nms=False,
                        max_det=100
                    )
                    current_detections = []
                    
                    for r in results:
                        names = r.names
                        for box in r.boxes:
                            cls_id = int(box.cls[0].item())
                            cls_name = names.get(cls_id, f"class_{cls_id}")
                            conf = round(float(box.conf[0].item()), 2)
                            coords = [int(v) for v in box.xyxy[0].tolist()]

                            current_detections.append({
                                "class_id": cls_id,
                                "class_name": cls_name,
                                "confidence": conf,
                                "bbox": coords,
                                "color": get_color_for_class(cls_name)
                            })
                            # Track detected class occurrence
                            if cls_name in self.class_counts:
                                self.class_counts[cls_name] += 1
                            else:
                                self.class_counts[cls_name] = 1
                    
                    last_detections = current_detections
                    self.total_detections += len(current_detections)

                    # Check for violations and trigger incident alerts
                    violations = [d for d in current_detections if d["class_name"] in VIOLATION_CLASSES]
                    if violations:
                        self.total_violations += len(violations)
                        alert = check_and_generate_alerts(
                            frame_bgr=frame,
                            detections=current_detections,
                            source=f"Video: {self.filename}",
                            video_timestamp=timestamp_str
                        )
                        if alert:
                            self.violations_summary.append({
                                "incident_id": alert["incident_id"],
                                "violation": alert["violation_category"],
                                "confidence": alert["confidence"],
                                "timestamp": timestamp_str,
                                "severity": alert["severity"],
                                "evidence_url": alert["evidence_path"]
                            })

                # Draw fast OpenCV annotations directly on frame (smooth output)
                annotated_frame = draw_fast_annotations_cv2(frame, last_detections)
                out.write(annotated_frame)

                # Update processing FPS metric
                self.elapsed_time = time.time() - start_time
                if self.elapsed_time > 0:
                    self.processing_fps = frame_idx / self.elapsed_time

            if self._stop_event.is_set():
                self.status = "stopped"
            else:
                self.status = "completed"
                self.progress = 100.0
                compliance_val = None
                if self.total_detections > 0:
                    compliance_val = max(0.0, min(100.0, ((self.total_detections - self.total_violations) / self.total_detections) * 100.0))
                
                duration = (self.total_frames / orig_fps) if orig_fps > 0 else self.elapsed_time
                # Record to persistent SQLite database
                record_video_job_completion(
                    job_id=self.job_id,
                    filename=self.filename,
                    duration_seconds=duration,
                    total_frames=self.total_frames,
                    frames_processed=self.current_frame,
                    total_detections=self.total_detections,
                    total_violations=self.total_violations,
                    compliance_rate=compliance_val
                )

        except Exception as e:
            self.status = "failed"
            self.error_msg = str(e)
            print(f"Error during video processing job {self.job_id}: {e}")

        finally:
            cap.release()
            out.release()
            self.elapsed_time = time.time() - start_time


def create_video_job(filepath: str, filename: str, conf_threshold: float = 0.25, frame_stride: int = 4) -> VideoJob:
    """Instantiate, register, and initiate an asynchronous video processing job."""
    job_id = f"vjob_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    job = VideoJob(
        job_id=job_id,
        input_path=filepath,
        filename=filename,
        conf_threshold=conf_threshold,
        frame_stride=frame_stride
    )
    with _jobs_lock:
        video_jobs[job_id] = job
    
    job.start()
    return job

def get_job(job_id: str) -> Optional[VideoJob]:
    """Retrieve job instance by id."""
    with _jobs_lock:
        return video_jobs.get(job_id)
