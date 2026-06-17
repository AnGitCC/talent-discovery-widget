"""Search Agent — natural language → structured conditions → ranked results."""
from agents.base import Agent
from llm.prompts import SEARCH_SYSTEM
from engine.rule_filter import apply_hard_filters, build_condition_dataframe_queries
from engine.keyword_match import keyword_search, keyword_score_for_candidates
from data.talent_store import get_store


class SearchAgent(Agent):
    """Parses natural language into search conditions and executes search."""

    def __init__(self):
        super().__init__("SearchAgent", SEARCH_SYSTEM)
        self.store = get_store()

    def search(self, query: str, top_n: int = 20) -> dict:
        """Execute a search from natural language query.

        Search pipeline:
          1. LLM: parse NL → structured conditions
          2. Rule filter: apply conditions + hard filters
          3. Keyword match: score by term overlap (always works)
          4. Vector match: semantic similarity (if real embeddings available)
          5. Build candidate profiles
          6. LLM: re-rank top candidates
        """
        # Step 1: Parse NL → conditions via LLM
        parsed = self.ask_json(query)
        conditions = parsed.get("conditions", [])
        search_mode = parsed.get("search_mode", "semantic")
        reasoning = parsed.get("reasoning", "")

        # Step 2: Apply conditions + hard filters
        filtered_df = build_condition_dataframe_queries(self.store.df, conditions)
        filtered_df = apply_hard_filters(filtered_df)

        # Step 3: Keyword matching (primary — always works)
        ranked_ids = keyword_search(filtered_df, query, top_n=min(50, len(filtered_df)))

        # Step 4: Vector semantic search (enhancement when real embeddings available)
        vector_scores = {}
        from utils.config import LLM_BACKEND
        if LLM_BACKEND != "mock" and self.store.has_vector_index:
            try:
                query_embedding = self.llm.embed([query])[0]
                vec_results = self.store.search_similar(query_embedding, top_k=50)
                # Blend: boost keyword results that also appear in vector results
                for vec_eid in vec_results[:30]:
                    if vec_eid not in set(ranked_ids[:30]):
                        ranked_ids.insert(min(15, len(ranked_ids)), vec_eid)
            except Exception:
                pass

        # Step 5: Build candidate profiles with scores
        keyword_scores = keyword_score_for_candidates(filtered_df, query, ranked_ids[:top_n * 2])

        candidates = []
        for eid in ranked_ids[:top_n * 2]:
            profile = self.store.get_by_id(eid)
            if profile:
                # Normalize keyword score to 0-100
                raw_score = keyword_scores.get(eid, 0)
                max_possible = 20.0  # approximate max for display
                normalized = min(99, round(raw_score / max_possible * 100, 1)) if raw_score > 0 else 0
                candidates.append({
                    "id": eid,
                    "profile": profile,
                    "keyword_score": normalized,
                    "vector_score": vector_scores.get(eid, normalized),
                })

        # Step 6: LLM ranking
        if candidates and len(candidates) > 1:
            try:
                from engine.llm_rank import llm_rank
                candidates, _ = llm_rank(self.llm, query, candidates, top_n=min(top_n, len(candidates)))
            except Exception:
                pass

        # Fill in grade for any candidate without one
        from engine.llm_rank import compute_match_grade
        for c in candidates:
            if "grade" not in c or not c.get("grade"):
                score = c.get("keyword_score", 50)
                c["grade"] = compute_match_grade(score)

        return {
            "candidates": candidates[:top_n],
            "total_count": len(filtered_df),
            "conditions_used": conditions,
            "search_mode": search_mode,
            "reasoning": reasoning,
        }
