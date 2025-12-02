# KeepItAllBot - YouTube Downloader Telegram Bot
# For Ubuntu/Debian on Contabo VPS
# Uses Pyrogram for 2GB uploads!

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install FFmpeg and build tools for TgCrypto
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home botuser

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY --chown=botuser:botuser . .

# Create directories
RUN mkdir -p /app/downloads /app/logs && chown -R botuser:botuser /app

USER botuser

CMD ["python", "main.py"]