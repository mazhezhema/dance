#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle Playwright终极优化版
基于engineering-memory的最佳实践，结合结构化问题分析方法论
"""

import asyncio
import json
import time
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import traceback

from playwright.async_api import async_playwright, BrowserContext, Page, Browser
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import aiofiles

# 基于engineering-memory的目录架构
PROJECT_ROOT = Path.cwd()
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output" 
LOGS_DIR = PROJECT_ROOT / "logs"
PROFILES_DIR = PROJECT_ROOT / "profiles"
TEMP_DIR = PROJECT_ROOT / "temp"

# 确保目录存在
for dir_path in [INPUT_DIR, OUTPUT_DIR, LOGS_DIR, PROFILES_DIR, TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 结构化日志配置 (engineering-memory 最佳实践)
class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # 文件处理器
            file_handler = logging.FileHandler(
                LOGS_DIR / f'viggle_{datetime.now().strftime("%Y%m%d")}.log',
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def log_event(self, event: str, **kwargs):
        """结构化事件日志"""
        extra_data = {
            "event": event,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.logger.info(f"Event: {event}", extra=extra_data)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """结构化错误日志"""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        self.logger.error(f"Error: {error_data['error_type']}", extra=error_data)

logger = StructuredLogger(__name__)

@dataclass
class TaskState:
    """任务状态（engineering-memory: 状态管理最佳实践）"""
    task_id: str
    video_path: str
    account_email: str
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    retry_count: int = 0
    error_message: str = ""
    output_path: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        data = asdict(self)
        # 处理datetime对象
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat() if value else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskState':
        """从字典反序列化"""
        # 处理datetime字段
        datetime_fields = ['created_at', 'started_at', 'completed_at']
        for field in datetime_fields:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)

class SessionManager:
    """会话管理器（engineering-memory: 反检测架构）"""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768}, 
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864}
        ]
    
    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)
    
    def get_random_viewport(self) -> Dict[str, int]:
        """获取随机视窗大小"""
        return random.choice(self.viewports)
    
    def get_browser_args(self) -> List[str]:
        """获取浏览器启动参数（反检测）"""
        return [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-domain-reliability",
            "--disable-extensions",
            "--disable-features=TranslateUI,VizDisplayCompositor",
            "--disable-hang-monitor",
            "--disable-ipc-flooding-protection",
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-renderer-backgrounding",
            "--disable-sync",
            "--disable-web-security",
            "--metrics-recording-only",
            "--no-crash-upload",
            "--no-default-browser-check",
            "--no-pings",
            "--password-store=basic",
            "--use-mock-keychain",
            f"--window-size={random.randint(1200, 1920)},{random.randint(800, 1080)}"
        ]

class HumanBehaviorSimulator:
    """人类行为模拟器（engineering-memory: 反检测技术）"""
    
    @staticmethod
    async def random_delay(min_ms: int = 500, max_ms: int = 2000):
        """随机延迟"""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        await asyncio.sleep(delay)
    
    @staticmethod
    async def human_type(page: Page, selector: str, text: str):
        """模拟人类打字"""
        element = page.locator(selector)
        await element.click()
        await HumanBehaviorSimulator.random_delay(200, 500)
        
        for char in text:
            await element.type(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))
    
    @staticmethod
    async def human_click(page: Page, selector: str):
        """模拟人类点击"""
        element = page.locator(selector)
        
        # 先悬停
        await element.hover()
        await HumanBehaviorSimulator.random_delay(200, 800)
        
        # 再点击
        await element.click()
        await HumanBehaviorSimulator.random_delay(300, 1000)
    
    @staticmethod
    async def random_mouse_movement(page: Page):
        """随机鼠标移动"""
        if random.random() < 0.3:  # 30%概率移动鼠标
            viewport = page.viewport_size
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            await page.mouse.move(x, y)
            await HumanBehaviorSimulator.random_delay(100, 300)
    
    @staticmethod
    async def scroll_randomly(page: Page):
        """随机滚动"""
        if random.random() < 0.2:  # 20%概率滚动
            scroll_amount = random.randint(-200, 200)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await HumanBehaviorSimulator.random_delay(200, 600)

class TaskQueue:
    """任务队列管理器（engineering-memory: 任务管理最佳实践）"""
    
    def __init__(self, queue_file: Path = None):
        self.queue_file = queue_file or (TEMP_DIR / "task_queue.json")
        self.tasks: Dict[str, TaskState] = {}
        self.load_queue()
    
    def load_queue(self):
        """加载任务队列"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = {
                        task_id: TaskState.from_dict(task_data)
                        for task_id, task_data in data.items()
                    }
                logger.log_event("queue_loaded", task_count=len(self.tasks))
            except Exception as e:
                logger.log_error(e, {"context": "load_queue"})
                self.tasks = {}
    
    def save_queue(self):
        """保存任务队列"""
        try:
            data = {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            }
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.log_event("queue_saved", task_count=len(self.tasks))
        except Exception as e:
            logger.log_error(e, {"context": "save_queue"})
    
    def add_task(self, video_path: str, account_email: str) -> str:
        """添加任务"""
        task_id = self.generate_task_id(video_path)
        
        if task_id not in self.tasks:
            task = TaskState(
                task_id=task_id,
                video_path=video_path,
                account_email=account_email
            )
            self.tasks[task_id] = task
            self.save_queue()
            logger.log_event("task_added", task_id=task_id, video_path=video_path)
        
        return task_id
    
    def update_task_status(self, task_id: str, status: str, **kwargs):
        """更新任务状态"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = status
            
            if status == "processing" and not task.started_at:
                task.started_at = datetime.now()
            elif status in ["completed", "failed"] and not task.completed_at:
                task.completed_at = datetime.now()
            
            for key, value in kwargs.items():
                setattr(task, key, value)
            
            self.save_queue()
            logger.log_event("task_status_updated", task_id=task_id, status=status)
    
    def get_pending_tasks(self) -> List[TaskState]:
        """获取待处理任务"""
        return [task for task in self.tasks.values() if task.status == "pending"]
    
    def get_failed_tasks(self, max_retries: int = 3) -> List[TaskState]:
        """获取可重试的失败任务"""
        return [
            task for task in self.tasks.values() 
            if task.status == "failed" and task.retry_count < max_retries
        ]
    
    @staticmethod
    def generate_task_id(video_path: str) -> str:
        """生成任务ID"""
        h = hashlib.md5()
        with open(video_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()[:12]

class ViggleAutomationEngine:
    """Viggle自动化引擎（engineering-memory: 核心业务逻辑）"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.session_manager = SessionManager()
        self.behavior_simulator = HumanBehaviorSimulator()
        self.task_queue = TaskQueue()
        
        # 性能配置
        self.max_concurrent_accounts = 3
        self.task_interval_seconds = (60, 120)  # 任务间隔
        self.session_rotation_hours = 6
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "accounts": [
                {
                    "email": "your_email@example.com",
                    "password": "your_password",
                    "daily_limit": 30,
                    "profile_dir": "./profiles/main_account"
                }
            ],
            "viggle": {
                "login_url": "https://viggle.ai/login",
                "app_url": "https://viggle.ai/app",
                "timeout": 300000
            },
            "processing": {
                "max_retries": 3,
                "timeout_minutes": 15,
                "parallel_accounts": 2
            }
        }
        
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 深度合并配置
                def deep_update(d, u):
                    for k, v in u.items():
                        if isinstance(v, dict):
                            d[k] = deep_update(d.get(k, {}), v)
                        else:
                            d[k] = v
                    return d
                deep_update(default_config, user_config)
        else:
            # 创建示例配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.log_event("config_created", path=str(config_file))
        
        return default_config
    
    async def create_browser_context(self, account: Dict[str, Any]) -> tuple:
        """创建浏览器上下文（反检测优化）"""
        playwright = await async_playwright().start()
        
        # 反检测浏览器配置
        browser = await playwright.chromium.launch(
            headless=False,  # 非无头模式更难检测
            slow_mo=random.randint(50, 150),  # 随机慢动作
            args=self.session_manager.get_browser_args()
        )
        
        # 会话状态文件
        profile_dir = Path(account['profile_dir'])
        profile_dir.mkdir(parents=True, exist_ok=True)
        storage_state_file = profile_dir / "storage_state.json"
        
        # 加载已保存的会话状态
        storage_state = None
        if storage_state_file.exists():
            try:
                with open(storage_state_file, 'r', encoding='utf-8') as f:
                    storage_state = json.load(f)
            except Exception as e:
                logger.log_error(e, {"context": "load_storage_state"})
        
        # 创建上下文
        context = await browser.new_context(
            storage_state=storage_state,
            user_agent=self.session_manager.get_random_user_agent(),
            viewport=self.session_manager.get_random_viewport(),
            accept_downloads=True,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            permissions=['notifications'],
            geolocation={'latitude': 39.9042, 'longitude': 116.4074}  # 北京坐标
        )
        
        # 设置超时
        context.set_default_timeout(self.config["viggle"]["timeout"])
        
        # 注入反检测脚本
        await context.add_init_script("""
            // 移除webdriver标识
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // 伪造插件
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // 伪造语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
            
            // 伪造权限
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        """)
        
        return playwright, browser, context, storage_state_file
    
    async def save_session_state(self, context: BrowserContext, storage_state_file: Path):
        """保存会话状态"""
        try:
            storage_state = await context.storage_state()
            with open(storage_state_file, 'w', encoding='utf-8') as f:
                json.dump(storage_state, f, indent=2)
            logger.log_event("session_saved", file=str(storage_state_file))
        except Exception as e:
            logger.log_error(e, {"context": "save_session_state"})
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=30, max=300),
        retry=retry_if_exception_type((asyncio.TimeoutError, Exception))
    )
    async def process_single_video(self, task: TaskState) -> Optional[str]:
        """处理单个视频（核心处理逻辑）"""
        account = next(
            (acc for acc in self.config["accounts"] if acc["email"] == task.account_email),
            None
        )
        
        if not account:
            raise ValueError(f"未找到账号配置: {task.account_email}")
        
        # 更新任务状态
        self.task_queue.update_task_status(task.task_id, "processing")
        
        logger.log_event("video_processing_start", 
                         task_id=task.task_id, 
                         video_path=task.video_path,
                         account=task.account_email)
        
        playwright, browser, context, storage_state_file = None, None, None, None
        
        try:
            # 创建浏览器上下文
            playwright, browser, context, storage_state_file = await self.create_browser_context(account)
            page = await context.new_page()
            
            # 导航到Viggle应用
            await page.goto(self.config["viggle"]["app_url"], wait_until="domcontentloaded")
            await self.behavior_simulator.random_delay(2000, 4000)
            
            # 检查登录状态
            if await self.check_login_required(page):
                await self.perform_login(page, account)
                await self.save_session_state(context, storage_state_file)
            
            # 上传视频文件
            await self.upload_video(page, task.video_path)
            
            # 配置生成参数（如果需要）
            await self.configure_generation_settings(page)
            
            # 开始生成
            await self.start_generation(page)
            
            # 等待生成完成并下载
            output_path = await self.wait_and_download_result(page, task.task_id)
            
            # 更新任务状态
            self.task_queue.update_task_status(
                task.task_id, 
                "completed", 
                output_path=output_path
            )
            
            logger.log_event("video_processing_success",
                           task_id=task.task_id,
                           output_path=output_path)
            
            return output_path
            
        except Exception as e:
            # 错误处理
            self.task_queue.update_task_status(
                task.task_id,
                "failed",
                error_message=str(e),
                retry_count=task.retry_count + 1
            )
            
            logger.log_error(e, {
                "context": "video_processing",
                "task_id": task.task_id,
                "video_path": task.video_path
            })
            
            # 错误截图
            try:
                if context:
                    page = context.pages[0] if context.pages else await context.new_page()
                    screenshot_path = LOGS_DIR / f"error_{task.task_id}_{int(time.time())}.png"
                    await page.screenshot(path=str(screenshot_path))
                    logger.log_event("error_screenshot", path=str(screenshot_path))
            except:
                pass
            
            raise e
            
        finally:
            # 清理资源
            try:
                if context:
                    await self.save_session_state(context, storage_state_file)
                    await context.close()
                if browser:
                    await browser.close()
                if playwright:
                    await playwright.stop()
            except Exception as cleanup_error:
                logger.log_error(cleanup_error, {"context": "cleanup"})
    
    async def check_login_required(self, page: Page) -> bool:
        """检查是否需要登录"""
        try:
            # 等待页面加载
            await page.wait_for_load_state("domcontentloaded")
            await self.behavior_simulator.random_delay(2000, 3000)
            
            # 检查登录相关元素
            login_indicators = [
                "text=Sign in",
                "text=Login", 
                "text=登录",
                "[data-testid='login-button']",
                "button:has-text('Sign in')"
            ]
            
            for indicator in login_indicators:
                try:
                    element = page.locator(indicator)
                    if await element.is_visible(timeout=3000):
                        return True
                except:
                    continue
            
            # 检查URL
            current_url = page.url
            if any(keyword in current_url.lower() for keyword in ['login', 'signin', 'auth']):
                return True
            
            return False
            
        except Exception as e:
            logger.log_error(e, {"context": "check_login_required"})
            return True  # 默认需要登录
    
    async def perform_login(self, page: Page, account: Dict[str, Any]):
        """执行登录操作"""
        logger.log_event("login_start", account=account["email"])
        
        try:
            # 导航到登录页面
            await page.goto(self.config["viggle"]["login_url"], wait_until="domcontentloaded")
            await self.behavior_simulator.random_delay(2000, 4000)
            
            # 填写邮箱
            email_selectors = [
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='email']",
                "#email"
            ]
            
            for selector in email_selectors:
                try:
                    if await page.locator(selector).is_visible(timeout=5000):
                        await self.behavior_simulator.human_type(page, selector, account["email"])
                        break
                except:
                    continue
            
            # 填写密码
            password_selectors = [
                "input[type='password']",
                "input[name='password']", 
                "#password"
            ]
            
            for selector in password_selectors:
                try:
                    if await page.locator(selector).is_visible(timeout=5000):
                        await self.behavior_simulator.human_type(page, selector, account["password"])
                        break
                except:
                    continue
            
            # 点击登录按钮
            login_button_selectors = [
                "button[type='submit']",
                "button:has-text('Sign in')",
                "button:has-text('Login')",
                "button:has-text('登录')",
                "[data-testid='login-button']"
            ]
            
            for selector in login_button_selectors:
                try:
                    if await page.locator(selector).is_visible(timeout=5000):
                        await self.behavior_simulator.human_click(page, selector)
                        break
                except:
                    continue
            
            # 等待登录完成
            await page.wait_for_url("**/app**", timeout=30000)
            await self.behavior_simulator.random_delay(3000, 5000)
            
            logger.log_event("login_success", account=account["email"])
            
        except Exception as e:
            logger.log_error(e, {"context": "login", "account": account["email"]})
            raise Exception(f"登录失败: {str(e)}")
    
    async def upload_video(self, page: Page, video_path: str):
        """上传视频文件"""
        logger.log_event("video_upload_start", video_path=video_path)
        
        try:
            # 查找文件上传元素
            upload_selectors = [
                "input[type='file']",
                "[data-testid='file-input']",
                "input[accept*='video']"
            ]
            
            file_input = None
            for selector in upload_selectors:
                try:
                    element = page.locator(selector)
                    if await element.is_visible(timeout=5000):
                        file_input = element
                        break
                except:
                    continue
            
            if not file_input:
                # 查找上传按钮并点击
                upload_button_selectors = [
                    "button:has-text('Upload')",
                    "button:has-text('上传')",
                    "[data-testid='upload-button']",
                    ".upload-btn"
                ]
                
                for selector in upload_button_selectors:
                    try:
                        if await page.locator(selector).is_visible(timeout=5000):
                            await self.behavior_simulator.human_click(page, selector)
                            await self.behavior_simulator.random_delay(1000, 2000)
                            break
                    except:
                        continue
                
                # 重新查找文件输入
                for selector in upload_selectors:
                    try:
                        element = page.locator(selector)
                        if await element.is_visible(timeout=5000):
                            file_input = element
                            break
                    except:
                        continue
            
            if not file_input:
                raise Exception("未找到文件上传元素")
            
            # 上传文件
            await file_input.set_input_files(video_path)
            await self.behavior_simulator.random_delay(3000, 6000)
            
            logger.log_event("video_upload_success", video_path=video_path)
            
        except Exception as e:
            logger.log_error(e, {"context": "upload_video", "video_path": video_path})
            raise Exception(f"视频上传失败: {str(e)}")
    
    async def configure_generation_settings(self, page: Page):
        """配置生成设置"""
        try:
            # 等待设置区域加载
            await self.behavior_simulator.random_delay(2000, 4000)
            
            # 这里可以添加特定的设置配置
            # 比如选择人物、风格等参数
            
            logger.log_event("generation_settings_configured")
            
        except Exception as e:
            logger.log_error(e, {"context": "configure_generation_settings"})
            # 设置配置失败不应该阻止流程
    
    async def start_generation(self, page: Page):
        """开始生成"""
        logger.log_event("generation_start")
        
        try:
            # 查找生成按钮
            generate_button_selectors = [
                "button:has-text('Generate')",
                "button:has-text('生成')",
                "[data-testid='generate-button']",
                ".generate-btn"
            ]
            
            for selector in generate_button_selectors:
                try:
                    if await page.locator(selector).is_visible(timeout=10000):
                        await self.behavior_simulator.human_click(page, selector)
                        await self.behavior_simulator.random_delay(2000, 4000)
                        logger.log_event("generation_submitted")
                        return
                except:
                    continue
            
            raise Exception("未找到生成按钮")
            
        except Exception as e:
            logger.log_error(e, {"context": "start_generation"})
            raise Exception(f"开始生成失败: {str(e)}")
    
    async def wait_and_download_result(self, page: Page, task_id: str) -> str:
        """等待生成完成并下载结果"""
        logger.log_event("waiting_for_result", task_id=task_id)
        
        try:
            # 生成超时时间（从配置读取）
            timeout_minutes = self.config["processing"]["timeout_minutes"]
            timeout_ms = timeout_minutes * 60 * 1000
            
            # 等待下载按钮出现
            download_selectors = [
                "a[download]",
                "button:has-text('Download')",
                "button:has-text('下载')",
                "[data-testid='download-button']",
                ".download-btn"
            ]
            
            download_element = None
            for selector in download_selectors:
                try:
                    element = page.locator(selector)
                    await element.wait_for(state="visible", timeout=timeout_ms)
                    download_element = element
                    break
                except:
                    continue
            
            if not download_element:
                raise Exception("生成超时或失败，未找到下载按钮")
            
            # 下载文件
            async with page.expect_download() as download_info:
                await self.behavior_simulator.human_click(page, selector)
            
            download = await download_info.value
            
            # 生成输出文件名
            timestamp = int(time.time())
            output_filename = f"{task_id}_viggle_{timestamp}.mp4"
            output_path = OUTPUT_DIR / output_filename
            
            # 保存文件
            await download.save_as(str(output_path))
            
            logger.log_event("download_complete", 
                           task_id=task_id, 
                           output_path=str(output_path))
            
            return str(output_path)
            
        except Exception as e:
            logger.log_error(e, {"context": "wait_and_download_result", "task_id": task_id})
            raise Exception(f"下载结果失败: {str(e)}")
    
    async def scan_input_videos(self) -> List[str]:
        """扫描输入视频文件"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        videos_dir = INPUT_DIR / "videos"
        
        if not videos_dir.exists():
            videos_dir.mkdir(parents=True)
            return []
        
        video_files = []
        for ext in video_extensions:
            video_files.extend(videos_dir.glob(f"*{ext}"))
            video_files.extend(videos_dir.glob(f"*{ext.upper()}"))
        
        return [str(f) for f in sorted(video_files)]
    
    async def run_batch_processing(self):
        """运行批量处理（主入口）"""
        logger.log_event("batch_processing_start")
        
        try:
            # 扫描输入视频
            video_files = await self.scan_input_videos()
            
            if not video_files:
                logger.log_event("no_videos_found")
                print("❌ 未找到视频文件，请将视频放入 input/videos/ 目录")
                return
            
            # 创建任务
            accounts = self.config["accounts"]
            if not accounts:
                logger.log_event("no_accounts_configured")
                print("❌ 未配置账号信息，请编辑 config.json")
                return
            
            # 分配任务到账号（轮询方式）
            for i, video_file in enumerate(video_files):
                account = accounts[i % len(accounts)]
                task_id = self.task_queue.add_task(video_file, account["email"])
                logger.log_event("task_created", task_id=task_id, video=video_file)
            
            # 获取待处理任务
            pending_tasks = self.task_queue.get_pending_tasks()
            failed_tasks = self.task_queue.get_failed_tasks()
            all_tasks = pending_tasks + failed_tasks
            
            if not all_tasks:
                logger.log_event("no_tasks_to_process")
                print("✅ 所有任务已完成")
                return
            
            print(f"📋 找到 {len(all_tasks)} 个待处理任务")
            
            # 按账号分组任务
            account_tasks = {}
            for task in all_tasks:
                if task.account_email not in account_tasks:
                    account_tasks[task.account_email] = []
                account_tasks[task.account_email].append(task)
            
            # 并行处理各账号的任务
            async def process_account_tasks(account_email: str, tasks: List[TaskState]):
                logger.log_event("account_processing_start", 
                               account=account_email, 
                               task_count=len(tasks))
                
                for task in tasks:
                    try:
                        result_path = await self.process_single_video(task)
                        print(f"✅ [{task.task_id}] 处理成功: {result_path}")
                        
                    except Exception as e:
                        print(f"❌ [{task.task_id}] 处理失败: {str(e)}")
                    
                    # 任务间延迟
                    interval = random.randint(*self.task_interval_seconds)
                    logger.log_event("task_interval_wait", seconds=interval)
                    print(f"😴 等待 {interval} 秒...")
                    await asyncio.sleep(interval)
                
                logger.log_event("account_processing_complete", account=account_email)
            
            # 启动并行处理
            coroutines = [
                process_account_tasks(account_email, tasks)
                for account_email, tasks in account_tasks.items()
            ]
            
            await asyncio.gather(*coroutines, return_exceptions=True)
            
            logger.log_event("batch_processing_complete")
            print("🎉 批量处理完成！")
            
        except Exception as e:
            logger.log_error(e, {"context": "batch_processing"})
            print(f"❌ 批量处理失败: {str(e)}")

async def main():
    """主函数"""
    print("🎭 Viggle Playwright 终极优化版")
    print("基于 engineering-memory 最佳实践")
    print("=" * 60)
    
    try:
        engine = ViggleAutomationEngine()
        await engine.run_batch_processing()
    except KeyboardInterrupt:
        print("\n⏹️  用户中断处理")
        logger.log_event("user_interrupted")
    except Exception as e:
        print(f"❌ 程序异常: {str(e)}")
        logger.log_error(e, {"context": "main"})

if __name__ == "__main__":
    asyncio.run(main())
