# 背景视频获取和处理指南

## 🎨 背景视频的重要性

在3060 GPU Pipeline中，背景视频是最终成品质量的关键因素。好的背景视频能够：
- 提升视频的专业感
- 避免版权问题
- 增强视觉效果
- 保持风格一致性

## 📋 背景视频获取方法

### 1. 免费素材网站

#### Pexels (推荐)
- **网址**: https://www.pexels.com/videos/
- **特点**: 高质量、免费商用、无需注册
- **搜索关键词**: 
  - `dance studio background`
  - `gym background`
  - `stage background`
  - `neutral background`

#### Pixabay
- **网址**: https://pixabay.com/videos/
- **特点**: 大量免费素材、分类清晰
- **搜索关键词**:
  - `background loop`
  - `abstract background`
  - `minimal background`

#### Mixkit
- **网址**: https://mixkit.co/free-stock-video/
- **特点**: 专业背景、循环视频
- **搜索关键词**:
  - `dance background`
  - `fitness background`
  - `performance background`

### 2. AI生成背景

#### Pika Labs
- **网址**: https://pika.art/
- **特点**: AI生成、风格多样
- **提示词示例**:
  ```
  A modern dance studio with clean white walls and wooden floors, 
  soft lighting, minimalist design, 4K quality, smooth camera movement
  ```

#### Stable Video Diffusion
- **特点**: 本地运行、完全控制
- **提示词示例**:
  ```
  professional dance studio background, 
  clean and modern, soft lighting, 
  high quality, smooth motion
  ```

### 3. 手动创建背景

#### 纯色背景
```bash
# 使用FFmpeg创建纯色背景
ffmpeg -f lavfi -i "color=c=black:size=1920x1080:duration=60" \
  -c:v libx264 -pix_fmt yuv420p black_bg.mp4

ffmpeg -f lavfi -i "color=c=white:size=1920x1080:duration=60" \
  -c:v libx264 -pix_fmt yuv420p white_bg.mp4
```

#### 渐变背景
```bash
# 创建渐变背景
ffmpeg -f lavfi -i "gradient=c0=blue:c1=purple:size=1920x1080:duration=60" \
  -c:v libx264 -pix_fmt yuv420p gradient_bg.mp4
```

## 🎯 推荐的背景类型

### 1. 舞蹈室背景
- **特点**: 简洁、专业、适合舞蹈视频
- **颜色**: 白色/浅灰色墙壁，木地板
- **灯光**: 柔和均匀照明
- **用途**: 舞蹈教学、表演视频

### 2. 健身房背景
- **特点**: 现代、活力、适合健身视频
- **颜色**: 深色/金属色调
- **元素**: 健身器材、镜子
- **用途**: 健身教学、运动视频

### 3. 舞台背景
- **特点**: 正式、华丽、适合表演
- **颜色**: 深色/金色/红色
- **元素**: 舞台灯光、帷幕
- **用途**: 正式表演、比赛视频

### 4. 中性背景
- **特点**: 简洁、通用、适合各种内容
- **颜色**: 白色/灰色/黑色
- **元素**: 纯色或简单纹理
- **用途**: 通用背景、商务视频

## ⚙️ 背景视频处理

### 1. 统一格式要求
```bash
# 标准格式
分辨率: 1920x1080 (1080p)
帧率: 30fps
编码: H.264
时长: 60秒 (循环使用)
码率: 2Mbps
```

### 2. 批量处理脚本
```bash
#!/bin/bash
# 批量处理背景视频

for video in backgrounds/*.mp4; do
    filename=$(basename "$video")
    output="backgrounds/processed_$filename"
    
    ffmpeg -i "$video" \
      -vf "scale=1920:1080,fps=30" \
      -t 60 \
      -c:v libx264 -pix_fmt yuv420p \
      -b:v 2M \
      -y "$output"
    
    echo "处理完成: $filename"
done
```

### 3. 循环处理
```bash
# 创建无缝循环背景
ffmpeg -i input.mp4 \
  -vf "loop=loop=-1:size=1800" \
  -c:v libx264 -pix_fmt yuv420p \
  -y looped_bg.mp4
```

