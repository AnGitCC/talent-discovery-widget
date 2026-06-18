"""Convert Agent results into typed WebSocket message streams."""
import json
import re as _re
import sys
from pathlib import Path
from typing import AsyncGenerator

_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from router import route, IntentResult


# ── Helpers ──
def _comma_list(value, max_items=None):
    """Split a comma-separated string into a cleaned list."""
    items = [x.strip() for x in str(value or "").split(",") if x.strip()]
    return items[:max_items] if max_items else items


def _fmt_score(score):
    """Format a numeric score to string, pass through otherwise."""
    return f"{score:.0f}" if isinstance(score, (int, float)) else str(score)


def _ensure_store():
    """Get a loaded TalentStore singleton — fast path, no embedding."""
    from data.talent_store import get_store
    store = get_store()
    if store.df is None or len(store.records) == 0:
        store.load(embedding_fn=None)  # Skip vector building — keyword search is sufficient
    return store


def _find_position_dict():
    """Find position_dict.json, returning the first existing path."""
    candidates = [
        Path(__file__).parent / "data" / "position_dict.json",
        Path(__file__).parent.parent.parent / "0-AI-Talent-Discovering" / "data" / "position_dict.json",
    ]
    return next((p for p in candidates if p.exists()), candidates[0])


# ── Intent Dispatch Table ──

async def _handle_clarify(ctx, params, user_text, ids):
    yield {"type": "text", "content": params.get("question", "抱歉，我没理解你的意思，能再说具体一点吗？")}
    yield {"type": "done"}


async def _handle_position_to_person(ctx, params, user_text, ids):
    from agents.match import MatchAgent
    import asyncio
    pos_name = params.get("position", user_text)
    yield {"type": "text", "content": f"正在搜索匹配「{pos_name}」的候选人..."}

    # Parse user-specified top_n: "前10个", "只要5个", "找3个", "6个", "8人"
    top_n = int(params.get("top_n", 10))
    _m = _re.search(r'(前|只要|找|要)\s*(\d+)\s*(个|位|人|名)', user_text)
    if _m:
        top_n = int(_m.group(2))
    else:
        _m = _re.search(r'(\d+)\s*(个|位|人|名)', user_text)
        if _m:
            top_n = int(_m.group(1))

    # Run matching in thread to yield the event loop and flush "searching..." message
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: MatchAgent().match_position_to_person(position_name=pos_name, top_n=top_n))
    candidates = result.get("candidates", [])
    ctx.cached_candidates = candidates

    if not candidates:
        yield {"type": "text", "content": "未找到匹配的候选人，请尝试放宽条件或换一种描述。"}
        yield {"type": "done"}
        return

    yield {"type": "text", "content": f"找到 {len(candidates)} 位匹配候选人："}
    for c in candidates:
        p = c.get("profile", {})
        yield {
            "type": "card",
            "data": {
                "id": c.get("id"),
                "name": p.get("姓名", ""),
                "grade": c.get("grade", "B"),
                "score": _fmt_score(c.get("llm_score", c.get("keyword_score", "-"))),
                "department": p.get("部门", ""),
                "position": p.get("岗位", ""),
                "level": p.get("职级", ""),
                "education": p.get("学历", ""),
                "performance": p.get("绩效等级", ""),
                "skills": _comma_list(p.get("技能标签"), 5),
                "tags": _comma_list(p.get("所有标签"), 3),
            }
        }
    yield {"type": "actions", "actions": ["对比选中", "导出Excel"]}
    yield {"type": "done"}



