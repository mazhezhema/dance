# Viggle网站自动化工具推荐

## RPA工具推荐

### 1. **UiPath (推荐指数: ⭐⭐⭐⭐⭐)**

#### 优势
- 🎯 专业级RPA平台，稳定性极高
- 🖱️ 可视化流程设计，无需编程
- 🛡️ 内置反检测机制
- 📊 完整的任务监控和报告
- 🔄 强大的错误处理和重试机制

#### Viggle自动化方案
```
UiPath Studio设计流程:
1. 打开浏览器 → 登录Viggle
2. 上传视频文件
3. 配置生成参数
4. 提交任务并监控进度
5. 下载完成的视频
6. 循环处理下一个文件
```

#### 成本
- **Community版**: 免费 (个人使用)
- **Pro版**: $420/月 (商业使用)

### 2. **Automation Anywhere (推荐指数: ⭐⭐⭐⭐)**

#### 优势
- ☁️ 云端RPA平台
- 🤖 AI驱动的智能识别
- 📱 支持多平台自动化
- 🔒 企业级安全和合规

#### 特色功能
- **IQ Bot**: AI识别网页元素
- **Bot Insight**: 实时任务监控
- **Control Room**: 集中管理和调度

### 3. **Power Automate (推荐指数: ⭐⭐⭐⭐)**

#### 优势
- 💼 微软生态系统集成
- 💰 相对经济的定价
- 🔗 与Office 365深度集成
- 📋 丰富的模板库

#### Viggle流程示例
```python
# Power Automate Desktop流程
1. 启动新Edge浏览器
2. 导航到viggle.ai
3. 执行登录操作
4. 上传视频循环:
   - 选择文件
   - 设置参数
   - 提交任务
   - 等待完成
   - 下载结果
```

## MCP工具推荐

### 1. **Browser Use MCP (推荐指数: ⭐⭐⭐⭐⭐)**

#### 特点
- 🎯 专为Claude设计的浏览器MCP
- 🧠 AI驱动的智能操作
- 🛡️ 内置反检测功能
- 🔄 支持复杂的工作流程

#### 安装和配置
```bash
# 安装Browser Use MCP
npm install @browser-use/mcp

# 配置Claude客户端
{
  "mcpServers": {
    "browser-use": {
      "command": "npx",
      "args": ["@browser-use/mcp"],
      "env": {
        "BROWSER_USE_API_KEY": "your-api-key"
      }
    }
  }
}
```

#### Viggle自动化示例
```python
# 使用Browser Use MCP
import asyncio
from browser_use import BrowserMCP

async def automate_viggle():
    mcp = BrowserMCP()
    
    # 启动浏览器会话
    session = await mcp.start_session()
    
    # 导航到Viggle
    await session.navigate("https://viggle.ai")
    
    # AI智能登录
    await session.smart_login(
        email="your-email@example.com",
        password="your-password"
    )
    
    # 批量处理视频
    video_files = ["video1.mp4", "video2.mp4", "video3.mp4"]
    
    for video in video_files:
        result = await session.process_video(
            video_path=video,
            character_prompt="dancing person",
            background="green screen"
        )
        
        await session.download_result(result.download_url)
    
    await session.close()
```

### 2. **Playwright MCP (推荐指数: ⭐⭐⭐⭐)**

#### 特点
- 🚀 高性能浏览器自动化
- 🌐 支持所有主流浏览器
- 📱 移动端和桌面端支持
- 🎭 强大的页面交互能力

#### 安装配置
```bash
# 安装Playwright MCP
pip install playwright-mcp

# 安装浏览器
playwright install
```

