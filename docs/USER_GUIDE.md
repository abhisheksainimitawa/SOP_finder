# Local SOP Finder - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Building the Index](#building-the-index)
3. [Querying for SOPs](#querying-for-sops)
4. [Understanding Results](#understanding-results)
5. [Advanced Usage](#advanced-usage)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- 500MB free disk space
- Internet connection (for initial model download only)

### Installation Steps

1. **Navigate to the project directory:**
   ```bash
   cd sop_finder_clone
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **First-time setup:**
   The first run will automatically download the sentence transformer model (~80MB). This is a one-time operation and the model is cached locally.

### Verify Installation

Run the test suite to verify everything is working:

```bash
pytest tests/ -v
```

You should see all tests passing.

---

## Building the Index

The index is a pre-computed database of SOP embeddings that enables fast searching.

### Automatic Index Building

The simplest approach - run the main script and it will build the index automatically from `data/structured_sops.txt`:

```bash
python main.py
```

On first run, you'll see:
```
Building new index...
Parsing SOPs...
Parsed 10 SOP chunks
Generating semantic embeddings...
Building FAISS index...
Saving index to ./data/sop_index.pkl...
Index built successfully with 10 SOPs
```

**Note**: Ensure your SOP file is located at `data/structured_sops.txt`

### Manual Index Building

For more control, you can build the index programmatically:

```python
from src.local_sop_identifier import LocalSOPIdentifier

# Initialize the identifier
identifier = LocalSOPIdentifier(
    model_name='all-MiniLM-L6-v2',
    cache_dir='./models'
)

# Build and save the index from data folder
identifier.build_index(
    sop_file_path='./data/structured_sops.txt',
    save_path='./data/sop_index.pkl'
)
```

### Index File Location

The index is saved as a pickle file:
- **Default location**: `./data/sop_index.pkl`
- **Size**: ~50MB for 100 SOPs
- **Contents**: SOP chunks, embeddings, BM25 data

### Rebuilding the Index

Rebuild the index when you:
- Add new SOPs
- Modify existing SOPs
- Change the model

To rebuild:
1. Delete the existing index: `rm data/sop_index.pkl` (Unix) or `del data\sop_index.pkl` (Windows)
2. Run the main script again: `python main.py`

---

## Querying for SOPs

### Interactive Mode (Recommended for Testing)

Run the main script and enter incident descriptions:

```bash
python main.py
```

After the examples run, you'll see:
```
INTERACTIVE MODE
Enter incident descriptions to find matching SOPs (or 'quit' to exit)

Incident description: 
```

Try queries like:
- "Database connection timeout"
- "API response times are very slow"
- "Users cannot authenticate"
- "High CPU usage on servers"

### Programmatic Usage

#### Basic Query

```python
from src.local_sop_identifier import LocalSOPIdentifier

# Initialize and load index
identifier = LocalSOPIdentifier()
identifier.load_index('./data/sop_index.pkl')

# Query for SOPs
results = identifier.retrieve_relevant_sops(
    query="Production database is down and unavailable",
    top_k=3  # Get top 3 results
)

# Print results
for sop in results:
    print(f"{sop['title']}: {sop['confidence_score']:.2f}")
```

#### Process Structured Incident Data

```python
incident = {
    'incident_details': {
        'short_description': 'Database service outage',
        'description': 'Production PostgreSQL database completely unavailable. All connections timing out.',
    },
    'log_insights': {
        'full_analysis': 'Connection refused errors on port 5432. Database process not running.'
    }
}

result = identifier.process_incident(incident)
print(f"Best SOP: {result['selected_sop_title']}")
print(f"Confidence: {result['confidence_score']:.2f}")
print(f"Action: {result['recommendation']}")
```

### Query Tips

**Good queries** are specific and descriptive:
- ✅ "Production database unavailable, connection timeouts on port 5432"
- ✅ "API response time increased from 200ms to 5000ms, high CPU usage"
- ✅ "OAuth authentication failing, users getting 401 errors"

**Poor queries** are too vague:
- ❌ "Issue"
- ❌ "Problem with system"
- ❌ "Not working"

**Best practice**: Include symptoms, error messages, and affected components.

---

## Understanding Results

### Result Structure

```python
{
    'selected_sop_id': 'sop_1',                    # Internal ID
    'selected_sop_number': 1,                      # SOP number
    'selected_sop_title': 'SOP-001: Database...',  # Full title
    'confidence_score': 0.8542,                    # Overall score (0-1)
    'confidence_level': 'HIGH',                    # HIGH/MEDIUM/LOW
    'semantic_score': 0.8234,                      # Semantic similarity
    'bm25_score': 0.7123,                          # Keyword match score
    'recommendation': 'ACCEPT',                    # ACCEPT/REVIEW/REJECT
    'reason': 'High confidence match...',          # Explanation
    'retrieved_sops': [...],                       # All top-k results
    'alternative_sops': [...]                      # Other options
}
```

### Confidence Levels Explained

#### HIGH Confidence (≥ 0.70)
- **Recommendation**: ACCEPT
- **Meaning**: Strong match between incident and SOP
- **Action**: Safe to use automatically
- **Example**: Score 0.85 for "database down" → Database Outage SOP

#### MEDIUM Confidence (0.40 - 0.69)
- **Recommendation**: REVIEW
- **Meaning**: Reasonable match, but verify
- **Action**: Human should review before applying
- **Example**: Score 0.55 for "slow queries" → Performance Degradation SOP

#### LOW Confidence (< 0.40)
- **Recommendation**: REJECT
- **Meaning**: Poor or uncertain match
- **Action**: Manual SOP selection required
- **Example**: Score 0.25 for vague "system issue"

### Score Components

#### Confidence Score
- **Range**: 0.0 to 1.0
- **Formula**: `0.6 × semantic_score + 0.4 × bm25_score`
- **Purpose**: Overall match quality

#### Semantic Score
- **Range**: 0.0 to 1.0
- **Measures**: Meaning similarity (contextual understanding)
- **Example**: Understands "DB crash" ≈ "database failure"

#### BM25 Score
- **Range**: 0.0 to 1.0 (normalized)
- **Measures**: Keyword/term matching
- **Example**: Rewards exact match of "PostgreSQL"

### Alternative SOPs

Even with a high-confidence match, check alternatives:

```python
if result['alternative_sops']:
    print("\nConsider also:")
    for alt in result['alternative_sops']:
        print(f"  - {alt['title']}: {alt['confidence_score']:.2f}")
```

**Why?** Complex incidents may benefit from multiple SOPs.

---

## Advanced Usage

### Custom Hybrid Weights

Adjust the balance between semantic and keyword matching:

```python
# More emphasis on semantic understanding
results = identifier.retrieve_relevant_sops(
    query="your query",
    semantic_weight=0.8,  # 80% semantic
    bm25_weight=0.2       # 20% keywords
)

# More emphasis on exact keyword matching
results = identifier.retrieve_relevant_sops(
    query="your query",
    semantic_weight=0.4,  # 40% semantic
    bm25_weight=0.6       # 60% keywords
)
```

**When to adjust:**
- **More semantic**: For descriptive incidents with varied terminology
- **More keyword**: For technical incidents with specific terms/IDs

### Custom Confidence Threshold

Set your own threshold for ACCEPT/REVIEW/REJECT:

```python
result = identifier.select_best_sop(
    incident_context="incident description",
    confidence_threshold=0.5  # Raise threshold (more conservative)
)

# Or lower it (more permissive)
result = identifier.select_best_sop(
    incident_context="incident description",
    confidence_threshold=0.3
)
```

### Batch Processing

Process multiple incidents:

```python
incidents = [
    {"incident_details": {"description": "Database down"}},
    {"incident_details": {"description": "API slow"}},
    {"incident_details": {"description": "Auth failing"}},
]

results = []
for incident in incidents:
    result = identifier.process_incident(incident)
    results.append(result)

# Analyze batch results
high_confidence = [r for r in results if r['confidence_level'] == 'HIGH']
print(f"High confidence matches: {len(high_confidence)}/{len(results)}")
```

### Export Results

Save results to JSON:

```python
import json

with open('results.json', 'w') as f:
    json.dump(result, f, indent=2)
```

---

## Troubleshooting

### Issue: Model Download Fails

**Symptoms**: 
```
Error downloading model...
```

**Solutions**:
1. Check internet connection
2. Try again (sometimes servers are busy)
3. Manually download model:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')
   ```

### Issue: Index File Not Found

**Symptoms**:
```
FileNotFoundError: Index file not found: ./data/sop_index.pkl
```

**Solutions**:
1. Build the index first: `python main.py`
2. Check file path is correct
3. Ensure you're running from the correct directory

### Issue: Low Confidence Scores for Everything

**Symptoms**: All queries return LOW confidence

**Possible Causes**:
1. **Vague queries**: Make queries more specific
2. **Wrong SOP file**: Ensure you're using the correct SOPs
3. **Index corruption**: Rebuild the index

**Solutions**:
```bash
# Rebuild index
rm data/sop_index.pkl
python main.py
```

### Issue: Memory Error During Index Building

**Symptoms**:
```
MemoryError: Unable to allocate array
```

**Solutions**:
1. Close other applications
2. Process SOPs in smaller batches
3. Use a machine with more RAM (minimum 512MB)

### Issue: Slow Query Performance

**Symptoms**: Queries take >5 seconds

**Possible Causes**:
1. First query (model loading): Normal, subsequent queries faster
2. Large SOP count (>1000): Consider FAISS
3. Old hardware: Upgrade CPU

**Solutions**:
- Pre-load index at startup
- Use smaller model (not recommended, accuracy loss)

---

## Best Practices

### Writing Good Queries

1. **Be Specific**: Include error messages, affected systems
   ```python
   # Good
   "PostgreSQL connection timeout on port 5432, all queries failing"
   
   # Bad
   "Database issue"
   ```

2. **Include Context**: Symptoms, impact, observed behavior
   ```python
   # Good
   "API response time increased from 200ms to 8s, 503 errors, CPU at 100%"
   
   # Bad
   "Slow API"
   ```

3. **Use Technical Terms**: Actual service names, error codes
   ```python
   # Good
   "OAuth token validation failing, 401 Unauthorized errors"
   
   # Bad
   "Login not working"
   ```

### Interpreting Results

1. **Always check confidence level** before trusting the result
2. **Review alternative SOPs** for complex incidents
3. **When in doubt, choose REVIEW** over automatic acceptance
4. **Low confidence?** Add more detail to your query

### Maintaining the Index

1. **Rebuild weekly** if SOPs change frequently
2. **Version your index** for rollback capability:
   ```bash
   cp data/sop_index.pkl data/sop_index_backup_$(date +%Y%m%d).pkl
   ```
3. **Test after rebuilding** with known queries

### Production Deployment

1. **Build index offline**, deploy with application
2. **Set conservative confidence thresholds** (e.g., 0.5)
3. **Log all queries and results** for monitoring
4. **Monitor confidence distribution**:
   ```python
   # Alert if too many LOW confidence results
   if result['confidence_level'] == 'LOW':
       logger.warning(f"Low confidence for: {incident}")
   ```

### Performance Optimization

1. **Pre-load index at startup** (don't load per-query)
2. **Cache the identifier instance**
3. **Use batch processing** for multiple queries
4. **Monitor memory usage** and restart if needed

---

## Common Use Cases

### Use Case 1: Automated Incident Triage

```python
def auto_triage(incident):
    result = identifier.process_incident(incident)
    
    if result['recommendation'] == 'ACCEPT':
        # Automatically assign SOP to engineer
        assign_sop_to_engineer(incident, result['selected_sop_id'])
    elif result['recommendation'] == 'REVIEW':
        # Flag for manual review
        flag_for_manual_review(incident, result)
    else:
        # Escalate to senior engineer
        escalate(incident)
```

### Use Case 2: SOP Recommendation UI

```python
def get_sop_recommendations(incident_description):
    incident = {
        'incident_details': {'description': incident_description}
    }
    
    result = identifier.process_incident(incident)
    
    return {
        'primary': {
            'sop': result['selected_sop_title'],
            'confidence': f"{result['confidence_score']:.0%}",
            'action': result['recommendation']
        },
        'alternatives': [
            {
                'sop': alt['title'],
                'confidence': f"{alt['confidence_score']:.0%}"
            }
            for alt in result['alternative_sops']
        ]
    }
```

### Use Case 3: Quality Assurance

```python
def qa_sop_assignment(incident, assigned_sop):
    """Check if the assigned SOP matches the recommendation"""
    result = identifier.process_incident(incident)
    
    if result['selected_sop_id'] != assigned_sop:
        print(f"Warning: Assigned {assigned_sop}, but recommend {result['selected_sop_id']}")
        print(f"Confidence in recommendation: {result['confidence_score']:.2f}")
        return False
    return True
```

---

## Getting Help

### Check Logs

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Run Tests

Validate your setup:

```bash
pytest tests/ -v
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError` | Index not built | Run `python main.py` |
| `MemoryError` | Insufficient RAM | Close apps, use smaller batches |
| `ValueError: Index not built` | Forgot to load index | Call `load_index()` first |
| `ModuleNotFoundError: sentence_transformers` | Dependencies not installed | Run `pip install -r requirements.txt` |

### Performance Expectations

| Operation | Expected Time | If Slower, Check |
|-----------|---------------|------------------|
| Model download | 30-60s | Internet connection |
| Index build (100 SOPs) | 20-30s | CPU, number of SOPs |
| Index load | <1s | Disk speed |
| Query | <200ms | RAM, CPU |

---

## Appendix: Quick Reference

### Common Commands

```bash
# Install
pip install -r requirements.txt

# Run with examples
python main.py

# Test
pytest tests/

# Rebuild index
rm data/sop_index.pkl && python main.py
```

### Code Snippets

#### Initialize and Query
```python
from src.local_sop_identifier import LocalSOPIdentifier

identifier = LocalSOPIdentifier()
identifier.load_index('./data/sop_index.pkl')

result = identifier.process_incident({
    'incident_details': {'description': 'Your incident here'}
})

print(f"SOP: {result['selected_sop_title']}")
print(f"Confidence: {result['confidence_score']:.2f}")
```

#### Build Custom Index
```python
identifier = LocalSOPIdentifier()
identifier.build_index(
    sop_file_path='your_sops.txt',
    save_path='custom_index.pkl'
)
```
