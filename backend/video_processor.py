import os
import time
import uuid
import threading
import subprocess
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

def _convert_to_browser_h264(raw_file: str, final_file: str):
    """
    Convert OpenCV's raw mp4v video to standard web-compatible H.264 (avc1) with yuv420p & faststart.
    Enables instant playback across Chrome, Edge, Firefox, Safari, and mobile browsers.
    """
    if not os.path.exists(raw_file) or os.path.getsize(raw_file) == 0:
        return

    ffmpeg_exe = None
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        import shutil
        ffmpeg_exe = shutil.which("ffmpeg")

    if ffmpeg_exe:
        cmd = [
            ffmpeg_exe, "-y",
            "-i", raw_file,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            final_file
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if res.returncode == 0 and os.path.exists(final_file) and os.path.getsize(final_file) > 0:
                try:
                    os.remove(raw_file)
                except Exception:
                    pass
                return
        except Exception as err:
            print(f"FFmpeg H.264 encoding error: {err}")

    # Fallback: rename raw to final if ffmpeg is somehow missing or failed
    if os.path.exists(raw_file) and not os.path.exists(final_file):
        try:
            os.replace(raw_file, final_file)
        except Exception:
            pass

MODEL_CLASSES = [
    "boots", "gloves", "goggles", "helmet", "vest",
    "no-boots", "no-gloves", "no-goggles", "no-helmet", "no-vest"
]

COMPLIANT_CLASSES = {"boots", "gloves", "goggles", "helmet", "vest"}
VIOLATION_CLASSES = {"no-boots", "no-gloves", "no-goggles", "no-helmet", "no-vest"}

def draw_fast_annotations_cv2(image_bgr: np.ndarray, detections: list) -> np.ndarray:
    """High-performance native OpenCV annotation rendering with ByteTrack ID labels."""
    if not detections:
        return image_bgr
    out_img = image_bgr.copy()
    for det in detections:
        bbox = det["bbox"]
        class_name = det["class_name"]
        conf = det["confidence"]
        track_id = det.get("track_id")
        color = det.get("color", (79, 70, 229))  # RGB
        # Convert RGB to BGR for OpenCV
        bgr_color = (int(color[2]), int(color[1]), int(color[0]))
        
        x1, y1, x2, y2 = bbox
        # Draw bounding box
        cv2.rectangle(out_img, (x1, y1), (x2, y2), bgr_color, 2)
        
        # Display ByteTrack unique ID when tracked
        if track_id is not None:
            label = f"#{track_id} {class_name} {int(conf * 100)}%"
        else:
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
    def __init__(self, job_id: str, input_path: str, filename: str, conf_threshold: float = 0.15, frame_stride: int = 4):
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

        # Total Frame Detections (Raw frame detections across all frames)
        self.total_detections = 0
        self.total_violations = 0
        self.class_counts: Dict[str, int] = {c: 0 for c in MODEL_CLASSES}

        # Unique Tracked Objects (ByteTrack tracking IDs)
        self.unique_class_tracks: Dict[str, set] = {c: set() for c in MODEL_CLASSES}
        self.all_unique_tracks: set = set()

        # Violation Grouping & Incident Cooldown Map
        self.active_violation_tracks: Dict[str, Dict[str, Any]] = {}
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
        # Calculate unique tracked counts per class
        unique_counts = {c: len(self.unique_class_tracks[c]) for c in MODEL_CLASSES}
        total_unique_compliant = sum(unique_counts[c] for c in COMPLIANT_CLASSES)
        total_unique_violations = sum(unique_counts[c] for c in VIOLATION_CLASSES)
        total_unique_objects = len(self.all_unique_tracks)

        # Accurate compliance rate based on unique tracked entities
        compliance = None
        if (total_unique_compliant + total_unique_violations) > 0:
            compliance = round((total_unique_compliant / (total_unique_compliant + total_unique_violations)) * 100.0, 1)
        elif self.total_detections > 0:
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

            # A. Total Frame Detections (across all processed frames)
            "total_detections": self.total_detections,
            "total_frame_detections": self.total_detections,
            "total_violations": self.total_violations,
            "total_frame_violations": self.total_violations,
            "class_counts": self.class_counts,
            "frame_class_counts": self.class_counts,

            # B. Unique Tracked Objects (ByteTrack tracking IDs)
            "tracking_enabled": True,
            "total_unique_objects": total_unique_objects,
            "unique_tracked_objects": total_unique_objects,
            "total_unique_violations": total_unique_violations,
            "unique_violations": total_unique_violations,
            "unique_class_counts": unique_counts,
            "unique_helmets": unique_counts.get("helmet", 0),
            "unique_vests": unique_counts.get("vest", 0),
            "unique_goggles": unique_counts.get("goggles", 0),
            "unique_gloves": unique_counts.get("gloves", 0),
            "unique_boots": unique_counts.get("boots", 0),

            "compliance_rate": compliance,
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

        # VideoWriter configuration (writes to temporary raw file, then converted to web H.264)
        raw_output_path = str(VIDEOS_DIR / f"raw_{self.job_id}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(raw_output_path, fourcc, orig_fps, (width, height))

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

                # Run inference on sampled frames with ByteTrack tracking
                if frame_idx % self.frame_stride == 1 or self.frame_stride == 1:
                    # Execute ByteTrack tracking with frame persistence
                    results = model.track(
                        source=frame,
                        persist=True,
                        tracker="bytetrack.yaml",
                        conf=self.conf_threshold,
                        iou=0.45,
                        imgsz=640,
                        device="cpu",
                        verbose=False
                    )
                    current_detections = []
                    
                    for r in results:
                        names = r.names
                        if r.boxes:
                            for box in r.boxes:
                                cls_id = int(box.cls[0].item())
                                cls_name = names.get(cls_id, f"class_{cls_id}")
                                conf = round(float(box.conf[0].item()), 2)
                                coords = [int(v) for v in box.xyxy[0].tolist()]
                                track_id = int(box.id[0].item()) if box.id is not None else None

                                current_detections.append({
                                    "class_id": cls_id,
                                    "class_name": cls_name,
                                    "confidence": conf,
                                    "track_id": track_id,
                                    "bbox": coords,
                                    "color": get_color_for_class(cls_name)
                                })

                                # 1. Track raw frame-level detection counts
                                if cls_name in self.class_counts:
                                    self.class_counts[cls_name] += 1
                                else:
                                    self.class_counts[cls_name] = 1

                                # 2. Track unique ByteTrack entity IDs
                                if track_id is not None:
                                    self.unique_class_tracks.setdefault(cls_name, set()).add(track_id)
                                    self.all_unique_tracks.add(track_id)
                    
                    last_detections = current_detections
                    self.total_detections += len(current_detections)

                    # 3. Check for violations and apply incident grouping logic
                    violations = [d for d in current_detections if d["class_name"] in VIOLATION_CLASSES]
                    if violations:
                        self.total_violations += len(violations)
                        
                        # Separate newly discovered violations from continuously tracked ones
                        new_violation_alerts = []
                        for v in violations:
                            v_name = v["class_name"]
                            v_tid = v.get("track_id")
                            # Grouping key: by violation class + track ID (or spatial cell if untracked)
                            if v_tid is not None:
                                vkey = f"{v_name}_track_{v_tid}"
                            else:
                                cx = (v["bbox"][0] + v["bbox"][2]) // 2
                                cy = (v["bbox"][1] + v["bbox"][3]) // 2
                                vkey = f"{v_name}_pos_{cx // 100}_{cy // 100}"
                            
                            existing = self.active_violation_tracks.get(vkey)
                            # Gap threshold: 60 frames (~2.5 sec video time)
                            if existing and (frame_idx - existing["last_seen_frame"]) <= 60:
                                # Continuously tracked violation: update tracking state, do not spam incidents
                                existing["last_seen_frame"] = frame_idx
                                existing["last_seen_time"] = timestamp_str
                                existing["occurrences"] += 1
                                existing["peak_conf"] = max(existing["peak_conf"], v["confidence"])
                            else:
                                # New violation instance (or reappeared after cooldown)
                                new_violation_alerts.append(v)
                                self.active_violation_tracks[vkey] = {
                                    "class_name": v_name,
                                    "track_id": v_tid,
                                    "first_seen_frame": frame_idx,
                                    "first_seen_time": timestamp_str,
                                    "last_seen_frame": frame_idx,
                                    "last_seen_time": timestamp_str,
                                    "occurrences": 1,
                                    "peak_conf": v["confidence"]
                                }

                        # Generate single grouped incident for new violation events
                        if new_violation_alerts:
                            track_tags = [f"Track #{v['track_id']}" for v in new_violation_alerts if v.get("track_id")]
                            source_desc = f"Video: {self.filename}"
                            if track_tags:
                                source_desc += f" ({', '.join(track_tags)})"

                            alert = check_and_generate_alerts(
                                frame_bgr=frame,
                                detections=current_detections,
                                source=source_desc,
                                video_timestamp=timestamp_str
                            )
                            if alert:
                                self.violations_summary.append({
                                    "incident_id": alert["incident_id"],
                                    "violation": alert["violation_category"],
                                    "confidence": alert["confidence"],
                                    "timestamp": timestamp_str,
                                    "severity": alert["severity"],
                                    "evidence_url": alert["evidence_path"],
                                    "tracks": track_tags or ["Tracked"]
                                })

                # Draw OpenCV annotations with ByteTrack unique IDs directly on frame
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
                
                unique_counts = {c: len(self.unique_class_tracks[c]) for c in MODEL_CLASSES}
                total_unique_compliant = sum(unique_counts[c] for c in COMPLIANT_CLASSES)
                total_unique_violations = sum(unique_counts[c] for c in VIOLATION_CLASSES)
                
                compliance_val = None
                if (total_unique_compliant + total_unique_violations) > 0:
                    compliance_val = round((total_unique_compliant / (total_unique_compliant + total_unique_violations)) * 100.0, 1)
                elif self.total_detections > 0:
                    compliance_val = round(max(0.0, min(100.0, ((self.total_detections - self.total_violations) / self.total_detections) * 100.0)), 1)
                
                duration = (self.total_frames / orig_fps) if orig_fps > 0 else self.elapsed_time
                
                # Record to persistent SQLite database
                record_video_job_completion(
                    job_id=self.job_id,
                    filename=self.filename,
                    duration_seconds=duration,
                    total_frames=self.total_frames,
                    frames_processed=self.current_frame,
                    total_detections=self.total_detections,
                    total_violations=total_unique_violations,
                    compliance_rate=compliance_val
                )

        except Exception as e:
            self.status = "failed"
            self.error_msg = str(e)
            print(f"Error during video processing job {self.job_id}: {e}")

        finally:
            cap.release()
            out.release()
            # Convert raw OpenCV video to browser-compliant H.264 video with faststart
            _convert_to_browser_h264(raw_output_path, self.output_path)
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
