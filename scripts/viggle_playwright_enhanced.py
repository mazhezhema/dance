#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle Playwright增强版本
集成SQLite数据库进行任务状态管理
"""

import asyncio
import json
import time
import random
import hashlib
import os
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, List
from dataclasses import dataclass

from playwright.async_api import async_playwright, BrowserContext, Page
from tenacity import retry, stop_after_attempt, wait_exponential
import aiofiles

# 导入数据库模块
from scripts.task_database import task_db, TaskStatus

# 配置文件路径
CONFIG_DIR = Path("config")
SECRETS_DIR = Path("secrets")
INPUT_DIR = Path("tasks_in")
OUTPUT_DIR = Path("downloads")
LOGS_DIR = Path("logs")

# 创建必要目录
for dir_path in [CONFIG_DIR, SECRETS_DIR, INPUT_DIR, OUTPUT_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'viggle_enhanced.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass 
class AccountConfig:
    """账号配置"""
    email: str
    storage_state_path: str
    daily_limit: int = 30
    concurrent_limit: int = 3

class ViggleEnhancedProcessor:
    def __init__(self, config_path: str = "config/viggle_config.json"):
        self.config = self.load_config(config_path)
        self.accounts = self.load_accounts()
        self.active_tasks = {}  # 跟踪活跃任务
        
        # 限流配置
        self.rate_min = 45  # 最小间隔秒数
        self.rate_max = 90  # 最大间隔秒数
        self.generate_timeout = 10 * 60 * 1000  # 生成超时
        self.page_timeout = 120 * 1000  # 页面超时
        
    def load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        default_config = {
            "viggle": {
                "app_url": "https://viggle.ai/app",
                "login_url": "https://viggle.ai/login"
            },
            "processing": {
                "concurrent_per_account": 3,
                "rate_limit_min": 45,
                "rate_limit_max": 90,
                "max_retries": 2,
                "generate_timeout_minutes": 10
            },
            "browser": {
                "headless": True,
                "slow_mo": 0,
                "timeout": 120000
            }
        }
        
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        else:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"创建默认配置文件: {config_path}")
            
        return default_config
    
    def load_accounts(self) -> List[AccountConfig]:
        """加载账号配置"""
        accounts_file = CONFIG_DIR / "accounts.json"
        
        if not accounts_file.exists():
            # 创建示例账号配置
            example_accounts = [
                {
                    "email": "account1@example.com",
                    "storage_state_path": "secrets/account1_state.json",
                    "daily_limit": 30,
                    "concurrent_limit": 3
                }
            ]
            with open(accounts_file, 'w', encoding='utf-8') as f:
                json.dump(example_accounts, f, indent=2, ensure_ascii=False)
            logger.warning(f"请配置账号信息: {accounts_file}")
            return []
        
        with open(accounts_file, 'r', encoding='utf-8') as f:
            accounts_data = json.load(f)
            
        return [AccountConfig(**acc) for acc in accounts_data]
    
    def calculate_task_id(self, file_path: str) -> str:
        """计算任务ID（基于文件MD5）"""
        h = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()[:12]  # 取前12位
    
    def get_file_size_mb(self, file_path: str) -> float:
        """获取文件大小（MB）"""
        try:
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except:
            return 0.0
    
    def get_video_duration(self, file_path: str) -> float:
        """获取视频时长（秒）"""
        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            return duration
        except:
            return 60  # 默认60秒
    
    def calculate_timeout(self, video_duration: float) -> int:
        """根据视频时长计算超时时间"""
        # 基础超时5分钟 + 视频时长的60倍
        base_timeout = 5 * 60 * 1000
        video_timeout = int(video_duration * 60 * 1000)
        return max(base_timeout, video_timeout)
    
    async def setup_browser_context(self, account: AccountConfig) -> tuple:
        """设置浏览器上下文"""
        playwright = await async_playwright().start()
        
        # 浏览器启动参数
        browser = await playwright.chromium.launch(
            headless=self.config["browser"]["headless"],
            slow_mo=self.config["browser"]["slow_mo"],
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage", 
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-breakpad",
                "--disable-client-side-phishing-detection",
                "--disable-component-update",
                "--disable-default-apps",
                "--disable-domain-reliability",
                "--disable-extensions",
                "--disable-features=TranslateUI",
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
                "--use-mock-keychain"
            ]
        )
        
        # 创建上下文
        storage_state_path = Path(account.storage_state_path)
        storage_state = None
        
        if storage_state_path.exists():
            with open(storage_state_path, 'r', encoding='utf-8') as f:
                storage_state = json.load(f)
        
        context = await browser.new_context(
            storage_state=storage_state,
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )
        
        # 设置默认超时
        context.set_default_timeout(self.config["browser"]["timeout"])
        
        # 设置资源拦截
        await context.route("**/*", self.route_filter)
        
        return playwright, browser, context
    
    async def route_filter(self, route):
        """资源拦截过滤器"""
        url = route.request.url
        
        # 屏蔽广告和追踪脚本
        block_patterns = [
            "googletag", "googletagmanager", "google-analytics", 
            "googleadservices", "doubleclick", "adsystem",
            "facebook.com/tr", "analytics", "hotjar", "mixpanel"
        ]
        
        should_block = any(pattern in url for pattern in block_patterns)
        
        if should_block:
            await route.abort()
        else:
            await route.continue_()
    
    async def humanize_action(self, page: Page):
        """模拟人类行为"""
        # 随机等待
        await page.wait_for_timeout(random.randint(500, 1500))
        
        # 偶尔移动鼠标
        if random.random() < 0.3:
            viewport = page.viewport_size
            x = random.randint(0, viewport['width'])
            y = random.randint(0, viewport['height'])
            await page.mouse.move(x, y)
        
        # 偶尔滚动
        if random.random() < 0.2:
            await page.evaluate("window.scrollBy(0, 100)")
            await page.wait_for_timeout(random.randint(200, 800))
    
    async def safe_click(self, page: Page, selector: str, timeout: int = 30000):
        """安全点击（带等待和人类化）"""
        element = page.locator(selector)
        await element.wait_for(state="visible", timeout=timeout)
        await element.scroll_into_view_if_needed()
        await self.humanize_action(page)
        await element.click()
        await self.humanize_action(page)
    
    async def upload_file(self, page: Page, file_path: str):
        """上传文件"""
        logger.info(f"上传文件: {file_path}")
        
        # 等待文件输入元素
        file_input = page.locator("input[type=file]").first
        await file_input.wait_for(state="attached", timeout=30000)
        
        # 上传文件
        await file_input.set_input_files(file_path)
        await self.humanize_action(page)
        
        logger.info("文件上传完成")
    
    async def wait_for_generation(self, page: Page, timeout: int):
        """等待生成完成"""
        logger.info("等待生成完成...")
        
        # 等待下载按钮出现
        download_selectors = [
            "a[download]",
            "button:has-text('Download')",
            "[role='button']:has-text('Download')",
            ".download-btn",
            "[data-testid='download']"
        ]
        
        for selector in download_selectors:
            try:
                element = page.locator(selector)
                await element.wait_for(state="visible", timeout=timeout)
                logger.info("检测到下载按钮")
                return element
            except:
                continue
        
        raise Exception("未检测到下载按钮，生成可能失败")
    
    async def download_result(self, page: Page, download_element, task_id: str) -> str:
        """下载结果文件"""
        logger.info("开始下载结果...")
        
        # 使用事件捕获下载
        async with page.expect_download() as download_info:
            await download_element.click()
        
        download = await download_info.value
        
        # 生成输出文件名
        timestamp = int(time.time())
        output_filename = f"{task_id}_viggle_{timestamp}.mp4"
        output_path = OUTPUT_DIR / output_filename
        
        # 保存文件
        await download.save_as(str(output_path))
        
        logger.info(f"下载完成: {output_path}")
        return str(output_path)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=30, max=300)
    )
    async def process_single_task(self, task: TaskStatus) -> Optional[str]:
        """处理单个任务"""
        account = next((acc for acc in self.accounts if acc.email == task.account_id), None)
        if not account:
            raise Exception(f"未找到账号: {task.account_id}")
        
        # 更新任务状态为处理中
        task_db.update_task_status(task.task_id, "processing", 
                                 started_at=datetime.now().isoformat(),
                                 account_id=account.email)
        task_db.add_task_log(task.task_id, "INFO", f"开始处理任务: {task.input_file}")
        
        logger.info(f"[{task.task_id}] 开始处理任务")
        
        start_time = time.time()
        playwright, browser, context = await self.setup_browser_context(account)
        
        try:
            page = await context.new_page()
            
            # 导航到应用页面
            logger.info(f"[{task.task_id}] 导航到Viggle应用")
            task_db.add_task_log(task.task_id, "INFO", "导航到Viggle应用")
            await page.goto(self.config["viggle"]["app_url"], wait_until="domcontentloaded")
            await self.humanize_action(page)
            
            # 检查是否需要登录
            if "/login" in page.url or "login" in page.url.lower():
                logger.warning(f"[{task.task_id}] 需要重新登录")
                task_db.add_task_log(task.task_id, "WARNING", "需要重新登录")
                raise Exception("会话过期，需要重新登录")
            
            # 上传文件
            await self.upload_file(page, task.input_file)
            task_db.add_task_log(task.task_id, "INFO", f"文件上传完成: {task.input_file}")
            
            # 点击生成按钮
            generate_selectors = [
                "button:has-text('Generate')",
                "[role='button']:has-text('Generate')",
                ".generate-btn",
                "[data-testid='generate']"
            ]
            
            generated = False
            for selector in generate_selectors:
                try:
                    await self.safe_click(page, selector)
                    generated = True
                    break
                except:
                    continue
            
            if not generated:
                raise Exception("未找到生成按钮")
            
            logger.info(f"[{task.task_id}] 已提交生成任务")
            task_db.add_task_log(task.task_id, "INFO", "已提交生成任务")
            
            # 计算超时时间
            video_duration = self.get_video_duration(task.input_file)
            timeout = self.calculate_timeout(video_duration)
            
            # 等待生成完成
            download_element = await self.wait_for_generation(page, timeout)
            task_db.add_task_log(task.task_id, "INFO", "生成完成，开始下载")
            
            # 下载结果
            output_path = await self.download_result(page, download_element, task.task_id)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 更新任务状态为完成
            task_db.update_task_status(task.task_id, "completed",
                                     output_file=output_path,
                                     completed_at=datetime.now().isoformat(),
                                     processing_time=processing_time)
            task_db.add_task_log(task.task_id, "INFO", f"任务完成: {output_path}")
            
            # 更新账号统计
            task_db.update_account_stats(account.email, True, processing_time)
            
            logger.info(f"[{task.task_id}] 任务完成: {output_path}")
            return output_path
            
        except Exception as e:
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 更新任务状态为失败
            task_db.update_task_status(task.task_id, "failed",
                                     completed_at=datetime.now().isoformat(),
                                     processing_time=processing_time,
                                     error_message=str(e),
                                     retries=task.retries + 1)
            task_db.add_task_log(task.task_id, "ERROR", f"任务失败: {str(e)}")
            
            # 更新账号统计
            task_db.update_account_stats(account.email, False, processing_time)
            
            logger.error(f"[{task.task_id}] 任务失败: {str(e)}")
            
            # 截图用于调试
            try:
                screenshot_path = LOGS_DIR / f"error_{task.task_id}_{int(time.time())}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"错误截图: {screenshot_path}")
                task_db.add_task_log(task.task_id, "INFO", f"错误截图已保存: {screenshot_path}")
            except:
                pass
            
            raise e
            
        finally:
            await context.close()
            await browser.close()
            await playwright.stop()
    
    async def scan_and_create_tasks(self) -> List[TaskStatus]:
        """扫描输入目录并创建任务"""
        tasks = []
        
        for video_file in sorted(INPUT_DIR.glob("*.mp4")):
            task_id = self.calculate_task_id(str(video_file))
            
            # 检查数据库中是否已存在
            existing_task = task_db.get_task(task_id)
            if existing_task and existing_task.status == "completed":
                logger.info(f"任务已完成，跳过: {video_file.name}")
                continue
            
            # 获取文件信息
            file_size_mb = self.get_file_size_mb(str(video_file))
            video_duration = self.get_video_duration(str(video_file))
            
            # 创建新任务
            task = TaskStatus(
                task_id=task_id,
                input_file=str(video_file),
                status="pending",
                created_at=datetime.now().isoformat(),
                file_size_mb=file_size_mb,
                video_duration=video_duration
            )
            
            # 添加到数据库
            if not existing_task:
                task_db.add_task(task)
                task_db.add_task_log(task_id, "INFO", f"新任务已创建: {video_file.name}")
                logger.info(f"新任务已创建: {video_file.name} (ID: {task_id})")
            
            tasks.append(task)
        
        return tasks
    
    async def get_pending_tasks(self) -> List[TaskStatus]:
        """获取待处理任务"""
        # 先扫描输入目录创建新任务
        await self.scan_and_create_tasks()
        
        # 从数据库获取待处理任务
        pending_tasks = task_db.get_pending_tasks()
        
        # 分配账号
        for i, task in enumerate(pending_tasks):
            if not task.account_id and self.accounts:
                account_index = i % len(self.accounts)
                task.account_id = self.accounts[account_index].email
        
        return pending_tasks
    
    async def run_batch_processing(self):
        """运行批量处理"""
        logger.info("🚀 开始批量处理...")
        task_db.add_task_log("system", "INFO", "开始批量处理")
        
        if not self.accounts:
            logger.error("❌ 未配置账号信息")
            task_db.add_task_log("system", "ERROR", "未配置账号信息")
            return
        
        # 获取待处理任务
        tasks = await self.get_pending_tasks()
        
        if not tasks:
            logger.info("📭 没有待处理的任务")
            task_db.add_task_log("system", "INFO", "没有待处理的任务")
            return
        
        logger.info(f"📋 找到 {len(tasks)} 个待处理任务")
        task_db.add_task_log("system", "INFO", f"找到 {len(tasks)} 个待处理任务")
        
        # 按账号分组任务
        account_tasks = {}
        for task in tasks:
            if task.account_id not in account_tasks:
                account_tasks[task.account_id] = []
            account_tasks[task.account_id].append(task)
        
        # 并行处理每个账号的任务
        async def process_account_tasks(account_id: str, task_list: List[TaskStatus]):
            logger.info(f"👤 账号 {account_id} 开始处理 {len(task_list)} 个任务")
            task_db.add_task_log("system", "INFO", f"账号 {account_id} 开始处理 {len(task_list)} 个任务")
            
            for task in task_list:
                try:
                    result = await self.process_single_task(task)
                    logger.info(f"✅ [{task.task_id}] 处理成功: {result}")
                except Exception as e:
                    logger.error(f"❌ [{task.task_id}] 处理失败: {str(e)}")
                
                # 任务间延迟
                delay = random.randint(self.rate_min, self.rate_max)
                logger.info(f"😴 等待 {delay} 秒...")
                await asyncio.sleep(delay)
        
        # 启动并行处理
        account_coroutines = [
            process_account_tasks(account_id, task_list)
            for account_id, task_list in account_tasks.items()
        ]
        
        await asyncio.gather(*account_coroutines, return_exceptions=True)
        
        # 导出统计信息
        task_db.export_stats_to_json()
        
        logger.info("🎉 批量处理完成！")
        task_db.add_task_log("system", "INFO", "批量处理完成")

async def main():
    """主函数"""
    print("🎭 Viggle Playwright 增强版自动化处理器")
    print("=" * 60)
    
    processor = ViggleEnhancedProcessor()
    await processor.run_batch_processing()

if __name__ == "__main__":
    asyncio.run(main())
