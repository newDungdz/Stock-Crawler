# Use Python 3.11-slim as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Update pip
RUN python -m pip install --upgrade pip

# Install dependencies
RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Copy main.py and requirements.txt from project root
COPY main.py .
COPY daily_runner.py .
COPY requirements.txt .


# Copy source code from src
COPY src/ ./src/

# Install Python packages
RUN pip install -r requirements.txt

# Run main script
CMD ["python3", "daily_runner.py"]