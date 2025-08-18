# Viggle + 本地GPU详细流程与最佳实践指南

## 完整工作流程

### 第一步：原始视频准备

#### 1.1 视频预处理
```bash
# 检查原始视频规格
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4

# 标准化预处理（如果需要）
ffmpeg -i input.mp4 -vf "scale=720:720:force_original_aspect_ratio=decrease,pad=720:720:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k preprocessed.mp4
```

#### 1.2 视频质量评估
```python
# 原始视频质量检查
def check_input_video(video_path):
    cap = cv2.VideoCapture(video_path)
    
    # 获取基本信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    
    # 检查人物清晰度（前10秒）
    clarity_scores = []
    for i in range(min(int(fps * 10), frame_count)):
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            clarity = cv2.Laplacian(gray, cv2.CV_64F).var()
            clarity_scores.append(clarity)
    
    cap.release()
    
    avg_clarity = np.mean(clarity_scores)
    
    return {
        'resolution': f"{width}x{height}",
        'fps': fps,
        'duration': duration,
        'clarity_score': avg_clarity,
        'recommendation': 'good' if avg_clarity > 100 else 'poor',
        'suitable_for_viggle': avg_clarity > 50 and duration <= 600  # 10分钟限制
    }
```

### 第二步：Viggle API处理

#### 2.1 API调用最佳实践
```javascript
// viggle_client.js
class ViggleClient {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://api.viggle.ai';
        this.retryCount = 3;
        this.retryDelay = 5000; // 5秒
    }
    
    async submitVideo(videoConfig) {
        const payload = {
            video_url: videoConfig.videoUrl,
            character: {
                style: videoConfig.characterStyle || 'realistic',
                age: videoConfig.age || 'adult',
                gender: videoConfig.gender || 'auto'
            },
            motion: {
                preserve_original: true,
                enhance_quality: true
            },
            output: {
                resolution: '1080p',
                format: 'mp4',
                watermark: false  // 需要付费套餐
            }
        };
        
        for (let attempt = 1; attempt <= this.retryCount; attempt++) {
            try {
                const response = await fetch(`${this.baseUrl}/generate`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    console.log(`Task submitted: ${result.task_id}`);
                    return result;
                }
                
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                
            } catch (error) {
                console.error(`Attempt ${attempt} failed:`, error.message);
                if (attempt < this.retryCount) {
                    await this.sleep(this.retryDelay * attempt);
                } else {
                    throw error;
                }
            }
        }
    }
    
    async pollTaskStatus(taskId, maxWaitTime = 3600) { // 1小时超时
        const startTime = Date.now();
        const pollInterval = 30000; // 30秒检查一次
        
        while (Date.now() - startTime < maxWaitTime * 1000) {
            try {
                const response = await fetch(`${this.baseUrl}/task/${taskId}`, {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`
                    }
                });
                
                const status = await response.json();
                
                console.log(`Task ${taskId} status: ${status.state} (${status.progress || 0}%)`);
                
                if (status.state === 'completed') {
                    return {
                        success: true,
                        outputUrl: status.output_url,
                        metadata: status.metadata
                    };
                } else if (status.state === 'failed') {
                    return {
                        success: false,
                        error: status.error_message
                    };
                }
                
                await this.sleep(pollInterval);
                
            } catch (error) {
                console.error('Polling error:', error.message);
                await this.sleep(pollInterval);
            }
        }
        
        throw new Error('Task timeout');
    }
    
    async downloadResult(outputUrl, localPath) {
        const response = await fetch(outputUrl);
        if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
        }
        
        const buffer = await response.arrayBuffer();
        fs.writeFileSync(localPath, Buffer.from(buffer));
        
        console.log(`Downloaded to: ${localPath}`);
        return localPath;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

#### 2.2 Credits使用优化
```javascript
// credits_manager.js
class CreditsManager {
    constructor(viggleClient) {
        this.client = viggleClient;
        this.dailyLimit = 50; // 每日处理限制
        this.processedToday = 0;
    }
    
    async checkCreditsBalance() {
        const response = await fetch(`${this.client.baseUrl}/account/credits`, {
            headers: {
                'Authorization': `Bearer ${this.client.apiKey}`
            }
        });
        
        const data = await response.json();
        return data.remaining_credits;
    }
    
    estimateCreditsNeeded(videoDuration) {
        // 1 credit ≈ 15秒
        return Math.ceil(videoDuration / 15);
    }
    
    async canProcessVideo(videoDuration) {
        const creditsNeeded = this.estimateCreditsNeeded(videoDuration);
        const availableCredits = await this.checkCreditsBalance();
        
        return {
            canProcess: availableCredits >= creditsNeeded && this.processedToday < this.dailyLimit,
            creditsNeeded,
            availableCredits,
            dailyRemaining: this.dailyLimit - this.processedToday
        };
    }
}
```

