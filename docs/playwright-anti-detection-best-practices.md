# Playwright反检测最佳实践与避坑指南

## 🎯 核心原则

**Playwright虽然内置反检测，但仍需要精心配置来避开高级检测系统！**

## 🛡️ Playwright反检测优势

### 1. **天然反检测能力**
```python
# Playwright默认就很"隐身"
browser = await playwright.chromium.launch()  # 已经很难检测了

# 而Selenium需要大量配置
options.add_argument('--disable-blink-features=AutomationControlled')
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

### 2. **多引擎支持**
```python
# 可以随机切换浏览器引擎
engines = [playwright.chromium, playwright.firefox, playwright.webkit]
browser = await random.choice(engines).launch()
```

## 🚨 Playwright避坑指南

### 1. **浏览器指纹避坑**

```python
# ❌ 错误做法 - 使用默认配置
browser = await playwright.chromium.launch()
context = await browser.new_context()

# ✅ 正确做法 - 完全随机化指纹
async def create_stealth_context(playwright):
    # 随机选择浏览器引擎
    engines = [
        (playwright.chromium, "chrome"),
        (playwright.firefox, "firefox"),
        (playwright.webkit, "safari")
    ]
    engine, engine_name = random.choice(engines)
    
    # 随机viewport
    viewports = [
        {'width': 1366, 'height': 768},   # 最常见
        {'width': 1920, 'height': 1080},  # 高端显示器
        {'width': 1440, 'height': 900},   # MacBook
        {'width': 1280, 'height': 720},   # 小屏幕
        {'width': 1536, 'height': 864},   # Windows缩放
    ]
    
    # 真实User-Agent池
    chrome_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    firefox_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
    ]
    
    # 根据引擎选择对应的User-Agent
    if engine_name == "firefox":
        user_agent = random.choice(firefox_agents)
    else:
        user_agent = random.choice(chrome_agents)
    
    # 启动浏览器（关键参数）
    browser = await engine.launch(
        headless=False,  # 显示浏览器，更真实
        args=[
            '--no-first-run',
            '--disable-blink-features=AutomationControlled',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-breakpad',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-default-apps',
            '--disable-dev-shm-usage',
            '--disable-domain-reliability',
            '--disable-extensions',
            '--disable-features=TranslateUI',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-renderer-backgrounding',
            '--disable-sync',
            '--disable-web-security',
            '--metrics-recording-only',
            '--no-crash-upload',
            '--no-default-browser-check',
            '--no-pings',
            '--password-store=basic',
            '--use-mock-keychain',
            '--disable-gpu-sandbox',
            '--disable-software-rasterizer'
        ]
    )
    
    # 创建上下文
    context = await browser.new_context(
        viewport=random.choice(viewports),
        user_agent=user_agent,
        locale='zh-CN',
        timezone_id='Asia/Shanghai',
        color_scheme='light',
        reduced_motion='no-preference',
        forced_colors='none',
        # 重要：模拟真实设备
        device_scale_factor=random.choice([1, 1.25, 1.5, 2]),
        is_mobile=False,
        has_touch=False,
        # 权限设置
        permissions=['geolocation', 'notifications'],
        geolocation={'latitude': 39.9042, 'longitude': 116.4074},  # 北京
    )
    
    return browser, context
```

### 2. **页面加载避坑**

```python
# ❌ 错误做法 - 立即操作
await page.goto(url)
await page.click("button")  # 可能页面还没完全加载

# ✅ 正确做法 - 智能等待
async def safe_page_load(page, url):
    """安全的页面加载"""
    # 1. 导航到页面
    await page.goto(url, wait_until='networkidle')  # 等待网络空闲
    
    # 2. 额外等待（模拟用户查看页面）
    await asyncio.sleep(random.uniform(2, 5))
    
    # 3. 模拟滚动（证明是真实用户）
    await page.evaluate("window.scrollBy(0, 100)")
    await asyncio.sleep(random.uniform(1, 3))
    
    # 4. 检查页面是否完全加载
    await page.wait_for_load_state('domcontentloaded')
    
    # 5. 等待关键元素
    try:
        await page.wait_for_selector('body', timeout=10000)
    except:
        pass
```

### 3. **元素操作避坑**

```python
# ❌ 错误做法 - 机械化操作
await page.click(selector)
await page.fill(selector, text)

# ✅ 正确做法 - 人类化操作
async def human_click(page, selector):
    """模拟人类点击"""
    # 1. 先滚动到元素可见
    await page.locator(selector).scroll_into_view_if_needed()
    
    # 2. 悬停一下（模拟查看）
    await page.hover(selector)
    await asyncio.sleep(random.uniform(0.2, 1))
    
    # 3. 点击
    await page.click(selector)
    
    # 4. 点击后等待
    await asyncio.sleep(random.uniform(0.5, 2))

