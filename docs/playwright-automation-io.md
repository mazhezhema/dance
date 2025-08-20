# Playwright自动化模块 - 输入输出详细说明

## 🎯 概述

本文档详细说明Playwright自动化模块的输入和输出，包括数据流、文件结构、配置参数等。

## 📥 输入 (Input)

### 1. 配置文件

#### 主配置文件: `config/viggle_config.json`
```json
{
  "viggle": {
    "app_url": "https://viggle.ai/app",
    "login_url": "https://viggle.ai/login"
  },
  "processing": {
    "concurrent_per_account": 3,
    "rate_limit_min": 45,
    "rate_limit_max": 90,
    "max_retries": 2,
    "generate_timeout_minutes": 10
  },
  "browser": {
    "headless": true,
    "slow_mo": 0,
    "timeout": 120000
  }
}
```

#### 账号配置文件: `config/accounts.json`
```json
[
  {
    "email": "account1@example.com",
    "storage_state_path": "secrets/account1_state.json",
    "daily_limit": 30,
    "concurrent_limit": 3,
    "notes": "主账号"
  },
  {
    "email": "account2@example.com", 
    "storage_state_path": "secrets/account2_state.json",
    "daily_limit": 25,
    "concurrent_limit": 2,
    "notes": "备用账号"
  }
]
```

### 2. 输入视频文件

#### 目录结构
```
input/
├── video1.mp4          # 输入视频文件
├── video2.mp4
├── dance_video.mp4
└── ...
```

#### 视频文件要求
- **格式**: MP4, MOV, AVI, MKV
- **分辨率**: 建议 720p 以上
- **时长**: 建议 10秒 - 5分钟
- **大小**: 建议 < 100MB
- **编码**: H.264, H.265

### 3. 会话状态文件

#### 目录结构
```
secrets/
├── account1_state.json     # 账号1的会话状态
├── account2_state.json     # 账号2的会话状态
└── ...
```

#### 会话状态内容
```json
{
  "cookies": [
    {
      "name": "session_id",
      "value": "abc123...",
      "domain": ".viggle.ai",
      "path": "/"
    }
  ],
  "origins": [
    {
      "origin": "https://viggle.ai",
      "localStorage": [
        {
          "name": "user_token",
          "value": "xyz789..."
        }
      ]
    }
  ]
}
```

### 4. 环境变量 (可选)

```bash
# 代理设置
HTTP_PROXY=http://proxy:8080
HTTPS_PROXY=http://proxy:8080

# 浏览器设置
PLAYWRIGHT_BROWSERS_PATH=/path/to/browsers

# 日志级别
LOG_LEVEL=INFO
```

## 📤 输出 (Output)

### 1. 处理结果文件

#### 目录结构
```
output/
├── abc123_viggle_processed.mp4    # 处理后的视频
├── def456_viggle_enhanced.mp4
├── ghi789_viggle_result.mp4
└── ...
```

#### 文件命名规则
```
{task_id}_viggle_{timestamp}.mp4
```

- `task_id`: 基于输入文件的MD5哈希值（前12位）
- `timestamp`: 处理时间戳

### 2. 日志文件

#### 目录结构
```
logs/
├── viggle_optimized.log           # 主日志文件
├── viggle_20241201.log           # 按日期分组的日志
├── error_screenshots/            # 错误截图
│   ├── error_20241201_143022.png
│   └── ...
└── ...
```

#### 日志内容示例
```
2024-12-01 14:30:22 - INFO - 🚀 开始批量处理...
2024-12-01 14:30:22 - INFO - 📋 找到 3 个待处理任务
2024-12-01 14:30:23 - INFO - 👤 账号 account1@example.com 开始处理 2 个任务
2024-12-01 14:30:25 - INFO - 上传文件: input/video1.mp4
2024-12-01 14:30:30 - INFO - 等待生成完成...
2024-12-01 14:35:45 - INFO - ✅ [abc123def456] 处理成功: output/abc123_viggle_processed.mp4
```

### 3. 任务状态文件

#### 目录结构
```
tasks/
├── pending_tasks.json            # 待处理任务列表
├── completed_tasks.json          # 已完成任务列表
├── failed_tasks.json            # 失败任务列表
└── task_history.json            # 任务历史记录
```

