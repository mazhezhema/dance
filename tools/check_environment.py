#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检查脚本
验证Dance项目运行所需的所有环境和依赖
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import importlib
import platform

def check_python_version():
    """检查Python版本"""
    print("🐍 Python环境检查:")
    version = sys.version_info
    print(f"   Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("   ✅ Python版本符合要求 (3.8+)")
        return True
    else:
        print("   ❌ Python版本过低，需要3.8+")
        return False

def check_ffmpeg():
    """检查FFmpeg是否安装"""
    print("\n🎬 FFmpeg检查:")
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   ✅ FFmpeg已安装: {version_line}")
            return True
        else:
            print("   ❌ FFmpeg不可用")
            return False
    except FileNotFoundError:
        print("   ❌ FFmpeg未安装")
        print("   💡 安装方法:")
        print("      Windows: 下载并添加到PATH")
        print("      Linux: sudo apt install ffmpeg")
        print("      macOS: brew install ffmpeg")
        return False

def check_chrome():
    """检查Chrome是否安装"""
    print("\n🌐 Chrome浏览器检查:")
    system = platform.system()
    
    chrome_paths = {
        "Windows": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ],
        "Linux": [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser"
        ],
        "Darwin": [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ]
    }
    
    paths = chrome_paths.get(system, [])
    for path in paths:
        if Path(path).exists():
            print(f"   ✅ Chrome已安装: {path}")
            return True
    
    print("   ❌ Chrome未找到")
    print("   💡 请安装Chrome或Chromium浏览器")
    return False

def check_python_packages():
    """检查Python包依赖"""
    print("\n📦 Python包依赖检查:")
    
    required_packages = [
        "cv2", "numpy", "PIL", "requests", "aiohttp", 
        "playwright", "sqlite3", "psutil", "GPUtil"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == "cv2":
                import cv2
                print(f"   ✅ {package} (OpenCV)")
            elif package == "PIL":
                from PIL import Image
                print(f"   ✅ {package} (Pillow)")
            else:
                importlib.import_module(package)
                print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n   💡 安装缺失包:")
        print(f"      pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_directories():
    """检查必要目录"""
    print("\n📁 目录结构检查:")
    
    required_dirs = [
        "tasks_in", "downloads", "final_output", "backgrounds",
        "input/people", "input/music", "temp_backgrounds", 
        "temp_gpu", "logs", "config", "secrets"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            files = len(list(Path(dir_path).glob("*")))
            print(f"   ✅ {dir_path} ({files} 个文件)")
        else:
            print(f"   ❌ {dir_path} 不存在")
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"\n   💡 创建缺失目录:")
        for dir_path in missing_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"      mkdir -p {dir_path}")
    
    return len(missing_dirs) == 0

def check_config_files():
    """检查配置文件"""
    print("\n⚙️ 配置文件检查:")
    
    config_files = [
        "config.json",
        "config/accounts.json",
        "config/viggle_config.json"
    ]
    
    missing_configs = []
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"   ✅ {config_file}")
        else:
            print(f"   ❌ {config_file} 不存在")
            missing_configs.append(config_file)
    
    if missing_configs:
        print(f"\n   💡 需要创建配置文件:")
        for config_file in missing_configs:
            print(f"      {config_file}")
    
    return len(missing_configs) == 0

def check_sample_files():
    """检查示例文件"""
    print("\n📄 示例文件检查:")
    
    # 检查输入视频
    video_files = list(Path("tasks_in").glob("*.mp4"))
    if video_files:
        print(f"   ✅ 输入视频: {len(video_files)} 个")
        for video in video_files[:3]:
            print(f"      - {video.name}")
        if len(video_files) > 3:
            print(f"      ... 还有 {len(video_files) - 3} 个")
    else:
        print("   ⚠️ 输入视频: 0 个 (需要添加测试视频)")
    
    # 检查背景图片
    bg_files = list(Path("backgrounds").glob("*.jpg")) + list(Path("backgrounds").glob("*.png"))
    if bg_files:
        print(f"   ✅ 背景图片: {len(bg_files)} 个")
        for bg in bg_files[:3]:
            print(f"      - {bg.name}")
        if len(bg_files) > 3:
            print(f"      ... 还有 {len(bg_files) - 3} 个")
    else:
        print("   ⚠️ 背景图片: 0 个 (需要添加背景素材)")
    
    # 检查人物图片
    people_files = list(Path("input/people").glob("*.jpg")) + list(Path("input/people").glob("*.png"))
    if people_files:
        print(f"   ✅ 人物图片: {len(people_files)} 个")
        for person in people_files[:3]:
            print(f"      - {person.name}")
        if len(people_files) > 3:
            print(f"      ... 还有 {len(people_files) - 3} 个")
    else:
        print("   ⚠️ 人物图片: 0 个 (需要添加人物素材)")

def check_gpu():
    """检查GPU状态"""
    print("\n🎮 GPU检查:")
    
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            for gpu in gpus:
                print(f"   ✅ GPU: {gpu.name}")
                print(f"      显存: {gpu.memoryTotal}MB")
                print(f"      使用率: {gpu.load*100:.1f}%")
                print(f"      显存使用: {gpu.memoryUsed}/{gpu.memoryTotal}MB")
        else:
            print("   ⚠️ 未检测到GPU")
    except ImportError:
        print("   ⚠️ GPUtil未安装，无法检查GPU")
    except Exception as e:
        print(f"   ⚠️ GPU检查失败: {e}")

def check_system_info():
    """检查系统信息"""
    print("\n💻 系统信息:")
    print(f"   操作系统: {platform.system()} {platform.release()}")
    print(f"   架构: {platform.machine()}")
    print(f"   Python路径: {sys.executable}")
    
    # 检查内存
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"   内存: {memory.total // (1024**3)}GB 总内存")
        print(f"   可用: {memory.available // (1024**3)}GB 可用内存")
    except ImportError:
        print("   ⚠️ psutil未安装，无法检查内存")

def main():
    """主函数"""
    print("🔍 Dance项目环境检查")
    print("=" * 50)
    
    checks = []
    
    # 执行各项检查
    checks.append(check_python_version())
    checks.append(check_ffmpeg())
    checks.append(check_chrome())
    checks.append(check_python_packages())
    checks.append(check_directories())
    checks.append(check_config_files())
    check_sample_files()
    check_gpu()
    check_system_info()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 检查总结:")
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"   🎉 所有必需检查通过! ({passed}/{total})")
        print("   ✅ 环境已准备就绪，可以开始使用Dance项目")
    else:
        print(f"   ⚠️ 部分检查未通过 ({passed}/{total})")
        print("   💡 请根据上述提示修复问题")
    
    print("\n💡 下一步:")
    print("   1. 添加测试视频到 tasks_in/ 目录")
    print("   2. 添加背景图片到 backgrounds/ 目录")
    print("   3. 添加人物图片到 input/people/ 目录")
    print("   4. 配置账号信息到 config/accounts.json")
    print("   5. 运行 python dance_main.py status 检查系统状态")

if __name__ == "__main__":
    main()
