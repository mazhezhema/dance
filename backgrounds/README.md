# 背景视频说明

## 🎨 背景视频要求

为了确保3060 GPU Pipeline的最佳效果，背景视频需要满足以下要求：

### 📋 技术规格
- **分辨率**: 1920x1080 (1080p)
- **帧率**: 30fps
- **编码**: H.264
- **时长**: 60秒 (循环使用)
- **码率**: 2Mbps
- **格式**: MP4

### 🎯 推荐背景类型

#### 1. 舞蹈室背景
- **特点**: 简洁、专业、适合舞蹈视频
- **颜色**: 白色/浅灰色墙壁，木地板
- **灯光**: 柔和均匀照明
- **用途**: 舞蹈教学、表演视频

#### 2. 健身房背景
- **特点**: 现代、活力、适合健身视频
- **颜色**: 深色/金属色调
- **元素**: 健身器材、镜子
- **用途**: 健身教学、运动视频

#### 3. 舞台背景
- **特点**: 正式、华丽、适合表演
- **颜色**: 深色/金色/红色
- **元素**: 舞台灯光、帷幕
- **用途**: 正式表演、比赛视频

#### 4. 中性背景
- **特点**: 简洁、通用、适合各种内容
- **颜色**: 白色/灰色/黑色
- **元素**: 纯色或简单纹理
- **用途**: 通用背景、商务视频

## 📥 获取背景视频的方法

### 1. 免费素材网站

#### Pexels (推荐)
- **网址**: https://www.pexels.com/videos/
- **搜索关键词**: 
  - `dance studio background`
  - `gym background`
  - `stage background`
  - `neutral background`

#### Pixabay
- **网址**: https://pixabay.com/videos/
- **搜索关键词**:
  - `background loop`
  - `abstract background`
  - `minimal background`

#### Mixkit
- **网址**: https://mixkit.co/free-stock-video/
- **搜索关键词**:
  - `dance background`
  - `fitness background`
  - `performance background`

### 2. 手动创建背景

#### 使用FFmpeg创建纯色背景
```bash
# 黑色背景
ffmpeg -f lavfi -i "color=c=black:size=1920x1080:duration=60" \
  -c:v libx264 -pix_fmt yuv420p -b:v 2M black_bg.mp4

# 白色背景
ffmpeg -f lavfi -i "color=c=white:size=1920x1080:duration=60" \
  -c:v libx264 -pix_fmt yuv420p -b:v 2M white_bg.mp4

# 渐变背景
ffmpeg -f lavfi -i "gradient=c0=blue:c1=purple:size=1920x1080:duration=60" \
  -c:v libx264 -pix_fmt yuv420p -b:v 2M gradient_bg.mp4
```

#### 使用在线工具
- **Canva**: 创建简单背景
- **Adobe Creative Cloud**: 专业背景制作
- **DaVinci Resolve**: 免费视频编辑软件

### 3. AI生成背景

#### Pika Labs
- **网址**: https://pika.art/
- **提示词示例**:
  ```
  A modern dance studio with clean white walls and wooden floors, 
  soft lighting, minimalist design, 4K quality, smooth camera movement
  ```

#### Stable Video Diffusion
- **提示词示例**:
  ```
  professional dance studio background, 
  clean and modern, soft lighting, 
  high quality, smooth motion
  ```

## 📁 文件命名规范

建议使用以下命名规范：

```
[类型]_[描述]_[分辨率].mp4

示例:
dance_studio_white_1080p.mp4
gym_dark_modern_1080p.mp4
stage_red_curtain_1080p.mp4
neutral_black_simple_1080p.mp4
```

## 🔧 处理现有视频

如果已有背景视频但格式不符合要求，可以使用以下命令处理：

```bash
# 统一格式处理
ffmpeg -i input.mp4 \
  -vf "scale=1920:1080,fps=30" \
  -t 60 \
  -c:v libx264 -pix_fmt yuv420p \
  -b:v 2M \
  -y output.mp4
```

## 💡 使用建议

1. **风格匹配**: 背景风格要与视频内容协调
2. **颜色搭配**: 避免与人物服装颜色冲突
3. **动态适中**: 背景不要过于复杂，影响主体
4. **版权安全**: 确保使用免费商用素材
5. **质量优先**: 选择高质量的背景素材
6. **循环优化**: 确保60秒循环无缝衔接

## 🚀 快速开始

1. 下载或创建背景视频
2. 确保符合技术规格要求
3. 放入 `backgrounds/` 目录
4. 在Pipeline中指定背景文件
5. 运行3060 GPU Pipeline处理

## 📊 背景视频规格表

| 类型 | 分辨率 | 帧率 | 时长 | 码率 | 文件大小 |
|------|--------|------|------|------|----------|
| 舞蹈室 | 1920x1080 | 30fps | 60s | 2Mbps | ~15MB |
| 健身房 | 1920x1080 | 30fps | 60s | 2Mbps | ~15MB |
| 舞台 | 1920x1080 | 30fps | 60s | 2Mbps | ~15MB |
| 中性 | 1920x1080 | 30fps | 60s | 2Mbps | ~15MB |

---

**注意**: 请确保所有背景视频都符合版权要求，建议使用免费商用素材或自己创建的内容。
