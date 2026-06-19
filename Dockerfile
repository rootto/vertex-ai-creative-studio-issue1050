# Use an official Python runtime as a parent image
FROM python:3.14-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by OpenCV and other libraries
# libgl1-mesa-glx provides libGL.so.1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . .

# Install any needed packages specified in pyproject.toml (via uv)
RUN pip install uv
RUN uv sync

# Make port 8080 available to the world outside this container
EXPOSE 8080

CMD ["/app/.venv/bin/gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "--forwarded-allow-ips", "*", "--access-logfile", "-", "-k", "uvicorn.workers.UvicornWorker", "main:app"]
