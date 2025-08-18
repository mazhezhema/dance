#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle自动化处理器
目录结构：
- source_videos/     # 原始视频源
- target_people/     # 目标人物图片
- output/           # 输出目录
- cookies/          # 保存的Cookie
"""

import os
import json
import time
import pickle
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import logging
import random
from datetime import datetime
import sys

class RateLimiter:
    """智能频率控制器"""
    def __init__(self):
        self.last_request_time = 0
        self.request_count = 0
        self.daily_limit = 50
        
    def should_continue(self):
        """检查是否可以继续请求"""
        current_hour = datetime.now().hour
        
        # 避开高峰时段
        if current_hour in [9, 10, 14, 15, 20, 21]:
            return False
            
        if self.request_count >= self.daily_limit:
            return False
            
        return True
    
    def wait_if_needed(self):
        """智能等待"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # 基础延迟：5-15分钟
        base_delay = random.uniform(300, 900)
        
        # 根据请求数量增加延迟
        if self.request_count > 20:
            base_delay *= 1.5
        elif self.request_count > 30:
            base_delay *= 2
            
        if time_since_last < base_delay:
            additional_wait = base_delay - time_since_last
            print(f"⏰ 频率控制，等待 {additional_wait/60:.1f} 分钟")
            time.sleep(additional_wait)
        
        self.last_request_time = time.time()
        self.request_count += 1

