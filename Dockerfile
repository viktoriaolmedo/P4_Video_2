# Use an official Python image as the base
FROM python:3.9-slim

# Install required dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy the manually downloaded Bento4 into the container
COPY Bento4 /opt/Bento4

# Build Bento4 inside the container
RUN cd /opt/Bento4 && \
    mkdir -p build && \
    cd build && \
    cmake .. && \
    make && \
    make install

# Remove the existing mp4encrypt link (if exists) and create a new one
RUN rm -f /usr/local/bin/mp4encrypt && ln -s /opt/Bento4/build/mp4encrypt /usr/local/bin/mp4encrypt

# Debug: Check if mp4encrypt is installed correctly
RUN ls -l /usr/local/bin/mp4encrypt

# Set working directory inside the container
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port your app runs on
EXPOSE 8000

# Start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]



