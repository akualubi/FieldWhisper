/* ============================================================================
   ChronoMirror · 史鉴 · Historical RAG Q&A Showcase · interaction layer v2
   ============================================================================ */

(() => {
'use strict';

// ============================================================================
// 1. Data
// ============================================================================

// 8 historical Q&A scenarios. The schema mirrors the original painting schema
// so the existing render pipeline keeps working — but semantics now map to:
//   title    →  问题 (the user-facing historical question)
//   titleEn  →  English rendition of the question
//   artist   →  涉及人物 / 史料出处
//   dynasty  →  朝代 / 时期
//   tags     →  题型标签
//   va[0]    →  事实型(-1) ↔ 推理型(+1)
//   va[1]    →  纯文本(-1) ↔ 多模态(+1)
//   rag      →  Top-3 检索到的史料片段
//   mode     →  'text' 纯文本题 / 'image' 多模态题图题
//   excerpt  →  纯文本题在题面卡上展示的代表性史料引文
//   file     →  多模态题图文件名（assets/paintings/ 下）
const PAINTINGS = [
  {
    id: 'p1', mode: 'text', file: '',
    title: '安史之乱的根本原因？', titleEn: 'What were the root causes of the An Lushan Rebellion?',
    artist: '《资治通鉴 · 卷二一七》',
    dynasty: '唐 · Tang', dynKey: '唐',
    tags: ['因果推理', '纯文本', '中等难度'],
    excerpt: '「安禄山潜豋十余年，兼范阳、平卢、河东三镇节度使，掌兵十八万余，根本动摇于内。」',
    va: [0.35, -0.55],
    rag: [
      { score: 0.42, text: '《新唐书 · 兵志》载：天宝以来节度使权重，安禄山兼范阳、平卢、河东三镇，掌兵十八万余，根本动摇于内。' },
      { score: 0.39, text: '开元盛世后期土地兼并加剧，府兵制崩坏，募兵制下藩镇兵将私属化，朝廷难以节制。' },
      { score: 0.36, text: '李林甫、杨国忠权斗及"重用蕃将"政策直接为安禄山起兵创造了条件，是政治制度性失衡的爆点。' },
    ],
  },
  {
    id: 'p2', mode: 'image', file: 'p2_houmuwu_ding.jpg',
    title: '图中这件青铜器属于哪个朝代？', titleEn: 'Which dynasty does this bronze vessel belong to?',
    artist: '题图：后母戊鼎（国家博物馆藏）',
    dynasty: '商 · Shang', dynKey: '商',
    tags: ['文物鉴定', '多模态', '考古学'],
    va: [-0.45, 0.65],
    rag: [
      { score: 0.51, text: '后母戊鼎（旧称司母戊鼎）为商代后期王室祭祀重器，1939 年河南安阳武官村出土，现藏国家博物馆。' },
      { score: 0.44, text: '商代铜器以饕餮纹、云雷纹为主要装饰，方鼎多为礼器；后母戊鼎重 832.84 公斤，是迄今出土最大青铜礼器。' },
      { score: 0.39, text: '铭文"后母戊"指商王祖庚或祖甲为其母"戊"所铸祭器，断代依据为铭文字体与纹饰风格。' },
    ],
  },
  {
    id: 'p3', mode: 'text', file: '',
    title: '王安石变法为何最终失败？', titleEn: 'Why did Wang Anshi\'s reforms ultimately fail?',
    artist: '《宋史 · 王安石传》',
    dynasty: '北宋 · N. Song', dynKey: '宋',
    tags: ['综合推理', '纯文本', '高难度'],
    excerpt: '「熙宁二年，安石参知政事，市易、青苗、免役诸法相继而出。天下讛讚，鬘鬘不能安。」',
    va: [0.62, -0.40],
    rag: [
      { score: 0.48, text: '熙宁变法（1069）推行青苗、免役、市易等法，意在富国强兵，但官吏执行中强行配贷，扰民甚于救民。' },
      { score: 0.43, text: '司马光为首的旧党与变法派围绕"祖宗之法"激烈党争，神宗去世后高太后听政尽废新法（元祐更化）。' },
      { score: 0.38, text: '钱穆《国史大纲》指出：王安石的改革缺乏足够基层吏治支撑，"立法之意虽善，行法之吏未善"。' },
    ],
  },
  {
    id: 'p4', mode: 'text', file: '',
    title: '科举制是何时正式确立的？', titleEn: 'When was the imperial examination system formally established?',
    artist: '《通典 · 选举志》',
    dynasty: '隋-唐 · Sui-Tang', dynKey: '隋唐',
    tags: ['史实考据', '纯文本', '简单'],
    excerpt: '「炀皇大业二年，始建进士科，以试策取士。自是以后，天下以文章进身。」',
    va: [-0.70, -0.55],
    rag: [
      { score: 0.55, text: '隋炀帝大业二年（606）始置进士科，以试策取士，标志着科举制度正式确立，结束了九品中正制。' },
      { score: 0.47, text: '唐代完善常科（明经、进士）与制科，进士科尤重诗赋；武则天创殿试，开后世皇帝亲试之先河。' },
      { score: 0.41, text: '邓嗣禹《中国考试制度史》：科举制延续 1300 年，至清光绪三十一年（1905）废止，是中古选官制度的核心。' },
    ],
  },
  {
    id: 'p5', mode: 'image', file: 'p5_battle_red_cliffs_map.jpg',
    title: '请识别这幅地图所反映的历史时期与战役', titleEn: 'Identify the era and battle depicted in this historical map.',
    artist: '题图：赤壁之战军势示意图',
    dynasty: '东汉末 · Late E. Han', dynKey: '汉',
    tags: ['图像识别', '多模态', '军事史'],
    va: [0.20, 0.70],
    rag: [
      { score: 0.49, text: '赤壁之战（208 年冬）发生于建安十三年，孙刘联军于长江赤壁段以火攻大破曹军，奠定三国鼎立基础。' },
      { score: 0.42, text: '《三国志 · 周瑜传》载黄盖诈降以火船冲曹军连环战船，加之北军水土不服疫病流行，曹操败走华容道。' },
      { score: 0.37, text: '陈寅恪指出，赤壁地理位置历来有蒲圻、黄州二说，主流考证倾向今湖北赤壁市。' },
    ],
  },
  {
    id: 'p6', mode: 'text', file: '',
    title: '丝绸之路的开通对中外交流有何影响？', titleEn: 'What impact did the opening of the Silk Road have on East-West exchange?',
    artist: '《史记 · 大宛列传》',
    dynasty: '西汉 · W. Han', dynKey: '汉',
    tags: ['综合分析', '纯文本', '文明交流'],
    excerpt: '「张騫凿空，西域之道始通。使者相望于道，一辈大者数百，少者百余人。」',
    va: [0.45, 0.50],
    rag: [
      { score: 0.50, text: '汉武帝建元三年（前 138）张骞出使大月氏，凿空西域；元狩四年（前 119）再使乌孙，正式打通陆上丝路。' },
      { score: 0.44, text: '丝绸、漆器、铸铁技术西传，葡萄、苜蓿、汗血马及佛教、祆教、摩尼教东传，开启欧亚大陆物质与思想双向流动。' },
      { score: 0.38, text: '季羡林《中印文化交流史》强调：丝路不仅是商道，更是宗教、艺术、医学、天文知识的输送动脉。' },
    ],
  },
  {
    id: 'p7', mode: 'text', file: '',
    title: '辛亥革命的历史意义是什么？', titleEn: 'What is the historical significance of the 1911 Revolution?',
    artist: '《孙中山选集 · 临时大总统宣言书》',
    dynasty: '清末民初 · 1911', dynKey: '近代',
    tags: ['综合评价', '纯文本', '近代史'],
    excerpt: '「国家之本在于人民，合汉、满、蒙、回、藏诸地为一国，即合汉、满、蒙、回、藏诸族为一人。」',
    va: [0.75, -0.30],
    rag: [
      { score: 0.46, text: '辛亥革命推翻清王朝，结束中国两千余年君主专制，于 1912 年 1 月 1 日建立中华民国，为亚洲第一个共和国。' },
      { score: 0.41, text: '革命未完成反帝反封建任务：袁世凯窃取果实，"二次革命"失败显示资产阶级革命派的局限性。' },
      { score: 0.36, text: '陈旭麓《近代中国社会的新陈代谢》：辛亥的最大意义在于把"民主共和"观念深植国人心中，使复辟成为不可能。' },
    ],
  },
  {
    id: 'p8', mode: 'image', file: 'p8_zhangheng_seismograph.jpg',
    title: '图中这位人物是谁？他有何主要贡献？', titleEn: 'Who is the figure in the image, and what are his major contributions?',
    artist: '题图：张衡像与候风地动仪',
    dynasty: '东汉 · E. Han', dynKey: '汉',
    tags: ['人物识别', '多模态', '科技史'],
    va: [-0.10, 0.55],
    rag: [
      { score: 0.53, text: '张衡（78–139），南阳西鄂人，东汉天文学家、数学家、文学家，曾任太史令。著《灵宪》《浑天仪图注》。' },
      { score: 0.45, text: '阳嘉元年（132）造候风地动仪，能测千里之外地震方位，是世界上最早的地震仪；浑天仪以漏壶水力驱动。' },
      { score: 0.39, text: '李约瑟《中国科学技术史》评：张衡的浑天说（"浑天如鸡子"）领先西方地心宇宙论数百年。' },
    ],
  },
];

const MODULES = [
  { id: 'M1', cn: '多模态问题编码', en: 'Multimodal Question Encoder',
    cat: 'perception',
    desc: 'Qwen2.5-VL 视觉编码 + BGE-M3 中英双语文本编码 + 题面元数据（朝代/人物）哈希嵌入。',
    stat: '768d · 754 LOC', lc: '754 LOC', fc: '3 figs',
    sig: { type: 'formula', html: `<div>q = σ(&nbsp;<em class="var-img">W<sub>v</sub>·e<sub>img</sub></em><span class="op">+</span><em class="var-txt">W<sub>t</sub>·e<sub>txt</sub></em><span class="op">+</span><em class="var-meta">W<sub>m</sub>·e<sub>meta</sub></em><span class="op">+ b</span>&nbsp;)</div>` },
    figs: ['M1_fig_modality_norms.png','M1_fig_similarity_heatmap.png','M1_fig_fusion_diagram.png'] },

  { id: 'M2', cn: '题型分类', en: 'Question Typing',
    cat: 'perception',
    desc: 'MLP 768 → 256 → 2 把问题向量映到「事实↔推理 × 文本↔多模态」二维空间；交叉熵 + 对比学习联合监督。',
    stat: '8 sectors · 621 LOC', lc: '621 LOC', fc: '3 figs',
    sig: { type: 'svg', html: `
      <svg viewBox="0 0 200 64" class="mc-illust" preserveAspectRatio="xMidYMid meet">
        <g transform="translate(100,32)">
          <circle r="28" fill="none" stroke="currentColor" stroke-width="1"/>
          <line x1="-28" y1="0" x2="28" y2="0" stroke="currentColor" stroke-width="0.5" opacity="0.45"/>
          <line x1="0" y1="-28" x2="0" y2="28" stroke="currentColor" stroke-width="0.5" opacity="0.45"/>
          <path d="M0,0 L28,0 A28,28 0 0,1 0,28 Z" fill="#b88f4e" opacity="0.18"/>
          <path d="M0,0 L0,28 A28,28 0 0,1 -28,0 Z" fill="#2a6e96" opacity="0.18"/>
          <path d="M0,0 L-28,0 A28,28 0 0,1 0,-28 Z" fill="#b8302a" opacity="0.18"/>
          <path d="M0,0 L0,-28 A28,28 0 0,1 28,0 Z" fill="#5e8466" opacity="0.18"/>
          <g class="m2-orbit"><circle cx="0" cy="0" r="3.5" fill="#b8302a"/><circle cx="0" cy="0" r="1.4" fill="#fff"/></g>
        </g>
        <text x="14" y="10" font-size="8" font-family="Cormorant Garamond" font-style="italic" fill="currentColor" opacity="0.7">arousal+</text>
        <text x="14" y="60" font-size="8" font-family="Cormorant Garamond" font-style="italic" fill="currentColor" opacity="0.7">arousal−</text>
        <text x="155" y="38" font-size="8" font-family="Cormorant Garamond" font-style="italic" fill="currentColor" opacity="0.7">val+</text>
      </svg>` },
    figs: ['M2_fig_circumplex.png','M2_fig_word_distribution.png','M2_fig_loss_components.png'] },

  { id: 'M3', cn: '历史知识检索', en: 'Historical RAG',
    cat: 'perception',
    desc: '平台 HTTP API 提供检索服务，BGE-M3 + FAISS 双索引；语料涵盖二十四史、地方志、学术文献共 1,129 chunks。',
    stat: '1,129 chunks', lc: '1,214 LOC', fc: '3 figs',
    sig: { type: 'snippet', html: `
      <div class="row"><span><span class="k">0.51</span>&nbsp; 《新唐书 · 兵志》节度使条</span></div>
      <div class="row"><span><span class="k">0.47</span>&nbsp; 《通典 · 选举志》</span></div>
      <div class="row"><span><span class="k">0.41</span>&nbsp; 邓嗣禹 · 考试制度史</span></div>` },
    figs: ['M3_fig_retrieval_scores.png','M3_fig_corpus_pca.png','M3_fig_query_pipeline.png'] },

  { id: 'M4', cn: '答案生成', en: 'Qwen2.5-VL Generator',
    cat: 'generation',
    desc: 'Qwen2.5-7B-VL 基座 + 检索片段拼装上下文；接受图文混合输入与 Top-k 检索结果，输出带引用的历史问答。',
    stat: '7B params · 677 LOC', lc: '677 LOC', fc: '3 figs',
    sig: { type: 'svg', html: `
      <svg viewBox="0 0 200 64" class="mc-illust m4-svg" preserveAspectRatio="xMidYMid meet">
        <g class="m4-bars" fill="currentColor">
          ${Array.from({length: 26}, (_, i) => {
            const x = 8 + i * 7.3;
            const h = 8 + Math.abs(Math.sin(i * 0.7) + Math.sin(i * 0.31)) * 18;
            const y = 32 - h/2;
            return `<rect x="${x}" y="${y}" width="3.2" height="${h}" rx="1"/>`;
          }).join('')}
        </g>
      </svg>` },
    figs: ['M4_fig_decoding_params.png','M4_fig_answer_length.png','M4_fig_generation_example.png'] },

  { id: 'M5', cn: '答案精修', en: 'Answer Refining',
    cat: 'interaction',
    desc: '检索结果重排（Cohere/BGE rerank）+ 引用校验 + 长上下文压缩 + 幻觉过滤。',
    stat: '4 ops · 753 LOC', lc: '753 LOC', fc: '3 figs',
    sig: { type: 'snippet', html: `
      <div class="row"><span><span class="k">refine_ops</span> = [</span></div>
      <div class="row" style="padding-left: 14px"><span><span class="s">'rerank'</span>,&nbsp; <span class="s">'cite-check'</span>,</span></div>
      <div class="row" style="padding-left: 14px"><span><span class="s">'ctx-compress'</span>,&nbsp; <span class="s">'halu-filter'</span></span></div>
      <div class="row"><span>]&nbsp;&nbsp;<span class="k">→</span> <span class="n">+9.4%</span> EM</span></div>` },
    figs: ['M5_fig_rerank_gain.png','M5_fig_citation_check.png','M5_fig_halu_filter.png'] },

  { id: 'M6', cn: 'Prompt 翻译', en: 'Prompt Engineering',
    cat: 'interaction',
    desc: '把用户口语化问题改写为结构化检索 query + 受控生成模板；支持 Zero-shot / CoT / ReAct 三档。',
    stat: '8 slots · 967 LOC', lc: '967 LOC', fc: '3 figs',
    sig: { type: 'snippet', html: `
      <div class="row"><span><span class="s">"安史之乱怎么回事"</span><span class="arrow">→</span><span class="k">query</span></span></div>
      <div class="row"><span><span class="s">"分析原因"</span><span class="arrow">→</span><span class="k">template</span>: <span class="s">'CoT'</span></span></div>
      <div class="row"><span><span class="s">"看图答"</span><span class="arrow">→</span><span class="k">VL</span>: enabled</span></div>` },
    figs: ['M6_fig_prompt_table.png','M6_fig_slot_heatmap.png','M6_fig_pipeline.png'] },

  { id: 'M7', cn: '多轮对话', en: 'Multi-turn Dialog',
    cat: 'interaction',
    desc: '会话记忆 + 跨轮指代消解 + 渐进式检索（多轮 retrieval）；支持「请再展开」类追问。',
    stat: 'r=0.957 · 757 LOC', lc: '757 LOC', fc: '3 figs',
    sig: { type: 'svg', html: `
      <svg viewBox="0 0 200 64" class="mc-illust" preserveAspectRatio="xMidYMid meet">
        <line x1="6" y1="56" x2="194" y2="56" stroke="currentColor" stroke-width="0.4" opacity="0.4"/>
        <line x1="6" y1="32" x2="194" y2="32" stroke="currentColor" stroke-width="0.3" opacity="0.18" stroke-dasharray="2 3"/>
        <path class="m7-curve" d="M6,42 Q 28,12 50,28 T 90,18 T 130,30 T 170,16 T 194,24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        <g fill="currentColor">
          <circle cx="6" cy="42" r="1.6"/>
          <circle cx="50" cy="28" r="1.6"/>
          <circle cx="90" cy="18" r="1.6"/>
          <circle cx="130" cy="30" r="1.6"/>
          <circle cx="170" cy="16" r="1.6"/>
        </g>
        <text x="180" y="56" font-size="7" font-family="JetBrains Mono" fill="currentColor" opacity="0.6">A major</text>
      </svg>` },
    figs: ['M7_fig_turn_flow.png','M7_fig_context_window.png','M7_fig_coreference.png'] },

  { id: 'M8', cn: '前后端', en: 'Frontend + Backend',
    cat: 'interface',
    desc: 'FastAPI 8 端点 + SSE 流式推送；React + TypeScript 前端；接入平台检索 API（学号 = API Key）。',
    stat: '8 endpoints · 1.1k LOC', lc: '1,105 LOC', fc: '3 figs',
    sig: { type: 'snippet', html: `
      <div class="row"><span><span class="k">POST</span> /ask</span><span style="opacity:0.5">image + text</span></div>
      <div class="row"><span><span class="k">POST</span> /retrieve</span><span style="opacity:0.5">chunks json</span></div>
      <div class="row"><span><span class="k">POST</span> /generate</span><span style="opacity:0.5">answer + cite</span></div>
      <div class="row"><span><span class="k">SSE</span>&nbsp;&nbsp; /stream</span><span style="opacity:0.5">token-by-token</span></div>` },
    figs: ['M8_fig_system_arch.png','M8_fig_endpoint_flow.png','M8_fig_va_panel_mockup.png'] },

  { id: 'M9', cn: '评测', en: 'Evaluation',
    cat: 'evaluation',
    desc: 'EM / F1 / BLEU + 检索 Recall@k + 引用一致性 + 人评 5 档 Likert + Qwen-Judge 自动评分。',
    stat: '5 dims · 1.1k LOC', lc: '1,077 LOC', fc: '3 figs',
    sig: { type: 'svg', html: `
      <svg viewBox="0 0 200 64" class="mc-illust" preserveAspectRatio="xMidYMid meet">
        <line x1="6" y1="56" x2="194" y2="56" stroke="currentColor" stroke-width="0.4" opacity="0.5"/>
        <g class="m9-bar"><rect x="16" y="14" width="14" height="42" rx="1.5" fill="currentColor" opacity="0.95"/></g>
        <g class="m9-bar"><rect x="42" y="22" width="14" height="34" rx="1.5" fill="currentColor" opacity="0.85"/></g>
        <g class="m9-bar"><rect x="68" y="10" width="14" height="46" rx="1.5" fill="currentColor" opacity="0.92"/></g>
        <g class="m9-bar"><rect x="94" y="20" width="14" height="36" rx="1.5" fill="currentColor" opacity="0.78"/></g>
        <g class="m9-bar"><rect x="120" y="16" width="14" height="40" rx="1.5" fill="currentColor" opacity="0.88"/></g>
        <text x="23" y="11" font-size="6.5" font-family="JetBrains Mono" fill="currentColor" text-anchor="middle">VA</text>
        <text x="49" y="19" font-size="6.5" font-family="JetBrains Mono" fill="currentColor" text-anchor="middle">FAD</text>
        <text x="75" y="7" font-size="6.5" font-family="JetBrains Mono" fill="currentColor" text-anchor="middle">cult</text>
        <text x="101" y="17" font-size="6.5" font-family="JetBrains Mono" fill="currentColor" text-anchor="middle">qual</text>
        <text x="127" y="13" font-size="6.5" font-family="JetBrains Mono" fill="currentColor" text-anchor="middle">pref</text>
        <text x="170" y="34" font-size="9" font-family="Cormorant Garamond" font-style="italic" fill="currentColor" opacity="0.7">A &gt; B,C</text>
      </svg>` },
    figs: ['M9_fig_human_rating.png','M9_fig_va_consistency_scatter.png','M9_fig_metric_summary.png'] },
];

// ============================================================================
// 2. V-A → word + descriptors (mirrors M2 + M6)
// ============================================================================

// 把 (factual↔inferential, text↔multimodal) 二维坐标映射为题型标签词
// X = valence (factual-, inferential+),  Y = arousal (text-, multimodal+)
function vaToWord(v, a) {
  const r = Math.hypot(v, a);
  if (r < 0.15) return '综合题';
  const theta = Math.atan2(a, v);
  const sectors = [
    { lo: -Math.PI/8,        hi:  Math.PI/8,        word: '因果推理' },   // 推理 + 文本
    { lo:  Math.PI/8,        hi:  3*Math.PI/8,      word: '综合分析' },   // 推理 + 多模态
    { lo:  3*Math.PI/8,      hi:  5*Math.PI/8,      word: '图像识别' },   // 中性 + 多模态
    { lo:  5*Math.PI/8,      hi:  7*Math.PI/8,      word: '文物鉴定' },   // 事实 + 多模态
    { lo:  7*Math.PI/8,      hi:  Math.PI + 1e-3,   word: '史实考据' },   // 事实 + 文本
    { lo: -Math.PI - 1e-3,   hi: -7*Math.PI/8,      word: '史实考据' },
    { lo: -7*Math.PI/8,      hi: -5*Math.PI/8,      word: '年代判定' },
    { lo: -5*Math.PI/8,      hi: -3*Math.PI/8,      word: '人物识别' },
    { lo: -3*Math.PI/8,      hi: -Math.PI/8,        word: '综合评价' },
  ];
  for (const s of sectors) if (theta >= s.lo && theta < s.hi) return s.word;
  return '综合题';
}

// 引用来源池（按象限）：题型 → 主要史料类别
const INSTRUMENTS_BY_QUADRANT = {
  'pp': ['正史', '考古报告'],   // 推理 + 多模态
  'pn': ['正史', '私家著述'],   // 推理 + 文本
  'np': ['图录', '博物馆志'],   // 事实 + 多模态
  'nn': ['正史', '类书'],       // 事实 + 文本
};

// 把 (题型, 多模态强度) 二维坐标映射为 8 项 RAG/生成参数
// a 轴 (多模态强度) 影响：top_k、context_len、decoding
// v 轴 (推理程度)   影响：prompt 模板、temperature、rerank
function vaToDescriptors(v, a) {
  // top_k：多模态强 → 检索更多片段以覆盖图文证据
  const tempo =
    a >  0.45 ? 'k=12' :
    a >  0.15 ? 'k=8' :
    a > -0.15 ? 'k=5' :
    a > -0.45 ? 'k=3' : 'k=2';
  // temperature：推理型 → 略高 T 鼓励发散
  const dynamics =
    v < -0.55 ? 'T=0.1' :
    v < -0.25 ? 'T=0.2' :
    v <  0.05 ? 'T=0.3' :
    v <  0.35 ? 'T=0.5' :
    v <  0.65 ? 'T=0.7' : 'T=0.9';
  // context_len：多模态/复杂题 → 长上下文
  const texture =
    a < -0.25 ? 'ctx=2k' :
    a >  0.25 ? 'ctx=8k' : 'ctx=4k';
  // decoding：多模态 → beam，纯文本 → greedy
  const articulation = a > 0.3 ? 'beam=4' : 'greedy';
  // prompt 模板：推理型 → CoT，事实型 → zero-shot
  const register =
    v < -0.3 ? 'zero-shot' :
    v >  0.3 ? 'CoT'      : 'few-shot';
  // rerank：复杂问题启用
  const meter = Math.abs(v) > 0.45 ? 'BGE-rerank' : 'none';
  // retriever：根据题型选择
  let mode;
  if (v < -0.25) mode = 'dense (BGE-M3)';
  else if (v > 0.25) mode = 'hybrid';
  else mode = 'sparse (BM25)';
  // 引用来源
  const quad = (v >= 0 ? 'p' : 'n') + (a >= 0 ? 'p' : 'n');
  const instrumentation = INSTRUMENTS_BY_QUADRANT[quad];
  return { tempo, mode, meter, register, texture, dynamics, articulation, instrumentation };
}

// ============================================================================
// 3. DOM helpers
// ============================================================================

const $  = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => Array.from(root.querySelectorAll(s));

// ============================================================================
// 4. Nav scroll state
// ============================================================================

const nav = $('#nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 60);
});

// ============================================================================
// 5. IntersectionObserver — fade-in + stagger + counter
// ============================================================================

const observer = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      if (e.target.dataset.count) animateCount(e.target, parseInt(e.target.dataset.count, 10));
      if (e.target.classList.contains('number-cell'))
        $$('[data-count]', e.target).forEach(el => animateCount(el, parseInt(el.dataset.count, 10)));
      observer.unobserve(e.target);
    }
  }
}, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

