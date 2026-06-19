# AI 人才发现助手 (Talent Discovery Widget)

> 嵌入 HR 门户的 AI 智能人才发现与全景履历 Widget

一键嵌入 `<script>` 标签，即可将智能人才搜索、卡片式候选人展示、多维对比分析、MTP 全景履历等功能集成到任何 HR 系统。

---

## 架构概览

```
浏览器 (Shadow DOM Widget)
  ↕ WebSocket (typed JSON messages)
Starlette Server (backend/server.py, port 8765)
  ↕
3 层匹配引擎: 规则过滤 → 关键词匹配 → LLM 排序（可选）
  ↕
┌─────────────────┬──────────────────┐
│ SiliconFlow API   │   1000 条测试数据   │
│ DeepSeek V4-Pro   │   Excel 161 字段   │
│ (对比分析 + 路由)  │   17 个历史子表    │
└─────────────────┴──────────────────┘
```

### 数据流

1. **启动** → `server.py` 加载 `TalentStore` 从 Excel（999 条主表记录，无向量索引）
2. **用户输入** → WebSocket `{type: "message", text: "..."}`  
3. **路由** → `router.py`（关键词快速匹配 → LLM 兜底意图解析）→ 分发到对应 handler
4. **Handler** → yield 类型化 JSON 消息：`text`, `card`, `report`, `compare`, `profile`, `actions`, `done`, `error`
5. **Widget** → Shadow DOM 渲染：卡片在消息列表内，报告/对比在全屏右侧面板

---

## 核心功能

### 1. 智能人才搜索

- 自然语言输入：「找高级产品经理」「按标签搜索人才」「找数字化转型人才」
- **两层路由**：关键词快速匹配（`router.py::quick_match()`）→ LLM 意图解析
- **三层匹配**：规则过滤（排除 D 级/敏感岗位）→ 关键词加权匹配（岗位、技能、标签、证书等）→ LLM 重排序（可选）
- 关键词匹配权重：`所在职位`=5.0、`技能标签`=4.0、`所有标签`=3.0、`证书`=3.0、`工作领域`=2.5 等
- 返回候选人卡片：头像 + 姓名 + 职级 + 学历 + 匹配分数 + 技能标签

### 2. 候选人卡片

- 头像（按性别自动匹配 91F/64M 池，哈希算法保证同一员工同一头像）
- 评级 badge（S/A/B/C，基于确定性哈希评分 70-100）
- 技能标签 + 人才标签（彩色 chip，64 色调色板按标签名哈希着色）
- 复选框批量选择 → **对比分析**

### 3. MTP 全景履历（人才画像）

参考标准 HR 人才画像设计稿，包含 **25 个信息模块**：

| 模块 | 内容 | 形式 |
|------|------|------|
| 基本信息 | 姓名、工号、性别、年龄、民族、籍贯、政治面貌、婚姻、住址、爱好 | 卡片 |
| 教育经历 | 最高学历、毕业院校、专业、学校类型 | 卡片 |
| 人才标签 | 彩色标签云（人才标签/能力标签/系统标签） | 标签 |
| 人才盘点 | 九宫格矩阵（潜力 × 绩效，含 X/Y 轴标注） | 九宫格 |
| 绩效 | 年度绩效等级 + 分数 | 表格 |
| 综合考评 | 干部年度考评结果 | 表格 |
| 日常过程评价 | 评价场景 + 评语 | 表格 |
| 外部/内部工作履历 | 单位、职位、日期 | 表格 |
| 外派经历 | 外派部门、岗位、地点 | 表格 |
| 培训经历 | 项目名称、机构、结业状态 | 表格 |
| 职级职等经历 | 晋升历史 + 职等折线图 | 表格 + Chart.js |
| 荣誉 & 奖项 | 奖项类型、名称 | 表格 |
| 负面信息 | 处罚类型、原因 | 表格 |
| 亲属关系 | 亲属工号、姓名、所在公司 | 表格 |
| 项目经验 | 项目类型、等级、角色 | 表格 |
| 领域经验 | 各领域年限分布 | Chart.js 柱状图 |
| 海外/客户/整机零件经验 | 年限分布 | Chart.js 条形图 |
| 干部通用能力 | 变革创新力/沟通影响力/规划执行力/组织发展力 | Chart.js 雷达图 |
| MTP 专业能力 | 商务/成本控制/项目管理/研发/工程 | Chart.js 折线图 |
| 企业精神/价值观/干部品格 | 三个五维雷达图 | Chart.js 雷达图 |
| 管理技能 | 计划/组织/领导/控制 + 总分 | Chart.js 折线图 |
| 语言能力 | 语种、熟练程度、证书 | 表格 |
| 专利/论文/专著/标准 | 学术产出 | 表格 |
| 管理个性 | Big Five（外向性/亲和性/尽责性/稳定性/开放性）| Chart.js 柱状图 |
| 潜力 & 商业推理 | 等级 + 维度评分 | Chart.js 柱状图 |
| 个人评价 & 职业规划 | 自评文字 | 文本 |

