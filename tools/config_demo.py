#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎛️ 配置系统演示脚本
展示新配置系统的使用方法和功能
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def demo_basic_usage():
    """演示基本配置使用"""
    print("🎯 基本配置使用演示")
    print("=" * 50)
    
    try:
        from src.config.manager import get_config, config_manager
        
        # 加载配置
        config = get_config()
        print(f"✅ 配置加载成功，包含 {len(config)} 个顶级配置项")
        
        # 获取各种配置值
        print("\n📊 默认配置值:")
        print(f"  每日限制: {get_config('accounts.daily_limit')}")
        print(f"  并发限制: {get_config('accounts.concurrent_limit')}")
        print(f"  生成超时: {get_config('timeouts.generation')} ms")
        print(f"  批次大小: {get_config('batch_processing.batch_size')}")
        print(f"  GPU显存限制: {get_config('gpu_processing.memory_limit_gb')} GB")
        
        # 获取不存在的配置（测试默认值）
        print(f"  不存在的配置: {get_config('non.existent.key', 'default_value')}")
        
    except Exception as e:
        print(f"❌ 基本配置演示失败: {e}")

def demo_env_override():
    """演示环境变量覆盖"""
    print("\n🌍 环境变量覆盖演示")
    print("=" * 50)
    
    try:
        from src.config.manager import get_config, reload_config
        
        # 设置环境变量
        os.environ["DANCE_DAILY_LIMIT"] = "999"
        os.environ["DANCE_BATCH_SIZE"] = "88"
        os.environ["DANCE_LOG_LEVEL"] = "DEBUG"
        
        # 重新加载配置
        config = reload_config()
        
        print("✅ 环境变量已设置:")
        print(f"  DANCE_DAILY_LIMIT=999")
        print(f"  DANCE_BATCH_SIZE=88") 
        print(f"  DANCE_LOG_LEVEL=DEBUG")
        
        print("\n📊 覆盖后的配置值:")
        print(f"  每日限制: {get_config('accounts.daily_limit')}")
        print(f"  批次大小: {get_config('batch_processing.batch_size')}")
        print(f"  日志级别: {get_config('monitoring.log_level')}")
        
        # 清理环境变量
        for key in ["DANCE_DAILY_LIMIT", "DANCE_BATCH_SIZE", "DANCE_LOG_LEVEL"]:
            if key in os.environ:
                del os.environ[key]
                
    except Exception as e:
        print(f"❌ 环境变量演示失败: {e}")

def demo_config_adapter():
    """演示配置适配器"""
    print("\n🔌 配置适配器演示")
    print("=" * 50)
    
    try:
        from src.config.adapter import (
            adapt_account_config, 
            adapt_processing_config,
            get_timeout_ms,
            get_delay_range
        )
        
        # 测试账号配置适配
        test_account = {
            "email": "test@example.com",
            "password": "password",
            "daily_limit": None,  # null值
            "concurrent_limit": 5,  # 有值
            "rate_limit_min": None  # null值
        }
        
        print("🏷️ 账号配置适配:")
        print(f"  原始配置: {test_account}")
        
        adapted_account = adapt_account_config(test_account)
        print(f"  适配后配置: {adapted_account}")
        
        # 测试处理配置适配
        test_processing = {
            "batch_size": None,
            "max_retries": 5,
            "generate_timeout_minutes": None
        }
        
        print("\n⚙️ 处理配置适配:")
        print(f"  原始配置: {test_processing}")
        
        adapted_processing = adapt_processing_config(test_processing)
        print(f"  适配后配置: {adapted_processing}")
        
        # 测试超时获取
        print("\n⏱️ 超时值获取:")
        print(f"  生成超时: {get_timeout_ms('generation')} ms")
        print(f"  页面加载超时: {get_timeout_ms('page_load')} ms")
        print(f"  自定义超时: {get_timeout_ms('custom', 15000)} ms")
        
        # 测试延迟范围
        print("\n🕰️ 延迟范围获取:")
        human_delay = get_delay_range('human')
        typing_delay = get_delay_range('typing')
        print(f"  人性化延迟: {human_delay[0]}-{human_delay[1]} ms")
        print(f"  打字延迟: {typing_delay[0]}-{typing_delay[1]} ms")
        
    except Exception as e:
        print(f"❌ 配置适配器演示失败: {e}")

