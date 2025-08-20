#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dance项目系统测试脚本
"""

import sys
from pathlib import Path
import json

def test_directory_structure():
    """测试目录结构"""
    print("📁 测试目录结构...")
    
    required_dirs = [
        "config",
        "tasks_in", 
        "downloads",
        "logs",
        "secrets",
        "input/people"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name}/ 目录存在")
        else:
            print(f"❌ {dir_name}/ 目录不存在")
            all_exist = False
    
    return all_exist

def test_config_files():
    """测试配置文件"""
    print("\n🔧 测试配置文件...")
    
    config_files = [
        "config/viggle_config.json",
        "config/accounts.json"
    ]
    
    all_exist = True
    for config_file in config_files:
        file_path = Path(config_file)
        if file_path.exists():
            print(f"✅ {config_file} 存在")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"   - 配置有效")
            except Exception as e:
                print(f"   - 配置无效: {e}")
                all_exist = False
        else:
            print(f"❌ {config_file} 不存在")
            all_exist = False
    
    return all_exist

def test_input_files():
    """测试输入文件"""
    print("\n📹 测试输入文件...")
    
    # 检查视频文件
    tasks_in_dir = Path("tasks_in")
    video_files = list(tasks_in_dir.glob("*.mp4"))
    
    if video_files:
        print(f"✅ 找到 {len(video_files)} 个视频文件")
        for video in video_files:
            print(f"   - {video.name}")
    else:
        print("⚠️ 没有找到视频文件")
        print("   请在 tasks_in/ 目录下放置测试视频文件")
    
    # 检查人物文件
    people_dir = Path("input/people")
    people_files = list(people_dir.glob("*.jpg")) + list(people_dir.glob("*.png"))
    
    if people_files:
        print(f"✅ 找到 {len(people_files)} 个人物图片")
        for people in people_files:
            print(f"   - {people.name}")
    else:
        print("⚠️ 没有找到人物图片")
        print("   请在 input/people/ 目录下放置人物图片")
    
    return len(video_files) > 0

def test_modules():
    """测试模块导入"""
    print("\n🧩 测试模块导入...")
    
    try:
        sys.path.append('.')
        from scripts.viggle_playwright_optimized import ViggleProcessor
        print("✅ ViggleProcessor 模块导入成功")
        
        # 测试创建实例
        processor = ViggleProcessor()
        print("✅ ViggleProcessor 实例创建成功")
        
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 Dance项目系统测试")
    print("=" * 50)
    
    tests = [
        ("目录结构", test_directory_structure),
        ("配置文件", test_config_files),
        ("输入文件", test_input_files),
        ("模块导入", test_modules)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {str(e)}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:12} : {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统已准备就绪")
        print("\n🚀 下一步:")
        print("1. 添加真实视频到 tasks_in/ 目录")
        print("2. 添加人物图片到 input/people/ 目录")
        print("3. 配置Viggle账号: python scripts/login_once.py")
        print("4. 运行自动化: python scripts/viggle_playwright_optimized.py")
    elif passed >= total * 0.8:
        print("⚠️ 大部分测试通过，需要配置一些参数")
    else:
        print("❌ 多个测试失败，需要修复配置问题")

if __name__ == "__main__":
    main()
