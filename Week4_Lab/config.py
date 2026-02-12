import os

# Data Directories
# Assuming we run from Week4_Lab/, the data is in ../Week3_Lab/project_data_mm
DATA_DIR = "../Week3_Lab/project_data_mm"
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
IMG_DIR = os.path.join(DATA_DIR, "figures")

# Logs
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "query_metrics.csv")

# Retrieval Defaults
DEFAULT_TOP_K_TEXT = 5
DEFAULT_TOP_K_IMAGES = 3
DEFAULT_TOP_K_EVIDENCE = 6
DEFAULT_ALPHA = 0.5  # 0.5 = equal weight. 1.0 = text only.

# Chunking Defaults
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
CHUNKING_MODE = "fixed"

# Models
# Using a lightweight model for default
DENSE_MODEL_NAME = 'all-MiniLM-L6-v2'
RERANK_MODEL_NAME = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
