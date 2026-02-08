# Configuration for Local SOP Finder
import os

# Model settings
MODEL_NAME = os.getenv('MODEL_NAME', 'all-MiniLM-L6-v2')  # Sentence transformer model
MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', './models')  # Where to cache the model

# Index settings
DEFAULT_INDEX_PATH = os.getenv('DEFAULT_INDEX_PATH', './data/sop_index.pkl')
DEFAULT_SOP_FILE = os.getenv('DEFAULT_SOP_FILE', './data/structured_sops.txt')

# Retrieval settings
DEFAULT_TOP_K = int(os.getenv('DEFAULT_TOP_K', '5'))
DEFAULT_SEMANTIC_WEIGHT = float(os.getenv('DEFAULT_SEMANTIC_WEIGHT', '0.6'))
DEFAULT_BM25_WEIGHT = float(os.getenv('DEFAULT_BM25_WEIGHT', '0.4'))

# Confidence thresholds
CONFIDENCE_THRESHOLD_HIGH = float(os.getenv('CONFIDENCE_THRESHOLD_HIGH', '0.70'))
CONFIDENCE_THRESHOLD_MEDIUM = float(os.getenv('CONFIDENCE_THRESHOLD_MEDIUM', '0.40'))

# Recommendations
RECOMMENDATION_ACCEPT = 'ACCEPT'
RECOMMENDATION_REVIEW = 'REVIEW'
RECOMMENDATION_REJECT = 'REJECT'
