# 🔧 配置系统说明

## 📋 概述

新的配置系统消除了硬编码值，提供了灵活的配置管理。

## 🎯 核心特性

### ✅ 消除硬编码
- 所有限制值、超时值都可配置
- 支持`null`值自动使用系统默认值
- 支持环境变量覆盖

### 🔄 动态配置
- 配置文件变更自动检测
- 运行时配置热加载
- 配置验证和错误检查

### 🌍 环境变量支持
- `DANCE_DAILY_LIMIT` - 每日处理限制
- `DANCE_CONCURRENT_LIMIT` - 并发限制
- `DANCE_GENERATION_TIMEOUT` - 生成超时(毫秒)
- `DANCE_BATCH_SIZE` - 批次大小
- `DANCE_GPU_MEMORY_LIMIT` - GPU显存限制(GB)
- `DANCE_LOG_LEVEL` - 日志级别
- `DANCE_SERVER_MODE` - 服务器模式(true/false)

## 📁 配置文件结构

### 优先级（从低到高）
1. `config.json` - 主配置文件 
2. `config/viggle_config.json` - Viggle配置
3. `config/accounts.json` - 账号配置
4. `config/local.json` - 本地配置（可选）
5. `.env.json` - 环境配置（可选）

### 配置文件说明

#### `config/accounts.json`
```json
{
  "_description": "账号配置文件 - 支持环境变量覆盖",
  "_env_overrides": {
    "daily_limit": "DANCE_DAILY_LIMIT",
    "concurrent_limit": "DANCE_CONCURRENT_LIMIT"
  },
  "accounts": [
    {
      "email": "your_email@gmail.com",
      "password": "your_password",
      "daily_limit": null,
      "concurrent_limit": null,
      "rate_limit_min": null,
      "rate_limit_max": null,
      "status": "active"
    }
  ]
}
```

#### `config/viggle_config.json`
```json
{
  "_description": "Viggle处理配置 - null值将使用系统默认配置",
  "processing": {
    "concurrent_per_account": null,
    "rate_limit_min": null,
    "rate_limit_max": null,
    "max_retries": null,
    "generate_timeout_minutes": null,
    "batch_size": null
  },
  "batch_processing": {
    "batch_size": null,
    "pause_between_batches": null,
    "max_daily_processing": null
  }
}
```

## 🚀 使用方法

### 代码中获取配置
```python
from src.config.manager import get_config

# 获取配置值
daily_limit = get_config('accounts.daily_limit')
timeout = get_config('timeouts.generation', 600000)

# 获取配置节段
accounts = get_config('accounts')
```

### 环境变量设置
```bash
# Windows
set DANCE_DAILY_LIMIT=100
set DANCE_BATCH_SIZE=30

# Linux/macOS
export DANCE_DAILY_LIMIT=100
export DANCE_BATCH_SIZE=30
```

### 配置适配器使用
```python
from src.config.adapter import adapt_account_config, get_timeout_ms

# 适配账号配置（null值自动填充默认值）
account_config = {"daily_limit": null, "email": "test@example.com"}
adapted = adapt_account_config(account_config)

# 获取超时值
timeout = get_timeout_ms('generation', 600000)
```

## 🎛️ 默认配置值

### 账号限制
- `daily_limit`: 50 (每日处理数量)
- `concurrent_limit`: 3 (并发处理数量)
- `rate_limit_min/max`: 60/120 (秒)
- `max_retries`: 3 (最大重试次数)

### 超时设置
- `page_load`: 30000ms (页面加载)
- `element_wait`: 10000ms (元素等待)
- `file_upload`: 60000ms (文件上传)
- `generation`: 600000ms (生成处理)
- `download`: 300000ms (下载)

### 批处理设置
- `batch_size`: 50 (批次大小)
- `pause_between_batches`: 1800s (批次间暂停)
- `max_daily_processing`: 200 (每日最大处理数)

### GPU处理设置
- `memory_limit_gb`: 10 (显存限制GB)
- `batch_size`: 1 (GPU批次大小)
- `device`: "auto" (设备选择)

## 📊 配置验证

系统会自动验证配置的合理性：
- 数值必须为正数
- 必需字段不能为空
- 类型检查
- 范围验证

## 🔍 配置调试

### 查看有效配置
```python
from src.config.manager import config_manager

# 导出当前有效配置
config_manager.export_effective_config("debug_config.json")
```

### 配置测试
```bash
# 测试配置系统
python src/config/defaults.py
python src/config/manager.py
python src/config/adapter.py
```

## 💡 最佳实践

1. **使用null值**: 配置文件中使用`null`让系统使用默认值
2. **环境变量**: 生产环境使用环境变量覆盖配置
3. **本地配置**: 开发环境创建`config/local.json`进行个性化配置
4. **配置分离**: 不同环境使用不同的配置文件组合
5. **定期验证**: 使用配置验证功能确保配置正确

## ⚠️ 注意事项

- 配置文件使用UTF-8编码
- null值会被默认值替换
- 环境变量优先级最高
- 配置变更会触发自动重载
- 验证失败会阻止程序启动
