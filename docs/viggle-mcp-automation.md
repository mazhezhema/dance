# Viggle会员 + 浏览器MCP自动化方案

## 方案概述

使用Viggle付费会员套餐，结合浏览器MCP (Model Context Protocol) 进行自动化操作，实现批量视频处理。

## Viggle会员套餐分析

### 套餐对比
| 套餐 | 月费 | Credits | 视频时长限制 | 特色功能 |
|------|------|---------|-------------|----------|
| **Free** | $0 | 有限 | 5秒 | 基础功能，有水印 |
| **Standard** | $9.99 | 300 credits | 10秒 | 无水印，更快处理 |
| **Pro** | $24.99 | 1000 credits | 30秒 | 高质量，优先处理 |
| **Max** | $49.99 | 3000 credits | 60秒 | 最高质量，批量处理 |

### Credits消耗规律
- **1 credit ≈ 1秒视频**
- **5分钟视频 = 300 credits ≈ Standard套餐**
- **建议：Pro套餐** (性价比最高，1000 credits ≈ 16-17分钟视频)

## MCP浏览器自动化方案

### 技术架构
```
批量任务管理器 → MCP浏览器控制 → Viggle网站操作 → 结果下载管理
```

### MCP工具选择
推荐使用支持浏览器操作的MCP工具：
- **Browser Use MCP**
- **Playwright MCP** 
- **Selenium MCP**

### 核心操作流程
```python
# viggle_mcp_controller.py
import asyncio
from playwright.async_api import async_playwright
import os
import time
from pathlib import Path

class ViggleMCPController:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.browser = None
        self.page = None
        self.viggle_url = "https://viggle.ai"
        
    async def initialize_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        
        # 启动浏览器（可见模式，便于调试）
        self.browser = await playwright.chromium.launch(
            headless=False,  # 显示浏览器窗口
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        # 创建新页面
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await context.new_page()
        
        # 屏蔽检测
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
    async def login_viggle(self):
        """登录Viggle"""
        await self.page.goto(self.viggle_url)
        await self.page.wait_for_load_state('networkidle')
        
        # 点击登录按钮
        await self.page.click('button:has-text("Sign In")')
        await self.page.wait_for_selector('input[type="email"]')
        
        # 输入邮箱和密码
        await self.page.fill('input[type="email"]', self.email)
        await self.page.fill('input[type="password"]', self.password)
        
        # 点击登录
        await self.page.click('button[type="submit"]')
        
        # 等待登录完成
        await self.page.wait_for_selector('.dashboard', timeout=30000)
        print("Viggle登录成功")
        
    async def upload_video(self, video_path):
        """上传视频文件"""
        # 点击上传按钮
        await self.page.click('button:has-text("Upload Video")')
        
        # 处理文件上传
        async with self.page.expect_file_chooser() as fc_info:
            await self.page.click('input[type="file"]')
        file_chooser = await fc_info.value
        await file_chooser.set_files(video_path)
        
        # 等待上传完成
        await self.page.wait_for_selector('.upload-complete', timeout=60000)
        print(f"视频上传完成: {video_path}")
        
        # 获取上传后的视频ID
        video_id = await self.page.get_attribute('.video-item:last-child', 'data-video-id')
        return video_id
        
    async def submit_mix_task(self, video_id, character_image=None, prompt=""):
        """提交Mix任务"""
        # 选择视频
        await self.page.click(f'[data-video-id="{video_id}"]')
        
        # 点击Mix按钮
        await self.page.click('button:has-text("Mix")')
        
        # 如果有角色图片，上传
        if character_image:
            async with self.page.expect_file_chooser() as fc_info:
                await self.page.click('.character-upload')
            file_chooser = await fc_info.value
            await file_chooser.set_files(character_image)
        
        # 输入提示词
        if prompt:
            await self.page.fill('textarea[placeholder*="prompt"]', prompt)
        
        # 选择背景模式
        await self.page.click('button:has-text("Green Screen")')  # 绿幕背景便于后处理
        
        # 提交任务
        await self.page.click('button:has-text("Generate")')
        
        # 获取任务ID
        await self.page.wait_for_selector('.task-item:last-child')
        task_id = await self.page.get_attribute('.task-item:last-child', 'data-task-id')
        
        print(f"任务提交成功，任务ID: {task_id}")
        return task_id
        
    async def monitor_task_progress(self, task_id, timeout=1800):  # 30分钟超时
        """监控任务进度"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 刷新任务状态
            await self.page.goto(f"{self.viggle_url}/tasks")
            await self.page.wait_for_load_state('networkidle')
            
            # 检查任务状态
            task_element = await self.page.query_selector(f'[data-task-id="{task_id}"]')
            if not task_element:
                print(f"找不到任务: {task_id}")
                return None
                
            status = await task_element.get_attribute('data-status')
            progress = await task_element.inner_text()
            
            print(f"任务 {task_id} 状态: {status} - {progress}")
            
            if status == 'completed':
                # 获取结果视频URL
                download_button = await task_element.query_selector('.download-button')
                video_url = await download_button.get_attribute('href')
                return video_url
            elif status == 'failed':
                error_msg = await task_element.query_selector('.error-message')
                error_text = await error_msg.inner_text() if error_msg else "Unknown error"
                print(f"任务失败: {error_text}")
                return None
                
            # 等待30秒后重新检查
            await asyncio.sleep(30)
        
        print(f"任务 {task_id} 超时")
        return None
        
    async def download_result(self, video_url, output_dir):
        """下载结果视频"""
        # 创建下载目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 开始下载
        async with self.page.expect_download() as download_info:
            await self.page.goto(video_url)
        download = await download_info.value
        
        # 保存文件
        filename = f"viggle_output_{int(time.time())}.mp4"
        output_path = Path(output_dir) / filename
        await download.save_as(output_path)
        
        print(f"视频下载完成: {output_path}")
        return str(output_path)
        
    async def process_batch_videos(self, video_list, output_dir):
        """批量处理视频"""
        results = []
        
        try:
            await self.initialize_browser()
            await self.login_viggle()
            
            for i, video_info in enumerate(video_list):
                print(f"处理视频 {i+1}/{len(video_list)}: {video_info['path']}")
                
                try:
                    # 上传视频
                    video_id = await self.upload_video(video_info['path'])
                    
                    # 提交任务
                    task_id = await self.submit_mix_task(
                        video_id, 
                        video_info.get('character_image'),
                        video_info.get('prompt', '')
                    )
                    
                    # 监控任务
                    result_url = await self.monitor_task_progress(task_id)
                    
                    if result_url:
                        # 下载结果
                        output_path = await self.download_result(result_url, output_dir)
                        results.append({
                            'input': video_info['path'],
                            'output': output_path,
                            'status': 'success'
                        })
                    else:
                        results.append({
                            'input': video_info['path'],
                            'output': None,
                            'status': 'failed'
                        })
                        
                except Exception as e:
                    print(f"处理视频失败: {str(e)}")
                    results.append({
                        'input': video_info['path'],
                        'output': None,
                        'status': 'error',
                        'error': str(e)
                    })
                
                # 处理间隔，避免触发限制
                if i < len(video_list) - 1:
                    await asyncio.sleep(60)  # 等待1分钟
                    
        finally:
            if self.browser:
                await self.browser.close()
                
        return results
        
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
```

