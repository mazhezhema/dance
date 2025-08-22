# 📥 Dance项目输入准备指南

## 🎯 **输入概述**

Dance项目需要三类主要输入：
1. **原始视频** - 需要AI换脸处理的舞蹈视频
2. **人物图片** - 用于AI换脸的人物照片
3. **背景素材** - 用于背景替换的图片素材

## 📹 **1. 原始视频准备**

### **存放位置**
```
📁 tasks_in/                    # 主要输入目录
├── dance_video_001.mp4         # 舞蹈视频1
├── dance_video_002.mp4         # 舞蹈视频2
├── tutorial_video_001.mp4      # 教程视频
└── performance_video_001.mp4   # 表演视频
```

### **视频要求**
| 参数 | 要求 | 说明 |
|------|------|------|
| **格式** | MP4, AVI, MOV, MKV | 推荐MP4格式 |
| **分辨率** | 480x360 - 1920x1080 | 推荐1080p |
| **时长** | 5秒 - 5分钟 | 建议1-3分钟 |
| **帧率** | 15-60fps | 推荐30fps |
| **文件大小** | 最大100MB | 建议50MB以内 |
| **编码** | H.264, H.265 | 推荐H.264 |

### **视频内容建议**
- ✅ **舞蹈动作清晰**: 人物动作要清楚可见
- ✅ **光线充足**: 避免过暗或过曝
- ✅ **背景简单**: 避免复杂背景干扰
- ✅ **人物居中**: 主要人物在画面中央
- ✅ **音质良好**: 音频清晰无杂音

### **视频命名规范**
```
格式: 类型_内容_编号.mp4
示例:
- dance_modern_001.mp4
- tutorial_basic_001.mp4
- performance_stage_001.mp4
- fitness_aerobics_001.mp4
```

## 👤 **2. 人物图片准备**

### **存放位置**
```
📁 input/people/               # 人物图片目录
├── dancer_001.jpg             # 舞者1
├── dancer_002.png             # 舞者2
├── instructor_001.jpg         # 教练1
├── performer_001.jpg          # 表演者1
└── *.jpg, *.png               # 支持JPG和PNG格式
```

### **图片要求**
| 参数 | 要求 | 说明 |
|------|------|------|
| **格式** | JPG, PNG | 推荐JPG格式 |
| **分辨率** | 512x512+ | 推荐1024x1024 |
| **背景** | 简单背景 | 避免复杂背景 |
| **角度** | 多角度 | 正面、侧面、45度角 |
| **表情** | 自然表情 | 适合舞蹈的表情 |
| **光线** | 充足均匀 | 避免阴影过重 |

### **图片内容建议**
- ✅ **人物清晰**: 面部特征清楚
- ✅ **表情自然**: 适合舞蹈的积极表情
- ✅ **角度多样**: 提供多个角度的照片
- ✅ **光线均匀**: 避免强烈的阴影
- ✅ **背景简单**: 纯色或简单背景

### **图片命名规范**
```
格式: 角色_编号.格式
示例:
- dancer_001.jpg
- instructor_001.jpg
- performer_001.jpg
- student_001.jpg
```

## 🎨 **3. 背景素材准备**

### **存放位置**
```
📁 backgrounds/                # 背景素材目录
├── 📁 dance/                  # 舞蹈背景
│   ├── dance_studio_white.jpg
│   ├── stage_red_curtain.jpg
│   └── modern_dance_space.png
├── 📁 gym/                    # 健身背景
│   ├── gym_dark_modern.jpg
│   ├── yoga_room_zen.jpg
│   └── outdoor_fitness.jpg
├── 📁 traditional/            # 传统背景
│   ├── classical_stage.jpg
│   └── traditional_building.jpg
└── 📁 neutral/                # 通用背景
    ├── neutral_gray_simple.jpg
    └── gradient_blue_purple.jpg
```

### **背景要求**
| 参数 | 要求 | 说明 |
|------|------|------|
| **格式** | JPG, PNG, BMP, WebP | 推荐JPG格式 |
| **分辨率** | 1920x1080+ | 推荐4K分辨率 |
| **分类** | 按场景分类 | 舞蹈、健身、传统等 |
| **质量** | 高质量 | 无版权问题 |
| **风格** | 多样化 | 不同风格和色调 |

### **背景类型建议**

#### **舞蹈背景**
- 舞蹈工作室（白色/黑色）
- 舞台背景（红色幕布）
- 现代舞蹈空间
- 练功房

#### **健身背景**
- 现代健身房
- 瑜伽室
- 户外健身场地
- 运动场馆

#### **传统背景**
- 古典舞台
- 传统建筑
- 文化场所
- 历史建筑

