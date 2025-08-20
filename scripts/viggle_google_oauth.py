#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle + Google OAuth集成
演示如何在Playwright中使用Google OAuth认证
"""

import asyncio
import json
import urllib.parse
from pathlib import Path
from typing import Optional, Dict
from playwright.async_api import async_playwright, BrowserContext, Page
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ViggleGoogleOAuth:
    """Viggle + Google OAuth集成处理器"""
    
    def __init__(self):
        self.config = self.load_config()
        self.oauth_config = self.load_oauth_config()
        
    def load_config(self) -> dict:
        """加载Viggle配置"""
        config_file = Path("config/viggle_config.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "viggle": {
                    "app_url": "https://viggle.ai/app",
                    "login_url": "https://viggle.ai/login"
                }
            }
    
    def load_oauth_config(self) -> dict:
        """加载OAuth配置"""
        oauth_file = Path("config/google_oauth_config.json")
        if oauth_file.exists():
            with open(oauth_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "oauth": {
                    "client_id": "",
                    "client_secret": "",
                    "redirect_uri": "http://localhost:8080/callback",
                    "scope": "openid email profile"
                }
            }
    
    async def setup_google_oauth(self, page: Page) -> bool:
        """设置Google OAuth认证"""
        try:
            logger.info("🔧 开始Google OAuth设置")
            
            # 检查是否已有OAuth配置
            if not self.oauth_config["oauth"]["client_id"]:
                await self.create_oauth_client(page)
            
            # 执行OAuth认证流程
            return await self.perform_oauth_flow(page)
            
        except Exception as e:
            logger.error(f"OAuth设置失败: {str(e)}")
            return False
    
    async def create_oauth_client(self, page: Page):
        """创建OAuth客户端（指导用户操作）"""
        print("🔧 Google OAuth客户端设置指南")
        print("=" * 50)
        print("请按以下步骤在Google Cloud Console创建OAuth客户端:")
        print()
        print("1. 访问: https://console.developers.google.com/")
        print("2. 创建新项目或选择现有项目")
        print("3. 启用以下API:")
        print("   - Google+ API")
        print("   - Google OAuth2 API")
        print("4. 在'凭据'页面创建OAuth 2.0客户端ID")
        print("5. 应用类型选择: Web应用")
        print("6. 授权重定向URI: http://localhost:8080/callback")
        print("7. 保存Client ID和Client Secret")
        print()
        
        client_id = input("请输入OAuth Client ID: ").strip()
        client_secret = input("请输入OAuth Client Secret: ").strip()
        
        if client_id and client_secret:
            self.oauth_config["oauth"]["client_id"] = client_id
            self.oauth_config["oauth"]["client_secret"] = client_secret
            self.save_oauth_config()
            print("✅ OAuth配置已保存")
        else:
            print("❌ OAuth配置不完整")
            raise Exception("OAuth配置不完整")
    
    async def perform_oauth_flow(self, page: Page) -> bool:
        """执行OAuth认证流程"""
        try:
            # 构建OAuth URL
            oauth_url = self.build_oauth_url()
            
            # 导航到OAuth页面
            logger.info("🌐 导航到Google OAuth页面")
            await page.goto(oauth_url, wait_until="domcontentloaded")
            
            # 等待用户完成认证
            print("📋 请在浏览器中完成Google认证:")
            print("1. 登录Google账号")
            print("2. 授权应用访问")
            print("3. 等待重定向到回调页面")
            print()
            
            # 监听页面变化
            auth_code = await self.wait_for_auth_code(page)
            
            if auth_code:
                logger.info("✅ 成功获取授权码")
                # 这里可以进一步处理token交换
                return True
            else:
                logger.error("❌ 未获取到授权码")
                return False
                
        except Exception as e:
            logger.error(f"OAuth流程异常: {str(e)}")
            return False
    
    def build_oauth_url(self) -> str:
        """构建OAuth URL"""
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "client_id": self.oauth_config["oauth"]["client_id"],
            "redirect_uri": self.oauth_config["oauth"]["redirect_uri"],
            "scope": self.oauth_config["oauth"]["scope"],
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"
    
    async def wait_for_auth_code(self, page: Page, timeout: int = 300) -> Optional[str]:
        """等待获取授权码"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            current_url = page.url
            
            # 检查是否到达回调页面
            if "localhost:8080/callback" in current_url:
                # 解析URL中的授权码
                parsed_url = urllib.parse.urlparse(current_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                
                if 'code' in query_params:
                    auth_code = query_params['code'][0]
                    logger.info(f"获取到授权码: {auth_code[:20]}...")
                    return auth_code
                elif 'error' in query_params:
                    error = query_params['error'][0]
                    logger.error(f"OAuth错误: {error}")
                    return None
            
            await asyncio.sleep(1)
        
        logger.error("等待授权码超时")
        return None
    
    async def login_viggle_with_google(self, page: Page) -> bool:
        """使用Google账号登录Viggle"""
        try:
            logger.info("🚀 开始使用Google账号登录Viggle")
            
            # 导航到Viggle登录页面
            await page.goto(self.config["viggle"]["login_url"], 
                          wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # 查找Google登录按钮
            google_login_selectors = [
                "button[data-provider='google']",
                "button:has-text('Google')",
                "button:has-text('Sign in with Google')",
                "[data-testid='google-login-button']",
                "a[href*='google']"
            ]
            
            google_button = None
            for selector in google_login_selectors:
                try:
                    google_button = page.locator(selector).first
                    if await google_button.is_visible():
                        break
                except:
                    continue
            
            if not google_button:
                logger.error("未找到Google登录按钮")
                return False
            
            # 点击Google登录按钮
            logger.info("🔘 点击Google登录按钮")
            await google_button.click()
            await page.wait_for_timeout(3000)
            
            # 处理Google OAuth流程
            return await self.handle_google_oauth_redirect(page)
            
        except Exception as e:
            logger.error(f"Google登录Viggle失败: {str(e)}")
            return False
    
    async def handle_google_oauth_redirect(self, page: Page) -> bool:
        """处理Google OAuth重定向"""
        try:
            # 等待重定向到Google OAuth页面
            await page.wait_for_url("**/accounts.google.com/**", timeout=10000)
            
            # 检查是否需要登录Google
            if await page.locator('input[type="email"]').is_visible():
                logger.info("📧 检测到Google登录页面")
                
                # 这里可以自动填写Google账号信息
                # 或者让用户手动完成
                print("请在浏览器中完成Google登录...")
                input("登录完成后按回车继续...")
            
            # 等待授权页面
            await page.wait_for_timeout(3000)
            
            # 检查授权页面
            if await page.locator('text=Allow').is_visible():
                logger.info("✅ 点击授权按钮")
                await page.click('text=Allow')
                await page.wait_for_timeout(3000)
            
            # 等待重定向回Viggle
            await page.wait_for_url("**/viggle.ai/**", timeout=30000)
            
            # 验证登录成功
            if await self.verify_viggle_login(page):
                logger.info("🎉 成功使用Google账号登录Viggle")
                return True
            else:
                logger.error("❌ Viggle登录验证失败")
                return False
                
        except Exception as e:
            logger.error(f"OAuth重定向处理失败: {str(e)}")
            return False
    
    async def verify_viggle_login(self, page: Page) -> bool:
        """验证Viggle登录状态"""
        try:
            # 等待页面加载
            await page.wait_for_timeout(3000)
            
            # 检查登录成功的标志
            success_indicators = [
                "https://viggle.ai/app",
                "text=Welcome",
                "text=Dashboard",
                "text=Logout",
                "[data-testid='user-menu']"
            ]
            
            for indicator in success_indicators:
                try:
                    if indicator.startswith("http"):
                        if indicator in page.url:
                            return True
                    else:
                        if await page.locator(indicator).is_visible():
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"登录验证异常: {str(e)}")
            return False
    
    def save_oauth_config(self):
        """保存OAuth配置"""
        config_file = Path("config/google_oauth_config.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.oauth_config, f, indent=2, ensure_ascii=False)
    
    async def run_demo(self):
        """运行演示"""
        print("🔑 Viggle + Google OAuth集成演示")
        print("=" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # 需要显示浏览器进行OAuth
                slow_mo=1000
            )
            
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768}
            )
            
            page = await context.new_page()
            
            try:
                # 使用Google账号登录Viggle
                success = await self.login_viggle_with_google(page)
                
                if success:
                    print("🎉 演示成功！")
                    print("现在可以在Viggle中使用Google账号了")
                    
                    # 保存会话状态
                    session_file = Path("secrets/viggle_google_oauth_state.json")
                    session_file.parent.mkdir(parents=True, exist_ok=True)
                    await context.storage_state(path=str(session_file))
                    print(f"💾 会话状态已保存: {session_file}")
                else:
                    print("❌ 演示失败")
                    
            except Exception as e:
                print(f"❌ 演示异常: {str(e)}")
            finally:
                await browser.close()

async def main():
    """主函数"""
    oauth_handler = ViggleGoogleOAuth()
    await oauth_handler.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
