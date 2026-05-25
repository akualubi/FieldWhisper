# 历史灾害数据整理

这份目录用于存放人工整理的历史灾害事件数据，当前版本以“真实新闻/官方报道可追溯”为原则，先整理出一批可直接使用的样本。

## 文件

- `disaster_events_curated.csv`：正式推荐使用的结构化 CSV
- `disaster_events_curated.md`：同一批数据的 Markdown 表格版本，便于人工查看

## 字段说明

- `id`：事件编号
- `year_month`：年月，格式为 `YYYY-MM`
- `province`：省份或直辖市
- `city_or_area`：主要影响地区
- `weather_type`：标准化灾害天气类型
- `event_name`：事件名称
- `report_date`：来源报道发布日期
- `source_org`：来源机构
- `source_title`：来源标题
- `source_url`：来源链接
- `news_summary`：对报道内容的整理摘要
- `impact_notes`：可用于后续建模或分析的影响说明

## 当前覆盖的天气类型

- 台风
- 暴雪
- 暴雨
- 高温
- 沙尘暴
- 洪涝
- 干旱
- 大风

## 使用说明

- 这是一份“人工精选样本”，不是全量历史库。
- 对于同时包含多种灾害特征的事件，`weather_type` 字段按主要致灾天气做归类。
- 后续如需扩成正式数据集，建议继续补充：
  - 具体开始/结束日期
  - 受灾人口
  - 直接经济损失
  - 农作物受灾面积
  - 经纬度或县级行政区
  - 是否影响农业生产
