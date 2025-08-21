#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google OAuth登录工具
简化版，用于快速登录Google账号
"""

import asyncio
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleOAuthLogin:
    def __init__(self):
        self.config = self.load_config()
        
    def load_config(self):
        """加载配置"""
        config_file = Path("config/google_oauth_config.json")
        default_config = {
            "google": {
                "login_url": "https://accounts.google.com/signin",
                "oauth_url": "https://accounts.google.com/o/oauth2/auth",
                "consent_url": "https://accounts.google.com/signin/oauth/consent"
            },
            "browser": {
                "headless": False,  # OAuth需要用户交互
                "slow_mo": 1000,
                "timeout": 30000,
                "viewport": {"width": 1366, "height": 768}
            },
            "oauth": {
                "client_id": "",  # 需要配置
                "redirect_uri": "http://localhost:8080/callback",
                "scope": "openid email profile",
                "response_type": "code"
            }
        }
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        else:
            # 创建默认配置
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"创建默认配置文件: {config_file}")
        
        return default_config
    
    async def login_with_google(self, email: str, password: str, save_session: bool = True):
        """使用Google账号登录"""
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=self.config["browser"]["headless"],
                slow_mo=self.config["browser"]["slow_mo"]
            )
            
            # 创建上下文
            context = await browser.new_context(
                viewport=self.config["browser"]["viewport"]
            )
            
            page = await context.new_page()
            
            try:
                logger.info("🚀 开始Google登录流程...")
                
                # 1. 访问Google登录页面
                await page.goto(self.config["google"]["login_url"])
                logger.info("📱 已打开Google登录页面")
                
                # 2. 输入邮箱
                await page.wait_for_selector('input[type="email"]', timeout=10000)
                await page.fill('input[type="email"]', email)
                await page.click('button[type="submit"]')
                logger.info(f"📧 已输入邮箱: {email}")
                
                # 等待页面跳转
                await page.wait_for_timeout(2000)
                
                # 3. 输入密码
                try:
                    await page.wait_for_selector('input[type="password"]', timeout=10000)
                    await page.fill('input[type="password"]', password)
                    await page.click('button[type="submit"]')
                    logger.info("🔐 已输入密码")
                except Exception as e:
                    logger.warning(f"密码输入异常: {e}")
                    logger.info("⚠️ 可能需要手动输入密码...")
                
                # 等待登录完成
                await page.wait_for_timeout(3000)
                
                # 4. 处理安全验证
                await self.handle_security_verification(page)
                
                # 5. 验证登录成功
                if await self.verify_login_success(page):
                    logger.info("✅ Google登录成功！")
                    
                    # 保存会话状态
                    if save_session:
                        await self.save_session_state(context, email)
                    
                    # 等待用户确认
                    input("按回车键继续...")
                    return True
                else:
                    logger.error("❌ Google登录失败")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ 登录过程异常: {str(e)}")
                return False
            finally:
                await browser.close()
    
    async def handle_security_verification(self, page: Page):
        """处理安全验证"""
        try:
            # 检查各种安全验证页面
            security_checks = [
                "text=Verify it's you",
                "text=Security check", 
                "text=Unusual activity",
                "text=Recovery email",
                "text=Phone number",
                "text=2-Step Verification"
            ]
            
            for check in security_checks:
                try:
                    if await page.locator(check).is_visible():
                        logger.warning(f"🔒 检测到安全验证: {check}")
                        logger.info("⚠️ 需要手动完成安全验证...")
                        input("完成验证后按回车继续...")
                        await page.wait_for_timeout(2000)
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"安全验证处理异常: {str(e)}")
    
    async def verify_login_success(self, page: Page) -> bool:
        """验证登录是否成功"""
        try:
            await page.wait_for_timeout(3000)
            
            # 检查登录成功的标志
            success_indicators = [
                "https://myaccount.google.com/",
                "https://accounts.google.com/ServiceLogin",
                "https://www.google.com/",
                "https://viggle.ai/"
            ]
            
            current_url = page.url
            for indicator in success_indicators:
                if indicator in current_url:
                    return True
            
            # 检查页面元素
            try:
                if await page.locator('text=Welcome').is_visible():
                    return True
                if await page.locator('text=My Account').is_visible():
                    return True
            except:
                pass
                
            return False
            
        except Exception as e:
            logger.error(f"登录验证异常: {str(e)}")
            return False
    
    async def save_session_state(self, context, email: str):
        """保存会话状态"""
        try:
            # 创建secrets目录
            secrets_dir = Path("secrets")
            secrets_dir.mkdir(exist_ok=True)
            
            # 保存会话状态
            session_file = secrets_dir / f"google_session_{email.replace('@', '_').replace('.', '_')}.json"
            await context.storage_state(path=str(session_file))
            logger.info(f"✅ 会话状态已保存: {session_file}")
            
            # 更新账号配置
            self.update_account_config(email, str(session_file))
            
        except Exception as e:
            logger.error(f"保存会话状态失败: {str(e)}")
    
    def update_account_config(self, email: str, session_path: str):
        """更新账号配置"""
        try:
            accounts_file = Path("config/accounts.json")
            if accounts_file.exists():
                with open(accounts_file, 'r', encoding='utf-8') as f:
                    accounts_config = json.load(f)
                
                # 更新账号的storage_state_path
                for account in accounts_config.get("accounts", []):
                    if account.get("email") == email:
                        account["storage_state_path"] = session_path
                        break
                
                with open(accounts_file, 'w', encoding='utf-8') as f:
                    json.dump(accounts_config, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ 已更新账号配置: {email}")
                
        except Exception as e:
            logger.error(f"更新账号配置失败: {str(e)}")

async def main():
    """主函数"""
    print("🔐 Google OAuth登录工具")
    print("=" * 50)
    
    # 获取用户输入
    email = input("请输入Google邮箱: ").strip()
    password = input("请输入密码: ").strip()
    
    if not email or not password:
        print("❌ 邮箱和密码不能为空")
        return
    
    # 创建登录器
    login_tool = GoogleOAuthLogin()
    
    # 执行登录
    success = await login_tool.login_with_google(email, password)
    
    if success:
        print("🎉 Google登录成功！现在可以用于Viggle自动化了。")
    else:
        print("❌ Google登录失败，请检查账号信息。")

if __name__ == "__main__":
    asyncio.run(main())

