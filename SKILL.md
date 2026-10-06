---
name: super-video
description: "超级视频：把写好的文案一键变成带中文配音与同步字幕的成片视频。MiniMax 整段合成中文旁白，faster-whisper 词级强制对齐取得真实时间轴，据此生成 HTML+GSAP 动画画面与静态整句字幕，经 HyperFrames 渲染、FFmpeg 合成音轨，音画严格同步。凡用户想把文案/文章/脚本做成视频、要 AI 配音、加字幕、做口播/解说/科普/不露脸短视频、文生视频时，都应使用本技能。"
license: MIT
metadata:
  display_name: "超级视频"
  version: "0.0.4"
  category: "video"
  platforms: ["Windows", "macOS", "Linux"]
  author: "super-mortal"
  tags: ["AI视频生成", "文生视频", "AI口播视频", "口播视频", "解说视频", "知识科普", "不露脸视频", "AI配音", "AI旁白", "TTS语音合成", "自动字幕", "同步字幕", "短视频", "音画同步", "GSAP动画", "MiniMax"]
---

# 超级视频｜Script → Narrated Video

> **超级视频（super-video）从零把一段写好的脚本，做成配音、同步字幕、动画画面齐备的成片。**
>
> 全链路：MiniMax 整段合成旁白 → faster-whisper 词级强制对齐取得真实时间轴 → 数据驱动生成 HTML+GSAP 画面与静态整句字幕 → HyperFrames 渲染无声视觉 → FFmpeg 后置合成音轨。
>
> 时间轴的唯一真源是**从真实音频反推的词级时间戳**，画面与字幕的全部时间由它生成——因此改稿重跑之后，音画永远同步。

---

## 概述

超级视频把一段写好的文案，自动变成一条完整的成片：中文旁白配音、整句同步字幕、动画画面三者严格同步，全程无需真人出镜、无需视频剪辑软件。渲染层基于 HyperFrames（HTML + CSS + GSAP 动画，经 Headless Chrome + FFmpeg 确定性渲染为 MP4），音频层由 MiniMax 语音合成与 faster-whisper 词级对齐驱动，专为 AI Agent 全流程自动化设计。

**核心能力：**
- 从文字稿一键生成完整成片（15 秒 ~ 3 分钟），配音、字幕、画面一次到位
- 中文旁白配音：MiniMax 整段合成，多音色可选；无密钥时向用户提供三选一（直接提供密钥 / 写入配置文件 / 免费回退 Edge-TTS）
- 整句同步字幕：时间轴从真实音频反推，字幕随场景整句切换，改稿重跑后音画依旧严格同步
- 动画画面完全可定制：布局、配色、动画、字体均由 HTML/CSS 控制
- AI 全流程自动化：配音 → 对齐 → 生成画面 → 渲染 → 混音 → 交付
- 支持按需 BGM 合成与音量调校，内置自检管线确保成片质量

---

## 产物目录约定

在**当前工作目录**下开一个 `.super-video/<任务名>/` 作为本次任务的工作区，一次任务的全部产物都放进这个目录，不散落到工作目录里。

```
.super-video/<任务名>/
├── script.txt          输入：旁白文案（每行一句）
├── scenes.json         输入：每场景画面描述（只写画面，不写时间）
├── audio/              音频与时间轴
│   ├── narration.mp3               原始合成音频
│   ├── narration.wav               44.1kHz 立体声（混音用）
│   ├── narration_16k.wav           16kHz 单声道（转写用）
│   ├── narration_words.json        词级时间戳
│   ├── narration_words_segments.json
│   ├── timeline.json               真实时间轴（唯一真源）
│   └── bgm.wav                     可选背景乐
├── composition/        HTML 画面（index.html）
├── render/             半成品：无声视觉版
│   ├── visual_v01_draft.mp4
│   └── visual_v01.mp4
└── deliver/            成品：含配音的成片
    ├── <主题>_v01.mp4
    └── <主题>_final.mp4
```

**规则：**

- `<任务名>` 用简短标识，例：`.super-video/deepseek`。
- 四类子目录各司其职：`audio/` 只放音频与时间轴，`composition/` 只放 HTML，`render/` 只放无声半成品，`deliver/` 只放最终成片。
- 只有 `deliver/` 里的成片交付给用户；其余都是过程产物，留在任务目录里不交付，也不主动清理。
- 所有脚本支持 `--workdir <任务目录>`：默认产物落到对应子目录，父目录按需自动创建；显式 `-o/--output` 仍优先，按原样使用。不带 `--workdir` 时保持旧行为（落在当前目录）。
- 版本命名：首次 `_v01`，返工递增 `_v02`…，用户认可后定稿 `_final`。

---

## 环境准备

### 必装工具

| 工具 | 最低版本 | 用途 | 安装 |
|------|---------|------|------|
| **Node.js** | 22+ | HyperFrames CLI 运行时 | 官网安装包 / `nvm install 22` |
| **FFmpeg / FFprobe** | 5.0+ | 编码、混音、抽帧 | Windows: `winget install Gyan.FFmpeg`（Win10+ 自带 winget，自动配置 PATH，装完重开终端验证 `ffmpeg -version`）；macOS: `brew install ffmpeg`；Linux: `apt install ffmpeg` |
| **Chrome Headless Shell** | 自动管理 | 逐帧渲染引擎 | `npx hyperframes browser ensure`（自动下载） |
| **HyperFrames CLI** | 0.6.90+ | composition 管理与渲染 | 经 npx 自动获取 |
| **Python 3.9+** | — | 本技能配音/转写/对齐/生成脚本 | python.org 安装包或系统包管理器 |
| **faster-whisper** | — | 旁白词级转写（本地，无需 Key） | `pip install faster-whisper` |
| **MiniMax 密钥** | — | 旁白合成鉴权（解析顺序见 H13） | 环境变量 `MINIMAX_API_KEY`，或写入配置文件 `~/.config/minimax/api_key` 一次到位 |

