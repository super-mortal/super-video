<!-- Extracted from SKILL.md during SkillHub length optimization. Keep as reference; SKILL.md links here for progressive loading. -->

## 口播后期处理管线（Post-Production Pipeline for Talking-Head Videos）

本章节覆盖 **对已有视频素材进行后期处理** 的完整流程——加字幕、叠特效、换背景、混音 BGM、画中画等。

> 下文 `<任务>` = `.super-video/<任务名>/`：素材音频归 `audio/`、composition 归 `composition/`、无声半成品归 `render/`、成品归 `deliver/`（约定见 `SKILL.md` 的「产物目录约定」）。

## 目录

1. [适用场景](#适用场景)
2. [关键经验：口播视频修改防错清单](#关键经验口播视频修改防错清单必须执行)
3. [完整 Step-by-Step 流程](#完整-step-by-step-流程)
4. [Phase 1: 素材预处理](#phase-1-素材预处理)
5. [Phase 2: 语音转写与字幕生成](#phase-2-语音转写与字幕生成)
6. [Phase 3: Composition 编排](#phase-3-composition-编排)
7. [Phase 4: 音频混音策略](#phase-4-音频混音策略)
8. [特效叠加模板库](#特效叠加模板库)
9. [字幕动效选项](#字幕动效选项)
10. [快速口播加工模式](#快速口播加工模式)
11. [口播后期自检追加项](#口播后期自检追加项)

### 适用场景

| 场景 | 输入 | 输出 |
|------|------|------|
| 口播 + 字幕 | 一段录好的口播 MP4 | 带字幕动效的成品 MP4 |
| 口播 + 字幕 + 特效 | 口播 MP4 | 带字幕 + 粒子/光效叠加的成品 |
| 口播 + 换背景 | 口播 MP4（纯色/杂背景） | 去背景 + 新背景的成品 |
| 多段素材拼接 | 多个 MP4 片段 | 合并 + 转场 + 统一字幕的成品 |
| 画中画 | 主视频 + 辅助画面 | PiP 布局的成品 |

### 关键经验：口播视频修改防错清单（必须执行）

以下经验来自一次 86 秒口播视频连续迭代中反复出现的问题。处理已有口播视频时必须优先执行这些规则，避免重复踩坑。

#### 0. 触发与能力边界：精细口播后期必须启用本 Skill

1. **用户要求“更精准时间对齐 / 更炫字幕动效 / 转场特效 / 完整口播后期处理管线”时，必须立即启用超级视频 Skill。** 不得只用纯 FFmpeg + ASS 字幕做简单烧录后交付，因为那只能完成基础字幕，不等于完整口播后期。
2. **不得在未启用 HyperFrames 的情况下承诺“精准匹配字幕位置和特效”。** 如果只是 FFmpeg 静态字幕，必须明确说明能力有限；若用户明确要求完整效果，进入 HyperFrames 管线。
3. **完整口播后期标准管线必须包含：** 素材预检 → 音频提取 → Whisper/whisper.cpp 转写或时间戳分析 → 用户原文校对 → HTML Composition 编排 → GSAP 字幕/特效/转场 → HyperFrames lint → HyperFrames render → FFmpeg 后置音频合成 → 交付前验证。
4. **第一次交付就应采用正确管线。** 不要先交一个“简单字幕版”再等用户指出“没有启用 HyperFrames”。如果用户一开始已经提出“自动匹配位置、加字幕和特效”，默认就是 HyperFrames 任务。
5. **若先前已经用非 HyperFrames 方案做错，必须在复盘中记录为：触发识别失败，而不是单纯“效果不好”。** 后续遇到类似请求时，先加载本 Skill，再执行完整管线。

#### A. 源素材与音频：不要凭听感或渲染结果臆断

1. **始终先确认用户指定的原视频就是唯一音频真源。** 用户说“原视频里有背景音乐”时，不得擅自判断为没有 BGM，也不得自行合成替代音乐。
2. **必须用 FFmpeg 验证尾段音频是否存在。** 对用户指出的时间段（例如 1:16 后）执行：

```bash
ffmpeg -ss 76 -t 10 -i input.mov -af volumedetect -f null /dev/null 2>&1 | grep -E "mean_volume|max_volume"
```

如果 `mean_volume`/`max_volume` 有有效值，说明该段确实有声音，后续成品必须保留。

3. **已有原片音频时，采用“视觉渲染 + FFmpeg 后置合成原音频”的可靠流程。** 不要依赖 HyperFrames 从 `.mov` 或长音频中直接 mux 完整音频；不要在 `<audio>` 中直接引用 `.mov` 作为音频源来保留长尾 BGM。正确做法：

```bash
# 1. 从原视频提取完整音频
ffmpeg -y -i input.mov -vn -acodec pcm_s16le -ar 44100 -ac 1 <任务>/audio/original_audio.wav

# 2. HyperFrames 渲染视觉版（可以不放 <audio>，允许 silent visual output）
#    在 <任务>/composition/ 内执行
npx hyperframes render --output ../render/visual_v01.mp4

# 3. 后置合成完整原音频
ffmpeg -y -i <任务>/render/visual_v01.mp4 -i <任务>/audio/original_audio.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k \
  -t <video_duration> -movflags +faststart <任务>/deliver/<主题>_v01.mp4
```

4. **最终必须验证音频完整性。** 不仅检查 `ffprobe` 时长，还要检查用户指出的尾段：

```bash
ffprobe -v quiet -show_entries format=duration -show_entries stream=codec_type,duration -of default=noprint_wrappers=1 <任务>/deliver/<主题>_v01.mp4
ffmpeg -ss 76 -t 10 -i <任务>/deliver/<主题>_v01.mp4 -af volumedetect -f null /dev/null 2>&1 | grep -E "mean_volume|max_volume"
```

#### B. 字幕与文案：用户给的精确文案优先级最高

1. **用户明确指定某段字幕时，必须逐字使用用户原文。** 不要根据 ASR、记忆或模型理解自行“纠错”产品名。例如用户指定“Codex自动化剪辑视频”，不得改成 “QDesk”“QClaw” 或其它更合理的词。
2. **每次修改字幕后必须定位对应 `cap-*`，只改目标时间段，不顺手改其它字幕。** 对 3s-7s 这类精确时间段，先在 `<任务>/composition/index.html` 中找到 `data-start`/`data-duration` 覆盖该区间的字幕节点，再替换文本。
3. **避免交付前只报“已改”。** 对字幕修正必须在最终回答中列出改动后的准确文本，便于用户核对。

#### C. 视觉迭代：严格按用户约束，不额外加效果

1. **用户要求“不要增强光效/不要粒子/不要某类动效”时，必须删除对应 CSS、DOM、GSAP tween。** 不要仅设为透明或保留隐藏元素，避免后续误启用或 lint 干扰。
2. **用户要求位置变化时，按方向显式调整坐标。** 例如“整体往左一点”应从 `right: ...` 改为明确 `left: ...` 或减少 `right` 值，并在交付说明中标注实际坐标变化。
3. **用户要求字体颜色不要为白色时，检查所有相关文本层。** 数据图表要同时检查 value、label、legend，不只改一个元素。

#### D. 交付门禁：未验证关键问题不得交付

在每次渲染交付前，至少完成以下验证：

- 字幕关键片段：目标 `cap-*` 文本与用户要求完全一致。
- 音频关键片段：用户指出的尾段存在有效音量。
- 成品时长：视频流和音频流时长接近，误差 ≤ 0.1s。
- 用户本轮要求：逐项勾选，不遗漏“颜色/位置/去除效果/音频”等小项。

### 完整 Step-by-Step 流程

```text
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: 素材预处理                                          │
│   ① 检查素材格式 → ② FFmpeg 标准化 → ③ 提取音频             │
├─────────────────────────────────────────────────────────────┤
│ Phase 2: 分析与转写                                          │
│   ④ 语音转写 → ⑤ 字幕分组 → ⑥ 时间轴确认                   │
├─────────────────────────────────────────────────────────────┤
│ Phase 3: 合成编排                                            │
│   ⑦ 初始化项目 → ⑧ 编写 Composition HTML → ⑨ 渲染           │
├─────────────────────────────────────────────────────────────┤
│ Phase 4: 后期混音                                            │
│   ⑩ BGM 合成 → ⑪ 音量平衡 → ⑫ 交付                        │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1: 素材预处理

#### 素材预检清单

```bash
# 检查视频信息
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4

# 确认关键参数
# - 分辨率：1920x1080 或 1080x1920（竖版）
# - 帧率：25/30fps
# - 编码：H.264/H.265
# - 音频：AAC，采样率 44100/48000
```

#### 常见预处理操作

```bash
# 分辨率不是 1080p → 缩放
ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" -c:a copy normalized.mp4

# 竖版视频标准化
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" -c:a copy normalized_v.mp4

# 帧率标准化为 30fps
ffmpeg -i input.mp4 -r 30 -c:a copy fps30.mp4

# 提取纯音频（用于转写和混音）
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio_for_transcribe.wav
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 2 audio_original.wav

# 获取视频时长（秒）
ffprobe -v error -show_entries format=duration -of csv=p=0 input.mp4
```

#### 多段素材拼接预处理

```bash
# 方式 1: FFmpeg concat demuxer（推荐，无重编码）
# 创建 filelist.txt:
# file 'clip1.mp4'
# file 'clip2.mp4'
# file 'clip3.mp4'
ffmpeg -f concat -safe 0 -i filelist.txt -c copy merged.mp4

# 方式 2: 需要重编码（分辨率/编码不同时）
ffmpeg -f concat -safe 0 -i filelist.txt -vf "scale=1920:1080" -c:v libx264 -c:a aac merged.mp4

# 方式 3: 在 HyperFrames 中用多个 <video> 元素分段播放（带转场）
# → 见后续 Composition 模板
```

### Phase 2: 语音转写与字幕生成

```bash
# 转写中文旁白（推荐 medium 模型，中文识别更准）
npx hyperframes transcribe input.mp4 --model medium

# 如果已有 SRT/VTT 字幕文件
npx hyperframes transcribe existing.srt
```

**中文字幕分组规则：**

| 规则 | 说明 |
|------|------|
| 每行最大字数 | 14-16 个中文字符 |
| 每组最大行数 | 2 行 |
| 按语义断句 | 在标点符号（，。！？）处断开 |
| 最短停留时间 | ≥ 1.2 秒（给观众阅读时间） |
| 最长停留时间 | ≤ 5 秒（避免字幕"粘"太久） |

### Phase 3: Composition 编排

#### 核心 HTML 模板：口播 + 字幕 + 特效

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    /* === 字幕层样式 === */
    .caption {
      position: absolute;
      bottom: 100px;
      left: 50%;
      transform: translateX(-50%);
      font-family: "Inter", sans-serif;
      font-size: 42px;
      font-weight: 700;
      color: #ffffff;
      text-align: center;
      max-width: 75%;
      padding: 12px 24px;
      border-radius: 8px;
      background: rgba(0, 0, 0, 0.6);
      text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
      /* 中文适配 */
      line-height: 1.5;
      letter-spacing: 0.02em;
    }

    /* === 特效层样式 === */
    .effect-layer {
      position: absolute;
      inset: 0;
      pointer-events: none;
      z-index: 10;
    }

    .particle {
      position: absolute;
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.6);
    }
  </style>
</head>
<body>
  <!-- Root composition -->
  <div data-composition-id="post-production"
       data-width="1920" data-height="1080" data-fps="30"
       data-duration="VIDEO_DURATION">

    <!-- Track 0: 原始视频（或去背景后的视频 + 新背景） -->
    <video id="main-video"
           data-start="0" data-duration="VIDEO_DURATION" data-track-index="0"
           src="input.mp4"
           style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;">
    </video>

    <!-- Track 1: 字幕层 -->
    <div id="cap-1" class="caption" data-start="0.5" data-duration="2.3" data-track-index="1">
      大家好，欢迎来到今天的分享
    </div>
    <div id="cap-2" class="caption" data-start="2.8" data-duration="2.0" data-track-index="1">
      今天我们聊一聊 AI 编程
    </div>
    <!-- ... 更多字幕 ... -->

    <!-- Track 2: 特效叠加层 -->
    <div id="effects" class="effect-layer"
         data-start="0" data-duration="VIDEO_DURATION" data-track-index="2">
      <!-- 粒子/光效/图标等 -->
    </div>

    <!-- Track 3: BGM -->
    <audio data-start="0" data-duration="VIDEO_DURATION" data-track-index="3"
           src="bgm.wav" data-volume="0.25"></audio>

  </div>

  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <script>window.gsap||document.write('<script src="https://unpkg.com/gsap@3.14.2/dist/gsap.min.js"><\/script>');</script>
  <script>
    // 字幕入场动画
    const captionTl = gsap.timeline({ paused: true });
    document.querySelectorAll('.caption').forEach(cap => {
      const start = parseFloat(cap.dataset.start);
      captionTl.fromTo(cap,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.3 },
        start
      );
      captionTl.to(cap,
        { opacity: 0, duration: 0.2 },
        start + parseFloat(cap.dataset.duration) - 0.2
      );
    });

    window.__timelines = window.__timelines || {};
    window.__timelines["post-production"] = captionTl;
  </script>
</body>
</html>
```

#### 去背景 + 换背景模板

```html
<!-- Track 0: 新背景 -->
<div id="new-bg" data-start="0" data-duration="VIDEO_DURATION" data-track-index="0"
     style="position:absolute;inset:0;background:linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);">
  <!-- 可放动态网格、粒子等背景动画 -->
</div>

<!-- Track 1: 去背景后的人物 -->
<video id="person" data-start="0" data-duration="VIDEO_DURATION" data-track-index="1"
       src="transparent.webm"
       style="position:absolute;bottom:0;left:50%;transform:translateX(-50%);height:90%;object-fit:contain;">
</video>

<!-- Track 2: 字幕 -->
<!-- ... -->
```

#### 画中画 (PiP) 模板

```html
<!-- Track 0: 主画面（全屏） -->
<video id="main" data-start="0" data-duration="VIDEO_DURATION" data-track-index="0"
       src="main-content.mp4"
       style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;">
</video>

<!-- Track 1: 画中画（右下角小窗） -->
<video id="pip" data-start="0" data-duration="VIDEO_DURATION" data-track-index="1"
       src="talking-head.mp4"
       style="position:absolute;bottom:40px;right:40px;width:360px;height:360px;
              border-radius:50%;object-fit:cover;border:3px solid rgba(255,255,255,0.8);
              box-shadow:0 4px 20px rgba(0,0,0,0.3);">
</video>

<!-- PiP 变体：左下角矩形 -->
<!--
<video id="pip-rect" ...
       style="position:absolute;bottom:40px;left:40px;width:480px;height:270px;
              border-radius:12px;object-fit:cover;border:2px solid rgba(255,255,255,0.5);">
</video>
-->
```

#### 分屏布局模板

```html
<!-- 左右分屏 50/50 -->
<video id="left" data-start="0" data-duration="VIDEO_DURATION" data-track-index="0"
       src="screen-recording.mp4"
       style="position:absolute;left:0;top:0;width:50%;height:100%;object-fit:cover;">
</video>
<video id="right" data-start="0" data-duration="VIDEO_DURATION" data-track-index="0"
       src="talking-head.mp4"
       style="position:absolute;right:0;top:0;width:50%;height:100%;object-fit:cover;">
</video>
<!-- 中间分割线 -->
<div data-start="0" data-duration="VIDEO_DURATION" data-track-index="1"
     style="position:absolute;left:50%;top:0;width:2px;height:100%;background:rgba(255,255,255,0.3);transform:translateX(-50%);">
</div>
```

### Phase 4: 音频混音策略

#### 基本混音（BGM + 原声）

```bash
# 1. 渲染视频（无音频），在 <任务>/composition/ 内执行
npx hyperframes render --quiet --output ../render/visual_v01.mp4

# 2. 提取原始旁白音频
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 2 <任务>/audio/voice.wav

# 3. 混合：原声为主，BGM 为辅
ffmpeg -i <任务>/audio/voice.wav -i <任务>/audio/bgm.wav -filter_complex \
  "[0:a]volume=1.0[voice];[1:a]volume=0.25[bgm];[voice][bgm]amix=inputs=2:duration=first" \
  -ac 2 -ar 44100 <任务>/audio/mixed_audio.wav

# 4. 合并视频 + 混音
ffmpeg -i <任务>/render/visual_v01.mp4 -i <任务>/audio/mixed_audio.wav \
  -c:v copy -c:a aac -shortest <任务>/deliver/<主题>_v01.mp4
```

#### 高级：BGM 自动避让（Ducking）

当人声出现时 BGM 自动降低音量，人声停顿时 BGM 恢复：

```bash
# 使用 sidechaincompress 实现 ducking
ffmpeg -i <任务>/audio/voice.wav -i <任务>/audio/bgm.wav -filter_complex \
  "[1:a]volume=0.35[bgm_vol];\
   [bgm_vol][0:a]sidechaincompress=threshold=0.02:ratio=4:attack=200:release=1000[bgm_ducked];\
   [0:a][bgm_ducked]amix=inputs=2:duration=first[out]" \
  -map "[out]" -ac 2 -ar 44100 <任务>/audio/mixed_ducked.wav
```

**参数说明：**
- `threshold=0.02`: 人声信号强度阈值（越低越敏感）
- `ratio=4`: 压缩比（4:1 表示 BGM 降到原来 1/4）
- `attack=200`: 压缩启动时间 200ms（避免突然降低）
- `release=1000`: 释放时间 1000ms（人声停后 1 秒 BGM 恢复）

#### 音量标准化

```bash
# 测量当前音量
ffmpeg -i mixed_audio.wav -af "volumedetect" -f null /dev/null

# 标准化到 -16 LUFS（适合社交媒体）
ffmpeg -i mixed_audio.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11" normalized.wav
```

### 特效叠加模板库

#### 1. 粒子飘落效果

```html
<div id="particles" class="effect-layer" data-start="0" data-duration="VIDEO_DURATION" data-track-index="2">
  <!-- 粒子由 JS 生成 -->
</div>

<script>
function mulberry32(seed) {
  return function() {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  }
}
const rand = mulberry32(42);

// 生成粒子
const container = document.getElementById('particles');
for (let i = 0; i < 30; i++) {
  const p = document.createElement('div');
  p.className = 'particle';
  p.style.cssText = `
    left: ${rand() * 100}%;
    top: -10px;
    width: ${3 + rand() * 4}px;
    height: ${3 + rand() * 4}px;
    opacity: ${0.3 + rand() * 0.5};
    background: hsl(${200 + rand() * 60}, 80%, 70%);
  `;
  container.appendChild(p);
}

// 粒子下落动画
const particleTl = gsap.timeline({ paused: true });
container.querySelectorAll('.particle').forEach((p, i) => {
  particleTl.to(p, {
    y: 1200,
    x: `+=${(rand() - 0.5) * 200}`,
    duration: 4 + rand() * 3,
    repeat: Math.floor(VIDEO_DURATION / 6),
    ease: "none",
    delay: rand() * 3
  }, 0);
});
// 注意：将 particleTl 加入 window.__timelines
</script>
```

#### 2. 底部动态信息条（Lower Third）

```html
<div id="lower-third" class="effect-layer" data-start="2" data-duration="8" data-track-index="2">
  <div style="position:absolute;bottom:60px;left:60px;display:flex;align-items:center;gap:16px;">
    <div style="width:4px;height:48px;background:linear-gradient(180deg,#00d4ff,#7b2ff7);border-radius:2px;"></div>
    <div>
      <div style="font-family:'Inter',sans-serif;font-size:28px;font-weight:700;color:#fff;">张三</div>
      <div style="font-family:'Inter',sans-serif;font-size:20px;color:rgba(255,255,255,0.7);margin-top:4px;">高级产品经理 · 某科技公司</div>
    </div>
  </div>
</div>

<script>
const ltTl = gsap.timeline({ paused: true });
const lt = document.querySelector('#lower-third > div');
ltTl.fromTo(lt, { x: -300, opacity: 0 }, { x: 0, opacity: 1, duration: 0.5, ease: "power2.out" }, 2);
ltTl.to(lt, { x: -300, opacity: 0, duration: 0.4, ease: "power2.in" }, 9.5);
// 加入 window.__timelines
</script>
```

#### 3. 光效扫描（Light Sweep）

```html
<div id="light-sweep" class="effect-layer" data-start="0" data-duration="VIDEO_DURATION" data-track-index="2">
  <div class="sweep-bar" style="
    position:absolute;
    top:0;left:-200px;
    width:200px;height:100%;
    background:linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    transform:skewX(-15deg);
  "></div>
</div>

<script>
const sweepTl = gsap.timeline({ paused: true });
sweepTl.to('.sweep-bar', {
  x: 2200,
  duration: 3,
  repeat: Math.floor(VIDEO_DURATION / 5),
  repeatDelay: 2,
  ease: "power1.inOut"
}, 0);
</script>
```

#### 4. 关键词高亮弹出

```html
<!-- 在特定时间点弹出关键信息 -->
<div id="keyword-pop" data-start="5" data-duration="3" data-track-index="2"
     style="position:absolute;top:50%;right:80px;transform:translateY(-50%);
            font-family:'Inter',sans-serif;font-size:56px;font-weight:900;
            color:#00d4ff;text-shadow:0 0 20px rgba(0,212,255,0.5);">
  效率提升 300%
</div>

<script>
const kwTl = gsap.timeline({ paused: true });
kwTl.fromTo('#keyword-pop',
  { scale: 0, opacity: 0, rotation: -5 },
  { scale: 1, opacity: 1, rotation: 0, duration: 0.4, ease: "back.out(1.7)" },
  5
);
kwTl.to('#keyword-pop', { opacity: 0, y: -30, duration: 0.3 }, 7.5);
</script>
```

### 字幕动效选项

AI 根据视频风格自动选择最合适的字幕动效：

| 动效类型 | 适用场景 | CSS/GSAP 实现 |
|----------|---------|--------------|
| **淡入淡出** | 正式/商务口播 | `opacity: 0→1→0` |
| **底部弹出** | 活泼/教程 | `y: 20→0`, `opacity: 0→1` |
| **逐字打字机** | 科技/极客风 | 每字 stagger 0.05s |
| **卡拉OK高亮** | 重点强调 | word-level 颜色切换 |
| **缩放弹入** | 短视频/抖音风 | `scale: 0.5→1`, `ease: back.out` |

#### 卡拉OK高亮实现

```html
<div id="cap-karaoke" class="caption" data-start="3" data-duration="2.5" data-track-index="1">
  <span class="word" data-word-start="3.0" data-word-end="3.4">今天</span>
  <span class="word" data-word-start="3.4" data-word-end="3.7">我们</span>
  <span class="word" data-word-start="3.7" data-word-end="4.1">来聊</span>
  <span class="word" data-word-start="4.1" data-word-end="4.5">AI</span>
  <span class="word" data-word-start="4.5" data-word-end="5.0">编程</span>
</div>

<style>
.word { color: rgba(255,255,255,0.5); transition: color 0.1s; }
.word.active { color: #00d4ff; text-shadow: 0 0 10px rgba(0,212,255,0.5); }
</style>

<script>
const karaokeTl = gsap.timeline({ paused: true });
document.querySelectorAll('#cap-karaoke .word').forEach(w => {
  const start = parseFloat(w.dataset.wordStart);
  karaokeTl.to(w, { className: "+=active", duration: 0.01 }, start);
});
</script>
```

#### 逐字打字机实现

```javascript
const typeTl = gsap.timeline({ paused: true });
const capEl = document.getElementById('cap-type');
const chars = capEl.textContent.split('');
capEl.textContent = '';
chars.forEach(ch => {
  const span = document.createElement('span');
  span.textContent = ch;
  span.style.opacity = '0';
  capEl.appendChild(span);
});
typeTl.to(capEl.querySelectorAll('span'), {
  opacity: 1,
  stagger: 0.05,
  duration: 0.01
}, parseFloat(capEl.dataset.start));
```

### 快速口播加工模式

当用户只说 **"帮我这段口播加字幕和特效"** 时，AI 自动执行以下完整流程：

```text
用户提供 MP4 → 
  ① ffprobe 检查素材参数
  ② 标准化为 1080p 30fps（如需）
  ③ hyperframes transcribe --model medium
  ④ 自动字幕分组（中文 14字/行，按标点断句）
  ⑤ 选择字幕动效（默认：底部弹出 + 半透明底板）
  ⑥ 选择特效层（默认：轻微粒子 + 底部信息条）
  ⑦ 编写 Composition HTML
  ⑧ hyperframes render
  ⑨ 音频处理（默认保留原片完整音频；仅在用户要求时混入 BGM）
  ⑩ 自检管线 Phase B-D
  ⑪ 交付 <任务>/deliver/<主题>_v01.mp4
```

**AI 默认选择（用户未指定时）：**
- 字幕样式：底部居中，42px，墨字 + 白色纸底板
- 字幕动效：淡入淡出
- 特效层：轻微光效扫描（不抢视觉焦点）
- BGM：无（除非用户要求）
- 画面处理：保持原始画面不去背景

**用户可随时覆盖任何默认选择。**

### 口播后期自检追加项

在标准 Phase A-D 自检管线之外，口播后期处理需额外检查：

| # | 检查项 | Pass 标准 |
|---|--------|-----------|
| P1 | 字幕与语音同步 | 字幕出现时间 ≤ 语音开始后 0.2s |
| P2 | 字幕无遮挡关键画面 | 字幕区域（bottom 100px）无人脸/关键信息 |
| P3 | 原视频音画同步 | 渲染后口型与音频匹配 |
| P4 | 特效层不干扰主内容 | 特效透明度 ≤ 0.3，不遮挡人物/字幕 |
| P5 | BGM ducking 生效 | 人声段 BGM 降到 -20dB 以下 |
| P6 | 视频时长完整 | output duration ≥ input duration - 0.1s |

---

