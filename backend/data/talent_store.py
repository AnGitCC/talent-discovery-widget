"""In-memory talent data store with CRUD + vector similarity search.

Uses DataProvider abstraction — swap "excel" <-> "api" in config to change data source.
Pure Python (numpy) vector search — no external vector DB needed for MVP scale.
"""
import numpy as np
import pandas as pd
from data.provider import DataProvider, get_provider, build_text_profile, EmployeeRecord


class TalentStore:
    """Singleton store holding employee records + pre-computed embeddings.

    Pure numpy vector similarity — fast enough for 1000-10000 records.
    """

    def __init__(self):
        self.provider: DataProvider | None = None
        self.records: list[EmployeeRecord] = []
        self._id_to_index: dict[str, int] = {}
        # Vector index: numpy array of all embeddings
        self._embeddings: np.ndarray | None = None
        self._embedding_ids: list[str] = []  # employee IDs parallel to _embeddings

    def load(self, provider: DataProvider | None = None, embedding_fn=None):
        """Load records from the given provider (or default from config)."""
        self.provider = provider or get_provider()
        self.records = self.provider.fetch_all()
        self._id_to_index = {
            str(r.get("工号", "")): i for i, r in enumerate(self.records)
        }
        # Build vector index if embedding function provided
        if embedding_fn is not None:
            self._build_embeddings(embedding_fn)
        return self

    @property
    def df(self) -> pd.DataFrame:
        """Lazy DataFrame view of all records."""
        return pd.DataFrame(self.records)

    def _build_embeddings(self, embedding_fn):
        """Pre-compute embeddings for all records in memory."""
        texts = [build_text_profile(r) for r in self.records]
        vecs = embedding_fn(texts)
        self._embeddings = np.array(vecs, dtype=np.float32)
        self._embedding_ids = [str(r.get("工号", "")) for r in self.records]

    # ── CRUD ──

    def get_by_id(self, employee_id: str) -> EmployeeRecord | None:
        idx = self._id_to_index.get(employee_id)
        if idx is None:
            return None
        return self.records[idx]

    def get_by_ids(self, employee_ids: list[str]) -> pd.DataFrame:
        indices = [self._id_to_index[eid] for eid in employee_ids if eid in self._id_to_index]
        return pd.DataFrame([self.records[i] for i in indices])

    # ── Vector search (pure numpy, no external DB) ──

    def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 50,
        candidate_ids: list[str] | None = None,
    ) -> list[str]:
        """Cosine similarity search over all embeddings.

        Args:
            query_embedding: Query vector
            top_k: Number of results
            candidate_ids: Optional whitelist of employee IDs to search within
        """
        if self._embeddings is None or len(self._embeddings) == 0:
            return []

        query = np.array(query_embedding, dtype=np.float32)
        query = query / (np.linalg.norm(query) + 1e-8)

        # Normalize all embeddings
        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True) + 1e-8
        normalized = self._embeddings / norms

        # Cosine similarity
        scores = normalized @ query

        # Get top-k indices
        k = min(top_k, len(scores))
        top_indices = np.argpartition(-scores, k - 1)[:k]
        top_indices = top_indices[np.argsort(-scores[top_indices])]

        results = []
        for idx in top_indices:
            eid = self._embedding_ids[idx]
            if candidate_ids is None or eid in candidate_ids:
                results.append(eid)
            if len(results) >= top_k:
                break

        return results

    @property
    def has_vector_index(self) -> bool:
        return self._embeddings is not None and len(self._embeddings) > 0

    # ── Aggregate helpers (used by UI) ──

    @property
    def all_employee_ids(self) -> list[str]:
        return list(self._id_to_index.keys())

    @property
    def departments(self) -> list[str]:
        vals = {r.get("部门", "") for r in self.records if r.get("部门")}
        return sorted(vals)

    @property
    def positions(self) -> list[str]:
        vals = {r.get("岗位", "") for r in self.records if r.get("岗位")}
        return sorted(vals)

    @property
    def levels(self) -> list[str]:
        vals = {r.get("职级", "") for r in self.records if r.get("职级")}
        return sorted(vals)

    def get_all_tags(self) -> list[str]:
        all_tags = set()
        for r in self.records:
            tags_str = str(r.get("所有标签", ""))
            if tags_str:
                for t in tags_str.split(","):
                    t = t.strip()
                    if t:
                        all_tags.add(t)
        return sorted(all_tags)


# ── Global singleton ──

_store: TalentStore | None = None


def get_store() -> TalentStore:
    global _store
    if _store is None:
        _store = TalentStore()
    return _store
