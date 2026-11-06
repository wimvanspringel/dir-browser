FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Line-buffer stdout/stderr so `docker logs` shows output immediately
ENV PYTHONUNBUFFERED=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY directory_server.py .
COPY directory_client.html .

# Create non-root user for security
# Use ARG to allow passing UID from docker-compose
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} appuser 2>/dev/null || true && \
    useradd -m -u ${USER_ID} -g ${GROUP_ID} appuser

RUN chown -R ${USER_ID}:${GROUP_ID} /app

USER appuser

# Expose port
EXPOSE 5000

# Health check (python:*.slim no longer ships curl, so use Python itself)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health', timeout=8)"]

# Run the application
CMD ["python", "directory_server.py"] 