# Google OAuth + Playwright 完整指南

## 🎯 概述

本指南介绍如何在Playwright自动化项目中使用Google OAuth认证，特别针对Viggle等需要Google账号登录的应用。

## 📋 目录

1. [OAuth基础概念](#oauth基础概念)
2. [Google Cloud Console配置](#google-cloud-console配置)
3. [Playwright OAuth实现](#playwright-oauth实现)
4. [实际应用示例](#实际应用示例)
5. [常见问题解决](#常见问题解决)

## 🔑 OAuth基础概念

### 什么是OAuth 2.0？

OAuth 2.0是一个授权框架，允许第三方应用在不需要用户密码的情况下访问用户资源。

### OAuth流程

1. **授权请求**: 用户访问应用，应用重定向到Google
2. **用户授权**: 用户在Google页面登录并授权
3. **授权码返回**: Google返回授权码给应用
4. **令牌交换**: 应用用授权码换取访问令牌
5. **API访问**: 应用使用访问令牌调用Google API

## 🌐 Google Cloud Console配置

### 步骤1: 创建项目

1. 访问 [Google Cloud Console](https://console.developers.google.com/)
2. 点击"创建项目"或选择现有项目
3. 输入项目名称，点击"创建"

### 步骤2: 启用API

1. 在左侧菜单中选择"API和服务" > "库"
2. 搜索并启用以下API：
   - Google+ API
   - Google OAuth2 API
   - Google Identity and Access Management (IAM) API

### 步骤3: 创建OAuth凭据

1. 进入"API和服务" > "凭据"
2. 点击"创建凭据" > "OAuth 2.0客户端ID"
3. 选择应用类型：**Web应用**
4. 配置授权重定向URI：
   ```
   http://localhost:8080/callback
   ```
5. 保存Client ID和Client Secret

### 步骤4: 配置授权域名

1. 在OAuth同意屏幕中添加授权域名：
   - `localhost`
   - `127.0.0.1`

## 🎭 Playwright OAuth实现

### 方案1: 直接OAuth流程

```python
import asyncio
from playwright.async_api import async_playwright
import urllib.parse

class GoogleOAuthHandler:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = "http://localhost:8080/callback"
    
    def build_oauth_url(self):
        """构建OAuth URL"""
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"
    
    async def perform_oauth_flow(self, page):
        """执行OAuth流程"""
        # 1. 导航到OAuth页面
        oauth_url = self.build_oauth_url()
        await page.goto(oauth_url)
        
        # 2. 等待用户完成认证
        print("请在浏览器中完成Google认证...")
        input("完成后按回车继续...")
        
        # 3. 获取授权码
        auth_code = await self.extract_auth_code(page)
        return auth_code
    
    async def extract_auth_code(self, page):
        """从URL中提取授权码"""
        current_url = page.url
        if "code=" in current_url:
            parsed = urllib.parse.urlparse(current_url)
            params = urllib.parse.parse_qs(parsed.query)
            return params.get('code', [None])[0]
        return None
```

### 方案2: 集成到现有登录流程

```python
async def login_viggle_with_google(page):
    """使用Google账号登录Viggle"""
    
    # 1. 导航到Viggle登录页面
    await page.goto("https://viggle.ai/login")
    
    # 2. 查找Google登录按钮
    google_button = page.locator("button:has-text('Google')")
    await google_button.click()
    
    # 3. 处理Google OAuth重定向
    await page.wait_for_url("**/accounts.google.com/**")
    
    # 4. 等待用户完成Google登录
    print("请在浏览器中完成Google登录...")
    input("完成后按回车继续...")
    
    # 5. 等待重定向回Viggle
    await page.wait_for_url("**/viggle.ai/**")
    
    # 6. 验证登录成功
    return await verify_login_success(page)
```

## 🚀 实际应用示例

### 完整的工作流程

```python
#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 1. 使用Google OAuth登录
            success = await login_with_google_oauth(page)
            
            if success:
                # 2. 保存会话状态
                await context.storage_state(path="google_oauth_session.json")
                print("✅ 登录成功，会话已保存")
                
                # 3. 继续其他自动化操作
                await perform_automation_tasks(page)
            else:
                print("❌ 登录失败")
                
        finally:
            await browser.close()

async def login_with_google_oauth(page):
    """Google OAuth登录流程"""
    
    # 配置OAuth参数
    client_id = "your-client-id.apps.googleusercontent.com"
    redirect_uri = "http://localhost:8080/callback"
    
    # 构建OAuth URL
    oauth_url = f"https://accounts.google.com/o/oauth2/auth?" \
                f"client_id={client_id}&" \
                f"redirect_uri={redirect_uri}&" \
                f"scope=openid%20email%20profile&" \
                f"response_type=code&" \
                f"access_type=offline"
    
    # 导航到OAuth页面
    await page.goto(oauth_url)
    
    # 等待用户完成认证
    print("🔑 请在浏览器中完成Google认证:")
    print("1. 登录Google账号")
    print("2. 授权应用访问")
    print("3. 等待重定向完成")
    
    # 等待重定向到回调页面
    await page.wait_for_url("**/localhost:8080/callback**", timeout=300000)
    
    # 检查是否成功
    if "code=" in page.url:
        print("✅ 成功获取授权码")
        return True
    else:
        print("❌ 认证失败")
        return False

async def perform_automation_tasks(page):
    """执行自动化任务"""
    print("🤖 开始执行自动化任务...")
    
    # 这里可以添加具体的自动化逻辑
    # 例如：访问Viggle应用，上传视频等
    
    await page.wait_for_timeout(5000)
    print("✅ 自动化任务完成")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 配置文件示例

### Google OAuth配置

```json
{
  "oauth": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "client_secret": "your-client-secret",
    "redirect_uri": "http://localhost:8080/callback",
    "scope": "openid email profile",
    "auth_url": "https://accounts.google.com/o/oauth2/auth",
    "token_url": "https://oauth2.googleapis.com/token"
  },
  "browser": {
    "headless": false,
    "slow_mo": 1000,
    "timeout": 30000
  },
  "security": {
    "enable_2fa": true,
    "backup_codes": ["code1", "code2", "code3"]
  }
}
```

### 账号配置

```json
[
  {
    "email": "user1@gmail.com",
    "password": "password123",
    "recovery_email": "recovery@example.com",
    "phone": "+1234567890",
    "storage_state_path": "secrets/user1_session.json",
    "daily_limit": 30,
    "notes": "主账号"
  }
]
```

## ⚠️ 常见问题解决

### 1. OAuth错误: redirect_uri_mismatch

**问题**: 重定向URI不匹配

**解决方案**:
- 检查Google Cloud Console中的授权重定向URI
- 确保与代码中的redirect_uri完全一致
- 包括协议、域名、端口和路径

### 2. 授权码过期

**问题**: 授权码只能使用一次，且有时效性

**解决方案**:
- 每次需要新的授权码时重新执行OAuth流程
- 使用refresh_token自动刷新访问令牌
- 保存会话状态避免重复认证

### 3. 2FA验证问题

**问题**: 双因素认证导致自动化失败

**解决方案**:
```python
async def handle_2fa(page):
    """处理双因素认证"""
    if await page.locator('text=2-Step Verification').is_visible():
        print("🔐 检测到2FA验证")
        
        # 使用备用码
        backup_code = "your-backup-code"
        await page.fill('input[type="text"]', backup_code)
        await page.click('button[type="submit"]')
        
        # 或者让用户手动完成
        input("请手动完成2FA验证后按回车...")
```

### 4. 会话状态管理

**问题**: 登录状态丢失

**解决方案**:
```python
# 保存会话状态
await context.storage_state(path="session.json")

# 恢复会话状态
context = await browser.new_context(storage_state="session.json")
```

## 🛡️ 安全最佳实践

### 1. 凭据管理

- 不要在代码中硬编码Client Secret
- 使用环境变量或配置文件
- 定期轮换Client Secret

### 2. 错误处理

```python
try:
    await perform_oauth_flow(page)
except Exception as e:
    logger.error(f"OAuth流程失败: {str(e)}")
    # 实现重试逻辑
    await retry_oauth_flow(page)
```

### 3. 速率限制

```python
import asyncio
from asyncio_throttle import Throttler

throttler = Throttler(rate_limit=10, period=60)  # 每分钟10次

async def throttled_oauth_request():
    async with throttler:
        # 执行OAuth请求
        pass
```

## 📚 相关资源

- [Google OAuth 2.0文档](https://developers.google.com/identity/protocols/oauth2)
- [Playwright官方文档](https://playwright.dev/)
- [Google Cloud Console](https://console.developers.google.com/)

## 🎯 总结

通过本指南，您可以：

1. ✅ 在Google Cloud Console中正确配置OAuth
2. ✅ 在Playwright中实现OAuth认证流程
3. ✅ 处理各种认证场景和错误情况
4. ✅ 安全地管理凭据和会话状态
5. ✅ 将OAuth集成到现有的自动化项目中

记住：OAuth认证需要用户交互，因此建议在开发阶段使用有头浏览器模式，生产环境可以考虑使用会话状态管理来减少重复认证。