$$('.fade-in, .stagger, [data-count], .number-cell, .pipeline, .section-head').forEach(el => observer.observe(el));

function animateCount(el, target) {
  const dur = 1400;
  const start = performance.now();
  const sup = el.querySelector('sup');
  const supHtml = sup ? sup.outerHTML : '';
  function step(now) {
    const t = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - t, 3);
    const val = Math.round(target * eased);
    el.innerHTML = val.toLocaleString() + supHtml;
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ============================================================================
// 6. Hero painting rotation + Ken Burns
// ============================================================================

const HERO_ROTATION = ['p1', 'p2', 'p6', 'p8']; // mix of text + image
const heroStack = $('#hero-painting-stack');
const heroCapTitle = $('#hero-caption-title');
const heroCapMeta = $('#hero-caption-meta');

HERO_ROTATION.forEach((pid, i) => {
  const p = PAINTINGS.find(x => x.id === pid);
  if (!p) return;
  const layer = document.createElement('div');
  layer.className = 'hero-layer' + (i === 0 ? ' active' : '');
  layer.dataset.pid = pid;
  if (p.mode === 'image') {
    const im = document.createElement('img');
    im.src = `assets/paintings/${p.file}`;
    im.alt = p.titleEn;
    layer.appendChild(im);
  } else {
    layer.classList.add('mode-text');
    layer.innerHTML = `
      <div class="text-scroll hero-scroll">
        <div class="ts-mark">問</div>
        <div class="ts-question">${p.title}</div>
        <div class="ts-rule"></div>
        <div class="ts-excerpt">${p.excerpt || ''}</div>
        <div class="ts-source">${p.artist}</div>
      </div>`;
  }
  heroStack.appendChild(layer);
});

let heroIndex = 0;
const heroLayers = $$('.hero-layer', heroStack);
function rotateHero() {
  heroLayers[heroIndex].classList.remove('active');
  heroIndex = (heroIndex + 1) % heroLayers.length;
  heroLayers[heroIndex].classList.add('active');
  const pid = heroLayers[heroIndex].dataset.pid;
  const p = PAINTINGS.find(x => x.id === pid);
  if (p) {
    heroCapTitle.textContent = p.title.replace(/[？?]$/, '');
    heroCapMeta.textContent = `${p.artist.replace(/^题图：/, '')} · ${p.dynasty.split(' · ')[0]}`;
  }
}
setInterval(rotateHero, 7200);
// initial caption
(function initHeroCaption(){
  const p = PAINTINGS.find(x => x.id === HERO_ROTATION[0]);
  if (p) {
    heroCapTitle.textContent = p.title.replace(/[？?]$/, '');
    heroCapMeta.textContent = `${p.artist.replace(/^题图：/, '')} · ${p.dynasty.split(' · ')[0]}`;
  }
})();

// ============================================================================
// 7. Painting picker + thumbs + V-A dots on circumplex
// ============================================================================

let currentPainting = PAINTINGS[0]; // boot with first text-mode question
let currentVA = [...currentPainting.va];
let userDraggedFar = false;

// Build thumbs
const thumbsEl = $('#painting-thumbs');
PAINTINGS.forEach((p, i) => {
  const t = document.createElement('div');
  t.className = 'thumb' + (i === 0 ? ' active' : '');
  t.dataset.id = p.id;
  t.classList.add(p.mode === 'image' ? 'thumb-image' : 'thumb-text');
  t.innerHTML = p.mode === 'image'
    ? `<img src="assets/paintings/${p.file}" alt="${p.titleEn}">`
    : `<div class="thumb-glyph">${p.dynKey || '史'}</div>`;
  t.addEventListener('click', () => selectPainting(p.id));
  thumbsEl.appendChild(t);
});

// Build painting dots on circumplex (placed in <g id="va-dots">)
const vaDotsGroup = $('#va-dots');
const dotTip = $('#va-dot-tip');
function renderPaintingDots() {
  vaDotsGroup.innerHTML = '';
  PAINTINGS.forEach((p) => {
    const x = p.va[0] * 100;
    const y = -p.va[1] * 100;
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.classList.add('va-painting-dot');
    g.setAttribute('transform', `translate(${x},${y})`);
    g.dataset.id = p.id;
    g.innerHTML = `
      <circle class="halo" r="6" />
      <circle class="core" r="3.2" />
    `;
    g.addEventListener('mouseenter', (e) => {
      const rect = $('#va-circumplex').getBoundingClientRect();
      const svgRect = $('#va-svg').getBoundingClientRect();
      const scaleX = svgRect.width / 220;
      const scaleY = svgRect.height / 220;
      const cx = svgRect.left + (x + 110) * scaleX - rect.left;
      const cy = svgRect.top + (y + 110) * scaleY - rect.top;
      dotTip.style.left = cx + 'px';
      dotTip.style.top  = cy + 'px';
      dotTip.textContent = `${p.title} · ${p.dynKey}`;
      dotTip.classList.add('show');
    });
    g.addEventListener('mouseleave', () => dotTip.classList.remove('show'));
    g.addEventListener('click', () => selectPainting(p.id));
    vaDotsGroup.appendChild(g);
  });
  highlightActiveDot();
}
function highlightActiveDot() {
  $$('.va-painting-dot', vaDotsGroup).forEach(el => {
    el.classList.toggle('active', el.dataset.id === currentPainting.id);
  });
}

function selectPainting(id) {
  const p = PAINTINGS.find(x => x.id === id);
  if (!p) return;
  currentPainting = p;
  currentVA = [...p.va];
  userDraggedFar = false;

  // swap frame content with fade — image mode or text-scroll mode
  const frame = $('#painting-frame');
  const img = $('#painting-img');
  frame.classList.add('changing');
  setTimeout(() => {
    if (p.mode === 'image') {
      frame.classList.remove('mode-text');
      frame.classList.add('mode-image');
      img.hidden = false;
      img.src = `assets/paintings/${p.file}`;
      img.alt = p.titleEn;
    } else {
      frame.classList.remove('mode-image');
      frame.classList.add('mode-text');
      img.hidden = true;
      img.removeAttribute('src');
      $('#ts-question').textContent = p.title;
      $('#ts-excerpt').textContent = p.excerpt || '';
      $('#ts-source').textContent = p.artist;
    }
    frame.classList.remove('changing');
  }, 240);

  // meta
  $('#painting-title').textContent = p.title;
  $('#painting-sub').textContent = `${p.artist} · ${p.titleEn}`;
  const tagsEl = $('#painting-tags');
  tagsEl.innerHTML = `<span class="tag dyn">${p.dynasty}</span>` +
    p.tags.map(t => `<span class="tag">${t}</span>`).join('');

  // thumbs active
  $$('.thumb', thumbsEl).forEach(t => t.classList.toggle('active', t.dataset.id === p.id));

  // V-A pin + descriptors + word + dots
  setVA(p.va[0], p.va[1], true);
  highlightActiveDot();

  // RAG (re-render to retrigger CSS slide-in)
  renderRag(p.rag);

  // update code panel
  refreshCodePanel();
}

// ============================================================================
// 8. V-A circumplex — drag
// ============================================================================

const svg = $('#va-svg');
const pin = $('#va-pin');
const wordEl = $('#va-word');
const coordEl = $('#va-coord');
let dragging = false;

function vaToPin(v, a) {
  return { x: v * 100, y: -a * 100 };
}

function setVA(v, a, animate = false) {
  v = Math.max(-1, Math.min(1, v));
  a = Math.max(-1, Math.min(1, a));
  currentVA = [v, a];
  const { x, y } = vaToPin(v, a);
  if (animate) {
    pin.style.transition = 'transform 700ms cubic-bezier(0.4,0,0.2,1)';
    setTimeout(() => pin.style.transition = '', 800);
  } else {
    pin.style.transition = '';
  }
  pin.setAttribute('transform', `translate(${x},${y})`);
  wordEl.textContent = vaToWord(v, a);
  coordEl.textContent = `v = ${v.toFixed(2)}  ·  a = ${a.toFixed(2)}`;
  const colorMap = {
    '史实考据':'#b88f4e', '年代判定':'#b88f4e',
    '因果推理':'#5e8466', '综合分析':'#5e8466', '综合评价':'#5e8466',
    '图像识别':'#b8302a', '文物鉴定':'#b8302a',
    '人物识别':'#2a6e96', '综合题':'#2a6e96',
  };
  wordEl.style.color = colorMap[wordEl.textContent] || 'var(--ink-dark)';
  renderDescriptors(vaToDescriptors(v, a));
  refreshCodePanel();
}

function clientToVA(clientX, clientY) {
  const rect = svg.getBoundingClientRect();
  const xPct = (clientX - rect.left) / rect.width;
  const yPct = (clientY - rect.top) / rect.height;
  const v = (xPct * 2 - 1) * 1.1;
  const a = -((yPct * 2 - 1) * 1.1);
  return [
    Math.max(-1, Math.min(1, v)),
    Math.max(-1, Math.min(1, a)),
  ];
}

function startDrag(e) {
  dragging = true;
  svg.classList.add('dragging');
  moveDrag(e);
}
function moveDrag(e) {
  if (!dragging) return;
  e.preventDefault();
  const pt = e.touches ? e.touches[0] : e;
  const [v, a] = clientToVA(pt.clientX, pt.clientY);
  setVA(v, a);
  // check if user has drifted far from painting's preset
  const dx = v - currentPainting.va[0];
  const dy = a - currentPainting.va[1];
  if (Math.hypot(dx, dy) > 0.30) userDraggedFar = true;
}
function endDrag() {
  if (!dragging) return;
  dragging = false;
  svg.classList.remove('dragging');
}

// V-A drag handlers — bind on document so dragging continues outside SVG
svg.addEventListener('mousedown', startDrag);
window.addEventListener('mousemove', moveDrag);
window.addEventListener('mouseup', endDrag);
svg.addEventListener('touchstart', startDrag, { passive: false });
window.addEventListener('touchmove', moveDrag, { passive: false });
window.addEventListener('touchend', endDrag);

// ============================================================================
// 9. Regenerate button — slot pulse only
// ============================================================================

$('#btn-regen').addEventListener('click', () => {
  const btn = $('#btn-regen');
  const original = btn.textContent;
  btn.textContent = '生成中…';
  btn.disabled = true;
  $$('.slot').forEach(s => { s.classList.add('flash'); setTimeout(() => s.classList.remove('flash'), 800); });
  setTimeout(() => {
    btn.textContent = original;
    btn.disabled = false;
  }, 1100);
});

// ============================================================================
// 10. Descriptors render
// ============================================================================

function renderDescriptors(d) {
  const grid = $('#slot-grid');
  $$('.slot', grid).forEach(slot => {
    const key = $('.slot-value', slot).dataset.slot;
    const val = d[key];
    const valEl = $('.slot-value', slot);
    if (key === 'instrumentation' && Array.isArray(val)) {
      valEl.textContent = val.join(' · ');
    } else {
      valEl.textContent = val;
    }
    const isNeutral = ['k=5', 'T=0.3', 'greedy', 'few-shot', 'none', 'ctx=4k', 'sparse (BM25)'].includes(val);
    slot.classList.toggle('highlight', !isNeutral && key !== 'instrumentation');
  });
}

// ============================================================================
// 12. RAG list (re-render with CSS slide-in)
// ============================================================================

function renderRag(items) {
  const list = $('#rag-list');
  list.innerHTML = '';
  // force reflow to retrigger animation
  void list.offsetWidth;
  list.innerHTML = items.map(r => `
    <div class="rag-item">
      <span class="rag-score">${r.score.toFixed(2)}</span>${r.text}
    </div>
  `).join('');
}

// ============================================================================
// 13. Module grid + figure hover-rotation + Lightbox
// ============================================================================

const moduleGrid = $('#module-grid');
MODULES.forEach(m => {
  const card = document.createElement('div');
  card.className = `module-card cat-${m.cat}`;
  // Use the headline figure as the small thumb
  const thumbFig = m.figs[0];
  const sigClass = m.sig.type === 'formula' ? 'formula' :
                   m.sig.type === 'svg'      ? 'svg-illust' : 'snippet';
  card.innerHTML = `
    <div class="mc-head">
      <div class="mc-thumb"><img src="assets/figures/${thumbFig}" alt=""></div>
      <div class="mc-head-text">
        <span class="mc-id">${m.id} · Module</span>
        <span class="mc-en">${m.en}</span>
      </div>
    </div>
    <h4>${m.cn}</h4>
    <div class="mc-sig ${sigClass}">${m.sig.html}</div>
    <p class="mc-desc">${m.desc}</p>
    <div class="mc-foot">
      <div class="mc-figs">
        ${m.figs.map((f, i) => `<span class="mini-fig" data-fig-idx="${i}" style="background-image:url('assets/figures/${f}')"></span>`).join('')}
      </div>
      <div class="mc-stat">
        <span class="key">${m.stat}</span>
        <span class="arrow">→</span>
      </div>
    </div>
  `;

  // mini-fig click opens lightbox jumping to that figure (still uses existing lightbox)
  $$('.mini-fig', card).forEach((mf, idx) => {
    mf.addEventListener('click', (e) => {
      e.stopPropagation();
      openLightbox(m, idx);
    });
  });

  card.addEventListener('click', () => openLightbox(m));
  moduleGrid.appendChild(card);
});

const lb = $('#lightbox');
const lbClose = $('#lightbox-close');
const lbTitle = $('#lb-title');
const lbDesc = $('#lb-desc');
const lbFigs = $('#lb-figs');

function openLightbox(m, focusIdx = -1) {
  lbTitle.textContent = `${m.id} · ${m.cn} · ${m.en}`;
  lbDesc.textContent = m.desc;
  lbFigs.innerHTML = m.figs.map((f, i) =>
    `<img src="assets/figures/${f}" alt="${f}" data-i="${i}" ${i === focusIdx ? 'style="outline:3px solid var(--seal); outline-offset:2px;"' : ''}>`).join('');
  lb.classList.add('open');
  document.body.style.overflow = 'hidden';
  if (focusIdx >= 0) {
    setTimeout(() => {
      const target = lbFigs.querySelector(`[data-i="${focusIdx}"]`);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
  }
}
function closeLightbox() {
  lb.classList.remove('open');
  document.body.style.overflow = '';
}
lbClose.addEventListener('click', closeLightbox);
lb.addEventListener('click', (e) => { if (e.target === lb) closeLightbox(); });
window.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLightbox(); });

// ============================================================================
// 14. Pipeline step hover → highlight
// ============================================================================

$$('.pipe-step').forEach((s) => {
  s.addEventListener('mouseenter', () => {
    $$('.pipe-step').forEach(x => x.classList.remove('active'));
    s.classList.add('active');
  });
});

// ============================================================================
// 15. Code transparency panel — live JSON state
// ============================================================================

const codePanel = $('#code-panel');
const codeToggle = $('#code-panel-toggle');
const codePre = $('#code-panel-pre');
const codeCopy = $('#code-panel-copy');
let codeTab = 'painting';

codeToggle.addEventListener('click', () => {
  codePanel.classList.toggle('expanded');
});
$$('.code-panel-tab').forEach(t => {
  t.addEventListener('click', () => {
    codeTab = t.dataset.tab;
    $$('.code-panel-tab').forEach(x => x.classList.toggle('active', x === t));
    refreshCodePanel();
  });
});
codeCopy.addEventListener('click', () => {
  navigator.clipboard.writeText(codePre.textContent).then(() => {
    codeCopy.textContent = 'copied!';
    setTimeout(() => codeCopy.textContent = 'copy', 1400);
  });
});

function colorizeJson(obj) {
  let s = JSON.stringify(obj, null, 2);
  s = s.replace(/"([^"]+)"(\s*:)/g, '<span class="key">"$1"</span>$2');
  s = s.replace(/:\s*"([^"]+)"/g, ': <span class="str">"$1"</span>');
  s = s.replace(/:\s*(-?\d+\.?\d*)/g, ': <span class="num">$1</span>');
  s = s.replace(/:\s*(true|false|null)/g, ': <span class="bool">$1</span>');
  return s;
}