#### Viggle自动化实现
```python
# playwright_viggle_automation.py
from playwright.async_api import async_playwright
import asyncio
import json

class PlaywrightViggleBot:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        
    async def setup(self):
        """初始化Playwright"""
        self.playwright = await async_playwright().start()
        
        # 启动浏览器(反检测配置)
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # 可见模式
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # 创建上下文(模拟真实用户)
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await context.new_page()
        
        # 反检测脚本
        await self.page.add_init_script("""
            // 删除webdriver属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // 模拟真实的chrome
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // 模拟插件
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
    async def login_viggle(self, email, password):
        """登录Viggle"""
        await self.page.goto('https://viggle.ai')
        await self.page.wait_for_load_state('networkidle')
        
        # 智能等待登录按钮
        login_selectors = [
            'button:has-text("Sign In")',
            'button:has-text("Login")', 
            'a:has-text("Sign In")',
            '.login-button',
            '#login'
        ]
        
        for selector in login_selectors:
            try:
                await self.page.click(selector, timeout=3000)
                break
            except:
                continue
        
        # 等待登录表单
        await self.page.wait_for_selector('input[type="email"], input[name="email"]')
        
        # 输入凭据
        await self.page.fill('input[type="email"], input[name="email"]', email)
        await self.page.fill('input[type="password"], input[name="password"]', password)
        
        # 提交登录
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Sign In")',
            'button:has-text("Login")',
            '.submit-button'
        ]
        
        for selector in submit_selectors:
            try:
                await self.page.click(selector)
                break
            except:
                continue
        
        # 等待登录成功
        await self.page.wait_for_url('**/dashboard**', timeout=30000)
        print("✅ Viggle登录成功")
        
    async def upload_and_process_video(self, video_path, config):
        """上传并处理视频"""
        try:
            # 查找上传按钮
            upload_selectors = [
                'input[type="file"]',
                '.upload-button',
                'button:has-text("Upload")',
                '.file-upload'
            ]
            
            for selector in upload_selectors:
                try:
                    await self.page.set_input_files(selector, video_path)
                    print(f"✅ 视频上传成功: {video_path}")
                    break
                except:
                    continue
            
            # 等待上传完成
            await self.page.wait_for_selector('.upload-complete, .file-uploaded', timeout=60000)
            
            # 配置生成参数
            if config.get('character_image'):
                await self.page.set_input_files('.character-upload', config['character_image'])
            
            if config.get('prompt'):
                await self.page.fill('textarea, .prompt-input', config['prompt'])
            
            # 选择背景模式(绿幕)
            bg_selectors = [
                'button:has-text("Green")',
                '.green-screen',
                '[data-bg="green"]'
            ]
            
            for selector in bg_selectors:
                try:
                    await self.page.click(selector)
                    break
                except:
                    continue
            
            # 提交生成任务
            generate_selectors = [
                'button:has-text("Generate")',
                'button:has-text("Create")',
                '.generate-button',
                '.submit-task'
            ]
            
            for selector in generate_selectors:
                try:
                    await self.page.click(selector)
                    print("✅ 任务提交成功")
                    break
                except:
                    continue
            
            # 监控任务进度
            task_id = await self.monitor_task_progress()
            
            return task_id
            
        except Exception as e:
            print(f"❌ 处理视频失败: {str(e)}")
            return None
            
    async def monitor_task_progress(self, max_wait_minutes=30):
        """监控任务进度"""
        start_time = asyncio.get_event_loop().time()
        max_wait_seconds = max_wait_minutes * 60
        
        while (asyncio.get_event_loop().time() - start_time) < max_wait_seconds:
            try:
                # 检查任务状态
                status_selectors = [
                    '.task-status',
                    '.progress-indicator', 
                    '.generation-status'
                ]
                
                for selector in status_selectors:
                    try:
                        status_element = await self.page.query_selector(selector)
                        if status_element:
                            status_text = await status_element.inner_text()
                            print(f"📊 任务状态: {status_text}")
                            
                            if 'complete' in status_text.lower() or 'done' in status_text.lower():
                                return await self.download_result()
                            elif 'fail' in status_text.lower() or 'error' in status_text.lower():
                                print("❌ 任务失败")
                                return None
                    except:
                        continue
                
                # 等待30秒后重新检查
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"⚠️ 监控出错: {str(e)}")
                await asyncio.sleep(30)
        
        print("⏰ 任务超时")
        return None
        
    async def download_result(self):
        """下载结果视频"""
        try:
            download_selectors = [
                'a:has-text("Download")',
                '.download-button',
                '.result-download',
                'button:has-text("Save")'
            ]
            
            for selector in download_selectors:
                try:
                    async with self.page.expect_download() as download_info:
                        await self.page.click(selector)
                    
                    download = await download_info.value
                    filename = f"viggle_result_{int(asyncio.get_event_loop().time())}.mp4"
                    await download.save_as(f"./output/{filename}")
                    
                    print(f"✅ 视频下载完成: {filename}")
                    return filename
                    
                except:
                    continue
            
            print("❌ 未找到下载链接")
            return None
            
        except Exception as e:
            print(f"❌ 下载失败: {str(e)}")
            return None
            
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

# 使用示例
async def batch_process_viggle():
    bot = PlaywrightViggleBot()
    
    try:
        await bot.setup()
        await bot.login_viggle("your-email@example.com", "your-password")
        
        # 批量处理配置
        video_configs = [
            {
                "video_path": "./input/dance1.mp4",
                "character_image": "./characters/dancer1.jpg",
                "prompt": "energetic dancing person"
            },
            {
                "video_path": "./input/dance2.mp4", 
                "character_image": "./characters/dancer2.jpg",
                "prompt": "graceful ballet dancer"
            }
        ]
        
        results = []
        for config in video_configs:
            result = await bot.upload_and_process_video(
                config["video_path"], 
                config
            )
            results.append(result)
            
            # 处理间隔
            await asyncio.sleep(60)
        
        print(f"🎉 批量处理完成，成功处理 {len([r for r in results if r])} 个视频")
        
    finally:
        await bot.cleanup()

if __name__ == "__main__":
    asyncio.run(batch_process_viggle())
```

