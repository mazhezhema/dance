# SQLite数据库使用指南

## 概述

Dance项目使用SQLite数据库来管理任务状态、进度跟踪和统计信息。相比之前的文件系统标记方式，SQLite提供了更强大的数据管理和查询能力。

## 数据库结构

### 主要表

#### 1. tasks (任务状态表)
```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,           -- 任务ID (基于文件MD5)
    input_file TEXT NOT NULL,           -- 输入文件路径
    output_file TEXT,                   -- 输出文件路径
    status TEXT NOT NULL DEFAULT 'pending', -- 状态: pending/processing/completed/failed
    account_id TEXT,                    -- 处理账号
    created_at TEXT,                    -- 创建时间
    started_at TEXT,                    -- 开始时间
    completed_at TEXT,                  -- 完成时间
    processing_time REAL,               -- 处理时间(秒)
    retries INTEGER DEFAULT 0,          -- 重试次数
    max_retries INTEGER DEFAULT 2,      -- 最大重试次数
    error_message TEXT,                 -- 错误信息
    file_size_mb REAL,                  -- 文件大小(MB)
    video_duration REAL,                -- 视频时长(秒)
    updated_at TEXT                     -- 更新时间
);
```

#### 2. task_logs (任务日志表)
```sql
CREATE TABLE task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,              -- 任务ID
    log_level TEXT NOT NULL,            -- 日志级别: INFO/WARNING/ERROR
    message TEXT NOT NULL,              -- 日志消息
    timestamp TEXT NOT NULL,            -- 时间戳
    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
);
```

#### 3. account_stats (账号统计表)
```sql
CREATE TABLE account_stats (
    account_id TEXT PRIMARY KEY,        -- 账号ID
    total_tasks INTEGER DEFAULT 0,      -- 总任务数
    completed_tasks INTEGER DEFAULT 0,  -- 成功任务数
    failed_tasks INTEGER DEFAULT 0,     -- 失败任务数
    total_processing_time REAL DEFAULT 0, -- 总处理时间
    last_used TEXT,                     -- 最后使用时间
    daily_limit INTEGER DEFAULT 30,     -- 每日限制
    daily_used INTEGER DEFAULT 0,       -- 今日已用
    reset_date TEXT                     -- 重置日期
);
```

## 使用方法

### 1. 任务监控工具

使用 `scripts/task_monitor.py` 查看任务状态和统计信息：

```bash
# 查看总体统计
python scripts/task_monitor.py stats

# 查看最近完成的任务
python scripts/task_monitor.py recent 20

# 查看待处理任务
python scripts/task_monitor.py pending

# 查看特定任务详情
python scripts/task_monitor.py task <任务ID>

# 查看账号统计
python scripts/task_monitor.py account <账号邮箱>

# 导出统计信息
python scripts/task_monitor.py export

# 显示帮助
python scripts/task_monitor.py help
```

### 2. 主程序状态查看

```bash
# 查看项目整体状态
python dance_main.py status
```

### 3. 数据库API使用

在代码中使用数据库：

```python
from scripts.task_database import task_db, TaskStatus

# 创建任务
task = TaskStatus(
    task_id="abc123",
    input_file="video.mp4",
    status="pending",
    created_at=datetime.now().isoformat()
)
task_db.add_task(task)

# 更新任务状态
task_db.update_task_status("abc123", "processing", 
                          started_at=datetime.now().isoformat())

# 添加日志
task_db.add_task_log("abc123", "INFO", "开始处理任务")

# 获取统计信息
stats = task_db.get_overall_stats()
```

## 状态管理

### 任务状态流转

```
pending → processing → completed
    ↓         ↓
  failed ← retry
```

- **pending**: 待处理
- **processing**: 处理中
- **completed**: 已完成
- **failed**: 失败

### 重试机制

- 默认最大重试次数：2次
- 失败任务会自动重新进入待处理队列
- 超过重试次数的任务标记为最终失败

## 统计功能

### 总体统计
- 任务总数、完成数、失败数
- 成功率、平均处理时间
- 各状态任务数量

### 账号统计
- 每个账号的使用情况
- 每日使用限制和计数
- 成功率统计

### 日志记录
- 详细的任务处理日志
- 错误信息和调试信息
- 时间戳记录

## 数据导出

### JSON导出
```bash
python scripts/task_monitor.py export
```

导出的JSON文件包含：
- 总体统计信息
- 最近50个已完成任务
- 导出时间戳

### 数据库文件
- 位置：`tasks/task_status.db`
- 格式：SQLite 3
- 可直接用SQLite工具查看

## 优势对比

### 相比文件系统标记的优势

| 特性 | 文件系统标记 | SQLite数据库 |
|------|-------------|-------------|
| 状态查询 | 需要扫描文件 | 快速SQL查询 |
| 统计信息 | 手动计算 | 自动统计 |
| 日志记录 | 分散在日志文件 | 结构化存储 |
| 重试机制 | 复杂实现 | 内置支持 |
| 并发安全 | 文件锁问题 | 数据库锁 |
| 数据完整性 | 容易损坏 | ACID保证 |

### 性能特点
- 轻量级：单个文件，无需服务器
- 快速：索引优化查询
- 可靠：事务保证数据一致性
- 便携：可复制、备份、迁移

## 维护建议

### 定期清理
```python
# 清理过期的日志记录
# 保留最近30天的日志
```

### 备份策略
```bash
# 定期备份数据库文件
cp tasks/task_status.db tasks/backup_$(date +%Y%m%d).db
```

### 性能优化
- 定期VACUUM数据库
- 监控数据库文件大小
- 清理过期数据

## 故障排除

### 常见问题

1. **数据库文件损坏**
   ```bash
   # 删除损坏的数据库，系统会自动重建
   rm tasks/task_status.db
   ```

2. **权限问题**
   ```bash
   # 确保有写入权限
   chmod 755 tasks/
   ```

3. **导入错误**
   ```python
   # 检查模块路径
   import sys
   sys.path.append(str(Path(__file__).parent.parent))
   ```

### 调试技巧

1. 使用SQLite命令行工具查看数据：
   ```bash
   sqlite3 tasks/task_status.db
   .tables
   SELECT * FROM tasks LIMIT 5;
   ```

2. 查看详细日志：
   ```bash
   tail -f logs/viggle_enhanced.log
   ```

3. 导出数据进行离线分析：
   ```bash
   python scripts/task_monitor.py export
   ```

## 扩展功能

### 未来计划
- Web界面展示统计信息
- 实时任务进度监控
- 邮件通知功能
- 多项目支持
- 数据可视化图表
