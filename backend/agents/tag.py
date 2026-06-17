"""Tag Agent — auto-tag, smart-tag, and categorized tag management."""
from agents.base import Agent
from llm.prompts import TAG_SYSTEM
from data.talent_store import get_store


TAG_CATEGORIES = {
    "水上": ["年龄标签", "籍贯标签", "忠勤标签", "职等标签", "学校类型标签",
             "劳模标签", "关键人才", "敏感岗位"],
    "水面": ["高成长标签", "研发项目达人标签", "量产项目达人标签", "管理改善达人标签",
             "Hipo人才", "导师", "GPS人员", "国际化人才", "技委会成员"],
    "水下": [],
}


class TagAgent(Agent):
    """Handles tag operations: auto-tag, smart-tag generation, categorized management."""

    def __init__(self):
        super().__init__("TagAgent", TAG_SYSTEM)
        self.store = get_store()

    def auto_tag(self, employee_id: str, tag_name: str) -> dict:
        """Add a tag to an employee from the existing tag architecture."""
        profile = self.store.get_by_id(employee_id)
        if not profile:
            return {"error": f"Employee {employee_id} not found"}

        existing_tags = str(profile.get("所有标签", "")).split(",")
        existing_tags = [t.strip() for t in existing_tags if t.strip()]

        if tag_name in existing_tags:
            return {"status": "already_tagged", "tag": tag_name, "employee_id": employee_id}

        existing_tags.append(tag_name)
        return {
            "status": "tagged",
            "tag": tag_name,
            "employee_id": employee_id,
            "employee_name": profile.get("姓名"),
            "all_tags": existing_tags,
        }

    def smart_extract_tags(self, text: str) -> dict:
        """Extract skill/ability tags from unstructured text via LLM."""
        return self.ask_json(f"请从以下文本中提取技能和能力标签:\n\n{text}")

    def categorize_tags(self, employee_id: str) -> dict:
        """Categorize an employee's tags by iceberg model layers."""
        profile = self.store.get_by_id(employee_id)
        if not profile:
            return {"error": f"Employee {employee_id} not found"}

        all_tags = str(profile.get("所有标签", "")).split(",")
        all_tags = [t.strip() for t in all_tags if t.strip()]

        categorized = {"水上": [], "水面": [], "水下": [], "未分类": []}
        for tag in all_tags:
            placed = False
            for cat, cat_tags in TAG_CATEGORIES.items():
                if tag in cat_tags:
                    categorized[cat].append(tag)
                    placed = True
                    break
            if not placed:
                categorized["未分类"].append(tag)

        return {
            "employee_id": employee_id,
            "employee_name": profile.get("姓名"),
            "categorized_tags": categorized,
            "total_tags": len(all_tags),
        }

    def get_all_available_tags(self) -> dict:
        """Get all tags in the system organized by iceberg category."""
        all_tags = self.store.get_all_tags()
        categorized = {"水上": [], "水面": [], "水下": [], "未分类": []}
        for tag in all_tags:
            placed = False
            for cat, cat_tags in TAG_CATEGORIES.items():
                if tag in cat_tags:
                    categorized[cat].append(tag)
                    placed = True
                    break
            if not placed:
                categorized["未分类"].append(tag)
        return categorized