### 第三步：本地GPU预处理

#### 3.1 显存管理
```python
# gpu_manager.py
import torch
import psutil
import GPUtil
import time

class GPUManager:
    def __init__(self):
        self.max_concurrent_tasks = 2
        self.current_tasks = 0
        self.memory_threshold = 0.8  # 80%显存使用率阈值
        
    def check_gpu_availability(self):
        """检查GPU可用性"""
        gpus = GPUtil.getGPUs()
        if not gpus:
            return False, "No GPU found"
            
        gpu = gpus[0]  # 使用第一块GPU
        
        memory_usage = gpu.memoryUsed / gpu.memoryTotal
        temperature = gpu.temperature
        
        if memory_usage > self.memory_threshold:
            return False, f"GPU memory usage too high: {memory_usage:.1%}"
            
        if temperature > 85:  # 温度过高
            return False, f"GPU temperature too high: {temperature}°C"
            
        if self.current_tasks >= self.max_concurrent_tasks:
            return False, f"Max concurrent tasks reached: {self.current_tasks}"
            
        return True, "GPU available"
    
    def allocate_task(self):
        """分配任务"""
        available, message = self.check_gpu_availability()
        if available:
            self.current_tasks += 1
            return True
        return False
    
    def release_task(self):
        """释放任务"""
        self.current_tasks = max(0, self.current_tasks - 1)
        
    def cleanup_gpu_memory(self):
        """清理GPU内存"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
```

#### 3.2 超分辨率处理
```bash
# super_resolution.sh
#!/bin/bash

super_resolution_process() {
    local input_video="$1"
    local output_video="$2"
    local scale_factor="${3:-2}"  # 默认2倍放大
    
    local temp_dir="temp_$(basename "$input_video" .mp4)_$$"
    mkdir -p "$temp_dir"
    
    echo "开始超分辨率处理: $input_video"
    
    # 1. 视频转帧（优化：只处理关键帧）
    ffmpeg -i "$input_video" -vf "select=not(mod(n\\,3))" \
        "$temp_dir/frame_%08d.png" -y
    
    # 2. 超分处理
    ./tools/realesrgan-ncnn-vulkan \
        -i "$temp_dir" \
        -o "${temp_dir}_up" \
        -s $scale_factor \
        -n realesrgan-x4plus \
        -f png \
        -j 1:1:1  # GPU线程配置
    
    # 3. 帧间插值（补充跳过的帧）
    python scripts/frame_interpolation.py \
        --input "${temp_dir}_up" \
        --output "${temp_dir}_interpolated" \
        --factor 3
    
    # 4. 重建视频
    ffmpeg -r 30 -i "${temp_dir}_interpolated/frame_%08d.png" \
        -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
        "$output_video" -y
    
    # 清理
    rm -rf "$temp_dir" "${temp_dir}_up" "${temp_dir}_interpolated"
    
    echo "超分辨率处理完成: $output_video"
}
```

### 第四步：视频抠像处理

#### 4.1 RVM抠像最佳实践
```python
# rvm_processor.py
import torch
import cv2
import numpy as np
from torch.utils.data import DataLoader
import torchvision.transforms as transforms

class RVMProcessor:
    def __init__(self, model_path='rvm_resnet50.pth', device='cuda'):
        self.device = device
        self.model = self.load_model(model_path)
        self.preprocess = self.get_preprocess()
        
    def load_model(self, model_path):
        """加载RVM模型"""
        from model import MobileNetV3LargeBiSeNetHead  # RVM模型
        
        model = MobileNetV3LargeBiSeNetHead()
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.eval()
        model.to(self.device)
        
        return model
    
    def get_preprocess(self):
        """预处理变换"""
        return transforms.Compose([
            transforms.Resize((512, 512)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    
    def process_video(self, input_path, output_path, downsample_ratio=0.25):
        """处理视频抠像"""
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 输出视频编码器（带alpha通道）
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # 初始化背景
        rec = [None] * 4  # r1, r2, r3, r4 for recurrent states
        
        frame_count = 0
        
        with torch.no_grad():
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 预处理
                input_tensor = self.preprocess(frame).unsqueeze(0).to(self.device)
                
                # 模型推理
                if rec[0] is None:
                    rec = [None] * 4
                
                fgr, pha, *rec = self.model(input_tensor, *rec, downsample_ratio)
                
                # 后处理
                fgr = fgr[0].cpu().numpy().transpose(1, 2, 0)
                pha = pha[0, 0].cpu().numpy()
                
                # 调整到原始尺寸
                fgr = cv2.resize(fgr, (width, height))
                pha = cv2.resize(pha, (width, height))
                
                # 创建RGBA图像
                rgba = np.zeros((height, width, 4), dtype=np.uint8)
                rgba[:, :, :3] = (fgr * 255).astype(np.uint8)
                rgba[:, :, 3] = (pha * 255).astype(np.uint8)
                
                # 转换为带透明度的视频帧
                rgb_frame = self.composite_green_screen(rgba)
                out.write(rgb_frame)
                
                frame_count += 1
                if frame_count % 30 == 0:
                    print(f"Processed {frame_count} frames")
        
        cap.release()
        out.release()
        
        print(f"RVM processing completed: {output_path}")
    
    def composite_green_screen(self, rgba_frame):
        """合成绿幕背景（便于后续背景替换）"""
        rgb = rgba_frame[:, :, :3]
        alpha = rgba_frame[:, :, 3:4] / 255.0
        
        # 绿色背景
        green_bg = np.zeros_like(rgb)
        green_bg[:, :, 1] = 255  # 纯绿色
        
        # Alpha混合
        result = rgb * alpha + green_bg * (1 - alpha)
        
        return result.astype(np.uint8)
```

