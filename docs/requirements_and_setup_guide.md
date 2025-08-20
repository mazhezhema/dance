# 🎯 Dance项目完整需求和环境搭建指南

## 📋 **项目输入素材需求**

### **1. 视频素材** 🎬
```
📁 输入视频目录: tasks_in/
├── 原始视频文件 (*.mp4, *.avi, *.mov, *.mkv)
├── 分辨率要求: 最低 480x360，最高 1920x1080
├── 时长要求: 5秒 - 5分钟
├── 帧率要求: 15-60fps
├── 文件大小: 最大 100MB
└── 编码格式: H.264, H.265, VP9
```

### **2. 人物图片素材** 👤
```
📁 人物图片目录: input/people/
├── 高质量人物照片 (*.jpg, *.png)
├── 分辨率: 建议 512x512 或更高
├── 背景: 简单背景，人物清晰
├── 角度: 正面、侧面、多角度
├── 表情: 自然表情，适合舞蹈
└── 数量: 建议 10-50 张不同人物
```

### **3. 背景素材** 🎨
```
📁 背景素材目录: backgrounds/
├── 舞蹈背景: dance_*.jpg/png
│   ├── 舞蹈教室
│   ├── 舞台背景
│   ├── 现代舞蹈空间
│   └── 专业舞蹈工作室
├── 健身背景: gym_*.jpg/png
│   ├── 健身房
│   ├── 瑜伽室
│   ├── 户外健身场地
│   └── 家庭健身空间
├── 传统背景: traditional_*.jpg/png
│   ├── 古典舞台
│   ├── 传统文化场景
│   └── 传统建筑背景
└── 通用背景: neutral_*.jpg/png
    ├── 纯色背景
    ├── 渐变背景
    └── 抽象背景
```

### **4. 音乐素材** 🎵
```
📁 音乐素材目录: input/music/
├── 舞蹈音乐 (*.mp3, *.wav)
├── 健身音乐
├── 传统音乐
├── 背景音乐
└── 音效文件
```

## 🛠️ **环境搭建要求**

### **1. 硬件要求** 💻

#### **最低配置**
```
CPU: Intel i5-8400 / AMD Ryzen 5 2600
内存: 16GB RAM
存储: 500GB SSD (推荐 NVMe)
显卡: GTX 1060 6GB / RX 580 8GB
网络: 稳定的互联网连接
```

#### **推荐配置**
```
CPU: Intel i7-10700K / AMD Ryzen 7 3700X
内存: 32GB RAM
存储: 1TB NVMe SSD
显卡: RTX 3060 12GB / RTX 3070 8GB
网络: 高速光纤网络
```

#### **生产环境配置**
```
CPU: Intel i9-10900K / AMD Ryzen 9 5900X
内存: 64GB RAM
存储: 2TB NVMe SSD + 4TB HDD
显卡: RTX 3080 10GB / RTX 3090 24GB
网络: 千兆光纤网络
```

### **2. 软件环境** 🔧

#### **操作系统**
```
✅ Windows 10/11 (推荐)
✅ Ubuntu 20.04+ / CentOS 8+
✅ macOS 10.15+ (部分功能受限)
```

#### **Python环境**
```
Python版本: 3.8 - 3.11
包管理器: pip 21.0+
虚拟环境: venv 或 conda
```

#### **必需软件**
```
1. FFmpeg 4.0+ (视频处理核心)
2. Chrome/Chromium 90+ (浏览器自动化)
3. Git (版本控制)
4. 7-Zip/WinRAR (文件压缩)
```

### **3. 开发工具** 🛠️

#### **IDE/编辑器**
```
推荐: VS Code, PyCharm, Sublime Text
插件: Python, Git, Markdown, JSON
```

#### **版本控制**
```
Git: 2.30+
GitHub/GitLab: 远程仓库
```

## 📦 **依赖安装指南**

### **1. Python依赖安装**
```bash
# 创建虚拟环境
python -m venv dance_env
source dance_env/bin/activate  # Linux/macOS
dance_env\Scripts\activate     # Windows

# 安装核心依赖
pip install -r scripts/requirements.txt

# 安装Playwright依赖
pip install -r scripts/requirements_playwright.txt

# 安装Playwright浏览器
playwright install chromium
```

### **2. 外部工具安装**

#### **FFmpeg安装**
```bash
# Windows
# 下载: https://ffmpeg.org/download.html
# 添加到系统PATH

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install epel-release
sudo yum install ffmpeg

# macOS
brew install ffmpeg
```

