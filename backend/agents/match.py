"""Match Agent — shared matching engine for both entry points."""
import pandas as pd
from agents.base import Agent
from llm.prompts import MATCH_SYSTEM
from engine.rule_filter import apply_hard_filters, parse_search_conditions
from engine.llm_rank import llm_rank, compute_final_score, compute_match_grade
from engine.keyword_match import keyword_search, keyword_score_for_candidates, _get_ids as _safe_df_ids
from data.talent_store import get_store
from data.provider import build_text_profile


class MatchAgent(Agent):
    """Core matching agent: orchestrates the 3-layer matching pipeline."""

    def __init__(self):
        super().__init__("MatchAgent", MATCH_SYSTEM)
        self.store = get_store()

    def match_position_to_person(
        self,
        position_name: str,
        conditions: list[dict] | None = None,
        top_n: int = 20,
    ) -> dict:
        """岗找人: given a position/query, find matching candidates."""
        df = self.store.df

        # Layer 1: Rule filter
        if conditions:
            params = parse_search_conditions(conditions)
            df = apply_hard_filters(df, **params)
        else:
            df = apply_hard_filters(df)

        query_text = f"岗位需求:{position_name}"

        # Layer 2: Keyword match (primary — always works, even with mock)
        ranked_ids = keyword_search(df, query_text, top_n=50)

        # Layer 2b: Vector semantic (blend-in when real embeddings available)
        from utils.config import LLM_BACKEND
        if LLM_BACKEND != "mock" and self.store.has_vector_index:
            try:
                query_emb = self.llm.embed([query_text])[0]
                vec_ids = self.store.search_similar(query_emb, top_k=30)
                # Blend into ranked_ids
                for vid in vec_ids[:15]:
                    if vid not in set(ranked_ids[:30]):
                        ranked_ids.insert(min(10, len(ranked_ids)), vid)
            except Exception:
                pass

        # Build candidate profiles with keyword scores
        filtered_ids = set(_safe_df_ids(df))
        ranked_ids = [eid for eid in ranked_ids if eid in filtered_ids]
        keyword_scores = keyword_score_for_candidates(df, query_text, ranked_ids[:top_n * 2])

        candidates = []
        for eid in ranked_ids[:top_n * 2]:
            profile = self.store.get_by_id(eid)
            if profile:
                raw = keyword_scores.get(eid, 0)
                normalized = min(99, round(raw / 20.0 * 100, 1)) if raw > 0 else 0
                candidates.append({
                    "id": eid,
                    "profile": profile,
                    "vector_score": normalized,
                })

        # Layer 3: LLM rank
        summary = ""
        if candidates:
            candidates, summary = llm_rank(self.llm, query_text, candidates, top_n=top_n)

        for c in candidates:
            c["final"] = compute_final_score(True, c.get("vector_score", 0), c.get("llm_score", 0))

        return {
            "candidates": candidates[:top_n],
            "total_matched": len(df),
            "summary": summary,
            "position": position_name,
        }

    def match_person_to_position(
        self,
        employee_id: str,
        position_list: list[dict],
        top_n: int = 10,
    ) -> dict:
        """人找岗: given an employee, find matching positions."""
        profile = self.store.get_by_id(employee_id)
        if not profile:
            return {"candidates": [], "error": f"Employee {employee_id} not found"}

        profile_text = build_text_profile(profile)

        try:
            profile_emb = self.llm.embed([profile_text])[0]
        except Exception:
            profile_emb = [0.0] * 384

        # Match against each position
        matches = []
        for pos in position_list:
            pos_text = f"{pos.get('name','')} {pos.get('requirements','')} {pos.get('description','')}"
            try:
                pos_emb = self.llm.embed([pos_text])[0]
                import numpy as np
                p_vec = np.array(profile_emb)
                q_vec = np.array(pos_emb)
                sim = float((p_vec @ q_vec) / (np.linalg.norm(p_vec) * np.linalg.norm(q_vec) + 1e-8))
            except Exception:
                sim = 0.5

            matches.append({
                "position": pos,
                "vector_score": round(sim * 100, 1),
            })

        matches.sort(key=lambda x: x["vector_score"], reverse=True)
        top_matches = matches[:top_n]

        # LLM ranking
        if top_matches:
            try:
                cands_for_llm = [
                    {
                        "id": m["position"]["name"],
                        "profile": {
                            "姓名": profile.get("姓名", ""),
                            "岗位": profile.get("岗位", ""),
                            "技能标签": profile.get("技能标签", ""),
                            "绩效等级": profile.get("绩效等级", ""),
                            **m["position"],
                        },
                        "vector_score": m["vector_score"],
                    }
                    for m in top_matches
                ]
                query = f"员工{profile.get('姓名','')} 寻找合适的岗位"
                ranked, _ = llm_rank(self.llm, query, cands_for_llm, top_n=top_n)
                for i, m in enumerate(top_matches):
                    for r in ranked:
                        if r.get("id") == m["position"]["name"]:
                            m["grade"] = r.get("grade", "B")
                            m["reason"] = r.get("reason", "")
                            m["llm_score"] = r.get("llm_score", m["vector_score"])
                            break
            except Exception:
                for m in top_matches:
                    m["grade"] = compute_match_grade(m["vector_score"])
                    m["reason"] = ""

        return {
            "employee_id": employee_id,
            "employee_name": profile.get("姓名", ""),
            "matches": top_matches,
        }