### 第五步：背景替换与合成

#### 5.1 背景匹配策略
```python
# background_manager.py
import random
import os
import json
import hashlib

class BackgroundManager:
    def __init__(self, bg_library_path='backgrounds'):
        self.bg_path = bg_library_path
        self.categories = {
            'popular': ['城市夜景', '霓虹灯效果', '现代广场'],
            'classic': ['社区广场', '公园傍晚', '传统庭院'],
            'ethnic': ['民族建筑', '文化广场', '传统背景'],
            'fitness': ['健身房', '体育场', '运动场地'],
            'health': ['公园晨景', '湖边风光', '山景自然']
        }
        
        self.style_mapping = {
            # 根据音乐风格/舞蹈类型映射背景类别
            '流行舞': 'popular',
            '广场舞': 'classic',
            '民族舞': 'ethnic',
            '健身操': 'fitness',
            '太极': 'health'
        }
    
    def select_background(self, video_metadata):
        """智能背景选择"""
        # 1. 基于元数据选择类别
        dance_type = video_metadata.get('dance_type', 'classic')
        category = self.style_mapping.get(dance_type, 'classic')
        
        # 2. 基于时间选择（早晨/傍晚/夜晚）
        time_preference = video_metadata.get('time_preference', 'auto')
        
        # 3. 基于视频长度选择背景长度
        video_duration = video_metadata.get('duration', 300)  # 5分钟默认
        
        bg_files = self.get_category_backgrounds(category)
        
        # 过滤合适的背景
        suitable_bgs = []
        for bg_file in bg_files:
            bg_info = self.get_background_info(bg_file)
            if bg_info['loop_duration'] >= 3 and bg_info['quality_score'] > 0.7:
                suitable_bgs.append(bg_file)
        
        if not suitable_bgs:
            # 回退到默认背景
            suitable_bgs = self.get_category_backgrounds('classic')
        
        return random.choice(suitable_bgs)
    
    def get_background_info(self, bg_file):
        """获取背景信息"""
        info_file = bg_file.replace('.mp4', '_info.json')
        if os.path.exists(info_file):
            with open(info_file, 'r') as f:
                return json.load(f)
        
        # 如果没有info文件，动态分析
        return self.analyze_background(bg_file)
    
    def analyze_background(self, bg_file):
        """分析背景视频"""
        cap = cv2.VideoCapture(bg_file)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        # 简单质量评估
        quality_scores = []
        for i in range(0, min(30, frame_count), 5):  # 检查6帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                score = cv2.Laplacian(gray, cv2.CV_64F).var()
                quality_scores.append(score)
        
        cap.release()
        
        avg_quality = np.mean(quality_scores) if quality_scores else 0
        
        return {
            'duration': duration,
            'loop_duration': duration,
            'quality_score': min(avg_quality / 200.0, 1.0),  # 归一化到0-1
            'fps': fps
        }
```

