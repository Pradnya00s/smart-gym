# -------- Base image (SLIM) --------
FROM python:3.11-slim

# Prevent Python from writing pyc files & buffering logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -------- System dependencies (minimal) --------
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# -------- Working directory --------
WORKDIR /app

# -------- Copy requirements first (for caching) --------
COPY backend/requirements.txt .

# -------- Install Python dependencies --------
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# -------- Copy application code --------
COPY backend .

# -------- Expose port --------
EXPOSE 8000

# -------- Run app --------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
