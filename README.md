# 穗安 SuiAn · 大田作物风险智能预警平台 — 后端

> **穗安**（"穗"=作物穗粒，"安"=安全无虞）— 面向 B 端机构的大田作物风险智能预警平台。
> 多 Agent 协同 + Harness 驱动的自进化机制，把"网络公开数据"提炼为"地块级、可追溯、可决策"的风险情报。
>
> *仓库代号：FieldWhisper · 产品中文名：穗安 · 英文名：SuiAn*

---

## 一、设计哲学

传统农情服务是"数据搬运工"——把气象/遥感/新闻翻译一遍推给用户。
穗安不一样：

1. **数据只是初始风险状态**：Collector Agent 只负责"搬"，不下判断。
2. **真正的智能在 Analyst Agent**：每个 Analyst 只看一个领域（气象 / 作物 / 地块 / 病虫害 / 舆情），输出领域结论。
3. **决策由 Decision Agent 统一整合**：领域结论 + 推演结果 → 结构化预警。
4. **真正的壁垒在 Harness 自进化**：每次预警后回收真实反馈，把失败案例**写回对应 Agent 的经验文档、规则、权重**，下一轮就比上一轮更准。

> **一个 Agent = 一个角色 + 一组可被 Harness 重写的资产文件**。

---

## 二、核心原则：按"角色职能"切分，不按"数据类型"切分

每个 Agent 都有**唯一职责**和**清晰的输入/输出契约**：

| 角色 | 职责 | 输入 | 输出 | 是否推理 |
|------|------|------|------|----------|
| **Collector 采集** | 只搬运、清洗、入库 | 外部 API / 网页 / 通报 | 标准化 DataItem | ❌ 不下判断 |
| **Analyst 分析** | 单领域专家：把数据 → 领域结论 | DataPool 中的相关切片 | 领域 RiskJudgment + 置信度 | ✅ 领域推理 |
| **Simulator 推演** | 综合所有领域结论推未来 | 全部 RiskJudgment | 24/48/72h 演化轨迹 | ✅ 时序推演 |
| **Decision 决策** | 把判断转成"农户能执行的话" | Judgments + Trajectory | 结构化预警 JSON | ✅ 整合决策 |
| **Delivery 推送** | 按 B 端客户类型适配输出 | 预警 JSON | API / 短信 / PDF / 大屏 | ❌ 模板化 |
| **Harness 进化** | 评估 → 归因 → 写回 Agent 资产 | 真实反馈 | Agent 资产更新 | ✅ 元推理 |

**关键设计约束**：
- Collector **绝对不做判断**。它把气象 API 返回的"明天 38℃"原样入库，不能写"高温预警"。"高温是不是预警"是 Analyst 的事。
- Analyst 之间**互不依赖**。Weather Analyst 看完气象就出判断，不等 Crop Analyst。这样并发执行、单独进化都更干净。
- 跨领域综合**只在 Simulator 和 Decision 发生**。
- 所有 Agent 的"知识"都以**人类可读文件**形式存在，被 Harness 持续重写。

---

## 三、智能体框架总览

