# Dockerfile

# Use a lean, official Python image
FROM python:3.10-slim

# Set environment variable for container logging
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy requirements file first for efficient caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the internal port for the application
EXPOSE 5000

# Command to run the SocketIO server application
CMD ["/usr/local/bin/python", "app.py"]