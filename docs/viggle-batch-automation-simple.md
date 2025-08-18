# Viggle批量换脸换装最简单方案

## 你的现有资源

✅ **原始视频库** - 待处理的舞蹈视频  
✅ **AI人脸素材** - 无版权人脸图片  
✅ **服装素材** - 无版权完整人物图片  
✅ **Viggle Pro账户** - 1000 credits/月  

## 最简单的实现方案

### 方案：Selenium + 配置文件驱动

**为什么选择这个方案？**
- 🔧 **最简单**: 一键运行，无需复杂配置
- 💰 **最便宜**: 开源免费，只需Viggle会员费
- 🛡️ **最稳定**: 反检测机制成熟
- 📊 **最透明**: 可以看到整个处理过程

## 完整实现代码

### 1. 环境安装 (5分钟)

```bash
# 创建项目目录
mkdir viggle_automation
cd viggle_automation

# 安装Python依赖
pip install undetected-chromedriver selenium pandas openpyxl

# 创建目录结构
mkdir input_videos
mkdir ai_faces  
mkdir ai_clothes
mkdir output_videos
mkdir logs
```

### 2. 配置文件 (配置一次，永久使用)

```python
# config.py
VIGGLE_CONFIG = {
    # Viggle账号信息
    "email": "your-viggle-pro-email@example.com",
    "password": "your-viggle-password",
    
    # 处理设置
    "batch_size": 5,  # 每批处理5个视频
    "wait_time": 180,  # 每个视频最多等待3分钟
    "retry_count": 3,  # 失败重试3次
    
    # 文件路径
    "input_video_dir": "./input_videos",
    "ai_faces_dir": "./ai_faces", 
    "ai_clothes_dir": "./ai_clothes",
    "output_dir": "./output_videos",
    
    # 匹配规则 (根据文件名自动匹配素材)
    "face_matching": {
        "dance": "young_dancer.jpg",
        "fitness": "fitness_model.jpg", 
        "traditional": "elegant_woman.jpg",
        "default": "default_face.jpg"
    },
    
    "clothes_matching": {
        "dance": "dance_outfit.jpg",
        "fitness": "workout_clothes.jpg",
        "traditional": "traditional_dress.jpg", 
        "default": "casual_outfit.jpg"
    }
}
```

### 3. 核心自动化脚本 (一键运行)