function refreshCodePanel() {
  let data;
  if (codeTab === 'painting') {
    data = {
      id: currentPainting.id,
      question: currentPainting.title,
      question_en: currentPainting.titleEn,
      source: currentPainting.artist,
      dynasty: currentPainting.dynasty,
      tags: currentPainting.tags,
      api_key: 'student_id (e.g. 2024XXXX)',
    };
  } else if (codeTab === 'va') {
    data = {
      inferential_score: parseFloat(currentVA[0].toFixed(3)),
      multimodal_score: parseFloat(currentVA[1].toFixed(3)),
      category: vaToWord(currentVA[0], currentVA[1]),
      source: 'M2 ▸ MLP(q) ▸ tanh',
      drift_from_preset: parseFloat(
        Math.hypot(currentVA[0] - currentPainting.va[0], currentVA[1] - currentPainting.va[1]).toFixed(3)
      ),
    };
  } else if (codeTab === 'descriptors') {
    data = vaToDescriptors(currentVA[0], currentVA[1]);
  } else {
    data = currentPainting.rag;
  }
  codePre.innerHTML = colorizeJson(data);
}

// ============================================================================
// 16. Concert mode — auto-tour all 8 paintings
// ============================================================================

const concertOverlay = $('#concert-overlay');
const concertBtn = $('#btn-concert');
const concertClose = $('#concert-close');
const concertFill = $('#concert-fill');
const concertIndex = $('#concert-index');
const concertTitle = $('#concert-title');
const concertSub = $('#concert-sub');
const concertVA = $('#concert-va');
const concertDesc = $('#concert-desc');
const concertPin = $('#concert-pin');
const concertImgStack = $('#concert-img-stack');

