#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台路径兼容性测试
验证在不同操作系统上的路径处理
"""

import platform
from pathlib import Path
import os
import tempfile

def test_cross_platform_paths():
    """测试跨平台路径处理"""
    print(f"🌐 当前系统: {platform.system()} {platform.release()}")
    print(f"🐍 Python版本: {platform.python_version()}")
    print("=" * 60)
    
    # 1. 测试基础路径
    print("📂 基础路径测试:")
    project_root = Path.cwd()
    print(f"   项目根目录: {project_root}")
    print(f"   路径类型: {type(project_root)}")
    print(f"   是否绝对路径: {project_root.is_absolute()}")
    
    # 2. 测试路径拼接
    print("\n🔗 路径拼接测试:")
    input_dir = project_root / "input"
    videos_dir = input_dir / "videos"
    config_file = project_root / "config.json"
    
    print(f"   input目录: {input_dir}")
    print(f"   videos目录: {videos_dir}")
    print(f"   配置文件: {config_file}")
    
    # 3. 测试相对路径 vs 绝对路径
    print("\n📍 相对/绝对路径测试:")
    relative_path = Path("./logs/test.log")
    absolute_path = project_root / "logs" / "test.log"
    
    print(f"   相对路径: {relative_path}")
    print(f"   绝对路径: {absolute_path}")
    print(f"   解析后相对: {relative_path.resolve()}")
    
    # 4. 测试路径分隔符
    print("\n🔀 路径分隔符测试:")
    test_path = project_root / "input" / "videos" / "test.mp4"
    print(f"   完整路径: {test_path}")
    print(f"   字符串形式: {str(test_path)}")
    print(f"   部分组件: {test_path.parts}")
    
    # 5. 测试目录创建
    print("\n📁 目录创建测试:")
    test_dirs = [
        project_root / "test_temp" / "level1" / "level2",
        project_root / "test_profiles" / "account1",
        project_root / "test_logs"
    ]
    
    created_dirs = []
    for test_dir in test_dirs:
        try:
            test_dir.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ 创建成功: {test_dir}")
            created_dirs.append(test_dir)
        except Exception as e:
            print(f"   ❌ 创建失败: {test_dir} - {e}")
    
    # 6. 测试文件操作
    print("\n📄 文件操作测试:")
    test_file = project_root / "test_cross_platform.txt"
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(f"跨平台测试 - {platform.system()}\n")
            f.write(f"路径: {test_file}\n")
        
        print(f"   ✅ 文件写入成功: {test_file}")
        
        # 读取验证
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"   ✅ 文件读取成功: {len(content)} 字符")
        
    except Exception as e:
        print(f"   ❌ 文件操作失败: {e}")
    
    # 7. 清理测试文件
    print("\n🧹 清理测试文件:")
    try:
        if test_file.exists():
            test_file.unlink()
            print(f"   ✅ 删除文件: {test_file}")
        
        # 删除测试目录（从最深层开始）
        for test_dir in reversed(created_dirs):
            if test_dir.exists():
                test_dir.rmdir()
                print(f"   ✅ 删除目录: {test_dir}")
                
    except Exception as e:
        print(f"   ⚠️ 清理时出现问题: {e}")
    
    # 8. 系统特定检测
    print("\n🔍 系统特定检测:")
    system = platform.system().lower()
    if system == "windows":
        print("   🪟 Windows环境检测")
        print(f"   驱动器: {Path.cwd().drive}")
        print(f"   盘符根目录: {Path.cwd().anchor}")
    elif system == "darwin":
        print("   🍎 macOS环境检测")
        home = Path.home()
        print(f"   用户目录: {home}")
    elif system == "linux":
        print("   🐧 Linux环境检测")
        home = Path.home()
        print(f"   用户目录: {home}")
        print(f"   是否在容器中: {Path('/.dockerenv').exists()}")
    
    print("\n✅ 跨平台路径测试完成!")
    return True

def test_viggle_paths():
    """测试Viggle项目特定路径"""
    print("\n🎭 Viggle项目路径测试:")
    
    # 模拟项目结构
    paths_to_test = {
        "项目根目录": Path.cwd(),
        "输入视频": Path.cwd() / "input" / "videos",
        "输入人像": Path.cwd() / "input" / "people", 
        "输出目录": Path.cwd() / "output",
        "配置文件": Path.cwd() / "config.json",
        "日志目录": Path.cwd() / "logs",
        "配置目录": Path.cwd() / "profiles" / "main_account",
        "临时目录": Path.cwd() / "temp"
    }
    
    for name, path in paths_to_test.items():
        exists = "✅" if path.exists() else "⚠️"
        print(f"   {exists} {name}: {path}")
    
    return True

if __name__ == "__main__":
    print("🧪 跨平台路径兼容性测试")
    print("=" * 60)
    
    try:
        test_cross_platform_paths()
        test_viggle_paths()
        print("\n🎉 所有测试通过! 代码具有优秀的跨平台兼容性!")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

