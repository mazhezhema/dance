#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google OAuth回调服务器
处理OAuth认证流程中的回调
"""

import asyncio
import json
import urllib.parse
from pathlib import Path
from aiohttp import web, ClientSession
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OAuthServer:
    """OAuth回调服务器"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = web.Application()
        self.auth_code = None
        self.setup_routes()
        
    def setup_routes(self):
        """设置路由"""
        self.app.router.add_get('/callback', self.handle_callback)
        self.app.router.add_get('/auth', self.handle_auth)
        self.app.router.add_get('/', self.handle_index)
        
    async def handle_index(self, request):
        """首页"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Google OAuth认证</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 600px; margin: 0 auto; }
                .btn { background: #4285f4; color: white; padding: 12px 24px; 
                       text-decoration: none; border-radius: 4px; display: inline-block; }
                .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
                .success { background: #d4edda; color: #155724; }
                .error { background: #f8d7da; color: #721c24; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔑 Google OAuth认证</h1>
                <p>点击下面的按钮开始Google OAuth认证流程：</p>
                <a href="/auth" class="btn">开始认证</a>
                <div id="status"></div>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def handle_auth(self, request):
        """处理认证请求"""
        # 从查询参数获取OAuth配置
        client_id = request.query.get('client_id', '')
        redirect_uri = request.query.get('redirect_uri', f'http://localhost:{self.port}/callback')
        scope = request.query.get('scope', 'openid email profile')
        
        if not client_id:
            return web.Response(
                text="❌ 缺少client_id参数",
                status=400
            )
        
        # 构建OAuth URL
        oauth_url = self.build_oauth_url(client_id, redirect_uri, scope)
        
        # 重定向到Google OAuth页面
        return web.HTTPFound(oauth_url)
    
    def build_oauth_url(self, client_id: str, redirect_uri: str, scope: str) -> str:
        """构建OAuth URL"""
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"
    
    async def handle_callback(self, request):
        """处理OAuth回调"""
        try:
            # 获取授权码
            code = request.query.get('code')
            error = request.query.get('error')
            
            if error:
                error_description = request.query.get('error_description', '未知错误')
                logger.error(f"OAuth错误: {error} - {error_description}")
                
                html = f"""
                <!DOCTYPE html>
                <html>
                <head><title>认证失败</title><meta charset="utf-8"></head>
                <body>
                    <div class="container">
                        <h1>❌ 认证失败</h1>
                        <div class="status error">
                            <strong>错误:</strong> {error}<br>
                            <strong>描述:</strong> {error_description}
                        </div>
                        <p><a href="/">返回首页</a></p>
                    </div>
                </body>
                </html>
                """
                return web.Response(text=html, content_type='text/html')
            
            if not code:
                return web.Response(
                    text="❌ 缺少授权码",
                    status=400
                )
            
            # 保存授权码
            self.auth_code = code
            logger.info(f"收到授权码: {code}")
            
            # 显示成功页面
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>认证成功</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    .status {{ padding: 10px; margin: 10px 0; border-radius: 4px; }}
                    .success {{ background: #d4edda; color: #155724; }}
                    .code {{ background: #f8f9fa; padding: 10px; border-radius: 4px; 
                            font-family: monospace; word-break: break-all; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ 认证成功</h1>
                    <div class="status success">
                        已成功获取授权码，可以关闭此页面
                    </div>
                    <h3>授权码:</h3>
                    <div class="code">{code}</div>
                    <p><small>此授权码将用于获取访问令牌</small></p>
                </div>
            </body>
            </html>
            """
            
            return web.Response(text=html, content_type='text/html')
            
        except Exception as e:
            logger.error(f"处理回调异常: {str(e)}")
            return web.Response(
                text=f"❌ 处理回调失败: {str(e)}",
                status=500
            )
    
    async def exchange_token(self, client_id: str, client_secret: str, 
                           redirect_uri: str, code: str) -> dict:
        """交换访问令牌"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        async with ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    logger.info("成功获取访问令牌")
                    return token_data
                else:
                    error_text = await response.text()
                    logger.error(f"获取令牌失败: {error_text}")
                    raise Exception(f"Token exchange failed: {error_text}")
    
    async def get_user_info(self, access_token: str) -> dict:
        """获取用户信息"""
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with ClientSession() as session:
            async with session.get(userinfo_url, headers=headers) as response:
                if response.status == 200:
                    user_data = await response.json()
                    logger.info(f"获取用户信息: {user_data.get('email')}")
                    return user_data
                else:
                    error_text = await response.text()
                    logger.error(f"获取用户信息失败: {error_text}")
                    raise Exception(f"Failed to get user info: {error_text}")
    
    async def start_server(self):
        """启动服务器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        logger.info(f"🚀 OAuth服务器已启动: http://localhost:{self.port}")
        return runner
    
    async def stop_server(self, runner):
        """停止服务器"""
        await runner.cleanup()
        logger.info("🛑 OAuth服务器已停止")

async def main():
    """主函数 - 演示OAuth服务器"""
    server = OAuthServer()
    
    print("🔑 Google OAuth服务器")
    print("=" * 40)
    
    # 启动服务器
    runner = await server.start_server()
    
    try:
        # 等待用户操作
        print("服务器正在运行...")
        print("访问 http://localhost:8080 开始认证")
        print("按 Ctrl+C 停止服务器")
        
        # 保持服务器运行
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
    finally:
        await server.stop_server(runner)

if __name__ == "__main__":
    asyncio.run(main())