// Build concert image stack — image-mode shows photo, text-mode shows scroll card
PAINTINGS.forEach((p, i) => {
  const layer = document.createElement('div');
  layer.className = 'concert-img';
  layer.style.position = 'absolute';
  layer.style.inset = '0';
  layer.style.opacity = '0';
  layer.style.transition = 'opacity 1.2s ease';
  if (p.mode === 'image') {
    const img = document.createElement('img');
    img.src = `assets/paintings/${p.file}`;
    img.alt = p.title;
    img.style.width = '100%';
    img.style.height = '100%';
    img.style.objectFit = 'cover';
    layer.appendChild(img);
  } else {
    layer.classList.add('mode-text');
    layer.innerHTML = `
      <div class="text-scroll concert-scroll">
        <div class="ts-mark">問</div>
        <div class="ts-question">${p.title}</div>
        <div class="ts-rule"></div>
        <div class="ts-excerpt">${p.excerpt || ''}</div>
        <div class="ts-source">${p.artist}</div>
      </div>`;
  }
  if (i === 0) layer.classList.add('active');
  concertImgStack.appendChild(layer);
});

let concertTimer = null;
let concertStep = 0;
const STEP_MS = 11000;

function concertSetStep(idx) {
  concertStep = idx;
  const p = PAINTINGS[idx];
  // image swap
  $$('.concert-img', concertImgStack).forEach((img, i) => {
    img.classList.toggle('active', i === idx);
    img.style.opacity = i === idx ? '1' : '0';
  });
  // info
  concertIndex.textContent = `题 · ${idx + 1} / ${PAINTINGS.length}`;
  concertTitle.textContent = p.title;
  concertSub.textContent = `${p.artist}`;
  concertVA.innerHTML = `<span>infer = ${p.va[0].toFixed(2)}</span><span>multi = ${p.va[1].toFixed(2)}</span><span>→ ${vaToWord(p.va[0], p.va[1])}</span>`;
  concertDesc.textContent = p.rag[0].text;
  // pin
  const x = p.va[0] * 100;
  const y = -p.va[1] * 100;
  concertPin.setAttribute('transform', `translate(${x},${y})`);
  // progress bar reset
  concertFill.style.transition = 'none';
  concertFill.style.width = '0%';
  void concertFill.offsetWidth;
  concertFill.style.transition = `width ${STEP_MS}ms linear`;
  concertFill.style.width = '100%';
}

