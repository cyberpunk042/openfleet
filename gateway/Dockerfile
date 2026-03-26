FROM python:3.11-slim

WORKDIR /app

# Install deps first (cached layer)
COPY pyproject.toml .
RUN pip install --no-cache-dir pyyaml httpx rich

# Copy application code
COPY gateway/ gateway/
COPY agents/ agents/
COPY config/ config/

EXPOSE 9400

CMD ["python", "-m", "gateway"]