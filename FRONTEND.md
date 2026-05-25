# 穗安 AI · 农作物灾害防控多智能体风险预警系统

> 将真实舆情、气象遥感与多智能体模拟融合，把未来 24–72 小时的农作物风险转化为每个农户能执行的一条提醒。
> 单页静态网站，**零 build · 零依赖 · 零后端**，本地起一个 http server 或直接双击即可预览。

---

## 启动

```bash
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

或直接用 Node：

```bash
npx serve -p 8080
```

> `index.html` 加载 ECharts 中国地图 JSON，需要 http server，**不能直接双击**打开。

---

## 页面结构 · 10 个 Section

| # | Section | 内容 |
|---|---|---|
| 1 | **Hero** | 品牌标题 · 雷达扫描动画 · 核心指标卡 · 快速入口按钮 |
| 2 | **痛点** | 农业风险预警三大现实痛点，卡片式呈现 |
| 3 | **风险地图** | SVG 雷达图 · 高风险区位标注 · 三大信号来源说明 |
| 4 | **系统能力** | 六大系统核心能力，图标 + 描述卡片网格 |
| 5 | **多智能体** | 五类 Agent 角色卡（气象/作物/地块/病虫害/舆情）|
| 6 | **架构链路** | ⭐ 六阶段多智能体推演流程图（外部数据源 → 采集 → 分析 → 推演 → 决策 → 推送 → Harness 进化）|
| 7 | **场景演示** | 72h 时间轴：从气象检测到农户反馈的完整预警流程 |
| 8 | **数据飞轮** | 闭环自进化机制说明 · 四步骤 · 底部飞轮卡 |
| 9 | **全国风险地图** | ECharts 热力地图（31省着色）· 8 种天气图标覆盖 · 悬停省份详情面板 |
| 10 | **Footer / CTA** | 启动演示 · 联系我们 · 技术栈标注 |

---

## 全国热力地图功能

- **ECharts 5** 渲染，`visualMap` 连续色谱（深蓝 → 青 → 绿 → 黄 → 橙 → 红）
- 31 个省区市按风险等级（高/中/低/安全）着色
- **拖拽 + 缩放**（`roam: true`）
- **8 种天气图标**随地图同步移动（`effectScatter + coordinateSystem:'geo'`）：台风 · 暴雪 · 暴雨 · 高温 · 沙尘暴 · 大风 · 洪涝 · 干旱
- 悬停省份弹出实时预警详情面板（风险等级 · 作物 · 置信度 · 推荐行动 · 最佳窗口期）

---

## 六阶段推演架构

```
外部数据源（气象/遥感/舆情/通报/影像）
      ↓
① 采集 Collector Agent   — 只搬不判，多源并行 + Manual Injection Demo 通道
      ↓
② 分析 Analyst Agents    — 气象/作物/地块/病虫害/舆情，并行输出 RiskJudgment[]
      ↓
③ 推演 Simulator Agent   — 不干预路径 vs 干预路径概率对比
      ↓
④ 决策 Decision Agent    — 输出结构化预警 JSON（plot_id/crop/risk/actions/confidence）
      ↓
⑤ 推送 Delivery Agent    — 保险API / 合作社短信 / 政府简报 / 粮企月报
      ↓
B端真实反馈
      ↓
⑥ Harness 进化 Agent     — Evaluator → Root Cause → Evolver → 写回 Agent 资产文件
      ↺ 下一轮加载直接读更新后资产
```

---

## 文件清单

```
Azgca/
├── index.html        全量单页应用（React 18 via CDN · ECharts · Tailwind · 零构建）
├── logo.png          品牌 Logo（导航栏 + 页脚）
└── README.md         本文件
```

---

## 技术栈

| 层 | 技术 |
|---|---|
| UI 框架 | React 18（CDN，Babel 转译） |
| 样式 | Tailwind CSS（CDN）+ 内联 CSS 变量 |
| 地图 | ECharts 5 + china.js |
| 字体 | Noto Serif SC · Cormorant Garamond · Ma Shan Zheng · JetBrains Mono |
| 图标 | 内联 SVG（Lucide 风格） |
| 构建 | ❌ 无 |
| 后端 | ❌ 无 |
| 依赖 | ❌ 无（仅 CDN） |

---

## 设计语言

**主色（绿调宣纸 · 传统水墨）**
```
纸色   #edf4ec     墨深   #1a1714     印章   #b8302a
石青   #2a6e96     石绿   #5e8466     描金   #b88f4e
```

**地图色（深海蓝科技风）**
```
底色   #040e1e     省界   rgba(0,200,255,0.35)
热力   深蓝 → 青 → 绿 → 黄绿 → 橙 → 红
```

---

## 不需要

- ❌ Node / npm / 任何 build 工具
- ❌ API Key
- ❌ 后端 / 数据库
- ❌ Python 包（只用标准库 `http.server`）

---

## License

MIT
