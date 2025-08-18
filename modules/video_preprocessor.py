#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
片源预处理模块
检测视频是否适合Viggle处理，进行标准化和分类
"""

import os
import cv2
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VideoInfo:
    """视频信息结构"""
    file_path: str
    file_name: str
    file_size: int  # bytes
    duration: float  # seconds
    fps: float
    width: int
    height: int
    bitrate: int  # kbps
    codec: str
    format: str
    
    # Viggle兼容性检查结果
    viggle_compatible: bool
    compatibility_score: float  # 0-100
    issues: List[str]
    recommendations: List[str]
    
    # 分类信息
    category: str  # dance, fitness, traditional, etc.
    priority: int  # 1-10, 10为最高优先级
    
    # 元数据
    md5_hash: str
    processed_time: str
    estimated_credits: int  # 预估Viggle积分消耗

class VideoPreprocessor:
    def __init__(self, config_path: str = "config/preprocessor_config.json"):
        self.config = self.load_config(config_path)
        self.create_directories()
        
    def load_config(self, config_path: str) -> dict:
        """加载预处理配置"""
        default_config = {
            "viggle_requirements": {
                "min_duration": 5,      # 最短5秒
                "max_duration": 300,    # 最长5分钟
                "min_fps": 15,          # 最低15fps
                "max_fps": 60,          # 最高60fps
                "min_resolution": [480, 360],   # 最低分辨率
                "max_resolution": [1920, 1080], # 最高分辨率
                "max_file_size": 100 * 1024 * 1024,  # 100MB
                "supported_codecs": ["h264", "h265", "vp9"],
                "supported_formats": ["mp4", "avi", "mov", "mkv"]
            },
            "scoring_weights": {
                "duration": 0.2,
                "resolution": 0.25,
                "fps": 0.15,
                "quality": 0.25,
                "file_size": 0.15
            },
            "categories": {
                "keywords": {
                    "dance": ["舞蹈", "广场舞", "dance", "dancing"],
                    "fitness": ["健身", "瑜伽", "fitness", "yoga", "workout"],
                    "traditional": ["传统", "古典", "traditional", "classical"],
                    "children": ["儿童", "小孩", "children", "kids"],
                    "elderly": ["老年", "大爷", "大妈", "elderly", "senior"]
                }
            },
            "directories": {
                "input": "./input_videos",
                "processed": "./processed_videos",
                "reports": "./preprocessing_reports",
                "quarantine": "./quarantine_videos"
            }
        }
        
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                self.deep_update(default_config, user_config)
        else:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"创建默认配置文件: {config_path}")
            
        return default_config
    
    def deep_update(self, base_dict, update_dict):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self.deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def create_directories(self):
        """创建必要目录"""
        for dir_path in self.config["directories"].values():
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def calculate_md5(self, file_path: str) -> str:
        """计算文件MD5"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extract_video_info(self, file_path: str) -> Optional[Dict]:
        """提取视频基础信息"""
        try:
            cap = cv2.VideoCapture(file_path)
            
            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {file_path}")
                return None
            
            # 获取基础信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            duration = frame_count / fps if fps > 0 else 0
            
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            # 估算比特率
            bitrate = int((file_size * 8) / duration / 1000) if duration > 0 else 0
            
            cap.release()
            
            return {
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_size,
                'duration': duration,
                'fps': fps,
                'width': width,
                'height': height,
                'bitrate': bitrate,
                'codec': 'unknown',  # 需要ffprobe获取准确信息
                'format': file_name.split('.')[-1].lower()
            }
            
        except Exception as e:
            logger.error(f"提取视频信息失败 {file_path}: {str(e)}")
            return None
    
    def check_viggle_compatibility(self, video_info: Dict) -> Tuple[bool, float, List[str], List[str]]:
        """检查Viggle兼容性"""
        issues = []
        recommendations = []
        requirements = self.config["viggle_requirements"]
        weights = self.config["scoring_weights"]
        
        score_components = {}
        
        # 1. 检查时长
        duration = video_info['duration']
        if duration < requirements["min_duration"]:
            issues.append(f"视频时长过短: {duration:.1f}秒 < {requirements['min_duration']}秒")
            score_components['duration'] = 0
        elif duration > requirements["max_duration"]:
            issues.append(f"视频时长过长: {duration:.1f}秒 > {requirements['max_duration']}秒")
            recommendations.append("建议分段处理")
            score_components['duration'] = 0.3
        else:
            # 理想时长30秒-2分钟
            if 30 <= duration <= 120:
                score_components['duration'] = 100
            elif duration <= 30:
                score_components['duration'] = 80
            else:
                score_components['duration'] = 60
        
        # 2. 检查分辨率
        width, height = video_info['width'], video_info['height']
        min_w, min_h = requirements["min_resolution"]
        max_w, max_h = requirements["max_resolution"]
        
        if width < min_w or height < min_h:
            issues.append(f"分辨率过低: {width}x{height} < {min_w}x{min_h}")
            score_components['resolution'] = 0
        elif width > max_w or height > max_h:
            issues.append(f"分辨率过高: {width}x{height} > {max_w}x{max_h}")
            recommendations.append("建议降低分辨率")
            score_components['resolution'] = 40
        else:
            # 理想分辨率720p-1080p
            if (width >= 1280 and height >= 720) and (width <= 1920 and height <= 1080):
                score_components['resolution'] = 100
            elif width >= 640 and height >= 480:
                score_components['resolution'] = 70
            else:
                score_components['resolution'] = 50
        
        # 3. 检查帧率
        fps = video_info['fps']
        if fps < requirements["min_fps"]:
            issues.append(f"帧率过低: {fps:.1f}fps < {requirements['min_fps']}fps")
            score_components['fps'] = 0
        elif fps > requirements["max_fps"]:
            recommendations.append(f"帧率较高: {fps:.1f}fps，建议降至30fps节省积分")
            score_components['fps'] = 80
        else:
            # 理想帧率24-30fps
            if 24 <= fps <= 30:
                score_components['fps'] = 100
            else:
                score_components['fps'] = 70
        
        # 4. 检查文件大小
        file_size = video_info['file_size']
        if file_size > requirements["max_file_size"]:
            issues.append(f"文件过大: {file_size/1024/1024:.1f}MB > {requirements['max_file_size']/1024/1024:.1f}MB")
            recommendations.append("建议压缩文件")
            score_components['file_size'] = 20
        else:
            # 理想文件大小10-50MB
            size_mb = file_size / 1024 / 1024
            if 10 <= size_mb <= 50:
                score_components['file_size'] = 100
            elif size_mb < 10:
                score_components['file_size'] = 80
            else:
                score_components['file_size'] = 60
        
        # 5. 检查格式
        format_ext = video_info['format']
        if format_ext not in requirements["supported_formats"]:
            issues.append(f"格式不支持: {format_ext}")
            recommendations.append("建议转换为mp4格式")
            score_components['format'] = 0
        else:
            score_components['format'] = 100
        
        # 6. 质量评估（基于比特率）
        bitrate = video_info['bitrate']
        if bitrate < 500:  # 低于500kbps
            issues.append("视频质量可能过低")
            score_components['quality'] = 30
        elif bitrate > 10000:  # 高于10Mbps
            recommendations.append("比特率较高，可以适当降低")
            score_components['quality'] = 80
        else:
            score_components['quality'] = 90
        
        # 计算综合得分
        total_score = 0
        for component, score in score_components.items():
            weight = weights.get(component, 0.1)
            total_score += score * weight
        
        # 兼容性判断
        compatible = len(issues) == 0 and total_score >= 60
        
        return compatible, total_score, issues, recommendations
    
    def categorize_video(self, file_name: str) -> str:
        """根据文件名分类视频"""
        file_name_lower = file_name.lower()
        
        for category, keywords in self.config["categories"]["keywords"].items():
            for keyword in keywords:
                if keyword.lower() in file_name_lower:
                    return category
        
        return "unknown"
    
    def calculate_priority(self, video_info: Dict, compatibility_score: float, category: str) -> int:
        """计算处理优先级"""
        priority = 5  # 基础优先级
        
        # 根据兼容性得分调整
        if compatibility_score >= 90:
            priority += 3
        elif compatibility_score >= 70:
            priority += 2
        elif compatibility_score >= 50:
            priority += 1
        else:
            priority -= 2
        
        # 根据分类调整
        category_priorities = {
            "dance": 3,
            "fitness": 2,
            "traditional": 2,
            "children": 1,
            "elderly": 1,
            "unknown": -1
        }
        priority += category_priorities.get(category, 0)
        
        # 根据时长调整（中等时长优先）
        duration = video_info['duration']
        if 30 <= duration <= 120:
            priority += 2
        elif duration <= 30:
            priority += 1
        
        return max(1, min(10, priority))
    
    def estimate_credits(self, video_info: Dict) -> int:
        """预估Viggle积分消耗"""
        # 基础积分：根据时长
        duration = video_info['duration']
        base_credits = max(1, int(duration / 30))  # 每30秒约1个积分
        
        # 分辨率调整
        width, height = video_info['width'], video_info['height']
        if width >= 1280 and height >= 720:
            base_credits = int(base_credits * 1.5)  # 高分辨率消耗更多
        
        return base_credits
    
    def process_video(self, file_path: str) -> Optional[VideoInfo]:
        """处理单个视频"""
        logger.info(f"处理视频: {file_path}")
        
        # 提取基础信息
        video_data = self.extract_video_info(file_path)
        if not video_data:
            return None
        
        # 检查兼容性
        compatible, score, issues, recommendations = self.check_viggle_compatibility(video_data)
        
        # 分类
        category = self.categorize_video(video_data['file_name'])
        
        # 计算优先级
        priority = self.calculate_priority(video_data, score, category)
        
        # 预估积分
        credits = self.estimate_credits(video_data)
        
        # 计算MD5
        md5_hash = self.calculate_md5(file_path)
        
        # 创建VideoInfo对象
        video_info = VideoInfo(
            **video_data,
            viggle_compatible=compatible,
            compatibility_score=score,
            issues=issues,
            recommendations=recommendations,
            category=category,
            priority=priority,
            md5_hash=md5_hash,
            processed_time=datetime.now().isoformat(),
            estimated_credits=credits
        )
        
        return video_info
    
    def batch_process(self, input_dir: str = None) -> List[VideoInfo]:
        """批量处理视频"""
        if not input_dir:
            input_dir = self.config["directories"]["input"]
        
        input_path = Path(input_dir)
        if not input_path.exists():
            logger.error(f"输入目录不存在: {input_dir}")
            return []
        
        # 支持的视频格式
        video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(input_path.glob(ext))
            video_files.extend(input_path.glob(ext.upper()))
        
        logger.info(f"发现 {len(video_files)} 个视频文件")
        
        results = []
        for video_file in video_files:
            try:
                video_info = self.process_video(str(video_file))
                if video_info:
                    results.append(video_info)
                    logger.info(f"✅ {video_info.file_name}: 兼容性{video_info.compatibility_score:.1f}% 优先级{video_info.priority}")
                else:
                    logger.warning(f"⚠️ 处理失败: {video_file}")
            except Exception as e:
                logger.error(f"❌ 处理出错 {video_file}: {str(e)}")
        
        return results
    
    def generate_report(self, results: List[VideoInfo], output_file: str = None):
        """生成处理报告"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"{self.config['directories']['reports']}/preprocessing_report_{timestamp}.json"
        
        # 统计信息
        total_videos = len(results)
        compatible_videos = len([r for r in results if r.viggle_compatible])
        total_credits = sum(r.estimated_credits for r in results)
        
        categories = {}
        priorities = {}
        for result in results:
            categories[result.category] = categories.get(result.category, 0) + 1
            priorities[result.priority] = priorities.get(result.priority, 0) + 1
        
        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_videos": total_videos,
                "compatible_videos": compatible_videos,
                "compatibility_rate": f"{compatible_videos/total_videos*100:.1f}%" if total_videos > 0 else "0%",
                "total_estimated_credits": total_credits,
                "average_credits_per_video": f"{total_credits/total_videos:.1f}" if total_videos > 0 else "0"
            },
            "statistics": {
                "categories": categories,
                "priorities": priorities
            },
            "videos": [asdict(result) for result in results]
        }
        
        # 保存报告
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 报告已生成: {output_file}")
        
        # 打印摘要
        print("\n" + "="*60)
        print("📊 视频预处理报告")
        print("="*60)
        print(f"📁 总计视频: {total_videos}")
        print(f"✅ Viggle兼容: {compatible_videos} ({compatible_videos/total_videos*100:.1f}%)")
        print(f"💰 预估积分: {total_credits}")
        print(f"📋 分类统计: {categories}")
        print(f"⭐ 优先级分布: {priorities}")
        print("="*60)
        
        return report
    
    def create_processing_queue(self, results: List[VideoInfo], min_priority: int = 5) -> List[str]:
        """创建处理队列（按优先级排序）"""
        # 筛选兼容视频
        compatible_videos = [r for r in results if r.viggle_compatible and r.priority >= min_priority]
        
        # 按优先级排序
        compatible_videos.sort(key=lambda x: (-x.priority, -x.compatibility_score))
        
        # 生成队列文件路径列表
        queue = [video.file_path for video in compatible_videos]
        
        # 保存队列
        queue_file = f"{self.config['directories']['processed']}/processing_queue.json"
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump({
                "created": datetime.now().isoformat(),
                "total_videos": len(queue),
                "queue": queue
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"🎯 处理队列已创建: {len(queue)} 个视频")
        return queue

def main():
    """主函数"""
    print("🎬 Dance项目 - 片源预处理模块")
    print("="*50)
    
    preprocessor = VideoPreprocessor()
    
    # 批量处理
    results = preprocessor.batch_process()
    
    if results:
        # 生成报告
        report = preprocessor.generate_report(results)
        
        # 创建处理队列
        queue = preprocessor.create_processing_queue(results, min_priority=5)
        
        print(f"\n🎉 预处理完成！共处理 {len(results)} 个视频")
        print(f"📋 已创建包含 {len(queue)} 个视频的处理队列")
    else:
        print("❌ 未找到可处理的视频文件")

if __name__ == "__main__":
    main()