### 4. 候选人对比分析

- **Phase 1**（即时，零 AI）：对比表格 — 头像、评级、评分、雷达图、部门/岗位/职级/学历/绩效/技能
- **Phase 2**（流式 AI）：SiliconFlow DeepSeek-V4-Pro 逐人分析 — 定位、优劣势、任用建议、综合得分、综合结论

### 5. 其他功能

- **标签管理**：授予/移除标签
- **导出 Excel**：候选人列表一键下载
- **数据缓存**：report/compare/profile 以 session 维度缓存，避免重复计算
- **头像池**：200+ AI 生成的真实亚洲人照片头像（91 女 + 64 男）

---

## 数据模型

### 主表（`test_talent_data_1000.xlsx` — 999 条记录）

- **161 列**，包含：
  - **基本信息**：姓名、性别、年龄、国籍、籍贯、民族、政治面貌、婚姻状况等
  - **组织信息**：所在职位、职级、职等、序列、司龄、工作上级、管理幅度等
  - **学历背景**：最高学历、毕业院校、专业、学校类型（含全日制、本科、硕士、博士）
  - **人才标签**：关键人才、国际化人才、Hipo人才、XPM领域、GPS角色、G-Plan 等
  - **能力维度**（0-5 或 0-10 评分）：
    - 干部通用能力：变革创新力、沟通影响力、规划执行力、组织发展力
    - MTP 专业能力：商务能力、成本控制、项目管理、研发能力、工程能力
    - 企业精神：艰苦奋斗、追求卓越、实事求是、创新进取、合作共赢
    - 价值观：客户导向、质量优先、合规经营、社会责任、员工发展
    - 干部精神品格：担当、廉洁、正直、奉献、公正
    - 管理技能：计划、组织、领导、控制
    - 管理个性（Big Five）：外向性、亲和性、尽责性、情绪稳定性、开放性
    - 潜力 + 商业综合推理
  - **人才盘点**：九宫格坐标（潜力 X × 绩效 Y）+ 年度

### 历史子表（17 个 Sheet — 可按需加载）

| Sheet | 记录数 | 字段 |
|-------|--------|------|
| 历史_工作业绩 | 4,593 | 年度、绩效等级、绩效分数 |
| 历史_晋升履历 | 2,894 | 晋升日期、原/新职级、职等、停等时间 |
| 历史_项目经验 | 4,440 | 开始/结束日期、项目名称、等级、类别、角色 |
| 历史_培训经历 | 1,283 | 培训项目、机构、结业状态 |
| 历史_奖惩信息 | 374 | 奖惩日期、类型、原因 |
| 历史_导师经历 | 495 | 导师类型、学员 |
| 历史_干部年度考评 | 2,940 | 年度、考评结果、评价记录 |
| 历史_地域工作经历 | 492 | 国家、城市、公司、类型 |
| 历史_外部工作履历 | 515 | 单位、职位 |
| 历史_内部工作履历 | 1,492 | 主兼岗、部门、岗位 |
| 历史_外派经历 | 130 | 外派部门、岗位、地点 |
| 历史_亲属关系 | 184 | 亲属类型、工号、姓名、公司 |
| 历史_荣誉称号 | 1,183 | 奖项类型、名称 |
| 历史_日常过程评价 | 1,549 | 评价场景、评语 |
| 历史_专利 | 29 | 专利类型、名称、专利号 |
| 历史_论文 | 300 | 论文名称、排名、刊物 |
| 历史_专著 | 61 | 专著名称、出版社 |

