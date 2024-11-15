# Start with the official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies, LibreOffice, and Poetry
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    libreoffice \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir poetry

# Set the working directory
WORKDIR /app

# Copy only requirements to cache them in docker layer
COPY pyproject.toml ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Generate poetry.lock file
RUN poetry lock

# Install project dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the FastAPI application code
COPY . /app

# Expose the port the app runs on
EXPOSE 5000

# Command to run the FastAPI app using Uvicorn
CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
