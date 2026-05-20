# ChronoMirror · 史鉴 · Showcase Demo

> 多模态历史问答 Agent 的精致网页演示：问题理解 → 题型分类 → 历史 RAG 检索 → Qwen2.5-VL 生成。
> 单页静态网站，**零 build · 零依赖 · 零后端**，本地起一个 http server 就能看。

---

## 启动 · 一句话

```bash
unzip chronomirror_demo.zip
cd chronomirror_demo
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

> ⚠️ **不能**直接双击 `index.html`。浏览器在 `file://` 协议下会拒绝音频/canvas 的跨源访问，导致波形和 Web Audio 实时合成失效。**必须**起本地 server。

### 换端口

```bash
python3 -m http.server 9000        # 端口 9000
```

### 停掉

```bash
pkill -f "http.server"
# 或者按住 Ctrl+C
```

### 用 Node 起（如果不喜欢 Python）

```bash
npx serve -p 8080
# 或
npx http-server -p 8080
```

---

## 浏览器要求

- **推荐**：Chrome / Edge / Safari **2024 年后** 的版本
- **完整体验需要**：
  - `animation-timeline: view()` —— 滚动驱动动画（Chrome 115+ / Safari 26+ / Firefox 137+）
  - `@property` —— CSS 自定义属性插值（Chrome 85+ / Safari 16.4+）
  - Web Audio API —— V-A 拖动实时合成（所有现代浏览器都支持）
- **老浏览器**会自动 fallback 到 IntersectionObserver 一次性 fade-in，内容完整但少了 Apple-style 的滚动跟随感

---

## 11 个 section 一览

| # | section | 内容 |
|---|---|---|
| 1 | **Hero** | 笔锋题字 · 4 题 Ken Burns 轮播 · 朱印 · 鼠标 3D parallax + 墨迹光标轨迹 |
| 2 | **引语** | "问者，问古今；答者，答有据" 大引号水印 |
| 3 | **Vision** | 项目愿景文字陈述 |
| 4 | **Pipeline · 五步问答** | 5 步骤卡片 + 4 个手绘 SVG 毛笔箭头（滚动入视时绘出）|
| 5 | **Live Demo · 展卷而问** | ⭐ 核心交互区：8 题例选择 + 可拖动题型坐标圆环 + 实时预览答案语音 + 8-slot 生成参数 + 音频播放器（6 变体）+ RAG top-3 检索 |
| 6 | **Case Study · 案例研究** | 后母戊鼎断代的完整 pipeline 4 步 trace（INPUT → ENCODER → TYPE+RAG → OUTPUT）|
| 7 | **Atlas · 题例图谱** | 8 道问题 grid，每张含 mini 题型圆环 + 史料上下文遮罩 |
| 8 | **Module Showcase · 模块陈列** | 9 卡片，每卡 = 小图标 + 公式/SVG/代码片段 + 描述 + 3 张图缩略 + 关键数字 |
| 9 | **Dataflow · 模块连接图** | 1280×680 SVG 网络图，hover 高亮进出边 + label |
| 10 | **Research Context · 研究语境** | 三栏对照：现状 / 差距 / 我们的方法 |
| 11 | **Timeline · 项目时间线** | 4 个里程碑（P1→P4）|
| 12 | **Numbers · 硬数字** | 8 个滚动入视时缓动计数 |
| 13 | **Tech Stack** | 22 个技术 pill 按视觉/检索/语言/框架/数据分色 |
| 14 | **Footer** | 团队 + 导师 + API 提示 |

外加 **6 个弹窗**：Lightbox（模块图）· About（关于）· Question Detail（题例详情）· Image Zoom（图片放大）· RAG Chunk（检索片段）· 讲解厅（自动巡演 8 题 ~96s）

---

## 关键交互

