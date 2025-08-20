#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的背景视频创建脚本
使用FFmpeg创建各种类型的背景视频
"""

import subprocess
import os
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_backgrounds():
    """创建各种背景视频"""
    
    # 创建背景目录
    backgrounds_dir = Path("backgrounds")
    backgrounds_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("🎨 开始创建背景视频...")
    
    # 1. 纯色背景
    colors = [
        ("black", "000000"),
        ("white", "FFFFFF"),
        ("gray", "808080"),
        ("blue", "0066CC"),
        ("green", "009933"),
        ("purple", "660099")
    ]
    
    for color_name, color_code in colors:
        filename = f"color_{color_name}.mp4"
        filepath = backgrounds_dir / filename
        
        cmd = [
            "ffmpeg", "-f", "lavfi",
            "-i", f"color=c=#{color_code}:size=1920x1080:duration=60",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "2M", "-y", str(filepath)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✅ 创建完成: {filename}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 创建失败: {filename} - {e}")
    
    # 2. 渐变背景
    gradients = [
        ("blue_purple", "0000FF", "800080"),
        ("orange_red", "FF6600", "FF0000"),
        ("green_blue", "00FF00", "0066CC"),
        ("purple_pink", "660099", "FF00FF")
    ]
    
    for grad_name, color1, color2 in gradients:
        filename = f"gradient_{grad_name}.mp4"
        filepath = backgrounds_dir / filename
        
        filter_complex = f"gradient=c0=#{color1}:c1=#{color2}:size=1920x1080:duration=60"
        
        cmd = [
            "ffmpeg", "-f", "lavfi",
            "-i", filter_complex,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "2M", "-y", str(filepath)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✅ 创建完成: {filename}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 创建失败: {filename} - {e}")
    
    # 3. 动态背景
    # 创建简单的动态效果
    dynamic_backgrounds = [
        ("moving_gradient", "gradient=c0=blue:c1=purple:size=1920x1080:duration=60,rotate=angle='t*0.1'"),
        ("pulsing_color", "color=c=red:size=1920x1080:duration=60,eq=brightness='sin(t)*0.1'"),
        ("wave_pattern", "color=c=blue:size=1920x1080:duration=60,wave=period=10:amplitude=50")
    ]
    
    for bg_name, filter_complex in dynamic_backgrounds:
        filename = f"dynamic_{bg_name}.mp4"
        filepath = backgrounds_dir / filename
        
        cmd = [
            "ffmpeg", "-f", "lavfi",
            "-i", filter_complex,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "2M", "-y", str(filepath)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✅ 创建完成: {filename}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 创建失败: {filename} - {e}")
    
    # 4. 创建背景索引
    create_background_index(backgrounds_dir)
    
    logger.info("🎉 背景视频创建完成！")
    logger.info(f"📁 背景文件位置: {backgrounds_dir}")

def create_background_index(backgrounds_dir):
    """创建背景视频索引"""
    video_files = list(backgrounds_dir.glob("*.mp4"))
    
    index_content = "# 背景视频索引\n\n"
    index_content += f"总数量: {len(video_files)}\n\n"
    
    # 按类型分类
    categories = {
        "纯色背景": [f for f in video_files if f.name.startswith("color_")],
        "渐变背景": [f for f in video_files if f.name.startswith("gradient_")],
        "动态背景": [f for f in video_files if f.name.startswith("dynamic_")]
    }
    
    for category, files in categories.items():
        index_content += f"## {category}\n"
        for file in files:
            size_mb = file.stat().st_size / (1024 * 1024)
            index_content += f"- {file.name} ({size_mb:.1f}MB)\n"
        index_content += "\n"
    
    # 保存索引文件
    index_file = backgrounds_dir / "README.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    logger.info(f"📝 索引文件已创建: {index_file}")

def check_ffmpeg():
    """检查FFmpeg是否可用"""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    """主函数"""
    print("🎨 背景视频创建工具")
    print("=" * 40)
    
    # 检查FFmpeg
    if not check_ffmpeg():
        print("❌ 错误: 未找到FFmpeg，请先安装FFmpeg")
        print("💡 安装方法:")
        print("  Windows: 下载 https://ffmpeg.org/download.html")
        print("  macOS: brew install ffmpeg")
        print("  Linux: sudo apt install ffmpeg")
        return
    
    print("✅ FFmpeg 已安装")
    
    # 创建背景视频
    create_backgrounds()
    
    print("\n🎉 完成！")
    print("💡 使用建议:")
    print("  1. 将背景视频放入 backgrounds/ 目录")
    print("  2. 在Pipeline中指定背景文件")
    print("  3. 根据需要调整背景类型")

if __name__ == "__main__":
    main()
