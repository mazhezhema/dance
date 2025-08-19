#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle 环境测试脚本
基于 engineering-memory 的测试最佳实践
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

async def test_environment():
    """测试环境"""
    print("🧪 环境测试开始...")
    test_results = {}
    
    # 1. Python版本检查
    python_version = sys.version_info
    if python_version >= (3, 7):
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        test_results["python_version"] = True
    else:
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}.{python_version.micro}")
        test_results["python_version"] = False
    
    # 2. 依赖库检查
    required_modules = [
        ("playwright", "Playwright"),
        ("asyncio", "AsyncIO"),
        ("json", "JSON"),
        ("pathlib", "PathLib"),
        ("hashlib", "HashLib"),
        ("logging", "Logging")
    ]
    
    missing_modules = []
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {display_name}: 已安装")
        except ImportError:
            print(f"❌ {display_name}: 未安装")
            missing_modules.append(module_name)
    
    test_results["dependencies"] = len(missing_modules) == 0
    
    # 3. Playwright浏览器检查
    try:
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()
        
        # 检查浏览器
        browsers = []
        try:
            browser = await playwright.chromium.launch(headless=True)
            await browser.close()
            browsers.append("Chromium")
            print("✅ Chromium浏览器: 可用")
        except Exception as e:
            print(f"❌ Chromium浏览器: 不可用 - {str(e)}")
        
        await playwright.stop()
        test_results["playwright"] = len(browsers) > 0
        
    except Exception as e:
        print(f"❌ Playwright测试失败: {str(e)}")
        test_results["playwright"] = False
    
    # 4. 目录结构检查
    required_dirs = [
        "input/videos",
        "input/people", 
        "output",
        "profiles",
        "logs",
        "temp"
    ]
    
    dirs_ok = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ 目录: {dir_path}")
        else:
            print(f"❌ 目录缺失: {dir_path}")
            dirs_ok = False
    
    test_results["directories"] = dirs_ok
    
    # 5. 配置文件检查
    config_file = Path("config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查账号配置
            accounts = config.get("accounts", [])
            if accounts and len(accounts) > 0:
                print(f"✅ 配置文件: 找到 {len(accounts)} 个账号")
                
                # 检查账号完整性
                valid_accounts = 0
                for i, account in enumerate(accounts):
                    if all(key in account for key in ["email", "password"]):
                        valid_accounts += 1
                
                if valid_accounts == len(accounts):
                    print(f"✅ 账号配置: {valid_accounts} 个账号配置完整")
                    test_results["config"] = True
                else:
                    print(f"❌ 账号配置: {len(accounts) - valid_accounts} 个账号配置不完整")
                    test_results["config"] = False
            else:
                print("❌ 配置文件: 未找到账号配置")
                test_results["config"] = False
                
        except Exception as e:
            print(f"❌ 配置文件解析失败: {str(e)}")
            test_results["config"] = False
    else:
        print("❌ 配置文件: config.json 不存在")
        test_results["config"] = False
    
    # 6. 素材文件检查
    videos_dir = Path("input/videos")
    people_dir = Path("input/people")
    
    video_files = []
    if videos_dir.exists():
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        for ext in video_extensions:
            video_files.extend(videos_dir.glob(f"*{ext}"))
            video_files.extend(videos_dir.glob(f"*{ext.upper()}"))
    
    people_files = []
    if people_dir.exists():
        image_extensions = ['.jpg', '.jpeg', '.png']
        for ext in image_extensions:
            people_files.extend(people_dir.glob(f"*{ext}"))
            people_files.extend(people_dir.glob(f"*{ext.upper()}"))
    
    if len(video_files) > 0:
        print(f"✅ 视频文件: 找到 {len(video_files)} 个")
        test_results["videos"] = True
    else:
        print("⚠️  视频文件: 未找到 (可在 input/videos/ 中添加)")
        test_results["videos"] = False
    
    if len(people_files) > 0:
        print(f"✅ 人像文件: 找到 {len(people_files)} 个")
        test_results["people"] = True
    else:
        print("⚠️  人像文件: 未找到 (可在 input/people/ 中添加)")
        test_results["people"] = False
    
    return test_results

def generate_test_report(test_results):
    """生成测试报告"""
    print("\n" + "="*60)
    print("📊 测试报告")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    print(f"总测试项目: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    print("\n详细结果:")
    status_map = {
        "python_version": "Python版本",
        "dependencies": "依赖库",
        "playwright": "Playwright浏览器",
        "directories": "目录结构",
        "config": "配置文件",
        "videos": "视频素材",
        "people": "人像素材"
    }
    
    for key, result in test_results.items():
        name = status_map.get(key, key)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    # 生成建议
    print("\n💡 建议:")
    if not test_results.get("python_version"):
        print("  • 升级到 Python 3.7 或更高版本")
    
    if not test_results.get("dependencies"):
        print("  • 运行: pip install playwright")
    
    if not test_results.get("playwright"):
        print("  • 运行: playwright install")
    
    if not test_results.get("directories"):
        print("  • 运行: python setup_viggle.py 创建目录")
    
    if not test_results.get("config"):
        print("  • 运行: python setup_viggle.py 配置账号")
    
    if not test_results.get("videos"):
        print("  • 将视频文件放入 input/videos/ 目录")
    
    if not test_results.get("people"):
        print("  • 将人像文件放入 input/people/ 目录")
    
    # 就绪状态
    critical_tests = ["python_version", "dependencies", "playwright", "directories", "config"]
    critical_passed = all(test_results.get(test, False) for test in critical_tests)
    
    print("\n🎯 状态评估:")
    if critical_passed:
        if test_results.get("videos") and test_results.get("people"):
            print("  🎉 完全就绪! 可以开始批量处理")
        else:
            print("  ⚠️  环境就绪，等待素材文件")
    else:
        print("  ❌ 环境未就绪，请按建议修复问题")

async def main():
    """主函数"""
    print("🎭 Viggle 环境测试")
    print("基于 engineering-memory 测试框架")
    print("=" * 60)
    
    try:
        test_results = await test_environment()
        generate_test_report(test_results)
        
        # 保存测试报告
        report_file = Path("logs") / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "test_results": test_results,
                "summary": {
                    "total": len(test_results),
                    "passed": sum(1 for r in test_results.values() if r),
                    "failed": sum(1 for r in test_results.values() if not r)
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 测试报告已保存: {report_file}")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
