# Use the official lightweight Python 3.12 image
FROM python:3.12-slim

# Install system dependencies (useful for audio processing libraries if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install 'uv' for lightning-fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set the working directory inside the container
WORKDIR /app

# Copy the dependency management files first to leverage Docker cache
COPY pyproject.toml ./

# Install dependencies directly into the system environment 
# (In Docker, we don't strictly need a virtual environment)
RUN uv pip install --system .

# Copy the rest of the application code
COPY . .

# Expose any required ports (LiveKit uses WebSockets, but if you have a health check port, expose it here)
# EXPOSE 8080

# Run the LiveKit Agent Worker in production mode
CMD ["python", "main.py", "start"]