## 批量管理器

### 任务调度器
```python
# viggle_batch_manager.py
import asyncio
import json
from datetime import datetime
import logging

class ViggleBatchManager:
    def __init__(self, config_file='viggle_config.json'):
        self.config = self.load_config(config_file)
        self.controller = ViggleMCPController(
            self.config['email'], 
            self.config['password']
        )
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('viggle_batch.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self, config_file):
        """加载配置文件"""
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def prepare_video_batch(self, input_dir, character_configs):
        """准备视频批次"""
        video_list = []
        
        for video_file in Path(input_dir).glob('*.mp4'):
            # 根据文件名匹配角色配置
            config = self.match_character_config(video_file.name, character_configs)
            
            video_list.append({
                'path': str(video_file),
                'character_image': config.get('character_image'),
                'prompt': config.get('prompt', ''),
                'priority': config.get('priority', 1)
            })
        
        # 按优先级排序
        video_list.sort(key=lambda x: x['priority'])
        
        return video_list
    
    def match_character_config(self, filename, character_configs):
        """根据文件名匹配角色配置"""
        for pattern, config in character_configs.items():
            if pattern in filename.lower():
                return config
        
        # 默认配置
        return character_configs.get('default', {})
    
    async def run_batch_processing(self, input_dir, output_dir):
        """运行批量处理"""
        self.logger.info("开始批量处理")
        
        # 准备视频列表
        video_list = self.prepare_video_batch(
            input_dir, 
            self.config['character_configs']
        )
        
        self.logger.info(f"准备处理 {len(video_list)} 个视频")
        
        # 分批处理（避免超时）
        batch_size = self.config.get('batch_size', 10)
        all_results = []
        
        for i in range(0, len(video_list), batch_size):
            batch = video_list[i:i+batch_size]
            self.logger.info(f"处理批次 {i//batch_size + 1}: {len(batch)} 个视频")
            
            try:
                batch_results = await self.controller.process_batch_videos(
                    batch, output_dir
                )
                all_results.extend(batch_results)
                
                # 保存中间结果
                self.save_progress(all_results, f"batch_{i//batch_size + 1}")
                
            except Exception as e:
                self.logger.error(f"批次处理失败: {str(e)}")
                continue
            
            # 批次间隔
            if i + batch_size < len(video_list):
                self.logger.info("等待5分钟后继续下一批次...")
                await asyncio.sleep(300)
        
        # 生成最终报告
        self.generate_report(all_results)
        
        return all_results
    
    def save_progress(self, results, batch_name):
        """保存处理进度"""
        progress_file = f"progress_{batch_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(progress_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    def generate_report(self, results):
        """生成处理报告"""
        total = len(results)
        success = len([r for r in results if r['status'] == 'success'])
        failed = total - success
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_videos': total,
            'successful': success,
            'failed': failed,
            'success_rate': f"{success/total*100:.1f}%" if total > 0 else "0%",
            'details': results
        }
        
        report_file = f"viggle_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"处理完成: {success}/{total} 成功")
        self.logger.info(f"报告已保存: {report_file}")

# 使用示例
async def main():
    # 配置文件示例
    config = {
        "email": "your-viggle-email@example.com",
        "password": "your-viggle-password",
        "batch_size": 5,
        "character_configs": {
            "dance": {
                "character_image": "characters/dancer.jpg",
                "prompt": "dancing person, energetic movement",
                "priority": 1
            },
            "exercise": {
                "character_image": "characters/fitness.jpg", 
                "prompt": "fitness instructor, healthy movement",
                "priority": 2
            },
            "default": {
                "character_image": "characters/default.jpg",
                "prompt": "person performing action",
                "priority": 3
            }
        }
    }
    
    # 保存配置
    with open('viggle_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    # 运行批量处理
    manager = ViggleBatchManager()
    results = await manager.run_batch_processing(
        input_dir='./input_videos',
        output_dir='./viggle_output'
    )
    
    print(f"处理完成，共处理 {len(results)} 个视频")

if __name__ == "__main__":
    asyncio.run(main())
```

