"""Data provider abstraction — decouples data source from application logic.

Architecture:
    TalentStore  ←  DataProvider (abstract)
                       ├── ExcelDataProvider   (MVP: local test Excel file)
                       └── APIDataProvider     (Future: company HRMS REST API)

To switch data source, change ONE line in utils/config.py:
    DATA_PROVIDER = "excel"  →  DATA_PROVIDER = "api"
Then implement APIDataProvider._request().
"""
import pandas as pd
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from utils.config import TEST_DATA_FILE


# ── Employee record is always a flat dict ──
# All providers normalize their output to this format.
EmployeeRecord = dict[str, Any]


class DataProvider(ABC):
    """Abstract data source for employee talent records."""

    @abstractmethod
    def fetch_all(self) -> list[EmployeeRecord]:
        """Return all employee records as a list of dicts."""
        ...

    @abstractmethod
    def fetch_by_id(self, employee_id: str) -> EmployeeRecord | None:
        """Return a single employee record by ID."""
        ...


# ═════════════════════════════════════════════════════════════════
# MVP implementation: read from local Excel file
# ═════════════════════════════════════════════════════════════════

class ExcelDataProvider(DataProvider):
    """Load talent data from local Excel (.xlsx) file."""

    def __init__(self, filepath: Path | None = None):
        self.filepath = filepath or TEST_DATA_FILE
        self._cache: list[EmployeeRecord] | None = None
        self._index: dict[str, EmployeeRecord] | None = None

    def fetch_all(self) -> list[EmployeeRecord]:
        if self._cache is not None:
            return self._cache

        if not self.filepath.exists():
            raise FileNotFoundError(f"Talent data not found: {self.filepath}")

        df = pd.read_excel(self.filepath, engine="openpyxl")

        # Normalize: fill NaN
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].fillna("")
        for col in df.select_dtypes(include="number").columns:
            df[col] = df[col].fillna(0)

        self._cache = df.to_dict(orient="records")
        self._index = {str(r.get("工号", "")): r for r in self._cache}
        return self._cache

    def fetch_by_id(self, employee_id: str) -> EmployeeRecord | None:
        if self._index is None:
            self.fetch_all()
        return self._index.get(employee_id)


# ═════════════════════════════════════════════════════════════════
# FUTURE: company HRMS REST API provider
# ═════════════════════════════════════════════════════════════════

class APIDataProvider(DataProvider):
    """Fetch employee data from company HRMS REST API.

    This is a PLACEHOLDER. Fill in when the API is ready.

    Expected endpoints:
        GET  /api/employees              → list all employees
        GET  /api/employees/{id}         → single employee
        GET  /api/employees/{id}/tags    → employee skill tags
        GET  /api/positions              → position dictionary
    """

    def __init__(self, base_url: str = "", api_key: str = ""):
        self.base_url = base_url
        self.api_key = api_key
        self._cache: list[EmployeeRecord] | None = None
        self._index: dict[str, EmployeeRecord] | None = None

    def _request(self, path: str) -> list[dict]:
        """Send GET request to HRMS API. Placeholder — implement when API is ready."""
        # import httpx
        # resp = httpx.get(
        #     f"{self.base_url}{path}",
        #     headers={"Authorization": f"Bearer {self.api_key}"},
        #     timeout=30,
        # )
        # resp.raise_for_status()
        # return resp.json()
        raise NotImplementedError(
            "HRMS API not connected yet. "
            "Implement _request() in data/provider.py, then set DATA_PROVIDER='api' in config."
        )

    def fetch_all(self) -> list[EmployeeRecord]:
        if self._cache is not None:
            return self._cache
        self._cache = self._request("/api/employees")
        self._index = {str(r.get("工号", "")): r for r in self._cache}
        return self._cache

    def fetch_by_id(self, employee_id: str) -> EmployeeRecord | None:
        if self._index is not None:
            return self._index.get(employee_id)
        records = self._request(f"/api/employees/{employee_id}")
        return records[0] if records else None


# ═════════════════════════════════════════════════════════════════
# Factory
# ═════════════════════════════════════════════════════════════════

def get_provider() -> DataProvider:
    """Factory: return the configured data provider."""
    from utils.config import DATA_PROVIDER
    if DATA_PROVIDER == "api":
        from utils.config import AIHUB_BASE_URL, AIHUB_API_KEY
        return APIDataProvider(base_url=AIHUB_BASE_URL, api_key=AIHUB_API_KEY)
    return ExcelDataProvider()


# ═════════════════════════════════════════════════════════════════
# Utility: build searchable text profile from ANY employee dict
# ═════════════════════════════════════════════════════════════════

# Fields to include in the semantic search profile text.
# These keys must exist in the employee dict (from ANY provider).
PROFILE_TEXT_FIELDS = [
    "岗位", "部门", "职级", "学历", "专业", "技能标签",
    "所有标签", "工作领域", "证书", "外派国家",
]


def build_text_profile(record: EmployeeRecord) -> str:
    """Build a searchable text profile from an employee record dict.

    Used for embedding / semantic search index.
    Provider-agnostic: works with Excel or API data.
    """
    field_labels = {
        "岗位": "岗位", "部门": "部门", "职级": "职级",
        "学历": "学历", "专业": "专业", "技能标签": "技能",
        "所有标签": "标签", "工作领域": "工作领域",
        "证书": "证书", "外派国家": "外派",
    }
    parts = []
    for field in PROFILE_TEXT_FIELDS:
        val = record.get(field, "")
        if val and str(val).strip():
            label = field_labels.get(field, field)
            parts.append(f"{label}:{val}")
    return " ".join(parts)