```
                  ┌──────────────────────────────────────────────┐
                  │              外 部 数 据 源                   │
                  │  气象 API · 遥感卫星 · 农业新闻 · 病虫害通报   │
                  │  政府通知 · 农户舆情 · 田间影像 · 历史样本     │
                  └────────────────────┬─────────────────────────┘
                                       ▼
   ╔═══════════════════════ ① 采集 Collector Agent ═══════════════════════╗
   ║   职责：只搬不判。多个 Source Adapter 并行拉取 → 清洗 → 标准化         ║
   ║                                                                     ║
   ║   ┌──────────┬──────────┬──────────┬──────────┬──────────┐           ║
   ║   │ 气象源    │ 遥感源   │ 通报源   │ 舆情源   │ 影像源   │  ……       ║
   ║   └────┬─────┴─────┬────┴─────┬────┴─────┬────┴─────┬────┘           ║
   ║        │           │          │          │          │                ║
   ║        │   ┌───────────────────────────────────────┐ │                ║
   ║        │   │  🎤 Manual Injection (Demo 通道)      │ │                ║
   ║        │   │   演讲者 / 用户手动注入一条 DataItem   │ │                ║
   ║        │   │   - 自由 JSON   - 预设场景一键触发     │ │                ║
   ║        │   └───────────────────┬───────────────────┘ │                ║
   ║        ▼           ▼           ▼          ▼          ▼               ║
   ║              ┌──────────────────────────────────┐                    ║
   ║              │    统一 DataPool (DataItem)     │                    ║
   ║              │ {source, type, ts, geo, payload, │                    ║
   ║              │  injected_by?}                   │                    ║
   ║              └──────────────────────────────────┘                    ║
   ╚══════════════════════════════════╤═══════════════════════════════════╝
                                      ▼
   ╔═══════════════════ ② 分析 Analyst Agents (并行) ═════════════════════╗
   ║                                                                     ║
   ║   每个 Analyst 只看自己领域的 DataItem，独立输出 RiskJudgment         ║
   ║                                                                     ║
   ║   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  ║
   ║   │ 气象 Analyst│  │ 作物 Analyst│  │ 地块 Analyst│                  ║
   ║   │ 触发条件?    │  │ 生育期脆弱? │  │ 地势/排水?  │                  ║
   ║   └─────────────┘  └─────────────┘  └─────────────┘                  ║
   ║                                                                     ║
   ║   ┌─────────────┐  ┌─────────────┐                                   ║
   ║   │ 病虫害      │  │ 舆情 Analyst│                                   ║
   ║   │ Analyst     │  │ 早期异常?   │                                   ║
   ║   └─────────────┘  └─────────────┘                                   ║
   ║                                                                     ║
   ║                  ▼  ▼  ▼  ▼  ▼  统一输出格式                        ║
   ║              ┌──────────────────────────────────┐                    ║
   ║              │   RiskJudgment[]                 │                    ║
   ║              │ {agent, level, type, evidence,   │                    ║
   ║              │   confidence, raw_refs}          │                    ║
   ║              └──────────────────────────────────┘                    ║
   ╚══════════════════════════════════╤═══════════════════════════════════╝
                                      ▼
   ╔═══════════════════ ③ 推演 Simulator Agent ═══════════════════════════╗
   ║                                                                     ║
   ║          综合所有 RiskJudgment，推演灾害演化轨迹                      ║
   ║                                                                     ║
   ║          ┌────────────────────────────────────────┐                  ║
   ║          │ "如果不干预 → 48h 后概率 X%"            │                  ║
   ║          │ "如果采取建议 → 损失降低 Y%"            │                  ║
   ║          └────────────────────────────────────────┘                  ║
   ╚══════════════════════════════════╤═══════════════════════════════════╝
                                      ▼
   ╔═══════════════════ ④ 决策 Decision Agent ════════════════════════════╗
   ║                                                                     ║
   ║   整合 Judgments + Trajectory → 输出结构化预警 JSON                  ║
   ║                                                                     ║
   ║   {                                                                 ║
   ║     "plot_id": "BJ-CP-001",                                         ║
   ║     "crop": "玉米", "stage": "抽雄期",                              ║
   ║     "risk_level": "高", "risk_type": "高温热害",                    ║
   ║     "actions": ["清晨喷灌降温", "叶面喷磷酸二氢钾"],                  ║
   ║     "best_window": "未来 48 小时",                                  ║
   ║     "confidence": 0.87,                                             ║
   ║     "evidence": [judgment_ids...],                                  ║
   ║     "data_sources": [...]                                           ║
   ║   }                                                                 ║
   ╚══════════════════════════════════╤═══════════════════════════════════╝
                                      ▼
   ╔═══════════════════ ⑤ 推送 Delivery Agent ════════════════════════════╗
   ║                                                                     ║
   ║   保险公司 API │ 合作社控制台+短信 │ 政府 PDF 简报 │ 粮企月报 │ 农资   ║
   ║                                                                     ║
   ╚══════════════════════════════════╤═══════════════════════════════════╝
                                      ▼
                          ┌──────────────────────────┐
                          │   B 端真实反馈           │
                          │  · 风险是否真的发生?      │
                          │  · 预警是否准确?         │
                          │  · 建议是否被采纳?       │
                          │  · 实际损失多少?         │
                          └────────────┬─────────────┘
                                       ▼
   ╔═══════════════════ ⑥ Harness 进化 Agent ═════════════════════════════╗
   ║                                                                     ║
   ║    ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐     ║
   ║    │Evaluator │───►│ Root Cause   │───►│      Evolver         │     ║
   ║    │打分      │    │ 归因到具体    │    │  写回 Agent 资产文件  │     ║
   ║    │误/漏/准  │    │ Agent + 资产 │    │                      │     ║
   ║    └──────────┘    └──────────────┘    └──────────┬───────────┘     ║
   ║                                                   │                  ║
   ║                                                   ▼                  ║
   ║                       backend/knowledge/<agent>/{experience.md,     ║
   ║                       rules.yaml, weights.json, prompt.md}          ║
   ║                                                   │                  ║
   ╚═══════════════════════════════════════════════════╪══════════════════╝
                                                       │
                       下一轮 Agent 加载时              │
                       直接读到更新后的资产 ◄───────────┘
```

