#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景图片转视频生成器
将静态背景图片转换为动态背景视频
"""

import subprocess
import os
import json
import random
from pathlib import Path
import logging
from typing import List, Dict, Optional, Tuple
import tempfile

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackgroundGenerator:
    def __init__(self, backgrounds_dir: str = "backgrounds"):
        self.backgrounds_dir = Path(backgrounds_dir)
        self.backgrounds_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("temp_backgrounds")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 支持的图片格式
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        self.video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        
    def get_video_duration(self, video_path: str) -> float:
        """获取视频时长"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return 60.0  # 默认60秒
        except Exception as e:
            logger.warning(f"获取视频时长失败: {e}")
            return 60.0
    
    def image_to_video(self, image_path: str, output_path: str, 
                      duration: float = 60.0, resolution: Tuple[int, int] = (1920, 1080),
                      fps: int = 30, effects: List[str] = None) -> bool:
        """将图片转换为视频"""
        try:
            logger.info(f"🎨 生成背景视频: {Path(image_path).name} → {duration}秒")
            
            # 基础FFmpeg命令
            cmd = [
                "ffmpeg", "-y",  # 覆盖输出文件
                "-loop", "1",    # 循环播放图片
                "-i", image_path,
                "-t", str(duration),  # 指定时长
                "-vf", f"scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=decrease,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2",
                "-r", str(fps),  # 帧率
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-b:v", "2M",
                "-preset", "fast"
            ]
            
            # 添加特效
            if effects:
                cmd = self.add_video_effects(cmd, effects, resolution, fps)
            
            cmd.append(output_path)
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 背景视频生成完成: {output_path}")
                return True
            else:
                logger.error(f"❌ 背景视频生成失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 背景视频生成异常: {e}")
            return False
    
    def add_video_effects(self, cmd: List[str], effects: List[str], 
                         resolution: Tuple[int, int], fps: int) -> List[str]:
        """添加视频特效"""
        # 找到vf参数的位置
        vf_index = -1
        for i, arg in enumerate(cmd):
            if arg == "-vf":
                vf_index = i
                break
        
        if vf_index == -1:
            return cmd
        
        # 获取现有的vf参数
        current_vf = cmd[vf_index + 1]
        
        # 添加特效
        new_vf = current_vf
        
        for effect in effects:
            if effect == "zoom":
                # 缓慢缩放效果
                new_vf += f",zoompan=z='min(zoom+0.0015,1.5)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            elif effect == "pan":
                # 缓慢平移效果
                new_vf += f",crop=w=in_w:h=in_h:x='t*{resolution[0]//100}':y='t*{resolution[1]//100}'"
            elif effect == "fade":
                # 淡入淡出效果
                new_vf += f",fade=t=in:st=0:d=2,fade=t=out:st={duration-2}:d=2"
            elif effect == "blur":
                # 轻微模糊效果
                new_vf += ",boxblur=5:1"
            elif effect == "color":
                # 颜色调整
                new_vf += ",eq=brightness=0.1:saturation=1.2"
        
        # 更新命令
        cmd[vf_index + 1] = new_vf
        return cmd
    
    def create_dynamic_background(self, image_path: str, target_duration: float,
                                 resolution: Tuple[int, int] = (1920, 1080),
                                 effects: List[str] = None) -> Optional[str]:
        """创建动态背景视频"""
        try:
            # 生成临时文件名
            image_name = Path(image_path).stem
            temp_video = self.temp_dir / f"{image_name}_bg_{int(target_duration)}s.mp4"
            
            # 转换为视频
            success = self.image_to_video(
                image_path, str(temp_video), 
                target_duration, resolution, effects=effects
            )
            
            if success:
                return str(temp_video)
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ 创建动态背景失败: {e}")
            return None
    
    def get_background_by_category(self, category: str = None, 
                                  style: str = None) -> Optional[str]:
        """根据类别获取背景"""
        # 按类别组织背景
        category_patterns = {
            "dance": ["dance", "studio", "ballroom"],
            "gym": ["gym", "fitness", "workout"],
            "stage": ["stage", "theater", "concert"],
            "neutral": ["neutral", "simple", "minimal"],
            "gradient": ["gradient", "color", "abstract"]
        }
        
        # 搜索图片文件
        image_files = []
        for ext in self.image_extensions:
            image_files.extend(self.backgrounds_dir.rglob(f"*{ext}"))
        
        # 搜索视频文件
        video_files = []
        for ext in self.video_extensions:
            video_files.extend(self.backgrounds_dir.rglob(f"*{ext}"))
        
        # 如果指定了类别，按类别筛选
        if category and category in category_patterns:
            patterns = category_patterns[category]
            filtered_images = []
            filtered_videos = []
            
            for pattern in patterns:
                # 筛选图片
                for img in image_files:
                    if pattern.lower() in img.name.lower():
                        filtered_images.append(img)
                
                # 筛选视频
                for vid in video_files:
                    if pattern.lower() in vid.name.lower():
                        filtered_videos.append(vid)
            
            # 优先使用视频文件
            if filtered_videos:
                selected = random.choice(filtered_videos)
                logger.info(f"🎨 选择视频背景: {selected.name}")
                return str(selected)
            
            # 如果没有视频，使用图片生成
            if filtered_images:
                selected = random.choice(filtered_images)
                logger.info(f"🎨 选择图片背景: {selected.name}")
                return str(selected)
        
        # 如果没有指定类别或找不到，随机选择
        all_files = image_files + video_files
        if all_files:
            selected = random.choice(all_files)
            logger.info(f"🎨 随机选择背景: {selected.name}")
            return str(selected)
        
        return None
    
    def generate_background_for_video(self, video_path: str, category: str = None,
                                    effects: List[str] = None) -> Optional[str]:
        """为指定视频生成背景"""
        try:
            # 获取视频时长
            duration = self.get_video_duration(video_path)
            
            # 获取背景文件
            background_path = self.get_background_by_category(category)
            if not background_path:
                logger.warning("⚠️ 没有找到合适的背景文件")
                return None
            
            # 如果是图片，转换为视频
            if Path(background_path).suffix.lower() in self.image_extensions:
                logger.info(f"🔄 将图片转换为视频背景: {Path(background_path).name}")
                return self.create_dynamic_background(
                    background_path, duration, effects=effects
                )
            else:
                # 如果是视频，检查时长是否匹配
                bg_duration = self.get_video_duration(background_path)
                if abs(bg_duration - duration) > 5:  # 允许5秒误差
                    logger.info(f"🔄 调整背景视频时长: {bg_duration}s → {duration}s")
                    return self.adjust_video_duration(background_path, duration)
                else:
                    return background_path
                    
        except Exception as e:
            logger.error(f"❌ 生成背景失败: {e}")
            return None
    
    def adjust_video_duration(self, video_path: str, target_duration: float) -> Optional[str]:
        """调整视频时长"""
        try:
            output_path = self.temp_dir / f"adjusted_{Path(video_path).name}"
            
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-t", str(target_duration),
                "-c", "copy",  # 快速复制，不重新编码
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ 视频时长调整完成: {output_path}")
                return str(output_path)
            else:
                logger.error(f"❌ 视频时长调整失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 调整视频时长异常: {e}")
            return None
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """清理临时文件"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_count = 0
            for temp_file in self.temp_dir.rglob("*"):
                if temp_file.is_file():
                    file_age = current_time - temp_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        temp_file.unlink()
                        cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 清理了 {cleaned_count} 个临时文件")
                
        except Exception as e:
            logger.error(f"❌ 清理临时文件失败: {e}")
    
    def list_available_backgrounds(self) -> Dict:
        """列出可用的背景"""
        backgrounds = {
            "images": {},
            "videos": {},
            "categories": {}
        }
        
        # 统计图片
        for ext in self.image_extensions:
            files = list(self.backgrounds_dir.rglob(f"*{ext}"))
            if files:
                backgrounds["images"][ext] = len(files)
        
        # 统计视频
        for ext in self.video_extensions:
            files = list(self.backgrounds_dir.rglob(f"*{ext}"))
            if files:
                backgrounds["videos"][ext] = len(files)
        
        # 按类别统计
        category_patterns = {
            "dance": ["dance", "studio", "ballroom"],
            "gym": ["gym", "fitness", "workout"],
            "stage": ["stage", "theater", "concert"],
            "neutral": ["neutral", "simple", "minimal"],
            "gradient": ["gradient", "color", "abstract"]
        }
        
        for category, patterns in category_patterns.items():
            count = 0
            for pattern in patterns:
                for ext in self.image_extensions + self.video_extensions:
                    files = list(self.backgrounds_dir.rglob(f"*{pattern}*{ext}"))
                    count += len(files)
            if count > 0:
                backgrounds["categories"][category] = count
        
        return backgrounds

def main():
    """主函数"""
    print("🎨 背景生成器")
    print("=" * 40)
    
    generator = BackgroundGenerator()
    
    # 显示可用背景
    backgrounds = generator.list_available_backgrounds()
    
    print("\n📁 可用背景统计:")
    if backgrounds["images"]:
        print("   📷 图片文件:")
        for ext, count in backgrounds["images"].items():
            print(f"      {ext}: {count} 个")
    
    if backgrounds["videos"]:
        print("   🎬 视频文件:")
        for ext, count in backgrounds["videos"].items():
            print(f"      {ext}: {count} 个")
    
    if backgrounds["categories"]:
        print("   🏷️ 按类别:")
        for category, count in backgrounds["categories"].items():
            print(f"      {category}: {count} 个")
    
    # 示例用法
    print("\n💡 使用示例:")
    print("1. 为视频生成背景:")
    print("   generator.generate_background_for_video('input.mp4', category='dance')")
    print("\n2. 图片转视频:")
    print("   generator.image_to_video('bg.jpg', 'bg.mp4', duration=60)")
    print("\n3. 清理临时文件:")
    print("   generator.cleanup_temp_files()")

if __name__ == "__main__":
    main()