class SmartRetry:
    """智能重试处理器"""
    def __init__(self, max_retries=3):
        self.max_retries = max_retries
        
    def retry_with_backoff(self, func, *args, **kwargs):
        """指数退避重试"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                
                wait_time = (2 ** attempt) * random.uniform(60, 180)
                print(f"⚠️ 第{attempt+1}次尝试失败，{wait_time/60:.1f}分钟后重试")
                time.sleep(wait_time)

class AntiDetectionMonitor:
    """反检测监控器"""
    def __init__(self):
        self.detection_signals = [
            "captcha", "verification", "suspicious", 
            "blocked", "banned", "limit", "robot"
        ]
    
    def check_page_for_detection(self, driver):
        """检查页面是否有被检测的信号"""
        try:
            page_source = driver.page_source.lower()
            
            for signal in self.detection_signals:
                if signal in page_source:
                    print(f"🚨 检测到风险信号: {signal}")
                    return True
            
            return False
        except:
            return False
    
    def emergency_stop(self):
        """紧急停止程序"""
        print("🛑 触发紧急停止协议")
        sys.exit(1)

class ViggleAutoProcessor:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.driver = None
        self.wait = None
        self.cookies_file = 'cookies/viggle_cookies.pkl'
        self.rate_limiter = RateLimiter()
        self.retry_handler = SmartRetry()
        self.detection_monitor = AntiDetectionMonitor()
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('viggle_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 创建必要目录
        self.create_directories()
        
    def load_config(self, config_file):
        """加载配置文件"""
        default_config = {
            "viggle": {
                "email": "your-email@example.com",
                "password": "your-password",
                "login_url": "https://viggle.ai/login",
                "dashboard_url": "https://viggle.ai/dashboard"
            },
            "directories": {
                "source_videos": "./source_videos",
                "target_people": "./target_people", 
                "output": "./output",
                "cookies": "./cookies"
            },
            "processing": {
                "batch_size": 2,
                "wait_timeout": 300,
                "retry_count": 3,
                "delay_between_tasks": 300,
                "daily_limit": 30,
                "avoid_peak_hours": True
            },
            "anti_detection": {
                "random_delays": True,
                "human_behavior": True,
                "session_rotation": True,
                "emergency_stop": True
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
                default_config.update(user_config)
        else:
            # 创建默认配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"创建了默认配置文件: {config_file}")
            
        return default_config
    
    def create_directories(self):
        """创建必要的目录"""
        for dir_path in self.config["directories"].values():
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            
    def setup_browser(self):
        """设置浏览器 - 反检测优化版"""
        self.logger.info("🚀 启动浏览器会话...")
        
        options = uc.ChromeOptions()
        
        # 反检测核心设置
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        
        # 随机化User-Agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # 随机化窗口大小
        width = random.randint(1366, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        # 下载设置
        download_dir = os.path.abspath(self.config["directories"]["output"])
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0
        }
        options.add_experimental_option("prefs", prefs)
        
        # 高级反检测设置
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = uc.Chrome(options=options)
        
        # 执行反检测脚本
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        
        self.wait = WebDriverWait(self.driver, 30)
        
        # 模拟真实浏览行为
        self.human_delay(2, 5)
        self.logger.info("✅ 浏览器会话建立成功")
        
    def human_delay(self, min_sec=2, max_sec=8):
        """模拟人类操作延迟"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        
    def typing_delay(self):
        """模拟打字延迟"""
        return random.uniform(0.05, 0.3)
        
    def human_click(self, element):
        """模拟人类点击"""
        # 先移动到元素附近
        size = element.size
        location = element.location
        
        # 随机偏移
        offset_x = random.randint(-size['width']//3, size['width']//3)
        offset_y = random.randint(-size['height']//3, size['height']//3)
        
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(element, offset_x, offset_y)
        actions.pause(random.uniform(0.1, 0.5))
        actions.click()
        actions.perform()
        
        self.human_delay(0.5, 2)
        
    def human_type(self, element, text):
        """模拟人类打字"""
        element.clear()
        self.human_delay(0.2, 0.8)
        
        for char in text:
            element.send_keys(char)
            time.sleep(self.typing_delay())
            
            # 偶尔暂停（模拟思考）
            if random.random() < 0.05:
                time.sleep(random.uniform(0.5, 2))
                
            # 偶尔删除重输（模拟打错）
            if random.random() < 0.02:
                element.send_keys(Keys.BACKSPACE)
                time.sleep(self.typing_delay())
                element.send_keys(char)
        
        self.human_delay(0.5, 1.5)
        
    def save_cookies(self):
        """保存Cookie"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            self.logger.info("💾 Cookie保存成功")
        except Exception as e:
            self.logger.error(f"❌ Cookie保存失败: {str(e)}")
            
    def load_cookies(self):
        """加载Cookie"""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                # 先访问首页
                self.driver.get("https://viggle.ai")
                time.sleep(2)
                
                # 添加Cookie
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        continue
                        
                self.logger.info("🍪 Cookie加载成功")
                return True
        except Exception as e:
            self.logger.error(f"❌ Cookie加载失败: {str(e)}")
            
        return False
        
    def login_viggle(self):
        """登录Viggle"""
        self.logger.info("🔑 开始登录流程...")
        
        # 尝试加载Cookie登录
        if self.load_cookies():
            self.driver.refresh()
            time.sleep(3)
            
            # 检查是否已登录
            if self.check_login_status():
                self.logger.info("✅ Cookie登录成功")
                return True
        
        # Cookie登录失败，使用账号密码登录
        self.logger.info("🔐 使用账号密码登录...")
        
        self.driver.get(self.config["viggle"]["login_url"])
        time.sleep(3)
        
        try:
            # 查找登录表单
            email_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
            )
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
            
            # 输入凭据
            email_input.clear()
            email_input.send_keys(self.config["viggle"]["email"])
            
            password_input.clear() 
            password_input.send_keys(self.config["viggle"]["password"])
            
            # 提交登录
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .login-button, button:contains('Sign In')")
            login_button.click()
            
            # 等待登录成功
            self.wait.until(EC.url_contains('dashboard'))
            
            # 保存Cookie
            self.save_cookies()
            
            self.logger.info("✅ 账号密码登录成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 登录失败: {str(e)}")
            return False
            
    def check_login_status(self):
        """检查登录状态"""
        try:
            current_url = self.driver.current_url
            if 'dashboard' in current_url or 'home' in current_url:
                return True
                
            # 尝试访问dashboard
            self.driver.get(self.config["viggle"]["dashboard_url"])
            time.sleep(2)
            
            return 'login' not in self.driver.current_url.lower()
            
        except:
            return False
            
    def get_matching_person(self, video_filename):
        """根据视频文件名匹配目标人物"""
        video_name = video_filename.lower()
        
        # 根据匹配规则选择人物
        person_file = self.config["matching_rules"]["default"]
        for keyword, person in self.config["matching_rules"].items():
            if keyword in video_name:
                person_file = person
                break
                
        person_path = os.path.join(self.config["directories"]["target_people"], person_file)
        
        if not os.path.exists(person_path):
            self.logger.warning(f"⚠️ 目标人物文件不存在: {person_path}")
            # 使用目录中的第一个图片文件
            people_dir = Path(self.config["directories"]["target_people"])
            image_files = list(people_dir.glob("*.jpg")) + list(people_dir.glob("*.png"))
            if image_files:
                person_path = str(image_files[0])
                self.logger.info(f"📷 使用替代人物: {person_path}")
            else:
                raise FileNotFoundError("未找到任何目标人物图片")
                
        return person_path
        
    def upload_video(self, video_path):
        """上传视频 - 反检测优化版"""
        self.logger.info(f"📤 上传视频: {os.path.basename(video_path)}")
        
        # 检查页面是否有异常
        if self.detection_monitor.check_page_for_detection(self.driver):
            self.detection_monitor.emergency_stop()
        
        try:
            # 查找视频上传元素
            upload_selectors = [
                "input[type='file'][accept*='video']",
                ".video-upload input[type='file']",
                ".upload-video input[type='file']",
                "input[type='file']"
            ]
            
            video_input = None
            for selector in upload_selectors:
                try:
                    video_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
                    
            if not video_input:
                # 尝试点击上传按钮 - 使用人类化点击
                upload_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Upload')] | //div[contains(@class, 'upload')]")
                if upload_buttons:
                    self.human_click(upload_buttons[0])
                    self.human_delay(2, 5)
                    video_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            
            if video_input:
                # 模拟文件选择延迟（用户浏览文件需要时间）
                self.human_delay(2, 8)
                
                video_input.send_keys(os.path.abspath(video_path))
                self.logger.info("✅ 视频上传成功")
                
                # 等待上传完成并观察进度
                self.human_delay(5, 15)
                return True
            else:
                raise Exception("未找到视频上传元素")
                
        except Exception as e:
            self.logger.error(f"❌ 视频上传失败: {str(e)}")
            return False
            
    def upload_target_person(self, person_path):
        """上传目标人物图片"""
        self.logger.info(f"👤 上传目标人物: {os.path.basename(person_path)}")
        
        try:
            # 查找人物图片上传元素
            person_selectors = [
                "input[type='file'][accept*='image']",
                ".character-upload input[type='file']",
                ".person-upload input[type='file']",
                ".reference-image input[type='file']"
            ]
            
            person_input = None
            for selector in person_selectors:
                try:
                    person_inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    # 如果有多个，通常第二个是人物上传
                    if len(person_inputs) > 1:
                        person_input = person_inputs[1]
                    elif len(person_inputs) == 1:
                        person_input = person_inputs[0]
                    if person_input:
                        break
                except:
                    continue
                    
            if person_input:
                person_input.send_keys(os.path.abspath(person_path))
                self.logger.info("✅ 目标人物上传成功")
                time.sleep(3)
                return True
            else:
                self.logger.warning("⚠️ 未找到人物上传元素，可能网页结构已变化")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 目标人物上传失败: {str(e)}")
            return False
            
    def configure_mix_settings(self):
        """配置Mix设置"""
        self.logger.info("⚙️ 配置Mix设置...")
        
        try:
            # 选择背景模式（绿幕便于后处理）
            bg_selectors = [
                "button:contains('Green')",
                ".green-background",
                "[data-background='green']",
                ".bg-green"
            ]
            
            for selector in bg_selectors:
                try:
                    bg_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    bg_btn.click()
                    self.logger.info("✅ 设置绿幕背景")
                    break
                except:
                    continue
            
            # 其他设置
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置设置失败: {str(e)}")
            return False
            
    def submit_mix_task(self):
        """提交Mix任务"""
        self.logger.info("🚀 提交Mix任务...")
        
        try:
            # 查找生成按钮
            generate_selectors = [
                "button:contains('Generate')",
                "button:contains('Create')",
                "button:contains('Mix')",
                ".generate-button",
                ".mix-button"
            ]
            
            for selector in generate_selectors:
                try:
                    generate_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    generate_btn.click()
                    self.logger.info("✅ 任务提交成功")
                    return True
                except:
                    continue
                    
            raise Exception("未找到生成按钮")
            
        except Exception as e:
            self.logger.error(f"❌ 任务提交失败: {str(e)}")
            return False
            
    def wait_for_completion_and_download(self, video_name):
        """等待完成并下载"""
        self.logger.info("⏳ 等待处理完成...")
        
        max_wait = self.config["processing"]["wait_timeout"]
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # 检查下载按钮
                download_selectors = [
                    "a:contains('Download')",
                    "button:contains('Download')",
                    ".download-button",
                    ".download-link"
                ]
                
                download_element = None
                for selector in download_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            download_element = elements[-1]  # 获取最新的
                            break
                    except:
                        continue
                
                if download_element:
                    # 开始下载
                    self.logger.info("📥 开始下载结果...")
                    download_element.click()
                    
                    # 等待下载完成
                    time.sleep(10)
                    
                    # 生成输出文件名
                    output_filename = f"viggle_mix_{video_name}_{int(time.time())}.mp4"
                    self.logger.info(f"✅ 下载完成: {output_filename}")
                    
                    return output_filename
                
                # 检查是否失败
                error_indicators = [
                    "*:contains('Failed')",
                    "*:contains('Error')", 
                    "*:contains('failed')",
                    ".error",
                    ".failed"
                ]
                
                for selector in error_indicators:
                    try:
                        if self.driver.find_elements(By.CSS_SELECTOR, selector):
                            raise Exception("Viggle处理失败")
                    except:
                        continue
                
                # 显示处理状态
                status_selectors = [
                    ".progress",
                    ".status", 
                    ".processing-status",
                    ".task-status"
                ]
                
                for selector in status_selectors:
                    try:
                        status_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if status_elements:
                            status_text = status_elements[-1].text
                            if status_text.strip():
                                self.logger.info(f"📊 处理状态: {status_text}")
                                break
                    except:
                        continue
                
                # 等待30秒后重新检查
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"⚠️ 检查状态出错: {str(e)}")
                time.sleep(30)
        
        raise Exception(f"任务超时 ({max_wait}秒)")
        
    def process_single_video(self, video_path):
        """处理单个视频"""
        video_name = os.path.basename(video_path)
        self.logger.info(f"\n🎬 开始处理: {video_name}")
        
        try:
            # 1. 获取匹配的目标人物
            person_path = self.get_matching_person(video_name)
            self.logger.info(f"👤 匹配人物: {os.path.basename(person_path)}")
            
            # 2. 上传视频
            if not self.upload_video(video_path):
                raise Exception("视频上传失败")
                
            # 3. 上传目标人物
            if not self.upload_target_person(person_path):
                self.logger.warning("⚠️ 人物上传失败，但继续处理")
                
            # 4. 配置设置
            self.configure_mix_settings()
            
            # 5. 提交任务
            if not self.submit_mix_task():
                raise Exception("任务提交失败")
                
            # 6. 等待完成并下载
            result_file = self.wait_for_completion_and_download(video_name)
            
            return {
                "status": "success",
                "input_video": video_name,
                "target_person": os.path.basename(person_path),
                "output_file": result_file
            }
            
        except Exception as e:
            self.logger.error(f"❌ 处理失败: {str(e)}")
            return {
                "status": "failed",
                "input_video": video_name,
                "error": str(e)
            }
            
    def process_batch(self):
        """批量处理"""
        self.logger.info("🚀 开始批量处理...")
        
        # 获取所有视频文件
        source_dir = Path(self.config["directories"]["source_videos"])
        video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(source_dir.glob(ext))
            video_files.extend(source_dir.glob(ext.upper()))
        
        if not video_files:
            self.logger.error("❌ 未找到视频文件！")
            return []
        
        total_videos = len(video_files)
        self.logger.info(f"📁 发现 {total_videos} 个视频文件")
        
        results = []
        batch_size = self.config["processing"]["batch_size"]
        delay = self.config["processing"]["delay_between_tasks"]
        
        # 分批处理
        for i in range(0, total_videos, batch_size):
            batch = video_files[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            self.logger.info(f"\n📦 处理批次 {batch_num}/{(total_videos-1)//batch_size + 1}: {len(batch)} 个视频")
            
            for j, video_file in enumerate(batch):
                result = self.process_single_video(str(video_file))
                results.append(result)
                
                # 任务间延迟 (除了批次中的最后一个)
                if j < len(batch) - 1:
                    self.logger.info(f"😴 等待 {delay} 秒...")
                    time.sleep(delay)
            
            # 批次间延迟 (除了最后一个批次)
            if i + batch_size < total_videos:
                batch_delay = delay * 3  # 批次间延迟更长
                self.logger.info(f"🛌 批次完成，休息 {batch_delay} 秒...")
                time.sleep(batch_delay)
        
        return results
        
    def generate_report(self, results):
        """生成处理报告"""
        self.logger.info("\n📊 生成处理报告...")
        
        success_results = [r for r in results if r["status"] == "success"]
        failed_results = [r for r in results if r["status"] == "failed"]
        
        total = len(results)
        success_count = len(success_results)
        failed_count = len(failed_results)
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        # 生成报告
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_videos": total,
                "successful": success_count,
                "failed": failed_count,
                "success_rate": f"{success_rate:.1f}%"
            },
            "successful_tasks": success_results,
            "failed_tasks": failed_results
        }
        
        # 保存报告
        report_file = f"viggle_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        self.logger.info(f"\n🎉 批量处理完成!")
        self.logger.info(f"📈 总共处理: {total} 个视频")
        self.logger.info(f"✅ 成功: {success_count} 个")
        self.logger.info(f"❌ 失败: {failed_count} 个") 
        self.logger.info(f"📊 成功率: {success_rate:.1f}%")
        self.logger.info(f"📄 详细报告: {report_file}")
        
        return report
        
    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()
            self.logger.info("🧹 浏览器已关闭")
            
    def run(self):
        """主运行函数"""
        try:
            # 1. 设置浏览器
            self.setup_browser()
            
            # 2. 登录
            if not self.login_viggle():
                raise Exception("登录失败")
                
            # 3. 批量处理
            results = self.process_batch()
            
            # 4. 生成报告
            self.generate_report(results)
            
        except Exception as e:
            self.logger.error(f"💥 严重错误: {str(e)}")
            
        finally:
            self.cleanup()

def main():
    print("🎭 Viggle自动化处理器")
    print("=" * 50)
    
    # 检查目录结构
    required_dirs = ['source_videos', 'target_people']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"❌ 请创建目录并添加文件: {dir_name}/")
            return
            
        files = os.listdir(dir_name)
        if not files:
            print(f"❌ 目录为空: {dir_name}/")
            return
            
        print(f"✅ {dir_name}/: 发现 {len(files)} 个文件")
    
    # 运行处理器
    processor = ViggleAutoProcessor()
    processor.run()

if __name__ == "__main__":
    main()
