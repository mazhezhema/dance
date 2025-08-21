# 🖥️ 服务器部署Google OAuth登录Viggle指南

## 📋 **服务器要求**

### **1. 基础要求**
- **操作系统**: Ubuntu 20.04+, CentOS 8+, Debian 11+
- **Python**: 3.8+
- **内存**: 4GB+ (推荐8GB)
- **存储**: 20GB+ 可用空间
- **网络**: 稳定的互联网连接
- **CPU**: 2核心+ (推荐4核心)

### **2. 云服务器推荐**
- **阿里云**: ECS 2核4GB
- **腾讯云**: CVM 2核4GB
- **AWS**: t3.medium
- **Azure**: Standard_B2s
- **Google Cloud**: e2-medium

## 🚀 **服务器部署步骤**

### **步骤1: 系统准备**

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git vim htop

# 安装Python依赖
sudo apt install -y python3 python3-pip python3-venv

# 安装浏览器依赖
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2
```

### **步骤2: 安装Playwright**

```bash
# 创建虚拟环境
python3 -m venv viggle_env
source viggle_env/bin/activate

# 安装Playwright
pip install playwright

# 安装浏览器
playwright install chromium

# 安装系统依赖
playwright install-deps
```

### **步骤3: 部署项目**

```bash
# 克隆项目
git clone <your-repo-url> /opt/viggle
cd /opt/viggle

# 安装项目依赖
pip install -r requirements.txt

# 创建必要目录
mkdir -p logs secrets config
```

### **步骤4: 配置Google OAuth**

```bash
# 编辑配置文件
vim config/accounts.json
```

```json
{
  "accounts": [
    {
      "email": "your_google_email@gmail.com",
      "password": "your_google_password",
      "storage_state_path": "secrets/viggle_google_session.json",
      "daily_limit": 150,
      "concurrent_limit": 1,
      "rate_limit_min": 60,
      "rate_limit_max": 120,
      "status": "active",
      "notes": "服务器Google绑定Viggle账号"
    }
  ]
}
```

### **步骤5: 运行服务器模式登录**

```bash
# 激活虚拟环境
source viggle_env/bin/activate

# 运行服务器模式登录
python tools/viggle_google_oauth_complete.py --server
```

## 🔧 **服务器模式特性**

### **1. 无头模式**
- 自动启用无头浏览器
- 无需图形界面
- 适合服务器环境

### **2. 验证处理**
- **手机号验证**: ✅ 自动处理
- **备用邮箱验证**: ✅ 自动处理
- **备用验证码验证**: ✅ 自动处理
- **YouTube验证**: ⚠️ 需要手动处理
- **通用验证**: ⚠️ 需要手动处理

### **3. 日志记录**
- 详细日志记录到文件
- 错误追踪和调试
- 性能监控

## 📱 **验证方式支持**

### **✅ 自动支持的验证方式**

#### **1. 手机号验证**
```bash
# 在登录时提供手机号
python tools/viggle_google_oauth_complete.py --server
# 输入: +86 13800138000
```

#### **2. 备用邮箱验证**
```bash
# 在登录时提供备用邮箱
python tools/viggle_google_oauth_complete.py --server
# 输入: backup@example.com
```

#### **3. 备用验证码验证**
```bash
# 在登录时提供备用验证码
python tools/viggle_google_oauth_complete.py --server
# 输入: 123456,789012,345678
```

### **⚠️ 需要手动处理的验证方式**

#### **1. YouTube验证**
- 服务器模式下无法自动处理
- 需要临时启用图形界面
- 或使用VNC远程桌面

#### **2. 通用验证**
- 某些复杂的验证方式
- 需要人工干预

## 🛠️ **服务器优化**

### **1. 性能优化**

```bash
# 设置环境变量
export PYTHONPATH=/opt/viggle
export DISPLAY=:99

