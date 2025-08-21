# 🔐 Google OAuth登录指南

## 📋 **概述**

Google OAuth登录用于Viggle自动化系统，支持：
- 自动登录Google账号
- 保存会话状态
- 处理安全验证
- 与Viggle集成

## 🚀 **快速开始**

### **方法1: 使用简化登录工具**

```bash
# 运行Google OAuth登录工具
python tools/google_oauth_login.py
```

**步骤**:
1. 输入Google邮箱
2. 输入密码
3. 按提示完成安全验证（如有）
4. 登录成功后自动保存会话状态

### **方法2: 手动配置**

#### **1. 配置Google账号**

编辑 `config/accounts.json`:
```json
{
  "accounts": [
    {
      "email": "your_google_email@gmail.com",
      "password": "your_password",
      "storage_state_path": "secrets/google_session_your_email.json",
      "daily_limit": 150,
      "concurrent_limit": 1,
      "rate_limit_min": 60,
      "rate_limit_max": 120,
      "status": "active",
      "notes": "Google账号 - 处理150个视频"
    }
  ]
}
```

#### **2. 配置OAuth设置**

编辑 `config/google_oauth_config.json`:
```json
{
  "google": {
    "login_url": "https://accounts.google.com/signin",
    "oauth_url": "https://accounts.google.com/o/oauth2/auth",
    "consent_url": "https://accounts.google.com/signin/oauth/consent"
  },
  "browser": {
    "headless": false,
    "slow_mo": 1000,
    "timeout": 30000,
    "viewport": {"width": 1366, "height": 768}
  },
  "oauth": {
    "client_id": "",
    "redirect_uri": "http://localhost:8080/callback",
    "scope": "openid email profile",
    "response_type": "code"
  }
}
```

## 🔧 **详细步骤**

### **步骤1: 准备Google账号**

确保您的Google账号：
- ✅ 已启用两步验证
- ✅ 有备用邮箱或手机号
- ✅ 可以正常登录Google服务

### **步骤2: 运行登录工具**

```bash
python tools/google_oauth_login.py
```

### **步骤3: 完成登录流程**

1. **输入邮箱**: 输入您的Google邮箱地址
2. **输入密码**: 输入您的Google密码
3. **安全验证**: 如果出现安全验证，按提示完成
4. **确认登录**: 登录成功后按回车继续

### **步骤4: 验证登录状态**

```bash
# 检查会话状态文件
ls secrets/

# 检查账号配置
cat config/accounts.json
```

## ⚠️ **安全验证处理**

### **常见安全验证类型**

#### **1. 两步验证**
- 输入验证码或使用Google Authenticator
- 选择备用验证方式

#### **2. 设备验证**
- 确认是否在可信设备上登录
- 可能需要输入备用邮箱或手机号

#### **3. 异常活动检测**
- 可能需要验证身份
- 输入备用邮箱或手机号

### **手动处理步骤**

当遇到安全验证时：
1. 在浏览器中手动完成验证
2. 验证完成后按回车继续
3. 系统会自动保存会话状态

## 🔄 **会话管理**

### **会话状态文件**

登录成功后，系统会在 `secrets/` 目录下创建会话状态文件：
```
secrets/
├── google_session_your_email.json    # Google会话状态
└── account_state.json               # 账号状态
```

### **会话有效期**

- **默认有效期**: 30天
- **自动刷新**: 系统会自动刷新会话
- **手动刷新**: 重新运行登录工具

### **会话恢复**

如果会话过期，重新运行登录工具即可：
```bash
python tools/google_oauth_login.py
```

## 🔗 **与Viggle集成**

### **自动登录Viggle**

配置好Google OAuth后，Viggle自动化系统会：
1. 使用保存的Google会话状态
2. 自动登录Viggle
3. 开始批量处理视频

### **运行Viggle处理**

```bash
# 使用Google OAuth登录的账号运行处理
python tools/batch_processor.py
```

## 🛠️ **故障排除**

### **常见问题**

#### **1. 登录失败**
```bash
# 检查网络连接
ping accounts.google.com

# 检查账号状态
python tools/google_oauth_login.py
```

#### **2. 安全验证无法通过**
- 确保备用邮箱/手机号正确
- 尝试使用不同的验证方式
- 检查Google账号设置

#### **3. 会话状态丢失**
```bash
# 重新登录
python tools/google_oauth_login.py

# 检查配置文件
cat config/accounts.json
```

#### **4. 浏览器启动失败**
```bash
# 安装Playwright浏览器
playwright install chromium

# 检查Playwright安装
python -c "import playwright; print('Playwright已安装')"
```

### **调试模式**

启用详细日志：
```bash
# 设置日志级别
export PYTHONPATH=.
python -u tools/google_oauth_login.py
```

## 📊 **最佳实践**

### **1. 账号安全**
- 使用强密码
- 启用两步验证
- 定期更换密码

### **2. 会话管理**
- 定期检查会话状态
- 及时更新过期会话
- 备份重要配置

### **3. 自动化运行**
- 使用cron定时任务
- 监控登录状态
- 自动处理异常

### **4. 监控和日志**
- 定期查看日志文件
- 监控登录成功率
- 记录异常情况

## 🎯 **完成检查**

登录成功后，您应该看到：

✅ **会话状态文件**: `secrets/google_session_*.json`  
✅ **账号配置更新**: `config/accounts.json`  
✅ **登录成功消息**: "Google登录成功！"  
✅ **可以运行Viggle**: `python tools/batch_processor.py`  

现在您的Google OAuth已经配置完成，可以开始Viggle自动化处理了！🚀

