#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle 自动化设置向导
基于 engineering-memory 的用户体验最佳实践
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

def print_banner():
    """打印欢迎横幅"""
    print("🎭" + "=" * 58 + "🎭")
    print("    Viggle Playwright 自动化设置向导")
    print("    基于 engineering-memory 最佳实践")
    print("🎭" + "=" * 58 + "🎭")
    print()

def check_environment():
    """检查环境"""
    print("🔍 检查环境...")
    
    # 检查目录
    required_dirs = ["input/videos", "input/people", "output", "profiles", "logs", "temp"]
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 目录创建: {dir_path}")
    
    # 检查Python依赖
    try:
        import playwright
        print(f"✅ Playwright 已安装: {playwright.__version__}")
    except ImportError:
        print("❌ Playwright 未安装，请运行: pip install playwright")
        return False
    
    try:
        import asyncio
        print("✅ asyncio 支持正常")
    except ImportError:
        print("❌ Python 版本过低，需要 Python 3.7+")
        return False
    
    print("✅ 环境检查完成\n")
    return True

def setup_config():
    """设置配置文件"""
    print("⚙️ 配置 Viggle 账号...")
    
    accounts = []
    account_count = 1
    
    while True:
        print(f"\n--- 账号 {account_count} ---")
        
        email = input("请输入 Viggle 邮箱: ").strip()
        if not email:
            if account_count == 1:
                print("❌ 至少需要配置一个账号")
                continue
            else:
                break
        
        password = input("请输入 Viggle 密码: ").strip()
        if not password:
            print("❌ 密码不能为空")
            continue
        
        daily_limit = input("每日处理上限 (默认30): ").strip()
        try:
            daily_limit = int(daily_limit) if daily_limit else 30
        except:
            daily_limit = 30
        
        profile_dir = f"./profiles/account_{account_count}"
        
        account = {
            "email": email,
            "password": password,
            "daily_limit": daily_limit,
            "profile_dir": profile_dir
        }
        
        accounts.append(account)
        print(f"✅ 账号 {account_count} 配置完成")
        
        if input("\n是否添加更多账号? (y/N): ").strip().lower() != 'y':
            break
        
        account_count += 1
    
    # 生成配置文件
    config = {
        "accounts": accounts,
        "viggle": {
            "login_url": "https://viggle.ai/login",
            "app_url": "https://viggle.ai/app",
            "timeout": 300000
        },
        "processing": {
            "max_retries": 3,
            "timeout_minutes": 15,
            "parallel_accounts": min(len(accounts), 2)
        },
        "anti_detection": {
            "random_delays": True,
            "human_behavior": True,
            "session_persistence": True
        }
    }
    
    # 保存配置
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 配置文件已保存: config.json")
    print(f"✅ 配置了 {len(accounts)} 个账号")

def show_usage_guide():
    """显示使用指南"""
    print("\n📖 使用指南:")
    print("-" * 50)
    
    print("1️⃣ 准备素材:")
    print("   • 将原始视频放入: input/videos/")
    print("   • 将AI人像放入: input/people/")
    
    print("\n2️⃣ 运行处理:")
    print("   python scripts/viggle_playwright_enhanced.py")
    
    print("\n3️⃣ 查看结果:")
    print("   • 处理完成的视频在: output/")
    print("   • 日志文件在: logs/")
    
    print("\n4️⃣ 注意事项:")
    print("   • 首次运行会弹出浏览器窗口进行登录")
    print("   • 登录成功后会保存会话，后续自动登录")
    print("   • 建议先用少量视频测试")
    print("   • 遇到问题查看日志文件")

def show_file_structure():
    """显示文件结构"""
    print("\n📁 项目结构:")
    print("-" * 50)
    
    structure = """
dance/
├── input/                  # 输入文件夹
│   ├── videos/            # 放置原始视频 (*.mp4)
│   └── people/            # 放置AI人像 (*.jpg, *.png)
├── output/                # 输出文件夹 (处理完成的视频)
├── profiles/              # 浏览器配置文件夹
├── logs/                  # 日志文件夹
├── temp/                  # 临时文件夹
├── config.json           # 配置文件
└── scripts/
    └── viggle_playwright_enhanced.py  # 主程序
    """
    
    print(structure)

def main():
    """主函数"""
    print_banner()
    
    if not check_environment():
        print("❌ 环境检查失败，请先安装依赖")
        return
    
    setup_config()
    show_file_structure()
    show_usage_guide()
    
    print("\n🎉 设置完成！现在可以开始使用了")
    print("\n💡 提示: 将素材文件放入对应目录后，运行主程序即可开始批量处理")

if __name__ == "__main__":
    main()
