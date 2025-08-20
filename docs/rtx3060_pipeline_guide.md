# RTX 3060 GPU Pipeline 使用指南

## 🎮 概述

RTX 3060 GPU Pipeline是专门为3060 12GB显存优化的视频处理流程，包含超分辨率、抠像、背景替换三个核心步骤。

## 📋 完整流程

### 1. 输入阶段
```
Viggle输出视频 → downloads/目录 → GPU Pipeline处理
```

### 2. 处理阶段
```
超分辨率处理 → 视频抠像 → 背景替换 → 最终输出
     ↓            ↓          ↓         ↓
   540p→1080p   提取人物   替换背景   高清成品
```

### 3. 输出阶段
```
final_output/目录 → 高质量视频文件
```

## ⚙️ 系统要求

### 硬件配置
- **GPU**: RTX 3060 12GB (必需)
- **内存**: 32GB+ (推荐)
- **存储**: NVMe SSD 1TB+ (快速IO)
- **CPU**: 8核+ (视频编解码)

### 软件环境
```bash
# 核心工具
- FFmpeg (视频处理)
- Real-ESRGAN-ncnn-vulkan (超分)
- RVM (视频抠像)
- Python 3.9+

# Python依赖
pip install torch torchvision opencv-python
pip install GPUtil psutil
```

## 🚀 快速开始

### 1. 准备环境
```bash
# 创建工具目录
mkdir -p tools
mkdir -p backgrounds
mkdir -p final_output
mkdir -p temp_gpu

# 下载工具
# Real-ESRGAN-ncnn-vulkan
# RVM (Robust Video Matting)
```

### 2. 配置背景素材
```bash
# 将背景视频放入backgrounds目录
backgrounds/
├── dance_studio.mp4      # 舞蹈室背景
├── gym_background.mp4    # 健身房背景
├── traditional_stage.mp4 # 传统舞台背景
└── neutral_background.mp4 # 中性背景
```

### 3. 运行Pipeline
```bash
# 运行3060专用Pipeline
python scripts/rtx3060_pipeline.py
```

## 📊 性能指标

### 处理速度 (基于3060 12GB)
| 视频时长 | 超分处理 | 抠像处理 | 背景合成 | 总耗时 |
|---------|---------|---------|---------|--------|
| 1分钟   | 1分钟   | 0.5分钟 | 0.2分钟 | 1.7分钟 |
| 3分钟   | 2.5分钟 | 1分钟   | 0.5分钟 | 4分钟   |
| 5分钟   | 4分钟   | 2分钟   | 1分钟   | 7分钟   |
| 10分钟  | 8分钟   | 4分钟   | 2分钟   | 14分钟  |

### 显存使用
- **超分阶段**: 4-6GB
- **抠像阶段**: 2-4GB
- **合成阶段**: 1-2GB
- **并行处理**: 最多2个任务同时运行

## 🔧 配置参数

### GPU配置
```python
gpu_memory_limit: int = 10  # GB，预留2GB给系统
max_concurrent_jobs: int = 2  # 并行任务数
```

### 处理参数
```python
superres_scale: int = 2      # 超分倍率 (2x)
superres_model: str = "realesr-animevideov3"  # 超分模型
target_resolution: tuple = (1920, 1080)  # 目标分辨率
target_fps: int = 30         # 目标帧率
```

### 质量设置
```python
video_codec: str = "libx264"  # 视频编码
video_bitrate: str = "2M"     # 视频码率
audio_codec: str = "aac"      # 音频编码
```

## 📁 目录结构

```
project/
├── downloads/              # Viggle输出视频 (输入)
├── final_output/           # 最终输出视频
├── backgrounds/            # 背景视频库
├── temp_gpu/              # 临时处理文件
│   ├── frames/            # 分解的帧
│   └── frames_up/         # 超分后的帧
├── tools/                 # 处理工具
│   ├── realesrgan-ncnn-vulkan.exe
│   └── inference_rvm.py
├── logs/                  # 处理日志
└── scripts/
    └── rtx3060_pipeline.py  # 主处理脚本
```

## 🎯 处理步骤详解

### 步骤1: 超分辨率处理
```bash
# 1. 分解视频为帧
ffmpeg -i input.mp4 -vf "fps=30" frames/frame_%08d.png

# 2. Real-ESRGAN超分
realesrgan-ncnn-vulkan -i frames -o frames_up -s 2 -n realesr-animevideov3

# 3. 重新合成视频
ffmpeg -r 30 -i frames_up/frame_%08d.png -c:v libx264 -pix_fmt yuv420p hd.mp4
```

**目的**: 提升视频分辨率，为抠像提供更好的边缘质量

### 步骤2: 视频抠像
```bash
python inference_rvm.py \
  --input hd.mp4 \
  --output person_alpha.mp4 \
  --model rvm_resnet50 \
  --device cuda
```

**目的**: 提取人物，去除原背景，生成带alpha通道的视频

### 步骤3: 背景替换
```bash
ffmpeg -i person_alpha.mp4 -i background.mp4 \
  -filter_complex "[1:v]scale=1920:1080[bg];[bg][0:v]overlay=0:0:format=auto" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac final_output.mp4
```

**目的**: 将人物合成到新背景上，生成最终成品

## ⚡ 优化技巧

### 1. 显存优化
- 控制并行任务数量不超过2个
- 使用较小的超分批处理大小
- 及时清理临时文件

### 2. 速度优化
- 使用NVMe SSD存储临时文件
- 预先统一视频分辨率到540p/720p
- 启用GPU硬件加速

### 3. 质量优化
- 选择合适的超分模型
- 使用高质量背景素材
- 保持音视频同步

## 🐛 常见问题

### 1. 显存不足
```
错误: CUDA out of memory
解决: 减少并行任务数或降低超分倍率
```

### 2. 工具路径错误
```
错误: 找不到real-esrgan-ncnn-vulkan
解决: 检查tools目录下的工具文件
```

### 3. 背景文件缺失
```
警告: 背景文件不存在
解决: 添加背景视频到backgrounds目录
```

## 📈 监控和日志

### 日志文件
- `logs/rtx3060_pipeline.log` - 详细处理日志
- 包含每个步骤的执行状态和错误信息

### 进度监控
```bash
# 查看处理进度
tail -f logs/rtx3060_pipeline.log

# 查看GPU使用情况
nvidia-smi
```

## 🎉 输出结果

### 文件命名
```
输入: video_name.mp4
输出: video_name_final.mp4
```

### 质量提升
- **分辨率**: 540p → 1080p (2x提升)
- **清晰度**: 显著改善细节和边缘
- **背景**: 替换为免版权素材
- **兼容性**: 标准编码格式，各平台播放

## 🔄 批量处理

Pipeline支持批量处理，自动处理`downloads/`目录下的所有MP4文件：

```bash
# 批量处理所有视频
python scripts/rtx3060_pipeline.py

# 处理完成后查看结果
ls final_output/
```

## 💡 最佳实践

1. **预处理**: 确保输入视频质量良好
2. **背景选择**: 使用与视频风格匹配的背景
3. **定期清理**: 清理临时文件释放空间
4. **备份重要**: 备份原始文件和最终成品
5. **监控资源**: 定期检查GPU温度和显存使用