### 首次安装序列

```bash
node --version                          # 1. 确认 Node >= 22
which ffmpeg || brew install ffmpeg     # 2. 安装 FFmpeg
npx hyperframes browser ensure          # 3. 下载 Chrome Headless Shell（缓存于 ~/.cache/hyperframes/chrome/）
npx hyperframes doctor                  # 4. 全量体检，所有项必须通过
```

### 每次任务前的预检

```bash
npx hyperframes doctor
which ffmpeg && ffmpeg -version
```

`doctor` 有任何失败项，先解决再动工——带病环境只会浪费渲染时间、产出废片。

### 环境故障速查

| 症状 | 原因 | 解法 |
|------|------|------|
| `doctor` 显示 ✗ FFmpeg | 未安装 | `brew install ffmpeg` |
| `doctor` 显示 ✗ Chrome | 首次运行无缓存浏览器 | `npx hyperframes browser ensure` |
| 渲染无限挂起 | AI Agent 沙箱与 Chrome 冲突 | 渲染命令在禁用沙箱的方式下运行 |
| `EACCES` 权限错误 | npx 缓存权限 | `sudo chown -R $(whoami) ~/.npm` |
| 渲染产出 0 字节 MP4 | FFmpeg 编码器问题 | 确认 `ffmpeg -encoders` 含 `libx264` 与 `aac` |
| `npx hyperframes` 找不到 | Node 不在 PATH | 确保 Node 22+ 在 PATH |

---

## 工作流决策树

1. **从零生成动画视频（配音 + 同步字幕 + 动画画面，本技能核心流程）**
   - 有旁白（默认）：走「核心管线：脚本 → 口播视频」七步，画面即 HTML+GSAP 动画场景
   - 无旁白纯动画：跳过音频链路，init → 写 composition → 动画 → lint → render（详见 `references/hyperframes-rendering.md`）
2. **口播后期加工（已有视频加字幕/特效/换背景/混音）** → 见「口播后期处理」并先读 `references/talking-head-pipeline-full.md`
3. **已有口播 + 去背景 + 换场景** → remove-background → 分层 composition → 字幕 → 配乐 → 渲染
4. **修改已有 composition** → 读文件 → 最小修改 → lint → render
5. **数据可视化视频** → 规划数据场景 → 动画图表 → 渲染
6. **多段素材拼接** → FFmpeg concat → 统一字幕/特效/转场 → 渲染

---

## 硬约束与软默认

### 提示词优先级（统辖一切）

```
用户提示词的明确意图 > 硬约束（技术安全）> 软默认（参考建议）
```

- **详细提示词**（明确指定布局、配色、风格、动画）：严格按提示词执行，软默认全部让位。AI 的任务是实现用户的视觉创意，不是把视频拉回模板。
- **简单提示词**（只给主题/关键词）：AI 自由发挥，软默认作起点，鼓励创新。

无论哪种模式，交付前必须执行「自检管线」，确保技术安全与视觉完整。

### 提示词合规清单（写 HTML 前建立，渲染后逐项核对）

动笔前先建立一份紧凑的生产清单：

- 主题/标题与目标受众
- 需要的场景或内容要点
- 要求的视觉风格与禁止的风格
- **要求的配色——永远以用户提示词为准，绝不擅自替换或覆盖**
- 要求的 BGM 风格、是否必须铺满全片、目标音量
- 时长目标与末场景结束时间
- 对字体/卡片/图标比例的特殊要求
- **创意方向判定**：用户是否给了详细视觉指示？（是 → 严格执行，软默认让位；否 → AI 自由发挥，参考软默认）

渲染后对照清单逐项核对。用户指定了 BGM 风格就不得换成别的风格（除非用户明确同意）；用户指定了配色就不得换成"更安全"或"更通用"的方案。

### 硬约束（永远生效，与用户提示词冲突也不可违反）

这些是技术限制，违反会导致渲染崩溃、输出错误或不可预期行为：

| # | 硬约束 | 原因 |
|---|--------|------|
| H1 | 禁止 `Math.random()`/`Date.now()`/`new Date()`/`performance.now()` | 非确定性渲染导致帧不一致 |
| H2 | 字体仅限白名单： Inter, JetBrains Mono, Roboto, sans-serif | 其他字体 lint 报错或渲染失败 |
| H3 | 禁止 `@import url()` 引入字体 | Compiler 不支持，渲染卡死 |
| H4 | GSAP 以 jsdelivr 为主源、unpkg 为回退源（两行 `<script>` 加载链，见「渲染硬规则」），禁止本地 `lib/gsap.min.js` | jsdelivr 在国内可能连接被重置；缺 GSAP 时场景停在 `opacity:0`，渲染会被判失败而中止。本地文件在渲染环境不可用 |
| H5 | `window.__timelines` 必须同步注册 | 异步注册导致空帧 |
| H6 | 内容不可超出画布边界（任何像素） | 超出部分被裁切 |
| H7 | 禁止 inline `style="top:XX%"` 覆盖定位 | 百分比定位跨场景不一致，导致溢出 |
| H8 | GSAP repeat 用 `Math.floor` 而非 `Math.ceil` | ceil 可能超出 composition 时长 |
| H9 | 音频必须 FFmpeg 后置合成（≥30s 视频） | HyperFrames 内置音频约 32s 截断 |
| H10 | 旁白必须整段一次性合成，禁止逐句拼接 | 逐句拼接句间塞固定静音，听感生硬 |
| H11 | 画面/字幕时间必须来自 whisper 强制对齐的真实时间轴（timeline.json） | 手写或估算时间必然与语音漂移 |
| H12 | 画面必须数据驱动生成，禁止手写 `data-start`/`data-duration` | 手写时间无法随音频变化同步更新 |
| H13 | 密钥按「`--api-key` → 环境变量 `MINIMAX_API_KEY` → 配置文件 `~/.config/minimax/api_key`」顺序解析，禁止硬编码/打印明文 | 凭证安全 |
| H14 | MiniMax 模型名必须全小写且版本号精确（如 `speech-2.8-hd`） | 大小写/无后缀变体返 2013 不可用 |

