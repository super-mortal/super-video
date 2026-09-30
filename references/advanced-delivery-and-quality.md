<!-- Extracted from SKILL.md during SkillHub length optimization. Keep as reference; SKILL.md links here for progressive loading. -->

## 目录

1. [Sub-Compositions](#sub-compositions)
2. [Variables (Parametrized Compositions)](#variables-parametrized-compositions)
3. [Iterative Fix Decision Tree](#iterative-fix-decision-tree)
4. [Chinese Content Adaptation](#chinese-content-adaptation-soft-default--中文适配参考)
5. [Vertical Video Safe Zones](#vertical-video-safe-zones-p1--10801920)
6. [Icon & Emoji Strategy](#icon--emoji-strategy-p1)
7. [Render Time Estimation](#render-time-estimation-p1)
8. [Performance Optimization](#performance-optimization-p2)
9. [Multi-Resolution Adaptation](#multi-resolution-adaptation-p2)
10. [Delivery & File Management](#delivery--file-management-p2)
11. [Quality Checklist (Final Gate)](#quality-checklist-final-gate--交付前必过)
12. [已知限制](#已知限制)
13. [Troubleshooting](#troubleshooting)

## Sub-Compositions

For complex videos, split into separate HTML files:

```html
<!-- In index.html -->
<div id="scene-1" data-composition-id="intro"
     data-composition-src="compositions/intro.html"
     data-start="0" data-duration="5" data-track-index="1"></div>
```

Sub-composition files use `<template>` wrapper (main index.html does NOT):

```html
<template id="intro-template">
  <div data-composition-id="intro" data-width="1920" data-height="1080">
    <!-- content, style, script -->
  </div>
</template>
```

## Variables (Parametrized Compositions)

Declare on `<html>` root, read with `window.__hyperframes.getVariables()`:

```html
<html data-composition-variables='[
  {"id":"title","type":"string","label":"Title","default":"Hello"},
  {"id":"accent","type":"color","label":"Accent Color","default":"#ff6b35"}
]'>
```

Override at render: `npx hyperframes render --variables '{"title":"Q4 Report"}'`

## Iterative Fix Decision Tree

When the user requests modifications after initial delivery, follow this decision tree to minimize re-work:

### Fix Classification

| Change type | Scope | Actions required |
|------------|-------|-----------------|
| **Text/data change** | Single scene content | Edit HTML → Lint → Re-render → Re-mux audio → Verify |
| **Layout/position fix** | CSS class or inline style | Edit CSS → Lint → Re-render → Re-mux audio → Verify |
| **Color/style change** | CSS variables or colors | Edit CSS → Lint → Re-render → Re-mux audio → Verify |
| **Animation timing** | GSAP parameters | Edit JS → Lint → Re-render → Re-mux audio → Verify |
| **Add/remove scene** | Structure change | Edit HTML+JS → Recalculate all timings → Lint → Re-render → Re-mux → Verify |
| **BGM style change** | Audio only | Only when user requested BGM change: regenerate/replace BGM → Re-mux only (skip re-render) → Verify audio |
| **Duration change** | Everything | Full rebuild required |

### Quick-Fix Workflow (for text/layout/color/animation changes)

```text
1. Identify affected scene(s) — read current HTML
2. Make targeted edit(s) — ONLY touch affected parts
3. npx hyperframes lint — must pass
4. npx hyperframes render --quality draft — fast preview check
5. If draft looks good → render --quality standard
6. Re-mux the approved audio source (original_audio.wav for existing videos, bgm.wav only for generated-BGM projects)
7. Verify final MP4 (Phase C+D checks)
8. Deliver
```

**Key optimization: DO NOT regenerate or replace audio** unless the user requests a music style change or duration change. For existing source videos, reuse the extracted `original_audio.wav`; for generated-BGM projects, reuse the existing approved `bgm.wav` across layout/content fixes.

### When to Use `--quality draft` First

ALWAYS render draft quality first when:
- Fixing layout issues (verify position before full render)
- User reported visual problems (confirm fix before spending 10+ minutes)
- Making multiple iterative adjustments (draft → confirm → standard)

Draft renders at ~3x speed. Only proceed to `standard` after visual confirmation.

### Batch Fix Strategy

When user reports multiple issues at once:
1. Collect ALL reported issues
2. Fix ALL issues in a single pass (edit HTML once)
3. Lint once
4. Render once (not once per fix)
5. Verify all fixes in the rendered output

NEVER render between each individual fix — that wastes 10+ minutes per cycle.

---

## Chinese Content Adaptation (Soft Default — 中文适配参考)

以下规则是中文视频的**经验参考**，帮助 AI 在用户未给出详细排版指示时做出合理的中文布局决策。**当用户的提示词有明确的排版/密度/风格要求时，以用户要求为准。**

### Text Density Reference

| Scene duration | 建议中文字数 (同时在屏) | 建议内容项数 |
|---------------|-------------------------|-------------|
| 3 seconds | 60-80 字 | 3-4 items |
| 4 seconds | 80-120 字 | 4-6 items |
| 5+ seconds | 120-160 字 | 6-8 items |

**自检关注点**: 如果某场景文字过密导致不可读（字号 ≤ 28px 且停留 ≤ 3s），AI 应自动拆分——这是可读性问题，不是风格限制。

### Chinese Typography CSS (推荐实践)

```css
/* Line breaking — keep Chinese words together */
.content-area, .content-col, .glass-card {
  word-break: keep-all;        /* prevent mid-word breaks */
  overflow-wrap: break-word;   /* break only at natural points */
  line-break: strict;          /* no punctuation at line start */
}

/* Chinese line height — wider than English */
p, span, .card-desc { line-height: 1.6; }   /* body text */
h2, h3 { line-height: 1.3; }                /* titles */

/* Mixed CJK + Latin spacing */
.mixed-text { text-spacing-trim: space-all; } /* if supported */
/* Fallback: manually add thin space between Chinese and numbers/English */
```

### Chinese-English Mixed Content Conventions

| Pattern | Example | Rule |
|---------|---------|------|
| Number + Chinese unit | `128亿美元` | No space between number and Chinese |
| English brand + Chinese | `GitHub Copilot 工具` | Space between English and Chinese |
| Percentage | `156%` or `156％` | Use half-width `%` (more compact) |
| Punctuation | `，、。；` | Use full-width Chinese punctuation in body text |
| Data labels | `市场规模：` | Use full-width colon `：` in Chinese context |
| Card titles | `核心技术突破` | No trailing punctuation on card titles |

### Chinese Layout Adjustments (参考)

Chinese characters are wider than Latin characters. 当 AI 自行规划布局时可参考：

| Element | English width | Chinese adjustment |
|---------|--------------|-------------------|
| Card title | 40-44px | 38-42px (reduce 2px) |
| Body text | 34-38px | 32-36px (reduce 2px) |
| Card width | 360px | 380-400px (increase 20-40px) |
| Line chars | ~40 chars/line | ~18-22 中文字/行 |

### Scene Content Text Templates (灵感参考，非必须)

```text
数据展示场景:
  主数据: "128亿" (数字 88-96px + 单位 42px)
  标签: "市场规模" (38px, opacity 0.7)

卡片场景:
  图标: 64-72px emoji/SVG
  卡片标题: "核心技术突破" (40px, bold)
  描述文字: "一句话说明功能或数据" (32-34px, opacity 0.8)
  底部标注: "具体数据或来源" (28px, opacity 0.6)

列表场景:
  序号: "01" (56px, accent color)
  内容: "一行描述，不超过25字" (36px)

NOTE: 以上仅为参考模板。AI 完全可以使用不同的信息层级、卡片结构或数据展示方式。
```

---

## Vertical Video Safe Zones (P1 — 1080×1920)

### Layout System for 9:16 Vertical Videos

```
┌───────────────────────┐
│ Top Safe: 120px       │ ← Platform UI (status bar)
├───────────────────────┤
│ Title Zone:           │
│ top 160px, h ≤ 200px  │
├───────────────────────┤
│                       │
│ Content Zone:         │
│ top 400px ~ bot 1600px│ ← Available: 1200px
│                       │
├───────────────────────┤
│ Bottom Safe: 320px    │ ← Platform UI (controls, comments)
└───────────────────────┘
```

### Vertical Video Typography Scale

| Element | Safe range | Hard max |
|---------|-----------|----------|
| Cover mega title | 120-160px | 180px |
| Scene title | 80-100px | 120px |
| Subtitle | 48-64px | 72px |
| Body text | 36-48px | 56px |
| Card title | 40-52px | 56px |
| Data number | 96-128px | 140px |
| Icon/emoji | 72-108px | 128px |

### Vertical Content Rules

- Max 2 cards horizontally (full width), prefer single-column stacking
- Card width: 90% container (≈ 972px)
- Scene transitions: faster pacing (2-3s per scene typical for Reels/TikTok)
- Bottom 320px always clear (platform overlays on mobile)
- Horizontal safe margin: ≥ 60px (narrower than landscape)

---

## Icon & Emoji Strategy (P1)

### Recommended Approach Priority

1. **Unicode Emoji** (first choice for most cases)
   - ✅ Renders consistently in Chrome Headless
   - ✅ No external dependencies
   - ✅ Supports all common categories
   - ⚠️ Style varies slightly across platforms (but video rendering uses Chrome's Noto Emoji)

2. **Inline SVG** (when custom icons needed)
   - ✅ Pixel-perfect control
   - ✅ Animatable with GSAP
   - ✅ Color matches theme exactly
   - ⚠️ Increases HTML file size

3. **CSS-drawn shapes** (for simple geometric icons)
   - ✅ No external resources
   - ✅ Fully animatable
   - ⚠️ Limited to simple shapes

### PROHIBITED approaches
- ❌ Font Awesome / Material Icons CDN (render environment may not load)
- ❌ External image URLs (network dependency = unreliable)
- ❌ Icon font `@import` (same issue as Google Fonts)

### Common Tech Video Icon Set (copy-paste ready)

```text
Categories:
💻 编程/开发   🚀 发布/增长   📊 数据/图表   🔧 工具/设置
🎯 目标/聚焦   ⚡ 性能/速度   🔒 安全/隐私   🌐 网络/全球
📱 移动端      🤖 AI/机器人   🎮 游戏        🏗️ 架构/构建
💡 创新/灵感   📈 增长/趋势   🛡️ 防护/安全   ⏱️ 时间/效率

Specific use cases:
Web开发: 🌐    移动应用: 📱    AI/ML: 🤖    游戏: 🎮
网络安全: 🔒   数据科学: 📊    代码: 💻     部署: 🚀
效率: ⚡       质量: ✅        风险: ⚠️     趋势: 📈
```

### Icon Sizing Rules

```css
/* Standard icon in card */
.card-icon { font-size: 64px; line-height: 1; }

/* Small inline icon */
.inline-icon { font-size: 48px; vertical-align: middle; }

/* Feature highlight icon */
.feature-icon { font-size: 72px; }

/* NEVER exceed these for icons: */
/* Horizontal video: 96px max */
/* Vertical video: 128px max */
```

### Custom SVG Icon Template

```html
<!-- Reusable SVG icon pattern for tech videos -->
<svg width="64" height="64" viewBox="0 0 64 64" fill="none">
  <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="2" opacity="0.3"/>
  <path d="M20 32 L28 40 L44 24" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
</svg>
```

---

## Render Time Estimation (P1)

### Estimated Render Duration by Quality

| Quality | Speed ratio | 10s video | 30s video | 42s video | 60s video |
|---------|------------|-----------|-----------|-----------|-----------|
| `draft` | ~6fps | ~2 min | ~5 min | ~7 min | ~10 min |
| `standard` | ~3fps | ~3 min | ~10 min | ~14 min | ~20 min |
| `high` | ~1.5fps | ~7 min | ~20 min | ~28 min | ~40 min |

*Times are approximate. Complex scenes (many particles, gradients, blur filters) render slower.*

### Factors That Increase Render Time

| Factor | Impact | Mitigation |
|--------|--------|-----------|
| `backdrop-filter: blur()` | +30-50% | Limit to 3-4 elements max |
| > 50 particles | +20% | Cap at 40, reduce size |
| Multiple box-shadows | +15% | Use single subtle shadow |
| 60fps (vs 30fps) | +100% | Use 30fps unless requested |
| Large video backgrounds | +40% | Use gradient/CSS backgrounds instead |

### User Communication Template

Before starting a render, inform the user:

```text
"开始渲染 [质量] 品质视频（[时长]秒），预计需要 [X-Y] 分钟。
渲染期间我会持续检查进度，完成后立即进行音频合成和质量验证。"
```

### Render Strategy Decision

```text
用户要求"快速看一下效果" → --quality draft
用户要求"正式版/最终版"  → --quality standard
用户明确说"最高画质"     → --quality high --fps 60
修复布局问题验证        → --quality draft (先确认再正式渲染)
```

---

## Performance Optimization (P2)

### DOM Element Limits

| Complexity level | Max DOM elements | Max particles | Max cards | Render impact |
|-----------------|-----------------|---------------|-----------|---------------|
| Light | < 200 | 20 | 3-4 | Normal speed |
| Medium | 200-500 | 40 | 6-8 | +20% time |
| Heavy | 500-1000 | 60 | 10-12 | +50% time |
| Danger zone | > 1000 | > 80 | > 15 | May crash Chrome |

### Optimization Techniques

```css
/* Use will-change for animated elements (Chrome optimization) */
.scene-wrapper, .glass-card, .particle {
  will-change: transform, opacity;
}

/* Reduce paint complexity */
.particle {
  border-radius: 50%;
  /* Use background-color, NOT box-shadow for particles */
  background: currentColor;
}

/* GPU-accelerated properties only */
/* PREFER: transform, opacity */
/* AVOID: width, height, top, left, margin, padding, box-shadow (triggers layout) */
```

### When Chrome Crashes During Render

1. Reduce `--workers` to 1: `npx hyperframes render --workers 1`
2. Remove excessive particles (cap at 30)
3. Replace `backdrop-filter: blur()` with pre-blurred gradient backgrounds
4. Remove multiple `box-shadow` layers
5. If still crashing: split into shorter sub-compositions, render separately, concatenate with FFmpeg

### Render Timeout Handling

If render exceeds 20 minutes for a ≤ 60s video:
1. Check if Chrome process is still alive (`ps aux | grep chrome`)
2. If frozen: kill and retry with `--workers 1 --quality draft`
3. If draft succeeds: the standard render had a resource issue → simplify complex scenes
4. Report specific scene if identifiable (check last rendered frame number in output)

---

## Multi-Resolution Adaptation (P2)

### Supported Canvas Sizes

| Aspect ratio | Resolution | Use case | Init config |
|-------------|-----------|----------|-------------|
| 16:9 横版 | 1920×1080 | YouTube, 公众号, B站 | `data-width="1920" data-height="1080"` |
| 9:16 竖版 | 1080×1920 | 抖音, Reels, 视频号 | `data-width="1080" data-height="1920"` |
| 1:1 正方形 | 1080×1080 | Instagram Feed, 小红书 | `data-width="1080" data-height="1080"` |
| 4:5 竖版 | 1080×1350 | Instagram Feed (推荐) | `data-width="1080" data-height="1350"` |
| 4:3 标准 | 1440×1080 | 演示文稿风格 | `data-width="1440" data-height="1080"` |

### Per-Resolution Safe Zone Quick Reference

| Resolution | Title top | Content top | Content bottom | Side margin |
|-----------|-----------|-------------|----------------|-------------|
| 1920×1080 | 50px | 240px | 980px | 120px |
| 1080×1920 | 160px | 400px | 1600px | 60px |
| 1080×1080 | 50px | 200px | 980px | 80px |
| 1080×1350 | 80px | 260px | 1200px | 80px |

### Resolution-Specific Typography Scale

| Element | 1920×1080 | 1080×1920 | 1080×1080 |
|---------|-----------|-----------|-----------|
| Mega title | 96-120px | 120-160px | 80-100px |
| Scene title | 64-84px | 80-100px | 56-72px |
| Body text | 28-42px | 36-48px | 28-38px |
| Card title | 32-44px | 40-52px | 30-40px |
| Icon | 56-96px | 72-108px | 48-80px |

### Cross-Resolution Card Layouts

```text
1920×1080 (横版):
  3 horizontal cards: 480px each + 36px gap
  2×3 grid: 520px × 300px cards
  
1080×1920 (竖版):
  2 horizontal cards: 480px each + 24px gap
  1-column stack: 920px wide cards
  
1080×1080 (正方形):
  2 horizontal cards: 460px each + 24px gap
  2×2 grid: 460px × 340px cards
```

---

## Delivery & File Management (P2)

### File Naming Convention

```text
{project_name}_{version}_{quality}.mp4

Examples:
  ai_coding_video_v1_standard.mp4      ← first delivery
  ai_coding_video_v2_standard.mp4      ← after layout fix
  ai_coding_video_v3_standard.mp4      ← after content update
  ai_coding_video_final_standard.mp4   ← user-approved final
```

### Intermediate File Cleanup

After user approves a final version:
```bash
# Keep: final approved MP4, source HTML, bgm.wav
# Remove: intermediate renders
rm -f render_v1.mp4 render_v2.mp4 render_v3.mp4
rm -f final_ai_coding_v1.mp4 final_ai_coding_v2.mp4
# Keep: final_ai_coding_v3.mp4 (or rename to _final)
```

**Rule**: Never auto-delete intermediate files without user confirmation. Ask: "是否清理中间渲染文件？只保留最终版本。"

### Delivery Checklist

Before calling `deliver_attachments`:
1. ✅ File is the post-mux version (not raw render)
2. ✅ Audio verified (Phase C checks passed)
3. ✅ File size reasonable (1080p 42s ≈ 5-15MB for standard quality)
4. ✅ Filename clearly indicates version

### What to Preserve for Future Edits

Always keep in project directory:
- `index.html` — source composition (for re-editing)
- `original_audio.wav` — extracted original audio for existing-video edits, when source audio must be preserved
- `bgm.wav` — approved BGM audio only when the project uses generated or external BGM
- Customized copies of bundled helper scripts only if they were modified for this project (`scripts/verify_audio.py`, `scripts/generate_bgm.py` remain available in the Skill package)
- Final approved `.mp4` — the delivered product

## Quality Checklist (Final Gate — 交付前必过)

Before delivering any video, execute the full **AI Self-Check Pipeline** (Section 9). The checklist adapts to prompt mode:

### 硬约束检查（两种模式都必须通过）

1. **Lint pass**: `npx hyperframes lint` → 0 errors. (H-all)
2. **No prohibited code**: No `Math.random`, no banned fonts, no inline `top:%` overrides. (H1, H2, H7)
3. **Deterministic rendering**: No non-deterministic APIs, GSAP repeat uses `Math.floor`. (H1, H8)
4. **Root duration alignment**: `data-duration` on root = last scene end time.
5. **Audio full coverage** (≥30s video): FFmpeg post-mux → verify duration ≥ video, no silence in last 12s, RMS -15~-20dB. (H9)
6. **Visual integrity**: All content within canvas bounds, no clipping, no unreadable overlaps. (H6)
7. **Final delivery**: Only deliver the verified post-mux MP4. Never send intermediate renders.

### 视觉质量检查（两种模式都必须通过）

8. **Frame spot-check**: Extract mid-scene screenshots → verify no overlap/overflow/clipping.
9. **Readability**: 关键文字可读（字号 + 对比度 + 停留时间足够）.
10. **Transitions**: 场景之间有过渡，无未经用户要求的跳切.

### 提示词合规检查（详细提示词模式）

11. **Prompt compliance**: Content points, visual style, **color palette (user-specified, never overridden)**, BGM style, duration all match original prompt.

### 布局参考检查（仅使用软默认布局时）

12. **Standard layout zone**: Content ≥ 240px, ≤ 980px; Title zone not overlapped.
13. **Card density**: Compute `content_height` vs `available_height`. If overflow → reduce/split.
14. **Typography scale**: Text/icon sizes within reference range hard max.

**Note**: Items 12-14 仅在 AI 使用了标准布局骨架时检查。如果 AI 根据用户提示词或创意判断使用了自定义布局，这些项被替换为 Item 8 (frame spot-check) 的通过即可。

## 已知限制

| # | 限制 | 影响 | 应对方式 |
|---|------|------|---------|
| 1 | HyperFrames 内置音频 ≥32s 截断 | 长视频音频不完整 | FFmpeg 后置合成完整音频 (H9) |
| 2 | 仅支持 Inter/JetBrains Mono/Roboto 字体 | 中文字体无法自定义 | 依赖 sans-serif 系统回退 |
| 3 | 不支持 `@import url()` 引入字体 | 自定义 Google Fonts 不可用 | 仅用 Compiler 自动解析的字体 |
| 4 | 渲染需 Headless Chrome + FFmpeg | 无法在纯容器环境直接运行 | 需安装完整依赖或使用 Docker |
| 5 | 非确定性 API 会导致帧不一致 | `Math.random()` 等使渲染结果不可复现 | 使用 mulberry32 seeded PRNG |
| 6 | 单次渲染 DOM 复杂度上限 ~500 节点 | 超出可能导致 Chrome crash | 拆分场景或简化 DOM |
| 7 | 竖版视频 (1080×1920) 为实验性支持 | 部分动画比例需手动调整 | 使用竖版安全区参考表 |
| 8 | 渲染速度受机器性能影响 | 42s 视频约需 3-8 分钟渲染 | 开发阶段用 draft 模式预览 |

---

## Troubleshooting

```bash
npx hyperframes doctor         # Check environment
npx hyperframes browser        # Manage bundled Chrome
npx hyperframes info           # Version details
```

Common issues:
- "FFmpeg not found" → `brew install ffmpeg`
- "Chrome not found" → `npx hyperframes browser` to download
- Render hangs → Check for `repeat: -1` in timelines
- Empty frames → Ensure `window.__timelines` is registered synchronously

## References
