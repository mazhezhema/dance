# 🚀 Dance项目快速开始指南

## 📋 当前状态
✅ **系统已准备就绪！** 所有核心组件都已配置完成。

## 📁 目录结构
```
dance/
├── tasks_in/              # 🎬 输入视频目录
│   ├── test_video.mp4     # 测试视频文件
│   └── README.md          # 使用说明
├── input/people/          # 👤 人物图片目录
│   └── 示例人物.txt       # 人物要求说明
├── downloads/             # 📤 输出视频目录
├── logs/                  # 📝 日志文件目录
├── secrets/               # 🔐 会话状态目录
├── config/                # ⚙️ 配置文件目录
└── scripts/               # 🛠️ 脚本文件目录
```

## 🎯 下一步操作

### 1. 添加真实视频文件
将您的视频文件放入 `tasks_in/` 目录：
```bash
# 复制视频文件到输入目录
cp your_video.mp4 tasks_in/
```

**视频要求**:
- 格式: MP4, AVI, MOV, MKV
- 大小: < 100MB
- 时长: 10秒 - 5分钟
- 分辨率: 720p或以上

### 2. 添加人物图片
将AI生成的人物图片放入 `input/people/` 目录：
```bash
# 复制人物图片到人物目录
cp your_person.jpg input/people/
```

**图片要求**:
- 格式: JPG, PNG
- 分辨率: 512x512或更高
- 内容: 清晰、正面、单人肖像

**推荐图片**:
- `主要舞者.jpg` - 默认主角
- `广场舞大妈.jpg` - 广场舞专用
- `健身教练.jpg` - 健身操专用
- `太极师傅.jpg` - 太极拳专用
- `瑜伽老师.jpg` - 瑜伽专用

### 3. 配置Viggle账号
运行登录脚本配置账号：
```bash
python scripts/login_once.py
```

### 4. 运行自动化处理
启动Viggle自动化处理：
```bash
python scripts/viggle_playwright_optimized.py
```

## 📊 系统监控

### 查看处理状态
```bash
# 查看日志
tail -f logs/viggle_optimized.log

# 查看输出文件
ls downloads/
```

### 查看系统状态
```bash
# 运行系统测试
python test_system.py
```

## 🔧 故障排除

### 常见问题
1. **模块导入失败**: 确保已安装所有依赖
2. **浏览器启动失败**: 运行 `playwright install`
3. **登录失败**: 检查账号配置和网络连接
4. **处理超时**: 检查视频文件大小和网络稳定性

### 获取帮助
- 查看详细文档: `docs/playwright-automation-io.md`
- 检查日志文件: `logs/viggle_optimized.log`
- 运行测试脚本: `python test_system.py`

## 🎉 开始使用

现在您可以开始使用Dance项目了！

1. **准备文件**: 添加视频和人物图片
2. **配置账号**: 设置Viggle登录
3. **启动处理**: 运行自动化脚本
4. **监控进度**: 查看日志和输出

**祝您使用愉快！** 🎭