### 软默认（仅当用户提示词未指定时生效，用户有明确意图即让位）

| # | 软默认 | 默认值 | 用户可覆盖场景 |
|---|--------|--------|--------------|
| S1 | 标题区位置 | top: 50px | 全屏标题、底部标题等 |
| S2 | 内容起始位置 | top: 240px | 居中布局、沉浸式设计等 |
| S3 | 卡片间距 | 28-36px | 紧凑/宽松排版 |
| S4 | 内容底部边界 | 980px | 明确要底部内容 |
| S5 | 左右安全边距 | 120px | 全出血设计 |
| S6 | 字号范围 | 见下方排版参考表 | 指定特定字号风格 |
| S7 | 卡片宽度 | 320-520px | 大卡片/小卡片 |
| S8 | 场景过渡 | 0.6s opacity fade | 滑动/缩放/3D 等过渡 |
| S9 | 背景风格 | 米白纸底 + 墨线网格 + 纸屑墨点 | 任何其他背景 |
| S10 | 粒子数量 | 40 个， mulberry32 seed=42 | 不要粒子或要更多 |
| S11 | 骨架结构 | scene-wrapper 标准骨架 | 不同的布局需求 |
| S12 | 配色 | 纸感墨蓝（米白纸底 / 墨字 / #4D6BFE 墨蓝 / #FFEE58 荧光黄，调色板见生成器内置 `:root`） | 用户指定配色 |
| S13 | 旁白音色 | MiniMax `female-shaonv`（少女） | 其他 voice_id |
| S14 | 字幕样式 | 整句静态显示，44px 加粗墨字，底部 74px 居中，无逐词动画 | 用户指定字号/位置/样式 |
| S15 | 字幕底板 | 浅色纸底（默认）无底板；复杂/深色画面场景在 scenes.json 设 `caption_bg: true`，加白色纸底板（rgba(255,255,255,.95) + 墨线边框 + 直角色块阴影） | 用户指定底板样式 |
| S16 | 顶部进度条 | 默认带（不询问、不提醒） | 用户明确说不要 |

### 1920x1080 排版参考（软默认）

| 元素 | 参考范围 | 硬上限（H6 防溢出） |
|---------|----------------|------|
| 封面大标题 | 96-120px | 132px |
| 场景标题 | 64-84px | 92px |
| 副标题 | 38-56px | 64px |
| 正文 | 28-42px | 48px |
| 卡片标题 | 32-44px | 48px |
| 数据数字 | 72-104px | 112px |
| 图标/emoji | 56-96px | 112px |
| 代码文本 | 26-36px | 42px |

硬上限只为防溢出，不是风格限制；用户明确要超大标题且布局容得下就实现。

**标准布局安全区（软默认）：**

```
┌──────────────────────────────────────────────┐
│ 标题安全区: top 50px, 高度 ≤ 150px            │ ← 标准参考
├──────────────────────────────────────────────┤
│ 内容安全区: top 240px ~ bottom 980px          │ ← 标准参考
├──────────────────────────────────────────────┤
│ 底部安全边距: bottom 100px                    │ ← 建议保留
└──────────────────────────────────────────────┘
```

- 标题区: `top: 50px`，居中，高度 ≤ 150px
- 内容区: `top: 240px`，底部不超过 980px
- 左右边距: ≥ 120px
- 标题与内容间距: ≥ 40px

硬约束始终生效：H6（所有可见内容在 0~1920px 水平、0~1080px 垂直范围内）与 H7（禁止 inline `top:XX%`，必须用 CSS class 或固定 px）。用户描述了不同布局需求（全屏沉浸、斜切、居中对称等）时自由设计，只需不违反 H6/H7。卡片布局尺寸与内容高度预算详见 `references/hyperframes-rendering.md`。

**配色规则：** 默认使用内置纸感调色板（S12）；用户提示词是配色的唯一真源，给了配色就精确实现，绝不擅自替换成"更安全"的方案。

### 自动补全默认值（简单提示词模式参考）

用户的提示词**未指定**以下细节时，可参考这些经过验证的默认值作为**起点**，鼓励在此基础上发挥创意：

| 缺失项 | 默认参考 | AI 可自由替换？ |
|-------------|------------------|----------------|
| 布局策略 | 标题 top:50px + 内容 top:240px | 可以，任何不违反 H6/H7 的布局 |
| 字体 | `Inter, sans-serif` | 不可以——硬约束 H2，只能用白名单字体 |
| 音频策略 | FFmpeg 后置合成（全长 WAV） | 不可以——硬约束 H9（≥30s 视频） |
| 内容容器 | `.content-area` / `.content-col` | 可以，任何语义化 CSS 结构 |
| 卡片间距 | 横向 28-36px，纵向 20-24px | 可以 |
| 粒子生成 | 40 个，mulberry32 seed=42 | 数量自由，但 PRNG 必须用 mulberry32（H1） |
| 背景 | 米白纸底 + 墨线网格 + 纸屑墨点 | 完全自由 |
| 转场风格 | 0.6s opacity fade | 可以，滑动/缩放/模糊等 |
| 网格背景动画 | 20s infinite translate loop | 可以 |
| 验证管线 | 完整 Phase A-D 自检 | 不可以——始终必须执行 |