---

## 技术栈

### 后端
- **Python 3.11+** · Starlette（异步 Web + WebSocket）· uvicorn
- **pandas** + openpyxl — Excel 数据源
- **numpy** — 向量相似度计算（可选）
- **httpx** — 异步 API 调用
- **SiliconFlow**（硅基流动）— DeepSeek-V4-Pro（对比分析流式）/ DeepSeek-V4-Flash（路由意图）
- **阿里云百炼**（Bailian）/ **Goertek AI Hub** — 备用 LLM

### 前端
- **零依赖** — 单文件 `talent-widget.js`（~300 行），无构建步骤
- **Shadow DOM** — 完全样式隔离
- **Chart.js 4.x** — MTP 全景履历图表（雷达图、折线图、柱状图），CDN 按需加载
- **WebSocket** — 实时双向通信，自动重连（指数退避，最长 30s）

### 头像生成
- **IvanVision MCP**（Goertek AI Hub Flux）— 200 张真实感亚洲人照片头像

---

## 开发

```bash
# 克隆项目
git clone https://github.com/AnGitCC/talent-discovery-widget.git
cd talent-discovery-widget

# 安装依赖
pip install -r requirements.txt

# 启动本地服务
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8765
```

### 本地测试入口

| URL | 说明 |
|-----|------|
| `http://localhost:8765/demo` | 模拟歌尔 HR 门户首页（含 Widget 嵌入） |
| `http://localhost:8765/mtp/G000002` | 直接查看员工全景履历页面 |
| `http://localhost:8765/api/health` | 健康检查 |
| `http://localhost:8765/api/debug` | 调试状态（记录数、数据源路径） |

### 数据源切换

在 `backend/utils/config.py` 中修改：

```python
DATA_PROVIDER = "excel"   # "excel" | "api"
LLM_BACKEND = "siliconflow"  # "siliconflow" | "bailian" | "aihub" | "mock"
LLM_BACKEND = "mock"         # 开发模式：零 API 调用
```

### API 密钥

通过环境变量注入：
```bash
export SILICONFLOW_API_KEY="sk-xxx"   # 硅基流动
export BAILIAN_API_KEY="xxx"           # 阿里云百炼
```

---

## WebSocket 消息协议

所有消息为 JSON，含 `type` 字段：

| type | 方向 | 说明 |
|------|------|------|
| `message` | Client→Server | 用户聊天文本 |
| `action` | Client→Server | 按钮点击（compare/report/export）+ 附带 ids |
| `text` | Server→Client | Markdown 文本气泡 |
| `card` | Server→Client | 候选人卡片 |
| `report` | Server→Client | MTP 全景履历（全屏右侧面板） |
| `compare` | Server→Client | 多候选人对比表 |
| `profile` | Server→Client | Iceberg 人才画像 |
| `actions` | Server→Client | 操作按钮行 |
| `done` | Server→Client | 响应流结束 |
| `error` | Server→Client | 错误信息 |

---

## 关键设计决策

- **Starlette 而非 FastAPI** — 更轻量，直接 WebSocket + HTTP 路由
- **确定性评分** — `hash(工号)` → 70-100，同一员工在所有视图（卡片/报告/对比）中评分一致
- **零 AI 成本的全景履历** — 全部数据来自 Excel 预计算，无需 API 调用
- **AI 仅在对比分析时调用** — 唯一一次 LLM 调用用于生成逐人分析文本和综合结论
- **关键词匹配为主** — Layer 2 无需 API，快速评分
- **LLM 排序跳过** — Layer 3 默认关闭（为速度和成本）
- **Shadow DOM 样式隔离** — Widget 嵌入任意页面不会污染宿主样式

