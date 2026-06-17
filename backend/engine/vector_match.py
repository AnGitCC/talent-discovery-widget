"""Second layer of matching engine: vector semantic matching (pure numpy)."""
import numpy as np
from typing import Callable
from data.talent_store import TalentStore
from data.provider import build_text_profile


def compute_similarity(query_embedding: list[float], doc_embeddings: list[list[float]]) -> list[float]:
    """Cosine similarity between query and doc embeddings."""
    query = np.array(query_embedding, dtype=np.float32)
    docs = np.array(doc_embeddings, dtype=np.float32)
    query = query / (np.linalg.norm(query) + 1e-8)
    docs = docs / (np.linalg.norm(docs, axis=1, keepdims=True) + 1e-8)
    return (docs @ query).tolist()


def semantic_search(
    store: TalentStore,
    query_text: str,
    embed_fn: Callable[[list[str]], list[list[float]]],
    candidate_ids: list[str] | None = None,
    top_k: int = 50,
) -> list[tuple[str, float]]:
    """Semantic search over talent profiles.

    Uses TalentStore's built-in numpy vector index for speed.
    Falls back to on-the-fly computation if no index built.
    """
    if not query_text.strip():
        return []

    query_vec = embed_fn([query_text])[0]

    # Use store's built-in numpy vector index if available
    if store.has_vector_index:
        result_ids = store.search_similar(query_vec, top_k=top_k, candidate_ids=candidate_ids)
        # Return with placeholder scores (actual cosine computed inside)
        return [(eid, 0.5) for eid in result_ids]

    # Fallback: compute on the fly
    if candidate_ids:
        df_subset = store.get_by_ids(candidate_ids)
    else:
        df_subset = store.df.head(top_k)

    texts = [build_text_profile(row) for _, row in df_subset.iterrows()]
    embeddings = embed_fn(texts)
    scores = compute_similarity(query_vec, embeddings)

    results = []
    for (_, row), score in zip(df_subset.iterrows(), scores):
        results.append((str(row.get("工号", "")), float(score)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
