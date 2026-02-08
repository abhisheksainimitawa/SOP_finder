# Local SOP Finder - Architecture Documentation

## Disclaimer

**This is a simplified demonstration project** for portfolio and educational purposes. It showcases the core technical approach for intelligent SOP selection without exposing any proprietary Infosys company data, credentials, or production implementation details.

**Key Simplifications**:
- Uses LLM-generated sample SOPs (not real company procedures)
- Local open-source models instead of enterprise cloud APIs
- Simplified architecture for educational purposes
- Scaled for demonstration (10-100 SOPs) vs. production (1000s)

See [CHANGELOG.md](../CHANGELOG.md) for detailed comparison with the company implementation.

---

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Data Flow](#data-flow)
4. [Core Components](#core-components)
5. [Design Decisions](#design-decisions)
6. [Performance](#performance)
7. [Limitations](#limitations)

---

## Overview

The Local SOP Finder is a lightweight, offline-capable system for identifying the most relevant Standard Operating Procedure (SOP) for a given incident description. Unlike the original implementation that relies on external APIs (Azure OpenAI, Qdrant Cloud), this solution runs entirely locally using open-source models.

### Key Features
- **No External API Calls**: Fully offline, no internet required after initial setup
- **Lightweight**: ~500MB total footprint including models
- **Hybrid Retrieval**: Combines semantic similarity (60%) and keyword matching (40%)
- **Confidence Scoring**: HIGH (≥0.70), MEDIUM (0.40-0.69), LOW (<0.40)
- **Fast**: Sub-second query response times
- **Portable**: Runs on any machine with Python 3.8+

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION                          │
│  - Interactive CLI (main.py)                                     │
│  - Programmatic API (import LocalSOPIdentifier)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LOCAL SOP IDENTIFIER                           │
│                 (local_sop_identifier.py)                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              INCIDENT PROCESSING                        │    │
│  │  - Extract context from structured data                │    │
│  │  - Combine description, logs, symptoms                 │    │
│  └────────────────────┬───────────────────────────────────┘    │
│                       │                                          │
│                       ▼                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │               HYBRID RETRIEVAL                          │    │
│  │                                                          │    │
│  │  ┌──────────────────┐      ┌──────────────────┐       │    │
│  │  │ SEMANTIC SEARCH  │      │   BM25 SEARCH    │       │    │
│  │  │                  │      │                  │       │    │
│  │  │ Model:           │      │ Algorithm:       │       │    │
│  │  │ all-MiniLM-L6-v2 │      │ Okapi BM25       │       │    │
│  │  │                  │      │                  │       │    │
│  │  │ Embedding: 384D  │      │ Token-based      │       │    │
│  │  │ Similarity:      │      │ TF-IDF weighted  │       │    │
│  │  │ Cosine           │      │                  │       │    │
│  │  └────────┬─────────┘      └────────┬─────────┘       │    │
│  │           │                         │                  │    │
│  │           │   Normalize [0-1]       │   Normalize      │    │
│  │           │                         │   [0-1]          │    │
│  │           └──────────┬──────────────┘                  │    │
│  │                      │                                 │    │
│  │                      ▼                                 │    │
│  │           ┌─────────────────────┐                     │    │
│  │           │  HYBRID SCORING     │                     │    │
│  │           │  score = 0.6*sem +  │                     │    │
│  │           │          0.4*bm25   │                     │    │
│  │           └──────────┬──────────┘                     │    │
│  │                      │                                 │    │
│  │                      ▼                                 │    │
│  │           ┌─────────────────────┐                     │    │
│  │           │  RANK & SELECT      │                     │    │
│  │           │  Top-K SOPs         │                     │    │
│  │           └──────────┬──────────┘                     │    │
│  └─────────────────────┼────────────────────────────────┘    │
│                        │                                       │
│                        ▼                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │            CONFIDENCE ASSESSMENT                        │  │
│  │                                                          │  │
│  │  Score ≥ 0.70  →  HIGH      →  ACCEPT                  │  │
│  │  Score ≥ 0.40  →  MEDIUM    →  REVIEW                  │  │
│  │  Score < 0.40  →  LOW       →  REJECT                  │  │
│  │                                                          │  │
│  │  Reasoning: Why this SOP was selected                  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         RESULTS                                  │
│                                                                   │
│  - Selected SOP (ID, number, title)                             │
│  - Confidence score (0.0 - 1.0)                                 │
│  - Confidence level (HIGH/MEDIUM/LOW)                           │
│  - Recommendation (ACCEPT/REVIEW/REJECT)                        │
│  - Score breakdown (semantic, BM25, hybrid)                     │
│  - Reasoning (why this SOP)                                     │
│  - Alternative SOPs (ranked list)                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Index Building
```
┌──────────────┐
│ SOP File     │
│ (text)       │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌────────────────┐
│ Parse SOPs   │────▶│ SOP Chunks     │
│              │     │ (structured)   │
└──────────────┘     └────────┬───────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
          ┌─────────────────┐  ┌──────────────┐
          │ Generate        │  │ Tokenize     │
          │ Embeddings      │  │ for BM25     │
          │ (384D vectors)  │  │ (words)      │
          └────────┬────────┘  └──────┬───────┘
                   │                  │
                   ▼                  ▼
          ┌─────────────────┐  ┌──────────────┐
          │ Vector Matrix   │  │ BM25 Index   │
          │ (NumPy array)   │  │ (term freq)  │
          └────────┬────────┘  └──────┬───────┘
                   │                  │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Pickle & Save   │
                   │ (index.pkl)     │
                   └─────────────────┘
```

### Query Processing
```
┌──────────────┐
│ User Query   │
│ (incident)   │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Extract Context  │
│ - Description    │
│ - Logs           │
│ - Symptoms       │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────┐
│ Parallel Search                  │
│                                   │
│  ┌─────────────┐  ┌────────────┐│
│  │Generate     │  │Tokenize    ││
│  │Query        │  │Query       ││
│  │Embedding    │  │Terms       ││
│  └──────┬──────┘  └──────┬─────┘│
│         │                │      │
│         ▼                ▼      │
│  ┌─────────────┐  ┌────────────┐│
│  │Cosine Sim   │  │BM25 Score  ││
│  │with all     │  │all docs    ││
│  │embeddings   │  │            ││
│  └──────┬──────┘  └──────┬─────┘│
│         │                │      │
│         └────────┬───────┘      │
└──────────────────┼──────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │ Combine Scores   │
        │ Normalize        │
        │ Rank by hybrid   │
        └──────┬───────────┘
               │
               ▼
        ┌──────────────────┐
        │ Top-K Results    │
        └──────┬───────────┘
               │
               ▼
        ┌──────────────────┐
        │ Assess Confidence│
        │ Generate Reason  │
        └──────┬───────────┘
               │
               ▼
        ┌──────────────────┐
        │ Return Results   │
        └──────────────────┘
```

---

## Core Components

### 1. Sentence Transformer (all-MiniLM-L6-v2)
- **Model Size**: ~80MB
- **Embedding Dimension**: 384
- **Inference Time**: ~20ms per encoding
- **Purpose**: Captures semantic meaning and context

### 2. BM25 (Okapi BM25)
- **Type**: Algorithmic (no model required)
- **Speed**: ~5ms per query
- **Purpose**: Exact keyword matching

### 3. Hybrid Scoring
```
Final Score = 0.6 × Semantic Score + 0.4 × BM25 Score
```

### Key Data Structures

#### SOP Chunk
```python
{
    'id': 'sop_1',
    'title': 'SOP-001: Database Outage...',
    'content': 'Full SOP text...',
    'sop_number': 1
}
```

#### Result
```python
{
    'selected_sop_id': 'sop_1',
    'selected_sop_number': 1,
    'confidence_score': 0.8542,
    'confidence_level': 'HIGH',
    'recommendation': 'ACCEPT',
    'semantic_score': 0.8234,
    'bm25_score': 0.7123,
    'reason': 'High confidence match...',
    'alternative_sops': [...]
}
```

---

## Design Decisions

### Why Hybrid Retrieval?

| Approach | Strength | Weakness |
|----------|----------|----------|
| Semantic Only | Understands context | Misses exact keywords |
| BM25 Only | Exact term matching | No semantic understanding |
| **Hybrid** | **Best of both** | **Slightly complex** |

**Example**: 
- Semantic: "database down" ≈ "database outage" ✓
- BM25: "PostgreSQL" matches "PostgreSQL" exactly ✓

### Confidence Levels

| Level | Range | Recommendation | Action |
|-------|-------|----------------|--------|
| **HIGH** | ≥0.70 | ACCEPT | Proceed safely |
| **MEDIUM** | 0.40-0.69 | REVIEW | Verify first |
| **LOW** | <0.40 | REJECT | Manual review |

### Model Choice

| Option | Size | Speed | Quality | Decision |
|--------|------|-------|---------|----------|
| **all-MiniLM-L6-v2** | 80MB | Fast | Good | ✅ Chosen |
| TF-IDF | 0MB | Fastest | Poor | ❌ Too simple |
| Full BERT | 440MB | Slow | Best | ❌ Overkill |

---

## Performance

### Resource Usage

| Metric | Value |
|--------|-------|
| **Model Size** | 80MB |
| **Index Size (100 SOPs)** | 50MB |
| **RAM (Idle)** | 150MB |
| **RAM (Query)** | 250MB |

### Speed

| Operation | Time |
|-----------|------|
| **Index Build (100 SOPs)** | 20-30s |
| **Index Load** | 0.5s |
| **Query (end-to-end)** | ~100ms |

### Accuracy (20 test scenarios)

| Metric | Value |
|--------|-------|
| **Precision@1** | 85% |
| **Precision@3** | 95% |
| **MRR** | 0.88 |
| **HIGH Confidence Precision** | 95% |

---

## Limitations

### 1. Cold Start
First run downloads ~80MB model (30-60s delay, cached afterward)

### 2. Domain Vocabulary
Pre-trained model may not understand company-specific jargon  
**Mitigation**: BM25 handles exact keyword matching

### 3. Single SOP Assumption
System selects one best SOP, but some incidents need multiple  
**Mitigation**: Alternative SOPs provided in results

### 4. Static Index
Adding SOPs requires full rebuild (~30s for 100 SOPs)

### 5. No Learning
System doesn't improve from user feedback without manual retraining

### 6. Language
Optimized for English only (multilingual models available)

### 7. Context Window
Long SOPs (>512 tokens) may be truncated

---

## Future Improvements

### High Priority
1. **Fine-tuning**: Train on domain-specific incident-SOP pairs (+10-15% accuracy)
2. **Query Expansion**: Add synonyms (e.g., "DB" → "database, DBMS") (+5% recall)
3. **Explainability**: Highlight matching keywords/phrases

### Medium Priority
4. **Multi-SOP Detection**: Identify complex scenarios requiring multiple SOPs
5. **Incremental Updates**: Add SOPs without full rebuild

### Long-term
6. **Active Learning**: Collect feedback and retrain periodically
7. **Multi-modal**: Support images, logs, metrics in incidents
8. **Monitoring Integration**: Auto-detect incidents and recommend SOPs

---

## Conclusion

This local SOP finder offers:
- **Predictability**: No API limits, consistent performance
- **Cost**: Zero operational costs
- **Privacy**: All data stays local
- **Speed**: Sub-second responses
- **Portability**: Runs anywhere Python runs

Ideal for constrained environments, air-gapped systems, or scenarios requiring guaranteed availability.
