#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dance项目主入口
AI视频处理自动化系统
"""

import sys
import argparse
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core import task_database
from src.automation import viggle_automation
from src.processing import background_generator, background_replacement, rtx3060_pipeline

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Dance项目 - AI视频处理自动化系统")
    parser.add_argument("command", choices=[
        "status", "full", "preprocess", "viggle", "gpu", "background", "test"
    ], help="执行命令")
    parser.add_argument("--test-mode", action="store_true", help="测试模式")
    parser.add_argument("--background", type=str, help="背景类别")
    parser.add_argument("--effects", nargs="+", help="特效列表")
    
    args = parser.parse_args()
    
    if args.command == "status":
        show_status()
    elif args.command == "full":
        run_full_pipeline(args.test_mode)
    elif args.command == "preprocess":
        run_preprocess()
    elif args.command == "viggle":
        run_viggle_automation()
    elif args.command == "gpu":
        run_gpu_pipeline()
    elif args.command == "background":
        run_background_replacement(args.background, args.effects)
    elif args.command == "test":
        run_tests()

def show_status():
    """显示项目状态"""
    print("📊 Dance项目状态:")
    print("=" * 60)
    
    # 使用数据库统计信息
    try:
        stats = task_database.task_db.get_overall_stats()
        
        print(f"📊 任务统计:")
        print(f"   总任务数: {stats.get('total_tasks', 0)}")
        print(f"   已完成: {stats.get('completed_tasks', 0)}")
        print(f"   失败: {stats.get('failed_tasks', 0)}")
        print(f"   待处理: {stats.get('pending_tasks', 0)}")
        print(f"   处理中: {stats.get('processing_tasks', 0)}")
        print(f"   成功率: {stats.get('success_rate', 0):.1f}%")
        print(f"   平均处理时间: {stats.get('avg_processing_time', 0):.1f}秒")
        
    except Exception as e:
        print(f"❌ 数据库模块错误: {e}")
    
    # 检查输入目录
    input_dir = Path("tasks_in")
    if input_dir.exists():
        video_files = list(input_dir.glob("*.mp4"))
        print(f"\n📁 输入视频: {len(video_files)} 个文件")
        for video in video_files[:5]:  # 只显示前5个
            print(f"   - {video.name}")
        if len(video_files) > 5:
            print(f"   ... 还有 {len(video_files) - 5} 个文件")
    else:
        print("\n📁 输入目录不存在")
    
    # 检查输出目录
    output_dir = Path("downloads")
    if output_dir.exists():
        output_files = list(output_dir.glob("*.mp4"))
        print(f"📁 输出视频: {len(output_files)} 个文件")
    else:
        print("📁 输出目录不存在")
    
    print("\n💡 使用以下命令查看更多信息:")
    print("   python tools/task_monitor.py stats     - 详细统计")
    print("   python tools/task_monitor.py pending   - 待处理任务")
    print("   python tools/task_monitor.py recent    - 最近任务")

def run_full_pipeline(test_mode=False):
    """运行完整Pipeline"""
    print("🚀 启动完整Pipeline...")
    if test_mode:
        print("🧪 测试模式")
    # 这里实现完整的Pipeline逻辑

def run_preprocess():
    """运行预处理"""
    print("🔧 运行视频预处理...")
    # 这里实现预处理逻辑

def run_viggle_automation():
    """运行Viggle自动化"""
    print("🎭 启动Viggle自动化...")
    # 这里实现Viggle自动化逻辑

def run_gpu_pipeline():
    """运行GPU处理Pipeline"""
    print("🎮 启动GPU处理Pipeline...")
    # 这里实现GPU处理逻辑

def run_background_replacement(background_type=None, effects=None):
    """运行背景替换"""
    print("🎨 启动背景替换...")
    if background_type:
        print(f"   背景类型: {background_type}")
    if effects:
        print(f"   特效: {', '.join(effects)}")
    # 这里实现背景替换逻辑

def run_tests():
    """运行测试"""
    print("🧪 运行测试...")
    # 这里实现测试逻辑

if __name__ == "__main__":
    main()
