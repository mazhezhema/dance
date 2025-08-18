# 广场舞App端到端解决方案 (从内容获取到成片交付)

> 目标：在 **3060 12G + 普通服务器** 条件下，稳定批量产出"**换脸换装（Viggle 已完成）+ 背景版权安全**"的成片；可扩展、可审计、可控成本。

## 0. 总体架构（Pipeline 一览）

```
[内容获取] → [（可选）AI 人物生成/替换] → [Viggle 动作/风格生成]
→ [清晰化超分] → [抠像] → [背景库（免版权/AI生成/自拍/有限制爬取）]
→ [Loop 化] → [无限循环合成] → [质检 & LUT 调色] → [导出 & 上线] → [留痕 & 审计]
```

## 1. 内容获取（前置素材）

### 1.1 官方来源（强推荐）

* **正版/自有网盘**：来自合作方/自采的舞蹈教学或原视频，留存授权证明。
* **免版权平台（视频）**：Pexels、Pixabay、Mixkit、Coverr（**商用可用**、有 License）。
* **音乐**：尽量使用免版权/自有版权音乐；若引用热门曲目，走平台合规路径（或自行混音/改编降低识别）。

### 1.2 （可选）有限制爬取（不推荐为主流程）

* 原因：**ToS/版权风险高**。若必须做：**仅针对 CC0/明确开放授权源**，遵守 robots/限速，**强制保存 license 链接、时间戳和快照**，并做去重（pHash+MD5）。
* **不要**爬取来历不明的短视频/网盘内容作为背景或主体。

## 2. AI 人物生成 / 替换策略

### 2.1 Route A（继续用 Viggle）

* **免费/Pro/Live 套餐**：建议至少 **Pro**（1080p、无水印、10 分钟上传长度），批量时评估 Credits（见成本分析）。
* **拆段方案（可选）**：按 1 分钟切片 → 生成 → FFmpeg 无损拼接，降低失败重跑成本（总 credits 不省，但更稳）。

### 2.2 Route B（自建替换/风格化）

* **换脸**：InsightFace/SimSwap/Roop（本地 GPU 批量跑，易控成本）。
* **换装**：ControlNet（OpenPose/DensePose）或静帧"Outfit-Anyone"再逐帧合成（速度慢于 Viggle，但更可控）。
* **何时选 B**：Viggle 成本过高或风格不可控时。

## 3. 背景库（版权安全的关键）

### 3.1 三种来源的组合（70/20/10 配比建议）

1. **免版权平台（70%）**：Pexels / Pixabay / Mixkit / Coverr
   * 筛选：固定机位/轻移动、无人物/无 Logo/无可识别文字、≥1080p/30fps。
   * **保存 license JSON**（provider、asset_id、license_url、下载时间、MD5）。

2. **AI 生成（20%）**：Pika/Runway/Stable Video Diffusion
   * Prompt 示例：*"static wide shot, night city plaza, soft bokeh neon lights, no people, no text, cinematic background, seamless loop, 1080p, 30fps"*
   * 生成 3–5 秒，后续做 Loop。

3. **自拍/自制（10%）**：手机/相机 + 三脚架
   * 场景：公园/广场/舞台、白天/夜景多版本、**无人物/无商标**；5–10 分钟固定机位素材/条。

### 3.2 十大分类与关键词（用于 API 检索）

1. 流行广场舞：`night city lights`, `neon street`, `concert stage lights`
2. 经典老歌舞：`community square evening`, `park sunset`, `city square dusk`
3. 民族舞/秀：`traditional architecture night`, `temple lights`, `cultural square`
4. 健身操/形体操：`fitness studio background`, `stadium lights`, `green field`
5. 养生太极/健康操：`morning park mist`, `lake sunrise`, `mountain sunrise`
6. 舞队PK：`city skyline night`, `spotlight smoke`, `urban plaza night`
7. 教学分步学：`dance studio clean`, `minimal white wall`, `soft gradient`
8. 节日主题：`festival lights`, `fireworks celebration`, `lantern festival`
9. 明星模仿秀：`concert led backdrop`, `fashion stage`, `runway lights`
10. 用户原创舞：`abstract gradient`, `soft bokeh background`, `blurred city lights`

## 4. 目录规范

```
project/
  tools/                 # RVM/Real-ESRGAN 等工具
  scripts/               # 批处理脚本
  viggle_src/            # Viggle 输出（未超分）
  superres_hd/           # 超分后视频
  alpha/                 # 抠像后人物透明视频（带 alpha）
  backgrounds_raw/<class>/   # API/自拍/AI生成原始背景
  backgrounds_loop/<class>/  # 3–10s Loop 化背景
  output/                # 合成成片
  licenses/<class>/      # 背景 license JSON 留痕
  logs/                  # 处理日志
```

