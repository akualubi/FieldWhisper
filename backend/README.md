# 穗安 SuiAn · 后端 v0.2

> 多 Agent + Harness 自进化的大田作物风险预警平台。
> **已对接姊妹窗口产出的 `seed/` 种子包**（parcels / scenarios / NDVI / 通报 / 群聊 / 保险 schema / 历史 case）。
> 架构总览见 [`../README.md`](../README.md)。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. （可选）配 LLM 给 Decision 润色话术。无 key 走规则模板，演讲仍能跑。
cp .env.example .env
# 编辑 .env，把 LLM_PROVIDER=deepseek 留着，填一个 LLM_API_KEY 即可

# 3. 起服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. 端到端冒烟测试（跑 seed 3 个 scenario + Harness 自进化）
python -m backend.tests.smoke
```

## 演讲一分钟流程

```bash
# 看 seed 仓库索引
curl http://localhost:8000/api/seed | jq

# 看预设 scenarios
curl http://localhost:8000/api/collect/presets | jq

# 一键触发"烂场雨"场景（不用传 plot_id，scenario 自带）
curl -X POST "http://localhost:8000/api/collect/inject/preset/DEMO-LANCHANG-YU"

# 直接分析对应 plot
curl -X POST "http://localhost:8000/api/analyze/P-HEB-GUANTAO-001?collect_first=false" | jq

# 看产出的 Warning + matched_history_case
curl "http://localhost:8000/api/warnings?plot_id=P-HEB-GUANTAO-001" | jq '.[0]'

# 切到保险公司视角（schema 完全对齐 seed/mock/insurance_payload.json）
WID=$(curl -s "http://localhost:8000/api/warnings?plot_id=P-HEB-GUANTAO-001" | jq -r '.[0].id')
curl "http://localhost:8000/api/warnings/$WID/render?customer=insurance" | jq

# 模拟漏报反馈 → Harness 写回
curl -X POST "http://localhost:8000/api/feedback/$WID" \
  -H "content-type: application/json" \
  -d "{\"warning_id\":\"$WID\",\"outcome\":\"underestimated\",\"actual_level\":\"极高\",\"actual_loss_pct\":0.45,\"adopted\":false,\"notes\":\"实际损失更严重\",\"reporter\":\"coop:demo\"}" | jq

