# Use Python 3.9 slim as base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY . .

# Copy SSL certificates
# COPY certs /app/certs

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy pydantic python-dotenv

# Expose port 8000 for HTTPS
EXPOSE 8000

# Run the FastAPI app with SSL
CMD ["python", "main.py"]
