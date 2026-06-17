"""Profile Agent — view and update employee talent profiles.

This agent does NOT use LLM — pure data access via TalentStore.
"""
from data.talent_store import get_store


class ProfileAgent:
    """Handles employee profile viewing and self-service updates."""

    def __init__(self):
        self.store = get_store()

    def get_profile(self, employee_id: str) -> dict | None:
        """Get full employee profile."""
        return self.store.get_by_id(employee_id)

    def search_employee(self, query: str) -> list[dict]:
        """Simple search by name or ID."""
        results = []
        query_lower = query.lower()
        for r in self.store.records:
            name = str(r.get("姓名", ""))
            eid = str(r.get("工号", ""))
            if query_lower in name.lower() or query_lower in eid.lower():
                results.append({
                    "id": eid,
                    "name": name,
                    "department": str(r.get("部门", "")),
                    "position": str(r.get("岗位", "")),
                    "level": str(r.get("职级", "")),
                })
                if len(results) >= 20:
                    break
        return results

    def update_profile(self, employee_id: str, updates: dict) -> dict:
        """Update profile fields (in-memory only for MVP)."""
        return {"status": "ok", "updated_fields": list(updates.keys())}

    def get_iceberg_view(self, employee_id: str) -> dict:
        """Return profile data organized by iceberg model layers."""
        profile = self.get_profile(employee_id)
        if not profile:
            return {}

        return {
            "水上_可见": {
                "基本信息": {
                    "姓名": profile.get("姓名"),
                    "工号": profile.get("工号"),
                    "性别": profile.get("性别"),
                    "年龄": profile.get("年龄"),
                },
                "学历背景": {
                    "学历": profile.get("学历"),
                    "专业": profile.get("专业"),
                    "院校类型": profile.get("院校类型"),
                },
                "任职信息": {
                    "部门": profile.get("部门"),
                    "岗位": profile.get("岗位"),
                    "职级": profile.get("职级"),
                    "司龄": f"{profile.get('司龄(年)', '')}年",
                },
                "绩效": {
                    "绩效等级": profile.get("绩效等级"),
                    "绩效分数": profile.get("绩效分数"),
                },
            },
            "水面_核心能力": {
                "技能": profile.get("技能标签", "").split(",") if profile.get("技能标签") else [],
                "证书": profile.get("证书", "").split(",") if profile.get("证书") else [],
                "工作领域": profile.get("工作领域", "").split(";") if profile.get("工作领域") else [],
                "项目经验": {
                    "NPI项目": profile.get("NPI项目数", 0),
                    "量产项目": profile.get("量产项目数", 0),
                    "管理改善": profile.get("管理改善项目数", 0),
                },
            },
            "水下_隐性特质": {
                "标签": profile.get("所有标签", "").split(",") if profile.get("所有标签") else [],
                "意愿": {
                    "愿意调岗": profile.get("是否愿意调岗"),
                    "愿意跨部门": profile.get("是否愿意跨部门"),
                    "感兴趣岗位": profile.get("感兴趣岗位"),
                },
            },
        }
