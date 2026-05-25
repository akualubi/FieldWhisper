
// ================================================================
// AgriVid AI — app.js
// ================================================================

// ---- Particle System ----
(function initParticles() {
  const canvas = document.getElementById('hero-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W = 0, H = 0, particles = [], animId;

  function resize() {
    W = canvas.width = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  const COLORS = ['#00e5ff', '#00ff88', '#7c3aed', '#ff6b35'];

  function createParticle() {
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.5,
      vy: -Math.random() * 0.8 - 0.2,
      r: Math.random() * 2 + 0.5,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      alpha: Math.random() * 0.6 + 0.1,
      life: 0,
      maxLife: Math.random() * 300 + 200
    };
  }

  for (let i = 0; i < 80; i++) particles.push(createParticle());

  let mouseX = -9999, mouseY = -9999;
  canvas.addEventListener('mousemove', function(e) {
    const rect = canvas.getBoundingClientRect();
    mouseX = e.clientX - rect.left;
    mouseY = e.clientY - rect.top;
  });

  function draw() {
    ctx.clearRect(0, 0, W, H);

    // Draw connecting lines
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < 100) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = 'rgba(0,229,255,' + (1 - d / 100) * 0.08 + ')';
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    // Draw particles
    particles.forEach(function(p, idx) {
      p.life++;
      if (p.life > p.maxLife) { particles[idx] = createParticle(); return; }

      // Mouse repulsion
      const dx = p.x - mouseX;
      const dy = p.y - mouseY;
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d < 80) {
        p.vx += dx / d * 0.3;
        p.vy += dy / d * 0.3;
      }

      p.x += p.vx;
      p.y += p.vy;
      p.vx *= 0.99;
      p.vy *= 0.99;

      if (p.x < 0) p.x = W;
      if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H;
      if (p.y > H) p.y = 0;

      const progress = p.life / p.maxLife;
      const a = p.alpha * (progress < 0.1 ? progress * 10 : progress > 0.9 ? (1 - progress) * 10 : 1);

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color.replace(')', ',' + a + ')').replace('rgb', 'rgba').replace('#', 'rgba(').replace('rgba(', 'rgba(');
      
      // Hex color to rgba
      const hex = p.color.replace('#', '');
      const r = parseInt(hex.substr(0, 2), 16);
      const g = parseInt(hex.substr(2, 2), 16);
      const b = parseInt(hex.substr(4, 2), 16);
      ctx.fillStyle = 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')';
      ctx.shadowColor = p.color;
      ctx.shadowBlur = p.r * 3;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    animId = requestAnimationFrame(draw);
  }
  draw();
})();

// ---- Hero Stat Counter ----
(function initHeroStats() {
  const stats = document.querySelectorAll('.stat-num[data-target]');
  let done = false;
  function countUp() {
    if (done) return;
    done = true;
    stats.forEach(function(el) {
      const target = parseFloat(el.dataset.target);
      const isFloat = target % 1 !== 0;
      let current = 0;
      const duration = 1800;
      const startTime = performance.now();
      function update(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        current = target * eased;
        el.textContent = isFloat ? current.toFixed(1) : Math.round(current).toLocaleString();
        if (progress < 1) requestAnimationFrame(update);
        else el.textContent = isFloat ? target.toFixed(1) : target.toLocaleString();
      }
      requestAnimationFrame(update);
    });
  }
  // Start immediately on load
  window.addEventListener('load', countUp);
})();

// ---- Scroll Counter for Numbers section ----
(function initCounters() {
  const counters = document.querySelectorAll('.count-num[data-target]');
  const triggered = new Set();
  const observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (!entry.isIntersecting || triggered.has(entry.target)) return;
      triggered.add(entry.target);
      const el = entry.target;
      const target = parseFloat(el.dataset.target);
      const decimals = parseInt(el.dataset.decimal || '0');
      const duration = 2000;
      const startTime = performance.now();
      function update(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = target * eased;
        el.textContent = current.toFixed(decimals);
        if (progress < 1) requestAnimationFrame(update);
        else el.textContent = target.toFixed(decimals);
      }
      requestAnimationFrame(update);
    });
  }, { threshold: 0.5 });
  counters.forEach(function(c) { observer.observe(c); });
})();