#### **通用背景**
- 纯色背景
- 渐变背景
- 抽象背景
- 自然风景

### **背景命名规范**
```
格式: 类型_描述.格式
示例:
- dance_studio_white.jpg
- gym_modern_dark.jpg
- traditional_stage_classical.jpg
- neutral_gradient_blue.jpg
```

## 🎵 **4. 音乐素材准备（可选）**

### **存放位置**
```
📁 input/music/               # 音乐素材目录
├── dance_music_001.mp3       # 舞蹈音乐
├── fitness_background.wav    # 健身背景音乐
├── traditional_music.mp3     # 传统音乐
└── *.mp3, *.wav              # 支持MP3和WAV格式
```

### **音乐要求**
| 参数 | 要求 | 说明 |
|------|------|------|
| **格式** | MP3, WAV | 推荐MP3格式 |
| **质量** | 高质量 | 320kbps+ |
| **时长** | 与视频匹配 | 建议稍长于视频 |
| **版权** | 无版权问题 | 使用免费音乐 |

## 📋 **5. 输入准备检查清单**

### **视频检查**
- [ ] 视频格式为MP4/AVI/MOV/MKV
- [ ] 分辨率在480x360-1920x1080之间
- [ ] 时长在5秒-5分钟之间
- [ ] 文件大小小于100MB
- [ ] 人物动作清晰可见
- [ ] 光线充足均匀
- [ ] 背景相对简单

### **人物图片检查**
- [ ] 图片格式为JPG/PNG
- [ ] 分辨率至少512x512
- [ ] 人物面部清晰
- [ ] 表情自然适合舞蹈
- [ ] 背景简单
- [ ] 光线均匀
- [ ] 提供多个角度

### **背景素材检查**
- [ ] 图片格式为JPG/PNG/BMP/WebP
- [ ] 分辨率至少1920x1080
- [ ] 按场景分类存放
- [ ] 质量高无版权问题
- [ ] 风格多样化
- [ ] 命名规范

### **目录结构检查**
- [ ] `tasks_in/` 目录存在
- [ ] `input/people/` 目录存在
- [ ] `backgrounds/` 目录存在
- [ ] `input/music/` 目录存在（可选）
- [ ] 文件命名规范
- [ ] 文件格式正确

## 🚀 **6. 快速开始**

### **步骤1: 创建目录结构**
```bash
# 确保目录存在
mkdir -p tasks_in
mkdir -p input/people
mkdir -p backgrounds/dance
mkdir -p backgrounds/gym
mkdir -p backgrounds/traditional
mkdir -p backgrounds/neutral
mkdir -p input/music
```

### **步骤2: 准备输入文件**
```bash
# 复制视频文件
cp your_dance_videos/*.mp4 tasks_in/

# 复制人物图片
cp person_photos/*.jpg input/people/

# 复制背景素材
cp background_images/*.jpg backgrounds/dance/
```

### **步骤3: 验证输入**
```bash
# 检查环境
python tools/check_environment.py

# 查看项目状态
python main.py status
```

### **步骤4: 开始处理**
```bash
# 运行完整Pipeline
python main.py full

# 或分步处理
python main.py viggle
python main.py background --background dance
```

## 💡 **7. 最佳实践**

### **视频准备**
- 使用高质量录制设备
- 确保光线充足均匀
- 选择简单背景
- 保持人物在画面中央
- 录制多个角度

### **人物图片**
- 拍摄多个角度和表情
- 使用自然光线
- 选择简单背景
- 确保面部清晰
- 表情适合舞蹈

### **背景素材**
- 收集多样化背景
- 确保高质量图片
- 按场景分类整理
- 注意版权问题
- 保持命名规范

## ⚠️ **8. 常见问题**

### **Q: 视频太大怎么办？**
A: 使用FFmpeg压缩视频：
```bash
ffmpeg -i input.mp4 -vf scale=1280:720 -c:v libx264 -crf 23 output.mp4
```

### **Q: 人物图片背景复杂怎么办？**
A: 使用在线工具或Photoshop去除背景，或重新拍摄简单背景的照片。

### **Q: 没有合适的背景素材怎么办？**
A: 可以从以下网站获取免费背景：
- Unsplash
- Pexels
- Pixabay
- 或使用纯色背景

### **Q: 视频质量不好怎么办？**
A: 重新录制或使用视频增强工具提升质量。

## 🎯 **总结**

准备输入是Dance项目成功的关键步骤。确保：
- ✅ 视频质量良好，符合要求
- ✅ 人物图片清晰，角度多样
- ✅ 背景素材丰富，分类清晰
- ✅ 目录结构正确，命名规范

按照本指南准备输入，您就可以开始使用Dance项目进行AI视频处理了！🚀