默认值是灵感参考，不是束缚；AI 应根据视频主题和内容自然选择最佳表达方式。

### 字体白名单（硬约束 H2）

```css
/* 允许——Compiler 可自动解析 */
font-family: "Inter", sans-serif;
font-family: "JetBrains Mono", monospace;  /* 代码块 */
font-family: "Roboto", sans-serif;

/* 禁止——lint 报错或渲染失败 */
font-family: "PingFang SC";        /* 仅 macOS，未打包 */
font-family: "Microsoft YaHei";    /* 仅 Windows */
font-family: "Noto Sans SC";       /* 不可自动解析 */
font-family: "Source Han Sans";    /* 不可自动解析 */
```

中文渲染依赖 `sans-serif` 回退（Chrome 下正常显示），对视频输出的视觉差异可忽略。

### 确定性渲染（硬约束 H1、H8）

```javascript
// 禁止——非确定性（H1）
Math.random(); Date.now(); new Date(); performance.now();

// 必须用种子 PRNG
function mulberry32(seed) {
  return function() {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  }
}
const rand = mulberry32(42);  // 固定种子

// GSAP repeat 计算（H8）：Math.floor 保证不超 composition 时长
repeat: Math.floor(duration / cycle) - 1
```

### 渲染硬规则（AI Agent 自动化环境必须遵守）

1. **GSAP 保持 CDN URL 并带同步回退**——主源 jsdelivr，失败自动换 unpkg：
   ```html
   <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
   <script>window.gsap||document.write('<script src="https://unpkg.com/gsap@3.14.2/dist/gsap.min.js"><\/script>');</script>
   ```
   回退用 `document.write` 在解析期同步补载，保证下面内联的时间轴脚本执行时 `gsap` 已就绪；主源成功时回退分支不执行。本地路径会破坏渲染（H4）
2. **字体禁止 @import**——CSS 里直接声明 `font-family`，Compiler 自动解析并缓存常见 Google Fonts（H3）
3. **渲染时禁用 Agent 沙箱**——启动 Headless Chrome（Puppeteer）在沙箱内会挂起
4. **命令加非交互旗标**——`init` 用 `--non-interactive`；`render` 用 `--quiet`（0.8.x 起已移除 `--non-interactive`）。旗标报 Unknown 时先 `--help` 核对当前版本

---

## 核心管线：脚本 → 口播视频

超级视频的核心，就是把「脚本 → 配音 → 字幕 → 画面」的同步链路做成一键式。核心原则一句话：**音频定时间，画面跟着音频走。**

> 完整原理、设计取舍见 `references/narration-sync-pipeline.md`；MiniMax 接口/音色/密钥惯例见 `references/minimax-tts.md`。

### 数据流

下图路径均相对 `.super-video/<任务名>/`：

```
script.txt（每行一句）
   │ ① minimax_narrate.py         MiniMax 整段合成           → audio/narration.mp3 / .wav / _16k.wav
   ▼
audio/narration_16k.wav
   │ ② transcribe_narration.py  faster-whisper 词级转写   → audio/narration_words.json
   ▼
audio/narration_words.json
   │ ③ build_timeline.py      文案字符 ↔ 词级字符 强制对齐  → audio/timeline.json（真实时间轴）
   ▼
audio/timeline.json + scenes.json
   │ ④ build_composition.py 数据驱动生成              → composition/index.html
   ▼
composition/index.html
   │ ⑤ npx hyperframes render  渲染无声视觉              → render/visual_v01.mp4
   ▼
render/visual_v01.mp4
   │ ⑥ merge_audio.py        FFmpeg 后置合成旁白(+BGM)   → deliver/<主题>_v01.mp4
   ▼
deliver/<主题>_v01.mp4
   │ ⑦ verify_audio.py         音频时长/尾段验证          → PASS/FAIL
```

### 完整命令序列（复制即用）

> 下文 `<skill>` 指本技能所在目录，`<任务>` 指 `.super-video/<任务名>`。

```bash
# ⓿ 开任务目录（<任务名> 换成内容主题，如 deepseek）
mkdir -p <任务>
# 把旁白文案写进 <任务>/script.txt（每行一句）

# ① 合成（密钥解析顺序见 H13，默认读配置文件）
python <skill>/scripts/minimax_narrate.py <任务>/script.txt \
    --workdir <任务> --model speech-2.8-hd --voice female-shaonv

# ② 转写
python <skill>/scripts/transcribe_narration.py <任务>/audio/narration_16k.wav \
    --workdir <任务>

# ③ 对齐（similarity 应 >= 0.9）
python <skill>/scripts/build_timeline.py <任务>/script.txt \
    <任务>/audio/narration_words.json <任务>/audio/narration.wav \
    --workdir <任务>

# ④ 生成 HTML（画面写在 <任务>/scenes.json）
python <skill>/scripts/build_composition.py <任务>/audio/timeline.json \
    <任务>/scenes.json --workdir <任务> --theme <skill>/assets/theme.css

# ⑤ lint + 渲染（在 composition/ 内执行；先草稿再成片）
cd <任务>/composition
npx hyperframes lint
npx hyperframes render --quality draft --output ../render/visual_v01_draft.mp4
npx hyperframes render --quality high  --output ../render/visual_v01.mp4
cd -

# ⑥ 后置合成（默认写入 <任务>/deliver/<任务名>_v01.mp4）
python <skill>/scripts/merge_audio.py <任务>/render/visual_v01.mp4 \
    <任务>/audio/narration.wav --workdir <任务>
#   可选加 BGM：追加 --bgm <任务>/audio/bgm.wav --bgm-gain -26
#   用户认可后定稿：追加 --version final

# ⑦ 验证
python <skill>/scripts/verify_audio.py <任务>/deliver/<任务名>_v01.mp4 \
    --min-duration <total> --tail-seconds 12
```

