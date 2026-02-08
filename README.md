# Local SOP Finder

[![Tests](https://github.com/yourusername/sop_finder_clone/workflows/Tests/badge.svg)](https://github.com/yourusername/sop_finder_clone/actions)
[![Docker Build](https://github.com/yourusername/sop_finder_clone/workflows/Docker%20Build/badge.svg)](https://github.com/yourusername/sop_finder_clone/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A lightweight, offline-capable system for identifying the most relevant Standard Operating Procedure (SOP) for incident resolution.

## Project Context

**Purpose**: This is a simplified, open-source demonstration project.

**Background**: The original implementation was developed as part of an Infosys company project but cannot be shared publicly due to:
- Proprietary company data and SOPs
- Enterprise API credentials and infrastructure
- Company-specific integrations and workflows

**This Clone**: Demonstrates the same core technical concept using:
- LLM-generated sample SOPs (not real company procedures)
- Open-source local models (no enterprise APIs)
- Simplified architecture suitable for learning
- **Zero company data or proprietary information**

## Features

- **Fully Offline**: No internet required after initial setup
- **Fast**: Sub-second query response (~100ms)
- **Confidence Scoring**: HIGH/MEDIUM/LOW with actionable recommendations
- **Hybrid Retrieval**: Semantic (FAISS) + keyword matching (BM25)
- **Lightweight**: ~500MB total footprint
- **Private**: All data stays local

## Quick Start

### Docker (Recommended)

The easiest way to run Local SOP Finder is with Docker:

```bash
# Using docker-compose (interactive mode)
docker-compose up

# Or build and run manually
docker build -t sop-finder .
docker run -it -v $(pwd)/data:/app/data sop-finder

# Run a single query
docker run --rm -v $(pwd)/data:/app/data sop-finder python main.py --query "database connection timeout"

# Build index only
docker run --rm -v $(pwd)/data:/app/data sop-finder python main.py --build-index-only
```

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run setup (downloads models, builds index)
python setup.py

# Run the application
python main.py
```

### Usage

```bash
# Interactive mode (default)
python main.py

# Single query mode
python main.py --query "API response time is slow"

# Skip examples and go straight to interactive
python main.py --no-examples

# Build index only
python main.py --build-index-only

# Run tests
pytest tests/ -v
```

## Project Structure

```
sop_finder_clone/
├── src/
│   └── local_sop_identifier.py
├── tests/
│   ├── test_identifier.py
│   ├── test_confidence.py
│   └── test_performance.py
├── data/
│   └── structured_sops.txt
├── docs/
│   ├── ARCHITECTURE.md
│   └── USER_GUIDE.md
├── main.py
├── setup.py
├── config.py
├── requirements.txt
└── CHANGELOG.md
```

- **src/**
  - [local_sop_identifier.py](src/local_sop_identifier.py) - Core SOP identifier
- **tests/**
  - [test_identifier.py](tests/test_identifier.py) - Unit tests
  - [test_confidence.py](tests/test_confidence.py) - Confidence tests
  - [test_performance.py](tests/test_performance.py) - Performance tests
- **data/**
  - [structured_sops.txt](data/structured_sops.txt) - Sample SOPs
- **docs/**
  - [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical architecture
  - [USER_GUIDE.md](docs/USER_GUIDE.md) - User guide
- [main.py](main.py) - Interactive demo
- [setup.py](setup.py) - Setup verification
- [config.py](config.py) - Configuration
- [requirements.txt](requirements.txt) - Dependencies
- [CHANGELOG.md](CHANGELOG.md) - Version history

## Confidence Levels

| Level | Score Range | Recommendation |
|-------|-------------|----------------|
| **HIGH** | ≥ 0.70 | ACCEPT |
| **MEDIUM** | 0.40 - 0.69 | REVIEW |
| **LOW** | < 0.40 | REJECT |

## Configuration Options

Configuration can be set via environment variables (useful for Docker) or by editing [config.py](config.py):

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `MODEL_CACHE_DIR` | `./models` | Model cache directory |
| `DEFAULT_INDEX_PATH` | `./data/sop_index.pkl` | Index file path |
| `DEFAULT_SOP_FILE` | `./data/structured_sops.txt` | SOP data file path |
| `DEFAULT_TOP_K` | `5` | Number of results to return |
| `DEFAULT_SEMANTIC_WEIGHT` | `0.6` | Semantic similarity weight (0-1) |
| `DEFAULT_BM25_WEIGHT` | `0.4` | Keyword matching weight (0-1) |
| `CONFIDENCE_THRESHOLD_HIGH` | `0.70` | High confidence threshold |
| `CONFIDENCE_THRESHOLD_MEDIUM` | `0.40` | Medium confidence threshold |

### Docker Environment Variables

```bash
docker run -it \
  -e DEFAULT_TOP_K=10 \
  -e CONFIDENCE_THRESHOLD_HIGH=0.75 \
  -v $(pwd)/data:/app/data \
  sop-finder
```

## Performance

| Metric | Value |
|--------|-------|
| Query Time | ~100ms |
| Index Build (100 SOPs) | ~25s |
| Memory Usage | ~250MB |
| Precision@1 | 85% |

## Comparison: Production vs Demo

| Feature | Infosys Production | This Demo |
|---------|-------------------|-----------|
| **Data** | Real company SOPs | LLM-generated samples |
| **API** | Azure OpenAI, Qdrant Cloud | None (local models) |
| **Vector DB** | Qdrant Cloud | FAISS (local) |
| **Internet** | Required | No (after setup) |

## Docker Deployment

See [DOCKER.md](DOCKER.md) for detailed Docker deployment instructions, including:
- Volume mounting strategies
- Environment variable configuration
- Production deployment with Kubernetes
- Troubleshooting common issues

## GitHub Setup

### Publishing to GitHub

```bash
# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Docker-containerized SOP Finder"

# Create repository on GitHub, then:
git remote add origin https://github.com/yourusername/sop_finder_clone.git
git branch -M main
git push -u origin main
```

### Update Repository

After pushing, update your GitHub repository:

1. **Add topics**: `python`, `docker`, `machine-learning`, `faiss`, `sop`, `incident-management`
2. **Update badges**: Replace `yourusername` in README badges with your GitHub username
3. **Enable Actions**: GitHub Actions will automatically run tests and build Docker images
4. **Configure Container Registry**: Settings → Actions → Enable "Read and write permissions"

### Pull Published Docker Image

```bash
docker pull ghcr.io/yourusername/sop_finder_clone:latest
docker run -it ghcr.io/yourusername/sop_finder_clone:latest
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Documentation

- [DOCKER.md](DOCKER.md) - Complete Docker deployment guide
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Step-by-step deployment checklist
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical architecture and design
- [USER_GUIDE.md](docs/USER_GUIDE.md) - Complete usage guide
- [CHANGELOG.md](CHANGELOG.md) - Version history and comparisons

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Sentence Transformers](https://www.sbert.net/)
- Uses [FAISS](https://github.com/facebookresearch/faiss) for vector search
- Keyword matching powered by [BM25](https://github.com/dorianbrown/rank_bm25)

---

**For questions or suggestions, please open an issue on GitHub.**
