FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ .

# Default environment variables
ENV APP_NAME=sample-tdx-app \
    APP_PORT=8080 \
    TDX_PROXY_PORT=8081 \
    CAPTURE_BASELINE=true

EXPOSE 8080

CMD ["python", "main.py"]