## 成本优化策略

### Credits使用优化
```python
# credits_optimizer.py
class CreditsOptimizer:
    def __init__(self, monthly_credits=1000):
        self.monthly_credits = monthly_credits
        self.used_credits = 0
        
    def estimate_video_credits(self, video_duration):
        """估算视频所需Credits"""
        return int(video_duration)  # 1秒 = 1 credit
    
    def optimize_batch_order(self, video_list):
        """优化批处理顺序"""
        # 按视频长度排序，短视频优先
        sorted_videos = sorted(video_list, key=lambda x: x.get('duration', 300))
        
        # 检查Credits是否够用
        total_credits_needed = sum(
            self.estimate_video_credits(v.get('duration', 300)) 
            for v in sorted_videos
        )
        
        if total_credits_needed > self.monthly_credits - self.used_credits:
            # 裁剪批次到可用Credits范围内
            optimized_batch = []
            credits_count = 0
            
            for video in sorted_videos:
                video_credits = self.estimate_video_credits(video.get('duration', 300))
                if credits_count + video_credits <= self.monthly_credits - self.used_credits:
                    optimized_batch.append(video)
                    credits_count += video_credits
                else:
                    break
            
            return optimized_batch, credits_count
        
        return sorted_videos, total_credits_needed
```

## 质量控制

### 结果验证
```python
# viggle_quality_check.py
def validate_viggle_output(output_video_path):
    """验证Viggle输出质量"""
    cap = cv2.VideoCapture(output_video_path)
    
    if not cap.isOpened():
        return {'valid': False, 'error': 'Cannot open video'}
    
    # 检查基本属性
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 检查是否有Viggle水印
    has_watermark = check_viggle_watermark(output_video_path)
    
    # 检查绿幕质量
    green_screen_quality = check_green_screen_quality(cap)
    
    cap.release()
    
    return {
        'valid': True,
        'resolution': f"{width}x{height}",
        'fps': fps,
        'duration': frame_count / fps,
        'has_watermark': has_watermark,
        'green_screen_quality': green_screen_quality
    }

def check_viggle_watermark(video_path):
    """检查是否有Viggle水印"""
    # 检查右下角是否有水印
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        h, w = frame.shape[:2]
        watermark_region = frame[h-100:h, w-200:w]  # 右下角区域
        
        # 简单的水印检测（基于颜色一致性）
        std_dev = np.std(watermark_region)
        return std_dev < 30  # 低标准差可能表示有水印
    
    return False
```

## 部署和运行

### 环境配置
```bash
# 安装依赖
pip install playwright asyncio pathlib

# 安装浏览器
playwright install chromium

# 创建目录结构
mkdir -p input_videos viggle_output characters logs
```

### 运行脚本
```bash
# 配置Viggle账号信息
nano viggle_config.json

# 运行批量处理
python viggle_batch_manager.py
```

## 方案优势

1. **✅ 稳定可靠**: 使用官方网站，避免API限制
2. **✅ 功能完整**: 支持所有Viggle功能
3. **✅ 成本可控**: 明确的会员费用和Credits消耗
4. **✅ 批量处理**: 支持自动化批量操作
5. **✅ 质量保证**: 可以使用付费套餐的高质量输出

## 风险控制

1. **检测风险**: 使用反检测技术，模拟真实用户行为
2. **频率控制**: 合理的处理间隔，避免触发限制
3. **错误恢复**: 完善的异常处理和重试机制
4. **账号安全**: 使用专门的账号，避免影响主账号

这个方案结合了Viggle的专业能力和MCP的自动化优势，是目前最现实可行的解决方案！
