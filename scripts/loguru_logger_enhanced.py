#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于engineering-memory最佳实践的Loguru增强日志系统
结合反检测技术和结构化日志设计
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

try:
    from loguru import logger
except ImportError:
    print("❌ 未安装loguru，请运行: pip install loguru")
    sys.exit(1)

class LoguruEnhancedLogger:
    """
    基于engineering-memory的Loguru增强日志器
    特性：
    1. 反检测安全日志
    2. 结构化事件记录
    3. 性能监控集成
    4. 跨平台文件管理
    5. 智能日志轮转
    """
    
    def __init__(self, app_name: str = "viggle_app", log_dir: str = "logs"):
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 敏感词过滤（反检测）
        self.sensitive_words = [
            'automation', 'bot', 'script', 'selenium', 'playwright',
            'crawl', 'spider', 'robot', 'headless', 'webdriver'
        ]
        
        self.setup_loguru()
        
    def setup_loguru(self):
        """配置Loguru日志器"""
        # 移除默认处理器
        logger.remove()
        
        # 1. 控制台处理器（彩色、简洁）
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level="INFO",
            colorize=True,
            filter=self._anti_detection_filter
        )
        
        # 2. 详细文件日志（按日期轮转）
        logger.add(
            self.log_dir / f"{self.app_name}_{{time:YYYY-MM-DD}}.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="00:00",  # 每天轮转
            retention="30 days",  # 保留30天
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
            filter=self._anti_detection_filter
        )
        
        # 3. 错误专用日志
        logger.add(
            self.log_dir / f"{self.app_name}_errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="10 MB",  # 按大小轮转
            retention="90 days",  # 错误日志保留更久
            encoding="utf-8"
        )
        
        # 4. 结构化JSON日志（用于分析）
        logger.add(
            self.log_dir / f"{self.app_name}_structured.jsonl",
            format="{message}",
            level="INFO",
            filter=lambda record: record["extra"].get("structured", False),
            rotation="100 MB",
            retention="60 days",
            encoding="utf-8"
        )
        
        # 5. 性能监控日志
        logger.add(
            self.log_dir / f"{self.app_name}_performance.log", 
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
            level="INFO",
            filter=lambda record: record["extra"].get("performance", False),
            rotation="50 MB",
            retention="30 days",
            encoding="utf-8"
        )
        
        logger.info("🎭 Loguru增强日志系统已启动")
    
    def _anti_detection_filter(self, record):
        """反检测过滤器"""
        message = record["message"]
        
        # 替换敏感词汇
        for word in self.sensitive_words:
            if word in message.lower():
                record["message"] = message.replace(word, "process")
        
        return True
    
    def log_event(self, event: str, **kwargs):
        """结构化事件日志"""
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "app": self.app_name,
            **kwargs
        }
        
        # 控制台友好格式
        logger.bind(structured=False).info(f"Event: {event}")
        
        # JSON结构化格式
        logger.bind(structured=True).info(json.dumps(event_data, ensure_ascii=False))
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, task_id: str = None):
        """增强错误日志"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "task_id": task_id,
            "traceback": traceback.format_exc(),
            "app": self.app_name
        }
        
        # 控制台错误（简洁）
        logger.error(f"❌ {error_data['error_type']}: {error_data['error_message']}")
        
        # 详细JSON错误
        logger.bind(structured=True).error(json.dumps(error_data, ensure_ascii=False))
    
    def log_performance(self, operation: str, duration: float, **metrics):
        """性能监控日志"""
        perf_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration_seconds": round(duration, 3),
            "app": self.app_name,
            **metrics
        }
        
        logger.bind(performance=True).info(json.dumps(perf_data, ensure_ascii=False))
    
    def log_task_start(self, task_id: str, task_type: str, **details):
        """任务开始日志"""
        self.log_event("task_start", 
                      task_id=task_id, 
                      task_type=task_type, 
                      **details)
    
    def log_task_complete(self, task_id: str, duration: float, **results):
        """任务完成日志"""
        self.log_event("task_complete", 
                      task_id=task_id, 
                      duration=duration, 
                      **results)
        
        # 同时记录性能
        self.log_performance("task_completion", duration, task_id=task_id)
    
    def log_task_failed(self, task_id: str, error: Exception, **context):
        """任务失败日志"""
        self.log_error(error, context=context, task_id=task_id)
        self.log_event("task_failed", task_id=task_id, error_type=type(error).__name__)
    
    def log_system_info(self, **info):
        """系统信息日志"""
        self.log_event("system_info", **info)
    
    def log_anti_detection(self, action: str, **details):
        """反检测行为日志（安全记录）"""
        # 使用隐蔽的描述
        safe_action = action.replace("anti_detection", "user_behavior")
        self.log_event("user_simulation", action=safe_action, **details)
    
    @staticmethod
    def timer():
        """性能计时装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # 假设第一个参数是self且有logger
                    if args and hasattr(args[0], 'logger'):
                        args[0].logger.log_performance(
                            operation=func.__name__,
                            duration=duration,
                            success=True
                        )
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    
                    if args and hasattr(args[0], 'logger'):
                        args[0].logger.log_performance(
                            operation=func.__name__,
                            duration=duration,
                            success=False,
                            error=str(e)
                        )
                    raise
            return wrapper
        return decorator

# 全局日志器实例
enhanced_logger = LoguruEnhancedLogger("viggle_enhanced")

# 便捷函数
def log_event(event: str, **kwargs):
    """全局事件日志"""
    enhanced_logger.log_event(event, **kwargs)

def log_error(error: Exception, context: Dict[str, Any] = None, task_id: str = None):
    """全局错误日志"""
    enhanced_logger.log_error(error, context, task_id)

def log_performance(operation: str, duration: float, **metrics):
    """全局性能日志"""
    enhanced_logger.log_performance(operation, duration, **metrics)

# 导出主要接口
__all__ = [
    'LoguruEnhancedLogger',
    'enhanced_logger', 
    'log_event',
    'log_error', 
    'log_performance',
    'logger'  # 原始loguru logger
]

if __name__ == "__main__":
    """测试日志系统"""
    print("🧪 测试Loguru增强日志系统...")
    
    # 测试基础日志
    logger.info("这是一个测试信息")
    logger.warning("这是一个警告")
    logger.error("这是一个错误")
    
    # 测试结构化日志
    log_event("test_event", user_id=123, action="login")
    
    # 测试错误日志
    try:
        raise ValueError("测试错误")
    except Exception as e:
        log_error(e, context={"test": True}, task_id="test_001")
    
    # 测试性能日志
    log_performance("test_operation", 1.234, records_processed=100)
    
    # 测试反检测日志
    enhanced_logger.log_anti_detection("user_click", element="button", delay=1.5)
    
    print("✅ 日志测试完成，请检查logs/目录中的日志文件")