| 操作 | 触发 |
|---|---|
| 拖动题型坐标圆环上的红点 | **Web Audio 实时合成预览音**（模拟答案语音预听）；松手后离当前题例太远会自动切到最接近的答案变体 |
| 点选 8 道题例缩略图 | 题面 fade 切换、题型坐标跳到该题预设、答案语音切换、RAG 列表刷新 |
| 点选圆环上 8 个淡墨小点 | 同上（圆环上散布着 8 道问题的预设坐标）|
| 点击 atlas / 缩略图 | 打开 **Question Detail** 弹窗（全字段 + 可放大图）|
| 点击模块卡 | 打开 **Lightbox** 看该模块完整 3 张图 |
| 点击模块卡底部小缩略图 | 打开 lightbox 并 outline 高亮指定那张 |
| 点击 RAG chunk | 打开 **RAG Chunk** 弹窗看全文 + meta |
| 点击 case-study 大图 | 全屏 zoom，再点切换 1× ⇄ 1.6× |
| **顶栏 讲解厅 按钮** | 全屏自动巡演 8 题 ~96s，可 ESC 退出 |
| **顶栏 关于** | About 弹窗（项目介绍 + BibTeX 引用）|
| **右下 ⌘ 按钮** | 代码透明面板，4 标签（question/type/params/rag）实时 JSON 状态 + copy |
| 滚动到 Dataflow 后 hover 节点 | 进出边变朱砂 + 发光，其它节点淡出 |
| 模块卡 hover | 底部 3 张图缩略图 spring 弹大 |

---

## 文件清单

```
chronomirror_demo/
├── README.md            ← 本文件
├── index.html           ~1,210 行  HTML 骨架 + 内容
├── styles.css           3,589 行   样式（含 Apple-style scroll-driven 动画 + 14 处连续呼吸 + 微交互）
├── app.js               ~1,510 行  交互（拖动 / Web Audio / 计数器 / 弹窗 / 讲解厅）
└── assets/
    ├── paintings/       （预留题图目录，可放入历史文物 / 地图 / 古画拓片）
    ├── figures/         （预留模块可视化目录）
    ├── audio/           7 段 demo 音频（用作答案语音 TTS 占位）4.7 MB
    └── data/            5 个 smoke test JSON（metadata / va / descriptors / retrieved_chunks / metrics）
```

> 注：`paintings/` 与 `figures/` 默认为空。上线时可把历史问题的题图放进去，文件名需与 `app.js` 中 `PAINTINGS[*].file` 一致（变量名保留为 `PAINTINGS` 以最小化代码改动，语义已重映射为「问答题例」）。

---

## 8 道题例 · 朝代分布

| 编号 | 问题 | 出处 | 朝代 | 题型坐标 (infer, multi) | 题型 |
|---|---|---|---|---:|---|
| p1 | 安史之乱的根本原因 | 《资治通鉴》 | 唐 | (+0.35, -0.55) | 因果推理 |
| p2 | 图中青铜器朝代 (smoke test) | 后母戊鼎拓片 | 商 | (-0.45, +0.65) | 文物鉴定 |
| p3 | 王安石变法为何失败 | 《宋史》 | 北宋 | (+0.62, -0.40) | 综合推理 |
| p4 | 科举制何时确立 | 《通典》 | 隋唐 | (-0.70, -0.55) | 史实考据 |
| p5 | 识别地图中的战役 | 赤壁军势图 | 汉 | (+0.20, +0.70) | 图像识别 |
| p6 | 丝绸之路影响 | 《大宛列传》 | 西汉 | (+0.45, +0.50) | 综合分析 |
| p7 | 辛亥革命意义 | 孙中山选集 | 近代 | (+0.75, -0.30) | 综合评价 |
| p8 | 图中人物与贡献 | 张衡像 | 东汉 | (-0.10, +0.55) | 人物识别 |

题例为演示用途。题面设计参考二十四史、地方志与主流史学年鉴，检索片段代表平台 RAG API 返回的示例格式。

---

## 设计语言（中国画美学）

**配色**
```
宣纸  #f5efe2     墨色   #2a2521     朱砂   #b8302a
石青  #2a6e96     石绿   #5e8466     描金   #b88f4e
```

**字体**
- 中文 serif：Noto Serif SC（标题）+ Ma Shan Zheng（毛笔印章）
- 拉丁 serif：Cormorant Garamond（斜体）
- 无衬线：Inter（小字）+ JetBrains Mono（mono）

**动画哲学**
- 所有 scroll-driven 入场用 `animation-timeline: view()`
- 全站 easing 统一：`ease-out` / `ease-smooth` / `ease-spring` / `ease-io`
- 焦点元素带连续"呼吸"（朱印 6.5s · 墨溅 18-26s · V-A halo 2.6s · 画 Ken Burns 22s）

---

## 不需要

- ❌ Node / npm / Vite / 任何 build 工具
- ❌ 任何 API key
- ❌ 后端 / 数据库
- ❌ Python 包（只用标准库 `http.server`）
- ❌ 网络（Google Fonts 第一次会下，之后浏览器 cache；离线只是字体退化，功能完整）

---

## License

代码 · MIT；题例文本·项目原创，面向教学与评测；音频 · 原项目研究产物（作为答案语音 TTS 占位）。
