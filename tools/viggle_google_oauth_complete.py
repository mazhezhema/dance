#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的Google OAuth登录Viggle实现
支持多种验证方式：手机号、YouTube、备用邮箱等
适用于服务器版和桌面版
"""

import asyncio
import json
import time
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging
import subprocess
import platform

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/viggle_google_oauth.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class GoogleAccount:
    """Google账号配置"""
    email: str
    password: str
    phone: Optional[str] = None
    recovery_email: Optional[str] = None
    youtube_channel: Optional[str] = None
    backup_codes: List[str] = None

class ViggleGoogleOAuthComplete:
    """完整的Google OAuth登录Viggle实现"""
    
    def __init__(self, headless: bool = False, server_mode: bool = False):
        self.headless = headless
        self.server_mode = server_mode
        self.config = self.load_config()
        self.account = None
        
    def load_config(self) -> dict:
        """加载配置"""
        config_file = Path("config/viggle_google_oauth_config.json")
        default_config = {
            "viggle": {
                "login_url": "https://viggle.ai/login",
                "app_url": "https://viggle.ai/app",
                "base_url": "https://viggle.ai"
            },
            "google": {
                "login_url": "https://accounts.google.com/signin",
                "oauth_url": "https://accounts.google.com/o/oauth2/auth",
                "consent_url": "https://accounts.google.com/signin/oauth/consent"
            },
            "browser": {
                "headless": self.headless,
                "slow_mo": 1000,
                "timeout": 30000,
                "viewport": {"width": 1366, "height": 768},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            "oauth": {
                "client_id": "",
                "redirect_uri": "http://localhost:8080/callback",
                "scope": "openid email profile",
                "response_type": "code"
            },
            "verification": {
                "enable_phone": True,
                "enable_youtube": True,
                "enable_recovery_email": True,
                "enable_backup_codes": True,
                "max_retries": 3
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
    
    def check_system_requirements(self) -> bool:
        """检查系统要求"""
        logger.info("🔍 检查系统要求...")
        
        # 检查Python版本
        if sys.version_info < (3, 8):
            logger.error("❌ Python版本过低，需要3.8+")
            return False
        
        # 检查操作系统
        os_name = platform.system()
        logger.info(f"📱 操作系统: {os_name}")
        
        # 检查Playwright
        try:
            import playwright
            logger.info("✅ Playwright已安装")
        except ImportError:
            logger.error("❌ Playwright未安装，请运行: pip install playwright")
            return False
        
        # 检查浏览器
        try:
            result = subprocess.run(['playwright', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Playwright浏览器已安装")
            else:
                logger.warning("⚠️ 需要安装Playwright浏览器")
                logger.info("💡 运行: playwright install chromium")
        except Exception as e:
            logger.warning(f"⚠️ 检查浏览器时出错: {e}")
        
        # 检查网络连接
        try:
            import urllib.request
            urllib.request.urlopen('https://viggle.ai', timeout=10)
            logger.info("✅ 网络连接正常")
        except Exception as e:
            logger.error(f"❌ 网络连接失败: {e}")
            return False
        
        logger.info("✅ 系统要求检查通过")
        return True
    
    async def setup_browser(self) -> tuple:
        """设置浏览器"""
        try:
            playwright = await async_playwright().start()
            
            # 启动浏览器
            browser_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
            
            if self.server_mode:
                browser_args.extend([
                    '--headless',
                    '--disable-gpu',
                    '--remote-debugging-port=9222'
                ])
            
            browser = await playwright.chromium.launch(
                headless=self.config["browser"]["headless"],
                slow_mo=self.config["browser"]["slow_mo"],
                args=browser_args
            )
            
            # 创建上下文
            context = await browser.new_context(
                viewport=self.config["browser"]["viewport"],
                user_agent=self.config["browser"]["user_agent"],
                ignore_https_errors=True
            )
            
            page = await context.new_page()
            
            logger.info("✅ 浏览器设置完成")
            return playwright, browser, context, page
            
        except Exception as e:
            logger.error(f"❌ 浏览器设置失败: {e}")
            raise
    
    async def login_viggle_with_google(self, account: GoogleAccount) -> bool:
        """使用Google账号登录Viggle"""
        self.account = account
        
        if not self.check_system_requirements():
            return False
        
        playwright, browser, context, page = None, None, None, None
        
        try:
            # 设置浏览器
            playwright, browser, context, page = await self.setup_browser()
            
            logger.info("🚀 开始Viggle Google OAuth登录流程...")
            
            # 1. 访问Viggle登录页面
            await self.navigate_to_viggle_login(page)
            
            # 2. 点击Google登录按钮
            if not await self.click_google_login_button(page):
                return False
            
            # 3. 在Google页面登录
            if not await self.login_to_google(page):
                return False
            
            # 4. 处理Google安全验证
            if not await self.handle_google_verification(page):
                return False
            
            # 5. 等待跳转回Viggle
            await self.wait_for_viggle_redirect(page)
            
            # 6. 验证Viggle登录成功
            if await self.verify_viggle_login_success(page):
                logger.info("✅ Viggle Google OAuth登录成功！")
                
                # 保存会话状态
                await self.save_session_state(context)
                
                return True
            else:
                logger.error("❌ Viggle登录失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 登录过程异常: {str(e)}")
            return False
        finally:
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
    
    async def navigate_to_viggle_login(self, page: Page):
        """导航到Viggle登录页面"""
        try:
            viggle_login_url = self.config["viggle"]["login_url"]
            await page.goto(viggle_login_url, wait_until='networkidle')
            logger.info("📱 已打开Viggle登录页面")
            await page.wait_for_timeout(3000)
        except Exception as e:
            logger.error(f"❌ 访问Viggle登录页面失败: {e}")
            raise
    
    async def click_google_login_button(self, page: Page) -> bool:
        """点击Google登录按钮"""
        try:
            # Google登录按钮选择器
            google_selectors = [
                'button[data-provider="google"]',
                'button:has-text("Google")',
                'button:has-text("Sign in with Google")',
                'button:has-text("Continue with Google")',
                'button:has-text("使用Google登录")',
                '[data-testid="google-login"]',
                '.google-login-btn',
                'a[href*="google"]',
                'button[aria-label*="Google"]'
            ]
            
            for selector in google_selectors:
                try:
                    if await page.locator(selector).is_visible():
                        await page.click(selector)
                        logger.info(f"✅ 找到并点击Google登录按钮: {selector}")
                        await page.wait_for_timeout(3000)
                        return True
                except Exception as e:
                    continue
            
            # 如果自动查找失败，提示手动点击
            logger.warning("⚠️ 未找到Google登录按钮，需要手动点击")
            if not self.server_mode:
                input("请在浏览器中手动点击Google登录按钮，然后按回车继续...")
                await page.wait_for_timeout(3000)
                return True
            else:
                logger.error("❌ 服务器模式下无法手动操作")
                return False
                
        except Exception as e:
            logger.error(f"❌ 点击Google登录按钮失败: {e}")
            return False
    
    async def login_to_google(self, page: Page) -> bool:
        """在Google页面登录"""
        try:
            # 等待Google登录页面加载
            await page.wait_for_timeout(3000)
            
            # 输入邮箱
            try:
                await page.wait_for_selector('input[type="email"]', timeout=10000)
                await page.fill('input[type="email"]', self.account.email)
                await page.click('button[type="submit"]')
                logger.info(f"📧 已输入Google邮箱: {self.account.email}")
            except Exception as e:
                logger.warning(f"邮箱输入异常: {e}")
                if not self.server_mode:
                    input("请手动输入邮箱，然后按回车继续...")
            
            await page.wait_for_timeout(2000)
            
            # 输入密码
            try:
                await page.wait_for_selector('input[type="password"]', timeout=10000)
                await page.fill('input[type="password"]', self.account.password)
                await page.click('button[type="submit"]')
                logger.info("🔐 已输入Google密码")
            except Exception as e:
                logger.warning(f"密码输入异常: {e}")
                if not self.server_mode:
                    input("请手动输入密码，然后按回车继续...")
            
            await page.wait_for_timeout(3000)
            return True
            
        except Exception as e:
            logger.error(f"❌ Google登录失败: {e}")
            return False
    
    async def handle_google_verification(self, page: Page) -> bool:
        """处理Google安全验证"""
        try:
            max_retries = self.config["verification"]["max_retries"]
            
            for attempt in range(max_retries):
                logger.info(f"🔄 处理Google验证 (尝试 {attempt + 1}/{max_retries})")
                
                # 检查各种验证页面
                verification_handlers = [
                    self.handle_phone_verification,
                    self.handle_youtube_verification,
                    self.handle_recovery_email_verification,
                    self.handle_backup_codes_verification,
                    self.handle_generic_verification
                ]
                
                for handler in verification_handlers:
                    if await handler(page):
                        return True
                
                # 等待一段时间后重试
                if attempt < max_retries - 1:
                    await page.wait_for_timeout(5000)
            
            logger.error("❌ Google验证处理失败")
            return False
            
        except Exception as e:
            logger.error(f"❌ Google验证处理异常: {e}")
            return False
    
    async def handle_phone_verification(self, page: Page) -> bool:
        """处理手机号验证"""
        if not self.account.phone or not self.config["verification"]["enable_phone"]:
            return False
        
        try:
            phone_selectors = [
                "text=Phone number",
                "text=手机号码",
                "text=Enter your phone number",
                "input[type='tel']",
                "input[name='phone']"
            ]
            
            for selector in phone_selectors:
                try:
                    if await page.locator(selector).is_visible():
                        logger.info("📱 检测到手机号验证")
                        
                        if selector.startswith("input"):
                            await page.fill(selector, self.account.phone)
                        else:
                            # 查找输入框并填写
                            input_element = await page.locator("input[type='tel'], input[name='phone']").first
                            if input_element:
                                await input_element.fill(self.account.phone)
                        
                        # 点击提交按钮
                        submit_selectors = [
                            "button[type='submit']",
                            "button:has-text('Next')",
                            "button:has-text('Continue')",
                            "button:has-text('下一步')"
                        ]
                        
                        for submit_selector in submit_selectors:
                            try:
                                if await page.locator(submit_selector).is_visible():
                                    await page.click(submit_selector)
                                    logger.info("✅ 已提交手机号")
                                    await page.wait_for_timeout(3000)
                                    return True
                            except:
                                continue
                        
                        if not self.server_mode:
                            input("请手动完成手机号验证，然后按回车继续...")
                            return True
                        
                        break
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"手机号验证处理异常: {e}")
            return False
    
    async def handle_youtube_verification(self, page: Page) -> bool:
        """处理YouTube验证"""
        if not self.config["verification"]["enable_youtube"]:
            return False
        
        try:
            youtube_selectors = [
                "text=YouTube",
                "text=YouTube channel",
                "text=YouTube verification",
                "a[href*='youtube']"
            ]
            
            for selector in youtube_selectors:
                try:
                    if await page.locator(selector).is_visible():
                        logger.info("📺 检测到YouTube验证")
                        
                        if not self.server_mode:
                            input("请手动完成YouTube验证，然后按回车继续...")
                            await page.wait_for_timeout(3000)
                            return True
                        else:
                            logger.warning("⚠️ 服务器模式下无法处理YouTube验证")
                            return False
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"YouTube验证处理异常: {e}")
            return False
    
    async def handle_recovery_email_verification(self, page: Page) -> bool:
        """处理备用邮箱验证"""
        if not self.account.recovery_email or not self.config["verification"]["enable_recovery_email"]:
            return False
        
        try:
            recovery_selectors = [
                "text=Recovery email",
                "text=备用邮箱",
                "text=Enter your recovery email",
                "input[type='email']"
            ]
            
            for selector in recovery_selectors:
                try:
                    if await page.locator(selector).is_visible():
                        logger.info("📧 检测到备用邮箱验证")
                        
                        if selector.startswith("input"):
                            await page.fill(selector, self.account.recovery_email)
                        else:
                            # 查找邮箱输入框
                            email_input = await page.locator("input[type='email']").first
                            if email_input:
                                await email_input.fill(self.account.recovery_email)
                        
                        # 点击提交
                        submit_button = await page.locator("button[type='submit'], button:has-text('Next')").first
                        if submit_button:
                            await submit_button.click()
                            logger.info("✅ 已提交备用邮箱")
                            await page.wait_for_timeout(3000)
                            return True
                        
                        break
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"备用邮箱验证处理异常: {e}")
            return False
    
    async def handle_backup_codes_verification(self, page: Page) -> bool:
        """处理备用验证码验证"""
        if not self.account.backup_codes or not self.config["verification"]["enable_backup_codes"]:
            return False
        
        try:
            backup_selectors = [
                "text=Backup codes",
                "text=备用验证码",
                "text=Enter backup code",
                "input[type='text']"
            ]
            
            for selector in backup_selectors:
                try:
                    if await page.locator(selector).is_visible():
                        logger.info("🔢 检测到备用验证码验证")
                        
                        # 使用第一个备用验证码
                        backup_code = self.account.backup_codes[0]
                        
                        if selector.startswith("input"):
                            await page.fill(selector, backup_code)
                        else:
                            # 查找输入框
                            code_input = await page.locator("input[type='text']").first
                            if code_input:
                                await code_input.fill(backup_code)
                        
                        # 点击提交
                        submit_button = await page.locator("button[type='submit'], button:has-text('Next')").first
                        if submit_button:
                            await submit_button.click()
                            logger.info("✅ 已提交备用验证码")
                            await page.wait_for_timeout(3000)
                            return True
                        
                        break
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"备用验证码验证处理异常: {e}")
            return False
    
    async def handle_generic_verification(self, page: Page) -> bool:
        """处理通用验证"""
        try:
            generic_selectors = [
                "text=Verify it's you",
                "text=Security check",
                "text=Unusual activity",
                "text=2-Step Verification",
                "text=Enter your password"
            ]
            
            for selector in generic_selectors:
                try:
                    if await page.locator(selector).is_visible():
                        logger.warning(f"🔒 检测到通用验证: {selector}")
                        
                        if not self.server_mode:
                            input("请手动完成验证，然后按回车继续...")
                            await page.wait_for_timeout(3000)
                            return True
                        else:
                            logger.warning("⚠️ 服务器模式下无法处理通用验证")
                            return False
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"通用验证处理异常: {e}")
            return False
    
    async def wait_for_viggle_redirect(self, page: Page):
        """等待跳转回Viggle"""
        try:
            logger.info("⏳ 等待跳转回Viggle...")
            
            # 等待URL变化
            max_wait = 30  # 最多等待30秒
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                current_url = page.url
                if "viggle.ai" in current_url:
                    logger.info("✅ 已跳转回Viggle")
                    break
                await page.wait_for_timeout(1000)
            
            await page.wait_for_timeout(3000)
            
        except Exception as e:
            logger.warning(f"等待跳转异常: {e}")
    
    async def verify_viggle_login_success(self, page: Page) -> bool:
        """验证Viggle登录是否成功"""
        try:
            await page.wait_for_timeout(3000)
            
            # 检查Viggle登录成功的标志
            success_indicators = [
                "https://viggle.ai/app",
                "https://viggle.ai/dashboard",
                "https://viggle.ai/",
                "text=Welcome",
                "text=Dashboard",
                "text=Create",
                "text=Upload",
                "text=开始创作"
            ]
            
            current_url = page.url
            for indicator in success_indicators:
                if indicator in current_url or indicator.startswith("text="):
                    if indicator.startswith("text="):
                        try:
                            if await page.locator(indicator).is_visible():
                                return True
                        except:
                            continue
                    else:
                        return True
            
            # 检查页面元素
            try:
                if await page.locator('text=Welcome').is_visible():
                    return True
                if await page.locator('text=Dashboard').is_visible():
                    return True
                if await page.locator('text=Create').is_visible():
                    return True
            except:
                pass
                
            return False
            
        except Exception as e:
            logger.error(f"Viggle登录验证异常: {str(e)}")
            return False
    
    async def save_session_state(self, context):
        """保存会话状态"""
        try:
            # 创建secrets目录
            secrets_dir = Path("secrets")
            secrets_dir.mkdir(exist_ok=True)
            
            # 保存会话状态
            session_file = secrets_dir / f"viggle_google_session_{self.account.email.replace('@', '_').replace('.', '_')}.json"
            await context.storage_state(path=str(session_file))
            logger.info(f"✅ Viggle会话状态已保存: {session_file}")
            
            # 更新账号配置
            self.update_account_config(str(session_file))
            
        except Exception as e:
            logger.error(f"保存会话状态失败: {str(e)}")
    
    def update_account_config(self, session_path: str):
        """更新账号配置"""
        try:
            accounts_file = Path("config/accounts.json")
            if accounts_file.exists():
                with open(accounts_file, 'r', encoding='utf-8') as f:
                    accounts_config = json.load(f)
                
                # 更新账号的storage_state_path
                for account in accounts_config.get("accounts", []):
                    if account.get("email") == self.account.email:
                        account["storage_state_path"] = session_path
                        break
                
                with open(accounts_file, 'w', encoding='utf-8') as f:
                    json.dump(accounts_config, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ 已更新Viggle账号配置: {self.account.email}")
                
        except Exception as e:
            logger.error(f"更新账号配置失败: {str(e)}")

async def main():
    """主函数"""
    print("🔐 Viggle Google OAuth完整登录工具")
    print("=" * 60)
    
    # 检查命令行参数
    headless = "--headless" in sys.argv
    server_mode = "--server" in sys.argv
    
    if server_mode:
        print("🖥️ 服务器模式")
        headless = True
    
    # 获取用户输入
    print("\n📝 请输入Google账号信息:")
    email = input("Google邮箱: ").strip()
    password = input("Google密码: ").strip()
    
    if not email or not password:
        print("❌ 邮箱和密码不能为空")
        return
    
    # 可选信息
    phone = input("手机号 (可选): ").strip() or None
    recovery_email = input("备用邮箱 (可选): ").strip() or None
    youtube_channel = input("YouTube频道 (可选): ").strip() or None
    backup_codes_input = input("备用验证码 (用逗号分隔，可选): ").strip()
    backup_codes = [code.strip() for code in backup_codes_input.split(",")] if backup_codes_input else None
    
    # 创建账号对象
    account = GoogleAccount(
        email=email,
        password=password,
        phone=phone,
        recovery_email=recovery_email,
        youtube_channel=youtube_channel,
        backup_codes=backup_codes
    )
    
    # 创建登录器
    login_tool = ViggleGoogleOAuthComplete(headless=headless, server_mode=server_mode)
    
    # 执行登录
    success = await login_tool.login_viggle_with_google(account)
    
    if success:
        print("🎉 Viggle Google OAuth登录成功！")
        print("💡 现在可以开始批量处理: python tools/batch_processor.py")
    else:
        print("❌ Viggle登录失败，请检查账号信息和网络连接")

if __name__ == "__main__":
    asyncio.run(main())

