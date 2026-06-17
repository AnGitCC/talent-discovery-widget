"""Global configuration for AI Talent Discovery system."""
from pathlib import Path
from pydantic import BaseModel

# Project root (talent-discover-widget/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Data
DATA_DIR = ROOT_DIR / "data"
TEST_DATA_FILE = ROOT_DIR / "test_talent_data_10000_cn.xlsx"

# Data source
DATA_PROVIDER = "excel"  # "excel" | "api"

# LLM
LLM_BACKEND = "mock"  # "mock" | "aihub"
AIHUB_BASE_URL = "https://aihub-api.goertek.com:30080/v1"
AIHUB_API_KEY = ""   # Fill when available
AIHUB_MODEL = "Qwen3-VL-235B-A22B-Instruct"

# Vector
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # lightweight local model
CHROMA_COLLECTION = "talent_profiles"

# Matching
RULE_FILTER_BATCH = 1000
VECTOR_TOP_K = 50
LLM_RANK_TOP_N = 10

# Export
EXPORT_DIR = ROOT_DIR / "exports"
