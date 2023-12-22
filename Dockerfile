FROM python:3.11.7-slim-bookworm

# Set non-interactive environment variable to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install aiortc and related packages via pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install aiortc aiohttp opencv-python ultralytics torch mediapipe aiohttp_cors 

# Install dependencies for aiortc
# Note: The Python image is based on Debian, so we use apt-get instead of apk
RUN apt-get update && \
    apt-get install -y \
    libavdevice-dev \
    libavfilter-dev \
    libopus-dev \
    libvpx-dev \
    pkg-config \
    libopencv-dev \
    ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Expose port 8080
EXPOSE 8080

# Copy your source code to the container
COPY ./src /workspace

# Set the working directory
WORKDIR /workspace

# Command to run your application
CMD ["python3", "./server.py"]
