# ── Base image (Bookworm avoids Debian Trixie package renames) ─────────────
FROM python:3.11-slim-bookworm

# ── Runtime env tuning for low-memory cloud containers (Render/Railway/HF) ─
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    YOLO_CONFIG_DIR=/tmp/Ultralytics \
    ULTRALYTICS_AUTOINSTALL=false

# ── System libs needed by OpenCV / PyTorch ──────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ───────────────────────────────────────────────────────
WORKDIR /app

# ── Install CPU-only PyTorch first (~200MB vs ~3GB CUDA) + app deps ────────
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy project files ──────────────────────────────────────────────────────
COPY . .

# ── Runtime directories (writable even under non-root cloud sandboxes) ──────
RUN mkdir -p backend/results \
             backend/evidence/images \
             backend/evidence/videos \
             backend/reports \
             backend/data \
             /tmp/Ultralytics && \
    chmod -R 777 backend/results backend/evidence backend/reports backend/data /tmp/Ultralytics

# ── Port ────────────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Start server (shell expansion supports Render/Railway/HF PORT env var) ──
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 75"]
