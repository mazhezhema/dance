# 🎯 单账号大批量处理配置指南

## 📋 **配置概览**

针对您的需求：
- **200个视频**
- **10个人物图片**
- **10个背景图片**
- **1个Viggle账号**

## ⚙️ **配置步骤**

### **1. 账号配置**

编辑 `config/accounts.json`：
```json
{
  "accounts": [
    {
      "email": "your_viggle_account@example.com",
      "password": "your_password",
      "storage_state_path": "secrets/account_state.json",
      "daily_limit": 200,
      "concurrent_limit": 1,
      "rate_limit_min": 60,
      "rate_limit_max": 120,
      "status": "active",
      "notes": "主账号 - 处理200个视频"
    }
  ],
  "settings": {
    "max_retries": 3,
    "retry_delay_min": 300,
    "retry_delay_max": 600,
    "session_timeout": 3600,
    "max_concurrent_sessions": 1
  }
}
```

### **2. 文件组织**

#### **视频文件**
```bash
# 将所有200个视频放入输入目录
cp /path/to/your/200_videos/*.mp4 tasks_in/

# 检查文件数量
ls tasks_in/ | wc -l  # 应该显示200
```

#### **人物图片**
```bash
# 将10个人物图片放入人物目录
cp /path/to/your/10_people/*.jpg input/people/
cp /path/to/your/10_people/*.png input/people/

# 检查文件数量
ls input/people/ | wc -l  # 应该显示10
```

#### **背景图片**
```bash
# 将10个背景图片放入背景目录
cp /path/to/your/10_backgrounds/*.jpg backgrounds/
cp /path/to/your/10_backgrounds/*.png backgrounds/

# 检查文件数量
ls backgrounds/ | wc -l  # 应该显示10
```

### **3. 处理策略**

#### **分批处理**
- **批次大小**: 50个视频/批次
- **批次数量**: 4个批次 (50+50+50+50)
- **批次间暂停**: 30分钟 (1800秒)

#### **时间估算**
- **单视频处理**: 2-5分钟
- **间隔时间**: 1-2分钟
- **总处理时间**: 约10-15小时
- **建议**: 分2-3天完成

## 🚀 **运行步骤**

### **1. 环境检查**
```bash
# 检查系统状态
python main.py status

# 检查环境配置
python tools/check_environment.py
```

### **2. 登录Viggle**
```bash
# 首次登录并保存会话状态
python tools/login_once.py
```

### **3. 运行批量处理**
```bash
# 使用专用批量处理器
python tools/batch_processor.py

# 或者使用标准处理器
python main.py full
```

### **4. 监控进度**
```bash
# 查看任务状态
python tools/task_monitor.py stats

# 查看待处理任务
python tools/task_monitor.py pending

# 查看最近任务
python tools/task_monitor.py recent
```

## 📊 **处理时间表**

### **批次1 (50个视频)**
- **开始时间**: Day 1 09:00
- **预计完成**: Day 1 14:00
- **暂停时间**: 30分钟

### **批次2 (50个视频)**
- **开始时间**: Day 1 14:30
- **预计完成**: Day 1 19:30
- **暂停时间**: 30分钟

### **批次3 (50个视频)**
- **开始时间**: Day 2 09:00
- **预计完成**: Day 2 14:00
- **暂停时间**: 30分钟

### **批次4 (50个视频)**
- **开始时间**: Day 2 14:30
- **预计完成**: Day 2 19:30
- **完成**: 全部200个视频

## ⚠️ **注意事项**

### **1. 账号限制**
- **每日限制**: 确保账号支持200个/天
- **频率限制**: 60-120秒间隔避免被封
- **会话管理**: 定期保存会话状态

### **2. 系统要求**
- **网络稳定**: 确保网络连接稳定
- **存储空间**: 预留足够存储空间
- **电力供应**: 确保设备不会断电

### **3. 监控要点**
- **定期检查**: 每2-3小时检查一次进度
- **错误处理**: 关注失败任务和重试
- **日志分析**: 定期查看日志文件

## 🔧 **故障排除**

### **常见问题**

#### **1. 账号被封**
```bash
# 检查账号状态
python tools/login_once.py

# 如果被封，等待24小时后重试
```

#### **2. 网络中断**
```bash
# 检查网络连接
ping viggle.ai

# 重新启动处理
python tools/batch_processor.py
```

#### **3. 存储空间不足**
```bash
# 检查磁盘空间
df -h

# 清理临时文件
rm -rf temp_backgrounds/*
rm -rf temp_gpu/*
```

### **恢复处理**
```bash
# 查看未完成任务
python tools/task_monitor.py pending

# 继续处理
python main.py full
```

## 📈 **优化建议**

### **1. 性能优化**
- **使用SSD**: 提升I/O性能
- **关闭其他程序**: 释放系统资源
- **定期重启**: 每批次后重启系统

### **2. 成功率提升**
- **视频质量**: 使用高质量原始视频
- **人物图片**: 选择清晰、正面的人物照片
- **网络优化**: 使用有线网络连接

### **3. 监控优化**
- **设置提醒**: 配置处理完成提醒
- **自动备份**: 定期备份处理结果
- **日志分析**: 分析失败原因并优化

## 🎉 **完成检查**

### **最终验证**
```bash
# 检查处理结果
ls downloads/ | wc -l  # 应该接近200
ls final_output/ | wc -l  # 应该接近200

# 查看统计报告
cat logs/batch_processing_report.json

# 验证成功率
python tools/task_monitor.py stats
```

### **成功标准**
- ✅ **处理完成**: 200个视频全部处理
- ✅ **成功率**: >90%的成功率
- ✅ **质量检查**: 随机抽查几个视频质量
- ✅ **备份完成**: 重要文件已备份

这个配置方案专门针对您的单账号大批量处理需求进行了优化，确保高效、稳定地完成200个视频的处理！🚀