# 启动虚拟显示
Xvfb :99 -screen 0 1366x768x24 &
```

### **2. 内存优化**

```bash
# 限制浏览器内存使用
export PLAYWRIGHT_BROWSERS_PATH=/tmp/playwright
export NODE_OPTIONS="--max-old-space-size=2048"
```

### **3. 网络优化**

```bash
# 设置代理 (如果需要)
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

# 设置超时
export PLAYWRIGHT_TIMEOUT=30000
```

## 🔄 **自动化部署**

### **1. 创建服务脚本**

```bash
# 创建服务文件
sudo vim /etc/systemd/system/viggle-oauth.service
```

```ini
[Unit]
Description=Viggle Google OAuth Service
After=network.target

[Service]
Type=simple
User=viggle
WorkingDirectory=/opt/viggle
Environment=PATH=/opt/viggle/viggle_env/bin
ExecStart=/opt/viggle/viggle_env/bin/python tools/viggle_google_oauth_complete.py --server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **2. 启动服务**

```bash
# 创建用户
sudo useradd -r -s /bin/false viggle
sudo chown -R viggle:viggle /opt/viggle

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable viggle-oauth
sudo systemctl start viggle-oauth

# 查看状态
sudo systemctl status viggle-oauth
```

### **3. 监控日志**

```bash
# 查看服务日志
sudo journalctl -u viggle-oauth -f

# 查看应用日志
tail -f /opt/viggle/logs/viggle_google_oauth.log
```

## 🔒 **安全配置**

### **1. 防火墙设置**

```bash
# 只允许必要端口
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### **2. 文件权限**

```bash
# 设置安全权限
sudo chmod 600 /opt/viggle/config/accounts.json
sudo chmod 700 /opt/viggle/secrets/
sudo chown -R viggle:viggle /opt/viggle
```

### **3. 定期更新**

```bash
# 创建更新脚本
vim /opt/viggle/update.sh
```

```bash
#!/bin/bash
cd /opt/viggle
git pull
source viggle_env/bin/activate
pip install -r requirements.txt
sudo systemctl restart viggle-oauth
```

## 📊 **监控和维护**

### **1. 健康检查**

```bash
# 检查服务状态
sudo systemctl status viggle-oauth

# 检查日志
tail -n 50 /opt/viggle/logs/viggle_google_oauth.log

# 检查磁盘空间
df -h

# 检查内存使用
free -h
```

### **2. 备份配置**

```bash
# 备份重要文件
tar -czf viggle_backup_$(date +%Y%m%d).tar.gz \
  config/accounts.json \
  secrets/ \
  logs/
```

### **3. 故障排除**

```bash
# 重启服务
sudo systemctl restart viggle-oauth

# 清理临时文件
rm -rf /tmp/playwright*

# 重新安装浏览器
playwright install chromium
```

## 🎯 **使用示例**

### **1. 首次登录**

```bash
# 进入项目目录
cd /opt/viggle

# 激活环境
source viggle_env/bin/activate

# 运行登录
python tools/viggle_google_oauth_complete.py --server

# 按提示输入信息
# Google邮箱: your_email@gmail.com
# Google密码: your_password
# 手机号: +86 13800138000
# 备用邮箱: backup@example.com
# 备用验证码: 123456,789012
```

### **2. 验证登录成功**

```bash
# 检查会话文件
ls -la secrets/

# 检查配置更新
cat config/accounts.json

# 运行批量处理
python tools/batch_processor.py
```

### **3. 监控处理**

```bash
# 查看任务状态
python tools/task_monitor.py stats

# 查看日志
tail -f logs/viggle_google_oauth.log
```

## 🚀 **生产环境建议**

### **1. 高可用配置**
- 使用负载均衡器
- 多实例部署
- 自动故障转移

### **2. 监控告警**
- 设置CPU/内存告警
- 磁盘空间监控
- 服务状态检查

### **3. 日志管理**
- 使用ELK Stack
- 日志轮转
- 错误告警

现在您的服务器已经配置完成，可以开始使用Google OAuth登录Viggle进行批量处理了！🎉