#### 5.2 高质量合成
```bash
# composite_final.sh
#!/bin/bash

composite_with_background() {
    local person_video="$1"      # 抠像后的人物视频
    local background_video="$2"  # 背景Loop视频
    local output_video="$3"      # 最终输出
    local audio_source="$4"      # 音频来源（可选）
    
    echo "开始最终合成: $output_video"
    
    # 获取人物视频信息
    person_duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$person_video")
    person_fps=$(ffprobe -v quiet -show_entries stream=r_frame_rate -of csv=p=0 "$person_video" | head -1)
    
    # 音频处理
    if [ -n "$audio_source" ]; then
        audio_options="-i \"$audio_source\" -map 2:a"
    else
        audio_options="-map 1:a?"
    fi
    
    # 高质量合成命令
    ffmpeg \
        -stream_loop -1 -i "$background_video" \
        -i "$person_video" \
        ${audio_source:+-i "$audio_source"} \
        -filter_complex "
            [0:v]scale=1920:1080:force_original_aspect_ratio=cover,crop=1920:1080[bg];
            [1:v]scale=1920:1080[person];
            [bg][person]overlay=0:0:format=auto:shortest=1[v]
        " \
        -map "[v]" \
        ${audio_options} \
        -t "$person_duration" \
        -c:v libx264 \
        -preset medium \
        -crf 18 \
        -pix_fmt yuv420p \
        -c:a aac \
        -b:a 192k \
        -avoid_negative_ts make_zero \
        "$output_video" -y
    
    echo "合成完成: $output_video"
}
```

## 最佳实践

### 1. 资源管理最佳实践

#### 1.1 内存和存储管理
```python
# resource_manager.py
import shutil
import tempfile
import os
from contextlib import contextmanager

@contextmanager
def temp_workspace(base_dir="/tmp"):
    """临时工作空间管理"""
    temp_dir = tempfile.mkdtemp(dir=base_dir, prefix="dance_processing_")
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def optimize_storage():
    """存储空间优化"""
    # 清理超过7天的临时文件
    import time
    temp_dirs = ['/tmp', './temp', './cache']
    
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if os.path.isfile(item_path):
                    file_age = time.time() - os.path.getmtime(item_path)
                    if file_age > 7 * 24 * 3600:  # 7天
                        os.remove(item_path)

def monitor_disk_space(min_free_gb=50):
    """磁盘空间监控"""
    statvfs = os.statvfs('.')
    free_bytes = statvfs.f_frsize * statvfs.f_bavail
    free_gb = free_bytes / (1024**3)
    
    if free_gb < min_free_gb:
        raise Exception(f"Insufficient disk space: {free_gb:.1f}GB available, {min_free_gb}GB required")
    
    return free_gb
```

#### 1.2 批量处理优化
```python
# batch_optimizer.py
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

class BatchProcessor:
    def __init__(self, max_concurrent=2):
        self.max_concurrent = max_concurrent
        self.gpu_manager = GPUManager()
        self.viggle_client = ViggleClient()
        self.processing_queue = queue.Queue()
        self.completed_tasks = []
        self.failed_tasks = []
        
    async def process_batch_optimized(self, video_list):
        """优化的批量处理"""
        # 1. 按视频长度排序（短视频优先）
        sorted_videos = sorted(video_list, key=lambda x: x.get('duration', 300))
        
        # 2. 预分配任务
        viggle_tasks = []
        local_tasks = queue.Queue()
        
        # 3. 并行提交Viggle任务
        semaphore = asyncio.Semaphore(5)  # 限制同时提交的API请求
        
        async def submit_viggle_task(video_info):
            async with semaphore:
                try:
                    task_result = await self.viggle_client.submitVideo(video_info)
                    return {'video_info': video_info, 'viggle_task': task_result}
                except Exception as e:
                    return {'video_info': video_info, 'error': str(e)}
        
        # 提交所有Viggle任务
        viggle_submissions = await asyncio.gather(*[
            submit_viggle_task(video) for video in sorted_videos
        ])
        
        # 4. 监控Viggle任务并进行本地处理
        local_processor = ThreadPoolExecutor(max_workers=self.max_concurrent)
        
        async def monitor_and_process():
            pending_tasks = [sub for sub in viggle_submissions if 'viggle_task' in sub]
            
            while pending_tasks:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                completed_viggle = []
                for task_info in pending_tasks[:]:
                    try:
                        status = await self.viggle_client.pollTaskStatus(
                            task_info['viggle_task']['task_id']
                        )
                        
                        if status['success']:
                            # Viggle完成，加入本地处理队列
                            local_tasks.put({
                                'video_info': task_info['video_info'],
                                'viggle_output': status['outputUrl']
                            })
                            pending_tasks.remove(task_info)
                            completed_viggle.append(task_info)
                            
                    except Exception as e:
                        print(f"Error checking task: {e}")
                        
                # 启动本地处理
                while not local_tasks.empty() and self.gpu_manager.allocate_task():
                    task = local_tasks.get()
                    local_processor.submit(self.process_local_task, task)
        
        await monitor_and_process()
        
        # 等待所有本地任务完成
        local_processor.shutdown(wait=True)
        
        return {
            'completed': len(self.completed_tasks),
            'failed': len(self.failed_tasks),
            'success_rate': len(self.completed_tasks) / len(video_list)
        }
    
    def process_local_task(self, task):
        """本地GPU任务处理"""
        try:
            with temp_workspace() as workspace:
                # 下载Viggle输出
                viggle_file = os.path.join(workspace, 'viggle_output.mp4')
                self.download_file(task['viggle_output'], viggle_file)
                
                # 本地处理流程
                result = self.local_gpu_pipeline(viggle_file, workspace, task['video_info'])
                
                self.completed_tasks.append({
                    'input': task['video_info'],
                    'output': result
                })
                
        except Exception as e:
            self.failed_tasks.append({
                'input': task['video_info'],
                'error': str(e)
            })
        finally:
            self.gpu_manager.release_task()
```

