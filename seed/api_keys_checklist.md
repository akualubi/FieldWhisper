# 需要你（人）手动办的清单

> 我能查文档、写代码、造 mock。**注册账号、绑卡、拿 key 只能你自己点。**
> 优先级从上到下，越上越关键。

## 🔴 P0 — Demo 必备

### 1. 天气数据源（二选一，**强烈建议先选 Open-Meteo**）

- **Open-Meteo**（推荐）
  - 链接：https://open-meteo.com/
  - **不需要注册、不需要 key、不需要绑卡**
  - 非商用免费，限速宽松（约 10,000 次/天/IP）
  - 缺点：不是中国本土数据源，预警 (weather warning) 接口不如 QWeather 细
  - **结论：demo 直接用，路演当天不会因为 key 翻车**

- **和风天气 QWeather**（备选）
  - 链接：https://console.qweather.com/
  - 2024 改版后：注册账号 → 创建"项目" → 创建"凭据"(JWT 或 API KEY) → 拿到一个**专属 host**（形如 `xxxxxxxxxx.re.qweatherapi.com`）
  - 免费开发版仍有，按"开发者订阅"开通，无需企业认证
  - 优点：中文预警分类细（暴雨/大风/冰雹/干旱… 都是国标编码）
  - **如果走 QWeather，请把 host 和 token 同时记下来填 .env**

### 2. LLM API key（任选一个）

看 [llm_api_notes.md](llm_api_notes.md) 的价格对比。
**最快路径：DeepSeek**（注册即送 500 万 token，无需绑卡）。
- 注册：https://platform.deepseek.com/
- 控制台 → API Keys → Create new
- 模型用 `deepseek-chat`（V4 Flash，0.14/0.28 USD per M tokens）

如果你已经有 Anthropic / 通义 / Moonshot 任一账号，直接用，省一次注册。

## 🟡 P1 — 加分项

### 3. 示例叶片图片

不用注册。看 [leaf_images_notes.md](leaf_images_notes.md)，从 PlantVillage 数据集拉 2 张玉米 Common Rust 或 Northern Leaf Blight 的真实病叶照片，扔到 `backend/static/demo_leaves/` 即可。

### 4. 真实地块经纬度

不给就用 `mock/parcels.json` 里的默认 3 块（河北馆陶 / 河南中牟 / 黑龙江绥化）。
要换成你自己的地块：把经纬度（精确到小数点后 4 位）发我，我替你改 mock。

### 5. 保险公司请求 schema

你如果手上没有真实样例，用 `mock/insurance_payload.json` 即可，字段是按行业常见 claim notification 推的，足够 demo。

## ⚪ P2 — 完全 mock，不用找

- 卫星 NDVI → `mock/ndvi_series.json`
- 农业部通报 → `mock/agri_bulletins.md`
- 农户群聊 → `mock/farmer_chats.md`
- 历史灾害案例 → `mock/experience.md`（8 条种子，演讲时显得"有底子"）
