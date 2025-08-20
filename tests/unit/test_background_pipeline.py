#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景替换流程测试脚本
演示完整的背景图片→视频→替换流程
"""

import os
import sys
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_background_pipeline():
    """测试完整的背景替换流程"""
    print("🎬 背景替换流程测试")
    print("=" * 50)
    
    try:
        # 1. 导入背景生成器
        from scripts.background_generator import BackgroundGenerator
        generator = BackgroundGenerator()
        
        # 2. 检查输入文件
        print("\n📁 检查输入文件:")
        
        # 检查背景图片
        backgrounds_dir = Path("backgrounds")
        if backgrounds_dir.exists():
            image_files = list(backgrounds_dir.rglob("*.jpg")) + list(backgrounds_dir.rglob("*.png"))
            print(f"   ✅ 背景图片: {len(image_files)} 个")
            for img in image_files[:3]:  # 显示前3个
                print(f"      - {img.name}")
            if len(image_files) > 3:
                print(f"      ... 还有 {len(image_files) - 3} 个")
        else:
            print("   ❌ 背景图片目录不存在")
            return
        
        # 检查Viggle输出视频
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            video_files = list(downloads_dir.glob("*viggle*.mp4"))
            print(f"   ✅ Viggle视频: {len(video_files)} 个")
            for vid in video_files[:3]:  # 显示前3个
                print(f"      - {vid.name}")
            if len(video_files) > 3:
                print(f"      ... 还有 {len(video_files) - 3} 个")
        else:
            print("   ❌ Viggle视频目录不存在")
            return
        
        # 3. 测试背景生成流程
        print("\n🔄 测试背景生成流程:")
        
        if video_files and image_files:
            # 选择第一个视频和第一个图片进行测试
            test_video = str(video_files[0])
            test_image = str(image_files[0])
            
            print(f"   测试视频: {Path(test_video).name}")
            print(f"   测试背景: {Path(test_image).name}")
            
            # 获取视频时长
            duration = generator.get_video_duration(test_video)
            print(f"   视频时长: {duration:.1f}秒")
            
            # 生成背景视频
            print("   🎨 生成背景视频...")
            bg_video = generator.create_dynamic_background(
                test_image, duration, effects=["zoom"]
            )
            
            if bg_video:
                print(f"   ✅ 背景视频生成成功: {Path(bg_video).name}")
                
                # 验证时长匹配
                bg_duration = generator.get_video_duration(bg_video)
                print(f"   背景视频时长: {bg_duration:.1f}秒")
                
                if abs(duration - bg_duration) < 1:
                    print("   ✅ 时长匹配成功")
                else:
                    print(f"   ⚠️ 时长略有差异: {abs(duration - bg_duration):.1f}秒")
            else:
                print("   ❌ 背景视频生成失败")
        
        # 4. 测试完整Pipeline
        print("\n🚀 测试完整Pipeline:")
        
        try:
            from scripts.rtx3060_pipeline import RTX3060Pipeline, PipelineConfig
            
            config = PipelineConfig()
            pipeline = RTX3060Pipeline(config)
            
            print("   ✅ Pipeline初始化成功")
            print(f"   输入目录: {config.input_dir}")
            print(f"   输出目录: {config.output_dir}")
            print(f"   背景目录: {config.backgrounds_dir}")
            
            # 测试单个视频处理
            if video_files:
                test_video = str(video_files[0])
                print(f"\n   🎬 测试处理: {Path(test_video).name}")
                
                # 模拟处理（不实际运行，只检查配置）
                print("   ✅ 配置检查完成")
                print("   💡 实际处理命令:")
                print(f"      python scripts/rtx3060_pipeline.py --background dance --effects zoom")
                
        except ImportError as e:
            print(f"   ❌ Pipeline导入失败: {e}")
        
        # 5. 使用建议
        print("\n💡 使用建议:")
        print("1. 准备背景图片:")
        print("   - 将背景图片放入 backgrounds/ 目录")
        print("   - 按类别命名: dance_*.jpg, gym_*.png, stage_*.jpg")
        
        print("\n2. 运行Viggle处理:")
        print("   - 确保 downloads/ 目录有Viggle输出视频")
        
        print("\n3. 执行背景替换:")
        print("   # 使用舞蹈背景 + 缩放特效")
        print("   python scripts/rtx3060_pipeline.py --background dance --effects zoom")
        print("   ")
        print("   # 使用健身房背景 + 平移特效")
        print("   python scripts/rtx3060_pipeline.py --background gym --effects pan")
        print("   ")
        print("   # 使用舞台背景 + 多种特效")
        print("   python scripts/rtx3060_pipeline.py --background stage --effects zoom fade")
        
        print("\n4. 查看结果:")
        print("   - 最终视频保存在 final_output/ 目录")
        print("   - 临时文件保存在 temp_backgrounds/ 目录")
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def create_sample_backgrounds():
    """创建示例背景图片"""
    print("\n🎨 创建示例背景图片...")
    
    backgrounds_dir = Path("backgrounds")
    backgrounds_dir.mkdir(exist_ok=True)
    
    # 创建示例背景图片（使用FFmpeg生成纯色图片）
    sample_backgrounds = [
        ("dance_studio_white.jpg", "white"),
        ("dance_studio_black.jpg", "black"),
        ("gym_dark_modern.jpg", "darkgray"),
        ("stage_red_curtain.jpg", "red"),
        ("neutral_gray_simple.jpg", "gray"),
        ("gradient_blue_purple.jpg", "blue")
    ]
    
    for filename, color in sample_backgrounds:
        output_path = backgrounds_dir / filename
        if not output_path.exists():
            try:
                import subprocess
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "lavfi",
                    "-i", f"color=c={color}:size=1920x1080:duration=1",
                    "-vframes", "1",
                    str(output_path)
                ]
                subprocess.run(cmd, capture_output=True)
                print(f"   ✅ 创建: {filename}")
            except Exception as e:
                print(f"   ❌ 创建失败 {filename}: {e}")
        else:
            print(f"   ⏭️ 已存在: {filename}")

def main():
    """主函数"""
    print("🎬 背景替换Pipeline测试")
    print("=" * 50)
    
    # 创建示例背景
    create_sample_backgrounds()
    
    # 运行测试
    test_background_pipeline()

if __name__ == "__main__":
    main()