function startConcert() {
  concertOverlay.classList.add('open');
  document.body.style.overflow = 'hidden';
  concertStep = 0;
  concertSetStep(0);
  concertTimer = setInterval(() => {
    const next = (concertStep + 1) % PAINTINGS.length;
    if (next === 0) {
      stopConcert();
    } else {
      concertSetStep(next);
    }
  }, STEP_MS);
}

function stopConcert() {
  clearInterval(concertTimer);
  concertTimer = null;
  concertOverlay.classList.remove('open');
  document.body.style.overflow = '';
}

concertBtn.addEventListener('click', startConcert);
concertClose.addEventListener('click', stopConcert);
concertOverlay.addEventListener('click', (e) => {
  if (e.target === concertOverlay) stopConcert();
});
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && concertOverlay.classList.contains('open')) stopConcert();
});

// ============================================================================
// 17. Hero 3D parallax + ink-wash cursor trail
// ============================================================================

const heroEl = $('#hero');
const heroArt = $('.hero-art');
const scrollFrame = $('.hero-art .scroll-frame');
const heroTrail = $('#hero-trail');
const trailCtx = heroTrail.getContext('2d');

function fitHeroTrail() {
  const r = heroEl.getBoundingClientRect();
  heroTrail.width  = Math.max(2, Math.floor(r.width  * devicePixelRatio));
  heroTrail.height = Math.max(2, Math.floor(r.height * devicePixelRatio));
}
fitHeroTrail();
window.addEventListener('resize', fitHeroTrail);

