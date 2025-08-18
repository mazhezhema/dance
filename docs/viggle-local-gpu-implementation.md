# Viggle + 本地GPU实施方案

## 方案确定

我们采用 **Viggle + 本地GPU混合方案** 作为舞蹈App的内容生成解决方案。

## 技术架构

### 核心流程
```
原始舞蹈视频 → Viggle API(换脸换装) → 本地3060GPU处理 → 最终成品
                                    ↓
                            [超分辨率] → [抠像] → [背景替换]
```

### 分工明确
- **Viggle**: 专业的换脸换装处理
- **本地GPU**: 超分辨率、抠像、背景合成

## 技术实现

### 阶段1: Viggle处理
```javascript
// Viggle API调用流程
const viggleService = {
  async submitTask(videoUrl, characterConfig) {
    const response = await fetch('https://api.viggle.ai/generate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.VIGGLE_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        video_url: videoUrl,
        character: characterConfig,
        style: 'dance',
        quality: 'hd'
      })
    });
    return response.json();
  },
  
  async checkStatus(taskId) {
    // 轮询检查处理状态
    // 返回处理进度和结果URL
  }
};
```

### 阶段2: 本地GPU处理链
```bash
#!/bin/bash
# 本地GPU处理脚本

process_viggle_output() {
    local input_file="$1"
    local output_dir="$2"
    local bg_category="$3"
    
    echo "开始处理Viggle输出: $input_file"
    
    # 1. 超分辨率处理 (Real-ESRGAN)
    echo "步骤1: 超分辨率处理..."
    ffmpeg -i "$input_file" temp_frames/frame_%08d.png
    realesrgan-ncnn-vulkan -i temp_frames -o temp_frames_up -s 2 -n realesrgan-x4plus
    ffmpeg -r 30 -i temp_frames_up/frame_%08d.png -c:v libx264 -pix_fmt yuv420p temp_hd.mp4
    
    # 2. 抠像处理 (RVM)
    echo "步骤2: 抠像处理..."
    python tools/RVM/inference_rvm.py \
        --input temp_hd.mp4 \
        --output temp_alpha.mp4 \
        --model rvm_resnet50
    
    # 3. 背景替换
    echo "步骤3: 背景替换..."
    bg_file=$(get_background_by_category "$bg_category")
    ffmpeg -stream_loop -1 -i "$bg_file" -i temp_alpha.mp4 \
        -filter_complex "[0:v]scale=1920:1080[bg];[bg][1:v]overlay=0:0:format=auto" \
        -map 1:a? -shortest -c:v libx264 -crf 18 -preset fast -pix_fmt yuv420p \
        "$output_dir/$(basename "$input_file" .mp4)_final.mp4"
    
    # 清理临时文件
    rm -rf temp_frames temp_frames_up temp_hd.mp4 temp_alpha.mp4
    
    echo "处理完成: $output_dir/$(basename "$input_file" .mp4)_final.mp4"
}
```

## 成本分析

### 单首歌曲成本构成
| 项目 | 成本 | 说明 |
|------|------|------|
| **Viggle API** | ¥40-50 | 换脸换装处理 |
| **本地处理** | ¥0.35 | 电费(3060, 8分钟) |
| **总成本** | **¥40.35-50.35** | |

### 500首歌曲总成本
- **总成本**: ¥20,175-25,175
- **处理时间**: 约30小时(并行处理)
- **单首平均**: ¥40.35-50.35

## 硬件要求

### 推荐配置
```
GPU: RTX 3060 12GB (已有)
CPU: 8核以上 (视频编解码)
内存: 32GB+ (处理大视频文件)
存储: NVMe SSD 1TB+ (临时文件IO)
网络: 千兆带宽 (Viggle API调用)
```

### 性能指标
- **并行任务数**: 2个
- **单视频处理时间**: 7-8分钟
- **显存占用**: 5-6GB/任务
- **日处理能力**: 100-150个视频

## 软件环境

### 核心工具安装
```bash
# 1. Real-ESRGAN-ncnn-vulkan
wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip
unzip realesrgan-ncnn-vulkan-20220424-windows.zip -d tools/

# 2. RVM (Robust Video Matting)
git clone https://github.com/PeterL1n/RobustVideoMatting.git tools/RVM
cd tools/RVM
pip install -r requirements.txt

# 3. FFmpeg
# 下载并配置环境变量
```

### Python依赖
```txt
# requirements.txt
torch>=1.12.0
torchvision>=0.13.0
opencv-python>=4.6.0
numpy>=1.21.0
Pillow>=9.0.0
imageio>=2.22.0
tqdm>=4.64.0
```

## 目录结构

```
project/
├── tools/
│   ├── Real-ESRGAN-ncnn-vulkan/     # 超分工具
│   └── RVM/                         # 抠像工具
├── scripts/
│   ├── viggle_api.js               # Viggle API调用
│   ├── local_processor.sh          # 本地处理脚本
│   └── batch_process.py            # 批量处理管理
├── viggle_output/                  # Viggle输出视频
├── backgrounds/
│   ├── popular/                    # 流行广场舞背景
│   ├── classic/                    # 经典老歌背景
│   └── health/                     # 健身太极背景
├── temp/                          # 临时处理文件
├── output/                        # 最终成品
└── logs/                          # 处理日志
```

## 背景库管理

### 分类体系
1. **流行广场舞**: 城市夜景、霓虹灯效果
2. **经典老歌舞**: 社区广场、公园傍晚
3. **民族舞**: 传统建筑、文化广场
4. **健身操**: 健身房、体育场
5. **太极养生**: 公园晨景、湖边山景

