# Dance项目 - 模块化AI视频处理系统

## 🎯 系统架构

Dance项目采用模块化设计，将视频处理流程分为三个独立且可协调的模块：

```
原始视频 → [预处理模块] → [Viggle自动化] → [本地GPU处理] → 最终视频
```

## 📦 模块详解

### 1. 📋 片源预处理模块 (`video_preprocessor.py`)

**功能**：检测和筛选适合Viggle处理的视频

**核心能力**：
- ✅ 视频质量检测（分辨率、帧率、时长、文件大小）
- ✅ Viggle兼容性评估（打分0-100）
- ✅ 智能分类（舞蹈、健身、传统等）
- ✅ 优先级排序（1-10级）
- ✅ 积分消耗预估
- ✅ 处理队列生成

**避坑要点**：
- 自动过滤过大、过长、格式不兼容的视频
- 基于关键词的智能分类
- 生成详细的兼容性报告

### 2. 🎭 Viggle自动化模块 (`viggle_automation.py`)

**功能**：基于Playwright的全自动Viggle处理

**核心能力**：
- ✅ 读取预处理队列
- ✅ 多账号智能调度
- ✅ 积分限额管理
- ✅ 批量上传处理
- ✅ 自动下载结果
- ✅ 错误重试机制

**避坑要点**：
- 基于优化版Playwright实现
- 完整的反检测技术
- 智能频率控制

### 3. 🎥 本地GPU Pipeline模块 (`local_gpu_pipeline.py`)

**功能**：RTX 3060本地视频后处理

**核心能力**：
- ✅ 超分辨率处理（Real-ESRGAN）
- ✅ 视频抠像（RVM）
- ✅ 背景替换（FFmpeg）
- ✅ 质量优化
- ✅ 并行处理

**避坑要点**：
- GPU内存管理
- 处理顺序优化（先超分再抠像）
- 音轨保留

### 4. 🎼 编排器模块 (`dance_orchestrator.py`)

**功能**：协调各模块执行，管理整体流程

**核心能力**：
- ✅ 项目生命周期管理
- ✅ 阶段间数据流转
- ✅ 进度监控
- ✅ 错误恢复
- ✅ 报告生成

## 🚀 快速开始

### 1. 环境初始化

```bash
# 初始化项目结构
python dance_main.py config --init

# 检查配置
python dance_main.py config --check
```

### 2. 准备素材

```bash
# 将原始视频放入输入目录
cp your_videos/*.mp4 input_videos/

# 将背景视频放入背景库
cp background_videos/*.mp4 backgrounds/
```

### 3. 运行处理

```bash
# 运行完整pipeline
python dance_main.py full --input ./input_videos --project "广场舞批次1"

# 或分步骤运行
python dance_main.py preprocess --input ./input_videos
python dance_main.py viggle
python dance_main.py gpu --input ./viggle_results
```

### 4. 查看结果

```bash
# 查看项目状态
python dance_main.py status

# 查看最终输出
ls final_output/
```

## 📁 目录结构

```
dance/
├── modules/                    # 核心模块
│   ├── video_preprocessor.py  # 片源预处理
│   ├── viggle_automation.py   # Viggle自动化
│   ├── local_gpu_pipeline.py  # 本地GPU处理
│   └── dance_orchestrator.py  # 编排器
├── scripts/                   # 独立脚本
│   ├── viggle_playwright_optimized.py
│   └── login_once.py
├── config/                    # 配置文件
├── input_videos/              # 输入视频
├── viggle_results/            # Viggle处理结果
├── final_output/              # 最终输出
├── backgrounds/               # 背景视频库
├── reports/                   # 处理报告
├── logs/                      # 日志文件
├── dance_main.py             # 主入口
└── README_MODULES.md         # 本文档
```

## ⚙️ 配置说明

每个模块都有独立的配置文件：

- `config/preprocessor_config.json` - 预处理规则
- `config/viggle_automation_config.json` - Viggle设置
- `config/gpu_pipeline_config.json` - GPU处理参数
- `config/orchestrator_config.json` - 编排器设置

## 📊 数据流转

### 1. 预处理阶段

```
原始视频 → 质量检测 → 兼容性评估 → 分类标记 → 处理队列
```

**输出**：`processing_queue.json`

### 2. Viggle处理阶段

```
处理队列 → 账号调度 → 批量上传 → 生成监控 → 结果下载
```

**输出**：`viggle_results/category/video_files.mp4`

### 3. GPU处理阶段

```
Viggle结果 → 超分辨率 → 视频抠像 → 背景替换 → 质量优化
```

**输出**：`final_output/category/final_videos.mp4`

## 🔧 高级用法

### 1. 自定义配置

```python
# 修改预处理规则
{
  "viggle_requirements": {
    "min_duration": 10,        # 最短10秒
    "max_duration": 180,       # 最长3分钟
    "target_resolution": [1280, 720]  # 目标分辨率
  }
}
```

### 2. 多账号配置

```python
# Viggle多账号轮换
{
  "accounts": [
    {"email": "account1@example.com", "daily_limit": 30},
    {"email": "account2@example.com", "daily_limit": 25}
  ]
}
```

### 3. GPU优化

```python
# GPU处理优化
{
  "processing": {
    "max_concurrent_jobs": 2,  # 3060建议最多2个并发
    "superres_scale": 2        # 超分倍数
  }
}
```

## 📈 性能指标

### 典型处理能力

- **预处理**：500个视频/小时
- **Viggle处理**：30个视频/天（Pro账号限制）
- **GPU处理**：7-8分钟/视频（3060）

### 成本估算

- **Viggle积分**：~2积分/视频
- **GPU电费**：~¥0.3/视频
- **总成本**：~¥40-50/视频（含Viggle Pro）

## 🚨 常见问题

### Q: 预处理时显示"兼容性过低"？
A: 检查视频分辨率、时长、格式是否符合Viggle要求

### Q: Viggle处理失败率高？
A: 检查网络连接，降低并发数，确认账号状态

### Q: GPU处理内存不足？
A: 降低并发数量，检查视频分辨率设置

### Q: 背景替换效果不好？
A: 确保抠像质量，选择合适的背景视频

## 🛡️ 安全建议

1. **账号安全**：使用专门的测试账号
2. **频率控制**：严格遵守平台限制
3. **数据备份**：定期备份处理结果
4. **监控告警**：设置处理失败告警

## 🔄 更新日志

- **v1.0** - 初始模块化架构
- **v1.1** - 优化Playwright反检测
- **v1.2** - 增加GPU处理pipeline
- **v1.3** - 完善编排器功能

---

这个模块化设计让你可以：

✅ **分步调试** - 每个模块独立测试
✅ **灵活配置** - 根据需求调整参数
✅ **扩展升级** - 单独升级某个模块
✅ **监控管理** - 完整的状态追踪

立即开始你的AI视频处理之旅！🚀
