# ── Base image ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── System libs needed by OpenCV / PyTorch ──────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ───────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python deps (cached layer) ─────────────────────────────────────
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy project files ──────────────────────────────────────────────────────
COPY . .

# ── Runtime directories ─────────────────────────────────────────────────────
RUN mkdir -p backend/results \
              backend/evidence/images \
              backend/evidence/videos \
              backend/reports \
              backend/data

# ── Port ────────────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Start server ─────────────────────────────────────────────────────────────
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 75
