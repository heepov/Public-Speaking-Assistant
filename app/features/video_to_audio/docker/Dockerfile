# Lightweight image for video to audio conversion
FROM python:3.11-slim

# Metadata
LABEL maintainer="Media Processor Team"
LABEL description="Lightweight video to audio converter service"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY app/features/video_to_audio/docker/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/core/ ./app/core/
COPY app/features/video_to_audio/ ./app/features/video_to_audio/
COPY app/features/__init__.py ./app/features/
COPY app/__init__.py ./app/

# Create necessary directories
RUN mkdir -p uploads outputs logs

# Set Python path for correct module imports
ENV PYTHONPATH=/app
ENV PORT=8003
ENV HOST=0.0.0.0

# Expose port for microservice
EXPOSE 8003

# Start microservice
CMD ["python", "-m", "app.features.video_to_audio.microservice"]