### 2. 质量控制最佳实践

#### 2.1 多层质量检查
```python
# quality_assurance.py
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

class QualityAssurance:
    def __init__(self):
        self.quality_thresholds = {
            'min_clarity': 100,
            'min_ssim': 0.7,
            'max_noise_level': 0.3,
            'min_resolution': (720, 720)
        }
    
    def comprehensive_quality_check(self, video_path):
        """综合质量检查"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return {'valid': False, 'error': 'Cannot open video'}
        
        # 基本信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if width < self.quality_thresholds['min_resolution'][0] or \
           height < self.quality_thresholds['min_resolution'][1]:
            return {'valid': False, 'error': 'Resolution too low'}
        
        # 采样检查关键帧
        check_frames = min(50, frame_count)
        step = max(1, frame_count // check_frames)
        
        clarity_scores = []
        noise_levels = []
        brightness_levels = []
        
        for i in range(0, frame_count, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                continue
                
            # 清晰度检查
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            clarity = cv2.Laplacian(gray, cv2.CV_64F).var()
            clarity_scores.append(clarity)
            
            # 噪声检查
            noise = self.estimate_noise(gray)
            noise_levels.append(noise)
            
            # 亮度检查
            brightness = np.mean(gray)
            brightness_levels.append(brightness)
        
        cap.release()
        
        # 统计分析
        avg_clarity = np.mean(clarity_scores)
        avg_noise = np.mean(noise_levels)
        avg_brightness = np.mean(brightness_levels)
        
        # 质量评分
        quality_score = self.calculate_quality_score(
            avg_clarity, avg_noise, avg_brightness
        )
        
        return {
            'valid': avg_clarity >= self.quality_thresholds['min_clarity'],
            'quality_score': quality_score,
            'metrics': {
                'clarity': avg_clarity,
                'noise_level': avg_noise,
                'brightness': avg_brightness,
                'resolution': f"{width}x{height}",
                'fps': fps,
                'duration': frame_count / fps
            },
            'recommendations': self.get_quality_recommendations(
                avg_clarity, avg_noise, avg_brightness
            )
        }
    
    def estimate_noise(self, image):
        """估算图像噪声"""
        return cv2.Laplacian(image, cv2.CV_64F).var() / np.mean(image)
    
    def calculate_quality_score(self, clarity, noise, brightness):
        """计算综合质量评分 (0-1)"""
        clarity_score = min(clarity / 200, 1.0)  # 归一化
        noise_score = max(0, 1.0 - noise)
        brightness_score = 1.0 - abs(brightness - 128) / 128  # 理想亮度128
        
        return (clarity_score * 0.5 + noise_score * 0.3 + brightness_score * 0.2)
    
    def get_quality_recommendations(self, clarity, noise, brightness):
        """质量改进建议"""
        recommendations = []
        
        if clarity < 100:
            recommendations.append("视频清晰度不足，建议重新处理或使用更高质量的原始视频")
        
        if noise > 0.3:
            recommendations.append("噪声水平较高，建议添加降噪处理")
        
        if brightness < 80:
            recommendations.append("视频偏暗，建议增加亮度")
        elif brightness > 180:
            recommendations.append("视频过亮，建议降低亮度")
        
        if not recommendations:
            recommendations.append("视频质量良好")
        
        return recommendations
```

### 3. 性能优化最佳实践

