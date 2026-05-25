# LLM API 接入笔记（2026-05 价格快照）

> 价格随时变。下面是 2026 年 5 月公开页快照，下单前自己再核一次。
> 单位统一为 **USD / 百万 token**（input / output）。

## 价格对比表

| 提供商 | 模型 | Input | Output | 备注 |
| --- | --- | ---: | ---: | --- |
| DeepSeek | `deepseek-chat` (V4 Flash) | $0.14 | $0.28 | 注册送 500 万 token；缓存命中 input 直降 98% |
| DeepSeek | `deepseek-reasoner` (V4 Pro) | $0.435* | $0.87* | *促销价至 2026-05-31；常规 $1.74 / $3.48 |
| 阿里 DashScope | `qwen-turbo` | ≈$0.033 | ≈$0.13 | 国内访问稳定，免代理 |
| 阿里 DashScope | `qwen-flash` | $0.05–$0.25 | $0.40–$2.00 | 1M context，中文好 |
| Moonshot | `kimi-k2.5` | （见官网） | （见官网） | 长中文/思维链强，缓存命中率高 |
| Anthropic | `claude-haiku-4.5` | $1.00 | $5.00 | 海外卡 |
| Anthropic | `claude-sonnet-4.6` | $3.00 | $15.00 | 海外卡 |

## 给穗安/SuiAn 的推荐

- **Decision Agent 润色话术** → `deepseek-chat` 或 `qwen-turbo`，2 句话级别的输出，每次成本 < $0.001
- **Harness 归因 / 经验反思** → `deepseek-reasoner` 或 `claude-sonnet-4.6`（需要更强推理）
- **完全离线兜底** → 规则模板：`f"{灾种}{风险等级}风险，{发生窗口}，{建议动作}"`，必须保证 LLM 挂了也能跑

## SDK 选型

四家都兼容 OpenAI Chat Completions 格式，**只换 base_url + api_key + model 名**：

```python
from openai import AsyncOpenAI

PROVIDERS = {
    "deepseek":  ("https://api.deepseek.com",                    "deepseek-chat"),
    "qwen":      ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-turbo"),
    "moonshot":  ("https://api.moonshot.cn/v1",                  "moonshot-v1-8k"),
}

def make_client(provider: str) -> tuple[AsyncOpenAI, str]:
    base, model = PROVIDERS[provider]
    return AsyncOpenAI(base_url=base, api_key=os.environ["LLM_API_KEY"]), model
```

Anthropic 用官方 SDK：`from anthropic import AsyncAnthropic`。

## 务必：规则回退

```python
async def polish(payload: dict) -> str:
    if os.getenv("LLM_PROVIDER", "none") == "none":
        return rule_based_phrasing(payload)
    try:
        return await llm_polish(payload)
    except Exception as e:
        log.warning("llm fallback: %s", e)
        return rule_based_phrasing(payload)
```

演讲现场断网/限流时，这一段决定 demo 死活。

## 信源

- [DeepSeek API Docs Pricing](https://api-docs.deepseek.com/quick_start/pricing)
- [DeepSeek Pricing 2026 — felloai](https://felloai.com/deepseek-pricing/)
- [Kimi 平台定价](https://platform.moonshot.cn/docs/pricing/tools)
- [2026 大模型 API 横评（SegmentFault）](https://segmentfault.com/a/1190000047676047)
