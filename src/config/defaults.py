"""
🔧 Dance项目默认配置
消除硬编码，提供灵活的配置管理
"""

from typing import Dict, Any
import os

# 🎯 默认配置值
DEFAULT_CONFIG = {
    # 📊 账号限制
    "accounts": {
        "daily_limit": 50,  # 每日处理数量限制
        "concurrent_limit": 3,  # 并发处理限制
        "rate_limit_min": 60,  # 最小间隔(秒)
        "rate_limit_max": 120,  # 最大间隔(秒) 
        "max_retries": 3,  # 最大重试次数
        "session_timeout": 3600,  # 会话超时(秒)
    },
    
    # ⏱️ 超时设置
    "timeouts": {
        "page_load": 30000,  # 页面加载超时(毫秒)
        "element_wait": 10000,  # 元素等待超时(毫秒)
        "file_upload": 60000,  # 文件上传超时(毫秒)
        "generation": 600000,  # 生成超时(毫秒, 10分钟)
        "download": 300000,  # 下载超时(毫秒, 5分钟)
        "auth_flow": 300000,  # 认证流程超时(毫秒, 5分钟)
    },
    
    # 🔄 批处理设置
    "batch_processing": {
        "batch_size": 50,  # 批次大小
        "pause_between_batches": 1800,  # 批次间暂停(秒, 30分钟)
        "max_daily_processing": 200,  # 每日最大处理数
        "auto_restart_on_failure": True,  # 失败时自动重启
        "max_batch_retries": 3,  # 批次最大重试次数
    },
    
    # 🎭 反检测设置  
    "anti_detection": {
        "min_delay": 500,  # 最小延迟(毫秒)
        "max_delay": 2000,  # 最大延迟(毫秒)
        "typing_delay_min": 50,  # 打字最小延迟(毫秒)
        "typing_delay_max": 200,  # 打字最大延迟(毫秒)
        "human_pause_min": 2000,  # 人性化暂停最小值(毫秒)
        "human_pause_max": 8000,  # 人性化暂停最大值(毫秒)
        "avoid_peak_hours": [9, 10, 11, 14, 15, 16, 20, 21, 22],  # 避开高峰时段
        "session_rotation_hours": 6,  # 会话轮换间隔(小时)
    },
    
    # 🎥 视频处理设置
    "video_processing": {
        "min_duration": 5,  # 最短时长(秒)
        "max_size_mb": 100,  # 最大文件大小(MB)
        "allowed_formats": ["mp4", "avi", "mov", "mkv"],  # 允许的格式
        "auto_resize": True,  # 自动调整尺寸
        "preserve_audio": True,  # 保留音轨
    },
    
    # 🖼️ 图片处理设置
    "image_processing": {
        "allowed_formats": ["jpg", "jpeg", "png"],  # 允许的格式
        "min_resolution": [512, 512],  # 最小分辨率
        "max_size_mb": 50,  # 最大文件大小(MB)
        "auto_resize": True,  # 自动调整尺寸
    },
    
    # 🔧 GPU处理设置
    "gpu_processing": {
        "memory_limit_gb": 10,  # 显存限制(GB)
        "batch_size": 1,  # GPU批次大小
        "enable_optimization": True,  # 启用优化
        "precision": "fp16",  # 精度设置
        "device": "auto",  # 设备选择(auto/cuda/cpu)
    },
    
    # 📁 目录设置
    "directories": {
        "input_videos": "./input/videos",
        "input_people": "./input/people", 
        "input_backgrounds": "./input/backgrounds",
        "output": "./output",
        "temp": "./temp",
        "logs": "./logs",
        "profiles": "./profiles",
        "secrets": "./secrets",
        "cache": "./cache",
    },
    
    # 🔐 认证设置
    "oauth": {
        "redirect_port": 8080,  # OAuth重定向端口
        "state_timeout": 600,  # 状态超时(秒)
        "max_verification_attempts": 5,  # 最大验证尝试次数
        "verification_timeout": 60,  # 验证超时(秒)
        "server_mode": False,  # 服务器模式
    },
    
    # 📊 监控设置
    "monitoring": {
        "log_level": "INFO",  # 日志级别
        "log_rotation": "10 MB",  # 日志轮换大小
        "log_retention": "7 days",  # 日志保留时间
        "enable_statistics": True,  # 启用统计
        "stats_interval": 3600,  # 统计间隔(秒)
    },
    
    # 🌐 网络设置
    "network": {
        "request_timeout": 30,  # 请求超时(秒)
        "retry_attempts": 3,  # 重试次数
        "retry_delay": 1,  # 重试延迟(秒)
        "user_agent_rotation": True,  # 轮换User-Agent
        "proxy_enabled": False,  # 启用代理
    }
}