// ---- Scroll Reveal ----
(function initReveal() {
  const els = document.querySelectorAll('.reveal');
  const observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(e) {
      if (e.isIntersecting) {
        const idx = parseInt(e.target.dataset.index || '0');
        setTimeout(function() { e.target.classList.add('visible'); }, idx * 80);
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  els.forEach(function(el) { observer.observe(el); });
})();

// ---- Nav Scroll ----
(function initNav() {
  const nav = document.getElementById('nav');
  window.addEventListener('scroll', function() {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  });
  document.getElementById('nav-toggle').addEventListener('click', function() {
    document.getElementById('nav-links').classList.toggle('open');
  });
  // Close nav on link click (mobile)
  document.querySelectorAll('.nav-links a').forEach(function(a) {
    a.addEventListener('click', function() {
      document.getElementById('nav-links').classList.remove('open');
    });
  });
})();

// ---- Demo Interactive ----
(function initDemo() {
  const PRODUCTS = {
    strawberry: { name: '草莓', emoji: '🍓', region: '浙江·建德', desc: '高糖低酸，果香浓郁，现摘现发' },
    apple:      { name: '苹果', emoji: '🍎', region: '陕西·洛川', desc: '高原苹果，日照充足，肉脆汁多' },
    honey:      { name: '蜂蜜', emoji: '🍯', region: '云南·罗平', desc: '油菜花蜜，纯天然，无添加' },
    yam:        { name: '山药', emoji: '🌿', region: '河南·焦作', desc: '铁棍山药，粉糯绵密，药食同源' },
    orange:     { name: '橙子', emoji: '🍊', region: '四川·眉山', desc: '春见柑橘，皮薄多汁，甜度爆表' },
    tea:        { name: '茶叶', emoji: '🍵', region: '云南·普洱', desc: '古树普洱，年份醇厚，口感层次丰富' },
    rice:       { name: '大米', emoji: '🌾', region: '黑龙江·五常', desc: '五常大米，粒粒饱满，米香浓郁' },
    chili:      { name: '辣椒', emoji: '🌶️', region: '湖南·邵阳', desc: '朝天椒，色泽红亮，香辣鲜爽' }
  };

  const STYLES = {
    live:     { name: '带货直播', platform: '抖音直播' },
    story:    { name: '种植故事', platform: '视频号' },
    quality:  { name: '品质溯源', platform: '淘宝直播' },
    festival: { name: '节日特卖', platform: '快手' }
  };

  const SCRIPTS = {
    strawberry: {
      live:     ['[开场] 宝宝们大家好！今天给大家带来的是浙江建德现摘草莓！', '[展示] 你看这颜色，红得发亮，果肉饱满——', '[促销] 直播间今天限量 500 单，现在下单直接享 8 折！', '[互动] 想要的宝宝扣 1，我们马上安排！'],
      story:    ['[旁白] 清晨五点，建德草莓基地的灯亮了——', '[画面] 这片草莓已经种了三年，土壤是精心配比的有机土。', '[采摘] 每颗草莓都是人工挑选，只取最红最甜的那一批。', '[感言] 希望你吃到的每一口，都是大地最真诚的馈赠。'],
      quality:  ['[溯源] 扫码可查：产地 · 采摘日期 · 农残检测报告', '[检测] 本批次农药残留检测：零检出', '[认证] 已通过绿色食品 A 级认证，放心吃！', '[发货] 冷链直发，48 小时内到达。'],
      festival: ['[节日] 🎉 端午节特惠！草莓礼盒买二送一！', '[限时] 今晚 12 点截止，错过等明年！', '[礼盒] 精美礼盒包装，适合送礼自用！', '[下单] 直接点购物车，秒杀价等你！']
    },
    apple: {
      live:     ['[开场] 老铁们好！今天直播间搬来了陕西洛川苹果！', '[展示] 海拔 1000 米以上的高原，日照 2600 小时！', '[卖点] 糖度 15 度以上，酸甜比完美——', '[促销] 5 斤装直播间价只要 29.9，快来抢！'],
      story:    ['[旁白] 黄土高原的风，吹了一百年的苹果传奇。', '[画面] 每棵苹果树都有超过 20 年树龄，根扎黄土深处。', '[采收] 10 月霜降之后，才是最佳采摘时节。', '[心愿] 一个苹果，一份来自高原的心意。'],
      quality:  ['[溯源] 洛川苹果 · 国家地理标志产品', '[土壤] 黄绵土，富含钾元素，造就独特口感', '[检测] SGS 国际认证，零农残，放心吃', '[包装] 单果独立包裹，防碰防压，新鲜到家'],
      festival: ['[春节] 新年礼盒现货！洛川苹果 "平平安安" 大礼包', '[寓意] 苹果=平安，送长辈送朋友最有心！', '[规格] 5kg/10kg 两款可选，礼盒精美', '[速抢] 年货节限量，先到先得！']
    },
    honey: {
      live:     ['[开场] 亲爱的们，今天给大家带来云南罗平油菜花蜜！', '[展示] 纯手工取蜜，零添加，看这浓稠度！', '[功效] 润肺止咳，助眠养颜，老少皆宜', '[价格] 500g 只要 49，两瓶包邮，心动就下单！'],
      story:    ['[旁白] 每年三月，罗平的山坡上开满金色油菜花。', '[蜜蜂] 300 万只蜜蜂穿梭在花海中，采集最甜的精华。', '[取蜜] 老蜂农凌晨三点就开始割蜜，只为给你最新鲜的那一批。', '[匠心] 守一片花海，酿一罐好蜜，就是这么简单。'],
      quality:  ['[成分] 100% 纯蜂蜜，不添加任何糖分和防腐剂', '[检测] 波美度 42 度以上，达到成熟蜜标准', '[认证] 有机认证 · 蜜源可溯源', '[保存] 密封避光，可保存 2 年以上'],
      festival: ['[中秋] 中秋礼盒！蜂蜜+干花茶，送健康送品味', '[套装] 三瓶装礼盒，颜值超高，朋友圈必晒', '[限量] 仅剩 200 套，今晚 0 点恢复原价', '[下单] 备注收件人姓名，送专属贺卡！']
    },
    yam: {
      live:     ['[开场] 大家好！今天带来的是焦作正宗铁棍山药！', '[对比] 你看这横截面，粉糯绵密，黏液丰富——', '[功效] 益肾健脾，增强免疫力，老人孩子都适合', '[价格] 5 斤装，产地直发，只要 35 元！'],
      story:    ['[旁白] 黄河古道的沙质土壤，孕育了千年铁棍山药的传奇。', '[种植] 每年清明栽种，立冬收获，完整生长 8 个月。', '[匠人] 老农说：铁棍山药最怕急，慢工才出细活。', '[传承] 一根山药，承载着黄河儿女的饮食记忆。'],
      quality:  ['[品质] 焦作四大怀药之首，国家地理标志', '[口感] 粉糯不烂，黏液足，蒸煮炒炸皆宜', '[检测] 土壤检测报告：铁、钙、锌含量超标准 3 倍', '[包装] 单根独立包装，防磕碰，新鲜直达'],
      festival: ['[冬至] 冬至进补，山药羊肉汤最暖！', '[礼品] 铁棍山药礼盒，送长辈的养生好礼', '[套餐] 买山药送枸杞，搭配食用效果翻倍', '[抢购] 产地直发，今日下单明日出货！']
    },
    orange: {
      live:     ['[开场] 宝宝们好！今天直播间来了四川春见！', '[外观] 你看这橙色，皮薄光亮，一剥就流汁！', '[口感] 甜度 14 度，酸度极低，吃完还想吃！', '[价格] 10 斤只要 39，邮费都我出，快下单！'],
      story:    ['[旁白] 四川眉山，中国柑橘之乡的王牌——春见。', '[生长] 岷江流域温暖湿润的气候，让每颗春见都自带蜜味。', '[采摘] 霜降后，果农们用剪刀一颗一颗手工采收。', '[分享] 一口春见，就是四川盆地最甜的春天。'],
      quality:  ['[品种] 春见 = 清见 × F2432 椪柑，混血精品', '[糖度] 糖度稳定 14 度以上，不打甜蜜素', '[检测] 农残检测报告：符合欧盟出口标准', '[保鲜] 冷链物流，新鲜保证，坏果包赔'],
      festival: ['[年货] 新年橙子礼盒！吉祥如意，大吉大利！', '[礼盒] 精品礼盒 20 枚装，红色丝带包装', '[寓意] 橙子谐音 "成功"，送礼倍有面', '[现货] 限量 1000 箱，手慢无！']
    },
    tea: {
      live:     ['[开场] 茶友们好！今天带来的是云南普洱古树茶！', '[展示] 这片叶子，来自 300 年以上的古茶树！', '[口感] 入口醇厚，回甘持久，越喝越上瘾', '[价格] 直播间专属价，买二送一，限今晚！'],
      story:    ['[旁白] 云南西双版纳的古茶园，见证了三百年风雨。', '[茶树] 这棵古茶树，胸径超过 40cm，叶芽肥厚。', '[工艺] 手工杀青、石磨压制，传统工艺不打折扣。', '[岁月] 好茶如好友，越陈越香，值得等待。'],
      quality:  ['[原料] 100% 古树春茶，拒绝台地茶混采', '[工艺] 晒青毛茶 → 拼配 → 蒸压 → 干仓存放', '[检测] 农残检测：零检出，符合有机标准', '[溯源] 扫码可见：茶园位置 + 采摘时间 + 制茶师姓名'],
      festival: ['[父亲节] 送爸爸一饼好茶，比什么都强！', '[礼盒] 357g 经典圆饼，红木礼盒，倍显档次', '[收藏] 普洱越陈越值钱，买来喝更买来存', '[限量] 本次仅 50 饼，藏家必抢！']
    },
    rice: {
      live:     ['[开场] 各位家人好！今天带来五常大米，米界爱马仕！', '[展示] 看这粒粒分明，颜色透亮，闻一下就香！', '[口感] 软糯弹牙，米香浓郁，不用配菜也能吃三碗！', '[价格] 5 斤直播价 49，现在下单今天发货！'],
      story:    ['[旁白] 松花江畔，长白山脚下，这里是五常大米的故乡。', '[气候] 年均气温 3.5 度，昼夜温差 15 度，积累天然糖分。', '[种植] 一年只种一季，180 天生长期，充分积累营养。', '[承诺] 每一粒米，都是黑土地给你最诚实的答案。'],
      quality:  ['[品种] 稻花香 2 号，原产地证明书认证', '[检测] 无农药、无化肥、无激素，三无保证', '[认证] 国家地理标志产品，正宗五常产地直发', '[溯源] 袋内附二维码，扫码查产地 + 检测报告'],
      festival: ['[中秋] 中秋礼盒！五常大米 + 长白山杂粮组合装', '[年货] 过年送大米，寓意年年有余', '[规格] 5 斤/10 斤/25 斤三种规格可选', '[团购] 10 箱起拿团购价，批发超划算！']
    },
    chili: {
      live:     ['[开场] 辣友们！今天带来湖南邵阳朝天椒！辣味正！', '[展示] 你看这颜色，红得发紫，干辣椒里的王者！', '[用途] 炒菜、做剁椒、卤味提色，样样拿手！', '[价格] 500g 只要 12.9，今天买三袋送一袋！'],
      story:    ['[旁白] 湖南邵阳，中国最辣的地方之一。', '[品种] 朝天椒，果实向天生长，吸收最多阳光和热量。', '[晾晒] 秋收后自然风干 30 天，锁住最纯粹的辣味精华。', '[传承] 一把辣椒，是湖南人骨子里的倔强与热情。'],
      quality:  ['[品种] 正宗朝天椒，辣度 5 万 SHU 以上', '[干燥] 自然风干，不添加色素，颜色纯天然', '[检测] 重金属及农残检测合格，放心入厨', '[产地] 邵阳本地直采，无中间商，品质把关'],
      festival: ['[腊味节] 腊月备货！朝天椒 + 花椒组合套装', '[年货] 自家做腊肠，少不了一把好辣椒！', '[礼品] 辣椒礼盒，送给爱吃辣的朋友', '[秒杀] 今晚 8 点！辣椒买 3 送 1，手慢无！']
    }
  };

  let currentProduct = 'strawberry';
  let currentStyle = 'live';
  let isGenerating = false;

  // Product selection
  document.querySelectorAll('.product-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.product-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      currentProduct = btn.dataset.product;
      updateProductTag();
    });
  });

  // Style selection
  document.querySelectorAll('.style-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.style-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      currentStyle = btn.dataset.style;
      updatePlatform();
    });
  });

  // Param buttons
  document.querySelectorAll('.param-btns').forEach(function(group) {
    group.querySelectorAll('.param-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        group.querySelectorAll('.param-btn').forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
      });
    });
  });

  function updateProductTag() {
    const p = PRODUCTS[currentProduct];
    document.getElementById('product-tag-text').textContent = p.emoji + ' ' + p.name;
  }

  function updatePlatform() {
    const s = STYLES[currentStyle];
    document.getElementById('vp-platform').textContent = s.platform;
  }

  function setSubtitle(text) {
    document.getElementById('subtitle-text').textContent = text;
  }

  function runGeneration() {
    if (isGenerating) return;
    isGenerating = true;
    const btn = document.getElementById('btn-generate');
    btn.disabled = true;
    btn.textContent = '生成中...';

    const progressEl = document.getElementById('vp-progress');
    progressEl.style.display = 'flex';
    const steps = document.querySelectorAll('.prog-step');
    steps.forEach(function(s) {
      s.classList.remove('active', 'done');
      s.querySelector('.prog-status').textContent = '';
    });

    const delays = [600, 1200, 900, 1500, 800];
    const labels = ['识别中...', '生成中...', '合成中...', '渲染中...', '完成！'];

    let currentStep = 0;
    function nextStep() {
      if (currentStep >= steps.length) {
        // Done
        setTimeout(function() {
          progressEl.style.display = 'none';
          showScript();
          isGenerating = false;
          btn.disabled = false;
          btn.innerHTML = '<svg viewBox="0 0 20 20" fill="none"><path d="M10 2 L12.5 7.5 L18 8.5 L14 12.5 L15 18 L10 15.5 L5 18 L6 12.5 L2 8.5 L7.5 7.5 Z" stroke="currentColor" stroke-width="1.5" fill="none"/></svg> 重新生成';
        }, 500);
        return;
      }
      steps[currentStep].classList.add('active');
      steps[currentStep].querySelector('.prog-status').textContent = labels[currentStep];
      setSubtitle(labels[currentStep]);
      setTimeout(function() {
        steps[currentStep].classList.remove('active');
        steps[currentStep].classList.add('done');
        steps[currentStep].querySelector('.prog-status').textContent = '\u2713';
        currentStep++;
        nextStep();
      }, delays[currentStep]);
    }
    nextStep();
  }

  function showScript() {
    const p = PRODUCTS[currentProduct];
    const lines = (SCRIPTS[currentProduct] && SCRIPTS[currentProduct][currentStyle]) || ['[AI 正在学习该产品数据...]'];
    const panel = document.getElementById('script-output');
    panel.className = 'script-content';
    
    let html = '<div style="margin-bottom:0.8rem;padding-bottom:0.5rem;border-bottom:1px solid rgba(0,229,255,0.15)">';
    html += '<span style="color:#00e5ff;font-family:JetBrains Mono,monospace;font-size:0.72rem">// ' + p.emoji + ' ' + p.name + ' · ' + STYLES[currentStyle].name + ' · ' + STYLES[currentStyle].platform + '</span>';
    html += '</div>';
    
    lines.forEach(function(line, i) {
      const tag = line.match(/^\[(.+?)\]/);
      if (tag) {
        html += '<div class="script-line tag">' + line.substring(0, tag[0].length) + '</div>';
        html += '<div class="script-line" style="padding-left:0.5rem;margin-bottom:0.8rem">' + line.substring(tag[0].length) + '</div>';
      } else {
        html += '<div class="script-line" style="margin-bottom:0.5rem">' + line + '</div>';
      }
    });

    html += '<div style="margin-top:1rem;padding-top:0.5rem;border-top:1px solid rgba(0,229,255,0.1)">';
    html += '<span style="color:#7a9cbf;font-size:0.72rem;font-family:JetBrains Mono,monospace">生成完成 · ' + p.region + ' · 字数约 ' + (lines.join('').length) + '字</span>';
    html += '</div>';
    panel.innerHTML = html;
    setSubtitle(lines[0].replace(/^\[.+?\]\s*/, '').substring(0, 30) + '...');
  }

  document.getElementById('btn-generate').addEventListener('click', runGeneration);
  document.getElementById('hero-demo-btn').addEventListener('click', function() {
    document.getElementById('demo').scrollIntoView({ behavior: 'smooth' });
  });
  document.getElementById('btn-start').addEventListener('click', function() {
    document.getElementById('demo').scrollIntoView({ behavior: 'smooth' });
  });

  updateProductTag();
  updatePlatform();
})();