---

## 四、各 Agent 的输入 / 输出契约

> 这是"角色清晰"的根本：每个 Agent 只接受/产出指定结构，编排器靠契约组装。

### ① Collector Agent
```yaml
input:
  - source_config:  哪些数据源 / 频率 / 鉴权
  - geo_scope:      地块经纬度 / 行政区
  # —— Demo 通道：手动注入 ——
  - manual_inject:  允许外部直接 POST 一条 DataItem 或一个预设场景名

output:
  - DataItem[]:
      source:        "weather_api" | "sentinel" | "news" | "field_cam"
                   | "farmer_chat" | "manual_injection" | ...
      type:          "forecast" | "ndvi" | "notice" | "image" | "post" | ...
      ts:            UTC timestamp
      geo:           {lat, lon, plot_id?}
      payload:       原始结构化数据（不解释、不判断）
      injected_by:   null | "user:<id>"   # 注入者标记，便于 Demo 时区分演示数据
side_effects:
  - 写入 DataPool

# 注入的 DataItem 和真实采集的走完全一样的下游 pipeline ——
# Analyst / Simulator / Decision / Harness 都不区分来源。
# 这意味着演讲时一键注入"未来 48h 华北大风"就能让全系统当场亮起来。
```

**Demo 预设场景（presets）**：把常用演示打包成可一键触发的 batch：

```
presets:
  - "玉米抽雄期连日 38℃ 高温热害"        → 注入 7 条 forecast
  - "华北大风 + 玉米拔节期土壤湿度偏高"   → 注入 forecast + soil + crop_stage
  - "小麦条锈病早期农户照片"             → 注入 1 条 field_cam 图像
  - "保险承保区域 1000 地块批量评分请求"  → 注入 plot 批量数据
```

### ② Analyst Agent（领域专家，可有多个实例）
```yaml
agent_kind: "weather" | "crop" | "plot" | "pest" | "sentiment"
input:
  - DataItem[] (按订阅的 source/type 过滤)
  - PlotProfile  (作物 / 生育期 / 历史 / 地势 等静态档案)
output:
  - RiskJudgment:
      agent_kind:  哪个领域
      plot_id:     针对哪块地
      risk_type:   "高温热害" | "倒伏" | "条锈病" | ...
      level:       "无" | "低" | "中" | "高" | "极高"
      evidence:    [DataItem_id, ...]       (可追溯)
      confidence:  0.0 ~ 1.0
      rationale:   人类可读的解释（一两句）
self_evolution_assets:
  - knowledge/<agent_kind>/experience.md
  - knowledge/<agent_kind>/rules.yaml
  - knowledge/<agent_kind>/weights.json
  - knowledge/<agent_kind>/prompt.md
```

### ③ Simulator Agent
```yaml
input:
  - RiskJudgment[]    (本轮所有 Analyst 输出)
  - PlotProfile
output:
  - Trajectory:
      baseline:    [{t+24h: level, prob}, {t+48h: ...}, {t+72h: ...}]
      mitigated:   同上结构，假设采纳建议后
      key_drivers: 推演中最关键的几个 Judgment
```

### ④ Decision Agent
```yaml
input:
  - RiskJudgment[]
  - Trajectory
  - PlotProfile
output:
  - Warning (结构化 JSON, 见架构图)
```

### ⑤ Delivery Agent
```yaml
input:
  - Warning
  - CustomerProfile  (B 端类型 / 推送渠道 / 接收 schema)
output:
  - 按客户定制的推送实例（API payload / SMS / PDF / 图表）
```

### ⑥ Harness Agent
```yaml
input:
  - Warning + Feedback (真实结果)
output:
  - Evaluation:    {accuracy, precision, recall, actionable_score}
  - RootCause:     该失败归因到哪个 Agent 的哪个资产
  - AssetPatch[]:  对 experience.md / rules.yaml / weights.json 的具体 diff
side_effects:
  - 应用 AssetPatch → 下一轮 Agent 加载时立刻生效
```

---

## 五、Agent 的"可进化资产"

每个会推理的 Agent（Analyst / Simulator / Decision）都绑定一个资产目录：

```
backend/knowledge/<agent_name>/
├── experience.md      # 经验文档：成功/失败案例 + 规则的"为什么"
├── prompt.md          # 系统提示词：角色、推理风格
├── rules.yaml         # 阈值规则：温度/风速/湿度等触发条件
├── weights.json       # 权重：多因素叠加时的加权系数
└── knowledge/         # 知识库片段：历史灾害案例、农艺规程
    └── case_*.md
```

**Agent 推理流程**（每次都重新加载，所以 Harness 写完立刻生效）：