### 各步骤要点

**① 整段合成（H10）**
- 把整个 `script.txt` **一次性**丢给 MiniMax，模型自己处理句间语气与停顿。
- 禁止逐句单独合成再拼固定静音——句子接缝明显、听感机械。
- 输出 3 个文件：`.mp3`（原始）、`.wav`（44.1k 立体声，混音用）、`_16k.wav`（转写用），全部落在 `audio/`。

**② 词级转写（H11）**
- faster-whisper 本地跑，`small` 模型够用，中文务必 `--lang zh`，不要 `.en` 模型（会翻译）。
- 输出每个词的 `start/end`。

**③ 强制对齐（H11）——本技能核心**
- 用 `difflib.SequenceMatcher` 把「文案字符序列」对齐到「whisper 字符序列」，取 equal 段的时间，缺口线性插值。
- 归一化只保留 CJK + 拉丁数字、统一小写、去标点/空格，中英混排也稳。
- **`similarity` 是体检指标**：正常 ≥ 0.9；< 0.85 说明文案与音频差异过大（多半是改了稿没重新合成）。
- 产出 `audio/timeline.json`：每句/每词的准确时间 + 场景切换点（取句首词时间 - lead）。

**④ 数据驱动生成（H12）**
- `scenes.json` **只写画面，不写时间**；时间只在 `timeline.json`，由生成器注入 HTML 的 `data-start`/`data-duration`。
- 子元素加 `class="reveal"` 自动入场、`class="pop"` 弹出强调。
- 生成器输出 `composition/index.html`；场景数必须与 `timeline.json` 一致（= script.txt 行数，1 句 1 场景），否则报错退出。
- 画面模板参考 `assets/scenes.example.json`、样式参考 `assets/theme.css`。

**⑤ 渲染**：在 `composition/` 目录内执行，先 draft 抽帧检查，满意再 high。渲染的是**无声视觉版**，产物写进 `render/`（`visual_v01.mp4`，草稿为 `visual_v01_draft.mp4`）。

**⑥ 后置合成（H9）**
- `merge_audio.py` 把 `narration.wav` 与 `visual_v01.mp4` 合到一起（旁白为准，`apad`+`atrim` 对齐，`-c:v copy` 不重编码视频）。
- 可选 BGM 铺底（`--bgm-gain -26`），旁白必须清晰不被盖。
- 带 `--workdir` 时默认输出 `<任务>/deliver/<任务名>_v01.mp4`；用户认可后加 `--version final` 定稿。

**⑦ 验证**：音频时长 ≥ 视频时长；尾段非静音（每秒 RMS > -30dB）；全程有声。

### MiniMax 模型与音色

模型（必须全小写 + 精确版本号，见 H14）：

| 模型 | 定位 |
|------|------|
| `speech-2.8-hd` | 最新 + 高保真（默认，S13） |
| `speech-2.8-turbo` | 最新 + 快速 |
| `speech-2.6-hd` / `speech-2.6-turbo` | 次新 |
| `speech-02-hd` / `speech-02-turbo` | 02 系列 |
| `speech-01-hd` / `speech-01-turbo` | 01 系列 |

不可用（返 2013）：`speech-2.5-*`、无后缀的 `speech-2.8`、任意大小写变体。

音色（`voice_id`）：默认 `female-shaonv`（少女）；备选 `male-qn-qingse`（青涩青年）、`female-yujie`（御姐）、`female-tianmei`（甜美）、`Chinese (Mandarin)_News_Anchor`（新闻主播）。配置见 `assets/voices.json`。

接口：`POST https://api.minimaxi.com/v1/t2a_v2`（**只有 api.minimaxi.com / api.minimax.cn 有效，`.io` 返 401**），单请求 ≤ 10000 字符。

**密钥与凭证（H13）**：密钥按「命令行 `--api-key`（仅本次运行，不落盘）→ 环境变量 `MINIMAX_API_KEY` → 配置文件 `~/.config/minimax/api_key`」顺序解析；脚本内不得出现明文，不得打印 Token。三处都没有时，向用户提供三选一，选哪个就按哪个执行：
1. **直接提供密钥**：用户把密钥发给 AI，AI 以 `--api-key` 传入本次运行；
2. **写入配置文件**（推荐，一次配置长期有效）：Windows 为 `C:\Users\<用户名>\.config\minimax\api_key`（macOS/Linux 为 `~/.config/minimax/api_key`），UTF-8 纯文本，内容为密钥本身或一行 `MINIMAX_API_KEY=sk-...`，空行与 `#` 注释忽略；
3. **改用免费 Edge-TTS**：无需密钥，仍走同一管线（见下）。

可选环境变量：`MINIMAX_BASE_URL`、`FFMPEG`/`FFPROBE`（默认从 PATH 取）。

**免费回退（Edge-TTS）**：无需 Key、需联网，自然度略逊。女声 `zh-CN-XiaoyiNeural`（活泼）/ 男声 `zh-CN-YunxiNeural`（青年）：
```bash
pip install edge-tts
edge-tts --voice zh-CN-XiaoyiNeural --text "..." --write-media out.mp3
```
回退时仍走「整段合成 → 转写 → 对齐 → 数据驱动生成」同一管线。

### 字幕（静态整句）

