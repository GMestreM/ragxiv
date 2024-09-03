# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including gcc
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libatlas-base-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, and wheel
RUN pip install --upgrade pip setuptools wheel

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run database initialization scripts
RUN python init_db.py && \
    python update_database.py
