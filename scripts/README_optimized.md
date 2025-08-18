# Viggle Playwright 优化版自动化处理器

## 🎯 特色功能

基于最新最佳实践设计，整合了生产级经验：

- ✅ **会话持久化** - 手动登录一次，永久复用
- ✅ **语义选择器** - 抗DOM变化，更稳定
- ✅ **事件驱动下载** - 100%可靠的文件下载
- ✅ **智能超时** - 根据视频长度动态调整
- ✅ **多账号轮换** - 自动负载均衡
- ✅ **人类化行为** - 随机延迟、鼠标移动
- ✅ **资源拦截** - 屏蔽广告提升稳定性
- ✅ **幂等处理** - 基于MD5防重复处理

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install playwright tenacity aiofiles
playwright install chromium

# 创建项目结构
mkdir -p {config,secrets,tasks_in,downloads,logs}
```

### 2. 首次登录配置

```bash
# 运行登录脚本（只需一次）
python login_once.py
```

按提示在浏览器中手动登录，脚本会自动保存会话状态。

### 3. 配置账号

编辑 `config/accounts.json`：

```json
[
  {
    "email": "your-account@example.com",
    "storage_state_path": "secrets/your_account_state.json",
    "daily_limit": 30,
    "concurrent_limit": 3
  }
]
```

### 4. 准备素材

```bash
# 将视频文件放入输入目录
cp your_videos/*.mp4 tasks_in/
```

### 5. 开始处理

```bash
python viggle_playwright_optimized.py
```

## 📁 目录结构

```
viggle-playwright/
├── config/
│   ├── viggle_config.json      # 主配置文件
│   └── accounts.json           # 账号配置
├── secrets/
│   └── *_state.json           # 会话状态文件（不要提交到git）
├── tasks_in/
│   └── *.mp4                  # 待处理视频
├── downloads/
│   └── *_viggle_*.mp4         # 处理结果
├── logs/
│   ├── viggle_optimized.log   # 运行日志
│   └── error_*.png            # 错误截图
├── login_once.py              # 会话导出工具
└── viggle_playwright_optimized.py  # 主处理程序
```

## ⚙️ 配置说明

### 主配置文件 (config/viggle_config.json)

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

### 账号配置 (config/accounts.json)

```json
[
  {
    "email": "account1@example.com",
    "storage_state_path": "secrets/account1_state.json",
    "daily_limit": 30,
    "concurrent_limit": 3
  },
  {
    "email": "account2@example.com", 
    "storage_state_path": "secrets/account2_state.json",
    "daily_limit": 25,
    "concurrent_limit": 2
  }
]
```

## 🛡️ 反检测特性

### 1. 会话管理
- 手动登录导出，避免频繁自动登录
- 会话状态持久化，减少检测风险
- 支持多账号独立会话

### 2. 行为模拟
- 随机延迟 (45-90秒)
- 鼠标移动和页面滚动
- 自然的操作节奏

### 3. 技术措施
- 语义选择器替代脆弱的CSS选择器
- 资源拦截减少干扰
- 智能重试机制
- 错误截图用于调试

## 📊 监控和日志

### 日志级别
- **INFO**: 正常操作流程
- **WARNING**: 需要注意的情况
- **ERROR**: 处理失败的任务

### 关键指标
- 任务处理成功率
- 平均处理时长
- 账号使用分布
- 错误类型统计

## 🔧 故障排除

### 常见问题

#### 1. 会话过期
```
错误: 需要重新登录
解决: 重新运行 python login_once.py
```

#### 2. 文件上传失败
```
错误: 未找到文件上传元素
解决: 检查视频格式和大小，确保符合Viggle要求
```

#### 3. 生成超时
```
错误: 未检测到下载按钮
解决: 增加 generate_timeout_minutes 配置
```

#### 4. 下载失败
```
错误: 下载事件捕获失败
解决: 检查网络连接，重试任务
```

### 调试技巧

1. **开启可视化模式**
   ```json
   "browser": {"headless": false}
   ```

2. **查看错误截图**
   ```bash
   ls logs/error_*.png
   ```

3. **查看详细日志**
   ```bash
   tail -f logs/viggle_optimized.log
   ```

## 🚨 安全提醒

1. **会话文件安全**
   - `secrets/` 目录不要提交到版本控制
   - 定期更新会话状态
   - 不要在多设备同时使用同一账号

2. **频率控制**
   - 严格遵守配置的限额
   - 避开网站高峰时段
   - 监控账号状态变化

3. **合规使用**
   - 仅处理有权使用的素材
   - 遵守Viggle服务条款
   - 保留处理记录用于审计

## 🔄 与后续流程衔接

处理完成的视频会保存在 `downloads/` 目录，命名格式：
```
{task_id}_viggle_{timestamp}.mp4
```

可以直接对接你的本地GPU处理流程：
```bash
# 示例：将结果移动到GPU处理队列
mv downloads/*_viggle_*.mp4 ../gpu_pipeline/input/
```

## 📈 性能优化建议

1. **并发设置**
   - 每账号2-3个并发任务
   - 避免单账号过载

2. **网络优化**
   - 使用稳定的网络连接
   - 考虑CDN加速下载

3. **存储优化**
   - 定期清理已处理文件
   - 使用SSD提升I/O性能

4. **监控告警**
   - 设置成功率阈值告警
   - 监控磁盘空间使用

---

这个优化版本基于最新的Playwright最佳实践，专为稳定性和反检测设计。如有问题，请查看日志文件或提交issue。
