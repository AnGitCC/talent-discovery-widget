"""Pluggable LLM backend: Mock (dev) + AIHub (internal) + Bailian (Alibaba)."""
from typing import Protocol
from utils.config import AIHUB_BASE_URL, AIHUB_API_KEY, AIHUB_MODEL
from utils.config import BAILIAN_API_KEY, BAILIAN_BASE_URL, BAILIAN_CHAT_MODEL, BAILIAN_EMBED_MODEL


class LLMBackend(Protocol):
    """Abstract LLM interface."""
    def chat(self, messages: list[dict], **kwargs) -> str:
        """Send messages, return text response."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts, return vectors."""
        ...


class MockBackend:
    """Mock LLM backend for development — returns plausible fake responses."""

    def chat(self, messages: list[dict], **kwargs) -> str:
        import json
        system = ""
        user = ""
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            elif m["role"] == "user":
                user = m["content"]

        if "SEARCH" in system or "搜索" in user:
            return self._mock_search_response(user)
        elif "ROUTER" in system or "意图解析器" in system:
            return self._mock_router_response(user)
        elif "REPORT" in system or "报告" in system:
            return self._mock_report_response(user)
        elif "COMPARE" in system or "对比" in system:
            return self._mock_compare_response(user)
        elif "TAG" in system or "标签" in user:
            return self._mock_tag_response(user)
        elif "CAREER" in system or "职业" in system:
            return self._mock_career_response(user)
        elif "MATCH" in system:
            return self._mock_match_response(user)
        else:
            return self._mock_match_response(user)

    def _mock_router_response(self, user: str) -> str:
        """Mock NLP router: keyword-based intent matching with real text extraction."""
        if any(w in user for w in ["找", "搜索", "有没有", "推荐候选人"]):
            # Extract position from user text
            import re as _re
            pos = _re.sub(r'(帮我找|搜索|找|有没有|前\d+|个|位|名|只要|要)', '', user).strip() or "人才"
            return '{"intent":"position_to_person","params":{"position":"'+pos+'","skills":[]},"confidence":0.9}'
        elif any(w in user for w in ["适合", "我的岗位", "推荐岗位"]):
            return '{"intent":"person_to_position","params":{},"confidence":0.85}'
        elif any(w in user for w in ["对比", "比较"]):
            return '{"intent":"compare","params":{},"confidence":0.9}'
        elif any(w in user for w in ["报告", "详情"]):
            return '{"intent":"report","params":{},"confidence":0.85}'
        elif any(w in user for w in ["画像", "履历"]):
            return '{"intent":"profile","params":{"employee_name":"'+user.replace('看','').replace('的','').strip()+'"},"confidence":0.8}'  # noqa
        elif any(w in user for w in ["职业", "发展", "规划"]):
            return '{"intent":"career","params":{},"confidence":0.8}'
        elif any(w in user for w in ["导出", "下载"]):
            return '{"intent":"export","params":{"format":"xlsx"},"confidence":0.95}'
        # Default: position_to_person for any search-like query
        return '{"intent":"position_to_person","params":{"position":"'+user.replace('帮我找','').replace('搜索','').strip()+'"},"confidence":0.75}'

    def _mock_search_response(self, user: str) -> str:
        return """```json
{
  "conditions": [
    {"field": "岗位", "op": "contains", "value": "工程师"},
    {"field": "职等", "op": "gte", "value": 5},
    {"field": "学历", "op": "in", "value": ["本科", "硕士"]}
  ],
  "hard_filters": {},
  "search_mode": "semantic",
  "reasoning": "用户想找工程师岗位的候选人，偏好本科以上学历"
}
```"""

    def _mock_match_response(self, user: str) -> str:
        return """```json
{
  "rankings": [],
  "summary": "基于岗位要求与候选人画像的三层匹配分析结果"
}
```"""

    def _mock_report_response(self, user: str) -> str:
        return """{"match_grade":"A","match_score":82,"dimensions":{"技能匹配":85,"经验匹配":80,"绩效趋势":78,"软性素质":82,"发展潜力":85},"explanation":"候选人在技能维度表现突出，核心技术栈与岗位要求高度吻合。近三年绩效呈上升趋势，具备良好的发展潜力。","strengths":["核心技术栈高度匹配","绩效持续优秀","有跨部门协作经验"],"weaknesses":["管理经验偏少","海外项目经验不足"],"development_suggestions":["参加PMP认证培训","可安排海外项目轮岗"]}"""

    def _mock_compare_response(self, user: str) -> str:
        import re as _re2, json as _json
        names = _re2.findall(r'姓名:\s*(\S+)', user)
        n = max(len(names), 2)
        positions = ["技术深度突出", "经验丰富全面", "潜力型人才"]
        recs = ["建议作为核心技术负责人重点培养", "适合担任项目统筹协调角色", "建议安排轮岗锻炼后再评估"]
        profiles = []
        for i in range(n):
            name = names[i] if i < len(names) else '候选人' + str(i+1)
            profiles.append({
                "name": name,
                "strengths": ["核心技术栈高度匹配", "绩效表现持续优秀", "团队协作能力强"],
                "weaknesses": (["管理经验有待积累", "跨领域经验不足"])[:1 + (i % 2)],
                "comprehensive_score": 88 - i * 5,
                "positioning": positions[i] if i < 3 else positions[2],
                "recommendation": recs[i] if i < 3 else recs[2],
            })
        overall = profiles[0]["name"] + "综合能力最强，适合承担核心技术角色；"
        if n >= 2:
            overall += profiles[1]["name"] + "经验丰富，在项目管理方面有优势。"
        if n <= 2:
            overall += "建议根据岗位侧重点进一步筛选面试。"
        else:
            overall += profiles[2]["name"] + "潜力较大，可安排导师制培养。"
        return _json.dumps({"profiles": profiles, "overall_comparison": overall}, ensure_ascii=False)

    def _mock_tag_response(self, user: str) -> str:
        return """```json
{
  "tags": [
    {"name": "数字化转型", "category": "水面", "confidence": 0.9},
    {"name": "敏捷管理", "category": "水面", "confidence": 0.85},
    {"name": "数据分析", "category": "水面", "confidence": 0.8}
  ],
  "reasoning": "从项目描述中提取了与数字化和敏捷相关的技能标签"
}
```"""

    def _mock_career_response(self, user: str) -> str:
        return """**职业发展分析报告**

**当前状态:** 高级软件工程师 (T7)，技术深度优秀，管理经验待发展。

**优劣势分析:**
- 技术栈深度突出，Python/云原生方向有竞争力
- 近三年绩效持续优秀，具备高潜人才特征
- 管理幅度较小，缺乏带领大团队的经验
- 跨部门项目经历有限

**发展建议:**
1. **短期 (3-6个月):** 参加PMP或敏捷管理认证培训
2. **中期 (6-12个月):** 争取担任项目技术负责人，锻炼管理能力
3. **长期 (1-2年):** 向技术总监或架构师方向发展

**推荐培训课程:**
- 系统架构设计高级课程
- 技术团队管理实践
- 跨部门沟通与协作"""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate mock embeddings using hash-based approach.
        In production, AIHubBackend delegates to the real embedding API.
        Produces 384-dim vectors to match all-MiniLM-L6-v2 dimensionality.
        """
        import hashlib
        TARGET_DIM = 384
        vectors = []
        for text in texts:
            vec = []
            seed = 0
            while len(vec) < TARGET_DIM:
                h = hashlib.sha256(f"{seed}:{text}".encode()).digest()
                for i in range(0, 32, 4):
                    val = int.from_bytes(h[i:i+4], 'big') / (2**32) * 2 - 1
                    vec.append(val)
                    if len(vec) >= TARGET_DIM:
                        break
                seed += 1
            vectors.append(vec[:TARGET_DIM])
        return vectors


class AIHubBackend:
    """Company AI Hub backend (Goertek aihub-api.goertek.com)."""

    def __init__(self, base_url=None, api_key=None, model=None):
        self.base_url = base_url or AIHUB_BASE_URL
        self.api_key = api_key or AIHUB_API_KEY
        self.model = model or AIHUB_MODEL

    def chat(self, messages: list[dict], **kwargs) -> str:
        import httpx
        if not self.api_key:
            raise ValueError("AIHUB_API_KEY not set. Configure in utils/config.py")

        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 2048),
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx
        if not self.api_key:
            raise ValueError("AIHUB_API_KEY not set.")

        resp = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["data"]]


class BailianBackend:
    """Alibaba Bailian (Dashscope) — OpenAI-compatible chat + embeddings."""

    def __init__(self, base_url=None, api_key=None, chat_model=None, embed_model=None):
        self.base_url = base_url or BAILIAN_BASE_URL
        self.api_key = api_key or BAILIAN_API_KEY
        self.chat_model = chat_model or BAILIAN_CHAT_MODEL
        self.embed_model = embed_model or BAILIAN_EMBED_MODEL

    def chat(self, messages: list[dict], **kwargs) -> str:
        import httpx
        if not self.api_key:
            raise ValueError("BAILIAN_API_KEY not set.")

        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.chat_model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 2048),
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx
        from concurrent.futures import ThreadPoolExecutor
        if not self.api_key:
            raise ValueError("BAILIAN_API_KEY not set.")

        # tongyi-embedding-vision-plus: max batch 20, 1152-dim output
        # Uses multimodal embedding endpoint (not compatible-mode)
        EMBED_URL = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"
        BATCH = 20
        batches = [texts[i:i+BATCH] for i in range(0, len(texts), BATCH)]

        def _fetch(batch):
            resp = httpx.post(
                EMBED_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.embed_model,
                    "input": {"contents": [{"text": t} for t in batch]},
                },
                timeout=120,
            )
            resp.raise_for_status()
            return [item["embedding"] for item in resp.json()["output"]["embeddings"]]

        # 8 concurrent requests, batch=20 = 160 records per round
        vectors = []
        with ThreadPoolExecutor(max_workers=8) as pool:
            for result in pool.map(_fetch, batches):
                vectors.extend(result)
        return vectors


def get_llm() -> LLMBackend:
    """Factory: return the configured LLM backend."""
    from utils.config import LLM_BACKEND
    if LLM_BACKEND == "bailian":
        return BailianBackend()
    if LLM_BACKEND == "aihub":
        return AIHubBackend()
    return MockBackend()
