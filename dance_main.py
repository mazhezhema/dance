#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dance项目主入口
提供命令行界面来执行不同的模块
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 添加modules目录到Python路径
sys.path.append(str(Path(__file__).parent))

from modules.video_preprocessor import VideoPreprocessor
from modules.viggle_automation import ViggleAutomationModule
from modules.local_gpu_pipeline import LocalGPUPipeline
from modules.dance_orchestrator import DanceOrchestrator

def print_banner():
    """打印程序横幅"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                        Dance项目                             ║
    ║                  AI视频处理自动化系统                         ║
    ║                                                              ║
    ║  🎬 片源预处理 → 🎭 Viggle自动化 → 🎥 本地GPU处理             ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Dance AI视频处理自动化系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 运行完整pipeline
  python dance_main.py full --input ./videos --project "广场舞项目"
  
  # 只运行预处理
  python dance_main.py preprocess --input ./videos
  
  # 只运行Viggle自动化
  python dance_main.py viggle
  
  # 只运行GPU处理
  python dance_main.py gpu --input ./viggle_results
  
  # 查看项目状态
  python dance_main.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 完整pipeline命令
    full_parser = subparsers.add_parser('full', help='运行完整pipeline')
    full_parser.add_argument('--input', '-i', required=True, 
                           help='输入视频目录')
    full_parser.add_argument('--project', '-p', required=True,
                           help='项目名称')
    
    # 预处理命令
    preprocess_parser = subparsers.add_parser('preprocess', help='视频预处理')
    preprocess_parser.add_argument('--input', '-i', required=True,
                                 help='输入视频目录')
    preprocess_parser.add_argument('--output', '-o', 
                                 help='报告输出目录')
    
    # Viggle自动化命令
    viggle_parser = subparsers.add_parser('viggle', help='Viggle自动化处理')
    viggle_parser.add_argument('--queue', '-q', 
                             help='队列文件路径')
    
    # GPU处理命令
    gpu_parser = subparsers.add_parser('gpu', help='本地GPU处理')
    gpu_parser.add_argument('--input', '-i', required=True,
                          help='Viggle结果目录')
    gpu_parser.add_argument('--output', '-o',
                          help='最终输出目录')
    
    # 状态查询命令
    status_parser = subparsers.add_parser('status', help='查看项目状态')
    status_parser.add_argument('--project-id', '-p',
                             help='项目ID')
    
    # 配置命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('--init', action='store_true',
                             help='初始化配置文件')
    config_parser.add_argument('--check', action='store_true',
                             help='检查配置')
    
    return parser

async def run_full_pipeline(args):
    """运行完整pipeline"""
    print("🚀 启动完整Dance Pipeline")
    
    orchestrator = DanceOrchestrator()
    project = await orchestrator.run_full_pipeline(args.project, args.input)
    
    if project.status == "completed":
        print(f"✅ 项目完成: {project.final_outputs}/{project.input_videos_count} 视频处理成功")
    else:
        print(f"❌ 项目失败: {project.status}")
    
    return project.status == "completed"

def run_preprocess(args):
    """运行预处理"""
    print("📋 开始视频预处理")
    
    preprocessor = VideoPreprocessor()
    results = preprocessor.batch_process(args.input)
    
    if results:
        report = preprocessor.generate_report(results, args.output)
        queue = preprocessor.create_processing_queue(results)
        
        print(f"✅ 预处理完成: {len(results)}个视频，{len(queue)}个进入队列")
        return True
    else:
        print("❌ 预处理失败或无可处理视频")
        return False

async def run_viggle(args):
    """运行Viggle自动化"""
    print("🎭 开始Viggle自动化处理")
    
    automation = ViggleAutomationModule()
    
    if args.queue:
        automation.config["queue_settings"]["input_queue_file"] = args.queue
    
    await automation.run_batch_processing()
    
    completed = len([j for j in automation.job_history if j.status == "completed"])
    total = len(automation.job_history)
    
    print(f"✅ Viggle处理完成: {completed}/{total} 任务成功")
    return completed > 0

def run_gpu_pipeline(args):
    """运行GPU处理"""
    print("🎥 开始GPU Pipeline处理")
    
    pipeline = LocalGPUPipeline()
    
    if args.output:
        pipeline.config["output"]["base_directory"] = args.output
    
    pipeline.run_batch_processing(args.input)
    
    completed = len([j for j in pipeline.job_history if j.status == "completed"])
    total = len(pipeline.job_history)
    
    print(f"✅ GPU处理完成: {completed}/{total} 任务成功")
    return completed > 0

def show_status(args):
    """显示项目状态"""
    orchestrator = DanceOrchestrator()
    
    if args.project_id:
        status = orchestrator.get_project_status(args.project_id)
        if status:
            print(f"项目ID: {status['project_id']}")
            print(f"状态: {status['status']}")
            print(f"当前阶段: {status['current_stage']}")
            print(f"进度: {status['progress']}")
        else:
            print(f"❌ 项目不存在: {args.project_id}")
    else:
        projects = orchestrator.list_projects()
        if projects:
            print("📋 项目列表:")
            print("-" * 80)
            for project in projects:
                print(f"ID: {project['project_id']}")
                print(f"名称: {project['project_name']}")
                print(f"状态: {project['status']}")
                print(f"输入/输出: {project['input_count']}/{project['output_count']}")
                print(f"开始时间: {project['start_time']}")
                print("-" * 80)
        else:
            print("📭 暂无项目记录")

def init_config():
    """初始化配置文件"""
    print("⚙️ 初始化配置文件...")
    
    config_dirs = [
        "config",
        "modules", 
        "input_videos",
        "viggle_results",
        "final_output",
        "backgrounds",
        "reports",
        "logs",
        "temp"
    ]
    
    for dir_name in config_dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {dir_name}/")
    
    # 创建示例配置
    example_files = {
        "config/README.md": """# Dance项目配置目录