# 查 Agent 进化历史
curl http://localhost:8000/api/agents/plot/history | jq
```

## API 一览

| 类别 | 端点 | 备注 |
|------|------|------|
| 地块 | `GET/POST /api/plots` | 启动从 `seed/mock/parcels.json` 自动种 |
| 采集 | `POST /api/collect/{plot_id}` | 拉 Open-Meteo + seed NDVI + 5 条通报 |
| **Demo 注入** | `POST /api/collect/inject/preset/{scenario_id}` | 触发 seed scenario，**plot_id 可省**（scenario 自带，含冰雹临时果园） |
| **Demo 注入** | `GET /api/collect/presets` | 列 seed 全部 scenarios |
| **Demo 注入** | `POST /api/collect/inject` | 自由注入 DataItem |
| 分析 | `POST /api/analyze/{plot_id}?collect_first=…` | 5 Analyst 并发 → Simulator → Decision |
| 预警 | `GET /api/warnings` / `…/{id}` | 含 peril_code + matched_history_case |
| 渲染 | `GET /api/warnings/{id}/render?customer=insurance` | 输出对齐 seed insurance schema |
| 反馈 | `POST /api/feedback/{warning_id}` | 触发 Harness 评估 + 写回 |
| Agent | `GET /api/agents/{name}/assets` / `…/history` | 透明可审计 |
| 批量 | `POST /api/batch/score` | 保险公司视角，批量 plot_ids |
| **Seed** | `GET /api/seed*` | 直通暴露 seed 内容（parcels / scenarios / bulletins / chats / insurance / experience） |
| **Live** | `GET /api/events/stream` | SSE 实时事件流（演讲大屏订阅） |

## 与 seed/ 的对应关系

| seed 文件 | 后端消费方式 |
|-----------|-------------|
| `seed/mock/parcels.json` | 启动时种 3 个真实物候期 plot；`Plot.from_seed()` |
| `seed/mock/manual_injection_scenarios.json` | `/api/collect/inject/preset/{id}` 一键触发，含天气 override / NDVI / 通报 / 群聊 / 临时地块 |
| `seed/mock/ndvi_series.json` | `collect_for_plot` 优先读 seed，掉了才退 mock 时序 |
| `seed/mock/agri_bulletins.md` | 5 条通报全量入池为 `notice` DataItem，Pest Analyst 自动匹配 |
| `seed/mock/farmer_chats.md` | 按 scenario 引用号取（`group_chat 4` → 冰雹群聊） |
| `seed/mock/insurance_payload.json` | Delivery `_render_insurance` 字段完全对齐 |
| `seed/mock/experience.md` | Decision 推理时与本地 `knowledge/decision/experience.md` 叠加，做 `matched_history_case` 检索 |
| `seed/weather_api_notes.md` | Collector `adapters.fetch_open_meteo_forecast` 已实现；QWeather 留 env hook |
| `seed/llm_api_notes.md` | LLM 客户端按 deepseek/qwen/moonshot/anthropic 四家统一抽象 |

## 三个 seed scenario 跑通后的产出

| Scenario | 触发条件 | 期望 Warning | 实际产出 |
|----------|---------|-------------|----------|
| `DEMO-LANCHANG-YU` | 河北馆陶冬麦灌浆末 + 5/28 起连阴雨 | `HEAVY_RAIN_AT_HARVEST` 高 | ✅ `peril=HEAVY_RAIN_AT_HARVEST` `case=CASE-001` |
| `DEMO-WAN-FROST` | 黑龙江绥化春玉米三叶 + 5/27 夜 -2℃ | `LATE_FROST` 中 | ✅ `peril=LATE_FROST` |
| `DEMO-HAIL` | 山东烟台苹果膨果期 + 冰雹群聊舆情 | `HAIL` 极高 + AUTO_CLAIM | ✅ `peril=HAIL` + `PRE_CLAIM_PREP` |

## 资产自进化文件（Harness 会改这些）

```
backend/knowledge/<agent>/
├── experience.md
├── prompt.md
├── rules.yaml
└── weights.json
```

跑完 demo 想回到种子状态：
```bash
git checkout backend/knowledge/
rm backend/suian.db
```

## 项目结构

```
backend/
├── app/
│   ├── main.py                 # 启动从 seed/parcels.json 种地块
│   ├── orchestrator.py
│   ├── api/                    # 10 个路由（plots/collect/analyze/warnings/feedback/agents/events/batch/seed）
│   ├── agents/
│   │   ├── collector/
│   │   │   ├── agent.py        # 真实 Open-Meteo + seed 通报 + 手动注入
│   │   │   ├── adapters.py
│   │   │   └── presets.py      # 翻译 seed scenario → DataItem[]
│   │   ├── analysts/           # weather / crop / plot / pest / sentiment
│   │   │   └── weather.py      # 含 frost / 烂场雨 / 干热风 检测
│   │   ├── simulator.py
│   │   ├── decision.py         # 复合场景检测 + peril_code + matched_history_case
│   │   └── delivery.py         # insurance schema 完全对齐 seed
│   ├── harness/                # evaluator + evolver
│   ├── events/                 # SSE 事件总线
│   ├── llm/                    # 4 家 LLM 统一抽象 + 规则回退
│   ├── models/                 # + peril.py
│   └── storage/
│       ├── data_pool.py
│       ├── knowledge.py
│       └── seed_loader.py      # 单一入口读 seed/
├── knowledge/                  # Agent 可进化资产
└── tests/smoke.py              # 跑通全部 3 个 seed scenario + Harness
```
