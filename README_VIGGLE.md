# 🎭 Viggle Playwright 自动化系统

> 基于 engineering-memory 最佳实践的专业级 Viggle 自动化解决方案

## 🎯 系统特色

### 🧠 Engineering-Memory 架构
- **结构化问题分析**: 背景 → 问题 → 解决方案 → 验证
- **模块化设计**: 会话管理 + 行为模拟 + 任务队列 + 错误处理
- **可观测性**: 结构化日志 + 错误追踪 + 性能监控
- **故障恢复**: 断点续传 + 自动重试 + 状态持久化

### 🛡️ 反检测技术
- **浏览器指纹随机化**: User-Agent + 视窗 + 插件伪造
- **人类行为模拟**: 随机延迟 + 鼠标轨迹 + 打字模式
- **会话持久化**: Cookie管理 + 状态保存 + 自动恢复
- **智能频控**: 动态间隔 + 账号轮换 + 高峰避让

### ⚡ 性能优化
- **并行处理**: 多账号同时工作
- **智能调度**: 负载均衡 + 失败重试
- **资源管理**: 内存控制 + 会话复用
- **断点续传**: 任务状态持久化

## 🚀 快速开始

### 1️⃣ 环境检查
```bash
# 运行环境测试
python test_viggle.py
```

### 2️⃣ 初始化设置
```bash
# 运行设置向导
python setup_viggle.py
```

### 3️⃣ 准备素材
```bash
# 目录结构
input/
├── videos/     # 放置原始视频 (.mp4, .avi, .mov)
└── people/     # 放置AI人像 (.jpg, .png)
```

### 4️⃣ 开始处理
```bash
# 运行自动化处理
python scripts/viggle_playwright_enhanced.py
```

## 📁 项目架构

```
dance/
├── 📊 核心文件
│   ├── config.json                           # 主配置文件
│   ├── setup_viggle.py                       # 设置向导
│   ├── test_viggle.py                        # 环境测试
│   └── README_VIGGLE.md                      # 使用说明
├── 📁 输入输出
│   ├── input/
│   │   ├── videos/                          # 原始视频
│   │   └── people/                          # AI人像
│   └── output/                              # 处理结果
├── 🎭 核心脚本
│   └── scripts/
│       └── viggle_playwright_enhanced.py     # 主处理程序
├── 💾 运行时数据
│   ├── profiles/                            # 浏览器配置
│   ├── logs/                               # 日志文件
│   └── temp/                               # 临时文件
└── 📚 文档
    └── docs/
        └── engineering-best-practices.md    # 工程最佳实践
```

## ⚙️ 配置说明

### 账号配置 (config.json)
```json
{
  "accounts": [
    {
      "email": "your_email@example.com",
      "password": "your_password",
      "daily_limit": 30,
      "profile_dir": "./profiles/main_account"
    }
  ],
  "processing": {
    "max_retries": 3,
    "timeout_minutes": 15,
    "parallel_accounts": 2
  }
}
```

### 反检测配置
```json
{
  "anti_detection": {
    "random_delays": true,
    "human_behavior": true,
    "session_persistence": true
  }
}
```

## 🎛️ 高级功能

### 📊 任务队列管理
```python
# 任务状态追踪
- pending: 等待处理
- processing: 正在处理  
- completed: 处理完成
- failed: 处理失败

# 支持断点续传
- 程序中断后可恢复
- 失败任务自动重试
- 状态持久化保存
```

### 🔍 实时监控
```bash
# 查看日志
tail -f logs/viggle_YYYYMMDD.log

# 检查任务状态
python -c "
from scripts.viggle_playwright_enhanced import TaskQueue
queue = TaskQueue()
print(f'待处理: {len(queue.get_pending_tasks())}')
print(f'失败重试: {len(queue.get_failed_tasks())}')
"
```

### 🛠️ 故障排除

#### 常见问题
1. **登录失败**
   ```bash
   # 检查账号配置
   python test_viggle.py
   
   # 清除会话状态
   rm -rf profiles/*/storage_state.json
   ```

2. **上传失败**
   ```bash
   # 检查视频格式
   支持: .mp4, .avi, .mov, .mkv
   大小: < 100MB
   时长: < 10分钟
   ```

3. **生成超时**
   ```bash
   # 调整超时设置
   vim config.json
   # 增加 timeout_minutes
   ```

4. **反检测触发**
   ```bash
   # 降低并发
   "parallel_accounts": 1
   
   # 增加延迟
   "task_interval_seconds": [120, 300]
   ```

## 📈 性能调优

### 🎯 最佳实践
```json
{
  "推荐配置": {
    "single_account": {
      "daily_limit": 30,
      "parallel_tasks": 1,
      "interval_seconds": [60, 120]
    },
    "multi_account": {
      "max_accounts": 3,
      "per_account_limit": 20,
      "stagger_start": true
    }
  }
}
```

### ⏰ 处理时间估算
```
单个5分钟视频:
- 上传时间: 1-2分钟
- 生成时间: 3-8分钟  
- 下载时间: 30秒-1分钟
- 总计: 5-12分钟

批量处理:
- 500个视频 ≈ 2-3天 (3账号并行)
- 建议分批处理: 50个/批次
```

## 🔒 安全考虑

### 账号安全
- ✅ 使用专门的测试账号
- ✅ 启用二步验证
- ✅ 定期更换密码
- ✅ 监控账号状态

### 数据安全  
- ✅ 本地存储敏感信息
- ✅ 加密配置文件
- ✅ 定期备份数据
- ✅ 清理临时文件

## 🚨 风险管理

### 限制策略
```json
{
  "daily_limits": {
    "per_account": 30,
    "total_across_accounts": 80
  },
  "rate_limits": {
    "min_interval_seconds": 60,
    "max_concurrent_tasks": 3,
    "peak_hour_avoidance": [9,10,11,14,15,16,20,21,22]
  }
}
```

### 应急处理
1. **检测到风险**: 自动暂停处理
2. **账号异常**: 切换备用账号  
3. **系统过载**: 降低并发数
4. **网络异常**: 自动重试机制

## 📚 学习资源

### Engineering-Memory 参考
- [软件工程最佳实践](docs/engineering-best-practices.md)
- [反检测技术指南](docs/playwright-anti-detection-best-practices.md)
- [任务队列设计模式](docs/detailed-workflow-best-practices.md)

### 技术文档
- [Playwright 官方文档](https://playwright.dev/)
- [反检测技术研究](docs/viggle-anti-detection-guide.md)
- [错误处理最佳实践](docs/engineering-best-practices.md#错误分析框架)

## 🤝 贡献指南

基于 engineering-memory 的贡献流程:
1. **问题定义**: 具体描述要解决的问题
2. **背景调研**: 分析问题产生的原因
3. **方案设计**: 提出解决方案和实现思路
4. **实现验证**: 编写代码并充分测试
5. **经验总结**: 文档化经验和避坑指南

## 📄 许可证

MIT License - 基于 engineering-memory 开源精神

---

**💡 提示**: 使用前请仔细阅读 Viggle 的服务条款，确保合规使用。

**🆘 支持**: 遇到问题请查看日志文件或运行测试脚本诊断。
