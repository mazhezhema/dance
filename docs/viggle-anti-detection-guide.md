# Viggle自动化 - 反检测最佳实践指南

## 🛡️ 核心原则

**永远记住：模拟真实用户行为，而不是机器人行为！**

## 🎯 避坑指南

### 1. **浏览器指纹避坑**

```python
# ❌ 错误做法 - 容易被检测
options.add_argument('--headless')  # 无头模式容易暴露
options.add_argument('--disable-gpu')  # 明显的自动化标志

# ✅ 正确做法 - 模拟真实环境
options = uc.ChromeOptions()
options.add_argument('--no-first-run')
options.add_argument('--no-default-browser-check')
options.add_argument('--disable-blink-features=AutomationControlled')

# 设置真实的User-Agent
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

# 随机化窗口大小
import random
width = random.randint(1366, 1920)
height = random.randint(768, 1080)
options.add_argument(f'--window-size={width},{height}')
```

### 2. **时间间隔避坑**

```python
# ❌ 错误做法 - 固定间隔容易被识别
time.sleep(5)  # 每次都是5秒，太规律
time.sleep(1)  # 太快，不像人类

# ✅ 正确做法 - 随机化间隔
import random

def human_delay(min_sec=2, max_sec=8):
    """模拟人类操作延迟"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def typing_delay():
    """模拟打字延迟"""
    return random.uniform(0.05, 0.3)

def page_load_delay():
    """模拟页面加载等待"""
    delay = random.uniform(3, 10)
    time.sleep(delay)
```

### 3. **鼠标操作避坑**

```python
# ❌ 错误做法 - 直线移动，瞬间点击
element.click()  # 太机械化

# ✅ 正确做法 - 模拟真实鼠标轨迹
from selenium.webdriver.common.action_chains import ActionChains

def human_click(driver, element):
    """模拟人类点击"""
    # 先移动到元素附近（不是中心点）
    size = element.size
    location = element.location
    
    # 随机偏移
    offset_x = random.randint(-size['width']//3, size['width']//3)
    offset_y = random.randint(-size['height']//3, size['height']//3)
    
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(element, offset_x, offset_y)
    actions.pause(random.uniform(0.1, 0.5))  # 悬停一下
    actions.click()
    actions.perform()
    
    human_delay(0.5, 2)  # 点击后等待

def human_scroll(driver):
    """模拟人类滚动"""
    # 随机滚动距离和方向
    scroll_distance = random.randint(100, 800)
    direction = random.choice([-1, 1])
    
    driver.execute_script(f"window.scrollBy(0, {scroll_distance * direction});")
    human_delay(1, 3)
```

### 4. **输入行为避坑**

```python
# ❌ 错误做法 - 瞬间输入全部文本
input_field.send_keys("complete_text_at_once")

# ✅ 正确做法 - 模拟逐字输入
def human_type(element, text):
    """模拟人类打字"""
    element.clear()
    human_delay(0.2, 0.8)
    
    for char in text:
        element.send_keys(char)
        time.sleep(typing_delay())
        
        # 偶尔暂停（模拟思考）
        if random.random() < 0.05:
            time.sleep(random.uniform(0.5, 2))
            
        # 偶尔删除重输（模拟打错）
        if random.random() < 0.02:
            element.send_keys(Keys.BACKSPACE)
            time.sleep(typing_delay())
            element.send_keys(char)
    
    human_delay(0.5, 1.5)
```

### 5. **文件上传避坑**

```python
# ❌ 错误做法 - 立即上传多个文件
for file in files:
    input_element.send_keys(file)  # 连续上传

# ✅ 正确做法 - 模拟真实上传流程
def upload_with_human_behavior(driver, file_path, upload_element):
    """模拟真实文件上传"""
    
    # 1. 先悬停在上传区域（模拟查看）
    actions = ActionChains(driver)
    actions.move_to_element(upload_element).perform()
    human_delay(1, 3)
    
    # 2. 点击上传按钮
    human_click(driver, upload_element)
    
    # 3. 模拟文件选择延迟（用户浏览文件需要时间）
    human_delay(2, 8)
    
    # 4. 上传文件
    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
    file_input.send_keys(os.path.abspath(file_path))
    
    # 5. 等待上传完成（观察进度）
    human_delay(5, 15)
    
    # 6. 上传完成后的确认行为
    human_delay(1, 3)
```

### 6. **Cookie管理避坑**

```python
# ❌ 错误做法 - 每次都删除Cookie
driver.delete_all_cookies()

# ✅ 正确做法 - 智能Cookie管理
class CookieManager:
    def __init__(self, cookie_file):
        self.cookie_file = cookie_file
        
    def save_session(self, driver):
        """保存完整会话状态"""
        session_data = {
            'cookies': driver.get_cookies(),
            'local_storage': driver.execute_script("return window.localStorage;"),
            'session_storage': driver.execute_script("return window.sessionStorage;"),
            'timestamp': time.time()
        }
        
        with open(self.cookie_file, 'wb') as f:
            pickle.dump(session_data, f)
    
    def restore_session(self, driver):
        """恢复会话状态"""
        if not os.path.exists(self.cookie_file):
            return False
            
        with open(self.cookie_file, 'rb') as f:
            session_data = pickle.load(f)
        
        # 检查Cookie是否过期（24小时）
        if time.time() - session_data['timestamp'] > 86400:
            return False
        
        # 恢复Cookie
        for cookie in session_data['cookies']:
            try:
                driver.add_cookie(cookie)
            except:
                continue
                
        # 恢复localStorage
        for key, value in session_data.get('local_storage', {}).items():
            driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")
            
        return True
```

### 7. **请求频率避坑**

