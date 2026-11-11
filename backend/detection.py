import os
import time
import uuid
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

from backend.model_loader import get_model, get_model_info

# Allowed image extensions and max size (10 MB)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Professional color palette for classes
CLASS_COLORS = {
    # PPE compliant (Green, Cyan, Blue, Gold, Purple)
    "helmet": (34, 197, 94),       # Vibrant Green
    "vest": (168, 85, 247),        # Purple
    "gloves": (234, 179, 8),       # Amber / Yellow
    "boots": (14, 165, 233),       # Sky Blue
    "goggles": (59, 130, 246),     # Blue
    
    # Violations / Non-compliant (Red / Coral / Orange)
    "no-helmet": (239, 68, 68),    # Crimson Red
    "no-vest": (244, 63, 94),      # Rose Red
    "no-gloves": (249, 115, 22),   # Orange Red
    "no-boots": (225, 29, 72),     # Dark Red
    "no-goggles": (217, 70, 239),  # Magenta
}
DEFAULT_COLOR = (99, 102, 241) # Indigo

def get_color_for_class(class_name: str):
    return CLASS_COLORS.get(class_name.lower(), DEFAULT_COLOR)

def validate_image_file(filename: str, file_size: int):
    """Validate file extension and size."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file extension '{ext}'. Only JPG, JPEG, and PNG are allowed."
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File size exceeds 10 MB limit ({file_size / (1024*1024):.2f} MB)."
    return True, ""

def draw_sleek_annotations(image_np: np.ndarray, detections: list) -> np.ndarray:
    """Draw clean, modern industrial annotations on image."""
    img_pil = Image.fromarray(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # Attempt to load a clean truetype font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", size=max(14, int(min(img_pil.size) * 0.025)))
    except Exception:
        font = ImageFont.load_default()

    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        class_name = det["class_name"]
        conf = det["confidence"]
        rgb_color = get_color_for_class(class_name)
        
        # Draw bounding box
        line_width = max(2, int(min(img_pil.size) * 0.003))
        draw.rectangle([x1, y1, x2, y2], outline=rgb_color, width=line_width)
        
        # Label text
        label_text = f"{class_name} {conf:.2f}"
        
        # Calculate text bounding box
        try:
            left, top, right, bottom = draw.textbbox((0, 0), label_text, font=font)
            text_w = right - left
            text_h = bottom - top
        except Exception:
            text_w = len(label_text) * 8
            text_h = 16

        padding = 4
        tag_x1 = x1
        tag_y1 = max(0, y1 - text_h - padding * 2)
        tag_x2 = tag_x1 + text_w + padding * 2
        tag_y2 = tag_y1 + text_h + padding * 2

        # Draw filled label tag background
        draw.rectangle([tag_x1, tag_y1, tag_x2, tag_y2], fill=rgb_color)
        
        # Draw text in white or dark depending on color
        draw.text((tag_x1 + padding, tag_y1 + padding), label_text, fill=(255, 255, 255), font=font)

    # Convert back to BGR OpenCV format
    annotated_np = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return annotated_np

def run_image_detection(image_bytes: bytes, filename: str, conf_threshold: float = 0.25) -> dict:
    """Run real YOLO inference on uploaded image bytes."""
    model = get_model()
    if model is None:
        return {
            "success": False,
            "error": "AI Model is not loaded or ready. Check /api/health.",
            "total_detections": 0,
            "detections": []
        }

    # Decode image with OpenCV
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        return {
            "success": False,
            "error": "Invalid or corrupted image file.",
            "total_detections": 0,
            "detections": []
        }

    start_time = time.time()
    
    # Run inference on CPU
    results = model.predict(source=img_bgr, conf=conf_threshold, device="cpu", verbose=False)
    inference_time = round(time.time() - start_time, 3)

    detections = []
    class_counter = {}

    for r in results:
        names = r.names
        for box in r.boxes:
            cls_id = int(box.cls[0].item())
            class_name = names.get(cls_id, f"class_{cls_id}")
            confidence = round(float(box.conf[0].item()), 2)
            coords = [int(v) for v in box.xyxy[0].tolist()]

            detections.append({
                "class_id": cls_id,
                "class_name": class_name,
                "confidence": confidence,
                "bbox": coords,
                "color": get_color_for_class(class_name)
            })

            class_counter[class_name] = class_counter.get(class_name, 0) + 1

    # Generate annotated image
    annotated_bgr = draw_sleek_annotations(img_bgr, detections)

    # Save to backend/results
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    unique_id = uuid.uuid4().hex[:10]
    out_filename = f"detection_{int(time.time())}_{unique_id}.jpg"
    out_path = results_dir / out_filename
    cv2.imwrite(str(out_path), annotated_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

    highest_conf = max([d["confidence"] for d in detections], default=0.0)

    return {
        "success": True,
        "total_detections": len(detections),
        "unique_classes_count": len(class_counter),
        "class_counts": class_counter,
        "highest_confidence": highest_conf,
        "inference_time": inference_time,
        "detections": detections,
        "annotated_image_url": f"/results/{out_filename}",
        "original_filename": filename
    }