#### 任务状态示例
```json
{
  "task_id": "abc123def456",
  "src_path": "input/video1.mp4",
  "account_id": "account1@example.com",
  "status": "completed",
  "start_time": "2024-12-01T14:30:25",
  "end_time": "2024-12-01T14:35:45",
  "output_path": "output/abc123_viggle_processed.mp4",
  "processing_time": 320,
  "retries": 0
}
```

### 4. 统计报告

#### 目录结构
```
reports/
├── daily_report_20241201.json    # 每日处理报告
├── account_usage.json           # 账号使用统计
├── performance_metrics.json     # 性能指标
└── error_summary.json          # 错误汇总
```

#### 报告内容示例
```json
{
  "date": "2024-12-01",
  "total_tasks": 15,
  "completed_tasks": 13,
  "failed_tasks": 2,
  "success_rate": 86.67,
  "total_processing_time": 4800,
  "average_processing_time": 320,
  "account_usage": {
    "account1@example.com": {
      "tasks_processed": 8,
      "daily_limit_used": 8,
      "daily_limit_remaining": 22
    }
  }
}
```

## 🔄 数据流

### 1. 任务处理流程

```
输入视频 → 任务创建 → 账号分配 → 浏览器启动 → 
登录验证 → 文件上传 → 等待处理 → 下载结果 → 
文件保存 → 状态更新 → 日志记录
```

### 2. 错误处理流程

```
错误发生 → 错误捕获 → 截图保存 → 日志记录 → 
重试判断 → 重试执行 → 最终失败 → 错误报告
```

### 3. 并发处理流程

```
任务列表 → 按账号分组 → 并行处理 → 结果收集 → 
状态更新 → 完成报告
```

## 📊 性能指标

### 1. 处理时间
- **平均处理时间**: 5-10分钟/视频
- **上传时间**: 30秒-2分钟
- **生成时间**: 3-8分钟
- **下载时间**: 30秒-1分钟

### 2. 成功率
- **整体成功率**: 85-95%
- **网络错误率**: 3-8%
- **账号限制率**: 2-5%

### 3. 资源使用
- **内存使用**: 500MB-1GB/浏览器实例
- **CPU使用**: 10-30%/核心
- **网络带宽**: 1-5MB/s

## ⚙️ 配置参数详解

### 1. 处理参数
```json
{
  "concurrent_per_account": 3,    // 每个账号同时处理的任务数
  "rate_limit_min": 45,          // 任务间最小间隔(秒)
  "rate_limit_max": 90,          // 任务间最大间隔(秒)
  "max_retries": 2,              // 最大重试次数
  "generate_timeout_minutes": 10  // 生成超时时间(分钟)
}
```

### 2. 浏览器参数
```json
{
  "headless": true,              // 无头模式
  "slow_mo": 0,                  // 操作延迟(毫秒)
  "timeout": 120000              // 页面超时(毫秒)
}
```

### 3. 账号参数
```json
{
  "daily_limit": 30,             // 每日处理限制
  "concurrent_limit": 3,         // 并发处理限制
  "storage_state_path": "..."    // 会话状态文件路径
}
```

## 🛠️ 使用示例

### 1. 基本使用
```bash
# 运行自动化处理
python scripts/viggle_playwright_optimized.py

# 查看状态
python dance_main.py status

# 配置账号
python scripts/login_once.py
```

### 2. 自定义配置
```python
# 创建自定义配置
config = {
    "processing": {
        "concurrent_per_account": 2,
        "rate_limit_min": 60,
        "rate_limit_max": 120
    }
}

# 保存配置
with open("config/custom_config.json", "w") as f:
    json.dump(config, f, indent=2)
```

### 3. 监控输出
```python
# 监控处理进度
import json
import time

while True:
    with open("tasks/completed_tasks.json", "r") as f:
        completed = json.load(f)
    
    print(f"已完成: {len(completed)} 个任务")
    time.sleep(30)
```

## 📝 注意事项

1. **文件权限**: 确保脚本有读写输入输出目录的权限
2. **网络连接**: 需要稳定的网络连接访问Viggle
3. **账号状态**: 定期检查账号会话状态是否有效
4. **存储空间**: 确保有足够的磁盘空间存储输出文件
5. **并发限制**: 根据服务器性能调整并发参数
