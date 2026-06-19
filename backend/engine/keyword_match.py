"""Keyword-based matching — the reliable baseline for talent search.

When semantic embeddings are unavailable (mock mode), keyword matching
provides meaningful scoring by checking term overlap between the user's
query and candidate profile fields.
"""
import re
import pandas as pd
from typing import Any


# Fields to search in, with their weight (higher = more important)
SEARCH_FIELDS = {
    "所在职位": 5.0,   # position title (1000 format)
    "岗位": 5.0,        # position title (400 format)
    "技能标签": 4.0,     # skills
    "所有标签": 3.0,     # tags
    "证书": 3.0,        # certifications
    "曾工作领域及年限": 2.5, # work domains (1000 format)
    "工作领域": 2.5,     # work domains (400 format)
    "最高学历专业": 2.0, # major (1000 format)
    "专业": 2.0,        # major (400 format)
    "最高学历": 1.0,    # education (1000 format)
    "学历": 1.0,        # education (400 format)
}


def _tokenize(text: str) -> list[str]:
    """Simple Chinese-friendly tokenizer that splits on common delimiters
    and also extracts meaningful substrings."""
    # Split on punctuation and whitespace
    tokens = re.split(r'[,;，；、\s]+', str(text).strip())
    # Also extract all 2-4 char Chinese substrings for partial matching
    result = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        result.append(token)
        # For Chinese text, add character bigrams
        if re.search(r'[一-鿿]', token):
            for i in range(len(token) - 1):
                result.append(token[i:i+2])
    return [t for t in result if len(t) >= 2]


def _score_row(row: pd.Series, query_tokens: list[str]) -> float:
    """Score a single employee row against query tokens."""
    score = 0.0
    matched_fields = []

    for field, weight in SEARCH_FIELDS.items():
        if field not in row.index:
            continue
        field_text = str(row[field])
        if not field_text or field_text == 'nan':
            continue

        field_tokens = set(_tokenize(field_text))

        # Count matching tokens
        hits = 0
        for qt in query_tokens:
            # Check exact token match
            if qt.lower() in {t.lower() for t in field_tokens}:
                hits += 1
            # Check substring match in original field text (for partial matches)
            elif qt.lower() in field_text.lower():
                hits += 0.5

        if hits > 0:
            score += weight * hits
            matched_fields.append(field)

    return score


def keyword_search(
    df: pd.DataFrame,
    query: str,
    top_n: int = 50,
) -> list[str]:
    """Score and rank candidates by keyword overlap with the query.

    Args:
        df: Pre-filtered DataFrame (rule filter already applied)
        query: Natural language query text
        top_n: Number of results to return

    Returns:
        List of employee IDs sorted by keyword relevance (descending)
    """
    if not query.strip():
        return _get_ids(df)[:top_n]

    query_tokens = _tokenize(query)
    if not query_tokens:
        return _get_ids(df)[:top_n]

    # Score every row
    scores = []
    for _, row in df.iterrows():
        s = _score_row(row, query_tokens)
        if s > 0:
            eid = _get_row_id(row)
            if eid:
                scores.append((eid, s))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    # Return top-N, then fill remaining up to top_n from unscored
    all_ids = _get_ids(df)
    results = [eid for eid, _ in scores[:top_n]]
    if len(results) < top_n:
        remaining = [eid for eid in all_ids if eid not in results]
        results.extend(remaining[:top_n - len(results)])

    return results[:top_n]


_ID_COLUMN_OPTIONS = ("员工编码", "工号", "id", "员工编号", "employee_id")


def _get_row_id(row) -> str:
    """Safely extract employee ID from a pandas Series row."""
    for key in _ID_COLUMN_OPTIONS:
        if key in row.index:
            val = row.get(key, "")
            if val:
                return str(val)
    # Fallback: use first column
    return str(row.iloc[0])


def _get_ids(df: pd.DataFrame) -> list[str]:
    """Safely get all employee IDs from a DataFrame."""
    for key in _ID_COLUMN_OPTIONS:
        if key in df.columns:
            return [str(x) for x in df[key].tolist()]
    # Fallback: use index
    return [str(i) for i in df.index.tolist()]


def keyword_score_for_candidates(
    df: pd.DataFrame,
    query: str,
    candidate_ids: list[str],
) -> dict[str, float]:
    """Compute keyword scores for a specific set of candidates."""
    id_set = set(candidate_ids)
    query_tokens = _tokenize(query)
    scores = {}
    for _, row in df.iterrows():
        eid = _get_row_id(row)
        if eid in id_set:
            scores[eid] = _score_row(row, query_tokens)
    return scores
