# 项目技术栈总结

## 🎯 **核心技术**

### **视频处理**
- **FFmpeg**: 核心视频处理引擎
  - 格式转换、音视频合成、滤镜效果
- **FFprobe**: 视频信息分析
  - 时长获取、元数据解析
- **OpenCV (cv2)**: 视频帧级处理
  - 视频信息提取、图像质量分析

### **图像处理**
- **Pillow (PIL)**: 基础图像处理
- **OpenCV**: 高级图像分析
  - 清晰度检测、边缘检测

### **浏览器自动化**
- **Playwright**: 现代浏览器自动化
- **Undetected ChromeDriver**: 反检测驱动

## 📚 **主要Python库**

### **核心库**
```python
# 视频处理
import cv2                    # OpenCV视频处理
import subprocess            # FFmpeg调用

# 图像处理  
from PIL import Image        # Pillow图像处理

# 浏览器自动化
from playwright.async_api import async_playwright
import undetected_chromedriver

# 数据处理
import json, numpy as np
from pathlib import Path
from typing import List, Dict, Optional

# 并发处理
import asyncio, concurrent.futures

# 系统监控
import psutil, GPUtil

# 数据库
import sqlite3

# 网络请求
import requests, aiohttp
```

## 🛠️ **外部工具**

### **必需工具**
1. **FFmpeg 4.0+**: 视频处理核心
2. **Chrome/Chromium**: 浏览器引擎

### **可选工具**
1. **Real-ESRGAN**: 超分辨率处理
2. **RVM**: 视频抠像处理

## 🏗️ **架构模块**

1. **视频预处理器**: 视频质量检测和分类
2. **背景生成器**: 图片转动态视频
3. **背景替换器**: 视频背景替换
4. **Pipeline处理器**: 完整处理流程
5. **Viggle自动化**: 浏览器自动化处理

## 💡 **技术特点**

- **双引擎处理**: FFmpeg + OpenCV
- **反检测技术**: Playwright + Undetected ChromeDriver  
- **模块化设计**: 独立功能模块
- **并发处理**: 多任务并行执行
- **数据库管理**: SQLite状态跟踪

这个技术栈结合了传统视频处理工具和现代自动化技术，实现了完整的视频处理流水线。