def get_config_value(path: str, default: Any = None) -> Any:
    """
    获取配置值，支持点符号路径
    
    Args:
        path: 配置路径，例如 "accounts.daily_limit"
        default: 默认值
        
    Returns:
        配置值或默认值
    """
    keys = path.split('.')
    value = DEFAULT_CONFIG
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default

def get_env_config(key: str, default: Any = None, type_cast=None) -> Any:
    """
    从环境变量获取配置，支持类型转换
    
    Args:
        key: 环境变量名
        default: 默认值
        type_cast: 类型转换函数
        
    Returns:
        配置值
    """
    value = os.getenv(key, default)
    if type_cast and value is not None:
        try:
            return type_cast(value)
        except (ValueError, TypeError):
            return default
    return value

def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并多个配置字典，后面的配置会覆盖前面的
    
    Args:
        *configs: 配置字典列表
        
    Returns:
        合并后的配置字典
    """
    result = {}
    
    for config in configs:
        if not isinstance(config, dict):
            continue
            
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_configs(result[key], value)
            else:
                result[key] = value
                
    return result

def validate_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    验证配置的合理性
    
    Args:
        config: 配置字典
        
    Returns:
        验证错误字典，空字典表示验证通过
    """
    errors = {}
    
    # 验证账号配置
    if 'accounts' in config:
        accounts_config = config['accounts']
        if isinstance(accounts_config, dict):
            if accounts_config.get('daily_limit', 0) <= 0:
                errors['accounts.daily_limit'] = "每日限制必须大于0"
            if accounts_config.get('concurrent_limit', 0) <= 0:
                errors['accounts.concurrent_limit'] = "并发限制必须大于0"
                
    # 验证超时配置
    if 'timeouts' in config:
        timeouts_config = config['timeouts']
        if isinstance(timeouts_config, dict):
            for timeout_key, timeout_value in timeouts_config.items():
                if not isinstance(timeout_value, (int, float)) or timeout_value <= 0:
                    errors[f'timeouts.{timeout_key}'] = f"超时值{timeout_key}必须为正数"
    
    # 验证批处理配置
    if 'batch_processing' in config:
        batch_config = config['batch_processing']
        if isinstance(batch_config, dict):
            if batch_config.get('batch_size', 0) <= 0:
                errors['batch_processing.batch_size'] = "批次大小必须大于0"
                
    return errors

# 🌍 环境变量覆盖映射
ENV_OVERRIDE_MAP = {
    "DANCE_DAILY_LIMIT": ("accounts.daily_limit", int),
    "DANCE_CONCURRENT_LIMIT": ("accounts.concurrent_limit", int),
    "DANCE_GENERATION_TIMEOUT": ("timeouts.generation", int),
    "DANCE_BATCH_SIZE": ("batch_processing.batch_size", int),
    "DANCE_GPU_MEMORY_LIMIT": ("gpu_processing.memory_limit_gb", int),
    "DANCE_LOG_LEVEL": ("monitoring.log_level", str),
    "DANCE_SERVER_MODE": ("oauth.server_mode", bool),
}

def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    应用环境变量覆盖
    
    Args:
        config: 基础配置
        
    Returns:
        应用环境变量后的配置
    """
    result = config.copy()
    
    for env_key, (config_path, type_cast) in ENV_OVERRIDE_MAP.items():
        env_value = get_env_config(env_key, type_cast=type_cast)
        if env_value is not None:
            # 设置嵌套配置值
            keys = config_path.split('.')
            current = result
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = env_value
            
    return result

def get_runtime_config() -> Dict[str, Any]:
    """
    获取运行时配置，包含默认值和环境变量覆盖
    
    Returns:
        完整的运行时配置
    """
    # 从默认配置开始
    config = DEFAULT_CONFIG.copy()
    
    # 应用环境变量覆盖
    config = apply_env_overrides(config)
    
    return config

if __name__ == "__main__":
    # 测试配置系统
    print("🔧 Dance项目配置系统测试")
    print("=" * 50)
    
    # 测试获取配置值
    print(f"默认每日限制: {get_config_value('accounts.daily_limit')}")
    print(f"默认生成超时: {get_config_value('timeouts.generation')} ms")
    print(f"默认批次大小: {get_config_value('batch_processing.batch_size')}")
    
    # 测试环境变量覆盖
    os.environ["DANCE_DAILY_LIMIT"] = "100"
    runtime_config = get_runtime_config()
    print(f"环境变量覆盖后每日限制: {runtime_config['accounts']['daily_limit']}")
    
    # 测试配置验证
    test_config = {"accounts": {"daily_limit": -1}}
    errors = validate_config(test_config)
    if errors:
        print(f"配置验证错误: {errors}")
    else:
        print("配置验证通过")