async def human_type(page, selector, text):
    """模拟人类输入"""
    # 1. 聚焦到输入框
    await page.focus(selector)
    await asyncio.sleep(random.uniform(0.3, 1))
    
    # 2. 清空现有内容
    await page.fill(selector, "")
    
    # 3. 逐字输入
    for char in text:
        await page.type(selector, char, delay=random.uniform(50, 200))
        
        # 偶尔暂停（模拟思考）
        if random.random() < 0.1:
            await asyncio.sleep(random.uniform(0.5, 2))
    
    # 4. 输入完成后等待
    await asyncio.sleep(random.uniform(0.5, 1.5))
```

### 4. **文件上传避坑**

```python
# ❌ 错误做法 - 直接上传
await page.set_input_files("input[type=file]", file_path)

# ✅ 正确做法 - 模拟真实上传流程
async def realistic_file_upload(page, file_selector, file_path):
    """真实的文件上传流程"""
    
    # 1. 先悬停在上传区域（用户会先看看）
    upload_area = page.locator(file_selector).or_(page.locator(".upload-area, .dropzone"))
    await upload_area.first.hover()
    await asyncio.sleep(random.uniform(1, 3))
    
    # 2. 点击上传按钮（模拟用户点击）
    await upload_area.first.click()
    
    # 3. 模拟文件选择延迟（用户需要时间浏览文件）
    await asyncio.sleep(random.uniform(2, 8))
    
    # 4. 上传文件
    await page.set_input_files(file_selector, file_path)
    
    # 5. 等待上传完成（观察进度）
    await asyncio.sleep(random.uniform(3, 10))
    
    # 6. 可选：检查上传状态
    try:
        # 等待上传成功的标志
        await page.wait_for_selector(".upload-success, .file-uploaded", timeout=30000)
    except:
        # 如果没有明显的成功标志，就等待一段时间
        await asyncio.sleep(5)
```

### 5. **多标签页避坑**

```python
# ❌ 错误做法 - 频繁切换标签
for url in urls:
    page = await context.new_page()
    await page.goto(url)
    # 处理...
    await page.close()

# ✅ 正确做法 - 自然的标签页管理
async def natural_tab_management(context, urls):
    """自然的多标签页操作"""
    
    # 1. 一次只开少量标签页（像真实用户）
    max_tabs = random.randint(2, 4)
    active_pages = []
    
    for i, url in enumerate(urls):
        # 2. 控制标签页数量
        if len(active_pages) >= max_tabs:
            # 关闭最老的标签页
            old_page = active_pages.pop(0)
            await old_page.close()
            await asyncio.sleep(random.uniform(1, 3))
        
        # 3. 开新标签页
        page = await context.new_page()
        active_pages.append(page)
        
        # 4. 模拟用户切换延迟
        await asyncio.sleep(random.uniform(2, 5))
        
        # 5. 加载页面
        await page.goto(url, wait_until='networkidle')
        
        # 6. 模拟用户浏览行为
        await simulate_browsing_behavior(page)
    
    # 7. 清理剩余标签页
    for page in active_pages:
        await page.close()

async def simulate_browsing_behavior(page):
    """模拟真实浏览行为"""
    # 随机滚动
    for _ in range(random.randint(1, 3)):
        scroll_distance = random.randint(100, 500)
        await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
        await asyncio.sleep(random.uniform(1, 3))
    
    # 偶尔移动鼠标
    if random.random() < 0.7:
        viewport = page.viewport_size
        x = random.randint(0, viewport['width'])
        y = random.randint(0, viewport['height'])
        await page.mouse.move(x, y)
```

### 6. **会话管理避坑**

```python
# ❌ 错误做法 - 每次都重新登录
browser = await playwright.chromium.launch()
context = await browser.new_context()
# 每次都登录...

# ✅ 正确做法 - 智能会话管理
class SessionManager:
    def __init__(self, profile_dir):
        self.profile_dir = Path(profile_dir)
        self.state_file = self.profile_dir / "state.json"
    
    async def get_persistent_context(self, playwright):
        """获取持久化上下文"""
        
        # 1. 检查是否有有效的会话状态
        if await self.is_session_valid():
            # 恢复已有会话
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                viewport={'width': 1920, 'height': 1080}
            )
            return context
        else:
            # 创建新会话
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                viewport={'width': 1920, 'height': 1080}
            )
            return context
    
    async def is_session_valid(self):
        """检查会话是否有效"""
        if not self.state_file.exists():
            return False
        
        # 检查会话文件的修改时间
        mtime = self.state_file.stat().st_mtime
        age_hours = (time.time() - mtime) / 3600
        
        # 会话超过24小时就认为过期
        return age_hours < 24
    
    async def save_session_state(self, context):
        """保存会话状态"""
        await context.storage_state(path=str(self.state_file))
