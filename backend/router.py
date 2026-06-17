"""NLP intent router: user text → intent → Agent dispatch."""
import json
import re
import sys
from pathlib import Path
from typing import Any
from dataclasses import dataclass

# Ensure backend dir is importable for data.talent_store etc.
_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from llm.backend import get_llm


ROUTER_PROMPT = """你是一个人才系统意图解析器。将用户输入映射到以下意图之一，并提取参数。

意图列表:
- position_to_person: 岗找人，根据岗位需求找候选人。参数: position(岗位名), skills(技能要求列表), filters(筛选条件)
- search: 自然语言搜索人才库。参数: query(搜索描述)
- report: 查看单个候选人详细匹配报告。参数: employee_name或employee_id
- compare: 对比多个候选人。参数: names(姓名列表)或ids(工号列表)
- profile: 查看员工冰山画像。参数: employee_name或employee_id
- career: 职业发展分析。参数: employee_name或employee_id
- tag: 标签操作。参数: action(add/extract/view), employee_name
- export: 导出。参数: format(xlsx)
- clarify: 无法确定意图时返回澄清问题。参数: question

规则:
1. "帮我找" "搜索" "推荐候选人" "有没有" → position_to_person
3. "对比" "比较" → compare
4. "报告" "详情" "详细" → report
5. "画像" "履历" "全景" → profile
6. "职业" "发展" "成长" "规划" → career
7. "导出" "下载" → export
8. 如果涉及多个意图或不确定，选最可能的。confidence < 0.7 时返回 clarify。

只返回JSON:
{"intent":"...","params":{...},"confidence":0.0-1.0}
"""


@dataclass
class IntentResult:
    intent: str
    params: dict[str, Any]
    confidence: float


def parse_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code fences."""
    text = text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


def quick_match(text: str, ctx) -> IntentResult | None:
    """Fast keyword-based intent matching to avoid LLM call for obvious cases."""
    t = text.strip()

    if ctx and ctx.cached_candidates:
        if any(w in t for w in ["对比", "比较"]):
            ids = [c.get("id") for c in ctx.cached_candidates[:5]]
            if "前" in t:
                m = re.search(r'前\s*(\d+)', t)
                n = int(m.group(1)) if m else 2
                ids = ids[:n]
            return IntentResult(intent="compare", params={"ids": ids}, confidence=0.9)

        if any(w in t for w in ["报告", "详情", "详细"]):
            for c in ctx.cached_candidates:
                name = c.get("profile", {}).get("姓名", "")
                if name and name in t:
                    return IntentResult(intent="report", params={"employee_id": c.get("id")}, confidence=0.9)
            if ctx.cached_candidates:
                return IntentResult(intent="report", params={"employee_id": ctx.cached_candidates[0].get("id")}, confidence=0.75)

        if "导出" in t or "下载" in t:
            return IntentResult(intent="export", params={"format": "xlsx"}, confidence=0.9)

    return None


def resolve_employee(text: str) -> dict | None:
    """Try to resolve an employee name or ID from text against the store."""
    from data.talent_store import get_store
    store = get_store()
    if store.df is None or len(store.records) == 0:
        from backend.llm.backend import get_llm
        store.load(embedding_fn=get_llm().embed)

    # Try ID match
    id_match = re.search(r'G\d{6}', text)
    if id_match:
        eid = id_match.group()
        rec = store.get_by_id(eid)
        if rec:
            return {"employee_id": eid, "employee_name": rec.get("姓名")}

    # Try name match
    for _, row in store.df.iterrows():
        name = str(row.get("姓名", ""))
        if name and len(name) >= 2 and name in text:
            return {"employee_id": row["工号"], "employee_name": name}

    return None


async def route(text: str, ctx) -> IntentResult:
    """Main routing function: quick match → LLM parse → dispatch."""
    # 1. Quick keyword match
    if result := quick_match(text, ctx):
        return result

    # 2. LLM intent parsing
    llm = get_llm()
    response = llm.chat([
        {"role": "system", "content": ROUTER_PROMPT},
        {"role": "user", "content": text},
    ])

    parsed = parse_json(response)
    intent = parsed.get("intent", "clarify")
    params = parsed.get("params", {})
    confidence = parsed.get("confidence", 0.5)

    # 3. Try to resolve employee references
    emp = resolve_employee(text)
    if emp:
        params.update(emp)

    return IntentResult(intent=intent, params=params, confidence=confidence)
