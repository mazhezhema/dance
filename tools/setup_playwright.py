#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright环境设置脚本
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8+，当前版本:", sys.version)
        return False
    print(f"✅ Python版本: {sys.version}")
    return True

def install_dependencies():
    """安装依赖"""
    print("\n📦 安装Python依赖...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_playwright.txt"
        ], check=True)
        print("✅ Python依赖安装完成")
    except subprocess.CalledProcessError:
        print("❌ Python依赖安装失败")
        return False
    
    return True

def install_playwright_browsers():
    """安装Playwright浏览器"""
    print("\n🌐 安装Playwright浏览器...")
    
    try:
        # 安装所有浏览器
        subprocess.run([
            sys.executable, "-m", "playwright", "install"
        ], check=True)
        print("✅ Playwright浏览器安装完成")
        
        # 安装系统依赖（Linux）
        if os.name == 'posix':
            subprocess.run([
                sys.executable, "-m", "playwright", "install-deps"
            ], check=True)
            print("✅ 系统依赖安装完成")
            
    except subprocess.CalledProcessError:
        print("❌ Playwright浏览器安装失败")
        return False
    
    return True

def create_project_structure():
    """创建项目结构"""
    print("\n📁 创建项目结构...")
    
    directories = [
        "source_videos",
        "target_people/dancers",
        "target_people/fitness", 
        "target_people/traditional",
        "target_people/children",
        "target_people/elderly",
        "output",
        "profiles/account1",
        "profiles/account2", 
        "profiles/account3",
        "logs",
        "temp",
        "screenshots"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}/")
    
    return True

def create_config_files():
    """创建配置文件"""
    print("\n⚙️ 创建配置文件...")
    
    # 复制配置模板
    if not os.path.exists("config_multi_account.json"):
        if os.path.exists("config_multi_account_example.json"):
            import shutil
            shutil.copy("config_multi_account_example.json", "config_multi_account.json")
            print("✅ 创建配置文件: config_multi_account.json")
        else:
            print("⚠️ 配置模板文件不存在")
    
    # 创建环境变量文件
    env_content = """# Viggle自动化环境变量

# 代理设置（可选）
# HTTP_PROXY=http://127.0.0.1:7890
# HTTPS_PROXY=http://127.0.0.1:7890

# 通知设置（可选）
# WEBHOOK_URL=https://hooks.slack.com/services/...

# 调试设置
DEBUG=false
HEADLESS=false

# 性能设置
MAX_CONCURRENT_ACCOUNTS=2
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print("✅ 创建环境配置: .env")
    
    return True

def create_example_files():
    """创建示例文件"""
    print("\n📄 创建示例文件...")
    
    # README文件
    readme_content = """# Playwright多账号Viggle自动化

## 🚀 快速开始

### 1. 环境设置
```bash
python setup_playwright.py
```

### 2. 配置账号
编辑 `config_multi_account.json`，填入你的Viggle账号信息：
```json
{
  "accounts": [
    {
      "email": "your-email@example.com",
      "password": "your-password",
      "daily_limit": 25
    }
  ]
}
```

### 3. 准备素材
- 将视频文件放入 `source_videos/`
- 将目标人物图片放入 `target_people/` 相应分类

### 4. 运行处理
```bash
python viggle_playwright_multi_account.py
```

## 📁 目录结构

```
├── source_videos/          # 原始视频
├── target_people/          # 目标人物图片
│   ├── dancers/           # 舞蹈演员
│   ├── fitness/           # 健身教练
│   ├── traditional/       # 传统服装
│   ├── children/          # 儿童形象
│   └── elderly/           # 老年人形象
├── output/                # 处理结果
├── profiles/              # 浏览器配置文件
├── logs/                  # 日志文件
└── screenshots/           # 错误截图
```

## ⚠️ 重要提醒

1. **账号安全**: 使用专门的测试账号，不要用主账号
2. **频率控制**: 严格遵守每日限额，避免被封
3. **时间安排**: 建议凌晨或深夜运行，避开高峰期
4. **网络稳定**: 确保网络连接稳定
5. **监控日志**: 定期查看日志文件排查问题

## 🔧 故障排除

### 常见问题
- **登录失败**: 检查账号密码是否正确
- **上传失败**: 检查文件格式和大小
- **处理超时**: 降低batch_size或增加超时时间
- **验证码出现**: 程序会自动暂停，等待后重试

### 日志位置
- 主日志: `logs/viggle_multi_account.log`
- 错误截图: `screenshots/`
- 使用统计: `account_usage_stats.json`
"""
    
    with open("README_playwright.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("✅ 创建使用说明: README_playwright.md")
    
    # 创建目录说明文件
    dir_explanations = {
        "source_videos/README.txt": """将原始视频文件放在这里

