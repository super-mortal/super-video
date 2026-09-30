# 口播视频同步管线（Narration Sync Pipeline）

本 reference 是本技能的核心：把「一段文案」变成「画面与语音严格同步的口播视频」。
它解释了**为什么**要这样做，以及每一步的踩坑与验证点。

---

## 0. 一句话概括

**音频定时间，画面跟着音频走。**

时间轴的真源不是 AI 的估算，而是**从真实合成音频里用 whisper 反推出来的词级时间戳**。
画面 HTML 的 `data-start`/`data-duration` 与字幕的出现时机，全部由这份时间轴**生成**，不允许手写。

```
文案 script.txt
   │ ① MiniMax 整段合成          → narration.mp3/.wav/_16k.wav（真实时长）
   │ ② faster-whisper 词级转写     → narration_words.json（每词的 start/end）
   │ ③ 文案字符 ↔ 词级字符 强制对齐  → timeline.json（每句/每词的准确时间）
   │ ④ 数据驱动生成               → index.html（时间从 timeline.json 注入）
   │ ⑤ HyperFrames 渲染           → visual.mp4（无声视觉）
   │ ⑥ FFmpeg 后置合成            → final.mp4（含旁白）
   │ ⑦ 验证                      → verify_audio.py + 抽帧
```

---

## 1. 为什么「整段合成」而不是「逐句合成」

早期版本把每句单独合成，再在句间拼固定静音（0.35s）。问题：

- 句间停顿生硬、机械，永远固定，不随语义变化；
- 句首/句尾被 TTS 各自的起收气影响，拼接处有明显"接缝"；
- 总时长被固定静音撑大，节奏变拖。

**正确做法（H10）：把整个脚本一次性丢给 TTS 合成一整段音频。** 模型自己处理句间语气与停顿，自然得多。

代价：整段合成后，**句子的真实起止时间不再由我们规定**，必须从音频反推 → 所以需要第 ②③ 步的强制对齐。

### 为什么不用「逐句合成 + 已知每句时长」

因为即使逐句合成拿到每句时长，句内**每个词**的时间仍不知道，而且逐句拼接的听感问题无法解决。整段合成 + 词级对齐是更彻底的方案。

---

## 2. 强制对齐（Forced Alignment）原理

**输入**：文案字符序列 A（我们知道用户写的是什么字），whisper 识别出的字符序列 B（每个字符带真实时间）。

**问题**：TTS 和 whisper 都可能有细微差异（同音字、漏字、多字、标点、数字读法），A 与 B 不会逐字相等。

**做法**：`difflib.SequenceMatcher` 求 A→B 的最长匹配子序列，`equal` 段直接取 whisper 的时间；非 equal 段（replace/insert/delete）按线性插值补齐。

```
A:  现 在 很 多 A I 编 程 工 具
B:  现 在 很 多 A I 编 程 工 具     → 全部 equal，直接取时间
```

```
A:  P o w e r S h e l l 7
B:  p o w e r  s h e l l 七        → "7"↔"七" 不同，插值处理
```

关键点：对齐的是**归一化字符**（只保留 CJK 与拉丁数字，统一小写，去标点/空格），所以中英混排也稳。

**相似度（similarity）是体检指标**：`sm.ratio()` 输出。正常情况下 ≥ 0.9。
- 若 < 0.85：说明文案与音频差异过大——极可能是**改了稿却没有重新合成音频**，或转写模型太小。
- 处置：重跑合成（确保音频 = 当前文案），必要时换 `--model medium` 转写。

---

## 3. 字幕切分与静态字幕

### 切分（tokenize）

- tokenize 用于 `build_timeline.py` 的词级切分（场景切换点依赖首词时间），拉丁串与标点规则保持一致；
- 拉丁串（如 `PowerShell`）作为一个整体单元，标点（。！？，；：、…—）处断开。

### 字幕样式（静态整句，无逐词高亮）

- 字幕 = 该场景的整句文案，随场景整体出现/消失，不做逐词打点、无动画切换；
- 默认 44px 加粗白字，底部 74px 居中；暗色场景无底板；
- 浅色/复杂画面场景在 scenes.json 设 `"caption_bg": true`，字幕加浅黑直角透明方框（rgba(0,0,0,.25) + 轻毛玻璃）；
- 词级时间轴只用于**场景切换时间**与对齐报告；字幕为整句静态显示，不按词打点。