## 5. Loop 化（3–10 秒无缝循环）

* 原则：**短（3–6s）轻、长（6–10s）自然**；固定机位/轻动态素材优先。
* 交叉溶解消除首尾突变（FFmpeg `xfade`）。

## 6. 清晰化超分（可选但推荐）

* **Real-ESRGAN-ncnn-vulkan**（快、低显存）：540p→1080p 约 **3–5 分钟/5 分钟片**（3060）。
* **PyTorch 版**（更清晰、稍慢）：约 **6–12 分钟/5 分钟片**。

## 7. 抠像（只替换背景，不动人物细节）

* **RVM（Robust Video Matting）**：1080p 约 **1–2 分钟/5 分钟片**（3060）。
* 输出：**带 alpha 通道的人物视频**（或 PNG 序列）。

## 8. 无限循环换背景合成（按歌曲时长自动匹配）

* 背景 loop 片段任意长度，利用 `-stream_loop -1` + `-shortest` 与歌曲/人物视频对齐。

## 9. LUT/色彩与质检（QA）

* **色彩体系**：每类绑定一套 LUT（如：流行=冷蓝、节日=暖金、太极=淡绿）。
* **亮度匹配**：`eq=contrast/brightness/saturation` 轻调，让人物不"贴片"。
* **抽检 5%**：边缘穿帮、循环突兀、闪烁、色偏、音轨缺失。
* **播放兼容**：导出 `-pix_fmt yuv420p`。

## 10. 合规模块与留痕

* 每个背景保存 `provider/asset_id/license_url/download_url/md5/时间/分类` → `licenses/`。
* 仅使用**明确商用许可**；剔除**人物/Logo/可识别文字**。
* AI 生成：记录 **Prompt + 平台条款版本**；自拍：保留原片与拍摄记录。
* 音乐：尽量免版权或自有版权；如用热门曲目，准备**下架/替换预案**。

## 11. 成本与套餐（Viggle Credits 粗算）

* 规则：**1 credit ≈ 15 秒**（Fast 模式、无水印）。
* **5 分钟视频 ≈ 20 credits**；**10 分钟 ≈ 40 credits**。

| 套餐       | 月度 Credits | 可覆盖 5 分钟片数 | 适用    |
| -------- | ---------: | ---------: | ----- |
| Pro      |         80 |      ~4 条 | 小规模验证 |
| Live     |        250 |     ~12 条 | 小批量上线 |
| Live Max |        800 |     ~40 条 | 大规模量产 |

## 12. 性能与并发（3060 12G）

* **单条 5 分钟视频**（含超分→抠像→合成）：约 **5–8 分钟**。
* **并发建议**：最多 **2 并行任务**（监控 `nvidia-smi`，单任务显存 ~5–6GB）。
* **磁盘 IO**：临时帧在 **NVMe SSD**，明显加速。

## 13. 运维与排障（Checklist）

* **分辨率统一**：Loop 化统一到 `1920x1080@30`。
* **音轨保留**：`-map 1:a?`，无则外接音轨再 `-map`。
* **显存爆**：超分倍率别太高，必要时**分段处理**。
* **循环突兀**：用 `xfade`；优先选**光效/树影/水面**等天然循环感素材。
* **合成拉伸**：用 `force_original_aspect_ratio=cover` 或事先裁切到 16:9。

## 14. 最短路径（今天就能跑的步骤）

1. **拉取背景**：用 Pexels/Pixabay 搜索上述关键词，下载每类 3–5 条（≥1080p）。
2. **Loop 化**：对每条跑 Loop化脚本（3–6s，交叉溶解）。
3. **（可选）超分**：对 Viggle 输出跑 Real-ESRGAN-ncnn-vulkan（x2）。
4. **抠像**：RVM 输出带 alpha 的人物视频。
5. **一键合成**：`-stream_loop -1` 无限循环背景，`-shortest` 自动对齐歌曲长度。
6. **抽检 & 导出**：LUT 调色、抽检 5%，上线。

---

## 技术实现

基于RTX 3060 12GB的具体实现方案：

### 核心工具链
- **Real-ESRGAN-ncnn-vulkan**: 超分辨率处理
- **RVM (Robust Video Matting)**: 视频抠像
- **FFmpeg**: 视频处理和合成
- **Viggle API**: 换脸换装

### 处理流程
1. Viggle输出 → 超分清晰化(4-5分钟)
2. 抠像处理(2分钟) → 背景合成(1分钟)
3. 总耗时: 7-8分钟/首，可并行2任务

### 成本控制
- **Viggle成本**: ¥40-50/首
- **本地处理**: ¥0.3/首(电费)
- **总成本**: ¥40.35-50.35/首
- **500首总成本**: ¥20,175-25,175
