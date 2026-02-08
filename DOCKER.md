# Docker Deployment Guide

This guide covers deploying and running Local SOP Finder in Docker containers.

## Table of Contents
- [Quick Start](#quick-start)
- [Building the Image](#building-the-image)
- [Running the Container](#running-the-container)
- [Docker Compose](#docker-compose)
- [Environment Variables](#environment-variables)
- [Volume Mounts](#volume-mounts)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Quick Start

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/yourusername/sop_finder_clone.git
cd sop_finder_clone

# Run with docker-compose
docker-compose up
```

## Building the Image

### Basic Build

```bash
docker build -t sop-finder:latest .
```

### Build with Custom Tag

```bash
docker build -t sop-finder:v1.0 .
```

### Multi-platform Build

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t sop-finder:latest .
```

## Running the Container

### Interactive Mode (Default)

```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  sop-finder:latest
```

On Windows PowerShell:
```powershell
docker run -it --rm `
  -v ${PWD}/data:/app/data `
  sop-finder:latest
```

### Single Query Mode

```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  sop-finder:latest \
  python main.py --query "database connection timeout"
```

### Build Index Only

Useful for pre-building the index without entering interactive mode:

```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  sop-finder:latest \
  python main.py --build-index-only
```

### Skip Example Queries

```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  sop-finder:latest \
  python main.py --no-examples
```

## Docker Compose

### Default Configuration

The included `docker-compose.yml` provides a complete setup:

```yaml
version: '3.8'

services:
  sop-finder:
    build: .
    image: sop-finder:latest
    container_name: sop-finder
    stdin_open: true
    tty: true
    volumes:
      - ./data:/app/data
    environment:
      - MODEL_NAME=all-MiniLM-L6-v2
      - DEFAULT_TOP_K=5
```

### Running with Docker Compose

```bash
# Start in foreground
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Custom Docker Compose Override

Create a `docker-compose.override.yml` for local customization:

```yaml
version: '3.8'

services:
  sop-finder:
    environment:
      - DEFAULT_TOP_K=10
      - CONFIDENCE_THRESHOLD_HIGH=0.75
    volumes:
      - ./models:/app/models  # Cache models locally
```

## Environment Variables

All configuration options can be set via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence transformer model name |
| `MODEL_CACHE_DIR` | `/app/models` | Model cache directory in container |
| `DEFAULT_INDEX_PATH` | `/app/data/sop_index.pkl` | Index file path |
| `DEFAULT_SOP_FILE` | `/app/data/structured_sops.txt` | SOP data file |
| `DEFAULT_TOP_K` | `5` | Number of results to return |
| `DEFAULT_SEMANTIC_WEIGHT` | `0.6` | Semantic similarity weight (0-1) |
| `DEFAULT_BM25_WEIGHT` | `0.4` | Keyword matching weight (0-1) |
| `CONFIDENCE_THRESHOLD_HIGH` | `0.70` | High confidence threshold |
| `CONFIDENCE_THRESHOLD_MEDIUM` | `0.40` | Medium confidence threshold |

### Setting Environment Variables

**Command Line:**
```bash
docker run -it --rm \
  -e DEFAULT_TOP_K=10 \
  -e CONFIDENCE_THRESHOLD_HIGH=0.75 \
  -v $(pwd)/data:/app/data \
  sop-finder:latest
```

**Environment File:**

Create a `.env` file:
```bash
DEFAULT_TOP_K=10
CONFIDENCE_THRESHOLD_HIGH=0.75
DEFAULT_SEMANTIC_WEIGHT=0.7
DEFAULT_BM25_WEIGHT=0.3
```

Then use it:
```bash
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  sop-finder:latest
```

## Volume Mounts

### Data Directory (Required)

The `/app/data` directory contains SOP files and generated indexes:

```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  sop-finder:latest
```

**Contents:**
- `structured_sops.txt` - Source SOP data
- `sop_index.pkl` - Generated index (metadata)
- `sop_index.faiss` - FAISS vector index

### Models Directory (Optional)

Cache the downloaded model to speed up subsequent runs:

```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  sop-finder:latest
```

**Note:** The model (~80MB) is pre-downloaded during the Docker build, so this is only needed if you want to persist it across image rebuilds.

### Named Volumes

For production deployments, use Docker named volumes:

```bash
# Create volumes
docker volume create sop_data
docker volume create sop_models

# Run with named volumes
docker run -it --rm \
  -v sop_data:/app/data \
  -v sop_models:/app/models \
  sop-finder:latest
```

## Advanced Usage

### Running Tests in Docker

```bash
# Run all tests
docker run --rm sop-finder:latest pytest tests/ -v

# Run with coverage
docker run --rm sop-finder:latest pytest tests/ --cov=src --cov-report=term

# Run specific test file
docker run --rm sop-finder:latest pytest tests/test_identifier.py -v
```

### Custom SOP File

Mount your own SOP file:

```bash
docker run -it --rm \
  -v /path/to/your/sops.txt:/app/data/structured_sops.txt \
  -v $(pwd)/data:/app/data \
  sop-finder:latest
```

### Resource Limits

Limit CPU and memory usage:

```bash
docker run -it --rm \
  --cpus="2" \
  --memory="2g" \
  -v $(pwd)/data:/app/data \
  sop-finder:latest
```

### Running as Non-Root User

For enhanced security, run as a non-root user:

```dockerfile
# Add to Dockerfile
RUN useradd -m -u 1000 sopuser && \
    chown -R sopuser:sopuser /app
USER sopuser
```

Then rebuild:
```bash
docker build -t sop-finder:secure .
```

### Health Checks

The Docker image includes a health check. Check container health:

```bash
docker ps
# Look for "healthy" in the STATUS column

# Or inspect directly
docker inspect --format='{{.State.Health.Status}}' sop-finder
```

## Production Deployment

### Publishing to GitHub Container Registry

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag the image
docker tag sop-finder:latest ghcr.io/yourusername/sop-finder:latest

# Push to registry
docker push ghcr.io/yourusername/sop-finder:latest
```

### Pulling from Registry

```bash
docker pull ghcr.io/yourusername/sop-finder:latest
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  ghcr.io/yourusername/sop-finder:latest
```

### Kubernetes Deployment

Example Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sop-finder
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sop-finder
  template:
    metadata:
      labels:
        app: sop-finder
    spec:
      containers:
      - name: sop-finder
        image: ghcr.io/yourusername/sop-finder:latest
        env:
        - name: DEFAULT_TOP_K
          value: "10"
        volumeMounts:
        - name: sop-data
          mountPath: /app/data
      volumes:
      - name: sop-data
        persistentVolumeClaim:
          claimName: sop-data-pvc
```

## Troubleshooting

### Container Exits Immediately

**Problem:** Container starts but exits right away.

**Solution:** Ensure you're running in interactive mode with `-it` flags:
```bash
docker run -it --rm sop-finder:latest
```

### SOP File Not Found

**Problem:** Error message: "ERROR: SOP file not found"

**Solution:** Mount the data directory correctly:
```bash
docker run -it --rm -v $(pwd)/data:/app/data sop-finder:latest
```

### Index Build Fails

**Problem:** Index building fails during startup.

**Solution:** 
1. Check that `structured_sops.txt` exists in the data directory
2. Ensure the file is not corrupted
3. Try rebuilding manually:
```bash
docker run --rm -v $(pwd)/data:/app/data sop-finder:latest python main.py --build-index-only
```

### Model Download Fails

**Problem:** Model download errors during build.

**Solution:**
1. Check internet connectivity during build
2. The model is cached in the image, so this should only happen during `docker build`
3. If needed, pre-download the model:
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Permission Denied Errors

**Problem:** Cannot write to mounted volumes.

**Solution:** Fix permissions on host:
```bash
sudo chown -R $(id -u):$(id -g) data/
sudo chown -R $(id -u):$(id -g) models/
```

### Out of Memory Errors

**Problem:** Container crashes with OOM (Out of Memory).

**Solution:** Increase Docker memory limit:
```bash
docker run -it --rm --memory="2g" -v $(pwd)/data:/app/data sop-finder:latest
```

### Slow Performance

**Problem:** Queries take longer than expected.

**Possible causes:**
1. Index not pre-built (rebuilds on every start)
2. CPU limits too restrictive
3. Large SOP dataset

**Solutions:**
- Pre-build index: `docker run --rm -v $(pwd)/data:/app/data sop-finder:latest python main.py --build-index-only`
- Increase CPU limits: `--cpus="4"`
- Use volume mounts to persist index

## Best Practices

1. **Always mount volumes** - Don't bake data into images
2. **Use named volumes in production** - For better data management
3. **Set resource limits** - Prevent containers from consuming all host resources
4. **Pre-build indexes** - Faster startup times
5. **Use .dockerignore** - Smaller build contexts and faster builds
6. **Multi-stage builds** - Already implemented, keeps final image small
7. **Version your images** - Use tags like `v1.0` instead of just `latest`

## Additional Resources

- [Dockerfile reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Project README](README.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
