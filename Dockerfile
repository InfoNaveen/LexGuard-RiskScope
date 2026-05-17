FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 lexguard && \
    mkdir -p /app && \
    chown -R lexguard:lexguard /app

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=lexguard:lexguard . .

# Switch to non-root user
USER lexguard

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=2)"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