```

### 7. **检测信号避坑**

```python
# ✅ 主动监控检测信号
class AntiDetectionMonitor:
    def __init__(self):
        self.detection_patterns = [
            # 验证码相关
            "captcha", "recaptcha", "hcaptcha", "verification",
            # 封禁相关
            "blocked", "banned", "suspended", "restricted",
            # 机器人检测
            "robot", "bot", "automation", "suspicious",
            # 限制相关
            "rate limit", "too many requests", "quota exceeded",
            # 安全检查
            "security check", "unusual activity", "verify identity"
        ]
    
    async def check_page_for_detection(self, page):
        """检查页面是否有检测信号"""
        try:
            # 检查页面标题
            title = await page.title()
            for pattern in self.detection_patterns:
                if pattern.lower() in title.lower():
                    return f"检测信号在标题中: {pattern}"
            
            # 检查页面内容
            content = await page.content()
            for pattern in self.detection_patterns:
                if pattern.lower() in content.lower():
                    return f"检测信号在内容中: {pattern}"
            
            # 检查特定元素
            detection_selectors = [
                ".captcha", "#captcha", "[data-sitekey]",  # 验证码
                ".blocked", ".banned", ".error",          # 错误信息
                ".rate-limit", ".quota-exceeded"          # 限制信息
            ]
            
            for selector in detection_selectors:
                element = await page.query_selector(selector)
                if element:
                    return f"检测到元素: {selector}"
            
            return None
            
        except Exception as e:
            return f"检查出错: {str(e)}"
    
    async def handle_detection(self, page, detection_info):
        """处理检测情况"""
        print(f"🚨 检测到风险: {detection_info}")
        
        # 截图保存证据
        await page.screenshot(path=f"detection_{int(time.time())}.png")
        
        # 根据检测类型采取不同策略
        if "captcha" in detection_info.lower():
            # 遇到验证码，暂停更长时间
            print("⏰ 遇到验证码，暂停2小时...")
            await asyncio.sleep(7200)
        elif "rate limit" in detection_info.lower():
            # 遇到频率限制，暂停1小时
            print("⏰ 遇到频率限制，暂停1小时...")
            await asyncio.sleep(3600)
        elif "blocked" in detection_info.lower():
            # 账号被封，停止程序
            print("🛑 账号被封，停止程序")
            raise Exception("账号被封禁")
        else:
            # 其他情况，短暂暂停
            print("⏰ 检测到异常，暂停30分钟...")
            await asyncio.sleep(1800)
```

### 8. **网络请求避坑**

```python
# ✅ 模拟真实网络行为
async def setup_realistic_network(context):
    """设置真实的网络行为"""
    
    # 1. 随机网络延迟
    await context.route("**/*", lambda route: asyncio.create_task(
        add_network_delay(route)
    ))
    
    # 2. 模拟真实请求头
    await context.set_extra_http_headers({
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    })

async def add_network_delay(route):
    """添加网络延迟"""
    # 模拟真实网络延迟
    delay = random.uniform(0.1, 2.0)
    await asyncio.sleep(delay)
    await route.continue_()
```

## 🚀 Playwright最佳实践总结

### 1. **启动配置清单**
- [ ] 使用`launch_persistent_context`保持会话
- [ ] 随机化viewport和user-agent
- [ ] 设置合理的启动参数
- [ ] 配置真实的网络行为

### 2. **操作行为清单**
- [ ] 所有操作都要模拟人类行为
- [ ] 添加随机延迟和暂停
- [ ] 模拟鼠标移动和滚动
- [ ] 使用`wait_for_load_state`等待页面

### 3. **监控保护清单**
- [ ] 实时监控检测信号
- [ ] 定期保存会话状态
- [ ] 记录操作日志和截图
- [ ] 设置紧急停止机制

### 4. **频率控制清单**
- [ ] 严格控制请求频率
- [ ] 多账号轮换使用
- [ ] 避开网站高峰时段
- [ ] 监控账号状态变化

## ⚡ Playwright vs Selenium 性能对比

| 特性 | Playwright | Selenium + undetected |
|------|------------|---------------------|
| 反检测能力 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 启动速度 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 内存占用 | ⭐⭐⭐⭐ | ⭐⭐ |
| API简洁度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 异步支持 | ⭐⭐⭐⭐⭐ | ⭐ |
| 学习成本 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 社区支持 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**结论：Playwright在技术上全面领先，特别适合你的多账号反检测需求！** 🎭
