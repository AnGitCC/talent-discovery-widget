"""Export utilities: Excel and HTML report generation."""
import pandas as pd
from pathlib import Path
from datetime import datetime
from utils.config import EXPORT_DIR


def ensure_export_dir():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def export_candidates_excel(candidates: list[dict], filename: str | None = None) -> str:
    """Export candidate list to Excel file."""
    ensure_export_dir()
    if filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"talent_export_{ts}.xlsx"
    filepath = EXPORT_DIR / filename

    rows = []
    for c in candidates:
        p = c.get("profile", {})
        rows.append({
            "工号": p.get("工号", ""),
            "姓名": p.get("姓名", ""),
            "性别": p.get("性别", ""),
            "年龄": p.get("年龄", ""),
            "部门": p.get("部门", ""),
            "岗位": p.get("岗位", ""),
            "职级": p.get("职级", ""),
            "学历": p.get("学历", ""),
            "专业": p.get("专业", ""),
            "绩效等级": p.get("绩效等级", ""),
            "技能标签": p.get("技能标签", ""),
            "所有标签": p.get("所有标签", ""),
            "证书": p.get("证书", ""),
            "是否愿意调岗": p.get("是否愿意调岗", ""),
            "匹配等级": c.get("grade", c.get("final", {}).get("grade", "")),
            "匹配分数": c.get("llm_score", c.get("final", {}).get("total_score", "")),
            "匹配理由": c.get("reason", ""),
        })

    df = pd.DataFrame(rows)
    df.to_excel(filepath, index=False, engine="openpyxl")
    return str(filepath)


def export_report_html(report: dict) -> str:
    """Generate an HTML report string from a match report dict."""
    profile = report.get("profile", {})
    dims = report.get("dimensions", {})

    dim_rows = ""
    for name, score in dims.items():
        bar = "█" * (int(score) // 10)
        dim_rows += f"<tr><td>{name}</td><td>{score}</td><td>{bar}</td></tr>"

    strengths = "".join(f"<li>{s}</li>" for s in report.get("strengths", []))
    weaknesses = "".join(f"<li>{w}</li>" for w in report.get("weaknesses", []))
    suggestions = "".join(f"<li>{s}</li>" for s in report.get("development_suggestions", []))

    grade = report.get("match_grade", "B")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>人才匹配报告 - {profile.get('姓名', '')}</title>
<style>
  body {{ font-family: 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
  .grade {{ font-size: 48px; font-weight: bold; margin: 10px 0; }}
  .grade-S {{ color: #f44336; }} .grade-A {{ color: #ff9800; }} .grade-B {{ color: #2196f3; }} .grade-C {{ color: #9e9e9e; }}
  table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
  th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
  th {{ background: #f5f5f5; }}
  .section {{ margin: 24px 0; }}
  h2 {{ border-bottom: 2px solid #43A047; padding-bottom: 8px; }}
</style>
</head>
<body>
<h1>人才匹配分析报告</h1>
<div class="section">
  <h2>基本信息</h2>
  <table>
    <tr><th>姓名</th><td>{profile.get('姓名', '')}</td><th>工号</th><td>{profile.get('工号', '')}</td></tr>
    <tr><th>部门</th><td>{profile.get('部门', '')}</td><th>岗位</th><td>{profile.get('岗位', '')}</td></tr>
    <tr><th>职级</th><td>{profile.get('职级', '')}</td><th>学历</th><td>{profile.get('学历', '')}</td></tr>
    <tr><th>绩效</th><td>{profile.get('绩效等级', '')} ({profile.get('绩效分数', '')}分)</td><th>司龄</th><td>{profile.get('司龄(年)', '')}年</td></tr>
  </table>
</div>
<div class="section">
  <h2>匹配度评估</h2>
  <p class="grade grade-{grade}">{grade}级 — {report.get('match_score', 0)}分</p>
  <table>
    <tr><th>维度</th><th>得分</th><th>可视化</th></tr>
    {dim_rows}
  </table>
</div>
<div class="section">
  <h2>综合分析</h2><p>{report.get('explanation', '暂无分析')}</p>
</div>
<div class="section">
  <h2>优势</h2><ul>{strengths or '<li>暂无数据</li>'}</ul>
</div>
<div class="section">
  <h2>待发展项</h2><ul>{weaknesses or '<li>暂无数据</li>'}</ul>
</div>
<div class="section">
  <h2>发展建议</h2><ul>{suggestions or '<li>暂无数据</li>'}</ul>
</div>
</body>
</html>"""
    return html


def save_report_html(report: dict, filename: str | None = None) -> str:
    """Save report as HTML file, return filepath."""
    ensure_export_dir()
    if filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = report.get("profile", {}).get("姓名", "unknown")
        filename = f"report_{name}_{ts}.html"
    filepath = EXPORT_DIR / filename
    html = export_report_html(report)
    filepath.write_text(html, encoding="utf-8")
    return str(filepath)
