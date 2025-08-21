#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTX 3060 GPU专用Pipeline脚本
针对3060 12GB显存优化的视频处理流程
"""

import os
import sys
import json
import subprocess
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging
from datetime import datetime
import concurrent.futures
import psutil
import GPUtil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rtx3060_pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PipelineConfig:
    """Pipeline配置"""
    # GPU配置
    gpu_memory_limit: Optional[int] = None  # GB，将从配置中获取
    max_concurrent_jobs: int = 2  # 3060可并行处理2个任务
    
    # 工具路径
    ffmpeg_path: str = "ffmpeg"
    realesrgan_path: str = "./tools/realesrgan-ncnn-vulkan.exe"
    rvm_path: str = "./tools/inference_rvm.py"
    
    # 处理参数
    superres_scale: int = 2  # 超分倍率
    superres_model: str = "realesr-animevideov3"
    target_resolution: tuple = (1920, 1080)
    target_fps: int = 30
    
    # 目录配置
    input_dir: str = "downloads"  # Viggle输出目录
    output_dir: str = "final_output"
    temp_dir: str = "temp_gpu"
    backgrounds_dir: str = "backgrounds"
    
    # 质量设置
    video_codec: str = "libx264"
    video_bitrate: str = "2M"
    audio_codec: str = "aac"

class RTX3060Pipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        
        # 从配置管理器获取GPU配置
        if config.gpu_memory_limit is None:
            from ..config.manager import get_config
            config.gpu_memory_limit = get_config('gpu_processing.memory_limit_gb', 10)
        
        self.setup_directories()
        self.check_gpu()
        
    def setup_directories(self):
        """创建必要目录"""
        dirs = [
            self.config.output_dir,
            self.config.temp_dir,
            f"{self.config.temp_dir}/frames",
            f"{self.config.temp_dir}/frames_up",
            "logs"
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 创建目录: {dir_path}")
    
    def check_gpu(self):
        """检查GPU状态"""
        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                logger.error("❌ 未检测到GPU")
                return False
            
            gpu = gpus[0]  # 使用第一个GPU
            logger.info(f"🎮 GPU: {gpu.name}")
            logger.info(f"💾 显存: {gpu.memoryTotal}MB")
            logger.info(f"📊 显存使用: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB")
            
            # 检查显存是否足够
            if gpu.memoryTotal < self.config.gpu_memory_limit * 1024:
                logger.warning(f"⚠️ 显存不足，建议至少{self.config.gpu_memory_limit}GB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ GPU检查失败: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> Dict:
        """获取视频信息"""
        try:
            cmd = [
                self.config.ffmpeg_path, "-i", video_path,
                "-f", "null", "-"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 解析视频信息
            info = {
                "duration": 0,
                "resolution": (0, 0),
                "fps": 0,
                "size_mb": 0
            }
            
            # 获取文件大小
            if os.path.exists(video_path):
                info["size_mb"] = os.path.getsize(video_path) / (1024 * 1024)
            
            return info
            
        except Exception as e:
            logger.error(f"❌ 获取视频信息失败: {e}")
            return {}
    
    def estimate_processing_time(self, video_path: str) -> float:
        """估算处理时间"""
        info = self.get_video_info(video_path)
        duration = info.get("duration", 60)  # 默认1分钟
        
        # 基于3060性能估算
        superres_time = duration * 0.8  # 超分时间
        matting_time = duration * 0.4   # 抠像时间
        synthesis_time = duration * 0.2  # 合成时间
        
        total_time = superres_time + matting_time + synthesis_time
        return total_time
    
    def step1_superres(self, input_path: str, output_path: str) -> bool:
        """步骤1: 超分辨率处理"""
        logger.info(f"🎯 开始超分处理: {Path(input_path).name}")
        
        try:
            # 1. 分解视频为帧
            frames_dir = f"{self.config.temp_dir}/frames"
            frames_up_dir = f"{self.config.temp_dir}/frames_up"
            
            # 清理旧文件
            shutil.rmtree(frames_dir, ignore_errors=True)
            shutil.rmtree(frames_up_dir, ignore_errors=True)
            os.makedirs(frames_dir)
            os.makedirs(frames_up_dir)
            
            # 分解帧
            cmd1 = [
                self.config.ffmpeg_path, "-i", input_path,
                "-vf", "fps=30",
                f"{frames_dir}/frame_%08d.png"
            ]
            
            logger.info("📹 分解视频为帧...")
            result1 = subprocess.run(cmd1, capture_output=True, text=True)
            if result1.returncode != 0:
                logger.error(f"❌ 分解帧失败: {result1.stderr}")
                return False
            
            # 2. Real-ESRGAN超分
            cmd2 = [
                self.config.realesrgan_path,
                "-i", frames_dir,
                "-o", frames_up_dir,
                "-s", str(self.config.superres_scale),
                "-n", self.config.superres_model
            ]
            
            logger.info("🚀 开始超分处理...")
            result2 = subprocess.run(cmd2, capture_output=True, text=True)
            if result2.returncode != 0:
                logger.error(f"❌ 超分失败: {result2.stderr}")
                return False
            
            # 3. 重新合成视频
            cmd3 = [
                self.config.ffmpeg_path,
                "-r", str(self.config.target_fps),
                "-i", f"{frames_up_dir}/frame_%08d.png",
                "-c:v", self.config.video_codec,
                "-pix_fmt", "yuv420p",
                "-b:v", self.config.video_bitrate,
                output_path
            ]
            
            logger.info("🎬 合成高清视频...")
            result3 = subprocess.run(cmd3, capture_output=True, text=True)
            if result3.returncode != 0:
                logger.error(f"❌ 合成失败: {result3.stderr}")
                return False
            
            logger.info(f"✅ 超分完成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 超分处理异常: {e}")
            return False
    
    def step2_matting(self, input_path: str, output_path: str) -> bool:
        """步骤2: 视频抠像"""
        logger.info(f"🎭 开始抠像处理: {Path(input_path).name}")
        
        try:
            cmd = [
                "python", self.config.rvm_path,
                "--input", input_path,
                "--output", output_path,
                "--model", "rvm_resnet50",
                "--device", "cuda"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"❌ 抠像失败: {result.stderr}")
                return False
            
            logger.info(f"✅ 抠像完成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 抠像处理异常: {e}")
            return False
    
    def step3_background_replace(self, alpha_path: str, output_path: str, 
                                background_path: str = None, category: str = None,
                                effects: List[str] = None) -> bool:
        """步骤3: 背景替换"""
        logger.info(f"🎨 开始背景替换: {Path(alpha_path).name}")
        
        try:
            # 使用智能背景生成器
            if not background_path:
                background_path = self.generate_smart_background(alpha_path, category, effects)
            
            if not os.path.exists(background_path):
                logger.warning(f"⚠️ 背景文件不存在: {background_path}")
                # 创建纯色背景
                background_path = self.create_color_background()
            
            # 合成最终视频（保留音轨）
            cmd = [
                self.config.ffmpeg_path,
                "-i", alpha_path,
                "-i", background_path,
                "-filter_complex", f"[1:v]scale={self.config.target_resolution[0]}:{self.config.target_resolution[1]}:force_original_aspect_ratio=decrease,pad={self.config.target_resolution[0]}:{self.config.target_resolution[1]}:(ow-iw)/2:(oh-ih)/2[bg];[bg][0:v]overlay=0:0:format=auto",
                "-c:v", self.config.video_codec,
                "-pix_fmt", "yuv420p",
                "-b:v", self.config.video_bitrate,
                "-c:a", self.config.audio_codec,
                "-map", "0:a?",  # 映射音频流（如果存在）
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"❌ 背景替换失败: {result.stderr}")
                return False
            
            logger.info(f"✅ 背景替换完成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 背景替换异常: {e}")
            return False
    
    def generate_smart_background(self, video_path: str, category: str = None, 
                                 effects: List[str] = None) -> str:
        """智能生成背景"""
        try:
            # 尝试导入背景生成器
            from scripts.background_generator import BackgroundGenerator
            generator = BackgroundGenerator(self.config.backgrounds_dir)
            
            # 生成背景
            bg_path = generator.generate_background_for_video(video_path, category, effects)
            if bg_path:
                logger.info(f"🎨 智能生成背景: {Path(bg_path).name}")
                return bg_path
            else:
                logger.warning("⚠️ 智能背景生成失败，使用传统选择")
                return self.select_smart_background(category)
                
        except ImportError:
            logger.warning("⚠️ 背景生成器未找到，使用传统模式")
            return self.select_smart_background(category)
        except Exception as e:
            logger.error(f"❌ 智能背景生成异常: {e}")
            return self.select_smart_background(category)
    
    def select_smart_background(self, category: str = None) -> str:
        """智能选择背景视频"""
        backgrounds_dir = Path(self.config.backgrounds_dir)
        
        if not backgrounds_dir.exists():
            logger.warning("⚠️ 背景目录不存在，使用默认背景")
            return self.create_color_background()
        
        # 按类别选择背景
        if category:
            # 查找指定类别的背景
            category_patterns = {
                "dance": ["dance", "studio"],
                "gym": ["gym", "fitness"],
                "stage": ["stage", "theater"],
                "neutral": ["neutral", "simple"],
                "gradient": ["gradient", "color"]
            }
            
            if category in category_patterns:
                patterns = category_patterns[category]
                for pattern in patterns:
                    bg_files = list(backgrounds_dir.glob(f"*{pattern}*.mp4"))
                    if bg_files:
                        selected_bg = random.choice(bg_files)
                        logger.info(f"🎨 选择{category}背景: {selected_bg.name}")
                        return str(selected_bg)
        
        # 如果没有指定类别或找不到，随机选择
        all_bg_files = list(backgrounds_dir.glob("*.mp4"))
        if all_bg_files:
            selected_bg = random.choice(all_bg_files)
            logger.info(f"🎨 随机选择背景: {selected_bg.name}")
            return str(selected_bg)
        
        # 如果没有任何背景文件，创建默认背景
        logger.warning("⚠️ 没有找到背景文件，创建默认背景")
        return self.create_color_background()
    
    def create_color_background(self) -> str:
        """创建纯色背景"""
        bg_path = f"{self.config.temp_dir}/color_bg.mp4"
        
        cmd = [
            self.config.ffmpeg_path,
            "-f", "lavfi",
            "-i", f"color=c=black:size={self.config.target_resolution[0]}x{self.config.target_resolution[1]}:duration=60",
            "-c:v", self.config.video_codec,
            "-pix_fmt", "yuv420p",
            bg_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        return bg_path
    
    def process_single_video(self, video_path: str, background_category: str = None, 
                           background_effects: List[str] = None) -> bool:
        """处理单个视频的完整Pipeline"""
        video_name = Path(video_path).stem
        start_time = time.time()
        
        logger.info(f"🎬 开始处理视频: {video_name}")
        if background_category:
            logger.info(f"🎨 背景类别: {background_category}")
        if background_effects:
            logger.info(f"✨ 背景特效: {', '.join(background_effects)}")
        
        try:
            # 临时文件路径
            temp_superres = f"{self.config.temp_dir}/{video_name}_superres.mp4"
            temp_alpha = f"{self.config.temp_dir}/{video_name}_alpha.mp4"
            final_output = f"{self.config.output_dir}/{video_name}_final.mp4"
            
            # 步骤1: 超分
            if not self.step1_superres(video_path, temp_superres):
                return False
            
            # 步骤2: 抠像
            if not self.step2_matting(temp_superres, temp_alpha):
                return False
            
            # 步骤3: 背景替换（支持类别和特效）
            if not self.step3_background_replace(temp_alpha, final_output, 
                                               category=background_category,
                                               effects=background_effects):
                return False
            
            # 清理临时文件
            if os.path.exists(temp_superres):
                os.remove(temp_superres)
            if os.path.exists(temp_alpha):
                os.remove(temp_alpha)
            
            processing_time = time.time() - start_time
            logger.info(f"🎉 视频处理完成: {video_name} (耗时: {processing_time:.1f}秒)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 视频处理失败: {video_name} - {e}")
            return False
    
    def run_batch_processing(self, background_category: str = None, background_effects: List[str] = None):
        """批量处理"""
        logger.info("🚀 开始RTX 3060 GPU批量处理")
        if background_category:
            logger.info(f"🎨 统一背景类别: {background_category}")
        if background_effects:
            logger.info(f"✨ 统一背景特效: {', '.join(background_effects)}")
        
        # 获取输入视频列表
        input_dir = Path(self.config.input_dir)
        if not input_dir.exists():
            logger.error(f"❌ 输入目录不存在: {self.config.input_dir}")
            return
        
        video_files = list(input_dir.glob("*.mp4"))
        if not video_files:
            logger.warning("⚠️ 没有找到视频文件")
            return
        
        logger.info(f"📁 找到 {len(video_files)} 个视频文件")
        
        # 估算总处理时间
        total_estimated_time = sum(self.estimate_processing_time(str(f)) for f in video_files)
        logger.info(f"⏱️ 预估总处理时间: {total_estimated_time:.1f}秒 ({total_estimated_time/60:.1f}分钟)")
        
        # 并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_concurrent_jobs) as executor:
            futures = []
            for video_file in video_files:
                future = executor.submit(self.process_single_video, str(video_file), 
                                       background_category, background_effects)
                futures.append(future)
            
            # 等待所有任务完成
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    completed += 1
                logger.info(f"📊 进度: {completed}/{len(video_files)}")
        
        logger.info(f"🎉 批量处理完成: {completed}/{len(video_files)} 成功")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RTX 3060 GPU Pipeline")
    parser.add_argument("--background", "-bg", type=str, 
                       choices=["dance", "gym", "stage", "neutral", "gradient"],
                       help="背景类别选择")
    parser.add_argument("--effects", "-e", nargs="+", 
                       choices=["zoom", "pan", "fade", "blur", "color"],
                       help="背景特效选择")
    parser.add_argument("--list-backgrounds", action="store_true",
                       help="列出可用的背景")
    parser.add_argument("--list-effects", action="store_true",
                       help="列出可用的特效")
    
    args = parser.parse_args()
    
    print("🎮 RTX 3060 GPU Pipeline")
    print("=" * 50)
    
    # 创建配置
    config = PipelineConfig()
    
    # 创建Pipeline实例
    pipeline = RTX3060Pipeline(config)
    
    # 列出特效
    if args.list_effects:
        print("\n✨ 可用背景特效:")
        effects = {
            "zoom": "缓慢缩放效果",
            "pan": "缓慢平移效果", 
            "fade": "淡入淡出效果",
            "blur": "轻微模糊效果",
            "color": "颜色调整效果"
        }
        for effect, desc in effects.items():
            print(f"   {effect}: {desc}")
        return
    
    # 列出背景
    if args.list_backgrounds:
        print("\n📁 可用背景类别:")
        backgrounds_dir = Path(config.backgrounds_dir)
        if backgrounds_dir.exists():
            categories = {
                "dance": ["dance", "studio"],
                "gym": ["gym", "fitness"],
                "stage": ["stage", "theater"],
                "neutral": ["neutral", "simple"],
                "gradient": ["gradient", "color"]
            }
            
            for category, patterns in categories.items():
                bg_files = []
                for pattern in patterns:
                    bg_files.extend(backgrounds_dir.glob(f"*{pattern}*.mp4"))
                if bg_files:
                    print(f"   {category}: {len(bg_files)} 个背景")
                else:
                    print(f"   {category}: 无背景文件")
        else:
            print("   ❌ 背景目录不存在")
        return
    
    # 运行批量处理
    pipeline.run_batch_processing(args.background, args.effects)

if __name__ == "__main__":
    main()