#### 3.1 智能缓存系统
```python
# cache_system.py
import hashlib
import pickle
import os
import time
from functools import wraps

class ProcessingCache:
    def __init__(self, cache_dir='./cache', max_age_days=30):
        self.cache_dir = cache_dir
        self.max_age = max_age_days * 24 * 3600
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_key(self, video_path, processing_params):
        """生成缓存键"""
        # 文件内容哈希
        with open(video_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # 参数哈希
        params_str = str(sorted(processing_params.items()))
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        return f"{file_hash}_{params_hash}"
    
    def get_cached_result(self, cache_key):
        """获取缓存结果"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if not os.path.exists(cache_file):
            return None
        
        # 检查缓存是否过期
        if time.time() - os.path.getmtime(cache_file) > self.max_age:
            os.remove(cache_file)
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except:
            return None
    
    def save_cached_result(self, cache_key, result):
        """保存缓存结果"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            print(f"Failed to save cache: {e}")

def cached_processing(cache_system):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(video_path, **kwargs):
            # 生成缓存键
            cache_key = cache_system.get_cache_key(video_path, kwargs)
            
            # 尝试获取缓存
            cached_result = cache_system.get_cached_result(cache_key)
            if cached_result:
                print(f"Using cached result for {os.path.basename(video_path)}")
                return cached_result
            
            # 执行处理
            result = func(video_path, **kwargs)
            
            # 保存缓存
            cache_system.save_cached_result(cache_key, result)
            
            return result
        return wrapper
    return decorator
```

## 避坑指南

### 1. Viggle API常见问题

#### 1.1 API调用失败处理
```python
# viggle_error_handler.py
class ViggleErrorHandler:
    def __init__(self):
        self.common_errors = {
            'INSUFFICIENT_CREDITS': '积分不足，请充值或等待积分重置',
            'VIDEO_TOO_LONG': '视频超过10分钟限制，请分段处理',
            'INVALID_FORMAT': '视频格式不支持，请转换为MP4格式',
            'PROCESSING_TIMEOUT': '处理超时，可能是服务器负载过高',
            'QUALITY_TOO_LOW': '输入视频质量过低，请使用更高质量的原始视频'
        }
    
    def handle_viggle_error(self, error_response):
        """处理Viggle API错误"""
        error_code = error_response.get('error_code', 'UNKNOWN')
        error_message = error_response.get('message', '')
        
        if error_code in self.common_errors:
            suggestion = self.common_errors[error_code]
            print(f"Viggle错误: {error_message}")
            print(f"解决建议: {suggestion}")
            
            # 自动处理一些错误
            if error_code == 'VIDEO_TOO_LONG':
                return self.suggest_video_split(error_response.get('duration', 0))
            elif error_code == 'INVALID_FORMAT':
                return self.suggest_format_conversion()
        
        return None
    
    def suggest_video_split(self, duration):
        """建议视频分割方案"""
        segments = []
        segment_length = 8 * 60  # 8分钟一段
        
        for start in range(0, int(duration), segment_length):
            end = min(start + segment_length, duration)
            segments.append({'start': start, 'end': end})
        
        return {
            'action': 'split_video',
            'segments': segments,
            'note': f'建议分割为{len(segments)}段进行处理'
        }
```

#### 1.2 Credits使用陷阱
```python
# credits_traps.py
class CreditsOptimizer:
    def __init__(self):
        self.credits_traps = {
            'redundant_processing': '避免重复处理相同视频',
            'quality_overkill': '不要为简单视频使用最高质量设置',
            'failed_retry': '失败的任务也会消耗Credits，注意重试策略',
            'watermark_cost': '去水印需要付费套餐'
        }
    
    def optimize_credits_usage(self, video_batch):
        """优化Credits使用"""
        optimized_batch = []
        
        for video in video_batch:
            # 去重检查
            if self.is_duplicate(video):
                continue
            
            # 质量设置优化
            video['quality_setting'] = self.recommend_quality(video)
            
            # 预估Credits消耗
            video['estimated_credits'] = self.estimate_credits(video)
            
            optimized_batch.append(video)
        
        # 按Credits效率排序
        optimized_batch.sort(key=lambda x: x['estimated_credits'])
        
        return optimized_batch
    
    def recommend_quality(self, video_info):
        """推荐质量设置"""
        duration = video_info.get('duration', 300)
        input_quality = video_info.get('input_resolution', '720p')
        
        if duration < 60 and input_quality in ['480p', '720p']:
            return 'standard'  # 短视频用标准质量
        elif duration > 300:
            return 'fast'  # 长视频用快速模式
        else:
            return 'high'  # 其他用高质量
```

### 2. 本地GPU处理陷阱