- **一句一屏**：script.txt 每行一句，一句一个场景；字幕即该句全文，随场景整体出现/消失，无逐词高亮、无跳动动画。
- **样式**：44px 加粗墨字，底部 74px 居中；浅色纸底场景默认无底板；复杂/深色画面场景在 scenes.json 设 `"caption_bg": true`，加白色纸底板（rgba(255,255,255,.95) + 墨线边框）。
- **建议单句 ≤ 16 字**：过长按标点在 script.txt 里拆行，否则字幕一行放不下。
- 词级时间轴（timeline.json）仍用于场景切换时间与对齐报告；字幕本身不再按词打点。
- 换样式只改 `build_composition.py` 内置 CSS 的 `.cap-box`（或用 `--theme` 追加覆盖），时间零影响。

### 换音色/换模型重做

只重跑 ①②③④（改 `--voice`/`--model`），**画面（scenes.json）无需改**，时间自动跟随新音频重算。

---

## 无旁白变体：纯动画视频

核心管线去掉音频层的用法（科技资讯、数据可视化、产品介绍等不需要配音的场景）——跳过①-④音频链路，直接走五步：

1. **初始化**：在任务目录内 `npx hyperframes init composition --non-interactive`，产物落在 `.super-video/<任务名>/composition/`（模板见 `references/hyperframes-rendering.md`）
2. **编写 composition**：单场景或多场景骨架 + 数据属性（详见 `references/hyperframes-rendering.md` §2）
3. **GSAP 动画**：时间轴规则与转场（详见 `references/hyperframes-rendering.md` §3）
4. **Lint**：`npx hyperframes lint`，0 error 才能渲染
5. **渲染**：`npx hyperframes render --quality high`（旗标详见 `references/hyperframes-rendering.md` §5）

单场景简单示例：

```bash
cd <任务>                                  # <任务> = .super-video/<任务名>
npx hyperframes init composition --non-interactive
# 编辑 composition/index.html（AI 生成内容）后，在 composition/ 内：
cd composition
npx hyperframes lint && npx hyperframes render --quiet --output ../render/visual_v01.mp4
```

### 长音频 BGM 工作流（≥30s 视频，硬约束 H9）

HyperFrames 内置音频处理会在约 32s 处截断长音频，所以超过 30s 的视频一律走「渲染视觉版 → FFmpeg 后置合成全长 WAV」：

1. 准备全长 WAV，时长至少 `root_duration + 3s`。用户要求新音乐或源素材无音频时，用 `python <skill>/scripts/generate_bgm.py --workdir <任务> --duration <root_duration+3>` 本地合成，落在 `audio/bgm.wav`。
2. 渲染视觉视频到 `render/visual_v01.mp4`（`<audio>` 的 `data-duration` 照写，但不要相信渲染出的音频）。
3. FFmpeg 后置合成并验证：

```bash
# 合成（不重编码视频；<任务> = .super-video/<任务名>）
ffmpeg -y -i <任务>/render/visual_v01.mp4 -i <任务>/audio/bgm.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k \
  -t <root_duration+0.02> -movflags +faststart <任务>/deliver/<主题>_v01.mp4

# 验证：查音频流真实时长，并测尾段 RMS
ffprobe -v error -select_streams a:0 \
  -show_entries stream=codec_name,duration -of csv=p=0 <任务>/deliver/<主题>_v01.mp4
ffmpeg -ss <root_duration-12> -t 12 -i <任务>/deliver/<主题>_v01.mp4 \
  -af volumedetect -f null /dev/null 2>&1 | grep -E "mean_volume|max_volume"

# 或用脚本一步验证
python <skill>/scripts/verify_audio.py <任务>/deliver/<主题>_v01.mp4 \
  --min-duration <root_duration> --tail-seconds 12
```

通过标准：抽出音频时长 ≥ 视频时长 - 0.1s；末 12 秒每秒 RMS > -30dB；音量可闻不压人声（RMS 均值 -15dB ~ -20dB）。完整细节（含 BGM 生成原则与图层清单）见 `references/hyperframes-rendering.md` §8。

已有原片音频的成片**保留并后置合成原音频**，不合成替代音乐。

---

## 口播后期处理（已有视频加工）

对已录好的口播视频加字幕、叠特效、换背景、混音 BGM、画中画、多段拼接时，走后期管线。

**能力边界**：用户要求「精准时间对齐 / 字幕动效 / 转场特效 / 完整口播后期」时，必须走 HyperFrames 管线（素材预检 → 音频提取 → 转写 → 原文校对 → composition 编排 → 字幕/特效 → lint → render → FFmpeg 后置合成 → 验证），不得只用纯 FFmpeg + ASS 字幕烧录交付；后者只能做基础字幕，若坚持使用必须向用户说明能力有限。

**四阶段流程**：素材预处理（FFmpeg 标准化、提取音频）→ 语音转写与字幕分组 → composition 编排（字幕层/特效层/画中画/换背景）→ 音频混音（人声优先、ducking、-16 LUFS）。完整模板与命令见 `references/talking-head-pipeline-full.md`。

### 防错清单（处理已有口播视频必须执行）

**音频——不凭听感或渲染结果臆断：**
- 用户指定的原视频是唯一音频真源；用户说有 BGM 就有，不得擅自判断没有、不得自行合成替代。
- 用 FFmpeg `volumedetect` 验证用户指出的尾段，有有效音量就必须保留。
- 已有原片音频时：提取原音频 → 渲染视觉版 → FFmpeg 后置合成原音频，不依赖 HyperFrames 内置 mux。
- 交付前同时验证 `ffprobe` 时长与用户指出的尾段音量。

**字幕——用户原文优先级最高：**
- 用户指定的字幕逐字使用，不按 ASR 或模型理解"纠错"产品名。
- 每次修改只定位目标时间段的 `cap-*` 节点，不顺手改其它字幕。
- 交付前在回复中列出改动后的准确文本供用户核对。

