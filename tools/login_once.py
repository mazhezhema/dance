#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle登录脚本 - 导出会话状态
只需要运行一次，手动登录后自动保存会话
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def login_and_save_session():
    """手动登录并保存会话状态"""
    
    # 确保目录存在
    secrets_dir = Path("secrets")
    secrets_dir.mkdir(exist_ok=True)
    
    print("🔑 Viggle会话导出工具")
    print("=" * 40)
    
    account_email = input("请输入账号邮箱: ").strip()
    if not account_email:
        print("❌ 邮箱不能为空")
        return
    
    # 生成会话文件名
    session_file = secrets_dir / f"{account_email.replace('@', '_').replace('.', '_')}_state.json"
    
    async with async_playwright() as p:
        # 启动有头浏览器（必须显示，方便手动操作）
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000,  # 慢速操作，便于观察
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        print("🌐 正在打开Viggle登录页面...")
        await page.goto("https://viggle.ai/login")
        
        print("\n📋 请按以下步骤操作：")
        print("1. 在打开的浏览器窗口中手动登录")
        print("2. 登录成功后，确保能看到dashboard或app页面")
        print("3. 然后回到这里按回车键继续")
        
        input("\n✋ 登录完成后，按回车键继续...")
        
        # 检查是否登录成功
        current_url = page.url
        print(f"📍 当前页面: {current_url}")
        
        if "login" in current_url.lower():
            print("❌ 似乎还没有登录成功，请重新运行脚本")
            await browser.close()
            return
        
        print("✅ 检测到登录成功！")
        
        # 导航到app页面确保会话完整
        try:
            print("🔄 导航到应用页面...")
            await page.goto("https://viggle.ai/app", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"⚠️ 导航警告: {str(e)}")
        
        # 保存会话状态
        print("💾 正在保存会话状态...")
        await context.storage_state(path=str(session_file))
        
        print(f"✅ 会话状态已保存: {session_file}")
        
        # 验证保存的会话
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                cookies_count = len(session_data.get('cookies', []))
                storage_count = len(session_data.get('origins', []))
                print(f"📊 保存了 {cookies_count} 个Cookie, {storage_count} 个存储项")
        except Exception as e:
            print(f"⚠️ 验证警告: {str(e)}")
        
        print("\n🎉 设置完成！")
        print("=" * 40)
        print("📝 接下来请：")
        print(f"1. 更新 config/accounts.json，添加账号配置：")
        print(f'   {{"email": "{account_email}", "storage_state_path": "{session_file}"}}')
        print("2. 运行主程序开始自动化处理")
        print("3. 如果会话过期，重新运行此脚本更新")
        
        await browser.close()

def create_accounts_config():
    """创建账号配置模板"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    accounts_file = config_dir / "accounts.json"
    
    if not accounts_file.exists():
        example_config = [
            {
                "email": "account1@example.com",
                "storage_state_path": "secrets/account1_example_com_state.json",
                "daily_limit": 30,
                "concurrent_limit": 3,
                "notes": "主账号"
            }
        ]
        
        with open(accounts_file, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=2, ensure_ascii=False)
        
        print(f"📄 创建了账号配置模板: {accounts_file}")
        print("请根据你的实际账号信息进行修改")

async def main():
    """主函数"""
    try:
        # 创建账号配置模板
        create_accounts_config()
        
        # 执行登录流程
        await login_and_save_session()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 操作已取消")
    except Exception as e:
        print(f"\n❌ 操作失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
