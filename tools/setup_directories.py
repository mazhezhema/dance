#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle自动化目录结构初始化脚本
"""

import os
from pathlib import Path

def create_directory_structure():
    """创建完整的目录结构"""
    
    # 主要目录
    directories = [
        "source_videos",      # 原始视频
        "target_people",      # 目标人物图片  
        "output",            # 输出结果
        "cookies",           # Cookie存储
        "logs",              # 日志文件
        "temp",              # 临时文件
    ]
    
    # 人物分类子目录
    people_categories = [
        "target_people/dancers",
        "target_people/fitness",
        "target_people/traditional",
        "target_people/yoga",
        "target_people/children",
        "target_people/elderly"
    ]
    
    # 创建目录
    all_dirs = directories + people_categories
    
    for dir_path in all_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {dir_path}/")
    
    # 创建示例文件
    create_example_files()
    
    print("\n🎉 目录结构创建完成！")
    print_usage_guide()

def create_example_files():
    """创建示例文件和说明"""
    
    # README文件
    readme_content = """# Viggle自动化处理器

## 目录说明

### source_videos/
存放原始视频文件，支持格式：mp4, avi, mov, mkv, wmv

### target_people/
存放目标人物图片，建议按类别分类：
- dancers/ - 舞蹈演员
- fitness/ - 健身教练  
- traditional/ - 传统服装
- yoga/ - 瑜伽教练
- children/ - 儿童形象
- elderly/ - 老年人形象

### output/
自动生成的处理结果

### cookies/
浏览器会话Cookie存储

### logs/
处理日志记录

### temp/
临时文件存储

## 使用流程

1. 将视频文件放入 source_videos/
2. 将目标人物图片放入 target_people/ 对应分类
3. 修改 config.json 配置文件
4. 运行 python viggle_auto_processor.py

## 注意事项

- 视频文件建议不超过30MB
- 人物图片建议清晰正面照，分辨率512x512以上
- 确保网络连接稳定
- 避开网站高峰时段运行
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # .gitignore文件
    gitignore_content = """# Viggle自动化忽略文件

# 配置文件（包含敏感信息）
config.json

# Cookie文件
cookies/*.pkl
cookies/*.json

# 日志文件
logs/*.log
*.log

# 视频文件（太大）
source_videos/*.mp4
source_videos/*.avi
source_videos/*.mov
source_videos/*.mkv
source_videos/*.wmv

# 输出文件
output/*.mp4
output/*.avi

# 临时文件
temp/*

# 系统文件
.DS_Store
Thumbs.db

# Python缓存
__pycache__/
*.pyc
*.pyo
*.egg-info/

# 浏览器缓存
.cache/
"""
    
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    
    # 创建目录说明文件
    dir_explanations = {
        "source_videos/README.txt": "将原始视频文件放在这里\n支持格式：mp4, avi, mov, mkv, wmv",
        "target_people/README.txt": "将目标人物图片放在这里\n建议按类别分类到子文件夹",
        "output/README.txt": "处理完成的视频文件会保存在这里",
        "cookies/README.txt": "浏览器Cookie会自动保存在这里\n请勿手动修改",
        "logs/README.txt": "处理日志会保存在这里",
        "temp/README.txt": "临时文件存储，程序会自动清理"
    }
    
    for file_path, content in dir_explanations.items():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

def print_usage_guide():
    """打印使用指南"""
    print("\n" + "="*50)
    print("📖 使用指南")
    print("="*50)
    
    print("\n1️⃣ 安装依赖：")
    print("   pip install undetected-chromedriver selenium")
    
    print("\n2️⃣ 配置设置：")
    print("   cp config_example.json config.json")
    print("   编辑 config.json 文件，填入你的Viggle账号")
    
    print("\n3️⃣ 准备素材：")
    print("   - 将视频文件放入 source_videos/")
    print("   - 将人物图片放入 target_people/对应分类/")
    
    print("\n4️⃣ 运行处理：")
    print("   python viggle_auto_processor.py")
    
    print("\n⚠️  重要提醒：")
    print("   - 首次运行会创建config.json，请修改其中的账号密码")
    print("   - 建议晚上或凌晨运行，避开网站高峰期")
    print("   - 确保有稳定的网络连接")
    print("   - 处理过程中请勿关闭电脑")
    
    print("\n🔧 故障排除：")
    print("   - 如果登录失败，检查账号密码是否正确")
    print("   - 如果上传失败，检查文件格式和大小")
    print("   - 如果频繁出错，降低batch_size设置")
    print("   - 查看logs/目录下的日志文件排查问题")

if __name__ == "__main__":
    print("🎭 Viggle自动化处理器 - 目录初始化")
    print("="*50)
    create_directory_structure()
