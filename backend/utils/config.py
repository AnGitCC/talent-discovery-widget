"""Global configuration for AI Talent Discovery system."""
from pathlib import Path
from pydantic import BaseModel

# Project root (talent-discover-widget/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Data
DATA_DIR = ROOT_DIR / "data"
TEST_DATA_FILE = ROOT_DIR / "test_talent_data_400_cn.xlsx"

# Data source
DATA_PROVIDER = "excel"  # "excel" | "api"

# LLM
LLM_BACKEND = "siliconflow"  # "mock" | "aihub" | "bailian" | "siliconflow"

# Alibaba Bailian (Dashscope) — fallback, set BAILIAN_API_KEY env var
BAILIAN_API_KEY = ""   # always read from env, never hardcode
BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
BAILIAN_CHAT_MODEL = "qwen3.7-plus"
BAILIAN_EMBED_MODEL = "tongyi-embedding-vision-plus-2026-03-06"

# SiliconFlow (primary) — set SILICONFLOW_API_KEY env var
SILICONFLOW_API_KEY = ""
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_CHAT_MODEL = "deepseek-ai/DeepSeek-V4-Pro"     # analysis: report/compare/llm_rank
SILICONFLOW_ROUTE_MODEL = "deepseek-ai/DeepSeek-V4-Flash"   # routing: intent detection

# AIHub (internal) — fallback
AIHUB_BASE_URL = "https://aihub-api.goertek.com:30080/v1"
AIHUB_API_KEY = ""
AIHUB_MODEL = "Qwen3-VL-235B-A22B-Instruct"

# Allow override via environment variables
import os
if _env_key := os.getenv("SILICONFLOW_API_KEY"):
    SILICONFLOW_API_KEY = _env_key
if _env_key := os.getenv("BAILIAN_API_KEY"):
    BAILIAN_API_KEY = _env_key

# Vector
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # lightweight local model
CHROMA_COLLECTION = "talent_profiles"

# Matching
RULE_FILTER_BATCH = 1000
VECTOR_TOP_K = 50
LLM_RANK_TOP_N = 10

# Export
EXPORT_DIR = ROOT_DIR / "exports"