// Tilt parallax on the scroll-frame (subtle 6deg max)
heroArt.addEventListener('mousemove', (e) => {
  const rect = heroArt.getBoundingClientRect();
  const x = (e.clientX - rect.left) / rect.width  - 0.5;
  const y = (e.clientY - rect.top)  / rect.height - 0.5;
  heroArt.classList.add('parallaxing');
  scrollFrame.style.transform =
    `perspective(1100px) rotateY(${x * 7}deg) rotateX(${-y * 7}deg) translateZ(8px)`;
});
heroArt.addEventListener('mouseleave', () => {
  heroArt.classList.remove('parallaxing');
  scrollFrame.style.transform = 'perspective(1100px) rotateY(0deg) rotateX(0deg)';
});

// Ink-wash cursor trail (only inside hero) — write a soft blot, fade entire canvas each frame
let lastBlot = { x: 0, y: 0, t: 0 };
heroEl.addEventListener('mousemove', (e) => {
  const rect = heroEl.getBoundingClientRect();
  const x = (e.clientX - rect.left) * devicePixelRatio;
  const y = (e.clientY - rect.top)  * devicePixelRatio;
  const dx = x - lastBlot.x, dy = y - lastBlot.y;
  const dist = Math.hypot(dx, dy);
  // Density limit: don't over-paint
  if (dist < 6) return;
  // Multiple soft blots along the segment for smooth trail
  const steps = Math.min(6, Math.max(1, Math.floor(dist / 14)));
  for (let i = 0; i < steps; i++) {
    const t = i / steps;
    const bx = lastBlot.x + dx * t;
    const by = lastBlot.y + dy * t;
    const r = 10 + Math.random() * 20;
    const grd = trailCtx.createRadialGradient(bx, by, 0, bx, by, r * devicePixelRatio);
    grd.addColorStop(0, 'rgba(20,17,15,0.06)');
    grd.addColorStop(1, 'rgba(20,17,15,0)');
    trailCtx.fillStyle = grd;
    trailCtx.beginPath();
    trailCtx.arc(bx, by, r * devicePixelRatio, 0, Math.PI * 2);
    trailCtx.fill();
  }
  lastBlot = { x, y, t: performance.now() };
});

