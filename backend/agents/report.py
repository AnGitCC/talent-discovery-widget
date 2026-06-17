"""Report Agent — detailed match reports with grades, radar, explanations."""
from agents.base import Agent
from llm.prompts import REPORT_SYSTEM
from data.talent_store import get_store


class ReportAgent(Agent):
    """Generate detailed match analysis report for a single candidate."""

    def __init__(self):
        super().__init__("ReportAgent", REPORT_SYSTEM)
        self.store = get_store()

    def generate_report(
        self,
        employee_id: str,
        context: str = "",
        match_data: dict | None = None,
    ) -> dict:
        """Generate a full match report."""
        profile = self.store.get_by_id(employee_id)
        if not profile:
            return {"error": f"Employee {employee_id} not found"}

        profile_text = f"""
员工画像:
  姓名: {profile.get('姓名', '')}
  工号: {profile.get('工号', '')}
  性别: {profile.get('性别', '')}
  年龄: {profile.get('年龄', '')}
  部门: {profile.get('部门', '')}
  岗位: {profile.get('岗位', '')}
  职级: {profile.get('职级', '')} (职等: {profile.get('职等', '')})
  学历: {profile.get('学历', '')} / {profile.get('专业', '')} / {profile.get('院校类型', '')}
  司龄: {profile.get('司龄(年)', '')}年
  绩效: {profile.get('绩效等级', '')} ({profile.get('绩效分数', '')}分)
  技能: {profile.get('技能标签', '')}
  标签: {profile.get('所有标签', '')}
  工作领域: {profile.get('工作领域', '')}
  证书: {profile.get('证书', '')}
  外派: {profile.get('外派国家', '')}
  跨部门经验: {profile.get('跨部门经验', '')}
  意愿调岗: {profile.get('是否愿意调岗', '')}
  感兴趣岗位: {profile.get('感兴趣岗位', '')}
  NPI项目: {profile.get('NPI项目数', 0)}个
  量产项目: {profile.get('量产项目数', 0)}个
  管理改善项目: {profile.get('管理改善项目数', 0)}个
  带徒人数: {profile.get('带徒人数', 0)}人
"""

        messages = [
            {"role": "system", "content": REPORT_SYSTEM},
            {"role": "user", "content": f"匹配上下文: {context}\n\n{profile_text}\n\n请生成详细的匹配度分析报告。"}
        ]

        result = self.ask_json(str(messages))

        if match_data:
            result.update(match_data)

        result.setdefault("match_grade", match_data.get("grade", "B") if match_data else "B")
        result.setdefault("match_score", match_data.get("total_score", 60) if match_data else 60)
        result.setdefault("dimensions", {})
        result.setdefault("explanation", "")
        result.setdefault("strengths", [])
        result.setdefault("weaknesses", [])
        result.setdefault("development_suggestions", [])

        return {
            "employee_id": employee_id,
            "profile": profile,
            **result,
        }