#### 2.1 显存管理陷阱
```python
# gpu_traps.py
class GPUTrapAvoidance:
    def __init__(self):
        self.memory_warnings = []
        
    def avoid_memory_leaks(self):
        """避免显存泄漏"""
        # 1. 及时清理PyTorch缓存
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        # 2. 限制模型加载
        # 不要在循环中重复加载模型
        
        # 3. 使用上下文管理器
        @contextmanager
        def gpu_memory_context():
            try:
                yield
            finally:
                torch.cuda.empty_cache()
    
    def monitor_gpu_health(self):
        """GPU健康监控"""
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            
            # 温度检查
            if gpu.temperature > 80:
                self.memory_warnings.append(f"GPU温度过高: {gpu.temperature}°C")
                
            # 显存使用率检查
            memory_usage = gpu.memoryUsed / gpu.memoryTotal
            if memory_usage > 0.9:
                self.memory_warnings.append(f"显存使用率过高: {memory_usage:.1%}")
            
            # 功耗检查
            if hasattr(gpu, 'powerDraw') and gpu.powerDraw > 200:
                self.memory_warnings.append(f"GPU功耗过高: {gpu.powerDraw}W")
        
        return self.memory_warnings
```

#### 2.2 文件处理陷阱
```bash
# file_traps.sh
#!/bin/bash

# 避免文件处理陷阱的最佳实践

avoid_file_traps() {
    local input_file="$1"
    local output_file="$2"
    
    # 1. 检查文件存在性
    if [ ! -f "$input_file" ]; then
        echo "错误: 输入文件不存在: $input_file"
        return 1
    fi
    
    # 2. 检查文件权限
    if [ ! -r "$input_file" ]; then
        echo "错误: 无法读取输入文件: $input_file"
        return 1
    fi
    
    # 3. 检查磁盘空间
    available_space=$(df "$(dirname "$output_file")" | awk 'NR==2 {print $4}')
    input_size=$(stat -c%s "$input_file")
    required_space=$((input_size * 3))  # 预留3倍空间
    
    if [ "$available_space" -lt "$required_space" ]; then
        echo "错误: 磁盘空间不足"
        return 1
    fi
    
    # 4. 创建输出目录
    mkdir -p "$(dirname "$output_file")"
    
    # 5. 使用临时文件避免覆盖
    temp_output="${output_file}.tmp.$$"
    
    # 6. 处理完成后原子性移动
    if process_video "$input_file" "$temp_output"; then
        mv "$temp_output" "$output_file"
        echo "成功: $output_file"
    else
        rm -f "$temp_output"
        echo "失败: 处理出错"
        return 1
    fi
}

# 音视频同步陷阱
avoid_sync_issues() {
    local video_file="$1"
    local audio_file="$2"
    local output_file="$3"
    
    # 检查音视频长度匹配
    video_duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$video_file")
    audio_duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$audio_file")
    
    duration_diff=$(echo "$video_duration - $audio_duration" | bc)
    duration_diff_abs=$(echo "$duration_diff" | sed 's/-//')
    
    if (( $(echo "$duration_diff_abs > 1.0" | bc -l) )); then
        echo "警告: 音视频长度不匹配，差异: ${duration_diff}秒"
        
        # 自动调整
        if (( $(echo "$video_duration > $audio_duration" | bc -l) )); then
            echo "裁剪视频到音频长度"
            ffmpeg -i "$video_file" -t "$audio_duration" temp_video.mp4 -y
            video_file="temp_video.mp4"
        fi
    fi
    
    # 使用安全的合并参数
    ffmpeg -i "$video_file" -i "$audio_file" \
        -c:v copy -c:a aac -b:a 192k \
        -map 0:v:0 -map 1:a:0 \
        -avoid_negative_ts make_zero \
        -fflags +genpts \
        "$output_file" -y
    
    # 清理临时文件
    [ -f "temp_video.mp4" ] && rm temp_video.mp4
}
```

### 3. 质量和合规陷阱