## 📁 目录结构建议

```
backgrounds/
├── dance_studio/          # 舞蹈室背景
│   ├── white_studio.mp4
│   ├── wooden_floor.mp4
│   └── modern_studio.mp4
├── gym/                   # 健身房背景
│   ├── dark_gym.mp4
│   ├── equipment_bg.mp4
│   └── mirror_wall.mp4
├── stage/                 # 舞台背景
│   ├── theater_stage.mp4
│   ├── concert_hall.mp4
│   └── red_curtain.mp4
├── neutral/               # 中性背景
│   ├── white_bg.mp4
│   ├── gray_bg.mp4
│   └── black_bg.mp4
└── gradients/             # 渐变背景
    ├── blue_purple.mp4
    ├── orange_red.mp4
    └── green_blue.mp4
```

## 🔧 自动化工具

### 1. 背景下载脚本
```python
# 自动下载背景视频
import requests
import os

def download_background(query, count=5):
    # 从Pexels API下载
    api_key = os.getenv('PEXELS_API_KEY')
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={count}"
    headers = {'Authorization': api_key}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    for video in data['videos']:
        video_url = video['video_files'][0]['link']
        filename = f"pexels_{query}_{video['id']}.mp4"
        # 下载处理...
```

### 2. 背景处理脚本
```python
# 批量处理背景视频
import subprocess
from pathlib import Path

def process_backgrounds():
    backgrounds_dir = Path("backgrounds")
    
    for video_file in backgrounds_dir.glob("*.mp4"):
        output_file = backgrounds_dir / f"processed_{video_file.name}"
        
        cmd = [
            "ffmpeg", "-i", str(video_file),
            "-vf", "scale=1920:1080,fps=30",
            "-t", "60",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "2M", "-y", str(output_file)
        ]
        
        subprocess.run(cmd)
```

## 💡 最佳实践

### 1. 选择原则
- **风格匹配**: 背景风格要与视频内容协调
- **颜色搭配**: 避免与人物服装颜色冲突
- **动态适中**: 背景不要过于复杂，影响主体
- **版权安全**: 确保使用免费商用素材

### 2. 处理技巧
- **统一格式**: 所有背景视频使用相同规格
- **循环优化**: 确保60秒循环无缝衔接
- **质量平衡**: 在文件大小和质量间找到平衡
- **备份管理**: 保留原始文件，处理后的文件单独存放

### 3. 使用建议
- **分类管理**: 按类型和用途分类存放
- **命名规范**: 使用描述性文件名
- **索引记录**: 创建背景视频索引文件
- **定期更新**: 定期添加新的背景素材

## 🚀 快速开始

### 1. 准备环境
```bash
# 创建背景目录
mkdir -p backgrounds/{dance_studio,gym,stage,neutral,gradients}

# 安装工具
pip install requests pillow
```

### 2. 下载背景
```bash
# 运行背景下载脚本
python scripts/download_backgrounds.py
```

### 3. 处理背景
```bash
# 批量处理背景视频
python scripts/process_backgrounds.py
```

### 4. 使用背景
```bash
# 在Pipeline中使用
python scripts/rtx3060_pipeline.py
```

## 📊 背景视频规格表

| 类型 | 分辨率 | 帧率 | 时长 | 码率 | 文件大小 |
|------|--------|------|------|------|----------|
| 舞蹈室 | 1920x1080 | 30fps | 60s | 2Mbps | ~15MB |
| 健身房 | 1920x1080 | 30fps | 60s | 2Mbps | ~15MB |
| 舞台 | 1920x1080 | 30fps | 60s | 2Mbps | ~15MB |
| 中性 | 1920x1080 | 30fps | 60s | 2Mbps | ~15MB |
| 渐变 | 1920x1080 | 30fps | 60s | 2Mbps | ~15MB |

通过以上方法，您可以轻松获取和处理高质量的背景视频，为3060 GPU Pipeline提供完美的背景素材！🎨
