# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the full project
COPY . .

# Create required runtime directories
RUN mkdir -p backend/results backend/evidence/images backend/evidence/videos backend/reports backend/data

# Expose the port Railway will use
EXPOSE 8000

# Start FastAPI with uvicorn, binding to 0.0.0.0 and PORT env var
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
