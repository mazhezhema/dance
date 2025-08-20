# -*- coding: utf-8 -*-
"""
Dance项目核心包
AI视频处理自动化系统
"""

__version__ = "1.0.0"
__author__ = "Dance Team"
__description__ = "AI视频处理自动化系统"

# 导入核心模块
from .core import task_database
from .automation import viggle_automation
from .processing import background_generator, background_replacement, rtx3060_pipeline

__all__ = [
    'task_database',
    'viggle_automation', 
    'background_generator',
    'background_replacement',
    'rtx3060_pipeline'
]