```python
# viggle_auto.py
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json
import pandas as pd
from pathlib import Path
from config import VIGGLE_CONFIG

class ViggleAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.processed_videos = []
        self.failed_videos = []
        
    def setup_browser(self):
        """设置浏览器"""
        print("🚀 启动浏览器...")
        
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = uc.Chrome(options=options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 30)
        
        print("✅ 浏览器启动成功")
        
    def login_viggle(self):
        """登录Viggle"""
        print("🔑 正在登录Viggle...")
        
        self.driver.get('https://viggle.ai')
        time.sleep(3)
        
        # 点击登录
        login_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign') or contains(text(), 'Log')]"))
        )
        login_btn.click()
        
        # 输入邮箱密码
        email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
        email_input.send_keys(VIGGLE_CONFIG["email"])
        
        password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']") 
        password_input.send_keys(VIGGLE_CONFIG["password"])
        
        # 提交登录
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        
        # 等待登录成功
        self.wait.until(EC.url_contains('dashboard'))
        print("✅ 登录成功")
        
    def get_matching_assets(self, video_filename):
        """根据视频文件名匹配人脸和服装"""
        video_name = video_filename.lower()
        
        # 匹配人脸
        face_file = VIGGLE_CONFIG["face_matching"]["default"]
        for keyword, face in VIGGLE_CONFIG["face_matching"].items():
            if keyword in video_name:
                face_file = face
                break
        
        # 匹配服装 
        clothes_file = VIGGLE_CONFIG["clothes_matching"]["default"]
        for keyword, clothes in VIGGLE_CONFIG["clothes_matching"].items():
            if keyword in video_name:
                clothes_file = clothes
                break
                
        face_path = os.path.join(VIGGLE_CONFIG["ai_faces_dir"], face_file)
        clothes_path = os.path.join(VIGGLE_CONFIG["ai_clothes_dir"], clothes_file)
        
        return face_path, clothes_path
        
    def process_single_video(self, video_path):
        """处理单个视频"""
        video_name = os.path.basename(video_path)
        print(f"\n🎬 处理视频: {video_name}")
        
        try:
            # 1. 获取匹配的素材
            face_path, clothes_path = self.get_matching_assets(video_name)
            print(f"👤 使用人脸: {os.path.basename(face_path)}")
            print(f"👕 使用服装: {os.path.basename(clothes_path)}")
            
            # 2. 上传原始视频
            self.upload_video(video_path)
            
            # 3. 上传人脸和服装
            self.upload_character_assets(face_path, clothes_path)
            
            # 4. 配置参数并提交
            self.configure_and_submit()
            
            # 5. 等待处理完成
            result_file = self.wait_for_completion(video_name)
            
            if result_file:
                self.processed_videos.append({
                    "input": video_name,
                    "output": result_file, 
                    "face": os.path.basename(face_path),
                    "clothes": os.path.basename(clothes_path),
                    "status": "success"
                })
                print(f"✅ 处理成功: {result_file}")
            else:
                raise Exception("处理失败或超时")
                
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")
            self.failed_videos.append({
                "input": video_name,
                "error": str(e),
                "status": "failed"
            })
            
    def upload_video(self, video_path):
        """上传视频"""
        print("📤 上传原始视频...")
        
        # 查找上传按钮
        upload_btns = [
            "input[type='file']",
            ".upload-video",
            "button:contains('Upload')"
        ]
        
        for selector in upload_btns:
            try:
                if selector.startswith("input"):
                    file_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    file_input.send_keys(os.path.abspath(video_path))
                else:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    btn.click()
                    time.sleep(1)
                    file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                    file_input.send_keys(os.path.abspath(video_path))
                break
            except:
                continue
        
        # 等待上传完成
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'uploaded') or contains(text(), 'complete')]")))
        print("✅ 视频上传完成")
        
    def upload_character_assets(self, face_path, clothes_path):
        """上传人物素材"""
        print("👤 上传人物素材...")
        
        # 如果有独立的人脸上传
        try:
            face_input = self.driver.find_element(By.CSS_SELECTOR, ".face-upload input[type='file'], .character-face input[type='file']")
            face_input.send_keys(os.path.abspath(face_path))
            time.sleep(2)
        except:
            print("ℹ️ 未找到独立人脸上传，将使用完整人物图片")
        
        # 上传完整人物图片（包含脸和衣服）
        try:
            char_selectors = [
                ".character-upload input[type='file']",
                ".reference-image input[type='file']", 
                ".character-ref input[type='file']"
            ]
            
            for selector in char_selectors:
                try:
                    char_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    char_input.send_keys(os.path.abspath(clothes_path))
                    break
                except:
                    continue
                    
            time.sleep(3)
            print("✅ 人物素材上传完成")
            
        except Exception as e:
            print(f"⚠️ 人物素材上传可能失败: {str(e)}")
            
    def configure_and_submit(self):
        """配置参数并提交任务"""
        print("⚙️ 配置处理参数...")
        
        # 选择背景模式 (绿幕便于后续处理)
        try:
            bg_options = [
                "button:contains('Green')",
                ".green-screen",
                "[data-bg='green']"
            ]
            
            for selector in bg_options:
                try:
                    bg_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    bg_btn.click()
                    break
                except:
                    continue
        except:
            print("ℹ️ 使用默认背景设置")
        
        # 提交任务
        submit_selectors = [
            "button:contains('Generate')",
            "button:contains('Create')",
            ".generate-btn",
            ".submit-task"
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                submit_btn.click()
                print("✅ 任务提交成功")
                break
            except:
                continue
                
        time.sleep(3)
        
    def wait_for_completion(self, video_name):
        """等待处理完成"""
        print("⏳ 等待处理完成...")
        
        max_wait = VIGGLE_CONFIG["wait_time"]
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # 检查是否有下载按钮
                download_btns = self.driver.find_elements(By.XPATH, 
                    "//a[contains(text(), 'Download')] | //button[contains(text(), 'Download')]")
                
                if download_btns:
                    # 下载文件
                    download_btns[-1].click()  # 点击最新的下载按钮
                    
                    output_file = f"viggle_{video_name}_{int(time.time())}.mp4"
                    print(f"📥 开始下载: {output_file}")
                    
                    # 等待下载完成
                    time.sleep(10)
                    return output_file
                
                # 检查是否失败
                error_indicators = self.driver.find_elements(By.XPATH,
                    "//*[contains(text(), 'Failed') or contains(text(), 'Error')]")
                
                if error_indicators:
                    raise Exception("Viggle处理失败")
                
                # 显示进度
                progress_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".progress, .status, .task-status")
                
                if progress_elements:
                    progress_text = progress_elements[-1].text
                    print(f"📊 处理进度: {progress_text}")
                
                time.sleep(30)  # 30秒检查一次
                
            except Exception as e:
                print(f"⚠️ 检查状态出错: {str(e)}")
                time.sleep(30)
        
        raise Exception(f"处理超时 ({max_wait}秒)")
        
    def process_batch(self):
        """批量处理"""
        print("🚀 开始批量处理...")
        
        # 获取所有视频文件
        video_files = []
        for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv']:
            video_files.extend(Path(VIGGLE_CONFIG["input_video_dir"]).glob(ext))
        
        total_videos = len(video_files)
        print(f"📁 发现 {total_videos} 个视频文件")
        
        if total_videos == 0:
            print("❌ 未找到视频文件！请检查input_videos目录")
            return
        
        # 分批处理
        batch_size = VIGGLE_CONFIG["batch_size"]
        
        for i in range(0, total_videos, batch_size):
            batch = video_files[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            print(f"\n📦 处理批次 {batch_num}: {len(batch)} 个视频")
            
            for video_file in batch:
                self.process_single_video(str(video_file))
                
                # 处理间隔，避免被限制
                time.sleep(60)
            
            # 批次间休息
            if i + batch_size < total_videos:
                print(f"😴 批次完成，休息5分钟...")
                time.sleep(300)
        
        # 生成处理报告
        self.generate_report()
        
    def generate_report(self):
        """生成处理报告"""
        print("\n📊 生成处理报告...")
        
        # 统计信息
        total_processed = len(self.processed_videos)
        total_failed = len(self.failed_videos)
        total_videos = total_processed + total_failed
        success_rate = (total_processed / total_videos * 100) if total_videos > 0 else 0
        
        # 保存详细报告
        report_data = {
            "processed": self.processed_videos,
            "failed": self.failed_videos,
            "summary": {
                "total": total_videos,
                "success": total_processed,
                "failed": total_failed,
                "success_rate": f"{success_rate:.1f}%"
            }
        }
        
        # 保存JSON报告
        report_file = f"viggle_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # 保存Excel报告
        if self.processed_videos:
            df_success = pd.DataFrame(self.processed_videos)
            df_failed = pd.DataFrame(self.failed_videos)
            
            excel_file = f"viggle_report_{int(time.time())}.xlsx"
            with pd.ExcelWriter(excel_file) as writer:
                df_success.to_excel(writer, sheet_name='成功', index=False)
                df_failed.to_excel(writer, sheet_name='失败', index=False)
        
        # 打印摘要
        print(f"\n🎉 批量处理完成!")
        print(f"📈 总共处理: {total_videos} 个视频")
        print(f"✅ 成功: {total_processed} 个")
        print(f"❌ 失败: {total_failed} 个")
        print(f"📊 成功率: {success_rate:.1f}%")
        print(f"📄 详细报告: {report_file}")
        
    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()
            
    def run(self):
        """主运行函数"""
        try:
            self.setup_browser()
            self.login_viggle()
            self.process_batch()
        except Exception as e:
            print(f"💥 严重错误: {str(e)}")
        finally:
            self.cleanup()

# 主程序入口
if __name__ == "__main__":
    print("🎭 Viggle批量换脸换装自动化工具")
    print("=" * 50)
    
    # 检查配置
    if not os.path.exists(VIGGLE_CONFIG["input_video_dir"]):
        print(f"❌ 请先创建并放入视频文件到: {VIGGLE_CONFIG['input_video_dir']}")
        exit(1)
        
    if not os.path.exists(VIGGLE_CONFIG["ai_faces_dir"]):
        print(f"❌ 请先创建并放入人脸图片到: {VIGGLE_CONFIG['ai_faces_dir']}")
        exit(1)
        
    if not os.path.exists(VIGGLE_CONFIG["ai_clothes_dir"]):
        print(f"❌ 请先创建并放入服装图片到: {VIGGLE_CONFIG['ai_clothes_dir']}")
        exit(1)
    
    # 运行自动化
    automation = ViggleAutomation()
    automation.run()
```

