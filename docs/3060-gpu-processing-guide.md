# 3060 GPU 广场舞视频超分 + 抠像 + 换背景最佳实践与避坑指南

## 1. 场景背景
Viggle 输出的视频虽然动作流畅，但分辨率和细节不足，并且原始背景可能存在版权风险。
目标是利用 **3060 12GB GPU** 本地批量实现：
1. 视频清晰化（超分辨率处理）
2. 抠像（保留换脸换装后的人物）
3. 背景替换（免版权或 AI 生成）
4. 合成输出

## 2. 全流程方案

### 步骤 1：超分清晰化
**目的**：提升视频分辨率，方便后续抠像边缘更干净。
**推荐工具**：Real-ESRGAN-ncnn-vulkan（低显存、速度快）。

**命令示例**：
```bash
# 分解视频为帧
ffmpeg -i input.mp4 frames/frame_%08d.png

# 超分 4x（540p → 1080p 或 4K）
realesrgan-ncnn-vulkan -i frames -o frames_up -s 2

# 合成回视频
ffmpeg -r 30 -i frames_up/frame_%08d.png -c:v libx264 -pix_fmt yuv420p hd.mp4
```

**3060 12G 耗时**：5 分钟视频约 4~5 分钟。

### 步骤 2：视频抠像

**目的**：提取换脸换装后的人物，去除原背景。
**推荐工具**：RVM（Robust Video Matting）。

**命令示例**：
```bash
python inference_rvm.py \
  --input hd.mp4 \
  --output person_alpha.mp4 \
  --model rvm_resnet50
```

输出带 **alpha 通道** 的透明背景视频。
**3060 12G 耗时**：5 分钟视频约 2 分钟。

### 步骤 3：背景替换

**目的**：换成免版权或 AI 生成背景，规避版权风险。

**背景来源**：
- 免版权视频库：Pexels / Pixabay / Videvo / Mixkit
- AI 视频生成：Pika Labs / Stable Video Diffusion
- 静态图延长：FFmpeg `loop 1` 转成长视频

**命令示例**（FFmpeg 叠加背景）：
```bash
ffmpeg -i person_alpha.mp4 -i bg.mp4 \
  -filter_complex "[1:v]scale=iw:ih[bg];[bg][0:v]overlay=0:0:format=auto" \
  -c:v libx264 -pix_fmt yuv420p output.mp4
```

**3060 12G 耗时**：5 分钟视频约 1 分钟。

### 步骤 4：一键批处理脚本（示例）

```bash
#!/bin/bash
for f in ./viggle_videos/*.mp4; do
    name=$(basename "$f" .mp4)

    # 1. 超分
    ffmpeg -i "$f" temp_frames/frame_%08d.png
    realesrgan-ncnn-vulkan -i temp_frames -o temp_frames_up -s 2
    ffmpeg -r 30 -i temp_frames_up/frame_%08d.png -c:v libx264 -pix_fmt yuv420p temp_hd.mp4

    # 2. 抠像
    python inference_rvm.py --input temp_hd.mp4 --output temp_alpha.mp4 --model rvm_resnet50

    # 3. 背景替换
    ffmpeg -i temp_alpha.mp4 -i background.mp4 \
      -filter_complex "[1:v]scale=iw:ih[bg];[bg][0:v]overlay=0:0:format=auto" \
      -c:v libx264 -pix_fmt yuv420p output/${name}_final.mp4

    # 清理临时文件
    rm -rf temp_frames temp_frames_up temp_hd.mp4 temp_alpha.mp4
done
```

运行后会自动批量处理 `./viggle_videos` 文件夹下所有视频。

## 3. 耗时预估（5 分钟视频）

| 步骤 | 工具 | 耗时 |
| --- | --- | --- |
| 超分清晰化 | Real-ESRGAN-ncnn-vulkan | 4~5 分钟 |
| 抠像 | RVM | 2 分钟 |
| 换背景+合成 | FFmpeg | 1 分钟 |
| **总计** |  | **7~8 分钟** |

## 4. 最佳实践

1. **分辨率控制**：先统一视频到 540p/720p 再超分，速度快一倍。
2. **背景匹配**：背景分辨率要和人物视频一致，避免拉伸。
3. **批量自动化**：用脚本避免人工导入导出，提升效率。
4. **显存优化**：3060 可并行处理 2 条 1080p 视频（显存占用 5~6GB/任务）。
5. **文件管理**：临时帧文件建议放到 NVMe SSD，加快读写速度。

## 5. 避坑指南

- **先超分再抠像**：低分辨率视频直接抠像容易边缘锯齿。
- **音视频同步**：合成背景时记得 `map 0:a?` 保留原音轨，否则会丢音。
- **背景版权**：不要用有水印或来源不明的视频背景。
- **FFmpeg 参数**：`pix_fmt yuv420p` 确保各平台播放兼容。
- **显存不足**：超分倍率过高（x4 以上）时可能爆显存，建议分段处理。

## 6. 推荐工具

- **Real-ESRGAN-ncnn-vulkan** → 快速超分
- **RVM** → 实时视频抠像
- **FFmpeg** → 视频拆分/合成/转码
- **Pexels / Pixabay / Mixkit** → 免费背景素材
- **Pika Labs / Stable Video Diffusion** → AI 背景生成

## 7. 环境配置

### 系统要求
- GPU: RTX 3060 12GB (推荐)
- 内存: 32GB+ (处理大视频文件)
- 存储: NVMe SSD 1TB+ (快速IO)
- CPU: 8核+ (视频编解码)

### 软件环境
```bash
# CUDA环境
CUDA 11.8 / 12.1
Python 3.9+

# 核心依赖
pip install torch torchvision opencv-python
pip install imageio moviepy

# 工具安装
# Real-ESRGAN-ncnn-vulkan (独立安装)
# RVM (git clone 安装)
```

### 目录结构
```
project/
├── tools/
│   ├── Real-ESRGAN-ncnn-vulkan/
│   └── RobustVideoMatting/
├── viggle_input/          # Viggle输出视频
├── backgrounds/           # 背景视频库
├── temp/                  # 临时处理文件
├── output/                # 最终输出
└── scripts/               # 批处理脚本
```
