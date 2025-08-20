#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle Playwright终极版 - 基于Loguru的现代化日志系统
结合engineering-memory最佳实践和loguru先进特性
"""

import asyncio
import json
import time
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import traceback

from playwright.async_api import async_playwright, BrowserContext, Page, Browser
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 导入增强的Loguru日志系统
from loguru_logger_enhanced import LoguruEnhancedLogger, logger, log_event, log_error, log_performance

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

# 初始化增强日志系统
app_logger = LoguruEnhancedLogger("viggle_loguru")

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
        ua = random.choice(self.user_agents)
        app_logger.log_anti_detection("user_agent_selection", ua_type=ua.split()[0])
        return ua
    
    def get_random_viewport(self) -> Dict[str, int]:
        """获取随机视窗大小"""
        viewport = random.choice(self.viewports)
        app_logger.log_anti_detection("viewport_randomization", 
                                     width=viewport["width"], 
                                     height=viewport["height"])
        return viewport

class HumanBehaviorSimulator:
    """人类行为模拟器（engineering-memory: 反检测技术）"""
    
    @staticmethod
    async def random_delay(min_ms: int = 500, max_ms: int = 2000):
        """随机延迟"""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        app_logger.log_anti_detection("random_delay", delay_seconds=delay)
        await asyncio.sleep(delay)
    
    @staticmethod
    async def human_click(page: Page, selector: str):
        """模拟人类点击"""
        start_time = time.time()
        
        try:
            element = page.locator(selector)
            
            # 先悬停
            await element.hover()
            await HumanBehaviorSimulator.random_delay(200, 800)
            
            # 再点击
            await element.click()
            await HumanBehaviorSimulator.random_delay(300, 1000)
            
            duration = time.time() - start_time
            app_logger.log_performance("human_click", duration, selector=selector)
            
        except Exception as e:
            duration = time.time() - start_time
            app_logger.log_error(e, context={"operation": "human_click", "selector": selector})
            raise

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
                log_event("queue_loaded", task_count=len(self.tasks))
            except Exception as e:
                log_error(e, context={"operation": "load_queue"})
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
            log_event("queue_saved", task_count=len(self.tasks))
        except Exception as e:
            log_error(e, context={"operation": "save_queue"})
    
    def update_task_status(self, task_id: str, status: str, **kwargs):
        """更新任务状态"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            old_status = task.status
            task.status = status
            
            if status == "processing" and not task.started_at:
                task.started_at = datetime.now()
            elif status in ["completed", "failed"] and not task.completed_at:
                task.completed_at = datetime.now()
            
            for key, value in kwargs.items():
                setattr(task, key, value)
            
            self.save_queue()
            log_event("task_status_updated", 
                     task_id=task_id, 
                     old_status=old_status, 
                     new_status=status)