### 3. **Selenium Grid + undetected-chromedriver (推荐指数: ⭐⭐⭐)**

#### 特点
- 🔧 完全开源免费
- 🛡️ 专门的反检测版本
- 🔄 支持分布式执行
- 💪 社区支持强大

#### 安装配置
```bash
# 安装依赖
pip install undetected-chromedriver selenium

# 安装Chrome浏览器
# Windows: 下载Chrome安装包
# Linux: apt install google-chrome-stable
```

#### Viggle自动化实现
```python
# selenium_viggle_bot.py
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

class SeleniumViggleBot:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """设置反检测Chrome驱动"""
        options = uc.ChromeOptions()
        
        # 性能优化
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # 反检测配置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 启动驱动
        self.driver = uc.Chrome(options=options, version_main=120)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 30)
        
    def login_viggle(self, email, password):
        """登录Viggle"""
        self.driver.get('https://viggle.ai')
        time.sleep(3)
        
        # 查找并点击登录按钮
        login_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign In') or contains(text(), 'Login')]"))
        )
        login_button.click()
        
        # 输入邮箱密码
        email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
        email_input.send_keys(email)
        
        password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.send_keys(password)
        
        # 提交登录
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # 等待登录成功
        self.wait.until(EC.url_contains('dashboard'))
        print("✅ 登录成功")
        
    def process_video_batch(self, video_configs):
        """批量处理视频"""
        results = []
        
        for i, config in enumerate(video_configs):
            print(f"🎬 处理视频 {i+1}/{len(video_configs)}: {config['video_path']}")
            
            try:
                # 上传视频
                file_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
                file_input.send_keys(os.path.abspath(config['video_path']))
                
                # 等待上传完成
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "upload-complete")))
                
                # 配置参数
                if config.get('prompt'):
                    prompt_input = self.driver.find_element(By.CSS_SELECTOR, "textarea")
                    prompt_input.clear()
                    prompt_input.send_keys(config['prompt'])
                
                # 选择绿幕背景
                green_bg_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Green')]")
                green_bg_button.click()
                
                # 提交任务
                generate_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Generate')]")
                generate_button.click()
                
                # 等待处理完成
                result_file = self.wait_for_completion()
                results.append(result_file)
                
                # 处理间隔
                time.sleep(60)
                
            except Exception as e:
                print(f"❌ 处理失败: {str(e)}")
                results.append(None)
        
        return results
        
    def wait_for_completion(self, timeout_minutes=30):
        """等待任务完成"""
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                # 检查是否有下载按钮
                download_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Download')] | //button[contains(text(), 'Download')]")
                
                if download_buttons:
                    # 下载文件
                    download_buttons[0].click()
                    print("✅ 任务完成，开始下载")
                    return f"viggle_result_{int(time.time())}.mp4"
                
                # 检查是否失败
                error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Failed') or contains(text(), 'Error')]")
                if error_elements:
                    print("❌ 任务失败")
                    return None
                
                time.sleep(30)  # 等待30秒后重新检查
                
            except Exception as e:
                print(f"⚠️ 检查状态出错: {str(e)}")
                time.sleep(30)
        
        print("⏰ 任务超时")
        return None
        
    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()

# 使用示例
def run_selenium_automation():
    bot = SeleniumViggleBot()
    
    try:
        bot.setup_driver()
        bot.login_viggle("your-email@example.com", "your-password")
        
        video_configs = [
            {"video_path": "./input/video1.mp4", "prompt": "dancing person"},
            {"video_path": "./input/video2.mp4", "prompt": "fitness instructor"}
        ]
        
        results = bot.process_video_batch(video_configs)
        
        print(f"🎉 处理完成: {len([r for r in results if r])}/{len(results)} 成功")
        
    finally:
        bot.cleanup()

if __name__ == "__main__":
    run_selenium_automation()
```

## 工具对比总结

| 工具 | 易用性 | 稳定性 | 反检测 | 成本 | 推荐场景 |
|------|--------|--------|--------|------|----------|
| **UiPath** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 💰💰💰 | 商业化大规模使用 |
| **Browser Use MCP** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 💰 | Claude用户优选 |
| **Playwright** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 免费 | 技术团队开发 |
| **Selenium** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 免费 | 预算有限的项目 |

## 最终推荐

### **小规模/个人使用**
**Playwright MCP** - 免费、稳定、功能强大

### **商业化/大规模使用**  
**UiPath** - 专业可靠，有技术支持

### **Claude用户**
**Browser Use MCP** - AI驱动，最智能

**你倾向于使用哪种工具？我可以帮你详细配置和部署！** 🚀