---

## 4. 场景时间怎么来

- 一句文案 = 一个场景（1:1）。
- 场景切换点 `cuts[i]` 取该句**首词时间 - lead**（默认 0.12s 提前量），保证画面先于话音切换，不"卡词"。
- 首场景从 0 开始；末场景到 `audio_dur + tail`（默认尾部多 0.9s，留收尾）。
- `root_duration = total`，覆盖最后场景。

这些全部由 `build_timeline.py` 计算并写进 `timeline.json`，`build_composition.py` 原样注入 HTML。

---

## 5. 数据驱动的意义（H12）

`scenes.json` 里**只有画面**，没有时间。时间只在 `timeline.json` 里。

好处：
- 改文案 → 重新合成 → 重跑对齐 → 重新生成 HTML，**时间自动跟上**，不会出现"改了字但时间还是旧的"的漂移；
- 同一套画面可换音色/换模型重做（重跑 ①-④，画面文件不动）；
- 杜绝"手写 data-start 抄错一位"这类低级错误。

`build_composition.py` 生成时还会校验 `timeline.json` 场景数 == `scenes.json` 场景数，不一致直接报错退出。

---

## 6. 渲染与后置合成

1. HyperFrames 渲染的是**无声视觉版**（`visual.mp4`）。不要依赖内置 `<audio>`——≥30s 会在约 32s 截断（H9）。
2. FFmpeg 后置合成旁白：
   ```bash
   python scripts/merge_audio.py visual.mp4 narration.wav -o final.mp4
   ```
   - 旁白为准，`apad`+`atrim` 对齐到视频长度；
   - 可选 `--bgm bgm.wav --bgm-gain -26` 铺底；
   - `-c:v copy` 视频不重编码，只加 AAC 音轨。

---

## 7. 验证清单（不可省）

| 项 | 命令 / 方法 | 通过标准 |
|----|-----------|---------|
| lint | `npx hyperframes lint` | 0 error |
| 音频时长覆盖 | `verify_audio.py final.mp4 --min-duration <root>` | 通过 |
| 尾段非静音 | 同上（`--tail-seconds 12`） | 每秒 RMS > -30dB |
| 画面完整性 | 每场景中段抽帧 | 无裁切/溢出/重叠 |
| **字幕完整** | 抽帧看长句字幕 | 不截断、不溢出画布 |
| **音画同步** | 3-5 点抽帧 | 高亮词 ≈ 当前所念词 |

---

## 8. 常见症状 → 处置

| 症状 | 根因 | 处置 |
|------|------|------|
| 字幕与语音错位 | 手写了时间 / 改了稿没重合成 | 重跑 ②③④，别手改 |
| 高亮整体偏一位 | JS 用了 `bar.children[wi]` | 改 `querySelectorAll('.cw')[wi]` |
| 句子切换卡词 | lead 太小 | 增大 `--lead` |
| 尾部语音被切 | tail 太小 / 视频比音频短 | 增大 `--tail` 或检查 mux |
| 全片无字幕高亮 | `__timelines` 未注册 / SUBS 为空 | 检查生成脚本输出与注册 |
| similarity < 0.85 | 文案≠音频 | 重新整段合成 |
| 字幕溢出画布 | 单屏字数过多 | 降 target 字数 / 降字号 |

---

## 9. 完整命令序列（复制即用）

```bash
# ① 合成（需 MINIMAX_API_KEY）
python scripts/minimax_narrate.py script.txt -o narration \
    --model speech-2.8-hd --voice female-shaonv

# ② 转写
python scripts/transcribe_narration.py narration_16k.wav -o narration_words.json

# ③ 对齐
python scripts/build_timeline.py script.txt narration_words.json narration.wav -o timeline.json

# ④ 生成 HTML（画面写在 scenes.json）
python scripts/build_composition.py timeline.json scenes.json \
    -o index.html --theme assets/theme.css

# ⑤ lint + 渲染
npx hyperframes lint
npx hyperframes render --quality draft --output visual_draft.mp4   # 先草稿
npx hyperframes render --quality high  --output visual.mp4         # 再成片

# ⑥ 后置合成
python scripts/merge_audio.py visual.mp4 narration.wav -o final.mp4

# ⑦ 验证
python scripts/verify_audio.py final.mp4 --min-duration <root_duration> --tail-seconds 12
```
