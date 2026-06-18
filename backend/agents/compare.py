"""Compare Agent — side-by-side multi-candidate comparison."""
import json, re
from agents.base import Agent
from llm.prompts import COMPARE_SYSTEM
from data.talent_store import get_store


class CompareAgent(Agent):
    """Compare multiple candidates side by side."""

    def __init__(self):
        super().__init__("CompareAgent", COMPARE_SYSTEM)
        self.store = get_store()

    def compare(
        self,
        employee_ids: list[str],
        context: str = "",
        match_data: dict[str, dict] | None = None,
    ) -> dict:
        """Generate a comparison of multiple candidates."""
        profiles = []
        for eid in employee_ids:
            p = self.store.get_by_id(eid)
            if p:
                profiles.append(p)

        if len(profiles) < 2:
            return {"error": "Need at least 2 candidates for comparison"}

        profiles_text = ""
        for i, p in enumerate(profiles):
            md = match_data.get(str(p["工号"]), {}) if match_data else {}
            profiles_text += f"""
候选人 {i+1}:
  姓名: {p.get('姓名', '')}
  部门: {p.get('部门', '')}
  岗位: {p.get('岗位', '')}
  职级: {p.get('职级', '')}
  学历: {p.get('学历', '')} / {p.get('专业', '')}
  绩效: {p.get('绩效等级', '')} ({p.get('绩效分数', '')}分)
  技能: {p.get('技能标签', '')}
  标签: {p.get('所有标签', '')}
  证书: {p.get('证书', '')}
  得分: {md.get('total_score', md.get('llm_score', '?'))}
  等级: {md.get('grade', '?')}
"""

        user_msg = f"比较上下文: {context}\n\n{profiles_text}\n\n请生成JSON格式的对比分析报告。"
        response = self.ask(user_msg)

        # Parse structured JSON from LLM response
        analysis = self._parse_compare_json(response, profiles)

        return {
            "employee_ids": employee_ids,
            "profiles": profiles,
            "comparison_text": analysis.get("overall_comparison", ""),
            "per_person": analysis.get("per_person", []),
            "context": context,
        }

    def _parse_compare_json(self, response: str, profiles: list) -> dict:
        """Parse the LLM JSON response, falling back gracefully."""
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                except json.JSONDecodeError:
                    data = {}
            else:
                m2 = re.search(r'\{.*\}', response, re.DOTALL)
                if m2:
                    try:
                        data = json.loads(m2.group())
                    except json.JSONDecodeError:
                        data = {}
                else:
                    data = {}

        overall = data.get("overall_comparison", response[:300])

        per_person = []
        llm_profiles = data.get("profiles", [])
        for i, p in enumerate(profiles):
            name = p.get("姓名", "")
            if i < len(llm_profiles):
                lp = llm_profiles[i]
                per_person.append({
                    "name": name,
                    "strengths": lp.get("strengths", []),
                    "weaknesses": lp.get("weaknesses", []),
                    "comprehensive_score": lp.get("comprehensive_score", 0),
                    "positioning": lp.get("positioning", ""),
                    "recommendation": lp.get("recommendation", ""),
                })
            else:
                per_person.append({
                    "name": name,
                    "strengths": [],
                    "weaknesses": [],
                    "comprehensive_score": 0,
                    "positioning": "",
                    "recommendation": "",
                })

        return {"overall_comparison": overall, "per_person": per_person}