此目录包含各模块的配置文件：

- `preprocessor_config.json` - 预处理模块配置
- `viggle_automation_config.json` - Viggle自动化配置  
- `gpu_pipeline_config.json` - GPU处理配置
- `orchestrator_config.json` - 编排器配置

首次运行时会自动创建默认配置文件。
""",
        "input_videos/README.md": """# 输入视频目录

将待处理的原始视频文件放在这里。

支持格式：mp4, avi, mov, mkv, wmv
建议：清晰度适中，时长30秒-5分钟
""",
        "backgrounds/README.md": """# 背景视频库

存放用于背景替换的视频文件。

建议分类：
- dance_studio.mp4 - 舞蹈室背景
- gym_background.mp4 - 健身房背景  
- traditional_stage.mp4 - 传统舞台背景
- neutral_background.mp4 - 中性背景
"""
    }
    
    for file_path, content in example_files.items():
        file_path = Path(file_path)
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 创建文件: {file_path}")
    
    print("\n🎉 配置初始化完成！")
    print("💡 接下来请：")
    print("1. 将视频文件放入 input_videos/ 目录")
    print("2. 将背景视频放入 backgrounds/ 目录") 
    print("3. 运行 python dance_main.py config --check 检查配置")

def check_config():
    """检查配置"""
    print("🔍 检查系统配置...")
    
    checks = []
    
    # 检查目录
    required_dirs = ["input_videos", "backgrounds", "config"]
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            checks.append(f"✅ 目录存在: {dir_name}/")
        else:
            checks.append(f"❌ 目录缺失: {dir_name}/")
    
    # 检查视频文件
    input_dir = Path("input_videos")
    if input_dir.exists():
        video_files = list(input_dir.glob("*.mp4")) + list(input_dir.glob("*.avi"))
        checks.append(f"📁 输入视频: {len(video_files)} 个文件")
    
    # 检查背景文件
    bg_dir = Path("backgrounds")
    if bg_dir.exists():
        bg_files = list(bg_dir.glob("*.mp4"))
        checks.append(f"🎨 背景视频: {len(bg_files)} 个文件")
    
    # 检查Python依赖
    try:
        import cv2
        checks.append("✅ OpenCV 已安装")
    except ImportError:
        checks.append("❌ OpenCV 未安装 (pip install opencv-python)")
    
    try:
        import playwright
        checks.append("✅ Playwright 已安装")
    except ImportError:
        checks.append("❌ Playwright 未安装 (pip install playwright)")
    
    # 打印检查结果
    print("\n" + "="*50)
    print("📊 配置检查结果")
    print("="*50)
    for check in checks:
        print(check)
    print("="*50)

async def main():
    """主函数"""
    print_banner()
    
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'full':
            success = await run_full_pipeline(args)
            sys.exit(0 if success else 1)
            
        elif args.command == 'preprocess':
            success = run_preprocess(args)
            sys.exit(0 if success else 1)
            
        elif args.command == 'viggle':
            success = await run_viggle(args)
            sys.exit(0 if success else 1)
            
        elif args.command == 'gpu':
            success = run_gpu_pipeline(args)
            sys.exit(0 if success else 1)
            
        elif args.command == 'status':
            show_status(args)
            
        elif args.command == 'config':
            if args.init:
                init_config()
            elif args.check:
                check_config()
            else:
                print("请指定 --init 或 --check")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"💥 执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
