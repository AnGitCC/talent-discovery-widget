"""Third layer of matching engine: LLM-based ranking and explainability."""
import json
import re
from typing import Any
from llm.prompts import MATCH_SYSTEM


def extract_json(text: str) -> dict:
    """Extract JSON object from LLM response (may be wrapped in markdown)."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}


def llm_rank(
    llm: Any,
    query_context: str,
    candidates: list[dict],
    top_n: int = 10,
) -> tuple[list[dict], str]:
    """Use LLM to rank and score the top candidates.

    Args:
        llm: LLM backend instance
        query_context: Description of what we're looking for
        candidates: List of candidate dicts with id, profile, vector_score
        top_n: How many to return

    Returns:
        (ranked candidates list, summary string)
    """
    if not candidates:
        return [], ""

    candidate_text = ""
    for i, c in enumerate(candidates[:top_n]):
        profile = c.get("profile", {})
        candidate_text += f"""
候选人 {i+1} (ID: {c['id']}):
  姓名: {profile.get('姓名', '')}
  岗位: {profile.get('岗位', '')}
  部门: {profile.get('部门', '')}
  职级: {profile.get('职级', '')}
  学历: {profile.get('学历', '')}
  绩效: {profile.get('绩效等级', '')} ({profile.get('绩效分数', '')}分)
  技能: {profile.get('技能标签', '')}
  标签: {profile.get('所有标签', '')}
  工作领域: {profile.get('工作领域', '')}
  证书: {profile.get('证书', '')}
  意愿调岗: {profile.get('是否愿意调岗', '')}
"""

    messages = [
        {"role": "system", "content": MATCH_SYSTEM},
        {"role": "user", "content": f"""岗位/搜索需求: {query_context}

候选人基本信息如下:
{candidate_text}

请对以上候选人综合评分排序，考虑技能匹配度、岗位经验、绩效趋势、发展潜力等因素。
按匹配度从高到低排列，给出评分(0-100)和匹配等级(S/A/B/C)。"""}
    ]

    response = llm.chat(messages, max_tokens=2048)
    result = extract_json(response)

    rankings = result.get("rankings", [])
    summary = result.get("summary", "")

    rank_map = {}
    for r in rankings:
        eid = r.get("employee_id", "")
        rank_map[eid] = {
            "llm_score": r.get("score", 0),
            "grade": r.get("grade", "B"),
            "reason": r.get("reason", ""),
        }

    for c in candidates:
        c.update(rank_map.get(c["id"], {
            "llm_score": 50,
            "grade": "B",
            "reason": "",
        }))

    candidates.sort(key=lambda x: x.get("llm_score", 0), reverse=True)
    return candidates[:top_n], summary


def compute_match_grade(score: float) -> str:
    """Convert numeric score to S/A/B/C grade."""
    if score >= 90:
        return "S"
    elif score >= 75:
        return "A"
    elif score >= 60:
        return "B"
    else:
        return "C"


def compute_final_score(rule_pass: bool, vector_score: float, llm_score: float = 0) -> dict:
    """Compute final composite score from all three layers."""
    if not rule_pass:
        return {"total_score": 0, "grade": "C", "breakdown": {"rule": 0, "vector": 0, "llm": 0}}

    total = vector_score * 40 + llm_score * 0.6
    total = min(100, max(0, total))

    return {
        "total_score": round(total, 1),
        "grade": compute_match_grade(total),
        "breakdown": {
            "rule_pass": True,
            "vector_score": round(vector_score, 1),
            "llm_score": round(llm_score, 1),
        },
    }
