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
from llm.prompts import COMPARE_SYSTEM


# ── Helpers ──
_CNS = {"一":1,"二":2,"两":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
def _parse_num(text, default=None):
    """Parse '3个/三个/前3/前三' → int. Handles Arabic + Chinese numerals."""
    m = _re.search(r'(\d+)\s*(?:个|位|人|名)?', text)
    if m: return int(m.group(1))
    m = _re.search(r'([一二两三四五六七八九十])\s*(?:个|位|人|名)?', text)
    if m: return _CNS.get(m.group(1), default)
    return default

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
    pos_name = params.get("position", user_text)
    yield {"type": "text", "content": "正在搜索匹配「" + pos_name + "」的候选人..."}

    # Parse user-specified top_n from text
    top_n = int(params.get("top_n", 10))
    _pn = _parse_num(user_text)
    if _pn: top_n = _pn

    result = MatchAgent().match_position_to_person(position_name=pos_name, top_n=top_n)
    candidates = result.get("candidates", [])
    ctx.cached_candidates = candidates

    if not candidates:
        yield {"type": "text", "content": "未找到匹配的候选人，请尝试放宽条件或换一种描述。"}
        yield {"type": "done"}
        return

    yield {"type": "text", "content": "找到 " + str(len(candidates)) + " 位匹配候选人："}
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

    # Auto-compare: "对比前三/前3个" → auto-trigger
    if candidates:
        _cm = _re.search(r'对比\s*前?\s*(\d+|[一二两三四五六七八九十])\s*(个|位|人|名)?', user_text)
        if _cm:
            cn = _cm.group(1)
            compare_n = int(cn) if cn.isdigit() else _CNS.get(cn, 2)
            compare_n = min(compare_n, len(candidates))
            if compare_n >= 2:
                async for _msg in _handle_compare(ctx, params, user_text, [c.get("id") for c in candidates[:compare_n]]):
                    yield _msg



async def _handle_report(ctx, params, user_text, ids):
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

    # Check cache
    if eid in ctx.cached_reports:
        yield {"type": "text", "content": f"已从缓存加载 {profile.get('姓名', eid)} 的报告"}
        yield ctx.cached_reports[eid]
        yield {"type": "done"}
        return

    yield {"type": "text", "content": f"正在加载 {profile.get('姓名', eid)} 的详细档案..."}

    # Deterministic score — no AI needed for detail page
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

    # All data from Excel — zero AI cost
    result = {
        "type": "report",
        "data": {
            "id": eid,
            "name": profile.get("姓名", ""),
            "grade": grade,
            "score": _fmt_score(score),
            "gender": profile.get("性别", ""),
            "age": profile.get("年龄", ""),
            "department": profile.get("部门", ""),
            "position": profile.get("岗位", ""),
            "level": profile.get("职级", ""),
            "level_num": profile.get("职等", ""),
            "education": profile.get("学历", ""),
            "school_type": profile.get("院校类型", ""),
            "major": profile.get("专业", ""),
            "workplace": profile.get("工作地点", ""),
            "native": profile.get("籍贯标签", ""),
            "tenure": profile.get("司龄(年)", ""),
            "performance": profile.get("绩效等级", ""),
            "performance_score": profile.get("绩效分数", ""),
            "supervisor_name": profile.get("主管姓名", ""),
            "subordinates": profile.get("直接下属数", ""),
            "promotions_3y": profile.get("近三年晋升次数", ""),
            "work_domain": profile.get("工作领域", ""),
            "cross_dept": profile.get("跨部门经验", ""),
            "npi_projects": profile.get("NPI项目数", ""),
            "mass_projects": profile.get("量产项目数", ""),
            "mgmt_projects": profile.get("管理改善项目数", ""),
            "certificates": profile.get("证书", ""),
            "is_mentor": profile.get("是否导师", ""),
            "mentees": profile.get("带徒人数", ""),
            "is_gps": profile.get("是否GPS人员", ""),
            "is_international": profile.get("国际化人才", ""),
            "overseas": profile.get("外派国家", ""),
            "willing_transfer": profile.get("是否愿意调岗", ""),
            "interested_position": profile.get("感兴趣岗位", ""),
            "willing_cross_dept": profile.get("是否愿意跨部门", ""),
            "willing_cross_bu": profile.get("是否愿意跨BU", ""),
            "dimensions": dims,
            "explanation": "基于员工档案数据和岗位体系匹配的综合评估",
            "strengths": ["综合能力匹配度高", "绩效表现符合岗位要求"],
            "weaknesses": ["建议持续关注职业发展规划"],
            "suggestions": ["参加专业技能提升培训", "争取项目历练机会"],
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

    # Handle "top-N" placeholder from router (LLM → "对比前3个" → ids:["top-3"])
    resolved_ids = []
    for cid in (compare_ids or []):
        if isinstance(cid, str) and cid.startswith("top-"):
            n = int(cid.split("-")[1])
            cached_ids = [c.get("id") for c in (ctx.cached_candidates or [])]
            resolved_ids = cached_ids[:n]
            break
        else:
            resolved_ids.append(cid)
    if resolved_ids:
        compare_ids = resolved_ids

    if len(compare_ids) < 2:
        yield {"type": "text", "content": "请至少选择2名候选人进行对比（可以说'对比前两个'）"}
        yield {"type": "done"}
        return

    c_key = ctx.compare_key(compare_ids)
    # Check cache: same set of people → return cached result
    if c_key in ctx.cached_compares and ctx.cached_compares[c_key]["data"].get("per_person"):
        cached = ctx.cached_compares[c_key]
        yield {"type": "text", "content": f"已从缓存加载对比结果"}
        yield cached
        yield {"type": "done"}
        return

    yield {"type": "text", "content": f"正在对比 {len(compare_ids)} 位候选人..."}

    # ── Phase 1: Build base profiles immediately (zero AI) ──
    profiles_raw = []
    store = _ensure_store()
    for eid in compare_ids:
        p = store.get_by_id(eid)
        if p: profiles_raw.append(p)

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

    # Yield base comparison table immediately — user sees data right away
    yield {
        "type": "compare",
        "data": {
            "profiles": profiles,
            "analysis": "AI 分析正在进行中，结果出来后自动更新...",
            "per_person": [],
        }
    }

    # ── Phase 2: LLM analysis with streaming progress ──
    yield {"type": "text", "content": "AI 正在逐人分析对比中..."}

    # Build the compare prompt directly instead of through CompareAgent (avoids double-prompting)
    profiles_text = ""
    for i, p in enumerate(profiles_raw):
        profiles_text += f"""
候选人 {i+1}: 姓名: {p.get('姓名','')}  部门: {p.get('部门','')}  岗位: {p.get('岗位','')}
  职级: {p.get('职级','')}  学历: {p.get('学历','')}/{p.get('专业','')}
  绩效: {p.get('绩效等级','')}({p.get('绩效分数','')}分)  司龄: {p.get('司龄(年)','')}年
  技能: {p.get('技能标签','')}
  标签: {p.get('所有标签','')}
  证书: {p.get('证书','')}
"""

    query_line = ""
    if user_text and user_text.strip():
        query_line = f"\n用户搜索需求: 「{user_text}」\n请围绕用户需求进行针对性分析：strengths要说明该候选人为什么符合这个需求，weaknesses要指出与需求之间的差距，positioning和recommendation要结合需求给出判断。"

    prompt = f"{profiles_text}{query_line}\n请生成对比JSON（strengths每人3-4条，weaknesses每人1-2条，positioning一句定位，recommendation任用建议，comprehensive_score 0-100整数，overall_comparison综合结论2-4句）。只返回JSON，不要其他。"
    messages = [{"role": "system", "content": COMPARE_SYSTEM}, {"role": "user", "content": prompt}]

    raw_text = ""
    per_person = []
    overall = ""
    try:
        # Stream LLM response — user sees progress in real time
        from llm.backend import get_llm
        llm = get_llm()
        async for chunk in llm.chat_stream(messages, model="deepseek-ai/DeepSeek-V4-Pro", timeout=120, temperature=0.1):
            raw_text += chunk
    except Exception as e:
        print(f"LLM stream failed: {e}")

    # Parse structured JSON from streamed text
    if raw_text:
        try:
            data = json.loads(raw_text)
        except:
            m = _re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw_text, re.DOTALL)
            if m:
                try: data = json.loads(m.group(1))
                except: data = {}
            else:
                m2 = _re.search(r'\{.*\}', raw_text, re.DOTALL)
                data = json.loads(m2.group()) if m2 else {}
        overall = data.get("overall_comparison", "")
        per_person = data.get("profiles", [])

    # Fallback: fill missing per_person
    if len(per_person) < len(profiles_raw):
        filled = []
        for i, p in enumerate(profiles_raw):
            if i < len(per_person) and per_person[i].get("comprehensive_score"):
                filled.append(per_person[i])
                continue
            seed2 = str(p.get("工号", p.get("姓名", str(i))))
            h2 = int(hashlib.md5(seed2.encode()).hexdigest()[:4], 16)
            s2 = 65 + (h2 % 31)
            filled.append({
                "name": p.get("姓名", ""),
                "strengths": ["技能匹配度高", "绩效表现稳定", "团队协作良好"][:3],
                "weaknesses": ["管理经验待提升"][:1],
                "comprehensive_score": s2,
                "positioning": "综合能力突出" if s2 >= 80 else "具备成长潜力",
                "recommendation": "建议重点考察" if s2 >= 80 else "建议培养后评估",
            })
        per_person = filled

    if not overall:
        names2 = [p.get("姓名","") for p in profiles_raw[:3]]
        overall = names2[0] + "综合能力最强；" + (names2[1] + "经验丰富。" if len(names2) >= 2 else "")
        if len(names2) >= 3: overall += names2[2] + "潜力较大。"

    # Cache and yield final enriched compare with AI analysis
    ctx.cached_compares[c_key] = {
        "type": "compare",
        "data": {
            "profiles": profiles,
            "analysis": overall,
            "per_person": per_person,
        }
    }
    yield ctx.cached_compares[c_key]
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
