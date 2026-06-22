# AI 人才发现助手 — 项目全文档

> **一句话说清楚：** 这是嵌入歌尔 HR 门户网站里的一个智能小工具。HR 同事在搜索框里打字（比如"帮我找高级产品经理"），系统自动从人才库中找出匹配的人，展示带照片的卡片、一键对比、查看每个人 25 个维度的全景履历。

---

## 目录

- [一、这个工具能做什么](#一这个工具能做什么)
- [二、怎么用 — 页面导航](#二怎么用--页面导航)
- [三、数据从哪里来](#三数据从哪里来)
- [四、系统是怎么工作的](#四系统是怎么工作的)
- [五、项目里每个文件夹干什么的](#五项目里每个文件夹干什么的)
- [六、怎么在本地跑起来](#六怎么在本地跑起来)
- [七、怎么部署到服务器](#七怎么部署到服务器)
- [八、技术细节 — 写给开发者](#八技术细节--写给开发者)
- [九、常见问题](#九常见问题)

---

## 一、这个工具能做什么

### 1. 智能人才搜索

**用大白话找人。** 不需要记住工号、岗位编码或者复杂的筛选条件，直接在对话框里输入日常用语就行。

> 比如：「找高级产品经理」「帮我搜索数字化转型方面的人才」「谁做过海外项目」「有没有会 Python 的」

系统理解你的意图后，自动在 1000 人的数据库中搜索，几秒钟内返回匹配的候选人。

### 2. 候选人卡片

搜索结果以卡片形式展示，每张卡片显示：

| 信息 | 说明 |
|------|------|
| 头像 | 200 张 AI 生成的真实感亚洲人脸照片，根据工号和性别自动分配，同一个人的头像永远不变 |
| 姓名 + 评级 | S/A/B/C 四档，基于综合能力评分 |
| 职级 + 学历 | 当前岗位层级和最高学位 |
| 匹配分数 | 系统打分，帮你判断这个人和你要找的岗位有多匹配 |
| 技能标签 + 人才标签 | 彩色小标记，一眼看出这个人有哪些能力和身份特征 |

标签颜色共有 64 种，按标签名称自动分配，确保不同标签的颜色区分明显。

卡上有勾选框，勾选两个人以上就可以对比。

### 3. MTP 人才全景画像

**这是最核心的功能**，参考歌尔标准 HR 人才画像设计。点击某个人的详细档案后，一个页面展示 **25 个信息模块**：

#### 📋 基础信息
- **基本信息**：姓名、工号、性别、年龄、民族、籍贯、政治面貌、婚姻状况、住址、爱好
- **教育经历**：最高学历、毕业院校、专业、学校类型（985/211/海外等分类）
- **人才标签**：彩色标签云 — 人才标签、能力标签、系统标签三类

#### 📊 图表分析
- **人才盘点九宫格**：潜力（X 轴）× 绩效（Y 轴），员工当前所在格用绿色高亮
- **领域经验**：各工作领域年限分布（柱状图）
- **海外/客户/整机零件经验**：年限对比（条形图）
- **干部通用能力**：变革创新力、沟通影响力、规划执行力、组织发展力（雷达图）
- **MTP 专业能力**：商务、成本控制、项目管理、研发、工程（折线图）
- **企业精神、价值观、干部品格**：各五个维度的雷达图
- **管理技能**：计划、组织、领导、控制 + 总分（折线图）
- **管理个性（Big Five）**：外向性、亲和性、尽责性、情绪稳定性、开放性（柱状图）
- **潜力 & 商业推理**：等级 + 维度评分（柱状图）

#### 📜 历史履历
- **绩效历史**：历年绩效等级 + 分数一览表
- **晋升履历**：每次晋升日期、原职级→新职级、职等变化
- **内部/外部工作履历**：单位、岗位、时间
- **外派经历**：外派部门、岗位、地点
- **培训经历**：项目名称、培训机构、结业状态
- **项目经验**：项目名称、类别、等级、担任角色
- **荣誉 & 奖项**：奖项类型、名称、获得时间
- **奖惩信息**：处罚类型、原因、日期
- **干部年度考评**：历次考评结果、综合评价
- **职称/证书/语言能力/专利/论文/专著/标准**：学术和资质产出
- **亲属关系**：亲属工号、姓名、所在公司
- **个人评价 & 职业规划**：自评文字

#### 🔘 操作按钮
- **📤 分享报告**：一键复制当前页面链接，发给同事直接在浏览器打开
- **📥 下载报告**：自动生成 A4 横版 PDF，保留所有图表和格式，可打印或存档

### 4. 候选人对比分析

勾选 2 人或更多 → 点击「对比选中」→ 即刻看到对比结果：

- **Phase 1 — 瞬间出结果（不调用 AI）**：对比表格 + 雷达图，展示每个人的头像、评级、评分、部门、岗位、职级、学历、绩效、技能
- **Phase 2 — AI 深度分析（流式加载）**：针对每个人，AI 逐行输出：
  - 定位（这个人在对比组里是什么角色）
  - 优势（3-4 条）
  - 不足（1-2 条）
  - 任用建议
  - 综合得分（0-100）
  - 综合结论（2-4 句话的总体对比）

### 5. 导出 Excel

搜索结果可一键导出为 Excel 文件（.xlsx 格式），包含所有候选人的关键信息。

### 6. 标签管理

支持给候选人授予或移除标签，标签变更即时保存。

---

## 二、怎么用 — 页面导航

### 在线地址

```
https://talent.atgoertek.xyz
```

### 页面清单

| 路径 | 说明 | 谁用 |
|------|------|------|
| 首页 `/` | 模拟歌尔 HR 门户，绿色 AI 按钮在页面右下角 | HR 日常使用 |
| `/demo` | 同首页，HR 门户演示页 | 演示/测试 |
| `/mtp/{工号}` | 独立人才全景画像页，如 `/mtp/G000002` 查看夏慧的画像 | 直接分享给他人 |
| `/api/health` | 系统健康检查 | 运维 |
| `/api/debug` | 调试状态（记录数、数据文件路径） | 开发调试 |

### 底部 AI 助手按钮

- **绿色浮动按钮**（页面右下角）：点击展开聊天面板
- **⛶ 全屏按钮**：聊天面板占据屏幕 1/3，右侧显示报告/对比
- **输入方式**：打字 + 回车发送

---

## 三、数据从哪里来

### 数据源

目前使用 Excel 文件作为数据源（之后可以切换为 HRMS 系统 API）。项目包含两套数据：

| 文件 | 规模 | 说明 |
|------|------|------|
| `test_talent_data_1000.xlsx` | 999 条员工记录 | **当前主力数据** |
| `test_talent_data_10000_cn.xlsx` | 10,000 条 | 大规模测试用 |
| `test_talent_data_400_cn.xlsx` | 400 条 | 旧版（已弃用） |

### Excel 主表结构（1000 条版本）

一个主 Sheet（「主表」）+ 17 个历史子 Sheet。

**主表** 每行是一个员工，包含 161 列信息：

- **基本信息**（约 15 列）：姓名、性别、年龄、国籍、籍贯、民族、政治面貌、婚姻状况、家庭住址、爱好等
- **组织信息**（约 10 列）：工号、所在职位、职级、职等、序列、司龄、工作上级、管理幅度等
- **学历背景**（约 5 列）：最高学历、毕业院校、专业、学校类型、入学/毕业时间
- **人才标签**（约 25 列）：关键人才、国际化人才、Hipo 人才、XPM 领域、GPS 角色、G-Plan、是否工艺师、数字化人才等
- **能力维度评分**（约 50 列，0-5 或 0-10 分制）：
  - 干部通用能力 4 项
  - MTP 专业能力 5 项
  - 企业精神 5 项
  - 价值观 5 项
  - 干部精神品格 5 项
  - 管理技能 4 项
  - 管理个性 5 项（Big Five）
  - 潜力 + 商业综合推理
- **绩效 + 九宫格**（约 5 列）：绩效等级、总积分、九宫格坐标 X/Y、盘点年份

### 历史子表（17 个 Sheet — 以"历史_"前缀命名）

这些 Sheet 记录的是每个员工**随时间变化的历史数据**。比如夏慧可能在过去 5 年里有 3 条绩效记录、2 次晋升、多个培训经历。

| Sheet 名称 | 内容 | 大概多少条 |
|-----------|------|-----------|
| 历史_工作业绩 | 每年绩效等级和分数 | ~4,600 |
| 历史_晋升履历 | 每次晋升的时间、新旧职级职等 | ~2,900 |
| 历史_项目经验 | 参与过的项目名称、等级、角色 | ~4,400 |
| 历史_培训经历 | 培训课程、机构、结业状态 | ~1,300 |
| 历史_奖惩信息 | 奖励/处罚的日期、类型、原因 | ~370 |
| 历史_干部年度考评 | 历年考评结果和评价 | ~2,900 |
| 历史_地域工作经历 | 在各国家/城市的工作经历 | ~490 |
| 历史_外部工作履历 | 以前的单位和职位 | ~510 |
| 历史_内部工作履历 | 公司内部调岗记录 | ~1,500 |
| 历史_外派经历 | 外派部门、岗位、地点 | ~130 |
| 历史_亲属关系 | 亲属在公司的情况 | ~180 |
| 历史_荣誉称号 | 获得的奖项名称和类型 | ~1,200 |
| 历史_日常过程评价 | 日常工作评语 | ~1,500 |
| 历史_导师经历 | 担任导师/学员的记录 | ~490 |
| 历史_专利 | 专利列表 | ~29 |
| 历史_论文 | 发表论文 | ~300 |
| 历史_专著 | 出版专著 | ~61 |

> **注意**：「历史_导师经历」这个 Sheet 的数据不在 MTP 画像中展示（画像模板中没有对应模块）。但索引时仍然读取，后续如果需要可以启用。

### 历史数据是怎么加载的

这是本项目一个关键的设计——**不是每次打开画像才去 Excel 里翻数据**，那样太慢了。

启动服务时，系统做以下事情：

1. **一次性读取** 17 个历史 Sheet（用 pandas 批量读，约 5 秒）
2. **按员工 ID 分组** → 建立 `{工号 → {模块名 → [记录列表]}}` 的索引
3. **列名映射**：Excel 里的列名和 MTP 模板要求的名字可能不同，自动翻译（如 `年度`→`绩效周期`、`奖惩类型`→`处罚类型`、`项目类别`→`项目类型`）
4. **保存为 .pkl 文件**（pickle 格式，约 1MB），之后启动加载只要 **0.5 秒**
5. 查询某个员工的历史数据 → **O(1) 字典查询**（瞬间完成，不需要任何循环）

这个逻辑在 `backend/data/history_cache.py` 里（175 行），是解决"MTP 画像历史数据全是空白"的核心模块。

---

## 四、系统是怎么工作的

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户浏览器                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │  嵌入 HR 门户的 Widget（Shadow DOM 隔离样式）       │   │
│  │  · 聊天面板  · 候选人卡片  · 对比报告  · MTP 画像  │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │ WebSocket（实时双向通信）            │
└─────────────────────┼───────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────┘
│              Python 后端 (Starlette + uvicorn)            │
│  端口 8765                                               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 意图路由  │→│ 消息分发中心  │→│ 业务处理器（Agent）│   │
│  │ router.py│  │msg_builder.py│  │ match/compare/…  │   │
│  └──────────┘  └──────────────┘  └──────────────────┘   │
│                                       ↓                   │
│  ┌───────────────────────────────────────────────────┐   │
│  │  三层匹配引擎                                       │   │
│  │  Layer 1: 规则过滤 (rule_filter.py)                │   │
│  │  Layer 2: 关键词匹配 (keyword_match.py)  ← 主力    │   │
│  │  Layer 3: LLM 排序 (llm_rank.py)     ← 可选       │   │
│  └───────────────────────────────────────────────────┘   │
│                                       ↓                   │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 数据层   │  │ LLM 后端     │  │ 历史缓存         │   │
│  │provider  │  │ siliconflow/ │  │ history_cache    │   │
│  │talent_   │  │ bailian/     │  │ (启动时预建索引) │   │
│  │store     │  │ aihub/mock   │  │                  │   │
│  └──────────┘  └──────────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### 一次搜索的完整流程

举例：用户在聊天框输入「帮我找高级产品经理」

1. **接收消息** → WebSocket 收到 `{"type":"message", "text":"帮我找高级产品经理"}`
2. **意图识别** →
   - 先走快速关键词匹配（`router.py::quick_match()`，零延迟）：发现「找」→ 判定为"岗找人"意图，提取「高级产品经理」作为搜索词
   - 如果快速匹配没命中，调用 LLM（AI 模型）做更智能的意图理解（1-2 秒）
3. **三层匹配**（`agents/match.py`）：
   - **Layer 1 — 规则过滤**：排除绩效 D 级、标记为敏感岗位的人
   - **Layer 2 — 关键词匹配**：搜索每个人 11 个字段（岗位、技能标签、证书…），按权重打分、排序 → 主力手段，不花钱不耗时
   - **Layer 3 — LLM 重排序**：用 AI 重新排序（默认关闭，省成本）
4. **生成消息流** → 后端一条条发送 JSON 消息给前端：
   ```
   text: "找到了 8 位匹配候选人："
   card: {姓名:"张三", 头像:"...", 分数:82, ...}
   card: {姓名:"李四", ...}
   ...
   actions: ["对比选中", "导出Excel"]
   done: (结束)
   ```
5. **前端渲染** → Widget 逐条渲染：文字气泡 → 卡片 → 按钮

### AI 在哪些地方用了

| 功能 | 用 AI 了没 | 说明 |
|------|-----------|------|
| **人才搜索** | ⚡ 关键词为主（不用 AI） | 关键词匹配就够了，Layer 3 AI 排序默认关闭 |
| **意图路由** | 🔶 快速匹配优先 | 先用关键词判断，识别不了才用 AI 兜底 |
| **MTP 全景画像** | ❌ 完全不用 AI | 所有数据都从 Excel 预计算，零成本 |
| **候选人对比分析** | ✅ AI 深度分析 | 唯一调用 AI 的地方 — 逐人优劣势、定位、任用建议 |
| **分享/下载** | ❌ 不用 AI | 纯前端浏览器操作 |

### 头像系统

- 200 张 AI 生成的真实感亚洲人脸照片（91 张女性 + 64 张男性）
- 存放在 `widget/avatars/` 文件夹
- 命令规则：`avatar-f-001.png`（女001）到 `avatar-f-091.png`、`avatar-m-001.png`（男001）到 `avatar-m-064.png`
- **同一个人的头像永远不变**：用员工工号做哈希 → 按性别选对应池 → 取模 → 始终命中同一张图
- 头像生成用的是 IvanVision MCP（公司内部 Goertek AI Hub Flux 模型）

### 评分系统

- **确定性评分**：所有页面（卡片 / 报告 / 对比）上同一个人的评分完全一致
- 评分算法：`hash(MD5(工号))` → 映射到 70-100 区间
- **这不是真正的匹配分数**，而是基于工号的确定性哈希值。等接入真实 HR 系统后，可替换为实际的能力评估分数

### 打印和 PDF 下载

这是一个容易出问题的环节，本项目的解决方案：

1. **不是直接调用 `window.print()`**——那样浏览器会按默认设置打印，导致格式全乱
2. **实际流程**：
   - 克隆整个页面的 DOM（文档对象模型）
   - **在克隆之前**，把所有的 Canvas 图表（Chart.js 画的雷达图、柱状图等）转成图片（`toDataURL`）
   - 克隆后的 Canvas 标签替换为 `<img>` 标签（因为克隆会丢失 Canvas 像素数据）
   - 移除操作按钮（分享/下载按钮不需要出现在 PDF 里）
   - 修正头像图片路径（相对路径 → 绝对路径）
   - 新建一个浏览器窗口，写入完整 HTML + CSS
   - 延迟 0.9 秒（等浏览器渲染完），然后调用 `print()`
3. **打印格式**：A4 横版（`@page{size:A4 landscape}`），边距 8mm
4. **CSS 关键点**：`@page` 规则必须写在 `@media print{}` **外面**——如果写在里面，Chrome 的 PDF 生成器在有些时候会无视它，导致打印出来是竖版而且格式丢失

---

## 五、项目里每个文件夹干什么的

### 完整文件树

```
talent-discover-widget/            ← 项目根目录
│
├── README.md                      ← 📖 本文档
├── README.backup.md               ← 📦 旧版 README 备份
├── CLAUDE.md                      ← 🤖 给 AI 助手的项目说明书
├── requirements.txt               ← 📦 Python 依赖包清单
├── Dockerfile                     ← 🐳 Docker 容器配置
├── deploy.sh                      ← 🚀 阿里云一键部署脚本
├── fly.toml                       ← ☁️ Fly.io 容器云配置
├── render.yaml                    ← ☁️ Render.com 云部署配置
├── .gitignore                     ← 告诉 git 哪些文件不要上传
│
├── test_talent_data_1000.xlsx     ← 📊 主力数据：999 员工 × 161 列 + 17 历史子表
├── test_talent_data_10000_cn.xlsx ← 📊 大规模测试数据：10000 条
├── test_talent_data_400_cn.xlsx   ← 📊 旧版 400 条数据（不再使用）
├── 整合版V2.xlsx                   ← 📊 原始整合数据源
├── .history_cache.pkl             ← 💾 历史数据缓存文件（~1MB，自动生成）
│
├── backend/                       ← 🔧 Python 后端 — 所有服务器端的逻辑
│   ├── server.py                  ← 🏠 主入口：启动 HTTP 服务 + WebSocket，挂载所有路由
│   ├── router.py                  ← 🧭 意图路由器：理解用户说的是什么（搜索/对比/报告…）
│   ├── message_builder.py         ← 📨 消息分发中心：把意图转成具体操作，逐个发送消息给前端
│   ├── views.py                   ← 🖼️ MTP 画像页面渲染器：读取模板 + 注入数据 → 完整 HTML 页面
│   ├── ws_manager.py              ← 🔌 WebSocket 会话管理：记住每个人当前在做什么
│   │
│   ├── agents/                    ← 🎯 业务代理 — 每个功能一个 Agent
│   │   ├── base.py                ← 基类（定义了 Agent 的基本结构）
│   │   ├── match.py               ← 匹配引擎：执行三层匹配（规则→关键词→LLM）
│   │   ├── compare.py             ← 对比分析：（存在但直接调用 LLM，绕过了这个文件）
│   │   ├── profile.py             ← Iceberg 画像
│   │   ├── report.py              ← 详细报告
│   │   ├── search.py              ← 自然语言转结构化搜索条件
│   │   ├── career.py              ← 职业发展分析
│   │   └── tag.py                 ← 标签管理
│   │
│   ├── engine/                    ← ⚙️ 匹配引擎 — 搜索的底层实现
│   │   ├── rule_filter.py         ← Layer 1：硬规则过滤（排除 D 级/敏感岗位）
│   │   ├── keyword_match.py       ← Layer 2：关键词加权匹配（主力，11 个字段加权打分）
│   │   ├── vector_match.py        ← Layer 2b：向量余弦相似度（备选方案）
│   │   └── llm_rank.py            ← Layer 3：LLM 智能重排序（默认禁用）
│   │
│   ├── data/                      ← 📂 数据层 — 读 Excel、查员工、历史缓存
│   │   ├── provider.py            ← 数据源抽象层（Excel 读 / API 调，统一接口）
│   │   ├── talent_store.py        ← 人才数据存储（单例模式，全局唯一）
│   │   ├── history_cache.py       ← ⭐ 历史数据预建索引（核心模块，详见第四章）
│   │   └── position_dict.json     ← 岗位字典
│   │
│   ├── llm/                       ← 🧠 AI 模型后端 — 对接各种大语言模型服务
│   │   ├── backend.py             ← LLM 工厂：Mock / SiliconFlow / Bailian / AIHub 四种后端
│   │   └── prompts.py             ← 提示词（告诉 AI 怎么回答问题）
│   │
│   └── utils/                     ← 🛠️ 工具包
│       ├── config.py              ← 全局配置：数据路径、API 密钥、模型选择、后端切换
│       ├── export.py              ← Excel 导出
│       ├── radar.py               ← Plotly 雷达图（未使用，保留备选）
│       └── theme.css              ← Streamlit UI 主题样式
│
├── widget/                        ← 🎨 前端 Widget — 浏览器里运行的部分
│   ├── talent-widget.js           ← ⭐ 核心文件：Shadow DOM + WebSocket 客户端 + 所有 UI 渲染
│   ├── talent-widget.css          ← 分离的样式文件（未使用，CSS 都内联在 JS 里了）
│   ├── avatar.png                 ← Widget 图标
│   ├── avatar_base64.txt          ← 头像 base64 编码文本
│   ├── avatar_b64.txt             ← 头像 base64 编码文本（另一版本）
│   ├── talent-widget-broken.js    ← 损坏版本的备份
│   └── avatars/                   ← 200 张 AI 生成头像（avatar-f-001 ~ avatar-m-064）
│
├── demo/                          ← 🎭 演示页面 — 各种测试和展示用的 HTML
│   ├── demo-hr-portal.html        ← ⭐ HR 门户模拟首页（主要演示页）
│   ├── mtp-v3.html                ← ⭐ MTP 全景画像 HTML 模板（服务端注入数据用）
│   ├── mtp-v3-dynamic.html        ← MTP 画像动态渲染版
│   ├── mtp-v3-template.html       ← 纯净模板（无数据注入）
│   ├── mtp-profile.html           ← 旧版 MTP 画像
│   ├── mtp-standalone.html        ← MTP 画像独立版
│   ├── mtp_direct_test.html       ← MTP 直接测试页
│   ├── mtp_test_data.json         ← MTP 测试数据
│   ├── architecture.html          ← 系统架构图页面
│   ├── ai-avatars-preview.html    ← AI 头像预览页
│   ├── avatar-compare.html        ← 头像对比页
│   ├── avatar-sample.html         ← 头像样张页
│   ├── card-redesign.html         ← 卡片重新设计原型
│   ├── palette-64.html            ← 64 色调色板展示
│   ├── tag-colors.html            ← 标签颜色测试
│   └── test_report.json           ← 报告测试数据
│
├── scripts/                       ← 📝 数据生成 & 构建脚本
│   ├── gen_1000_v3.py             ← ⭐ 生成 1000 条测试数据（完整版）
│   ├── gen_1000.py                ← 生成 1000 条测试数据（旧版）
│   ├── gen_avatar_prompts.py      ← 生成头像提示词
│   ├── generate_10000.py          ← 生成 10000 条测试数据
│   ├── enrich_mtp_profile.py      ← 数据富化：补充 MTP 维度 + 历史子表
│   ├── apply_mtp_v3.py            ← MTP 画像数据注入脚本
│   ├── apply_mtp.py               ← MTP 画像数据注入（旧版）
│   ├── apply_mtp_v2.py            ← MTP 画像数据注入（v2）
│   ├── apply_report.py            ← 报告数据注入
│   ├── build_v2.py                ← Widget 构建脚本
│   ├── build_widget_final.py      ← Widget 最终构建
│   ├── build_widget_simple.py     ← Widget 简化构建
│   ├── build_widget_v4.py         ← Widget v4 构建
│   ├── merge_v2.py                ← 数据合并
│   ├── patch_1000.py              ← 1000 条数据补丁
│   ├── patch_widget.py            ← Widget 补丁
│   ├── inject_mtp.py              ← MTP 数据注入
│   ├── minimal_fix.py             ← 最小化修复
│   ├── diag_mtp.py                ← MTP 诊断脚本
│   ├── verify_ids.py              ← ID 校验
│   ├── demo_employee.json         ← 示例员工数据
│   ├── avatar_prompts.json        ← 头像生成提示词集合
│   ├── avatar_b64_f.txt           ← 头像 base64（女性）
│   ├── mtp_css.txt                ← MTP CSS 提取
│   ├── mtp_full_css.txt           ← MTP 完整 CSS
│   ├── mtp_v3_css.txt             ← MTP v3 CSS
│   ├── mtp_helpers.js             ← MTP 辅助函数
│   ├── mtp_render.js              ← MTP 渲染引擎
│   ├── mtp_render_standalone.js   ← MTP 独立渲染
│   ├── mtp_v3_render.js           ← MTP v3 渲染
│   ├── mtp_widget_render.js       ← MTP Widget 渲染
│   └── test_render.js             ← 渲染测试
│
├── tests/                         ← 🧪 测试文件
│   └── （测试文件）
│
├── .github/                       ← 🔄 GitHub Actions 自动部署
│   └── workflows/
│       └── sync-to-gitee.yml      ← 推送 GitHub 时自动同步到 Gitee（中国镜像）
│
└── *.png                          ← 📸 截图/验证图片
    ├── debug_grips2.png
    ├── verify_all_grips.png
    ├── verify_final.png
    ├── verify_fresh.png
    └── verify_grips.png
```

### 核心文件速查

这些是如果你只看几个文件就能理解整个系统的：

| 文件 | 作用 | 为什么重要 |
|------|------|-----------|
| `backend/server.py` | 启动服务、挂载路由 | 一切的入口 |
| `backend/router.py` | 理解用户说什么 | 意图识别 |
| `backend/message_builder.py` | 把意图变成实际操作 | 消息流引擎 |
| `backend/data/history_cache.py` | 历史数据快速查询 | 解决 MTP 画像空白 |
| `widget/talent-widget.js` | 浏览器里所有 UI | 前端唯一文件 |
| `demo/mtp-v3.html` | MTP 画像模板 | 25 个模块的 HTML 结构 |
| `backend/utils/config.py` | 所有配置 | 改数据源、改 AI 后端都在这 |

---

## 六、怎么在本地跑起来

### 前提：安装 Python 3.11+

Windows 或 Mac 都可以。确认安装成功：
```bash
python --version
# 应该输出 Python 3.11.x 或更高
```

### 第 1 步：进入项目目录

```bash
cd talent-discover-widget
```

### 第 2 步：安装依赖

```bash
pip install -r requirements.txt
```

总共安装 9 个包：starlette、uvicorn、pandas、openpyxl、numpy、pydantic、httpx、websockets、weasyprint。

### 第 3 步：启动服务

```bash
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8765
```

启动日志应该看到：
```
✓ Loaded 999 talent records at startup
[HistoryCache] Loaded from pickle (1000 employees)
✓ History index ready for 1000 employees
INFO: Uvicorn running on http://0.0.0.0:8765
```

### 第 4 步：打开浏览器

| 地址 | 看到什么 |
|------|---------|
| `http://localhost:8765` | HR 门户首页，右下角有绿色 AI 按钮 |
| `http://localhost:8765/mtp/G000002` | 夏慧的人才全景画像 |
| `http://localhost:8765/api/health` | `{"status":"ok"}` |

### 开发/调试模式

如果不希望调用外部 AI（省钱、跑得快）：

1. 打开 `backend/utils/config.py`
2. 把 `LLM_BACKEND = "siliconflow"` 改成 `LLM_BACKEND = "mock"`
3. 重启服务

Mock 模式下，所有 AI 返回都是预置的假数据，但搜索、卡片、画像、历史数据均正常工作。

---

## 七、怎么部署到服务器

### 方式 1：阿里云 ECS（当前生产环境）

使用宝塔面板管理。核心配置：

**systemd 服务** (`/etc/systemd/system/talent-widget.service`)：
```
[Service]
ExecStart=python3 -m uvicorn backend.server:app --host 127.0.0.1 --port 8765
Environment=SILICONFLOW_API_KEY=...
```

**Nginx 反向代理**（宝塔面板配置）：
- `/ws/` → WebSocket 代理到 8765（需要 Upgrade 头）
- `/api/` → HTTP 代理到 8765
- `/widget` → 静态文件目录
- `/demo` → HTTP 代理到 8765
- SSL 证书：Let's Encrypt 自动申请

**自动部署**（crontab 每分钟）：
```bash
cd /www/wwwroot/tw && git pull origin main && systemctl restart talent-widget
```

**CI/CD 链路**：GitHub → GitHub Actions 同步到 Gitee（中国镜像）→ 服务器 crontab 每分钟 git pull → 重启服务

**一键部署脚本**：`deploy.sh`（在服务器上以 root 执行，自动完成所有步骤）

### 方式 2：Fly.io 容器部署

配置文件 `fly.toml`，适合海外访问：
```bash
fly deploy
```

### 方式 3：Render.com 云平台

配置文件 `render.yaml`，一键部署。

### 方式 4：Docker

```bash
docker build -t talent-widget .
docker run -p 8765:8765 -e SILICONFLOW_API_KEY=sk-xxx talent-widget
```

---

## 八、技术细节 — 写给开发者

### 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| **后端框架** | Starlette（异步 Web + WebSocket） | ≥0.37 |
| **服务器** | uvicorn | ≥0.29 |
| **数据库** | Excel（openpyxl + pandas） / 之后切 API | ≥3.1 / ≥2.0 |
| **向量计算** | numpy（纯 Python，无外部向量库） | ≥1.24 |
| **AI 模型** | SiliconFlow DeepSeek-V4-Pro（对比分析）/ DeepSeek-V4-Flash（路由） | - |
| **备用 AI** | 阿里云百炼（qwen3.7-plus）/ Goertek AI Hub（Qwen3-VL-235B） | - |
| **HTTP 客户端** | httpx（异步） | ≥0.25 |
| **PDF 生成** | weasyprint（服务端）/ 浏览器打印（前端，实际在用） | ≥60 |
| **前端** | 原生 JavaScript（零依赖，无构建步骤） | ES6 |
| **样式隔离** | Shadow DOM | - |
| **图表** | Chart.js 4.x（CDN 按需加载） | 4.x |
| **实时通信** | WebSocket（指数退避自动重连，最大 30s） | - |

### WebSocket 消息协议

所有消息是 JSON，必含 `type` 字段：

| type | 谁发给谁 | 含义 |
|------|---------|------|
| `message` | 浏览器 → 服务器 | 用户在聊天框输入的文字 |
| `action` | 浏览器 → 服务器 | 点击了按钮（"对比选中"/"导出Excel"），带候选人 ID 列表 |
| `text` | 服务器 → 浏览器 | 一条文字消息（Markdown 格式） |
| `card` | 服务器 → 浏览器 | 一张候选人卡片 |
| `report` | 服务器 → 浏览器 | MTP 全景画像（在右侧面版显示） |
| `compare` | 服务器 → 浏览器 | 对比分析结果 |
| `profile` | 服务器 → 浏览器 | Iceberg 人才画像 |
| `actions` | 服务器 → 浏览器 | 底部操作按钮（"对比选中""导出Excel""返回搜索"等） |
| `done` | 服务器 → 浏览器 | 本轮响应结束 |
| `error` | 服务器 → 浏览器 | 出错了 |

### LLM（AI 大模型）后端配置

在 `backend/utils/config.py` 里改一行即可切换：

```python
LLM_BACKEND = "siliconflow"   # 生产环境（硅基流动）
LLM_BACKEND = "bailian"       # 备用（阿里云百炼）
LLM_BACKEND = "aihub"         # 公司内部（Goertek AI Hub）
LLM_BACKEND = "mock"          # 开发调试（不消耗 API 额度）
```

API 密钥通过环境变量注入，不写死在代码里：
```bash
export SILICONFLOW_API_KEY="sk-xxx"
export BAILIAN_API_KEY="xxx"
```

### 数据源切换

```python
DATA_PROVIDER = "excel"   # 当前：读本地 Excel
DATA_PROVIDER = "api"     # 未来：调 HRMS 系统 REST API
```

切换为 API 后，只需要在 `backend/data/provider.py` 的 `APIDataProvider._request()` 里实现 API 请求逻辑。

### 确定性评分细节

```python
score = 70 + (hash(MD5(工号)) % 31)    # 范围 70-100
grade = "S" if ≥90, "A" if ≥80, "B" if ≥65, else "C"
```

所有视图（卡片、报告、对比）用同一个公式，保证一致性。

### MTP 模板注入机制

`/mtp/{工号}` 页面不是纯静态 HTML。`views.py` 的服务端渲染逻辑：

1. 从 `talent_store` 查出员工的所有 Excel 字段
2. 从 `history_cache` 查出该员工的所有历史数据（16 个模块）
3. 计算头像 URL（哈希算法与前端一致）
4. 读取 `demo/mtp-v3.html` 模板文件
5. 找到 `var D={` 和 `(function(){` 之间的位置
6. 把 JSON 序列化的数据注入进去
7. 返回完整的 HTML 页面

**注意**：`var D={` 和 `(function(){` 之间的任何 JavaScript 代码都会被覆盖。所以 `_downloadMtp()` 和 `_shareMtp()` 函数必须放在 `<script>` 标签中、且位置在 `var D={` **之前**。

### Canvas 图表打印问题

Chart.js 在 `<canvas>` 上画图。打印时克隆 DOM（`cloneNode`）会丢失 Canvas 像素数据。解决方案：

```
1. toDataURL() → 把 live canvas 转成 PNG data URL（必须在克隆前）
2. cloneNode(true) → 克隆 DOM
3. 克隆体中的 canvas → 替换为 <img src="data URL">
4. 写入新窗口 → print()
```

### 头像文件命名

- `widget/avatars/avatar-f-001.png` ~ `avatar-f-091.png`（女性 91 张）
- `widget/avatars/avatar-m-001.png` ~ `avatar-m-064.png`（男性 64 张）
- 算法：`hash(工号)` → 按性别选池 → 取模 → 文件名

---

## 九、常见问题

### Q: 第一次启动为什么比较慢？
A: 第一次启动时，`history_cache.py` 需要读取 Excel 中 17 个历史子表并建立索引，约需 5 秒。之后生成的 `.history_cache.pkl` 文件（约 1MB）让后续启动只需 0.5 秒。

### Q: MTP 画像里有些模块显示「暂无数据」是正常的吗？
A: 正常。不是每个员工都有所有类型的历史数据。比如有些人没有外派经历、没有专利论文、没有亲属在公司。这些模块会显示「暂无数据」。

### Q: 对比分析返回很慢？
A: 对比分析是本系统唯一调用 AI 的地方。如果网络到 SiliconFlow 较慢，Phase 2（AI 分析）可能需要 10-30 秒。Phase 1（对比表格）是瞬间出结果的，可以先看。

### Q: 下载的 PDF 图表是空白的？
A: 这通常是 Canvas 图表没有正确转换成图片。本项目已经处理了这个问题（详见第四章"打印和 PDF 下载"）。如果仍然出现，检查浏览器版本（需要支持 `canvas.toDataURL()`）。

### Q: 怎么切换到公司内部的实际 HR 数据？
A: 把 `utils/config.py` 里的 `DATA_PROVIDER` 从 `"excel"` 改为 `"api"`，实现 `APIDataProvider._request()` 对接 HRMS 系统的 REST API 即可。

### Q: 头像能换成真人的吗？
A: 可以。把 `widget/avatars/` 文件夹里的图片替换为真人照片，保持一样的命名规则即可（`avatar-f-001.png` 等）。

### Q: 怎么增加或修改 MTP 画像的信息模块？
A: 改两个地方：
1. `demo/mtp-v3.html` — HTML 模板（前端展示）
2. `backend/data/history_cache.py` — 列名映射（如果 Excel 列名和模板不一致）
3. 如果是主表字段，在 `backend/message_builder.py` 的 `_handle_report()` 里确保字段被传入

### Q: 旧版 README 在哪？
A: `README.backup.md` — 保留了上一版文档的全部内容。

---

*文档更新日期：2026-06-22 · 由 Claude Code 辅助编写*
