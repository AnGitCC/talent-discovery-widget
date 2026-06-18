"""NLP intent router: user text → intent → Agent dispatch. LLM-powered for accuracy."""
import json
import re
import sys
from pathlib import Path
from typing import Any
from dataclasses import dataclass

_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from llm.backend import get_llm

_CN_DIGIT = {"一":1,"二":2,"两":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
_DIGIT_PAT = r'(\d+|[一二两三四五六七八九十])'  # matches "3" or "三"


def _parse_num(text: str, default: int = 2) -> int:
    """Parse '3个/三个/前3/前三' → int. Handles both Arabic and Chinese numerals."""
    m = re.search(r'(\d+)\s*(?:个|位|人|名)?', text)
    if m: return int(m.group(1))
    m = re.search(r'([一二两三四五六七八九十])\s*(?:个|位|人|名)?', text)
    if m: return _CN_DIGIT.get(m.group(1), default)
    return default


ROUTER_PROMPT = """你是意图路由器。分析用户输入，返回精准JSON。

意图类型：
- position_to_person: 搜索/查找/推荐候选人。params: {position:岗位名描述}
- compare: 对比候选人。如果用户说"对比前N个"/"比较选中的"/"对比这几个人"，且上下文有候选人列表，params: {ids:["top-3"]} 用 "top-N" 占位。
- report: 查看单个候选人详细报告。params: {employee_name:姓名}
- profile: 查看员工画像/履历。params: {employee_name:姓名}
- career: 职业发展分析。
- export: 导出Excel。
- clarify: 无法确定意图。

规则：
1. "找"/"搜索"/"有没有"/"几个"/"人" → position_to_person
2. "对比"/"比较" → compare (如果同时提到搜索和对比，返回position_to_person但附加action:compare和compare_n)
3. "详情"/"报告"/"看看" → report
4. "画像"/"履历"/"全景" → profile
5. "导出"/"下载" → export
6. 数量词如"5个"/"8位"/"找3人" → 提取到position_to_person的top_n参数

只返回JSON，不要其他文字。"""


@dataclass
class IntentResult:
    intent: str
    params: dict[str, Any]
    confidence: float


def parse_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try: return json.loads(m.group())
        except: pass
    try: return json.loads(text)
    except: return {}


def quick_match(text: str, ctx) -> IntentResult | None:
    """Ultra-fast keyword match — actions first, then search."""
    t = text.strip()

    # ── COMPARE always wins ──
    if "对比" in t or "比较" in t:
        if ctx and ctx.cached_candidates:
            ids = [c.get("id") for c in ctx.cached_candidates[:10]]
            n = _parse_num(t, default=2)
            ids = ids[:n]
            return IntentResult(intent="compare", params={"ids": ids}, confidence=0.9)
        return IntentResult(intent="compare", params={}, confidence=0.85)

    # ── REPORT / PROFILE ──
    if any(w in t for w in ["报告", "详情", "看看", "画像", "履历"]):
        if ctx and ctx.cached_candidates:
            for c in ctx.cached_candidates:
                name = c.get("profile", {}).get("姓名", "")
                if name and name in t:
                    return IntentResult(intent="report", params={"employee_id": c.get("id")}, confidence=0.9)
            return IntentResult(intent="report", params={"employee_id": ctx.cached_candidates[0].get("id")}, confidence=0.7)
        return IntentResult(intent="report", params={}, confidence=0.8)

    # ── EXPORT ──
    if "导出" in t or "下载" in t:
        return IntentResult(intent="export", params={"format": "xlsx"}, confidence=0.95)

    # ── SEARCH ──
    search_words = ["找", "搜索", "有没有", "推荐", "候选人", "人才", "帮我",
                    "谁是", "哪个", "哪位", "只要", "就要", "给我"]
    has_search = any(w in t for w in search_words)
    bare_qty = bool(re.search(r'(?:^|\s)(' + _DIGIT_PAT + r')\s*(?:个|位|人|名)', t))

    if has_search or bare_qty:
        pos = t
        for _ in range(3):
            prev = pos
            pos = re.sub(r'^(帮我|我要|请|帮忙|给我|找|搜索|推荐|有没有|只要|要|谁是|哪个|哪位|给我)\s*', '', pos).strip()
            if pos == prev: break
        pos = re.sub(r'\s*' + _DIGIT_PAT + r'\s*(个|位|人|名)\s*', ' ', pos).strip()
        pos = re.sub(r'有\s*\d+\s*年\s*经验的?\s*', '', pos).strip()
        if not pos or len(pos) < 2: pos = "人才"
        return IntentResult(intent="position_to_person", params={"position": pos}, confidence=0.9)

    return None


def resolve_employee(text: str) -> dict | None:
    from data.talent_store import get_store
    store = get_store()
    # Store is pre-loaded at startup — no load() call needed

    id_match = re.search(r'G\d{6}', text)
    if id_match:
        eid = id_match.group()
        rec = store.get_by_id(eid)
        if rec: return {"employee_id": eid, "employee_name": rec.get("姓名")}

    for _, row in store.df.iterrows():
        name = str(row.get("姓名", ""))
        if name and len(name) >= 2 and name in text:
            return {"employee_id": row["工号"], "employee_name": name}
    return None


async def route(text: str, ctx) -> IntentResult:
    """Main routing: quick_match → LLM parse → dispatch."""
    # 1. Quick keyword match (instant)
    if result := quick_match(text, ctx):
        return result

    # 2. LLM intent parsing (fast, ~2-3s via SiliconFlow)
    try:
        llm = get_llm()
        response = llm.chat([
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": text},
        ], model="deepseek-ai/DeepSeek-V3", max_tokens=300)
        parsed = parse_json(response)
        return IntentResult(
            intent=parsed.get("intent", "clarify"),
            params=parsed.get("params", {}),
            confidence=parsed.get("confidence", 0.5),
        )
    except Exception:
        return IntentResult(intent="clarify", params={"question": "我没理解你的意思，能再说具体一点吗？"}, confidence=0.3)
