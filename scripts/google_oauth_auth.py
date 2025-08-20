#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google OAuth认证模块
支持Playwright自动化登录Google账号
"""

import asyncio
import json
import time
import random
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from playwright.async_api import async_playwright, BrowserContext, Page
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GoogleAccount:
    """Google账号配置"""
    email: str
    password: str
    recovery_email: Optional[str] = None
    phone: Optional[str] = None
    storage_state_path: Optional[str] = None

class GoogleOAuthAuth:
    """Google OAuth认证处理器"""
    
    def __init__(self, config_path: str = "config/google_oauth_config.json"):
        self.config = self.load_config(config_path)
        self.accounts = self.load_accounts()
        
    def load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        default_config = {
            "google": {
                "login_url": "https://accounts.google.com/signin",
                "oauth_url": "https://accounts.google.com/o/oauth2/auth",
                "consent_url": "https://accounts.google.com/signin/oauth/consent"
            },
            "browser": {
                "headless": False,  # OAuth需要用户交互，建议有头模式
                "slow_mo": 1000,
                "timeout": 30000,
                "viewport": {"width": 1366, "height": 768}
            },
            "oauth": {
                "client_id": "",  # 需要配置Google OAuth Client ID
                "redirect_uri": "http://localhost:8080/callback",
                "scope": "openid email profile",
                "response_type": "code"
            },
            "security": {
                "enable_2fa": True,
                "backup_codes": [],
                "trusted_devices": []
            }
        }
        
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        else:
            # 创建默认配置文件
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"创建默认配置文件: {config_path}")
        
        return default_config
    
    def load_accounts(self) -> Dict[str, GoogleAccount]:
        """加载账号配置"""
        accounts_file = Path("config/google_accounts.json")
        accounts = {}
        
        if accounts_file.exists():
            with open(accounts_file, 'r', encoding='utf-8') as f:
                accounts_data = json.load(f)
                for acc_data in accounts_data:
                    account = GoogleAccount(**acc_data)
                    accounts[account.email] = account
        else:
            # 创建示例账号配置
            self.create_accounts_template()
            
        return accounts
    
    def create_accounts_template(self):
        """创建账号配置模板"""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        template = [
            {
                "email": "your-email@gmail.com",
                "password": "your-password",
                "recovery_email": "recovery@example.com",
                "phone": "+1234567890",
                "storage_state_path": "secrets/google_account_state.json",
                "notes": "主Google账号"
            }
        ]
        
        with open(config_dir / "google_accounts.json", 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        logger.info("创建了Google账号配置模板: config/google_accounts.json")
    
    async def setup_oauth_client(self, page: Page):
        """设置OAuth客户端（需要手动配置）"""
        print("🔧 Google OAuth客户端设置")
        print("=" * 50)
        print("请按以下步骤配置Google OAuth:")
        print("1. 访问 https://console.developers.google.com/")
        print("2. 创建新项目或选择现有项目")
        print("3. 启用Google+ API和Google OAuth2 API")
        print("4. 创建OAuth 2.0客户端ID")
        print("5. 添加授权重定向URI: http://localhost:8080/callback")
        print("6. 将Client ID和Client Secret更新到配置文件中")
        print()
        
        client_id = input("请输入OAuth Client ID (或按回车跳过): ").strip()
        if client_id:
            self.config["oauth"]["client_id"] = client_id
            self.save_config()
            print("✅ OAuth Client ID已保存")
        else:
            print("⚠️ 跳过OAuth客户端配置，将使用标准Google登录")
    
    async def perform_google_login(self, page: Page, account: GoogleAccount) -> bool:
        """执行Google登录流程"""
        try:
            logger.info(f"开始Google登录: {account.email}")
            
            # 导航到Google登录页面
            await page.goto(self.config["google"]["login_url"], wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # 输入邮箱
            print(f"📧 输入邮箱: {account.email}")
            await page.fill('input[type="email"]', account.email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)
            
            # 输入密码
            print("🔒 输入密码...")
            await page.fill('input[type="password"]', account.password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            # 处理2FA验证
            if self.config["security"]["enable_2fa"]:
                await self.handle_2fa(page, account)
            
            # 处理安全验证
            await self.handle_security_checks(page, account)
            
            # 验证登录成功
            if await self.verify_login_success(page):
                logger.info(f"✅ Google登录成功: {account.email}")
                return True
            else:
                logger.error(f"❌ Google登录失败: {account.email}")
                return False
                
        except Exception as e:
            logger.error(f"Google登录异常: {str(e)}")
            return False
    
    async def handle_2fa(self, page: Page, account: GoogleAccount):
        """处理双因素认证"""
        try:
            # 检查是否需要2FA
            if await page.locator('text=2-Step Verification').is_visible():
                print("🔐 检测到2FA验证...")
                
                # 尝试使用备用码
                if hasattr(account, 'backup_codes') and account.backup_codes:
                    print("📱 使用备用码验证...")
                    backup_code = account.backup_codes[0]  # 使用第一个备用码
                    await page.fill('input[type="text"]', backup_code)
                    await page.click('button[type="submit"]')
                    await page.wait_for_timeout(2000)
                else:
                    print("📱 请手动完成2FA验证...")
                    input("完成2FA验证后按回车继续...")
                    
        except Exception as e:
            logger.warning(f"2FA处理异常: {str(e)}")
    
    async def handle_security_checks(self, page: Page, account: GoogleAccount):
        """处理安全验证"""
        try:
            # 检查各种安全验证页面
            security_checks = [
                "text=Verify it's you",
                "text=Security check",
                "text=Unusual activity",
                "text=Recovery email",
                "text=Phone number"
            ]
            
            for check in security_checks:
                if await page.locator(check).is_visible():
                    print(f"🔒 检测到安全验证: {check}")
                    
                    # 根据验证类型处理
                    if "Recovery email" in check and account.recovery_email:
                        await page.fill('input[type="email"]', account.recovery_email)
                        await page.click('button[type="submit"]')
                    elif "Phone number" in check and account.phone:
                        await page.fill('input[type="tel"]', account.phone)
                        await page.click('button[type="submit"]')
                    else:
                        print("⚠️ 需要手动完成安全验证...")
                        input("完成验证后按回车继续...")
                    
                    await page.wait_for_timeout(2000)
                    break
                    
        except Exception as e:
            logger.warning(f"安全验证处理异常: {str(e)}")
    
    async def verify_login_success(self, page: Page) -> bool:
        """验证登录是否成功"""
        try:
            # 等待页面加载完成
            await page.wait_for_timeout(3000)
            
            # 检查登录成功的标志
            success_indicators = [
                "https://myaccount.google.com/",
                "https://accounts.google.com/ServiceLogin",
                "https://www.google.com/",
                "https://viggle.ai/"  # 如果是要跳转到Viggle
            ]
            
            current_url = page.url
            for indicator in success_indicators:
                if indicator in current_url:
                    return True
            
            # 检查页面元素
            if await page.locator('text=Welcome').is_visible():
                return True
            if await page.locator('text=My Account').is_visible():
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"登录验证异常: {str(e)}")
            return False
    
    async def save_session_state(self, context: BrowserContext, account: GoogleAccount):
        """保存会话状态"""
        try:
            if account.storage_state_path:
                session_file = Path(account.storage_state_path)
                session_file.parent.mkdir(parents=True, exist_ok=True)
                
                await context.storage_state(path=str(session_file))
                logger.info(f"✅ 会话状态已保存: {session_file}")
                
                # 更新账号配置
                account.storage_state_path = str(session_file)
                self.save_accounts()
                
        except Exception as e:
            logger.error(f"保存会话状态失败: {str(e)}")
    
    def save_config(self):
        """保存配置"""
        config_file = Path("config/google_oauth_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def save_accounts(self):
        """保存账号配置"""
        accounts_file = Path("config/google_accounts.json")
        accounts_data = []
        
        for account in self.accounts.values():
            account_dict = {
                "email": account.email,
                "password": account.password,
                "recovery_email": account.recovery_email,
                "phone": account.phone,
                "storage_state_path": account.storage_state_path
            }
            accounts_data.append(account_dict)
        
        with open(accounts_file, 'w', encoding='utf-8') as f:
            json.dump(accounts_data, f, indent=2, ensure_ascii=False)
    
    async def login_and_save_session(self, email: str = None):
        """登录并保存会话状态"""
        if not email:
            email = input("请输入Google邮箱: ").strip()
        
        if email not in self.accounts:
            print(f"❌ 账号 {email} 未在配置中找到")
            return False
        
        account = self.accounts[email]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.config["browser"]["headless"],
                slow_mo=self.config["browser"]["slow_mo"],
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            
            context = await browser.new_context(
                viewport=self.config["browser"]["viewport"],
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # 执行登录
            if await self.perform_google_login(page, account):
                # 保存会话状态
                await self.save_session_state(context, account)
                await browser.close()
                return True
            else:
                await browser.close()
                return False
    
    async def create_oauth_url(self, client_id: str, redirect_uri: str, scope: str) -> str:
        """创建OAuth URL"""
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def handle_oauth_callback(self, code: str, client_id: str, client_secret: str, redirect_uri: str):
        """处理OAuth回调"""
        # 这里需要实现OAuth code交换access token的逻辑
        # 由于需要后端服务器，这里只提供框架
        print("🔄 处理OAuth回调...")
        print(f"Authorization Code: {code}")
        print("需要实现token交换逻辑")

async def main():
    """主函数 - 演示Google OAuth认证"""
    auth = GoogleOAuthAuth()
    
    print("🔑 Google OAuth认证工具")
    print("=" * 50)
    
    # 检查配置
    if not auth.accounts:
        print("❌ 未找到账号配置，请先配置Google账号")
        return
    
    # 选择账号
    print("可用的Google账号:")
    for i, email in enumerate(auth.accounts.keys(), 1):
        print(f"{i}. {email}")
    
    choice = input("\n请选择账号 (输入序号): ").strip()
    try:
        email = list(auth.accounts.keys())[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ 无效选择")
        return
    
    # 执行登录
    print(f"\n🚀 开始登录: {email}")
    success = await auth.login_and_save_session(email)
    
    if success:
        print("🎉 登录成功！会话状态已保存")
        print("现在可以在其他脚本中使用保存的会话状态")
    else:
        print("❌ 登录失败，请检查账号信息")

if __name__ == "__main__":
    asyncio.run(main())