class ViggleAutomationEngine:
    """Viggle自动化引擎（engineering-memory: 核心业务逻辑）"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.session_manager = SessionManager()
        self.behavior_simulator = HumanBehaviorSimulator()
        self.task_queue = TaskQueue()
        self.logger = app_logger
        
        # 性能配置
        self.max_concurrent_accounts = 3
        self.task_interval_seconds = (60, 120)
        
        logger.info("🎭 Viggle自动化引擎已初始化")
    
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
                default_config.update(user_config)
            log_event("config_loaded", path=str(config_file))
        else:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            log_event("config_created", path=str(config_file))
        
        return default_config
    
    @app_logger.timer()
    async def create_browser_context(self, account: Dict[str, Any]) -> tuple:
        """创建浏览器上下文（反检测优化）"""
        logger.info(f"🌐 为账号 {account['email']} 创建浏览器上下文")
        
        playwright = await async_playwright().start()
        
        # 反检测浏览器配置
        browser = await playwright.chromium.launch(
            headless=False,
            slow_mo=random.randint(50, 150),
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--disable-background-networking",
                "--disable-extensions"
            ]
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
                log_event("session_loaded", account=account['email'])
            except Exception as e:
                log_error(e, context={"operation": "load_session_state"})
        
        # 创建上下文
        context = await browser.new_context(
            storage_state=storage_state,
            user_agent=self.session_manager.get_random_user_agent(),
            viewport=self.session_manager.get_random_viewport(),
            accept_downloads=True,
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )
        
        context.set_default_timeout(self.config["viggle"]["timeout"])
        
        log_event("browser_context_created", account=account['email'])
        return playwright, browser, context, storage_state_file
    
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
        
        # 开始处理
        self.task_queue.update_task_status(task.task_id, "processing")
        self.logger.log_task_start(task.task_id, "video_processing", 
                                  video_path=task.video_path,
                                  account=task.account_email)
        
        start_time = time.time()
        playwright, browser, context, storage_state_file = None, None, None, None
        
        try:
            # 创建浏览器上下文
            playwright, browser, context, storage_state_file = await self.create_browser_context(account)
            page = await context.new_page()
            
            # 导航到Viggle应用
            await page.goto(self.config["viggle"]["app_url"], wait_until="domcontentloaded")
            await self.behavior_simulator.random_delay(2000, 4000)
            
            # 上传视频文件
            await self.upload_video(page, task.video_path)
            
            # 开始生成
            await self.start_generation(page)
            
            # 等待生成完成并下载
            output_path = await self.wait_and_download_result(page, task.task_id)
            
            # 任务完成
            duration = time.time() - start_time
            self.task_queue.update_task_status(task.task_id, "completed", output_path=output_path)
            self.logger.log_task_complete(task.task_id, duration, output_path=output_path)
            
            return output_path
            
        except Exception as e:
            duration = time.time() - start_time
            self.task_queue.update_task_status(
                task.task_id,
                "failed", 
                error_message=str(e),
                retry_count=task.retry_count + 1
            )
            
            self.logger.log_task_failed(task.task_id, e, 
                                       video_path=task.video_path,
                                       account=task.account_email,
                                       duration=duration)
            
            # 错误截图
            try:
                if context:
                    page = context.pages[0] if context.pages else await context.new_page()
                    screenshot_path = LOGS_DIR / f"error_{task.task_id}_{int(time.time())}.png"
                    await page.screenshot(path=str(screenshot_path))
                    log_event("error_screenshot", path=str(screenshot_path), task_id=task.task_id)
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
                log_error(cleanup_error, context={"operation": "cleanup"})
    
    async def upload_video(self, page: Page, video_path: str):
        """上传视频文件"""
        start_time = time.time()
        
        try:
            log_event("video_upload_start", video_path=video_path)
            
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
                raise Exception("未找到文件上传元素")
            
            # 上传文件
            await file_input.set_input_files(video_path)
            await self.behavior_simulator.random_delay(3000, 6000)
            
            duration = time.time() - start_time
            log_performance("video_upload", duration, video_path=video_path)
            log_event("video_upload_success", video_path=video_path, duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            log_error(e, context={"operation": "upload_video", "video_path": video_path})
            log_performance("video_upload", duration, success=False, error=str(e))
            raise Exception(f"视频上传失败: {str(e)}")
    
    async def start_generation(self, page: Page):
        """开始生成"""
        start_time = time.time()
        
        try:
            log_event("generation_start")
            
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
                        duration = time.time() - start_time
                        log_event("generation_submitted", duration=duration)
                        log_performance("start_generation", duration)
                        return
                except:
                    continue
            
            raise Exception("未找到生成按钮")
            
        except Exception as e:
            duration = time.time() - start_time
            log_error(e, context={"operation": "start_generation"})
            log_performance("start_generation", duration, success=False, error=str(e))
            raise Exception(f"开始生成失败: {str(e)}")
    
    async def wait_and_download_result(self, page: Page, task_id: str) -> str:
        """等待生成完成并下载结果"""
        start_time = time.time()
        
        try:
            log_event("waiting_for_result", task_id=task_id)
            
            # 生成超时时间
            timeout_minutes = self.config["processing"]["timeout_minutes"]
            timeout_ms = timeout_minutes * 60 * 1000
            
            # 等待下载按钮出现
            download_selectors = [
                "a[download]",
                "button:has-text('Download')",
                "button:has-text('下载')",
                "[data-testid='download-button']"
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
            
            duration = time.time() - start_time
            log_event("download_complete", task_id=task_id, output_path=str(output_path), duration=duration)
            log_performance("wait_and_download", duration, task_id=task_id)
            
            return str(output_path)
            
        except Exception as e:
            duration = time.time() - start_time
            log_error(e, context={"operation": "wait_and_download_result", "task_id": task_id})
            log_performance("wait_and_download", duration, success=False, error=str(e))
            raise Exception(f"下载结果失败: {str(e)}")
    
    async def save_session_state(self, context: BrowserContext, storage_state_file: Path):
        """保存会话状态"""
        try:
            storage_state = await context.storage_state()
            with open(storage_state_file, 'w', encoding='utf-8') as f:
                json.dump(storage_state, f, indent=2)
            log_event("session_saved", file=str(storage_state_file))
        except Exception as e:
            log_error(e, context={"operation": "save_session_state"})
    
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
        
        log_event("videos_scanned", count=len(video_files), directory=str(videos_dir))
        return [str(f) for f in sorted(video_files)]
    
    async def run_batch_processing(self):
        """运行批量处理（主入口）"""
        log_event("batch_processing_start")
        
        try:
            # 扫描输入视频
            video_files = await self.scan_input_videos()
            
            if not video_files:
                log_event("no_videos_found")
                logger.warning("❌ 未找到视频文件，请将视频放入 input/videos/ 目录")
                return
            
            # 创建任务
            accounts = self.config["accounts"]
            if not accounts:
                log_event("no_accounts_configured")
                logger.error("❌ 未配置账号信息，请编辑 config.json")
                return
            
            # 分配任务到账号
            for i, video_file in enumerate(video_files):
                account = accounts[i % len(accounts)]
                task_id = self.task_queue.generate_task_id(video_file)
                if task_id not in self.task_queue.tasks:
                    task = TaskState(
                        task_id=task_id,
                        video_path=video_file,
                        account_email=account["email"]
                    )
                    self.task_queue.tasks[task_id] = task
                    log_event("task_created", task_id=task_id, video=video_file)
            
            self.task_queue.save_queue()
            
            # 获取待处理任务
            pending_tasks = [task for task in self.task_queue.tasks.values() if task.status == "pending"]
            
            if not pending_tasks:
                log_event("no_tasks_to_process")
                logger.info("✅ 所有任务已完成")
                return
            
            logger.info(f"📋 找到 {len(pending_tasks)} 个待处理任务")
            
            # 处理任务
            for task in pending_tasks:
                try:
                    result_path = await self.process_single_video(task)
                    logger.success(f"✅ [{task.task_id}] 处理成功: {result_path}")
                    
                except Exception as e:
                    logger.error(f"❌ [{task.task_id}] 处理失败: {str(e)}")
                
                # 任务间延迟
                interval = random.randint(*self.task_interval_seconds)
                log_event("task_interval_wait", seconds=interval)
                logger.info(f"😴 等待 {interval} 秒...")
                await asyncio.sleep(interval)
            
            log_event("batch_processing_complete")
            logger.success("🎉 批量处理完成！")
            
        except Exception as e:
            log_error(e, context={"operation": "batch_processing"})
            logger.error(f"❌ 批量处理失败: {str(e)}")

# 为TaskQueue添加生成task_id的方法
def generate_task_id(video_path: str) -> str:
    """生成任务ID"""
    h = hashlib.md5()
    with open(video_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()[:12]

# 给TaskQueue类添加方法
TaskQueue.generate_task_id = staticmethod(generate_task_id)

async def main():
    """主函数"""
    logger.info("🎭 Viggle Playwright Loguru版")
    logger.info("基于 engineering-memory + loguru 最佳实践")
    logger.info("=" * 60)
    
    try:
        engine = ViggleAutomationEngine()
        await engine.run_batch_processing()
    except KeyboardInterrupt:
        logger.warning("⏹️  用户中断处理")
        log_event("user_interrupted")
    except Exception as e:
        logger.error(f"❌ 程序异常: {str(e)}")
        log_error(e, context={"operation": "main"})

if __name__ == "__main__":
    asyncio.run(main())