#### 3.1 版权风险规避
```python
# copyright_compliance.py
class CopyrightCompliance:
    def __init__(self):
        self.risk_indicators = {
            'watermarks': ['logo', 'watermark', 'copyright', '©'],
            'brand_elements': ['brand', 'trademark', 'tm', '®'],
            'recognizable_people': ['face_detection_threshold'],
            'copyrighted_music': ['audio_fingerprint']
        }
    
    def check_copyright_risks(self, video_path):
        """检查版权风险"""
        risks = []
        
        # 1. 检查水印和Logo
        watermark_risk = self.detect_watermarks(video_path)
        if watermark_risk:
            risks.append(watermark_risk)
        
        # 2. 检查可识别人物
        people_risk = self.detect_recognizable_people(video_path)
        if people_risk:
            risks.append(people_risk)
        
        # 3. 检查背景内容
        background_risk = self.check_background_content(video_path)
        if background_risk:
            risks.append(background_risk)
        
        return {
            'total_risks': len(risks),
            'risk_level': 'high' if len(risks) > 2 else 'medium' if len(risks) > 0 else 'low',
            'risks': risks,
            'recommendations': self.get_compliance_recommendations(risks)
        }
    
    def detect_watermarks(self, video_path):
        """检测水印"""
        # 简化的水印检测
        cap = cv2.VideoCapture(video_path)
        
        # 检查画面四角
        corner_regions = [
            (0, 0, 200, 100),      # 左上角
            (-200, 0, 200, 100),   # 右上角
            (0, -100, 200, 100),   # 左下角
            (-200, -100, 200, 100) # 右下角
        ]
        
        watermark_detected = False
        
        for i in range(0, 300, 30):  # 检查前10秒，每秒一帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            for region in corner_regions:
                x, y, w, h = region
                if x < 0:
                    x = frame.shape[1] + x
                if y < 0:
                    y = frame.shape[0] + y
                
                roi = frame[y:y+h, x:x+w]
                
                # 简单的文字检测（基于边缘密度）
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 50, 150)
                edge_density = np.sum(edges) / (w * h)
                
                if edge_density > 0.1:  # 阈值可调
                    watermark_detected = True
                    break
        
        cap.release()
        
        if watermark_detected:
            return {
                'type': 'watermark',
                'severity': 'high',
                'description': '检测到可能的水印或Logo'
            }
        
        return None
```

#### 3.2 输出质量陷阱
```python
# output_quality_traps.py
class OutputQualityControl:
    def __init__(self):
        self.quality_checkpoints = [
            'resolution_consistency',
            'frame_rate_stability',
            'audio_sync',
            'color_accuracy',
            'compression_artifacts'
        ]
    
    def final_quality_check(self, output_video):
        """最终质量检查"""
        issues = []
        
        # 1. 分辨率一致性
        if not self.check_resolution_consistency(output_video):
            issues.append("分辨率不一致或异常")
        
        # 2. 帧率稳定性
        if not self.check_frame_rate_stability(output_video):
            issues.append("帧率不稳定")
        
        # 3. 音画同步
        if not self.check_audio_sync(output_video):
            issues.append("音画不同步")
        
        # 4. 压缩质量
        compression_quality = self.check_compression_quality(output_video)
        if compression_quality < 0.7:
            issues.append(f"压缩质量过低: {compression_quality:.2f}")
        
        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'quality_score': self.calculate_overall_score(output_video)
        }
    
    def check_compression_quality(self, video_path):
        """检查压缩质量"""
        cap = cv2.VideoCapture(video_path)
        
        quality_scores = []
        frame_count = 0
        
        while frame_count < 100:  # 检查前100帧
            ret, frame = cap.read()
            if not ret:
                break
            
            # 计算压缩伪影
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 使用拉普拉斯算子检测清晰度
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 使用Sobel算子检测边缘质量
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            sobel_mean = np.mean(np.sqrt(sobelx**2 + sobely**2))
            
            # 综合评分
            frame_quality = min(laplacian_var / 100 + sobel_mean / 50, 1.0)
            quality_scores.append(frame_quality)
            
            frame_count += 1
        
        cap.release()
        
        return np.mean(quality_scores) if quality_scores else 0
```

### 4. 运维监控陷阱

#### 4.1 日志和错误追踪
```python
# monitoring_traps.py
import logging
import traceback
import json
from datetime import datetime

class ProcessingLogger:
    def __init__(self, log_dir='./logs'):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{log_dir}/processing.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def log_processing_start(self, video_info):
        """记录处理开始"""
        self.logger.info(f"开始处理视频: {video_info.get('name', 'unknown')}")
        
        # 详细日志到JSON文件
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'processing_start',
            'video_info': video_info,
            'system_info': self.get_system_info()
        }
        
        self.save_json_log(log_entry)
    
    def log_processing_error(self, video_info, error):
        """记录处理错误"""
        error_details = {
            'timestamp': datetime.now().isoformat(),
            'event': 'processing_error',
            'video_info': video_info,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        
        self.logger.error(f"处理失败: {error_details['error_message']}")
        self.save_json_log(error_details)
    
    def get_system_info(self):
        """获取系统信息"""
        gpus = GPUtil.getGPUs()
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'gpu_memory_used': gpus[0].memoryUsed if gpus else 0,
            'gpu_temperature': gpus[0].temperature if gpus else 0
        }
    
    def save_json_log(self, log_entry):
        """保存JSON格式日志"""
        log_file = f"{self.log_dir}/processing_{datetime.now().strftime('%Y%m%d')}.json"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
```

这个详细的流程指南涵盖了从视频预处理到最终输出的每一个环节，以及在实际操作中需要注意的各种陷阱和最佳实践。按照这个指南可以大大提高处理成功率和输出质量。
