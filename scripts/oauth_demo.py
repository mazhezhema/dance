#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google OAuth + Playwright 简化演示
展示如何在Playwright中使用Google OAuth认证
"""

import asyncio
import urllib.parse
from playwright.async_api import async_playwright
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleOAuthDemo:
    """Google OAuth演示类"""
    
    def __init__(self):
        # OAuth配置 - 您需要替换为自己的Client ID
        self.client_id = "your-client-id.apps.googleusercontent.com"  # 替换为您的Client ID
        self.redirect_uri = "http://localhost:8080/callback"
        self.scope = "openid email profile"
    
    def build_oauth_url(self):
        """构建OAuth URL"""
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"
    
    async def perform_oauth_flow(self, page):
        """执行OAuth认证流程"""
        try:
            # 1. 构建OAuth URL
            oauth_url = self.build_oauth_url()
            logger.info(f"OAuth URL: {oauth_url}")
            
            # 2. 导航到Google OAuth页面
            logger.info("🌐 导航到Google OAuth页面...")
            await page.goto(oauth_url, wait_until="domcontentloaded")
            
            # 3. 等待用户完成认证
            print("\n📋 请在浏览器中完成Google认证:")
            print("1. 登录Google账号")
            print("2. 授权应用访问")
            print("3. 等待重定向完成")
            print()
            
            # 4. 等待重定向到回调页面
            logger.info("⏳ 等待OAuth回调...")
            await page.wait_for_url("**/localhost:8080/callback**", timeout=300000)
            
            # 5. 检查是否成功获取授权码
            current_url = page.url
            if "code=" in current_url:
                # 解析授权码
                parsed_url = urllib.parse.urlparse(current_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                auth_code = query_params.get('code', [None])[0]
                
                if auth_code:
                    logger.info(f"✅ 成功获取授权码: {auth_code[:20]}...")
                    return auth_code
                else:
                    logger.error("❌ 未找到授权码")
                    return None
            else:
                logger.error("❌ 认证失败，未获取到授权码")
                return None
                
        except Exception as e:
            logger.error(f"OAuth流程异常: {str(e)}")
            return None
    
    async def login_viggle_with_google(self, page):
        """使用Google账号登录Viggle（演示）"""
        try:
            logger.info("🚀 开始使用Google账号登录Viggle")
            
            # 1. 导航到Viggle登录页面
            await page.goto("https://viggle.ai/login", wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # 2. 查找Google登录按钮
            google_selectors = [
                "button[data-provider='google']",
                "button:has-text('Google')",
                "button:has-text('Sign in with Google')",
                "[data-testid='google-login-button']",
                "a[href*='google']"
            ]
            
            google_button = None
            for selector in google_selectors:
                try:
                    button = page.locator(selector).first
                    if await button.is_visible():
                        google_button = button
                        break
                except:
                    continue
            
            if not google_button:
                logger.warning("⚠️ 未找到Google登录按钮，可能需要手动操作")
                print("请在浏览器中手动点击Google登录按钮...")
                input("完成后按回车继续...")
            else:
                # 3. 点击Google登录按钮
                logger.info("🔘 点击Google登录按钮")
                await google_button.click()
                await page.wait_for_timeout(3000)
            
            # 4. 处理Google OAuth重定向
            logger.info("🔄 处理Google OAuth重定向...")
            await page.wait_for_url("**/accounts.google.com/**", timeout=10000)
            
            # 5. 等待用户完成Google登录
            print("请在浏览器中完成Google登录...")
            input("登录完成后按回车继续...")
            
            # 6. 等待重定向回Viggle
            logger.info("⏳ 等待重定向回Viggle...")
            await page.wait_for_url("**/viggle.ai/**", timeout=30000)
            
            # 7. 验证登录成功
            if await self.verify_login_success(page):
                logger.info("🎉 成功使用Google账号登录Viggle")
                return True
            else:
                logger.error("❌ Viggle登录验证失败")
                return False
                
        except Exception as e:
            logger.error(f"Google登录Viggle失败: {str(e)}")
            return False
    
    async def verify_login_success(self, page):
        """验证登录是否成功"""
        try:
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
    
    async def run_demo(self):
        """运行演示"""
        print("🔑 Google OAuth + Playwright 演示")
        print("=" * 50)
        
        # 检查OAuth配置
        if self.client_id == "your-client-id.apps.googleusercontent.com":
            print("⚠️ 请先配置Google OAuth Client ID")
            print("1. 访问 https://console.developers.google.com/")
            print("2. 创建OAuth 2.0客户端ID")
            print("3. 更新脚本中的client_id")
            print()
            return
        
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
                print("选择演示模式:")
                print("1. 纯OAuth流程")
                print("2. Viggle + Google OAuth集成")
                
                choice = input("\n请选择 (1 或 2): ").strip()
                
                if choice == "1":
                    # 纯OAuth流程
                    auth_code = await self.perform_oauth_flow(page)
                    if auth_code:
                        print("🎉 OAuth认证成功！")
                        print(f"授权码: {auth_code[:20]}...")
                    else:
                        print("❌ OAuth认证失败")
                        
                elif choice == "2":
                    # Viggle + Google OAuth集成
                    success = await self.login_viggle_with_google(page)
                    if success:
                        print("🎉 演示成功！")
                        
                        # 保存会话状态
                        session_file = "secrets/viggle_google_oauth_demo.json"
                        await context.storage_state(path=session_file)
                        print(f"💾 会话状态已保存: {session_file}")
                    else:
                        print("❌ 演示失败")
                else:
                    print("❌ 无效选择")
                    
            except Exception as e:
                print(f"❌ 演示异常: {str(e)}")
            finally:
                await browser.close()

async def main():
    """主函数"""
    demo = GoogleOAuthDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
