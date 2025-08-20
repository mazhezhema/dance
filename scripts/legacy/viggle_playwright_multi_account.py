#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle多账号Playwright自动化处理器
专为反spam和多账号轮换设计
"""

import asyncio
import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
import logging
from playwright.async_api import async_playwright
import os

class ViggleMultiAccountProcessor:
    def __init__(self, config_file='config_multi_account.json'):
        self.config = self.load_config(config_file)
        self.current_account_index = 0
        self.account_usage = {}  # 跟踪每个账号的使用情况
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('viggle_multi_account.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 创建目录
        self.create_directories()
        
    def load_config(self, config_file):
        """加载多账号配置"""
        default_config = {
            "accounts": [
                {
                    "email": "account1@example.com",
                    "password": "password1",
                    "daily_limit": 20,
                    "profile_dir": "./profiles/account1"
                },
                {
                    "email": "account2@example.com", 
                    "password": "password2",
                    "daily_limit": 20,
                    "profile_dir": "./profiles/account2"
                }
            ],
            "viggle": {
                "login_url": "https://viggle.ai/login",
                "dashboard_url": "https://viggle.ai/dashboard"
            },
            "directories": {
                "source_videos": "./source_videos",
                "target_people": "./target_people",
                "output": "./output",
                "profiles": "./profiles"
            },
            "anti_spam": {
                "min_delay_between_accounts": 3600,  # 1小时
                "max_daily_total": 100,             # 总日限额
                "random_delay_range": [300, 1800],   # 5-30分钟随机延迟
                "avoid_peak_hours": [9, 10, 14, 15, 20, 21],
                "account_rotation_strategy": "round_robin"  # 或 "least_used"
            },
            "matching_rules": {
                "dance": "dancer.jpg",
                "fitness": "fitness_model.jpg",
                "traditional": "traditional_woman.jpg",
                "default": "default_person.jpg"
            }
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 深度合并配置
                self.deep_update(default_config, user_config)
        else:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"创建了默认配置文件: {config_file}")
            
        return default_config
    
    def deep_update(self, base_dict, update_dict):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self.deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
                
    def create_directories(self):
        """创建目录结构"""
        for dir_path in self.config["directories"].values():
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            
        # 为每个账号创建独立的profile目录
        for account in self.config["accounts"]:
            Path(account["profile_dir"]).mkdir(parents=True, exist_ok=True)
    
    def get_next_account(self):
        """获取下一个可用账号"""
        strategy = self.config["anti_spam"]["account_rotation_strategy"]
        
        if strategy == "round_robin":
            return self._round_robin_account()
        elif strategy == "least_used":
            return self._least_used_account()
        else:
            return self._round_robin_account()
    
    def _round_robin_account(self):
        """轮询策略"""
        available_accounts = []
        
        for i, account in enumerate(self.config["accounts"]):
            if self.can_use_account(i):
                available_accounts.append((i, account))
        
        if not available_accounts:
            return None, None
            
        # 从当前索引开始查找
        for offset in range(len(available_accounts)):
            index = (self.current_account_index + offset) % len(available_accounts)
            account_index, account = available_accounts[index]
            
            if self.can_use_account(account_index):
                self.current_account_index = (index + 1) % len(available_accounts)
                return account_index, account
                
        return None, None
    
    def _least_used_account(self):
        """最少使用策略"""
        best_account = None
        best_index = None
        min_usage = float('inf')
        
        for i, account in enumerate(self.config["accounts"]):
            if not self.can_use_account(i):
                continue
                
            today = datetime.now().strftime('%Y-%m-%d')
            usage_key = f"{i}_{today}"
            usage_count = self.account_usage.get(usage_key, 0)
            
            if usage_count < min_usage:
                min_usage = usage_count
                best_account = account
                best_index = i
        
        return best_index, best_account
    
    def can_use_account(self, account_index):
        """检查账号是否可用"""
        account = self.config["accounts"][account_index]
        today = datetime.now().strftime('%Y-%m-%d')
        usage_key = f"{account_index}_{today}"
        
        # 检查日限额
        daily_usage = self.account_usage.get(usage_key, 0)
        if daily_usage >= account["daily_limit"]:
            return False
        
        # 检查账号间延迟
        last_used_key = f"{account_index}_last_used"
        last_used = self.account_usage.get(last_used_key, 0)
        min_delay = self.config["anti_spam"]["min_delay_between_accounts"]
        
        if time.time() - last_used < min_delay:
            return False
            
        return True
    
    def record_account_usage(self, account_index):
        """记录账号使用"""
        today = datetime.now().strftime('%Y-%m-%d')
        usage_key = f"{account_index}_{today}"
        last_used_key = f"{account_index}_last_used"
        
        self.account_usage[usage_key] = self.account_usage.get(usage_key, 0) + 1
        self.account_usage[last_used_key] = time.time()
        
        # 保存使用记录
        self.save_usage_stats()
    
    def save_usage_stats(self):
        """保存使用统计"""
        stats_file = "account_usage_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.account_usage, f, indent=2)
    
    def load_usage_stats(self):
        """加载使用统计"""
        stats_file = "account_usage_stats.json"
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                self.account_usage = json.load(f)
    
    def should_avoid_current_time(self):
        """检查是否应该避开当前时间段"""
        current_hour = datetime.now().hour
        avoid_hours = self.config["anti_spam"]["avoid_peak_hours"]
        
        return current_hour in avoid_hours
    
    def get_smart_delay(self):
        """获取智能延迟时间"""
        delay_range = self.config["anti_spam"]["random_delay_range"]
        base_delay = random.uniform(delay_range[0], delay_range[1])
        
        # 根据当前时间调整延迟
        current_hour = datetime.now().hour
        
        # 高峰时段增加延迟
        if current_hour in [9, 10, 14, 15, 20, 21]:
            base_delay *= 1.5
        # 深夜时段减少延迟  
        elif current_hour in [1, 2, 3, 4, 5]:
            base_delay *= 0.7
            
        return base_delay
    
    async def create_browser_context(self, account):
        """为账号创建浏览器上下文"""
        # 随机化浏览器指纹
        viewports = [
            {'width': 1366, 'height': 768},
            {'width': 1920, 'height': 1080}, 
            {'width': 1440, 'height': 900},
            {'width': 1280, 'height': 720}
        ]
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # 启动浏览器
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # 显示浏览器便于调试
            args=[
                '--no-first-run',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # 创建独立上下文
        context = await browser.new_context(
            viewport=random.choice(viewports),
            user_agent=random.choice(user_agents),
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            # 使用账号独立的存储
            storage_state=f"{account['profile_dir']}/state.json" if os.path.exists(f"{account['profile_dir']}/state.json") else None
        )
        
        return playwright, browser, context
    
    async def save_context_state(self, context, account):
        """保存上下文状态"""
        await context.storage_state(path=f"{account['profile_dir']}/state.json")
    
    async def login_account(self, page, account):
        """登录指定账号"""
        self.logger.info(f"🔑 登录账号: {account['email']}")
        
        try:
            await page.goto(self.config["viggle"]["login_url"])
            
            # 等待页面加载
            await page.wait_for_load_state('networkidle')
            
            # 输入邮箱 - 模拟人类输入
            email_selector = "input[type='email'], input[name='email']"
            await page.fill(email_selector, "")  # 先清空
            await self.human_type(page, email_selector, account['email'])
            
            # 输入密码
            password_selector = "input[type='password'], input[name='password']"
            await page.fill(password_selector, "")
            await self.human_type(page, password_selector, account['password'])
            
            # 点击登录按钮
            login_button = "button[type='submit'], .login-button"
            await page.click(login_button)
            
            # 等待登录成功
            await page.wait_for_url("**/dashboard**", timeout=30000)
            
            self.logger.info("✅ 登录成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 登录失败: {str(e)}")
            return False
    
    async def human_type(self, page, selector, text):
        """模拟人类打字"""
        for char in text:
            await page.type(selector, char, delay=random.uniform(50, 200))
            
            # 偶尔暂停
            if random.random() < 0.1:
                await asyncio.sleep(random.uniform(0.5, 2))
    
    async def upload_files_and_process(self, page, video_path, person_path):
        """上传文件并处理"""
        self.logger.info(f"📤 处理: {os.path.basename(video_path)}")
        
        try:
            # 上传视频
            video_input = "input[type='file'][accept*='video']"
            await page.set_input_files(video_input, video_path)
            await asyncio.sleep(random.uniform(2, 5))
            
            # 上传人物图片
            image_inputs = await page.query_selector_all("input[type='file'][accept*='image']")
            if len(image_inputs) > 0:
                # 通常第二个input是人物图片
                target_input = image_inputs[-1] if len(image_inputs) > 1 else image_inputs[0]
                await target_input.set_input_files(person_path)
                await asyncio.sleep(random.uniform(2, 5))
            
            # 设置背景为绿幕（便于后处理）
            try:
                green_bg_selector = "button:has-text('Green'), .green-background, [data-background='green']"
                await page.click(green_bg_selector, timeout=5000)
            except:
                self.logger.warning("⚠️ 未找到绿幕背景选项")
            
            # 提交处理任务
            generate_button = "button:has-text('Generate'), button:has-text('Create'), .generate-button"
            await page.click(generate_button)
            
            # 等待处理完成
            return await self.wait_for_completion(page)
            
        except Exception as e:
            self.logger.error(f"❌ 处理失败: {str(e)}")
            return False
    
    async def wait_for_completion(self, page):
        """等待处理完成"""
        self.logger.info("⏳ 等待处理完成...")
        
        max_wait_time = 600  # 10分钟超时
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # 检查下载按钮
                download_button = await page.query_selector("a:has-text('Download'), button:has-text('Download')")
                if download_button:
                    await download_button.click()
                    self.logger.info("✅ 开始下载结果")
                    await asyncio.sleep(10)  # 等待下载完成
                    return True
                
                # 检查错误信息
                error_elements = await page.query_selector_all("*:has-text('Failed'), *:has-text('Error')")
                if error_elements:
                    self.logger.error("❌ 处理失败")
                    return False
                
                # 等待30秒后重新检查
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.warning(f"⚠️ 检查状态出错: {str(e)}")
                await asyncio.sleep(30)
        
        self.logger.error("❌ 处理超时")
        return False
    
    def get_matching_person(self, video_filename):
        """根据视频文件名匹配目标人物"""
        video_name = video_filename.lower()
        
        person_file = self.config["matching_rules"]["default"]
        for keyword, person in self.config["matching_rules"].items():
            if keyword in video_name:
                person_file = person
                break
                
        person_path = os.path.join(self.config["directories"]["target_people"], person_file)
        
        if not os.path.exists(person_path):
            # 使用目录中的第一个图片文件
            people_dir = Path(self.config["directories"]["target_people"])
            image_files = list(people_dir.glob("*.jpg")) + list(people_dir.glob("*.png"))
            if image_files:
                person_path = str(image_files[0])
            else:
                raise FileNotFoundError("未找到任何目标人物图片")
                
        return person_path
    
    async def process_videos_with_account(self, account_index, account, video_files):
        """使用指定账号处理视频"""
        playwright, browser, context = await self.create_browser_context(account)
        
        try:
            page = await context.new_page()
            
            # 登录账号
            if not await self.login_account(page, account):
                return []
            
            # 保存登录状态
            await self.save_context_state(context, account)
            
            results = []
            
            for video_file in video_files:
                try:
                    # 检查账号限额
                    if not self.can_use_account(account_index):
                        self.logger.warning(f"⚠️ 账号 {account['email']} 已达限额")
                        break
                    
                    # 获取匹配的人物图片
                    person_path = self.get_matching_person(os.path.basename(video_file))
                    
                    # 处理视频
                    success = await self.upload_files_and_process(page, str(video_file), person_path)
                    
                    # 记录结果
                    result = {
                        "video": os.path.basename(video_file),
                        "person": os.path.basename(person_path),
                        "account": account['email'],
                        "success": success,
                        "timestamp": datetime.now().isoformat()
                    }
                    results.append(result)
                    
                    # 记录账号使用
                    self.record_account_usage(account_index)
                    
                    # 任务间智能延迟
                    delay = self.get_smart_delay()
                    self.logger.info(f"😴 等待 {delay/60:.1f} 分钟...")
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    self.logger.error(f"❌ 处理视频失败 {video_file}: {str(e)}")
                    continue
            
            return results
            
        finally:
            await context.close()
            await browser.close()
            await playwright.stop()
    
    async def run_multi_account_processing(self):
        """运行多账号处理"""
        self.logger.info("🚀 启动多账号批量处理...")
        
        # 加载使用统计
        self.load_usage_stats()
        
        # 获取所有视频文件
        source_dir = Path(self.config["directories"]["source_videos"])
        video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(source_dir.glob(ext))
            video_files.extend(source_dir.glob(ext.upper()))
        
        if not video_files:
            self.logger.error("❌ 未找到视频文件！")
            return
        
        total_videos = len(video_files)
        self.logger.info(f"📁 发现 {total_videos} 个视频文件")
        
        # 检查总日限额
        today = datetime.now().strftime('%Y-%m-%d')
        total_today = sum(
            self.account_usage.get(f"{i}_{today}", 0) 
            for i in range(len(self.config["accounts"]))
        )
        
        max_daily = self.config["anti_spam"]["max_daily_total"]
        if total_today >= max_daily:
            self.logger.error(f"❌ 今日总限额已达上限: {total_today}/{max_daily}")
            return
        
        all_results = []
        processed_count = 0
        
        # 分配视频到各账号
        remaining_videos = list(video_files)
        
        while remaining_videos and processed_count < max_daily:
            # 获取下一个可用账号
            account_index, account = self.get_next_account()
            
            if account is None:
                if self.should_avoid_current_time():
                    self.logger.info("⏰ 当前为高峰时段，等待1小时...")
                    await asyncio.sleep(3600)
                    continue
                else:
                    self.logger.warning("⚠️ 暂无可用账号，等待30分钟...")
                    await asyncio.sleep(1800)
                    continue
            
            # 为当前账号分配视频
            account_limit = account["daily_limit"]
            today_usage = self.account_usage.get(f"{account_index}_{today}", 0)
            can_process = min(
                account_limit - today_usage,
                len(remaining_videos),
                max_daily - processed_count
            )
            
            if can_process <= 0:
                continue
            
            batch_videos = remaining_videos[:can_process]
            remaining_videos = remaining_videos[can_process:]
            
            self.logger.info(f"👤 账号 {account['email']} 处理 {len(batch_videos)} 个视频")
            
            # 处理视频
            results = await self.process_videos_with_account(account_index, account, batch_videos)
            all_results.extend(results)
            processed_count += len(results)
            
            # 账号间延迟
            if remaining_videos:
                delay = self.config["anti_spam"]["min_delay_between_accounts"]
                self.logger.info(f"🔄 切换账号，等待 {delay/60:.1f} 分钟...")
                await asyncio.sleep(delay)
        
        # 生成报告
        self.generate_final_report(all_results)
    
    def generate_final_report(self, results):
        """生成最终报告"""
        success_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        total = len(results)
        success_count = len(success_results)
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        # 按账号统计
        account_stats = {}
        for result in results:
            account = result["account"]
            if account not in account_stats:
                account_stats[account] = {"total": 0, "success": 0}
            account_stats[account]["total"] += 1
            if result["success"]:
                account_stats[account]["success"] += 1
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_videos": total,
                "successful": success_count,
                "failed": len(failed_results),
                "success_rate": f"{success_rate:.1f}%"
            },
            "account_statistics": account_stats,
            "detailed_results": results
        }
        
        # 保存报告
        report_file = f"multi_account_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        self.logger.info(f"\n🎉 多账号批量处理完成!")
        self.logger.info(f"📈 总共处理: {total} 个视频")
        self.logger.info(f"✅ 成功: {success_count} 个")
        self.logger.info(f"❌ 失败: {len(failed_results)} 个")
        self.logger.info(f"📊 成功率: {success_rate:.1f}%")
        self.logger.info(f"📄 详细报告: {report_file}")

async def main():
    print("🎭 Viggle多账号Playwright自动化处理器")
    print("=" * 60)
    
    processor = ViggleMultiAccountProcessor()
    await processor.run_multi_account_processing()

if __name__ == "__main__":
    asyncio.run(main())
