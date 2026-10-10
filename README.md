<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="超级视频 super-video —— 一段写好的文案，一键成为带中文配音与同步字幕的成片">
</p>

<h3 align="center">把写好的脚本，从零做成配音、同步字幕、动画画面齐备的成片视频</h3>
<p align="center">全程 AI 自动化 · 无需真人出镜 · 无需视频剪辑软件</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.0.4-1A1A18?style=flat-square" alt="version 0.0.4">
  <img src="https://img.shields.io/badge/license-MIT-1A1A18?style=flat-square" alt="license MIT">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-1A1A18?style=flat-square" alt="platforms">
</p>

## 安装

本技能是一个标准的 Agent Skill，可通过 [`skills`](https://skills.sh) CLI 一行安装（任一即可）：

```bash
# 安装到当前项目（交互式选择目标 Agent）
npx skills add super-mortal/super-video

# 安装到用户目录，所有项目可用
npx skills add super-mortal/super-video -g

# 非交互安装到指定 Agent（CI 友好）
npx skills add super-mortal/super-video --skill super-video -a codebuddy -y
```

```bash
# 先看看仓库里有哪些技能，不安装
npx skills add super-mortal/super-video --list

# 用复制而非软链安装（跨机器更稳）
npx skills add super-mortal/super-video --copy
```

> 兼容 Cursor、Claude Code、Codex、CodeBuddy 等 60+ 种 Agent；安装时会自动探测本机环境并写入对应目录（项目级 `./.<agent>/skills/`，全局 `~/.<agent>/skills/`）。

安装完成后，还需按下方[环境要求](#环境要求)准备运行依赖（Node.js、FFmpeg、Python、faster-whisper、MiniMax 密钥），即可开始生成视频。

## 实操效果展示

用本技能从零生成的完整成片（1920×1080，含配音与同步字幕），点击封面观看：

[![实操效果演示](demo-cover.jpg)](https://yun.52013142.us.ci/file/github/super-video/1790744540839.mp4)

## 它能做什么

- 从文字稿一键生成完整成片（15 秒 ~ 3 分钟），配音、字幕、画面一次到位
- 中文旁白配音：MiniMax 整段合成，5 种实测音色可选；无密钥时可免费回退 Edge-TTS
- 整句同步字幕：时间轴从真实音频反推，字幕随场景整句切换，改稿重跑后音画依旧严格同步
- 动画画面完全可定制：布局、配色、动画、字体均由 HTML/CSS 控制
- 支持按需 BGM 合成与音量调校，内置自检管线确保成片质量
- 也可加工已有口播视频：加字幕、叠特效、换背景、混音

## 工作原理

核心原则一句话：**音频定时间，画面跟着音频走。**

```
任务目录 .super-video/<任务名>/
 ① minimax_narrate.py      MiniMax 整段合成配音        → audio/narration.mp3 / .wav / _16k.wav
 ② transcribe_narration.py faster-whisper 词级转写     → audio/narration_words.json
 ③ build_timeline.py       文案字符 ↔ 词级字符 强制对齐 → audio/timeline.json（真实时间轴）
 ④ build_composition.py    数据驱动生成 HTML+GSAP 画面  → composition/index.html
 ⑤ hyperframes render      渲染无声视觉版              → render/visual_v01.mp4（半成品）
 ⑥ merge_audio.py          FFmpeg 后置合成旁白(+BGM)   → deliver/<主题>_v01.mp4（成品）
 ⑦ verify_audio.py         音频时长/尾段验证           → PASS/FAIL
```

## 环境要求

| 工具 | 说明 |
|------|------|
| Node.js 22+ | HyperFrames CLI 运行时 |
| FFmpeg 5.0+ | Windows: `winget install Gyan.FFmpeg`；macOS: `brew install ffmpeg`；Linux: `apt install ffmpeg` |
| Python 3.9+ | 运行技能脚本 |
| faster-whisper | `pip install faster-whisper`（本地词级转写） |
| MiniMax 密钥 | 环境变量 `MINIMAX_API_KEY`，或写入 `~/.config/minimax/api_key`（推荐，一次配置长期有效） |

## 快速开始

```bash
# ⓿ 开任务目录，把文案写进 <任务>/script.txt（<任务> = .super-video/<任务名>）
mkdir -p <任务>

# ① 合成配音（默认少女音，--voice 可换音色）
python <skill>/scripts/minimax_narrate.py <任务>/script.txt --workdir <任务>

# ② 词级转写
python <skill>/scripts/transcribe_narration.py <任务>/audio/narration_16k.wav --workdir <任务>

# ③ 强制对齐，生成真实时间轴
python <skill>/scripts/build_timeline.py <任务>/script.txt \
    <任务>/audio/narration_words.json <任务>/audio/narration.wav --workdir <任务>

# ④ 数据驱动生成画面（画面写在 <任务>/scenes.json，参考 assets/scenes.example.json）
python <skill>/scripts/build_composition.py <任务>/audio/timeline.json \
    <任务>/scenes.json --workdir <任务> --theme <skill>/assets/theme.css

# ⑤ 渲染（在 composition/ 内执行，先草稿再成片）
cd <任务>/composition
npx hyperframes lint
npx hyperframes render --quality draft --output ../render/visual_v01_draft.mp4 --quiet
npx hyperframes render --quality high  --output ../render/visual_v01.mp4 --quiet
cd -

# ⑥ 合成音轨（成品落 <任务>/deliver/<任务名>_v01.mp4）
python <skill>/scripts/merge_audio.py <任务>/render/visual_v01.mp4 \
    <任务>/audio/narration.wav --workdir <任务>

# ⑦ 验证
python <skill>/scripts/verify_audio.py <任务>/deliver/<任务名>_v01.mp4 \
    --min-duration <total> --tail-seconds 12
```

换音色/换模型只需重跑 ①-④（改一个 `--voice` 或 `--model` 参数），画面文件不动，时间轴自动跟随新音频重算。

## 音色

| 音色 | voice_id |
|------|----------|
| 少女（默认） | `female-shaonv` |
| 青涩青年 | `male-qn-qingse` |
| 御姐 | `female-yujie` |
| 甜美 | `female-tianmei` |
| 新闻主播 | `Chinese (Mandarin)_News_Anchor` |

无密钥时可免费回退 Edge-TTS（女声 `zh-CN-XiaoyiNeural` / 男声 `zh-CN-YunxiNeural`），仍走同一管线。

## 产物目录

一次任务的全部产物都归档在**当前工作目录**下的 `.super-video/<任务名>/`，不会散落各处：

```
.super-video/<任务名>/
├── script.txt          旁白文案（每行一句）
├── scenes.json         画面脚本（只写画面，不写时间）
├── audio/              音频与时间轴
├── composition/        HTML 画面（index.html）
├── render/             半成品：无声视觉版
└── deliver/            成品：含配音的成片
```

所有脚本支持 `--workdir <任务目录>`，默认产物自动落到对应子目录并创建父目录；显式 `-o` 仍然优先。

时间轴的唯一真源是**从真实音频反推的词级时间戳**，画面与字幕的全部时间由它生成——因此换音色、改稿重跑之后，音画永远同步。

## 目录结构

```
super-video/
├── SKILL.md          # 技能主文件：工作流、硬约束、产物目录约定、管线命令
├── scripts/          # 管线脚本（合成/转写/对齐/生成/混音/验证）
├── references/       # 深度参考文档（渲染、对齐原理、TTS、后期加工等）
└── assets/           # 音色配置、场景示例、主题样式
```

## 许可证

[MIT](LICENSE) © super-mortal

> 本项目部分灵感来源于 @zrzqbr
