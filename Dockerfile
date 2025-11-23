# Stage 1: Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file (which now includes flask-socketio)
COPY requirements.txt .

# Install dependencies (This is the step that will now install the missing package)
# This is a critical step for the "Build Image" stage in Jenkins.
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files (app.py, etc.) into the container
COPY . .

# Expose the port the Flask app runs on (informational)
EXPOSE 5000

# Set the command to run the application when the container starts
# CMD is the final instruction and ensures the Python app runs correctly.
CMD ["python", "-u", "app.py"]