#### **Chrome/Chromium安装**
```bash
# Windows: 下载Chrome安装包
# Linux: sudo apt install chromium-browser
# macOS: brew install chromium
```

### **3. GPU工具安装 (可选)**

#### **Real-ESRGAN**
```bash
# 下载预编译版本
wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth

# 或从源码编译
git clone https://github.com/xinntao/Real-ESRGAN.git
cd Real-ESRGAN
pip install -r requirements.txt
```

#### **RVM (Robust Video Matting)**
```bash
# 安装PyTorch
pip install torch torchvision

# 安装RVM
pip install rvm-pytorch
```

## ⚙️ **配置设置**

### **1. 目录结构创建**
```bash
# 创建必要目录
mkdir -p tasks_in
mkdir -p downloads
mkdir -p final_output
mkdir -p backgrounds
mkdir -p input/people
mkdir -p input/music
mkdir -p temp_backgrounds
mkdir -p temp_gpu
mkdir -p logs
mkdir -p config
mkdir -p secrets
```

### **2. 配置文件设置**

#### **主配置文件 (config.json)**
```json
{
  "viggle": {
    "base_url": "https://viggle.ai",
    "max_retries": 3,
    "timeout": 300
  },
  "gpu": {
    "enabled": true,
    "max_memory": "10GB",
    "concurrent_jobs": 2
  },
  "backgrounds": {
    "default_category": "dance",
    "effects": ["zoom", "pan"]
  },
  "output": {
    "format": "mp4",
    "quality": "high",
    "preserve_audio": true
  }
}
```

#### **账号配置文件 (config/accounts.json)**
```json
{
  "accounts": [
    {
      "username": "your_email@example.com",
      "password": "your_password",
      "status": "active"
    }
  ]
}
```

### **3. 环境变量设置**
```bash
# .env 文件
VIGGLE_USERNAME=your_email@example.com
VIGGLE_PASSWORD=your_password
FFMPEG_PATH=/usr/bin/ffmpeg
GPU_ENABLED=true
LOG_LEVEL=INFO
```

## 🎯 **素材准备清单**

### **1. 视频素材准备**
- [ ] 收集原始舞蹈视频 (10-50个)
- [ ] 检查视频质量和格式
- [ ] 按类别分类存储
- [ ] 重命名为规范格式

### **2. 人物图片准备**
- [ ] 收集高质量人物照片
- [ ] 裁剪为正方形格式
- [ ] 调整分辨率为512x512+
- [ ] 按人物分类存储

### **3. 背景素材准备**
- [ ] 收集各类背景图片
- [ ] 按场景分类命名
- [ ] 调整分辨率为1920x1080
- [ ] 优化图片质量

### **4. 音乐素材准备**
- [ ] 收集舞蹈音乐
- [ ] 检查音频质量
- [ ] 按类型分类
- [ ] 准备音效文件

## 🚀 **快速启动检查清单**

### **环境检查**
- [ ] Python 3.8+ 已安装
- [ ] FFmpeg 已安装并添加到PATH
- [ ] Chrome/Chromium 已安装
- [ ] Git 已安装

### **依赖检查**
- [ ] Python依赖已安装
- [ ] Playwright浏览器已安装
- [ ] GPU工具已安装 (可选)

### **配置检查**
- [ ] 配置文件已创建
- [ ] 账号信息已配置
- [ ] 目录结构已创建
- [ ] 环境变量已设置

### **素材检查**
- [ ] 输入视频已准备
- [ ] 人物图片已准备
- [ ] 背景素材已准备
- [ ] 音乐素材已准备

### **功能测试**
- [ ] 系统状态检查通过
- [ ] 背景替换功能测试通过
- [ ] Viggle自动化测试通过
- [ ] GPU处理测试通过

## 💡 **优化建议**

### **性能优化**
1. **存储优化**: 使用NVMe SSD提升I/O性能
2. **内存优化**: 增加RAM减少磁盘交换
3. **GPU优化**: 使用RTX 3060+提升处理速度
4. **网络优化**: 使用高速网络提升下载速度

### **质量优化**
1. **视频质量**: 使用高质量原始视频
2. **图片质量**: 使用高分辨率人物图片
3. **背景质量**: 使用专业背景素材
4. **音频质量**: 使用高质量音乐素材

### **效率优化**
1. **批量处理**: 一次性处理多个文件
2. **并行处理**: 利用多核CPU和GPU
3. **缓存机制**: 缓存重复处理结果
4. **自动化**: 减少人工干预

这个指南涵盖了项目运行所需的所有要素，按照这个清单准备，您就可以开始使用Dance项目了！🎉