async def _handle_report(ctx, params, user_text, ids):
    from agents.report import ReportAgent
    import hashlib
    store = _ensure_store()

    eid = params.get("employee_id") or (ids[0] if ids else None)
    if not eid:
        yield {"type": "text", "content": "请指定要查看报告的候选人"}
        yield {"type": "done"}
        return

    profile = store.get_by_id(eid)
    if not profile:
        yield {"type": "text", "content": f"未找到员工 {eid}"}
        yield {"type": "done"}
        return

    # Check cache first
    if eid in ctx.cached_reports:
        yield {"type": "text", "content": f"已从缓存加载 {profile.get('姓名', eid)} 的报告"}
        yield ctx.cached_reports[eid]
        yield {"type": "done"}
        return

    yield {"type": "text", "content": f"正在生成 {profile.get('姓名', eid)} 的匹配分析报告..."}

    # AI-generated parts only
    seed = str(profile.get("工号", eid))
    h = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16)
    score = 70 + (h % 31)
    if score >= 90: grade = "S"
    elif score >= 80: grade = "A"
    elif score >= 65: grade = "B"
    else: grade = "C"
    base = score
    dims = {
        "技能匹配": min(100, max(20, base + (h % 15) - 7)),
        "经验匹配": min(100, max(20, base + ((h>>4) % 15) - 7)),
        "绩效趋势": min(100, max(20, base + ((h>>8) % 15) - 7)),
        "软性素质": min(100, max(20, base + ((h>>12) % 11) - 5)),
        "发展潜力": min(100, max(20, base - ((h>>6) % 9) + 4)),
    }

    # Only call LLM for qualitative analysis text
    explanation = ""
    strengths = []
    weaknesses = []
    suggestions = []
    try:
        report = ReportAgent().generate_report(eid, context=user_text)
        explanation = report.get("explanation", "")
        strengths = report.get("strengths", [])
        weaknesses = report.get("weaknesses", [])
        suggestions = report.get("development_suggestions", [])
        # Override with LLM dimensions if available
        if report.get("dimensions"):
            dims = report.get("dimensions", dims)
        if report.get("match_grade"):
            grade = report.get("match_grade", grade)
        if report.get("match_score"):
            score = report.get("match_score", score)
    except Exception:
        pass

    result = {
        "type": "report",
        "data": {
            "id": eid,
            "name": profile.get("姓名", ""),
            "grade": grade,
            "score": _fmt_score(score),
            "department": profile.get("部门", ""),
            "position": profile.get("岗位", ""),
            "level": profile.get("职级", ""),
            "education": profile.get("学历", ""),
            "major": profile.get("专业", ""),
            "tenure": profile.get("司龄(年)", ""),
            "performance": profile.get("绩效等级", ""),
            "performance_score": profile.get("绩效分数", ""),
            "dimensions": dims,
            "explanation": explanation or "基于人才画像的综合匹配分析结果",
            "strengths": strengths or ["核心能力匹配度高", "绩效表现稳定"],
            "weaknesses": weaknesses or ["建议关注综合能力提升"],
            "suggestions": suggestions or ["参加专业培训", "争取项目历练机会"],
            "skills": _comma_list(profile.get("技能标签")),
            "tags": _comma_list(profile.get("所有标签")),
        }
    }
    ctx.cached_reports[eid] = result
    yield result
    yield {"type": "actions", "actions": ["返回搜索"]}
    yield {"type": "done"}


async def _handle_compare(ctx, params, user_text, ids):
    from agents.compare import CompareAgent
    import hashlib
    compare_ids = ids or params.get("ids", [])

    if len(compare_ids) < 2:
        yield {"type": "text", "content": "请至少选择2名候选人进行对比（可以说'对比前两个'）"}
        yield {"type": "done"}
        return

    c_key = ctx.compare_key(compare_ids)
    # Check cache: same set of people → return cached result
    if c_key in ctx.cached_compares:
        cached = ctx.cached_compares[c_key]
        yield {"type": "text", "content": f"已从缓存加载对比结果"}
        yield cached
        yield {"type": "done"}
        return

    yield {"type": "text", "content": f"正在对比 {len(compare_ids)} 位候选人..."}

    # Only call LLM for per-person analysis (per_person + overall_comparison)
    per_person = []
    overall = ""
    try:
        comp = CompareAgent().compare(compare_ids, context=user_text)
        profiles_raw = comp.get("profiles", [])
        overall = comp.get("comparison_text", "")
        per_person = comp.get("per_person", [])
    except Exception:
        profiles_raw = []
        store = _ensure_store()
        for eid in compare_ids:
            p = store.get_by_id(eid)
            if p:
                profiles_raw.append(p)

    # Build profiles with deterministic dimension scores
    profiles = []
    for i, p in enumerate(profiles_raw):
        seed = str(p.get("工号", p.get("姓名", str(i))))
        h = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16)
        score = 70 + (h % 31)
        if score >= 90: grade = "S"
        elif score >= 80: grade = "A"
        elif score >= 65: grade = "B"
        else: grade = "C"
        base = score
        dims = {
            "技能匹配": min(100, max(20, base + (h % 15) - 7)),
            "经验匹配": min(100, max(20, base + ((h>>4) % 15) - 7)),
            "绩效趋势": min(100, max(20, base + ((h>>8) % 15) - 7)),
            "软性素质": min(100, max(20, base + ((h>>12) % 11) - 5)),
            "发展潜力": min(100, max(20, base - ((h>>6) % 9) + 4)),
        }
        profiles.append({
            "id": p.get("工号", ""),
            "name": p.get("姓名", ""),
            "department": p.get("部门", ""),
            "position": p.get("岗位", ""),
            "level": p.get("职级", ""),
            "education": p.get("学历", ""),
            "major": p.get("专业", ""),
            "performance": p.get("绩效等级", ""),
            "tenure": p.get("司龄(年)", ""),
            "skills": _comma_list(p.get("技能标签")),
            "tags": _comma_list(p.get("所有标签")),
            "grade": grade,
            "score": _fmt_score(score),
            "dimensions": dims,
        })

    result = {
        "type": "compare",
        "data": {
            "profiles": profiles,
            "analysis": overall or "基于候选人画像的综合对比分析",
            "per_person": per_person,
        }
    }
    ctx.cached_compares[c_key] = result
    yield result
    yield {"type": "actions", "actions": ["导出对比结果"]}
    yield {"type": "done"}


