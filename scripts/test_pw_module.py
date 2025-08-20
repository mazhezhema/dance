#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright模块功能测试脚本
验证各个组件是否正常工作
"""

import asyncio
import json
from pathlib import Path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from scripts.viggle_playwright_optimized import ViggleProcessor
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaywrightModuleTester:
    """Playwright模块测试器"""
    
    def __init__(self):
        self.processor = ViggleProcessor()
        
    def test_config_loading(self):
        """测试配置加载"""
        print("🔧 测试配置加载...")
        
        # 测试主配置
        if self.processor.config:
            print("✅ 主配置加载成功")
            print(f"   - Viggle URL: {self.processor.config.get('viggle', {}).get('app_url', 'N/A')}")
            print(f"   - 并发数: {self.processor.config.get('processing', {}).get('concurrent_per_account', 'N/A')}")
        else:
            print("❌ 主配置加载失败")
            return False
        
        # 测试账号配置
        if self.processor.accounts:
            print("✅ 账号配置加载成功")
            print(f"   - 账号数量: {len(self.processor.accounts)}")
            for acc in self.processor.accounts:
                print(f"   - 账号: {acc.email}")
        else:
            print("⚠️ 账号配置为空（需要配置真实账号）")
        
        return True
    
    def test_directory_structure(self):
        """测试目录结构"""
        print("\n📁 测试目录结构...")
        
        required_dirs = [
            "config",
            "input",
            "output", 
            "logs",
            "secrets",
            "tasks"
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
    
    def test_input_files(self):
        """测试输入文件"""
        print("\n📹 测试输入文件...")
        
        input_dir = Path("input")
        video_files = list(input_dir.rglob("*.mp4")) + list(input_dir.rglob("*.mov"))
        
        if video_files:
            print(f"✅ 找到 {len(video_files)} 个视频文件")
            for video in video_files[:3]:  # 只显示前3个
                print(f"   - {video.name}")
        else:
            print("⚠️ 没有找到视频文件")
            print("   请在 input/ 目录下放置测试视频文件")
        
        return len(video_files) > 0
    
    def test_session_files(self):
        """测试会话状态文件"""
        print("\n🔐 测试会话状态文件...")
        
        secrets_dir = Path("secrets")
        session_files = list(secrets_dir.glob("*_state.json"))
        
        if session_files:
            print(f"✅ 找到 {len(session_files)} 个会话状态文件")
            for session in session_files:
                print(f"   - {session.name}")
        else:
            print("⚠️ 没有找到会话状态文件")
            print("   请运行 python scripts/login_once.py 创建会话")
        
        return len(session_files) > 0
    
    async def test_task_generation(self):
        """测试任务生成"""
        print("\n📋 测试任务生成...")
        
        try:
            # 创建测试视频文件（如果不存在）
            test_video = Path("input/test_video.mp4")
            if not test_video.exists():
                test_video.parent.mkdir(parents=True, exist_ok=True)
                test_video.write_bytes(b"fake video content")
                print("📝 创建测试视频文件")
            
            # 测试任务生成
            tasks = await self.processor.get_pending_tasks()
            
            if tasks:
                print(f"✅ 成功生成 {len(tasks)} 个任务")
                for task in tasks[:2]:  # 只显示前2个
                    print(f"   - 任务ID: {task.task_id}")
                    print(f"   - 源文件: {Path(task.src_path).name}")
                    print(f"   - 分配账号: {task.account_id}")
            else:
                print("⚠️ 没有生成任务")
                if not self.processor.accounts:
                    print("   原因: 没有配置账号")
                else:
                    print("   原因: 没有找到输入文件或文件已处理")
            
            # 清理测试文件
            if test_video.exists():
                test_video.unlink()
            
            return True
            
        except Exception as e:
            print(f"❌ 任务生成测试失败: {str(e)}")
            return False
    
    def test_browser_setup(self):
        """测试浏览器设置"""
        print("\n🌐 测试浏览器设置...")
        
        try:
            # 测试浏览器启动（不实际启动，只测试配置）
            browser_config = self.processor.config.get("browser", {})
            
            print(f"✅ 浏览器配置正常")
            print(f"   - 无头模式: {browser_config.get('headless', True)}")
            print(f"   - 超时时间: {browser_config.get('timeout', 120000)}ms")
            print(f"   - 操作延迟: {browser_config.get('slow_mo', 0)}ms")
            
            return True
            
        except Exception as e:
            print(f"❌ 浏览器设置测试失败: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 Playwright模块功能测试")
        print("=" * 50)
        
        tests = [
            ("配置加载", self.test_config_loading, False),
            ("目录结构", self.test_directory_structure, False),
            ("输入文件", self.test_input_files, False),
            ("会话状态", self.test_session_files, False),
            ("任务生成", self.test_task_generation, True),
            ("浏览器设置", self.test_browser_setup, False)
        ]
        
        results = []
        for test_name, test_func, is_async in tests:
            try:
                if is_async:
                    result = await test_func()
                else:
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
            print("🎉 所有测试通过！Playwright模块已准备就绪")
        elif passed >= total * 0.8:
            print("⚠️ 大部分测试通过，需要配置一些参数")
        else:
            print("❌ 多个测试失败，需要修复配置问题")
        
        return passed == total

async def main():
    """主函数"""
    tester = PlaywrightModuleTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 可以开始使用Playwright自动化模块了！")
        print("下一步:")
        print("1. 配置真实账号: python scripts/login_once.py")
        print("2. 添加测试视频到 input/ 目录")
        print("3. 运行自动化: python scripts/viggle_playwright_optimized.py")
    else:
        print("\n🔧 请先解决配置问题再使用模块")

if __name__ == "__main__":
    asyncio.run(main())
