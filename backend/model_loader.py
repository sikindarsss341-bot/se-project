import os
import torch
from pathlib import Path
from ultralytics import YOLO

# Global model state
_model = None
_model_info = {
    "status": "Loading",
    "model_name": "best.pt",
    "architecture": "YOLO DetectionModel",
    "task": "detect",
    "classes": {},
    "total_classes": 0,
    "device": "CPU (Optimized)",
    "device_type": "cpu",
    "error": None
}

def find_model_path() -> str:
    """Find the best.pt model file path."""
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    candidate_paths = [
        project_root / "models" / "best.pt",
        project_root / "best.pt",
        project_root / "best (2).pt",
        project_root / "best (1).pt",
        current_dir / "models" / "best.pt",
        current_dir / "best.pt",
    ]

    for p in candidate_paths:
        if p.exists() and p.is_file():
            return str(p)

    raise FileNotFoundError("best.pt model checkpoint could not be located.")

def load_ai_model():
    """Load the trained YOLO model once into memory."""
    global _model, _model_info
    try:
        model_path = find_model_path()
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
        device_display = "GPU (CUDA)" if device_name == "cuda" else "CPU (Optimized)"
        
        print(f"Loading YOLO model from: {model_path} on {device_display}...")
        model = YOLO(model_path)
        
        # Extract class names and info
        names = model.names if hasattr(model, "names") else {}
        total_classes = len(names)
        task = getattr(model, "task", "detect")
        arch = type(model.model).__name__ if hasattr(model, "model") and model.model is not None else "YOLO DetectionModel"

        _model = model
        _model_info.update({
            "status": "Ready",
            "model_name": Path(model_path).name,
            "model_path": model_path,
            "architecture": f"YOLO ({arch})",
            "task": task,
            "classes": names,
            "total_classes": total_classes,
            "device": device_display,
            "device_type": device_name,
            "error": None
        })
        print(f"Model loaded successfully! Detected {total_classes} classes: {names}")
        return _model
    except Exception as e:
        error_msg = f"Failed to load model: {str(e)}"
        print(f"ERROR: {error_msg}")
        _model = None
        _model_info.update({
            "status": "Error",
            "error": error_msg
        })
        return None

def get_model():
    """Get the loaded model instance."""
    global _model
    if _model is None and _model_info["status"] != "Error":
        return load_ai_model()
    return _model

def get_model_info() -> dict:
    """Return model information dictionary."""
    global _model_info
    return _model_info
