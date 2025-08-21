# 📥📤 Dance项目输入输出指南

## 🎯 **项目概述**

Dance项目是一个AI视频处理自动化系统，主要功能包括：
- **Viggle自动化处理**: 使用AI换脸技术处理视频
- **背景替换**: 动态背景生成和替换
- **GPU加速处理**: RTX3060 GPU Pipeline优化
- **批量处理**: 多任务并行处理

## 📥 **输入结构**

### **1. 视频输入** 🎬
```
📁 tasks_in/                    # 主要输入目录
├── video1.mp4                  # 原始舞蹈视频
├── dance_tutorial.mp4          # 舞蹈教程视频
├── performance.mp4             # 表演视频
└── *.mp4                       # 支持格式: MP4, AVI, MOV, MKV
```

**视频要求**:
- **格式**: MP4, AVI, MOV, MKV
- **分辨率**: 最低 480x360，最高 1920x1080
- **时长**: 5秒 - 5分钟
- **帧率**: 15-60fps
- **文件大小**: 最大 100MB
- **编码**: H.264, H.265, VP9

### **2. 人物图片输入** 👤
```
📁 input/people/               # 人物图片目录
├── person1.jpg                # 高质量人物照片
├── person2.png                # 支持格式: JPG, PNG
├── dancer_001.jpg             # 建议命名: 人物名_编号.格式
└── *.jpg, *.png               # 分辨率建议: 512x512+
```

**图片要求**:
- **格式**: JPG, PNG
- **分辨率**: 建议 512x512 或更高
- **背景**: 简单背景，人物清晰
- **角度**: 正面、侧面、多角度
- **表情**: 自然表情，适合舞蹈
- **数量**: 建议 10-50 张不同人物

### **3. 背景素材输入** 🎨
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

**背景要求**:
- **格式**: JPG, PNG, BMP, WebP
- **分辨率**: 建议 1920x1080
- **分类**: 按场景分类命名
- **质量**: 高质量，无版权问题

### **4. 音乐素材输入** 🎵
```
📁 input/music/               # 音乐素材目录
├── dance_music_001.mp3       # 舞蹈音乐
├── fitness_background.wav    # 健身背景音乐
├── traditional_music.mp3     # 传统音乐
└── *.mp3, *.wav              # 支持格式: MP3, WAV
```

**音乐要求**:
- **格式**: MP3, WAV
- **质量**: 高质量音频
- **时长**: 与视频匹配
- **版权**: 无版权问题

## 📤 **输出结构**

### **1. Viggle处理输出** 🎭
```
📁 downloads/                  # Viggle处理输出
├── video1_viggle_1234567890.mp4    # 格式: 原文件名_viggle_时间戳.mp4
├── dance_tutorial_viggle_1234567891.mp4
├── performance_viggle_1234567892.mp4
└── *.mp4                      # 保留原音轨的换脸视频
```

**输出特点**:
- **格式**: MP4
- **音轨**: 保留原始音频
- **质量**: 与原视频相同
- **命名**: 自动生成时间戳

### **2. 背景替换输出** 🎨
```
📁 final_output/               # 最终成品输出
├── video1_final_dance_001.mp4     # 格式: 原文件名_final_背景类型_编号.mp4
├── dance_tutorial_final_gym_001.mp4
├── performance_final_traditional_001.mp4
└── *.mp4                      # 带新背景的最终视频
```

**输出特点**:
- **格式**: MP4
- **背景**: 动态背景替换
- **音轨**: 保留原始音频
- **质量**: 高质量输出

### **3. 临时文件输出** 🔧
```
📁 temp_backgrounds/           # 临时背景视频
├── dance_studio_white_45.2s.mp4    # 格式: 背景名_时长.mp4
├── gym_dark_modern_30.5s.mp4
└── *.mp4                      # 图片转视频的临时文件

📁 temp_gpu/                   # GPU处理临时文件
├── video1_super_res.mp4       # 超分辨率处理
├── video1_matted.mp4          # 抠像处理
└── *.mp4                      # 各种处理步骤的临时文件
```

### **4. 日志和报告输出** 📊
```
📁 logs/                       # 日志文件
├── viggle_enhanced.log        # Viggle处理日志
├── rtx3060_pipeline.log       # GPU处理日志
├── task_monitor.log           # 任务监控日志
└── *.log                      # 各种处理日志

📁 preprocessing_reports/      # 预处理报告
├── video1_analysis.json       # 视频分析报告
├── quality_assessment.json    # 质量评估报告
└── *.json                     # JSON格式报告

📁 tasks/                      # 任务数据
├── task_status.db             # SQLite任务数据库
├── test_stats.json            # 测试统计
└── *.db, *.json               # 任务状态和统计
```

## 🔄 **处理流程**

### **完整Pipeline流程**
```
输入视频 (tasks_in/) 
    ↓
Viggle处理 (AI换脸)
    ↓
Viggle输出 (downloads/)
    ↓
背景替换处理
    ↓
最终输出 (final_output/)
```

### **详细步骤**
1. **输入扫描**: 扫描 `tasks_in/` 目录
2. **任务创建**: 在数据库中创建任务记录
3. **Viggle处理**: 上传到Viggle进行AI换脸
4. **下载结果**: 保存到 `downloads/` 目录
5. **背景替换**: 选择背景进行替换
6. **最终合成**: 输出到 `final_output/` 目录

## 📋 **使用示例**

### **基本使用**
```bash
# 1. 准备输入文件
cp your_video.mp4 tasks_in/
cp person_photo.jpg input/people/
cp background.jpg backgrounds/dance/

# 2. 运行完整Pipeline
python main.py full

# 3. 查看输出结果
ls downloads/      # Viggle处理结果
ls final_output/   # 最终成品
```

### **分步处理**
```bash
# 1. 只运行Viggle处理
python main.py viggle

# 2. 只运行背景替换
python main.py background --background dance

# 3. 只运行GPU处理
python main.py gpu
```

### **批量处理**
```bash
# 批量处理所有输入视频
python main.py full --test-mode

# 指定背景类型和特效
python main.py background --background gym --effects zoom pan
```

## ⚙️ **配置说明**

### **输入配置**
```json
{
  "input": {
    "video_formats": ["mp4", "avi", "mov", "mkv"],
    "max_file_size_mb": 100,
    "min_resolution": "480x360",
    "max_resolution": "1920x1080"
  }
}
```

### **输出配置**
```json
{
  "output": {
    "format": "mp4",
    "quality": "high",
    "preserve_audio": true,
    "naming_pattern": "{original_name}_final_{background_type}_{index}.mp4"
  }
}
```

## 💡 **最佳实践**

### **输入准备**
1. **视频质量**: 使用高质量原始视频
2. **人物图片**: 选择清晰、正面的人物照片
3. **背景素材**: 按场景分类，使用专业背景
4. **文件命名**: 使用有意义的文件名

### **输出管理**
1. **定期清理**: 清理临时文件
2. **备份重要**: 备份最终成品
3. **版本控制**: 保留不同版本的处理结果
4. **质量检查**: 检查输出质量

### **性能优化**
1. **批量处理**: 一次性处理多个文件
2. **并行处理**: 利用多核CPU和GPU
3. **存储优化**: 使用SSD提升I/O性能
4. **网络优化**: 使用高速网络

这个输入输出结构确保了项目的可扩展性和易用性，支持从单个文件到批量处理的多种使用场景！🎉