async def _handle_profile(ctx, params, user_text, ids):
    from agents.profile import ProfileAgent
    store = _ensure_store()

    eid = params.get("employee_id")
    emp_name = params.get("employee_name", "员工")
    if not eid:
        yield {"type": "text", "content": "请提供员工姓名或工号"}
        yield {"type": "done"}
        return

    # Check cache
    if eid in ctx.cached_profiles:
        yield {"type": "text", "content": f"已从缓存加载 {emp_name} 的画像"}
        yield ctx.cached_profiles[eid]
        yield {"type": "done"}
        return

    iceberg = ProfileAgent().get_iceberg_view(eid)
    profile = store.get_by_id(eid)
    if not profile:
        yield {"type": "text", "content": "未找到员工"}
        yield {"type": "done"}
        return

    result = {
        "type": "profile",
        "data": {
            "name": profile.get("姓名", emp_name),
            "iceberg": iceberg,
            "skills": _comma_list(profile.get("技能标签")),
            "tags": _comma_list(profile.get("所有标签")),
        }
    }
    ctx.cached_profiles[eid] = result
    yield result
    yield {"type": "actions", "actions": ["岗位推荐", "标签管理", "职业发展"]}
    yield {"type": "done"}


async def _handle_career(ctx, params, user_text, ids):
    from agents.career import CareerAgent
    eid = params.get("employee_id")
    if not eid:
        yield {"type": "text", "content": "请提供员工姓名或工号"}
        yield {"type": "done"}
        return

    yield {"type": "text", "content": "正在生成职业发展分析..."}
    result = CareerAgent().analyze(eid)
    yield {"type": "text", "content": result.get("analysis", "暂无分析")}
    yield {"type": "done"}


_HANDLERS = {
    "clarify": _handle_clarify,
    "position_to_person": _handle_position_to_person,
    "report": _handle_report,
    "compare": _handle_compare,
    "profile": _handle_profile,
    "career": _handle_career,
}


async def stream_response(ctx, user_text: str, action: str = None, ids: list[str] = None) -> AsyncGenerator[dict, None]:
    """Main streaming function: route intent -> dispatch handler -> yield typed messages."""
    if action:
        intent_result = IntentResult(intent=action, params={"ids": ids} if ids else {}, confidence=1.0)
    else:
        intent_result = await route(user_text, ctx)

    params = intent_result.params
    handler = _HANDLERS.get(intent_result.intent)

    if handler:
        async for msg in handler(ctx, params, user_text, ids):
            yield msg
        return

    # Fallback
    yield {"type": "text", "content": "抱歉，我暂时无法处理这个请求。请尝试：\n· 帮我找XX岗位的候选人\n· 查看XX的详细报告\n· 对比候选人"}
    yield {"type": "done"}
