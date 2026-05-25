# 天气 API 接入笔记

## 方案 A — Open-Meteo（推荐，零 key）

**Base**：`https://api.open-meteo.com/v1`
**鉴权**：无
**非商用免费**，限速宽松（约 10k/天/IP）。

### 端点：未来 7 天日尺度预报

```
GET https://api.open-meteo.com/v1/forecast
    ?latitude=36.5475
    &longitude=115.2887
    &daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max,precipitation_hours,et0_fao_evapotranspiration
    &timezone=Asia%2FShanghai
    &forecast_days=7
```

### 与作物风险相关的字段对照

| 农气风险 | Open-Meteo 字段 |
| --- | --- |
| 高温热害 | `temperature_2m_max`, `apparent_temperature_max` |
| 低温冷害/霜冻 | `temperature_2m_min` |
| 暴雨/烂场雨 | `precipitation_sum`, `precipitation_hours` |
| 大风/倒伏 | `wind_speed_10m_max`, `wind_gusts_10m_max` |
| 干旱/墒情 | `et0_fao_evapotranspiration`（参考蒸散量），小时级有 `soil_moisture_0_to_7cm` 等 |

### Collector 伪代码

```python
async def fetch_openmeteo(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "precipitation_hours",
            "wind_speed_10m_max", "wind_gusts_10m_max",
            "et0_fao_evapotranspiration",
        ]),
        "timezone": "Asia/Shanghai",
        "forecast_days": 7,
    }
    r = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
    return r.json()["daily"]
```

---

## 方案 B — 和风天气 QWeather（中文预警精）

**Base**：每个账号专属 host，形如 `xxxxxxx.re.qweatherapi.com`（不再是公开的 `devapi.qweather.com`）
**鉴权**：`Authorization: Bearer <YOUR_JWT_OR_API_TOKEN>`

### 端点

| 用途 | 路径 |
| --- | --- |
| 3 天日尺度预报 | `GET /v7/weather/3d?location=<lon,lat>` |
| 24h 小时级 | `GET /v7/weather/24h?location=<lon,lat>` |
| 天气预警（国标） | `GET /v7/warning/now?location=<lon,lat>` |

### 注意

- `location` 可以是 LocationID，也可以直接传 `经度,纬度`（**经度在前**，跟绝大多数 API 相反，容易踩坑）
- 响应顶层字段：`code`, `updateTime`, `fxLink`, `daily | hourly | warning`, `refer`
- `code == "200"` 才是成功，其它都是错误码
- 免费开发版仍可用，但要去 console.qweather.com 创建"项目"+"凭据"
- 预警接口的 `severity` / `typeName` 字段是中文国标，对农业灾种适配比 Open-Meteo 好

### Collector 伪代码

```python
async def fetch_qweather_3d(lat: float, lon: float) -> dict:
    headers = {"Authorization": f"Bearer {os.environ['QWEATHER_TOKEN']}"}
    url = f"https://{os.environ['QWEATHER_HOST']}/v7/weather/3d"
    params = {"location": f"{lon:.2f},{lat:.2f}"}  # 注意经度在前
    r = await client.get(url, params=params, headers=headers)
    body = r.json()
    if body.get("code") != "200":
        raise RuntimeError(f"qweather error: {body}")
    return body["daily"]
```

---

## 建议落地

1. Collector 写一个 `WeatherProvider` 抽象，下面挂 `OpenMeteoProvider` 和 `QWeatherProvider` 两个实现，通过 `LLM_PROVIDER` 类似的 env 切换。
2. Demo 默认走 Open-Meteo。
3. 走 QWeather 时把预警 `warning/now` 的 `typeName` 直通 Analyzer，作为风险信号的最强先验。
