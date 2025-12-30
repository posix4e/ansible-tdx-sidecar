# Multi-stage build for TDX Attestation Dashboard

# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Python application
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for DCAP (optional, for real verification)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libsgx-dcap-quote-verify \
#     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Copy built frontend
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Environment
ENV HOST=0.0.0.0 \
    PORT=8080 \
    DATABASE_URL=sqlite+aiosqlite:///./data/attestation.db

# Create data directory for SQLite
RUN mkdir -p /app/data

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