### 背景制作流程
```bash
# 背景Loop化脚本
create_loop_background() {
    local input="$1"
    local output="$2"
    local duration="5"  # 5秒循环
    
    # 提取核心片段
    ffmpeg -i "$input" -t $duration -an \
        -vf "scale=1920:1080:force_original_aspect_ratio=cover,fps=30" \
        temp_A.mp4
    
    # 创建无缝循环
    cp temp_A.mp4 temp_B.mp4
    ffmpeg -i temp_A.mp4 -i temp_B.mp4 \
        -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.8:offset=4.2,format=yuv420p" \
        -c:v libx264 "$output"
    
    rm temp_A.mp4 temp_B.mp4
}
```

## 质量控制

### 自动化质检
```python
# quality_checker.py
import cv2
import numpy as np

def check_video_quality(video_path):
    """检查视频质量"""
    cap = cv2.VideoCapture(video_path)
    
    clarity_scores = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret or frame_count > 50:  # 检查前50帧
            break
            
        # 计算清晰度
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clarity = cv2.Laplacian(gray, cv2.CV_64F).var()
        clarity_scores.append(clarity)
        
        frame_count += 1
    
    cap.release()
    
    avg_clarity = np.mean(clarity_scores)
    return {
        'clarity_score': avg_clarity,
        'is_acceptable': avg_clarity > 100,
        'recommendation': 'good' if avg_clarity > 200 else 'acceptable' if avg_clarity > 100 else 'poor'
    }

def batch_quality_check(video_dir):
    """批量质检"""
    results = {}
    for video_file in os.listdir(video_dir):
        if video_file.endswith('.mp4'):
            results[video_file] = check_video_quality(os.path.join(video_dir, video_file))
    return results
```

## 批量处理管理

### 任务队列系统
```python
# batch_processor.py
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import subprocess

class VideoProcessor:
    def __init__(self):
        self.viggle_api_key = os.getenv('VIGGLE_API_KEY')
        self.max_concurrent = 2  # 3060可并行2任务
        
    async def process_batch(self, video_list):
        """批量处理视频"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        tasks = [
            self.process_single_video(video_info, semaphore) 
            for video_info in video_list
        ]
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def process_single_video(self, video_info, semaphore):
        """处理单个视频"""
        async with semaphore:
            # 1. 调用Viggle API
            viggle_result = await self.call_viggle_api(video_info)
            
            # 2. 等待Viggle处理完成
            while viggle_result['status'] != 'completed':
                await asyncio.sleep(30)
                viggle_result = await self.check_viggle_status(viggle_result['task_id'])
            
            # 3. 本地GPU处理
            final_output = await self.local_gpu_process(viggle_result['output_url'])
            
            return final_output
    
    async def call_viggle_api(self, video_info):
        """调用Viggle API"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.viggle.ai/generate',
                headers={'Authorization': f'Bearer {self.viggle_api_key}'},
                json={
                    'video_url': video_info['url'],
                    'character': video_info['character_config'],
                    'style': 'dance'
                }
            ) as response:
                return await response.json()
    
    async def local_gpu_process(self, viggle_output_url):
        """本地GPU处理"""
        # 下载Viggle输出
        local_file = await self.download_video(viggle_output_url)
        
        # 执行本地处理脚本
        result = subprocess.run([
            'bash', 'scripts/local_processor.sh',
            local_file, 'output/', 'popular'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return {'status': 'success', 'output': result.stdout}
        else:
            return {'status': 'error', 'error': result.stderr}
```

## 监控和日志

### 处理状态监控
```python
# monitor.py
import psutil
import GPUtil
import time
import json

def monitor_system():
    """系统监控"""
    while True:
        # GPU监控
        gpus = GPUtil.getGPUs()
        gpu_info = {
            'gpu_utilization': gpus[0].load * 100,
            'gpu_memory_used': gpus[0].memoryUsed,
            'gpu_memory_total': gpus[0].memoryTotal,
            'gpu_temperature': gpus[0].temperature
        }
        
        # CPU和内存监控
        system_info = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
        
        # 记录日志
        log_entry = {
            'timestamp': time.time(),
            'gpu': gpu_info,
            'system': system_info
        }
        
        with open('logs/system_monitor.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        time.sleep(10)  # 每10秒记录一次
```

## 实施计划

### 第一阶段: 环境搭建 (1周)
1. ✅ 安装Real-ESRGAN和RVM工具
2. ✅ 配置Python环境和依赖
3. ✅ 申请Viggle API账号和配额
4. ✅ 创建项目目录结构

### 第二阶段: 脚本开发 (1-2周)
1. 开发Viggle API调用脚本
2. 完善本地GPU处理脚本
3. 实现批量处理管理系统
4. 添加质量检查和监控

### 第三阶段: 背景库建设 (1周)
1. 收集和分类背景素材
2. 制作Loop化背景库
3. 建立背景选择规则

### 第四阶段: 批量生产 (持续)
1. 小批量测试(10-20首)
2. 优化处理流程
3. 扩大到500首目标

## 风险控制

### 技术风险
- **Viggle API限制**: 监控Credits使用，合理分配
- **GPU过热**: 监控温度，必要时降低并行数
- **存储空间**: 定期清理临时文件
- **网络中断**: 实现断点续传机制

### 质量风险  
- **输出质量不稳定**: 建立质检标准和重处理机制
- **背景匹配不当**: 完善分类规则和人工审核
- **音画不同步**: 确保FFmpeg参数正确设置

### 成本风险
- **Viggle费用超预算**: 严格控制处理数量和质量设置
- **硬件故障**: 准备备用GPU或云端备用方案
- **电费成本**: 优化处理时间，避免峰电时段