```python
# ❌ 错误做法 - 固定频率批量处理
def bad_batch_processing():
    for video in videos:
        process_video(video)  # 连续处理
        time.sleep(60)  # 固定间隔

# ✅ 正确做法 - 智能频率控制
class RateLimiter:
    def __init__(self):
        self.last_request_time = 0
        self.request_count = 0
        self.daily_limit = 50  # Viggle Pro限制
        
    def should_continue(self):
        """检查是否可以继续请求"""
        current_hour = datetime.now().hour
        
        # 避开高峰时段
        if current_hour in [9, 10, 14, 15, 20, 21]:
            return False
            
        # 检查每日限额
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
            
        # 如果距离上次请求时间太短，额外等待
        if time_since_last < base_delay:
            additional_wait = base_delay - time_since_last
            self.logger.info(f"⏰ 频率控制，等待 {additional_wait/60:.1f} 分钟")
            time.sleep(additional_wait)
        
        self.last_request_time = time.time()
        self.request_count += 1
```

### 8. **错误处理避坑**

```python
# ❌ 错误做法 - 立即重试
try:
    element.click()
except:
    element.click()  # 立即重试，容易被检测

# ✅ 正确做法 - 智能重试机制
class SmartRetry:
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
                
                # 指数退避 + 随机抖动
                wait_time = (2 ** attempt) * random.uniform(60, 180)
                self.logger.warning(f"⚠️ 第{attempt+1}次尝试失败，{wait_time/60:.1f}分钟后重试")
                time.sleep(wait_time)
                
                # 重试前刷新页面（模拟用户刷新行为）
                if attempt > 0:
                    self.refresh_page_like_human()
    
    def refresh_page_like_human(self):
        """模拟人类刷新页面"""
        # 随机选择刷新方式
        refresh_methods = [
            lambda: self.driver.refresh(),
            lambda: self.driver.execute_script("location.reload();"),
            lambda: self.driver.get(self.driver.current_url)
        ]
        
        random.choice(refresh_methods)()
        human_delay(3, 8)  # 等待页面加载
```

### 9. **IP和网络避坑**

```python
# 网络配置建议
class NetworkConfig:
    @staticmethod
    def setup_proxy_rotation():
        """代理轮换（如果需要）"""
        proxies = [
            "proxy1:port",
            "proxy2:port", 
            # ... 住宅IP代理池
        ]
        
        proxy = random.choice(proxies)
        options.add_argument(f'--proxy-server={proxy}')
    
    @staticmethod
    def add_network_delay():
        """网络延迟模拟"""
        # 模拟真实网络波动
        delay = random.uniform(0.5, 3.0)
        time.sleep(delay)
```

### 10. **日志和监控避坑**

```python
# ❌ 错误做法 - 详细日志容易暴露
logger.info("Starting automated browser session")  # 暴露自动化意图

# ✅ 正确做法 - 隐蔽日志
logger.info("User session initiated")  # 模拟用户行为描述

class StealthLogger:
    def __init__(self):
        # 日志文件名正常化
        log_filename = f"viggle_session_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 避免敏感词汇
        self.sensitive_words = [
            'automation', 'bot', 'script', 'selenium', 
            'crawl', 'spider', 'robot'
        ]
    
    def safe_log(self, message):
        """安全日志记录"""
        # 替换敏感词汇
        safe_message = message
        for word in self.sensitive_words:
            safe_message = safe_message.replace(word, 'process')
        
        self.logger.info(safe_message)
```

## 🚀 最佳实践总结

### 1. **启动前检查清单**
- [ ] 使用最新版undetected-chromedriver
- [ ] 设置随机User-Agent和窗口大小
- [ ] 配置真实的浏览器插件和扩展
- [ ] 准备住宅IP代理（如果需要）

### 2. **会话管理**
- [ ] 实现智能Cookie管理
- [ ] 保持会话连续性
- [ ] 定期更换浏览器指纹
- [ ] 监控账号状态

### 3. **行为模拟**
- [ ] 随机化所有时间间隔
- [ ] 模拟真实鼠标轨迹
- [ ] 添加"人类犯错"行为
- [ ] 模拟页面浏览行为

### 4. **频率控制**
- [ ] 设置每日处理上限
- [ ] 避开网站高峰时段
- [ ] 实现指数退避重试
- [ ] 监控请求成功率

### 5. **异常处理**
- [ ] 优雅处理验证码
- [ ] 智能应对页面变化
- [ ] 自动恢复中断任务
- [ ] 保存处理进度

## ⚠️ 紧急情况处理

### 如果被检测到：
1. **立即停止所有自动化活动**
2. **等待24-48小时**
3. **更换浏览器指纹**
4. **如果有条件，更换IP**
5. **降低处理频率**

### 账号安全：
- 使用专门的测试账号
- 不要在主账号上进行大量自动化
- 定期手动使用账号保持活跃
- 监控账号状态变化

## 🔧 监控脚本示例

```python
class AntiDetectionMonitor:
    def __init__(self):
        self.detection_signals = [
            "captcha", "verification", "suspicious", 
            "blocked", "banned", "limit"
        ]
    
    def check_page_for_detection(self, driver):
        """检查页面是否有被检测的信号"""
        page_source = driver.page_source.lower()
        
        for signal in self.detection_signals:
            if signal in page_source:
                self.logger.warning(f"🚨 检测到风险信号: {signal}")
                return True
        
        return False
    
    def emergency_stop(self):
        """紧急停止程序"""
        self.logger.error("🛑 触发紧急停止协议")
        # 清理痕迹，保存状态，安全退出
        self.save_progress()
        self.cleanup_traces()
        sys.exit(1)
```

记住：**最好的反检测就是完美模拟真实用户！** 🎭
