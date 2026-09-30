# MiniMax TTS 接口与凭证（MiniMax TTS Reference）

本 reference 说明旁白合成所用的 MiniMax 语音接口、可用模型/音色、密钥与凭证处理惯例，以及免费回退方案。

---

## 1. 接口

- **Base URL（国内区）**：`https://api.minimaxi.com/v1/t2a_v2`
  - 只有 `api.minimaxi.com` 与 `api.minimax.cn` 有效；`api.minimax.io` 会返回 **401**。
- **鉴权**：HTTP Header `Authorization: Bearer <MINIMAX_API_KEY>`。
- **单请求文本上限**：≤ 10000 字符（整段合成远达不到，正常旁白稿几百字）。
- **返回**：JSON，音频在 `data.audio`（当 `output_format=hex` 时为十六进制字符串）。
- **错误**：`base_resp.status_code != 0` 即失败。常见：
  - `2013` → 模型不可用（多为模型名大小写/后缀错误）。
  - 401 → Key 无效或域名错误。

### 请求体（本技能脚本所用）

```json
{
  "model": "speech-2.8-hd",
  "text": "整段旁白文案……",
  "stream": false,
  "language_boost": "Chinese",
  "output_format": "hex",
  "voice_setting": { "voice_id": "female-shaonv", "speed": 1.0, "vol": 1.0, "pitch": 0 },
  "audio_setting": { "sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1 }
}
```

`voice_setting`：
- `speed` 语速（1.0 正常）；
- `vol` 音量；
- `pitch` 音调（整数，0 默认）。

---

## 2. 可用模型（必须全小写 + 精确版本号，H14）

`status=0`（可用）的仅以下 8 个：

| 模型 | 定位 |
|------|------|
| `speech-2.8-hd` | **最新 + 高保真（默认）** |
| `speech-2.8-turbo` | 最新 + 快速 |
| `speech-2.6-hd` | 次新 + 高保真（本项目首次采用） |
| `speech-2.6-turbo` | 次新 + 快速 |
| `speech-02-hd` | 02 高保真 |
| `speech-02-turbo` | 02 快速 |
| `speech-01-hd` | 01 高保真 |
| `speech-01-turbo` | 01 快速 |

**不可用**（返回 2013）：`speech-2.5-*`、无后缀的 `speech-2.8`，以及任意大小写变体。
→ 记住：**全小写、带 `-hd`/`-turbo` 后缀、精确版本号。**

---

## 3. 音色（系统音色，50+）

常用中文音色（`voice_id`）：

| voice_id | 标签 | 适用 |
|----------|------|------|
| `female-shaonv` | 少女 | **默认**：通用解说/科技/教程 |
| `male-qn-qingse` | 青涩青年 | 男声/青年向 |
| `female-yujie` | 御姐 | 成熟女声 |
| `female-tianmei` | 甜美 | 轻松/生活向 |
| `Chinese (Mandarin)_News_Anchor` | 新闻主播 | 正式播报 |
| `Chinese (Mandarin)_Radio_Host` | 电台主持 | 谈话/夜话 |

（完整列表以平台文档为准；本技能默认取 `female-shaonv`。）

### 免费回退：Edge-TTS

无需 Key、需联网（微软云端合成），自然度略逊 MiniMax：

```bash
pip install edge-tts
edge-tts --voice zh-CN-XiaoyiNeural --text "..." --write-media out.mp3
```

| voice | 标签 |
|-------|------|
| `zh-CN-XiaoyiNeural` | 女声-活泼 |
| `zh-CN-YunxiNeural` | 男声-青年 |

回退时仍需走「整段合成 → 转写 → 强制对齐 → 数据驱动生成」同一管线（H10/H11/H12 不因引擎改变）。

---

## 4. 密钥与凭证（H13）

### 硬规则

- **只从环境变量 `MINIMAX_API_KEY` 读取**；
- 脚本内**不得**出现任何明文 Key；
- **不得打印/回显 Token**（日志、报错、对话里都不行）；
- 未设置时脚本直接报错并提示设置方法，**绝不回退到硬编码**。

### 设置方法

```powershell
# Windows PowerShell（当前会话）
$env:MINIMAX_API_KEY = "sk-..."
# 持久化（用户级）
[Environment]::SetEnvironmentVariable("MINIMAX_API_KEY","sk-...","User")
```
```bash
# macOS / Linux
export MINIMAX_API_KEY="sk-..."
```

### 本机凭证惯例（参考 figma / ima 等技能）

这些技能统一采用「凭证托管」模式：
- 标准文件集：`get-token.sh`（类 Unix）+ `get-token.ps1`（Windows）+ `SETUP_TOKEN.md`；
- **每条命令内联取用 Token**，因为每次 shell 是独立进程，`export` 不会传递到下一条命令（这是被明确点名的反模式）；
- 平台托管模式下走本地代理/网关；本地回退模式读环境变量或 `~/.config/<skill>/` 下的凭据文件；
- **明文打印 Token 被明确禁止**。

MiniMax 目前无平台网关条目，故本技能采用最简单的**环境变量**方案，并在脚本内联取用（符合"不 export 传递"惯例）。

> 若将来接入平台凭证网关，可在 `minimax_narrate.py` 的 `key = os.environ.get(...)` 处改为先调 `get-token`，其余逻辑不变。

### 可选环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `MINIMAX_BASE_URL` | `https://api.minimaxi.com/v1/t2a_v2` | 接口地址 |
| `FFMPEG` / `FFPROBE` | 从 PATH 取 | 可执行文件路径 |

---

## 5. Token Plan 与计费（背景）

- 订阅制 Token Plan 覆盖 MiniMax **全系模型**（语言/图像/语音）。
- **排除**：MiniMax H3、音色设计（voice design）、快速复刻（voice clone）——这三项不在 Token Plan 内。
- 语音合成按字符计费；本技能一次旁白稿数百字符，成本极低。
- 定价参考页：`https://platform.minimax.cn/docs/guides/pricing-token-plan.md`。

---

## 6. 与旧方案（Kokoro）的差异

| 维度 | Kokoro-82M（旧，已弃用） | MiniMax（现用） |
|------|------------------------|----------------|
| 部署 | 本地模型，无 Key | 云端接口，需 Key |
| 中文 | 需语言码 `cmn`（"zh" 报 phonemizer 不支持） | `language_boost=Chinese` |
| 音色 | 偏闷飘（`zf_xiaobei`） | 自然度高，可选音色多 |
| 合成方式 | 曾逐句拼接（句间固定静音） | **整段合成**（H10） |
| 成本 | 免费 | 按字符，Token Plan 内含 |

---

## 7. 排错速查

| 现象 | 原因 | 处置 |
|------|------|------|
| 401 | 域名错误（用了 `api.minimax.io`）或 Key 无效 | 改 `api.minimaxi.com`；确认 Key |
| 2013 | 模型名非全小写/后缀错 | 用上表 8 个之一 |
| `MINIMAX_API_KEY 未设置` | 环境变量缺失 | 按上文设置 |
| 无 `data.audio` | 请求异常返回 | 看 `base_resp` 全文 |
| 音频能出但很闷 | 音色选择 | 换 `female-shaonv` 等 |
