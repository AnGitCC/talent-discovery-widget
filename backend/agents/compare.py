"""Compare Agent — side-by-side multi-candidate comparison."""
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

        user_msg = f"比较上下文: {context}\n\n{profiles_text}\n\n请生成对比分析报告。"
        response = self.ask(user_msg)

        return {
            "employee_ids": employee_ids,
            "profiles": profiles,
            "comparison_text": response,
            "context": context,
        }