def demo_config_validation():
    """演示配置验证"""
    print("\n🔍 配置验证演示")
    print("=" * 50)
    
    try:
        from src.config.defaults import validate_config
        
        # 测试有效配置
        valid_config = {
            "accounts": {
                "daily_limit": 50,
                "concurrent_limit": 3
            },
            "timeouts": {
                "generation": 600000,
                "page_load": 30000
            }
        }
        
        print("✅ 验证有效配置:")
        errors = validate_config(valid_config)
        if not errors:
            print("  配置验证通过")
        else:
            print(f"  验证错误: {errors}")
            
        # 测试无效配置
        invalid_config = {
            "accounts": {
                "daily_limit": -1,  # 无效值
                "concurrent_limit": 0   # 无效值
            },
            "timeouts": {
                "generation": "invalid"  # 无效类型
            }
        }
        
        print("\n❌ 验证无效配置:")
        errors = validate_config(invalid_config)
        if errors:
            print("  发现配置错误:")
            for key, error in errors.items():
                print(f"    {key}: {error}")
        else:
            print("  配置验证通过（意外）")
            
    except Exception as e:
        print(f"❌ 配置验证演示失败: {e}")

def demo_config_export():
    """演示配置导出"""
    print("\n📤 配置导出演示")
    print("=" * 50)
    
    try:
        from src.config.manager import config_manager
        
        # 导出有效配置
        export_path = "config_export_demo.json"
        config_manager.export_effective_config(export_path)
        
        if Path(export_path).exists():
            print(f"✅ 配置已导出到: {export_path}")
            
            # 读取并显示部分内容
            with open(export_path, 'r', encoding='utf-8') as f:
                exported_config = json.load(f)
                
            print(f"📄 导出的配置包含 {len(exported_config)} 个顶级配置项:")
            for key in sorted(exported_config.keys())[:5]:  # 显示前5个
                print(f"  - {key}")
            if len(exported_config) > 5:
                print(f"  ... 等共 {len(exported_config)} 项")
                
            # 清理演示文件
            Path(export_path).unlink()
            print(f"🗑️ 已清理演示文件: {export_path}")
        else:
            print(f"❌ 配置导出失败")
            
    except Exception as e:
        print(f"❌ 配置导出演示失败: {e}")

def demo_usage_examples():
    """演示实际使用示例"""
    print("\n💡 实际使用示例")
    print("=" * 50)
    
    print("🔧 在代码中使用配置:")
    print("""
# 1. 基本使用
from src.config.manager import get_config

daily_limit = get_config('accounts.daily_limit')
timeout = get_config('timeouts.generation', 600000)

# 2. 使用配置适配器
from src.config.adapter import adapt_account_config, get_timeout_ms

# 处理null值配置
account_config = {"daily_limit": null, "email": "test@example.com"}
adapted = adapt_account_config(account_config)

# 获取超时值
page_timeout = get_timeout_ms('page_load', 30000)

# 3. 动态超时计算
def calculate_timeout(video_duration: float) -> int:
    base_timeout = get_timeout_ms('generation', 300000)
    video_timeout = int(video_duration * 60 * 1000)
    return max(base_timeout, video_timeout)
""")
    
    print("\n🌍 环境变量使用:")
    print("""
# Windows
set DANCE_DAILY_LIMIT=100
set DANCE_BATCH_SIZE=30
set DANCE_LOG_LEVEL=DEBUG

# Linux/macOS  
export DANCE_DAILY_LIMIT=100
export DANCE_BATCH_SIZE=30
export DANCE_LOG_LEVEL=DEBUG
""")

    print("\n📁 配置文件使用:")
    print("""
# config/local.json (本地开发配置)
{
  "accounts": {
    "daily_limit": 20,
    "concurrent_limit": 1
  },
  "timeouts": {
    "generation": 300000
  }
}

# 账号配置使用null值
{
  "accounts": [
    {
      "email": "test@example.com",
      "daily_limit": null,  // 使用默认值
      "concurrent_limit": 2  // 覆盖默认值
    }
  ]
}
""")

def main():
    """主演示函数"""
    print("🎛️ Dance项目配置系统演示")
    print("=" * 60)
    print("消除硬编码，提供灵活的配置管理")
    print("=" * 60)
    
    # 检查项目结构
    if not (project_root / "src" / "config").exists():
        print("❌ 项目配置目录不存在，请确保在正确的项目根目录运行")
        return
    
    try:
        # 运行各种演示
        demo_basic_usage()
        demo_env_override()
        demo_config_adapter()
        demo_config_validation()
        demo_config_export()
        demo_usage_examples()
        
        print("\n🎉 配置系统演示完成！")
        print("\n💡 主要优势:")
        print("  ✅ 消除硬编码值")
        print("  ✅ 支持环境变量覆盖")
        print("  ✅ null值自动使用默认值")
        print("  ✅ 配置验证和错误检查")
        print("  ✅ 动态配置热加载")
        print("  ✅ 多层次配置优先级")
        
        print(f"\n📖 详细说明请查看: {project_root}/config/README.md")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