---

## 部署

### 生产环境

- **阿里云 ECS** · 宝塔面板 · Nginx 反向代理
- **域名**：`talent.atgoertek.xyz`
- **systemd 服务**：`/etc/systemd/system/talent-widget.service`
- **自动部署**：crontab 每 1 分钟 `git pull → systemctl restart`
- **CI/CD**：GitHub Actions → Gitee 镜像 → 服务器拉取

### Nginx 配置要点

```nginx
location / { proxy_pass http://127.0.0.1:8765; }
location /ws/ { proxy_pass http://127.0.0.1:8765/ws/; ... Upgrade headers ... }
location /widget { alias /www/wwwroot/tw/widget; }
```

---

## 项目结构

```
talent-discover-widget/
├── backend/                    # Python 后端
│   ├── server.py               # Starlette 入口：HTTP 路由 + WebSocket
│   ├── router.py               # 意图路由：关键词 + LLM 兜底
│   ├── message_builder.py      # 消息分发中心：意图→流式消息
│   ├── views.py                # MTP 全景履历服务端渲染
│   ├── ws_manager.py           # 会话管理（内存缓存，1h 过期）
│   ├── agents/                 # 业务代理
│   │   ├── match.py            # MatchAgent：3 层匹配流水线
│   │   ├── compare.py          # CompareAgent：对比分析
│   │   ├── profile.py          # ProfileAgent：Iceberg 画像
│   │   ├── search.py           # SearchAgent：NL→结构化条件
│   │   ├── report.py           # ReportAgent：详细报告
│   │   ├── career.py           # CareerAgent：职业发展
│   │   └── tag.py              # TagAgent：标签管理
│   ├── engine/                 # 匹配引擎
│   │   ├── rule_filter.py      # Layer 1：规则过滤
│   │   ├── keyword_match.py    # Layer 2：关键词加权匹配
│   │   ├── vector_match.py     # Layer 2b：余弦相似度
│   │   └── llm_rank.py         # Layer 3：LLM 重排序
│   ├── data/                   # 数据层
│   │   ├── talent_store.py     # 单例数据存储 + in-memory 索引
│   │   ├── provider.py         # DataProvider 抽象（Excel/API）
│   │   └── position_dict.json  # 岗位字典
│   ├── llm/                    # LLM 后端
│   │   ├── backend.py          # Mock/SiliconFlow/Bailian/AIHub
│   │   └── prompts.py          # 系统提示词
│   └── utils/                  # 工具
│       ├── config.py           # 全局配置（路径、API 密钥、模型）
│       ├── export.py           # Excel/HTML 导出
│       └── radar.py            # Plotly 雷达图（未使用）
├── widget/                     # 前端 Widget
│   ├── talent-widget.js        # 主文件：Shadow DOM + WebSocket 客户端
│   ├── talent-widget.css       # 分离 CSS（未使用，CSS 内联在 JS 中）
│   ├── avatars/                # 200 张 AI 生成头像
│   └── avatar.png              # Widget 图标
├── demo/                       # 演示页面
│   ├── demo-hr-portal.html     # 模拟歌尔 HR 门户
│   ├── mtp-v3.html             # MTP 全景履历模板
│   └── ...
├── scripts/                    # 数据生成 + 构建脚本
│   ├── gen_1000_v3.py          # 1000 条测试数据生成器
│   ├── gen_avatar_prompts.py   # 头像生成提示词
│   ├── enrich_mtp_profile.py   # 数据富化（MTP 维度 + 历史子表）
│   └── ...
├── test_talent_data_1000.xlsx  # 1000 条测试数据（999 员工 × 161 列）
├── test_talent_data_400_cn.xlsx # 旧版 400 条数据（已弃用）
├── requirements.txt
├── Dockerfile
├── deploy.sh
└── CLAUDE.md
```

---

## License

Internal use — Goertek HR Department

---

*Built with Claude Code · Last updated 2026-06-20*
