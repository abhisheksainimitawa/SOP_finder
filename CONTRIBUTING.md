# Contributing to Local SOP Finder

Thank you for your interest in contributing to Local SOP Finder! This document provides guidelines for contributing to the project.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, Docker version if applicable)
- **Relevant logs or error messages**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear and descriptive title**
- **Detailed description** of the proposed functionality
- **Use cases** explaining why this would be useful
- **Possible implementation approach** (if you have ideas)

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the coding standards below
3. **Add tests** if you've added code that should be tested
4. **Update documentation** if you've changed APIs or functionality
5. **Ensure tests pass** by running `pytest tests/ -v`
6. **Submit the pull request** with a clear description of changes

## Development Setup

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/sop_finder_clone.git
cd sop_finder_clone

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py

# Run tests
pytest tests/ -v
```

### Docker Development

```bash
# Build the Docker image
docker build -t sop-finder:dev .

# Run with docker-compose
docker-compose up

# Run tests in Docker
docker run --rm sop-finder:dev pytest tests/ -v
```

## Coding Standards

### Python Style

- Follow **PEP 8** style guidelines
- Use **type hints** where appropriate
- Write **docstrings** for all functions and classes (Google style)
- Keep functions focused and under 50 lines when possible
- Use meaningful variable and function names

### Testing

- Write unit tests for new functionality
- Maintain or improve code coverage
- Test edge cases and error conditions
- Use pytest fixtures for common setup

### Documentation

- Update README.md if you change functionality
- Add docstrings to new functions and classes
- Update ARCHITECTURE.md for architectural changes
- Include examples for new features

### Commit Messages

- Use clear and descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Keep the first line under 72 characters
- Provide additional context in the body if needed

Example:
```
Add support for custom confidence thresholds

- Allow users to override default thresholds via environment variables
- Update documentation with new configuration options
- Add tests for threshold validation
```

## Project Structure

```
sop_finder_clone/
├── src/                    # Core application code
│   └── local_sop_identifier.py
├── tests/                  # Test suite
│   ├── test_identifier.py
│   ├── test_confidence.py
│   └── test_performance.py
├── data/                   # Data files
│   └── structured_sops.txt
├── docs/                   # Documentation
├── .github/                # GitHub workflows
├── main.py                 # Entry point
├── config.py               # Configuration
└── requirements.txt        # Dependencies
```

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_identifier.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run performance tests
pytest tests/test_performance.py -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names that explain what is being tested
- Follow the Arrange-Act-Assert pattern

## Docker Guidelines

### Building Images

- Keep Dockerfile changes minimal and well-documented
- Use multi-stage builds to minimize image size
- Cache dependencies appropriately
- Test images locally before submitting PR

### Docker Compose

- Update docker-compose.yml for new services or configurations
- Document environment variables in comments
- Provide sensible defaults

## Documentation

- Keep documentation up-to-date with code changes
- Use clear, concise language
- Include code examples where helpful
- Update README.md badges and links as needed

## Questions?

Feel free to open an issue with the `question` label if you have any questions about contributing.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
