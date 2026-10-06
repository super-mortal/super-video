# HyperFrames 渲染参考（Composition 编写、动画、渲染与常用配方）

> 本文件是超级视频的渲染层参考。SKILL.md 只保留工作流骨架与硬约束；编写 composition、调动画、选渲染参数时按需查阅本文件。

## 目录

1. [初始化项目](#1-初始化项目)
2. [编写 Composition](#2-编写-composition)
3. [GSAP 动画规则](#3-gsap-动画规则)
4. [Lint 与检查](#4-lint-与检查)
5. [渲染](#5-渲染)
6. [常用配方（Recipes）](#6-常用配方recipes)
7. [转写与去背景 CLI](#7-转写与去背景-cli)
8. [长音频 BGM 工作流](#8-长音频-bgm-工作流)

---

## 1. 初始化项目

```bash
npx hyperframes init <project-name> --non-interactive
npx hyperframes init my-video --example blank
npx hyperframes init my-video --video clip.mp4        # 带已有视频
npx hyperframes init my-video --audio track.mp3       # 带已有音频
npx hyperframes init my-video --tailwind              # Tailwind v4 支持
```

可用模板：`blank`、`warm-grain`、`play-mode`、`swiss-grid`、`vignelli`、`decision-tree`、`kinetic-type`、`product-promo`、`nyt-graph`

---

## 2. 编写 Composition

Composition 就是一个 HTML 文件，根容器定义视频画布。

### 2.1 单场景示例

```html
<!doctype html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <script>window.gsap||document.write('<script src="https://unpkg.com/gsap@3.14.2/dist/gsap.min.js"><\/script>');</script>
</head>
<body>
  <div data-composition-id="main" data-start="0" data-width="1920" data-height="1080">

    <!-- 视频片段：轨道 0，0s 开始，播 10s -->
    <video id="bg-video" data-start="0" data-duration="10" data-track-index="0"
           src="background.mp4" muted playsinline></video>

    <!-- 标题叠加：轨道 1，1s 出现，持续 4s -->
    <h1 id="title" class="clip" data-start="1" data-duration="4" data-track-index="1">
      Product Launch
    </h1>

    <!-- 音频：轨道 2，0s 起 10s，音量 50% -->
    <audio data-start="0" data-duration="10" data-track-index="2"
           data-volume="0.5" src="music.wav"></audio>
  </div>

  <style>
    body { margin: 0; overflow: hidden; }
    [data-composition-id="main"] {
      width: 1920px; height: 1080px;
      position: relative; background: #000;
    }
    #title {
      position: absolute; top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      font-size: 96px; color: white; font-family: sans-serif;
    }
  </style>

  <script>
    window.__timelines = window.__timelines || {};
    const tl = gsap.timeline({ paused: true });
    tl.from("#title", { opacity: 0, y: 60, duration: 0.8, ease: "power3.out" }, 1);
    tl.to("#title", { opacity: 0, y: -40, duration: 0.5, ease: "power2.in" }, 4);
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
```

### 2.2 多场景标准骨架（软默认参考起点）

适用于 3 个以上场景、且用户未指定自定义布局的情况。用户描述了其他视觉结构（全屏转场、分屏、非线性导航、电影级视差等）时自由设计，只守硬约束 H1-H9。

```html
<!doctype html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <script>window.gsap||document.write('<script src="https://unpkg.com/gsap@3.14.2/dist/gsap.min.js"><\/script>');</script>
</head>
<body>
<div data-composition-id="main" data-start="0" data-duration="TOTAL_SECONDS"
     data-width="1920" data-height="1080">

  <!-- ===== 背景层（贯穿全片） ===== -->
  <div id="bg-layer" style="position:absolute;inset:0;z-index:0;">
    <div id="grid-bg"></div>
    <div id="particles-container"></div>
  </div>

  <!-- ===== 场景 1：开场 ===== -->
  <div id="scene-1" class="scene-wrapper" data-start="0" data-duration="4" data-track-index="1">
    <div class="scene-title" id="s1-title">
      <!-- 主标题内容 -->
    </div>
    <div class="content-area" id="s1-content">
      <!-- 场景内容：卡片、文字、数据 -->
    </div>
  </div>

  <!-- ===== 场景 2 ===== -->
  <div id="scene-2" class="scene-wrapper" data-start="4" data-duration="4" data-track-index="1">
    <div class="scene-title" id="s2-title">
      <h2>场景标题</h2>
      <p class="subtitle">副标题说明</p>
    </div>
    <div class="content-area" id="s2-cards">
      <!-- 横向卡片布局 -->
    </div>
  </div>

  <!-- ===== 场景 N：（按此模式重复） ===== -->

  <!-- ===== 音频 ===== -->
  <audio data-start="0" data-duration="TOTAL_SECONDS" data-track-index="2"
         data-volume="0.5" src="bgm.wav"></audio>
</div>

<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { margin: 0; overflow: hidden; background: #0a0a0f; font-family: "Inter", sans-serif; color: #fff; }
  [data-composition-id="main"] { width: 1920px; height: 1080px; position: relative; overflow: hidden; }

  /* ===== 场景容器 ===== */
  .scene-wrapper { position: absolute; inset: 0; opacity: 0; }

  /* ===== 标题区：固定 top 50px ===== */
  .scene-title {
    position: absolute;
    top: 50px;
    left: 0;
    width: 100%;
    text-align: center;
    z-index: 10;
  }
  .scene-title h2 { font-size: 76px; font-weight: 700; margin: 0; }
  .scene-title .subtitle { font-size: 38px; opacity: 0.7; margin-top: 8px; }

  /* ===== 内容区：固定 top 240px ===== */
  .content-area {
    position: absolute;
    top: 240px;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: 36px;
    flex-wrap: wrap;
  }
  .content-col {
    position: absolute;
    top: 240px;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 24px;
  }

  /* ===== 卡片样式 ===== */
  .glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 28px 24px;
    backdrop-filter: blur(12px);
  }
</style>

<script>
  // ===== 种子随机数（mulberry32，硬约束 H1） =====
  function mulberry32(seed) {
    return function() {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    }
  }
  const rand = mulberry32(42);

  // ===== GSAP 时间轴 =====
  window.__timelines = window.__timelines || {};
  const tl = gsap.timeline({ paused: true });
  const TOTAL = TOTAL_SECONDS;

  // --- 场景 1：0-4s ---
  tl.to("#scene-1", { opacity: 1, duration: 0.01 }, 0);
  tl.from("#s1-title", { scale: 0.5, opacity: 0, duration: 0.8, ease: "back.out(1.4)" }, 0.1);
  tl.from("#s1-content", { y: 40, opacity: 0, duration: 0.6 }, 0.5);
  tl.to("#scene-1", { opacity: 0, duration: 0.5 }, 3.4);  // 场景结束前 0.6s 退场

  // --- 场景 2：4-8s ---
  tl.to("#scene-2", { opacity: 1, duration: 0.01 }, 4);
  tl.from("#s2-title", { x: -60, opacity: 0, duration: 0.6, ease: "power2.out" }, 4.1);
  tl.from("#s2-cards .glass-card", { scale: 0.6, opacity: 0, duration: 0.5, stagger: 0.15 }, 4.4);
  tl.to("#scene-2", { opacity: 0, duration: 0.5 }, 7.4);

  // --- 场景 N：（按此模式重复） ---

  window.__timelines["main"] = tl;
</script>
</body>
</html>
```

**骨架命名约定（建议保持一致，非强制）：**
- 场景容器：`#scene-1`、`#scene-2`、… `#scene-N`
- 场景标题：`#s1-title`、`#s2-title`、… `#sN-title`
- 内容容器：`#s1-content`、`#s2-cards`、`#s3-items`、…（语义化后缀）
- 卡片元素：`.glass-card`、`.data-card`、`.app-card`（语义命名）
- 背景：`#bg-layer`、`#grid-bg`、`#particles-container`

**场景包装模式（AI 可按用户要求改用其他转场方式）：**
```javascript
// 场景入场（瞬间显示）
tl.to("#scene-N", { opacity: 1, duration: 0.01 }, SCENE_START);
// 场景内容动画
tl.from("#sN-title", { /* 入场 */ }, SCENE_START + 0.1);
tl.from("#sN-content ...", { /* 入场 */ }, SCENE_START + 0.3);
// 场景退场（结束前 0.6s）—— 末尾场景除外
tl.to("#scene-N", { opacity: 0, duration: 0.5 }, SCENE_END - 0.6);
```

### 2.3 数据属性参考

| 属性 | 必填 | 用途 |
|-----------|----------|---------|
| `data-composition-id` | 是 | composition 唯一 ID |
| `data-start` | 是 | 开始时间（秒），或片段引用（`"el-1 + 2"`） |
| `data-duration` | img/div 必填 | 持续秒数（video/audio 自动检测） |
| `data-track-index` | 是 | 轨道层（同轨片段不可重叠） |
| `data-width` / `data-height` | 根节点必填 | 画布尺寸（1920x1080 或 1080x1920） |
| `data-volume` | 否 | 音量 0-1（默认 1） |
| `data-media-start` | 否 | 源媒体裁切偏移 |
| `data-composition-src` | 否 | 外部子 composition HTML 路径 |

### 2.4 视频与音频规则

- 视频必须 `muted playsinline`——音频一律用独立 `<audio>` 元素
- 禁止调用 `video.play()` / `audio.play()`——播放由框架接管
- 禁止把 video 嵌进计时 div——用非计时 wrapper 包裹
- **长 BGM 警告**：HyperFrames 内置音频处理可能在约 32s 处截断长背景音乐（即使源音频和 `data-duration` 更长）。渲染后必须抽出音频流验证解码时长与 RMS；`volumedetect -ss 30 -t 12` 有误导性（只分析已有采样）。
- **可靠的长 BGM 工作流**：先渲染视觉视频，再用 FFmpeg 从全长 WAV 后置合成音频：
  `ffmpeg -i <任务>/render/visual_v01.mp4 -i <任务>/audio/bgm.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -t <composition_duration> -movflags +faststart <任务>/deliver/<主题>_v01.mp4`，再抽该成品的音频逐秒验证 RMS 到底。

### 2.5 内容高度预算与卡片布局（软默认）

```text
available_height = 980px - 240px = 740px
max_card_height = (available_height - (rows-1) × gap) / rows

示例：3 行，gap=24px → 每行最高 (740 - 48) / 3 = 230px ✓
示例：6 卡 2×3，gap=28px → 每行最高 (740 - 28) / 2 = 356px ✓
示例：4 个纵向条目，gap=18px → 每个最高 (740 - 54) / 4 = 171px ✓
```

内容高度超过可用高度（溢出风险）时的修复顺序：
1. 缩卡片内边距（28px → 20px）
2. 缩间距（36px → 24px → 18px）
3. 缩卡片内图标/文字
4. 拆成两个连续场景

| 布局类型 | 卡片宽度 | 最大间距 | 容器宽度 |
|-------------|-----------|---------|-----------------|
| 3 卡横排 | 360-480px | 36px | 90% (1728px) |
| 4 卡横排 | 280-380px | 30px | 90% |
| 2×3 网格 | 320-520px | 28px | 1600px |
| 2 大卡横排 | 680-780px | 36px | 90% |
| 纵向列表（3-4 项） | 90% 宽 | 20-24px | 90% |
| 时间轴（3 项） | 90% 宽 | 20px | 90% |

---

## 3. GSAP 动画规则

### 3.1 不可违反的规则

1. 所有时间轴必须 `{ paused: true }` 启动——播放由 player 控制
2. 每条时间轴都要注册：`window.__timelines["<composition-id>"] = tl`
3. 时长以 `data-duration` 为准，不看 GSAP 时间轴长度
4. **禁止 `repeat: -1`**——精确计算重复次数：`repeat: Math.ceil(duration / cycleDuration) - 1`
5. **禁止 `Math.random()`、`Date.now()`**——需要随机时用种子 PRNG（mulberry32）
6. **禁止异步构建时间轴**——不用 `setTimeout`、`await`、Promise
7. 只做视觉属性动画：`opacity`、`x`、`y`、`scale`、`rotation`、`color`、`backgroundColor`
8. 禁止动画 `visibility`、`display`
9. 首个动画从 t=0 偏移 0.1–0.3s

### 3.2 场景转场（多场景 composition）

1. 场景之间必须有转场——禁止硬切
2. 每个元素都要有入场动画（`gsap.from()`）
3. 除末尾场景外禁止退场动画——转场本身就是退场
4. 仅末尾场景可以让元素淡出

### 3.3 先布局后动画

先用静态 CSS 搭好终态，再加动效：
1. 元素定位在其**最可见的时刻**
2. 用 `gsap.from()` 加入场——从画面外动画到 CSS 位置
3. 用 `gsap.to()` 加退场——仅限末尾场景

---

## 4. Lint 与检查

```bash
npx hyperframes lint              # 结构/代码检查（快）
npx hyperframes lint --json       # 机器可读
npx hyperframes inspect           # 视觉布局检查（启动 Chrome）
npx hyperframes inspect --json    # Agent 可读结果
```

渲染前必须修完所有 error；warning 也应处理。

---

## 5. 渲染

```bash
npx hyperframes render                          # 标准 MP4
npx hyperframes render --quality draft          # 快速迭代（约 3 倍速）
npx hyperframes render --quality high --fps 60  # 最终交付
npx hyperframes render --output ../render/visual_v01.mp4   # 自定义输出路径
npx hyperframes render --format webm            # 透明 WebM
npx hyperframes render --docker                 # 字节级一致
```

| 旗标 | 取值 | 默认 | 说明 |
|------|---------|---------|-------|
| `--output` | 路径 | `renders/name_timestamp.mp4` | 输出路径 |
| `--fps` | 24, 30, 60 | 30 | 60fps 渲染时间翻倍 |
| `--quality` | draft, standard, high | standard | 迭代用 draft |
| `--format` | mp4, webm | mp4 | WebM 支持透明 |
| `--workers` | 1-8 或 auto | auto | 每个 worker 启动一个 Chrome |
| `--docker` | 旗标 | 关 | 可复现输出 |
| `--variables` | JSON | — | 覆盖 composition 变量 |

---

## 6. 常用配方（Recipes）

### Recipe 1：真人出镜 + 字幕 + 背景音乐

```bash
# 1. 去背景
npx hyperframes remove-background talking-head.mp4 -o transparent.webm
# 2. 转写用于字幕
npx hyperframes transcribe talking-head.mp4 --model small
# 3. 初始化项目并编排
npx hyperframes init captioned-video --non-interactive
```

Composition 结构：
- 轨道 0：背景（渐变、图片或视频）
- 轨道 1：透明底人物（`transparent.webm`）
- 轨道 2：动效字幕（由 `transcript.json` 驱动）
- 轨道 3：背景音乐（`<audio>` 设 `data-volume="0.3"`）

### Recipe 2：产品发布视频

```bash
npx hyperframes init product-launch --example product-promo --non-interactive
```

典型结构：3-5 个场景，标题 → 功能 → 演示 → CTA。

### Recipe 3：代码讲解

结构：终端/编辑器模拟背景 + 代码高亮动画 + 旁白字幕。

### Recipe 4：数据可视化

结构：动画图表（CSS/GSAP 驱动）、数字滚动、错峰入场的数据展示。

### Recipe 5：社媒竖版短视频（1080x1920）

根节点设 `data-width="1080" data-height="1920"`。布局规则、字号、安全边距详见 `references/advanced-delivery-and-quality.md` 的「Vertical Video Safe Zones」。要点：标题在顶部 160px，内容区 400-1600px，底部 320px 留给平台 UI，节奏快（每场景 2-3s），色彩大胆，优先单列卡片。

---

## 7. 转写与去背景 CLI

### HyperFrames 转写（生成字幕用）

```bash
npx hyperframes transcribe audio.mp3                      # → transcript.json
npx hyperframes transcribe video.mp4 --model small        # 默认模型
npx hyperframes transcribe video.mp4 --model medium       # 更高精度
npx hyperframes transcribe subtitles.srt                  # 导入已有字幕
```

输出 `transcript.json`，带词级时间戳：
```json
[{"id": "w0", "text": "Hello", "start": 0.0, "end": 0.5}, ...]
```

**注意**：音频未确认为英文时禁止用 `.en` 模型——`.en` 模型会翻译而非转写。中文口播管线的词级转写用 `scripts/transcribe_narration.py`（faster-whisper），见 SKILL.md 核心管线。

### 去背景（本地 u2net_human_seg 模型，无需 API Key）

```bash
npx hyperframes remove-background talking-head.mp4 -o transparent.webm
npx hyperframes remove-background subject.mp4 -o subject.webm --background-output plate.webm
npx hyperframes remove-background portrait.jpg -o cutout.png
```

输出格式：
- `.webm`（VP9 + alpha）——直接用于 `<video>` composition
- `.mov`（ProRes 4444）——外部剪辑工具用
- `.png`——单张抠图

---

## 8. 长音频 BGM 工作流

> 路径均相对任务目录 `<任务>` = `.super-video/<任务名>/`（约定见 `SKILL.md` 的「产物目录约定」）。

超过 30s 的视频不要依赖 HyperFrames 内的短音频循环，按以下流程：

1. 生成或准备全长 WAV，时长至少 `root_duration + 3s`，放在 `<任务>/audio/bgm.wav`。
2. 用 HyperFrames 渲染视觉视频到 `<任务>/render/visual_v01.mp4`（`<audio>` 的 `data-duration` 可以照写，但**不要相信渲染出的音频**）。
3. 用 FFmpeg 从 WAV 源替换/合成最终音频：

```bash
ffmpeg -y -i <任务>/render/visual_v01.mp4 -i <任务>/audio/bgm.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k \
  -t <root_duration+0.02> -movflags +faststart <任务>/deliver/<主题>_v01.mp4
```

4. 验证最终 MP4：查音频流真实解码时长，并测逐秒 RMS：

```bash
ffprobe -v error -select_streams a:0 \
  -show_entries stream=codec_name,duration -of csv=p=0 <任务>/deliver/<主题>_v01.mp4
ffmpeg -ss <root_duration-12> -t 12 -i <任务>/deliver/<主题>_v01.mp4 \
  -af volumedetect -f null /dev/null 2>&1 | grep -E "mean_volume|max_volume"
```

脚本辅助：

```bash
python <skill>/scripts/verify_audio.py <任务>/deliver/<主题>_v01.mp4 \
  --min-duration <root_duration> --tail-seconds 12
```

BGM 检查通过标准：
- 抽出音频时长 ≥ 视频时长 - 0.1s
- 最后 12 秒无静音秒（每秒 RMS > -30dB）
- BGM 风格符合用户要求或已确认的风格
- 音量可闻但不压人声（RMS 均值 -15dB ~ -20dB）

**BGM 生成原则**：仅在用户明确要求新音乐、或源素材没有可保留音频时才生成。无 numpy 时用 Python 标准库 `struct` + `wave` + `math` 合成。130BPM 电子轨可含：底鼓（4-on-floor）、hi-hat（八分音符）、贝斯（sub 振荡器）、pad（和弦进行）、主旋律、琶音层。已有原片音频的成片保留并后置合成原音频，不合成替代音乐。

脚本辅助（本地 BGM 生成，无外部依赖）：

```bash
python <skill>/scripts/generate_bgm.py --workdir <任务> --duration <root_duration+3> --bpm 110 --volume 0.25
```

### 场景时长与根时长

根 composition 时长必须等于最后一个场景的结束时间：

```text
root_duration = max(scene.data_start + scene.data_duration)
```

`data-duration` 不得短于末场景结束时间，否则渲染行为不可靠、QA 结果混乱。