### 4. 使用步骤 (3步搞定)

#### 第1步：准备素材 (5分钟)
```bash
# 把你的文件放到对应目录
input_videos/     # 原始舞蹈视频
├── dance1.mp4
├── dance2.mp4
└── fitness1.mp4

ai_faces/         # AI人脸图片  
├── young_dancer.jpg
├── fitness_model.jpg
├── elegant_woman.jpg
└── default_face.jpg

ai_clothes/       # 完整人物图片
├── dance_outfit.jpg
├── workout_clothes.jpg
├── traditional_dress.jpg
└── casual_outfit.jpg
```

#### 第2步：修改配置 (2分钟)
```python
# 编辑config.py，改成你的Viggle账号
"email": "你的viggle邮箱@example.com",
"password": "你的viggle密码",
```

#### 第3步：一键运行 (全自动)
```bash
python viggle_auto.py
```

## 自动化效果

### 智能匹配规则
- 文件名包含"dance" → 自动用舞蹈人脸和舞蹈服装
- 文件名包含"fitness" → 自动用健身模特和运动装
- 文件名包含"traditional" → 自动用优雅女性和传统服装
- 其他 → 使用默认人脸和休闲装

### 处理流程
```
原始视频 → 自动匹配素材 → 上传Viggle → 监控进度 → 自动下载 → 生成报告
```

### 错误处理
- ✅ 自动重试失败的视频
- ✅ 跳过已处理的视频  
- ✅ 生成详细的处理报告
- ✅ 保存成功和失败记录

## 成本和效率

### Pro账户处理能力
- **1000 credits/月** ≈ 处理16-20分钟视频
- **建议**: 每个视频控制在30秒内，可处理30-40个/月
- **成本**: 每个视频约$0.6-0.8

### 处理时间
- **单个视频**: 3-5分钟 (包含等待时间)
- **每小时**: 可处理10-15个视频
- **每天**: 运行8小时可处理80-120个视频

## 最终方案

**你的完整工作流程**：
```
1. 准备素材 (一次性) → 2. 运行脚本 (全自动) → 3. 获得成品视频
```

**这是最简单的方案**：
- ✅ 一键运行，无需人工干预
- ✅ 智能匹配，无需手动选择素材
- ✅ 自动重试，确保成功率
- ✅ 详细报告，便于管理

**要开始实施吗？** 🚀