**视觉迭代——严格按用户约束：**
- 用户要求删效果（光效/粒子/动效）时，删除对应 CSS、DOM、GSAP tween，不只设为透明。
- 位置调整按方向显式改坐标，并在交付说明中标注实际坐标变化。
- 改字体颜色时检查所有相关文本层（value、label、legend）。

**交付门禁：** 字幕关键片段与用户要求完全一致；音频关键段有有效音量；视频/音频流时长误差 ≤ 0.1s；用户本轮要求逐项核对无遗漏。

---

## 自检管线（交付前必须执行，两种模式通用）

此管线验证**技术安全和视觉完整性**，不约束风格。按顺序执行全部检查。

### Phase A：写 HTML 前校验

| # | 检查 | 详细提示词模式 | 简单提示词模式 |
|---|-------|---------------|---------------|
| A1 | 场景数 × 平均时长 = 总时长 | 按提示词场景规划 | AI 自行规划 |
| A2 | 内容密度与场景时长匹配 | 按提示词内容量 | 参考中文密度表 |
| A3 | 配色匹配 | 严格匹配提示词配色 | AI 自由选择 |
| A4 | 字体只用白名单（H2） | 必查 | 必查 |
| A5 | 无硬约束冲突 | 必查 | 必查 |

### Phase B：写完 HTML、渲染前

```bash
cd <任务>/composition
npx hyperframes lint                                                    # B1: 0 error 才算过
grep -n "Math.random\|Date.now\|PingFang\|Microsoft YaHei\|Noto Sans" index.html   # B2: 必须为空
grep -n 'style=.*top:.*%' index.html                                    # B3: 发现即删（H7）
grep 'data-composition-id.*data-duration\|data-start.*data-duration' index.html    # B4: 末场景结束 = 根时长
```

### Phase C：渲染后

以下检查针对 `deliver/` 里的成品（`<任务>/deliver/<主题>_v01.mp4`）。

| # | 检查 | 命令 | 通过标准 |
|---|-------|---------|---------------|
| C1 | 视频时长 | `ffprobe -show_format` | ≥ 目标 - 0.1s |
| C2 | 分辨率 | `ffprobe -show_streams` | 匹配用户要求 |
| C3 | 帧率 | `ffprobe -show_streams` | 30fps（除非用户要求 60fps） |
| C4 | 混音后音频时长 | `ffprobe -select_streams a:0` | ≥ 视频时长 |
| C5 | 末 12s 无静音 | 逐秒 RMS | 每秒 > -30dB |
| C6 | 音频均量 | `volumedetect` | -15dB ~ -20dB |

### Phase D：布局与视觉完整性（每个视频都做）

```bash
# 抽场景中点关键帧到系统临时目录（不落在任务目录里，检查完即弃）
ffmpeg -ss <mid_time> -i <任务>/deliver/<主题>_v01.mp4 \
  -frames:v 1 -q:v 2 "<系统临时目录>/check_scene_N.jpg"
```

通用检查：内容在画布内无裁切（H6）；文字无重叠不可读；卡片间距均匀无挤压；关键信息可读（字号、对比度）；过渡流畅无跳切（除非用户要求跳切风格）。使用软默认布局时额外检查：标题在顶部可见不与内容重叠；卡片都在安全区内。

任一检查失败 → 修复 → 重渲染 → 复验。最多 2 轮重试，仍失败则向用户报告具体问题。

### 常见坑速查

| 坑 | 根因 | 类型 | 预防 |
|---------|-----------|------|------------|
| 内容超出底部 | inline `top:XX%` | H7 | 用 CSS class 固定 px |
| 音频约 32s 处截断 | HyperFrames 内置音频缺陷 | H9 | FFmpeg 后置合成 |
| 帧不确定 | `Math.random()` | H1 | mulberry32 PRNG |
| lint 报字体无法解析 | 用了 PingFang SC 等 | H2 | 只用白名单字体 |
| GSAP 超出 composition | repeat 用 `Math.ceil` | H8 | 用 `Math.floor` |
| 空帧/黑帧 | `window.__timelines` 未注册 | H5 | 同步注册 |
| 卡片压住标题 | `translate(-50%,-50%)` 居中 | 自检 | Phase D 抽帧发现即修 |
| 2×3 网格间距不均 | 卡片宽对容器太小 | 自检 | Phase D 视觉检查 |
| 场景硬切 | 缺退场转场 | 自检 | 除非用户要求跳切 |
| 旁白停顿生硬 | 逐句拼接 + 固定静音 | H10 | 整段合成 |
| 字幕与语音对不上 | 手写/估算时间 | H11 | whisper 强制对齐 |
| 改文案后时间错乱 | 手改 data-start | H12 | 数据驱动重生成 |
| MiniMax 401 | 用了 api.minimax.io | 接口 | 用 `api.minimaxi.com` |
| MiniMax 2013 | 模型名大小写/后缀错 | H14 | 全小写精确版本 |

---

## 中文内容与多分辨率适配

- **中文密度参考**：15s 视频 3-4 场景；30s 视频 5-7 场景；60s 视频 8-12 场景。每场景 1 个主标题 + 1-3 个要点；短句、强对比、少行数；中文字号可比英文略大；避免长段落，改用卡片、短句、数字和关键词高亮；中英混排时英文产品名不强行翻译。
- **竖版 1080×1920**：标题 top 120-180px；主体 360-1560px；底部 320px 留给平台 UI；左右边距 60-80px；单列卡片优先，2-3s 一个信息点；主标题 72-96px，正文 38-52px，关键数字 96-132px。
- **图标**：优先 CSS/SVG/文字图标，不依赖外部 icon 库；禁止无法离线解析的 icon font；emoji 仅在语义明确、尺寸一致时使用，不替代关键信息。
- **性能与渲染策略**：draft 调试、standard 常规交付、high/60fps 仅在用户要求或精品交付时用；控制 DOM 数量，避免大量滤镜、超大阴影、复杂 SVG path；Chrome 崩溃时减 workers、降粒子、拆场景或降质量重试。
- **交付与文件**：产物全部落在 `.super-video/<任务名>/`（见「产物目录约定」）；成片命名 `<主题>_v01.mp4`，返工递增 `_v02`…，用户认可后定稿 `_final`；过程产物原样留在任务目录内，不主动清理；交付必须以附件返回 `deliver/` 里的成片，并说明分辨率、时长、是否含音频、做过哪些验证。

