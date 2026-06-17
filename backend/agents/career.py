"""Career Agent — gap analysis, development paths, training recommendations."""
from agents.base import Agent
from llm.prompts import CAREER_SYSTEM
from data.talent_store import get_store


class CareerAgent(Agent):
    """Provides career development advice based on employee profile analysis."""

    def __init__(self):
        super().__init__("CareerAgent", CAREER_SYSTEM)
        self.store = get_store()

    def analyze(self, employee_id: str) -> dict:
        """Generate a complete career development analysis."""
        profile = self.store.get_by_id(employee_id)
        if not profile:
            return {"error": f"Employee {employee_id} not found"}

        profile_text = f"""
员工画像:
  姓名: {profile.get('姓名', '')}
  部门: {profile.get('部门', '')}
  岗位: {profile.get('岗位', '')}
  职级: {profile.get('职级', '')} (职等: {profile.get('职等', '')})
  学历: {profile.get('学历', '')} / {profile.get('专业', '')}
  司龄: {profile.get('司龄(年)', '')}年
  绩效: {profile.get('绩效等级', '')} ({profile.get('绩效分数', '')}分)
  晋升次数: {profile.get('近三年晋升次数', 0)}次
  技能: {profile.get('技能标签', '')}
  证书: {profile.get('证书', '')}
  工作领域: {profile.get('工作领域', '')}
  项目经验: NPI {profile.get('NPI项目数', 0)}个 / 量产 {profile.get('量产项目数', 0)}个 / 管理改善 {profile.get('管理改善项目数', 0)}个
  跨部门经验: {profile.get('跨部门经验', '')}
  标签: {profile.get('所有标签', '')}
  意愿: 调岗={profile.get('是否愿意调岗', '')} 跨部门={profile.get('是否愿意跨部门', '')}
  感兴趣岗位: {profile.get('感兴趣岗位', '')}
  管理经验: 下属{profile.get('直接下属数', 0)}人 带徒{profile.get('带徒人数', 0)}人
"""

        analysis_text = self.ask(
            f"请为以下员工生成职业发展分析报告:\n\n{profile_text}",
            system_override=CAREER_SYSTEM,
            max_tokens=2048,
        )

        return {
            "employee_id": employee_id,
            "employee_name": profile.get("姓名"),
            "department": profile.get("部门"),
            "position": profile.get("岗位"),
            "analysis": analysis_text,
        }
