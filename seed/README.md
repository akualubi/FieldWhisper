# 穗安 / SuiAn — 外部资源种子包

> 给另一个正在 `backend/` 做最小实现的 Claude Code 窗口的"输入仓库"。
> 这里只放：可直接拿来跑的 mock 数据 + 需要外部 API key 时的接入说明。
> **不动 backend/ 代码**，由实现窗口决定怎么消费。

## 目录

| 文件 | 给谁用 | 是否需要联网/key |
| --- | --- | --- |
| [api_keys_checklist.md](api_keys_checklist.md) | 你（人）手动操作 | — |
| [weather_api_notes.md](weather_api_notes.md) | Weather Collector | Open-Meteo 不要 key / QWeather 要 |
| [llm_api_notes.md](llm_api_notes.md) | Decision Agent + Harness | 任选一个 key |
| [leaf_images_notes.md](leaf_images_notes.md) | 田间影像 demo 截图 | 不要 key |
| [mock/parcels.json](mock/parcels.json) | Collector / Analyzer | mock |
| [mock/experience.md](mock/experience.md) | Decision Agent 经验库种子 | mock |
| [mock/insurance_payload.json](mock/insurance_payload.json) | Delivery Agent | mock |
| [mock/ndvi_series.json](mock/ndvi_series.json) | Analyzer (遥感) | mock |
| [mock/agri_bulletins.md](mock/agri_bulletins.md) | 病虫情报源 | mock |
| [mock/farmer_chats.md](mock/farmer_chats.md) | 舆情源 | mock |
| [mock/manual_injection_scenarios.json](mock/manual_injection_scenarios.json) | 演讲现场点亮 pipeline | mock |

## Demo 当天最低跑通条件

1. **天气源**：能联网就用 Open-Meteo（零 key），实在不能联网就读 `mock/manual_injection_scenarios.json` 里的预设。
2. **LLM**：有 key 就调真模型润色话术；没 key 也要规则回退（Decision Agent 必须能输出，只是不那么"像人话"）。
3. **手动注入**：演讲现场点按钮 → 走 `mock/manual_injection_scenarios.json` 里的某一条 → SSE 实时刷新页面。这是 demo 的护城河，不能依赖联网。

## 真实 key 拿到后填到哪里

实现窗口请在 `backend/.env.example` 里预留这几个变量（具体命名由实现方决定）：

```
QWEATHER_HOST=
QWEATHER_TOKEN=
OPENMETEO_BASE=https://api.open-meteo.com/v1
LLM_PROVIDER=deepseek            # deepseek | qwen | moonshot | anthropic | none
LLM_API_KEY=
LLM_MODEL=deepseek-chat
```

用户拿到真 key 后只改 `.env`，不动代码。