多分辨率字号/安全区速查、渲染耗时估算、性能优化细则见 `references/advanced-delivery-and-quality.md`。

---

## 返工决策树（Iterative Fix）

返工分四类，对号入座：

| 问题类别 | 修法 |
|---------|------|
| 文案/字幕错误 | 直接定位目标节点（`data-start`/`data-duration` 覆盖目标时间段），只改目标不顺手改其它 |
| 布局/溢出 | 先降内容密度、缩 gap/padding/字号；仍溢出则拆成两个连续场景 |
| 动效/节奏 | 先 `--quality draft` 快速验证，满意再 high |
| 音频错误 | 回到 FFmpeg 后置合成，跑 `scripts/verify_audio.py` 验证 |

通用流程：读文件 → 定位目标节点/样式/tween → 最小修改 → lint → draft render → 抽帧/音频验证 → final render。批量修改按「文案 → 布局 → 动画 → 音频 → 交付信息」的顺序处理。

---

## 已知限制与故障排查

- HyperFrames 内置长音频可能在约 32s 后截断；≥30s 一律 FFmpeg 后置合成（H9）。
- 禁止非确定性 JS、时间函数、异步 timeline；字体仅限可解析白名单（H1/H2/H3）。
- FFmpeg 缺失：安装后重跑 `npx hyperframes doctor`；Chrome 缺失：`npx hyperframes browser ensure`。
- 渲染挂起：检查 GSAP CDN、本地字体引用、异步 timeline、Chrome 沙箱。
- 0 字节 MP4：检查 FFmpeg 编码器（libx264/aac）与输出权限。
- 画面裁切：抽帧定位问题场景，降密度或拆场景。
- 音频不完整：重新后置 mux，运行 `scripts/verify_audio.py`。
- 字幕不准：优先用户原文，必要时重新转写并人工校对关键段。

---

## 交付门禁（最终检查）

交付前必须通过：

- 硬约束：H1-H14 无违规；`npx hyperframes lint` 0 error；根时长覆盖最后场景。
- **音画同步：抽 3-5 个时间点，当前字幕句 = 当前正在念的句子。**
- 视觉：抽帧检查无裁切、无重叠、可读、对比度足够、节奏自然；**长句字幕完整不截断/不溢出**。
- 音频：音频时长覆盖视频；尾段非静音；人声/BGM 比例合理。
- 提示词：用户要求的风格、配色、字幕、位置、分辨率、时长、音频处理逐项满足。
- 文件：输出文件可播放，体积合理，附件交付。

---

## References

按需读取：

| 文件 | 内容 |
|------|------|
| `references/narration-sync-pipeline.md` | **核心**——MiniMax 整段合成 → whisper 强制对齐 → 数据驱动画面 → 静态整句字幕的完整链路、设计原理 |
| `references/minimax-tts.md` | MiniMax t2a 接口、模型/音色清单、密钥与凭证惯例、Edge-TTS 回退 |
| `references/hyperframes-rendering.md` | composition 编写、多场景骨架、GSAP 动画规则、渲染旗标、常用配方、长音频 BGM 工作流 |
| `references/composition-rules.md` | composition/data attributes/variables/sub-composition 规则 |
| `references/animation-guide.md` | GSAP 动效、转场、时间轴实践 |
| `references/caption-patterns.md` | 字幕分组、样式和口播字幕模式 |
| `references/talking-head-pipeline-full.md` | 完整口播后期模板、混音策略与防错清单 |
| `references/advanced-delivery-and-quality.md` | 高级修复、多分辨率、性能、交付和质量门禁 |

脚本（`scripts/`，全部支持 `--workdir <任务目录>`，产物自动落到对应子目录）：

| 脚本 | 用途 | 默认产物（带 --workdir） |
|------|------|--------------------------|
| `minimax_narrate.py` | MiniMax 整段旁白合成（环境变量取 Key） | `audio/narration.mp3/.wav/_16k.wav` |
| `transcribe_narration.py` | faster-whisper 词级转写 | `audio/narration_words.json` |
| `build_timeline.py` | 文案 ↔ 词级时间戳强制对齐 | `audio/timeline.json` |
| `build_composition.py` | 由 timeline.json + scenes.json 生成 HTML | `composition/index.html` |
| `merge_audio.py` | FFmpeg 后置合成旁白(+BGM) | `deliver/<任务名>_<版本>.mp4` |
| `generate_bgm.py` | 无外部依赖的本地 BGM 生成 | `audio/bgm.wav` |
| `verify_audio.py` | 最终视频音频时长和尾段可听性验证 | 只读，不落盘 |
| `task_paths.py` | 共享模块：解析/创建任务目录下的产物路径（被以上脚本引用） | — |
| `text_units.py` | 共享模块：中文分词与时间单元切分（被 build_timeline 引用，场景切换点取首词时间） | — |

资源（`assets/`）：

| 资源 | 用途 |
|------|------|
| `voices.json` | 音色与模型配置 |
| `theme.css` | 场景卡片样式（可 `--theme` 追加） |
| `scenes.example.json` | scenes.json 参考模板 |
