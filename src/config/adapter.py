"""
🔌 配置适配器
处理配置值的null值替换和类型转换
"""

from typing import Any, Dict, Optional, Union
from .defaults import get_config_value

def adapt_config_value(config: Dict[str, Any], key_path: str, default_path: str = None) -> Any:
    """
    适配配置值，如果是null则使用默认值
    
    Args:
        config: 配置字典
        key_path: 配置键路径，如 "accounts.daily_limit"
        default_path: 默认值路径，如果为None则使用key_path
        
    Returns:
        适配后的配置值
    """
    if default_path is None:
        default_path = key_path
        
    # 获取配置值
    keys = key_path.split('.')
    value = config
    
    try:
        for key in keys:
            value = value[key]
            
        # 如果值为null，使用默认值
        if value is None:
            return get_config_value(default_path)
        
        return value
        
    except (KeyError, TypeError):
        # 如果键不存在，使用默认值
        return get_config_value(default_path)

def adapt_account_config(account_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    适配账号配置，处理null值
    
    Args:
        account_config: 账号配置字典
        
    Returns:
        适配后的账号配置
    """
    adapted = account_config.copy()
    
    # 映射关系：配置键 -> 默认值路径
    mappings = {
        'daily_limit': 'accounts.daily_limit',
        'concurrent_limit': 'accounts.concurrent_limit',
        'rate_limit_min': 'accounts.rate_limit_min',
        'rate_limit_max': 'accounts.rate_limit_max',
        'max_retries': 'accounts.max_retries',
        'session_timeout': 'accounts.session_timeout',
    }
    
    for key, default_path in mappings.items():
        if key in adapted and adapted[key] is None:
            adapted[key] = get_config_value(default_path)
    
    return adapted

def adapt_processing_config(processing_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    适配处理配置，处理null值
    
    Args:
        processing_config: 处理配置字典
        
    Returns:
        适配后的处理配置
    """
    adapted = processing_config.copy()
    
    # 映射关系
    mappings = {
        'concurrent_per_account': 'accounts.concurrent_limit',
        'rate_limit_min': 'accounts.rate_limit_min',
        'rate_limit_max': 'accounts.rate_limit_max',
        'max_retries': 'accounts.max_retries',
        'generate_timeout_minutes': 'timeouts.generation',
        'batch_size': 'batch_processing.batch_size',
        'pause_between_batches': 'batch_processing.pause_between_batches',
    }
    
    for key, default_path in mappings.items():
        if key in adapted and adapted[key] is None:
            if key == 'generate_timeout_minutes':
                # 特殊处理：将毫秒转换为分钟
                default_ms = get_config_value(default_path)
                adapted[key] = default_ms // 60000 if default_ms else 10
            else:
                adapted[key] = get_config_value(default_path)
    
    return adapted

def adapt_browser_config(browser_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    适配浏览器配置，处理null值
    
    Args:
        browser_config: 浏览器配置字典
        
    Returns:
        适配后的浏览器配置
    """
    adapted = browser_config.copy()
    
    # 映射关系
    mappings = {
        'slow_mo': 'anti_detection.min_delay',
        'timeout': 'timeouts.page_load',
    }
    
    for key, default_path in mappings.items():
        if key in adapted and adapted[key] is None:
            adapted[key] = get_config_value(default_path)
    
    return adapted

def adapt_monitoring_config(monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    适配监控配置，处理null值
    
    Args:
        monitoring_config: 监控配置字典
        
    Returns:
        适配后的监控配置
    """
    adapted = monitoring_config.copy()
    
    # 映射关系
    mappings = {
        'log_level': 'monitoring.log_level',
        'progress_report_interval': 'monitoring.stats_interval',
    }
    
    for key, default_path in mappings.items():
        if key in adapted and adapted[key] is None:
            adapted[key] = get_config_value(default_path)
    
    return adapted

def adapt_batch_processing_config(batch_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    适配批处理配置，处理null值
    
    Args:
        batch_config: 批处理配置字典
        
    Returns:
        适配后的批处理配置
    """
    adapted = batch_config.copy()
    
    # 映射关系
    mappings = {
        'batch_size': 'batch_processing.batch_size',
        'pause_between_batches': 'batch_processing.pause_between_batches', 
        'max_daily_processing': 'batch_processing.max_daily_processing',
    }
    
    for key, default_path in mappings.items():
        if key in adapted and adapted[key] is None:
            adapted[key] = get_config_value(default_path)
    
    return adapted

def adapt_full_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    适配完整配置，处理所有section的null值
    
    Args:
        config: 完整配置字典
        
    Returns:
        适配后的配置字典
    """
    adapted = {}
    
    for section, section_config in config.items():
        if section.startswith('_'):
            # 跳过元数据字段
            adapted[section] = section_config
            continue
            
        if not isinstance(section_config, dict):
            adapted[section] = section_config
            continue
            
        # 根据section类型适配
        if section == 'accounts':
            if isinstance(section_config, list):
                adapted[section] = [adapt_account_config(acc) for acc in section_config]
            else:
                adapted[section] = adapt_account_config(section_config)
        elif section == 'processing':
            adapted[section] = adapt_processing_config(section_config)
        elif section == 'browser':
            adapted[section] = adapt_browser_config(section_config)
        elif section == 'monitoring':
            adapted[section] = adapt_monitoring_config(section_config)
        elif section == 'batch_processing':
            adapted[section] = adapt_batch_processing_config(section_config)
        else:
            # 其他section保持原样
            adapted[section] = section_config
    
    return adapted

def get_timeout_ms(timeout_key: str, default_ms: int = 30000) -> int:
    """
    获取超时值（毫秒）
    
    Args:
        timeout_key: 超时键，如 'page_load', 'generation'
        default_ms: 默认值（毫秒）
        
    Returns:
        超时值（毫秒）
    """
    return get_config_value(f'timeouts.{timeout_key}', default_ms)

def get_delay_range(delay_type: str = 'human') -> tuple:
    """
    获取延迟范围
    
    Args:
        delay_type: 延迟类型，如 'human', 'typing'
        
    Returns:
        (最小延迟, 最大延迟) 毫秒
    """
    if delay_type == 'human':
        min_delay = get_config_value('anti_detection.human_pause_min', 2000)
        max_delay = get_config_value('anti_detection.human_pause_max', 8000)
    elif delay_type == 'typing':
        min_delay = get_config_value('anti_detection.typing_delay_min', 50)
        max_delay = get_config_value('anti_detection.typing_delay_max', 200)
    else:
        min_delay = get_config_value('anti_detection.min_delay', 500)
        max_delay = get_config_value('anti_detection.max_delay', 2000)
    
    return (min_delay, max_delay)

if __name__ == "__main__":
    # 测试配置适配器
    print("🔌 配置适配器测试")
    print("=" * 50)
    
    # 测试账号配置适配
    test_account = {
        "email": "test@example.com",
        "password": "password",
        "daily_limit": None,
        "concurrent_limit": 5,
        "rate_limit_min": None
    }
    
    adapted_account = adapt_account_config(test_account)
    print(f"原始账号配置: {test_account}")
    print(f"适配后账号配置: {adapted_account}")
    
    # 测试超时获取
    timeout = get_timeout_ms('generation')
    print(f"生成超时: {timeout} ms")
    
    # 测试延迟范围
    human_delay = get_delay_range('human')
    print(f"人性化延迟范围: {human_delay} ms")
