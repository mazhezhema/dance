#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景替换处理脚本
实现视频背景替换功能
"""

import subprocess
import os
import json
import random
from pathlib import Path
import logging
from typing import List, Dict, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackgroundReplacer:
    def __init__(self, backgrounds_dir: str = "backgrounds"):
        self.backgrounds_dir = Path(backgrounds_dir)
        self.backgrounds_dir.mkdir(parents=True, exist_ok=True)
        self.background_cache = {}
        
        # 导入背景生成器
        try:
            from scripts.background_generator import BackgroundGenerator
            self.generator = BackgroundGenerator(backgrounds_dir)
            self.use_generator = True
        except ImportError:
            logger.warning("⚠️ 背景生成器未找到，使用传统模式")
            self.generator = None
            self.use_generator = False
        
        self.load_backgrounds()
    
    def load_backgrounds(self):
        """加载背景视频库"""
        logger.info("📁 加载背景视频库...")
        
        # 按类别组织背景
        categories = {
            "dance_studio": [],
            "gym": [],
            "stage": [],
            "neutral": [],
            "gradients": []
        }
        
        # 扫描背景文件
        for bg_file in self.backgrounds_dir.rglob("*.mp4"):
            category = self.classify_background(bg_file)
            if category in categories:
                categories[category].append(bg_file)
        
        self.background_cache = categories
        
        # 统计信息
        total_bg = sum(len(bgs) for bgs in categories.values())
        logger.info(f"✅ 背景库加载完成: {total_bg} 个背景")
        for category, bgs in categories.items():
            if bgs:
                logger.info(f"   {category}: {len(bgs)} 个")
    
    def classify_background(self, bg_file: Path) -> str:
        """分类背景视频"""
        filename = bg_file.name.lower()
        
        if "dance" in filename or "studio" in filename:
            return "dance_studio"
        elif "gym" in filename or "fitness" in filename:
            return "gym"
        elif "stage" in filename or "theater" in filename:
            return "stage"
        elif "gradient" in filename or "color" in filename:
            return "gradients"
        else:
            return "neutral"
    
    def select_background(self, category: str = None, style: str = None) -> Optional[Path]:
        """选择合适的背景视频"""
        if category and category in self.background_cache:
            backgrounds = self.background_cache[category]
        else:
            # 如果没有指定类别，从所有背景中选择
            backgrounds = []
            for bgs in self.background_cache.values():
                backgrounds.extend(bgs)
        
        if not backgrounds:
            logger.warning("⚠️ 没有找到合适的背景视频")
            return None
        
        # 根据风格选择
        if style:
            filtered_bgs = [bg for bg in backgrounds if style.lower() in bg.name.lower()]
            if filtered_bgs:
                backgrounds = filtered_bgs
        
        # 随机选择一个背景
        selected_bg = random.choice(backgrounds)
        logger.info(f"🎨 选择背景: {selected_bg.name}")
        
        return selected_bg
    
    def replace_background(self, input_video: str, output_video: str, 
                          background_path: str = None, category: str = None,
                          style: str = None, resolution: tuple = (1920, 1080),
                          effects: List[str] = None) -> bool:
        """替换视频背景"""
        try:
            # 使用背景生成器
            if self.use_generator and not background_path:
                logger.info("🔄 使用智能背景生成器")
                bg_path = self.generator.generate_background_for_video(
                    input_video, category, effects
                )
                if bg_path:
                    bg_path = Path(bg_path)
                else:
                    logger.warning("⚠️ 背景生成失败，使用传统模式")
                    bg_path = self.select_background(category, style)
            else:
                # 传统模式
                if background_path:
                    bg_path = Path(background_path)
                else:
                    bg_path = self.select_background(category, style)
            
            if not bg_path or not bg_path.exists():
                logger.error(f"❌ 背景文件不存在: {bg_path}")
                return False
            
            logger.info(f"🎬 开始背景替换: {Path(input_video).name}")
            logger.info(f"🎨 使用背景: {bg_path.name}")
            
            # 构建FFmpeg命令
            cmd = [
                "ffmpeg",
                "-i", input_video,  # 输入视频（带alpha通道）
                "-i", str(bg_path),  # 背景视频
                "-filter_complex", f"[1:v]scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=decrease,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2[bg];[bg][0:v]overlay=0:0:format=auto",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-b:v", "2M",
                "-c:a", "aac",  # 保留音频
                "-map", "0:a?",  # 映射音频流（如果存在）
                "-y", output_video
            ]
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 背景替换完成: {output_video}")
                return True
            else:
                logger.error(f"❌ 背景替换失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 背景替换异常: {e}")
            return False
    
    def batch_replace_backgrounds(self, input_dir: str, output_dir: str, 
                                 category: str = None, style: str = None) -> Dict:
        """批量替换背景"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🔄 开始批量背景替换: {input_dir} → {output_dir}")
        
        results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        # 处理所有视频文件
        for video_file in input_path.glob("*.mp4"):
            results["total"] += 1
            
            output_file = output_path / f"{video_file.stem}_bg_replaced.mp4"
            
            success = self.replace_background(
                str(video_file), str(output_file), 
                category=category, style=style
            )
            
            if success:
                results["success"] += 1
                results["details"].append({
                    "input": video_file.name,
                    "output": output_file.name,
                    "status": "success"
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "input": video_file.name,
                    "status": "failed"
                })
        
        # 输出统计
        logger.info(f"📊 批量处理完成:")
        logger.info(f"   总数: {results['total']}")
        logger.info(f"   成功: {results['success']}")
        logger.info(f"   失败: {results['failed']}")
        
        return results
    
    def create_background_preview(self, background_path: str, output_path: str = None) -> str:
        """创建背景预览图"""
        if not output_path:
            output_path = f"preview_{Path(background_path).stem}.jpg"
        
        cmd = [
            "ffmpeg", "-i", background_path,
            "-vframes", "1",
            "-q:v", "2",
            "-y", output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✅ 背景预览已创建: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 创建预览失败: {e}")
            return ""
    
    def list_backgrounds(self) -> Dict:
        """列出所有背景"""
        return {
            category: [str(bg) for bg in bgs]
            for category, bgs in self.background_cache.items()
            if bgs
        }

def main():
    """主函数"""
    print("🎨 背景替换处理工具")
    print("=" * 40)
    
    replacer = BackgroundReplacer()
    
    # 显示背景库信息
    backgrounds = replacer.list_backgrounds()
    print("\n📁 背景库信息:")
    for category, bgs in backgrounds.items():
        print(f"   {category}: {len(bgs)} 个背景")
    
    # 示例用法
    print("\n💡 使用示例:")
    print("1. 单个视频背景替换:")
    print("   replacer.replace_background('input.mp4', 'output.mp4', category='dance_studio')")
    print("\n2. 批量背景替换:")
    print("   replacer.batch_replace_backgrounds('input_dir', 'output_dir', category='gym')")
    print("\n3. 指定背景文件:")
    print("   replacer.replace_background('input.mp4', 'output.mp4', background_path='backgrounds/dance_studio.mp4')")

if __name__ == "__main__":
    main()