支持格式：mp4, avi, mov, mkv, wmv
建议大小：不超过50MB
建议时长：10秒-5分钟

命名建议：
- dance_xxx.mp4 (舞蹈类)
- fitness_xxx.mp4 (健身类)  
- traditional_xxx.mp4 (传统类)
""",
        "target_people/README.txt": """将目标人物图片放在这里

要求：
- 格式：jpg, jpeg, png
- 分辨率：建议512x512以上
- 质量：清晰正面照，无遮挡
- 分类：按子文件夹分类存放

分类说明：
- dancers/ - 舞蹈演员形象
- fitness/ - 健身教练形象
- traditional/ - 传统服装形象
- children/ - 儿童形象
- elderly/ - 老年人形象
""",
        "output/README.txt": """处理完成的视频文件会保存在这里

文件命名格式：
viggle_mix_原始文件名_时间戳.mp4

注意：
- 文件会自动下载到这里
- 建议定期清理或备份
- 大文件可能影响硬盘空间
""",
        "profiles/README.txt": """浏览器配置文件存储

每个账号都有独立的配置文件夹：
- account1/ - 第一个账号的浏览器数据
- account2/ - 第二个账号的浏览器数据

包含内容：
- Cookie和登录状态
- 浏览器设置和偏好
- 本地存储数据

注意：请勿手动修改这些文件
""",
        "logs/README.txt": """日志文件存储

主要日志文件：
- viggle_multi_account.log - 主程序日志
- error_*.log - 错误日志
- account_usage_stats.json - 使用统计

日志级别：
- INFO: 正常操作信息
- WARNING: 警告信息  
- ERROR: 错误信息

建议定期清理过期日志文件
"""
    }
    
    for file_path, content in dir_explanations.items():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 创建说明: {file_path}")
    
    return True

def create_launch_scripts():
    """创建启动脚本"""
    print("\n🚀 创建启动脚本...")
    
    # Windows批处理文件
    batch_content = """@echo off
echo 🎭 Viggle多账号自动化处理器
echo ================================

REM 检查Python环境
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查配置文件
if not exist "config_multi_account.json" (
    echo ❌ 未找到配置文件，请先配置账号信息
    echo 💡 复制 config_multi_account_example.json 为 config_multi_account.json 并编辑
    pause
    exit /b 1
)

REM 运行程序
echo 🚀 启动自动化处理...
python viggle_playwright_multi_account.py

pause
"""
    
    with open("start_viggle.bat", "w", encoding="utf-8") as f:
        f.write(batch_content)
    print("✅ 创建Windows启动脚本: start_viggle.bat")
    
    # Linux/Mac shell脚本
    shell_content = """#!/bin/bash

echo "🎭 Viggle多账号自动化处理器"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查配置文件
if [ ! -f "config_multi_account.json" ]; then
    echo "❌ 未找到配置文件，请先配置账号信息"
    echo "💡 复制 config_multi_account_example.json 为 config_multi_account.json 并编辑"
    exit 1
fi

# 运行程序
echo "🚀 启动自动化处理..."
python3 viggle_playwright_multi_account.py
"""
    
    with open("start_viggle.sh", "w", encoding="utf-8") as f:
        f.write(shell_content)
    
    # 添加执行权限
    try:
        os.chmod("start_viggle.sh", 0o755)
    except:
        pass
    
    print("✅ 创建Linux/Mac启动脚本: start_viggle.sh")
    
    return True

def main():
    """主函数"""
    print("🎭 Playwright Viggle自动化环境设置")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return False
    
    # 安装依赖
    if not install_dependencies():
        return False
    
    # 安装Playwright浏览器
    if not install_playwright_browsers():
        return False
    
    # 创建项目结构
    if not create_project_structure():
        return False
    
    # 创建配置文件
    if not create_config_files():
        return False
    
    # 创建示例文件
    if not create_example_files():
        return False
    
    # 创建启动脚本
    if not create_launch_scripts():
        return False
    
    print("\n🎉 Playwright环境设置完成！")
    print("=" * 50)
    print("\n📋 下一步操作：")
    print("1. 编辑 config_multi_account.json 配置你的Viggle账号")
    print("2. 将视频文件放入 source_videos/ 目录")
    print("3. 将目标人物图片放入 target_people/ 相应分类")
    print("4. 运行 python viggle_playwright_multi_account.py")
    print("\n💡 提示：")
    print("- Windows用户可以双击 start_viggle.bat 启动")
    print("- Linux/Mac用户可以运行 ./start_viggle.sh 启动")
    print("- 查看 README_playwright.md 了解详细使用说明")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ 设置过程中出现错误，请检查并重试")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ 设置已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 设置失败: {str(e)}")
        sys.exit(1)