// Continuous fade so the trail breathes
function fadeTrail() {
  trailCtx.fillStyle = 'rgba(245, 239, 226, 0.022)';
  trailCtx.fillRect(0, 0, heroTrail.width, heroTrail.height);
  requestAnimationFrame(fadeTrail);
}
fadeTrail();

// ============================================================================
// 18. Scroll progress
// ============================================================================

const scrollProg = $('#scroll-progress');
window.addEventListener('scroll', () => {
  const max = document.documentElement.scrollHeight - window.innerHeight;
  const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
  scrollProg.style.width = pct + '%';
});

// ============================================================================
// 19. Paintings Atlas — render grid + click → Painting Detail modal
// ============================================================================

const atlasGrid = $('#atlas-grid');
PAINTINGS.forEach((p) => {
  const card = document.createElement('div');
  card.className = 'atlas-card';
  card.dataset.id = p.id;
  const word = vaToWord(p.va[0], p.va[1]);
  card.innerHTML = `
    <div class="ac-frame">
      <div class="ac-mini-va">
        <svg viewBox="-110 -110 220 220" aria-hidden="true">
          <circle r="100" fill="none" stroke="#2a2521" stroke-width="2"/>
          <line x1="-100" y1="0" x2="100" y2="0" stroke="#a8a39e" stroke-width="0.8"/>
          <line x1="0" y1="-100" x2="0" y2="100" stroke="#a8a39e" stroke-width="0.8"/>
          <circle cx="${p.va[0] * 100}" cy="${-p.va[1] * 100}" r="14" fill="#b8302a"/>
        </svg>
      </div>
      ${p.mode === 'image'
        ? `<img src="assets/paintings/${p.file}" alt="${p.titleEn}">`
        : `<div class="text-scroll ac-scroll">
             <div class="ts-mark">問</div>
             <div class="ts-question">${p.title}</div>
             <div class="ts-rule"></div>
             <div class="ts-excerpt">${p.excerpt || ''}</div>
             <div class="ts-source">${p.artist}</div>
           </div>`}
      <div class="ac-seal"><span>史</span><span>鉴</span></div>
      <div class="ac-overlay">${p.rag[0].text}</div>
    </div>
    <div class="ac-body">
      <div class="ac-title">${p.title}</div>
      <div class="ac-artist">${p.artist}</div>
      <div class="ac-foot">
        <span class="word">${word}</span>
        <span>v=${p.va[0].toFixed(2)}</span>
        <span>a=${p.va[1].toFixed(2)}</span>
      </div>
    </div>
  `;
  card.addEventListener('click', () => openPaintingDetail(p));
  atlasGrid.appendChild(card);
});

// ============================================================================
// 20. Modal management — generic open/close
// ============================================================================

function openModal(id) {
  $('#' + id).classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeModal(id) {
  $('#' + id).classList.remove('open');
  document.body.style.overflow = '';
}
$$('[data-close]').forEach(btn => {
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    closeModal(btn.dataset.close);
  });
});
$$('.modal-overlay').forEach(m => {
  m.addEventListener('click', (e) => { if (e.target === m) closeModal(m.id); });
});
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') $$('.modal-overlay.open').forEach(m => closeModal(m.id));
});

// ============================================================================
// 21. About modal — open from nav
// ============================================================================

$('#open-about').addEventListener('click', (e) => {
  e.preventDefault();
  openModal('about-modal');
});

$('#cite-copy').addEventListener('click', () => {
  const txt = $('#bibtex-block').textContent;
  navigator.clipboard.writeText(txt).then(() => {
    $('#cite-copy').textContent = 'copied!';
    setTimeout(() => $('#cite-copy').textContent = 'copy', 1400);
  });
});

// ============================================================================
// 22. Painting Detail modal
// ============================================================================

