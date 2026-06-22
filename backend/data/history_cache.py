"""Pre-built history index for O(1) per-employee lookup.

Reads all 17 history sub-sheets ONCE at startup/build-time using pandas
(fast batch reads), groups by employee ID, renames columns for the MTP
template, and saves as pickle for instant subsequent loads.

Usage:
    >>> from backend.data.history_cache import get_history
    >>> history = get_history("G000002")
    >>> history["工作业绩"]  # [{绩效周期: "2023", 等级: "C", 绩效分数: "67.3"}, ...]
"""

import pickle
from pathlib import Path
from typing import Any

# ── Column name mapping: Excel field → Template display key ──
# Only the sheets with mismatches need entries.
_COLUMN_MAP: dict[str, dict[str, str]] = {
    "工作业绩": {
        "年度": "绩效周期",
        "绩效等级": "等级",
    },
    "干部年度考评": {
        "年度": "考评年度",
        "评价记录": "综合评价",
    },
    "奖惩信息": {
        "奖惩日期": "日期",
        "奖惩类型": "处罚类型",
        "奖惩原因": "处罚原因",
    },
    "项目经验": {
        "项目类别": "项目类型",
        "关联领域": "负责项目的领域",
        "项目名称": "担任项目名称",
    },
    "外派经历": {
        "开始日期": "日期",
    },
}

# Sheets to skip (not used in the MTP template)
_SKIP_SHEETS = {"导师经历"}

# Fields to strip from every history record (internal bookkeeping)
_STRIP_FIELDS = {"工号", "姓名", "记录序号"}

# ── In-memory index ──
_history_index: dict[str, dict[str, list[dict[str, str]]]] | None = None


def _remap_columns(short_name: str, records: list[dict]) -> list[dict]:
    mapping = _COLUMN_MAP.get(short_name, {})
    if not mapping:
        return records
    return [
        {mapping.get(k, k): v for k, v in rec.items()}
        for rec in records
    ]


def build(filepath: Path | None = None) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Read all history sub-sheets from Excel using pandas (fast batch reads).

    Returns: {employee_id: {sheet_short_name: [row_dict, ...]}}
    """
    import pandas as pd

    if filepath is None:
        from utils.config import TEST_DATA_FILE
        filepath = TEST_DATA_FILE

    if not filepath.exists():
        print(f"[HistoryCache] File not found: {filepath}")
        return {}

    index: dict[str, dict[str, list[dict[str, str]]]] = {}
    all_sheet_names = pd.ExcelFile(str(filepath)).sheet_names

    for sheet_name in all_sheet_names:
        if not sheet_name.startswith("历史_"):
            continue
        short = sheet_name.replace("历史_", "")
        if short in _SKIP_SHEETS:
            continue

        df = pd.read_excel(str(filepath), sheet_name=sheet_name, engine="openpyxl", header=0)
        if df.empty:
            continue

        # ── Extract employee ID from column 0 BEFORE dropping it ──
        id_col = df.columns[0]  # always "工号"
        eids = df[id_col].fillna("").astype(str).str.strip()

        # Drop internal bookkeeping columns
        drop_cols = [c for c in _STRIP_FIELDS if c in df.columns]
        df = df.drop(columns=drop_cols)

        # Convert all remaining values to string
        df = df.fillna("").astype(str)

        # Group by employee ID and convert to dict records
        for i in range(len(df)):
            eid = eids.iloc[i]
            if not eid or eid in ("", "nan", "None"):
                continue
            rec = df.iloc[i].to_dict()
            if eid not in index:
                index[eid] = {}
            if short not in index[eid]:
                index[eid][short] = []
            index[eid][short].append(rec)

        # Apply column remapping
        if short in _COLUMN_MAP:
            for eid in index:
                if short in index[eid]:
                    index[eid][short] = _remap_columns(short, index[eid][short])

        print(f"  [HistoryCache] {sheet_name}: {len(df)} records indexed")

    print(f"[HistoryCache] Built index for {len(index)} employees "
          f"({sum(len(v) for v in index.values())} total history modules)")
    return index


def _cache_path() -> Path:
    from utils.config import ROOT_DIR
    return ROOT_DIR / ".history_cache.pkl"


def load(rebuild: bool = False) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Load history index from pickle cache, or rebuild if missing/stale.

    This is called at server startup and blocks ~5-15 seconds on first
    run (reading Excel with pandas). Subsequent starts load the pickle
    file in ~0.5 seconds.
    """
    global _history_index

    cache_path = _cache_path()

    if not rebuild and _history_index is not None:
        return _history_index

    if not rebuild and cache_path.exists():
        try:
            _history_index = pickle.loads(cache_path.read_bytes())
            print(f"[HistoryCache] Loaded from pickle ({len(_history_index)} employees)")
            return _history_index
        except Exception as e:
            print(f"[HistoryCache] Pickle load failed: {e}, rebuilding...")

    _history_index = build()
    try:
        cache_path.write_bytes(pickle.dumps(_history_index))
        print(f"[HistoryCache] Pickle saved: {cache_path}")
    except Exception as e:
        print(f"[HistoryCache] Could not save pickle: {e}")

    return _history_index


def get_history(eid: str) -> dict[str, list[dict[str, str]]]:
    """Return all history data for one employee. O(1) dict lookup."""
    if _history_index is None:
        load()
    return (_history_index or {}).get(str(eid), {})


def ensure_loaded():
    """Pre-load the history index (call at server startup). No-op if already loaded."""
    if _history_index is None:
        load()