```
load(experience.md) + load(prompt.md) + load(rules.yaml) + load(weights.json)
                              │
                              ▼
              组装 system prompt + 决策上下文
                              │
                              ▼
                    LLM 调用 或 规则引擎
                              │
                              ▼
                   结构化输出 + 置信度 + 引用
```

---

## 六、自进化闭环（一个具体例子）

> 玉米拔节期 + 土壤湿度连续偏高 + 6～7 级大风 → 严重倒伏

```
T0  Decision Agent 综合后判断为 [中风险]，建议"加强排水观察"
T1  Delivery Agent 推送给合作社
T2  3 天后实际发生大面积倒伏，合作社上报损失
T3  Harness Evaluator：判定为漏报（中风险 ≠ 严重灾害）
T4  Root Cause 归因：
       - Weather Analyst 风速阈值 6 级偏宽 ✗
       - Crop Analyst 拔节期脆弱度权重不足 ✗
       - Decision Agent 未识别"湿度+大风+生育期"复合场景 ✗
T5  Evolver 写回：
       knowledge/weather/rules.yaml:  wind_threshold 6 → 5.5
       knowledge/crop/weights.json:   jointing_stage 1.0 → 1.4
       knowledge/decision/experience.md: 追加复合场景案例
T6  下一次相同情形 → Decision 直接判定 [高风险] + 具体行动建议
```

---

## 七、API 与服务面（规划中）

| 类别 | Endpoint | 用途 |
|------|----------|------|
| 地块 | `POST /plots` / `GET /plots/{id}` | 注册/查询地块 |
| 采集 | `POST /collect` | 手动触发一次 Collector 真实抓取 |
| **Demo 注入** | `POST /collect/inject` | **手动 POST 一条 DataItem 注入 DataPool（演示用）** |
| **Demo 注入** | `POST /collect/inject/preset/{name}` | **一键触发预设场景（如"玉米高温热害"）** |
| **Demo 注入** | `GET /collect/presets` | **列出所有可用预设场景** |
| 分析 | `POST /analyze/{plot_id}` | 触发一次完整链路（Collector→Analysts→Simulator→Decision） |
| 预警 | `GET /warnings?plot_id=&since=` | 查询历史预警 |
| 反馈 | `POST /feedback/{warning_id}` | B 端回写真实结果 → 触发 Harness |
| Agent | `GET /agents/{name}/assets` | 查看某 Agent 当前的经验/规则（透明可审计） |
| Agent | `GET /agents/{name}/history` | 该 Agent 的资产进化历史（diff 序列） |
| 批量 | `POST /batch/score` | 保险公司视角：批量地块风险评分 |
| **Live** | `GET /events/stream` (SSE) | **Server-Sent Events：实时推送 DataItem/Judgment/Warning，演讲屏幕直接订阅** |

---

## 八、目录规划

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── api/                 # REST 路由
│   ├── agents/
│   │   ├── base.py          # Agent 抽象基类（资产加载/输出契约）
│   │   ├── collector.py     # ① Collector + source adapters
│   │   ├── analysts/        # ② 各领域 Analyst
│   │   │   ├── weather.py
│   │   │   ├── crop.py
│   │   │   ├── plot.py
│   │   │   ├── pest.py
│   │   │   └── sentiment.py
│   │   ├── simulator.py     # ③ Simulator
│   │   ├── decision.py      # ④ Decision
│   │   └── delivery.py      # ⑤ Delivery
│   ├── harness/             # ⑥ Evaluator + RootCause + Evolver
│   ├── orchestrator.py      # 编排：按契约串/并联各 Agent
│   ├── llm/                 # LLM 客户端 + 规则回退
│   ├── models/              # Pydantic 契约模型
│   └── storage/             # SQLite + DataPool + 知识库读写
├── knowledge/               # 每个 Agent 的可进化资产
│   ├── weather/
│   ├── crop/
│   ├── plot/
│   ├── pest/
│   ├── sentiment/
│   ├── simulator/
│   └── decision/
├── data/                    # 种子数据 / mock 外部数据
└── tests/
```

---

## 九、技术栈

- **Python 3.13 + FastAPI**（异步 Web 框架）
- **Pydantic v2**（结构化数据模型 + Agent 契约）
- **SQLite + aiosqlite**（DataPool / 预警 / 反馈持久化）
- **LLM**：Anthropic Claude（可选；无 API Key 时回退到规则引擎，保证开箱即跑）
- **知识库**：Markdown + YAML/JSON（人类可读，Harness 可改）

---

> 下一步：按上述契约实现 backend 代码，先跑通"玉米高温热害"最小闭环。