function openPaintingDetail(p) {
  const d = vaToDescriptors(p.va[0], p.va[1]);
  const word = vaToWord(p.va[0], p.va[1]);
  const colorMap = {
    '史实考据':'#b88f4e', '年代判定':'#b88f4e',
    '因果推理':'#5e8466', '综合分析':'#5e8466', '综合评价':'#5e8466',
    '图像识别':'#b8302a', '文物鉴定':'#b8302a',
    '人物识别':'#2a6e96', '综合题':'#2a6e96',
  };
  const visualBlock = p.mode === 'image'
    ? `<div class="pd-img-wrap" data-img="assets/paintings/${p.file}" data-cap="${p.title} · ${p.artist}">
         <img src="assets/paintings/${p.file}" alt="${p.titleEn}">
         <div class="pd-seal"><span>史</span><span>鉴</span></div>
       </div>`
    : `<div class="pd-img-wrap pd-text-mode">
         <div class="text-scroll pd-scroll">
           <div class="ts-mark">問</div>
           <div class="ts-question">${p.title}</div>
           <div class="ts-rule"></div>
           <div class="ts-excerpt">${p.excerpt || ''}</div>
           <div class="ts-source">${p.artist}</div>
         </div>
         <div class="pd-seal"><span>史</span><span>鉴</span></div>
       </div>`;
  $('#pd-body').innerHTML = `
    ${visualBlock}
    <div class="pd-info">
      <h2>${p.title}</h2>
      <div class="pd-en">${p.artist} · ${p.titleEn}</div>
      <div class="pd-tags">
        <span class="tag dyn">${p.dynasty}</span>
        ${p.tags.map(t => `<span class="tag">${t}</span>`).join('')}
        <span class="tag">RAG-API · v1.0</span>
      </div>
      <div class="pd-section">
        <h4>题型坐标 · Question Type</h4>
        <div class="pd-va-row">
          <svg viewBox="-110 -110 220 220">
            <circle r="100" fill="none" stroke="#524841" stroke-width="1"/>
            <line x1="-100" y1="0" x2="100" y2="0" stroke="#a8a39e" stroke-width="0.5"/>
            <line x1="0" y1="-100" x2="0" y2="100" stroke="#a8a39e" stroke-width="0.5"/>
            <path d="M0,0 L100,0 A100,100 0 0,1 0,100 Z" fill="#b88f4e" opacity="0.16" />
            <path d="M0,0 L0,100 A100,100 0 0,1 -100,0 Z" fill="#2a6e96" opacity="0.16" />
            <path d="M0,0 L-100,0 A100,100 0 0,1 0,-100 Z" fill="#b8302a" opacity="0.16" />
            <path d="M0,0 L0,-100 A100,100 0 0,1 100,0 Z" fill="#5e8466" opacity="0.16" />
            <circle cx="${p.va[0]*100}" cy="${-p.va[1]*100}" r="11" fill="${colorMap[word] || '#b8302a'}" opacity="0.3"/>
            <circle cx="${p.va[0]*100}" cy="${-p.va[1]*100}" r="6" fill="${colorMap[word] || '#b8302a'}"/>
          </svg>
          <div class="pd-va-info">
            <div class="pd-word" style="color: ${colorMap[word] || '#14110f'};">${word}</div>
            <div class="pd-coord">infer = ${p.va[0].toFixed(2)}  ·  multi = ${p.va[1].toFixed(2)}</div>
          </div>
        </div>
      </div>
      <div class="pd-section">
        <h4>生成参数 · M5/M6 ▸ 8-slot</h4>
        <div class="pd-slots">
          ${Object.entries(d).map(([k, v]) => `
            <div class="pd-slot">
              <div class="pd-slot-label">${k}</div>
              <div class="pd-slot-value">${Array.isArray(v) ? v.join(' · ') : v}</div>
            </div>
          `).join('')}
        </div>
      </div>
      <div class="pd-section">
        <h4>检索到的历史史料 · M3 ▸ top-3 of 1129</h4>
        <div class="pd-rag-list">
          ${p.rag.map((r, i) => `
            <div class="pd-rag-item" data-rag-idx="${i}">
              <span class="pd-rag-score">${r.score.toFixed(2)}</span>${r.text}
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  // Wire up RAG item clicks → RAG modal
  $$('.pd-rag-item', $('#pd-body')).forEach(item => {
    item.addEventListener('click', () => {
      const idx = parseInt(item.dataset.ragIdx, 10);
      openRagModal(p.rag[idx]);
    });
  });

  // Image zoom (only when there's an actual image)
  if (p.mode === 'image') {
    $('.pd-img-wrap', $('#pd-body')).addEventListener('click', (e) => {
      const wrap = e.currentTarget;
      openZoom(wrap.dataset.img, wrap.dataset.cap);
    });
  }

  openModal('painting-detail-modal');
}

// ============================================================================
// 23. Image zoom modal
// ============================================================================

const zoomImg = $('#zoom-img');
const zoomCap = $('#zoom-caption');
function openZoom(src, cap) {
  zoomImg.src = src;
  zoomImg.classList.remove('zoomed');
  zoomCap.textContent = cap || '点击切换 1× / 1.6×';
  openModal('zoom-modal');
}
zoomImg.addEventListener('click', () => zoomImg.classList.toggle('zoomed'));

// case-banner image → zoom modal
const caseImgWrap = $('#case-img-wrap');
if (caseImgWrap) {
  caseImgWrap.addEventListener('click', () => {
    const img = $('img', caseImgWrap);
    openZoom(img.src, '后母戊鼎 · 多模态题例 · 商');
  });
}

// ============================================================================
// 24. RAG modal
// ============================================================================

function openRagModal(r) {
  $('#rag-modal-score').textContent = r.score.toFixed(2);
  $('#rag-modal-src').textContent = `史料语料库 chunk · cosine ${r.score.toFixed(3)}`;
  $('#rag-modal-text').textContent = r.text;
  openModal('rag-modal');
}

// Wire up demo's RAG items: click → open modal
$('#rag-list').addEventListener('click', (e) => {
  const item = e.target.closest('.rag-item');
  if (!item) return;
  // Find index from siblings
  const items = $$('.rag-item', $('#rag-list'));
  const idx = items.indexOf(item);
  if (idx >= 0 && currentPainting.rag[idx]) {
    openRagModal(currentPainting.rag[idx]);
  }
});

// Make demo rag items look clickable
const ragListStyle = document.createElement('style');
ragListStyle.textContent = `.rag-item { cursor: pointer; transition: background 200ms; }
.rag-item:hover { background: rgba(42,110,150,0.08); }`;
document.head.appendChild(ragListStyle);

// ============================================================================
// 25. Dataflow diagram — hover highlights connected edges + neighbour nodes
// ============================================================================

const dfSvg = $('#df-svg');
if (dfSvg) {
  const dfNodes = $$('.df-node', dfSvg);
  const dfEdges = $$('.df-edge', dfSvg);
  const dfLabels = $$('.df-edge-label', dfSvg);

  function dfClear() {
    dfSvg.classList.remove('has-active');
    dfNodes.forEach(n => n.classList.remove('active'));
    dfEdges.forEach(e => e.classList.remove('active'));
    dfLabels.forEach(l => l.classList.remove('active'));
  }

  function dfHighlight(id) {
    dfSvg.classList.add('has-active');
    const neighbours = new Set([id]);
    dfEdges.forEach((edge, idx) => {
      const from = edge.dataset.from, to = edge.dataset.to;
      const isMe = from === id || to === id;
      edge.classList.toggle('active', isMe);
      // matching label is the next sibling text element in the SVG;
      // we just check label position; simpler: toggle all labels by index
      if (isMe) {
        neighbours.add(from === id ? to : from);
        // Find the closest label by index
        const lbl = edge.nextElementSibling;
        if (lbl && lbl.classList && lbl.classList.contains('df-edge-label')) {
          lbl.classList.add('active');
        }
      }
    });
    dfNodes.forEach(n => n.classList.toggle('active', neighbours.has(n.dataset.id)));
  }

  dfNodes.forEach(n => {
    n.addEventListener('mouseenter', () => dfHighlight(n.dataset.id));
    n.addEventListener('mouseleave', dfClear);
    n.addEventListener('focusin', () => dfHighlight(n.dataset.id));
    n.addEventListener('focusout', dfClear);
    // click → jump to corresponding module's lightbox if it's a real module
    n.addEventListener('click', () => {
      const id = n.dataset.id.toUpperCase();
      const mod = MODULES.find(m => m.id === id);
      if (mod) openLightbox(mod);
    });
    // a11y
    n.setAttribute('tabindex', '0');
    n.setAttribute('role', 'button');
  });

  // Observe to trigger the edge-drawing animation on scroll-in
  const dfObs = new IntersectionObserver((es) => {
    es.forEach(e => { if (e.isIntersecting) {
      e.target.classList.add('visible');
      dfObs.unobserve(e.target);
    }});
  }, { threshold: 0.25 });
  dfObs.observe($('.dataflow'));
}

// ============================================================================
// 26. Init
// ============================================================================

renderPaintingDots();
selectPainting('p1');
refreshCodePanel();

})();
