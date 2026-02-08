# Multi-stage Dockerfile for Local SOP Finder
# Stage 1: Builder - Download model and install dependencies
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Pre-download the sentence-transformers model during build
# This makes the container ready to run immediately
RUN python -c "from sentence_transformers import SentenceTransformer; \
    import os; \
    os.makedirs('./models', exist_ok=True); \
    model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='./models'); \
    print('Model downloaded successfully')"

# Build the search index if SOP file exists
RUN python << 'EOF'
import os
if os.path.exists('./data/structured_sops.txt'):
    from src.local_sop_identifier import LocalSOPIdentifier
    identifier = LocalSOPIdentifier(model_name='all-MiniLM-L6-v2', cache_dir='./models')
    identifier.build_index('./data/structured_sops.txt', './data/sop_index.pkl')
    print('Index built successfully')
else:
    print('SOP file not found, index will be built on first run')
EOF

# Stage 2: Runtime - Smaller final image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code and pre-built assets
COPY --from=builder /app /app

# Create necessary directories
RUN mkdir -p /app/models /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_CACHE_DIR=/app/models \
    DEFAULT_INDEX_PATH=/app/data/sop_index.pkl \
    DEFAULT_SOP_FILE=/app/data/structured_sops.txt

# Expose port (if adding API in future)
# EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command - interactive mode
CMD ["python", "main.py"]
