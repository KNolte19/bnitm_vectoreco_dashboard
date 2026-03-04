FROM python:3.10-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x docker/entrypoint.sh

# Expose the Gunicorn port
EXPOSE 8000

ENTRYPOINT ["docker/entrypoint.sh"]
