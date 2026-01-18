FROM python:3.12-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure stdout/stderr are unbuffered
ENV PYTHONUNBUFFERED=1

# Set project root inside container
WORKDIR /app

# Install system dependencies if required by Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure instance directory exists (will be overridden by volume)
RUN mkdir -p /app/instance

# Expose Flask/Gunicorn port
EXPOSE 5000

# Start application via Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
