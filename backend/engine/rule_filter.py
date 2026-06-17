"""First layer of matching engine: rule-based hard filtering."""
import pandas as pd
from typing import Any


def apply_hard_filters(
    df: pd.DataFrame,
    level_min: int | None = None,
    level_max: int | None = None,
    education_required: list[str] | None = None,
    exclude_departments: list[str] | None = None,
    performance_min: str | None = None,
    exclude_employee_ids: list[str] | None = None,
    min_tenure: int | None = None,
) -> pd.DataFrame:
    """Apply hard-filter rules. Returns filtered DataFrame."""

    result = df.copy()

    # Exclude specific employees
    if exclude_employee_ids:
        result = result[~result["工号"].isin(exclude_employee_ids)]

    # Exclude sensitive positions
    if "敏感岗位" in result.columns:
        result = result[result["敏感岗位"] != "是"]

    # Exclude poor performers (D grade)
    if "绩效等级" in result.columns:
        result = result[result["绩效等级"] != "D"]

    # Level range
    if level_min is not None and "职等" in result.columns:
        result = result[result["职等"] >= level_min]
    if level_max is not None and "职等" in result.columns:
        result = result[result["职等"] <= level_max]

    # Education requirement
    if education_required and "学历" in result.columns:
        result = result[result["学历"].isin(education_required)]

    # Exclude departments
    if exclude_departments and "部门" in result.columns:
        result = result[~result["部门"].isin(exclude_departments)]

    # Performance minimum
    if performance_min and "绩效等级" in result.columns:
        perf_order = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
        min_val = perf_order.get(performance_min, 0)
        result = result[result["绩效等级"].apply(lambda x: perf_order.get(str(x), 0) >= min_val)]

    # Minimum tenure
    if min_tenure is not None and "司龄(年)" in result.columns:
        result = result[result["司龄(年)"] >= min_tenure]

    return result


def parse_search_conditions(conditions: list[dict]) -> dict[str, Any]:
    """Convert LLM-parsed search conditions into filter params."""
    params = {}

    for cond in conditions:
        field = cond.get("field", "")
        op = cond.get("op", "eq")
        value = cond.get("value")

        if field == "职等" and op == "gte":
            params["level_min"] = int(value)
        elif field == "职等" and op == "lte":
            params["level_max"] = int(value)
        elif field == "学历" and op == "in":
            params["education_required"] = value
        elif field == "绩效等级" and op == "gte":
            params["performance_min"] = value
        elif field == "司龄(年)" and op == "gte":
            params["min_tenure"] = int(value)

    return params


def build_condition_dataframe_queries(
    df: pd.DataFrame,
    conditions: list[dict],
) -> pd.DataFrame:
    """Apply structured conditions as DataFrame queries directly.

    This is the primary filter path for the Search Agent:
    takes LLM-parsed conditions, converts to pandas boolean masks,
    returns the filtered DataFrame.
    """
    result = df.copy()

    for cond in conditions:
        field = cond.get("field", "")
        op = cond.get("op", "eq")
        value = cond.get("value")

        if field not in result.columns:
            continue

        try:
            if op == "eq":
                result = result[result[field] == value]
            elif op == "in":
                result = result[result[field].isin(value)]
            elif op == "gte":
                result = result[result[field] >= value]
            elif op == "lte":
                result = result[result[field] <= value]
            elif op == "contains":
                result = result[result[field].astype(str).str.contains(str(value), na=False)]
            elif op == "neq":
                result = result[result[field] != value]
        except Exception:
            continue

    return result
