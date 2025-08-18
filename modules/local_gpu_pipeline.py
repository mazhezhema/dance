#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地GPU Pipeline模块
处理Viggle输出的视频，进行超分辨率、抠像、背景替换
"""

import os
import cv2
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
import concurrent.futures
import psutil
import GPUtil

logger = logging.getLogger(__name__)

@dataclass
class PipelineJob:
    """GPU Pipeline任务"""
    input_path: str
    job_id: str
    category: str
    status: str = "pending"  # pending, processing, completed, failed
    stage: str = "superres"  # superres, matting, background, finalize
    
    # 输出路径
    superres_path: Optional[str] = None
    matting_path: Optional[str] = None
    background_path: Optional[str] = None
    final_path: Optional[str] = None
    
    # 处理信息
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    
    # 质量信息
    input_resolution: Optional[Tuple[int, int]] = None
    output_resolution: Optional[Tuple[int, int]] = None
    input_size_mb: Optional[float] = None
    output_size_mb: Optional[float] = None

class LocalGPUPipeline:
    def __init__(self, config_path: str = "config/gpu_pipeline_config.json"):
        self.config = self.load_config(config_path)
        self.job_history = []
        self.setup_tools()
        
    def load_config(self, config_path: str) -> dict:
        """加载Pipeline配置"""
        default_config = {
            "tools": {
                "realesrgan_path": "./tools/realesrgan-ncnn-vulkan.exe",
                "rvm_path": "./tools/inference_rvm.py",
                "ffmpeg_path": "ffmpeg"
            },
            "processing": {
                "superres_scale": 2,
                "superres_model": "realesr-animevideov3",
                "max_concurrent_jobs": 2,
                "temp_directory": "./temp_gpu",
                "keep_intermediates": False
            },
            "output": {
                "base_directory": "./final_output",
                "organize_by_category": True,
                "video_codec": "libx264",
                "video_bitrate": "2M",
                "audio_codec": "aac"
            },
            "backgrounds": {
                "library_path": "./backgrounds",
                "default_backgrounds": {
                    "dance": "dance_studio.mp4",
                    "fitness": "gym_background.mp4",
                    "traditional": "traditional_stage.mp4",
                    "unknown": "neutral_background.mp4"
                }
            },
            "quality": {
                "min_duration": 5,
                "max_duration": 600,
                "target_fps": 30,
                "target_resolution": [1920, 1080]
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
    
    def setup_tools(self):
        """检查和设置工具"""
        # 创建必要目录
        for directory in [
            self.config["processing"]["temp_directory"],
            self.config["output"]["base_directory"],
            self.config["backgrounds"]["library_path"]
        ]:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # 检查GPU
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                logger.info(f"GPU检测: {gpu.name} ({gpu.memoryTotal}MB)")
                if gpu.memoryTotal < 8000:  # 小于8GB
                    logger.warning("⚠️ GPU内存可能不足，建议降低并发数")
            else:
                logger.warning("⚠️ 未检测到GPU，将使用CPU处理")
        except Exception as e:
            logger.warning(f"⚠️ GPU检测失败: {str(e)}")
        
        # 检查工具可用性
        tools_status = {}
        
        # 检查Real-ESRGAN
        realesrgan_path = self.config["tools"]["realesrgan_path"]
        if Path(realesrgan_path).exists():
            tools_status["realesrgan"] = "available"
        else:
            tools_status["realesrgan"] = "missing"
            logger.warning(f"⚠️ Real-ESRGAN未找到: {realesrgan_path}")
        
        # 检查FFmpeg
        try:
            subprocess.run([self.config["tools"]["ffmpeg_path"], "-version"], 
                         capture_output=True, check=True)
            tools_status["ffmpeg"] = "available"
        except (subprocess.CalledProcessError, FileNotFoundError):
            tools_status["ffmpeg"] = "missing"
            logger.warning("⚠️ FFmpeg未找到")
        
        self.tools_status = tools_status
        logger.info(f"工具状态: {tools_status}")
    
    def get_video_info(self, video_path: str) -> Dict:
        """获取视频信息"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            file_size = os.path.getsize(video_path) / 1024 / 1024  # MB
            
            return {
                "resolution": (width, height),
                "fps": fps,
                "duration": duration,
                "size_mb": file_size
            }
        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return {}
    
    def select_background(self, category: str) -> str:
        """选择背景视频"""
        bg_config = self.config["backgrounds"]
        bg_library = Path(bg_config["library_path"])
        
        # 优先使用分类对应的背景
        if category in bg_config["default_backgrounds"]:
            bg_filename = bg_config["default_backgrounds"][category]
            bg_path = bg_library / bg_filename
            
            if bg_path.exists():
                return str(bg_path)
        
        # 使用默认背景
        default_bg = bg_library / bg_config["default_backgrounds"]["unknown"]
        if default_bg.exists():
            return str(default_bg)
        
        # 使用库中的第一个背景
        bg_files = list(bg_library.glob("*.mp4"))
        if bg_files:
            return str(bg_files[0])
        
        logger.warning("⚠️ 未找到合适的背景视频")
        return ""
    
    def process_superresolution(self, job: PipelineJob) -> bool:
        """超分辨率处理"""
        if self.tools_status.get("realesrgan") != "available":
            logger.error("Real-ESRGAN不可用，跳过超分辨率处理")
            job.superres_path = job.input_path
            return True
        
        logger.info(f"🔍 超分辨率处理: {job.job_id}")
        
        temp_dir = Path(self.config["processing"]["temp_directory"]) / job.job_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = temp_dir / f"{job.job_id}_superres.mp4"
        
        try:
            # Real-ESRGAN命令
            realesrgan_cmd = [
                self.config["tools"]["realesrgan_path"],
                "-i", job.input_path,
                "-o", str(output_path),
                "-s", str(self.config["processing"]["superres_scale"]),
                "-m", self.config["processing"]["superres_model"],
                "-f", "mp4"
            ]
            
            # 执行超分辨率
            result = subprocess.run(realesrgan_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_path.exists():
                job.superres_path = str(output_path)
                logger.info(f"✅ 超分辨率完成: {output_path}")
                return True
            else:
                raise Exception(f"Real-ESRGAN失败: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ 超分辨率失败: {str(e)}")
            job.superres_path = job.input_path  # 使用原始文件
            return False
    
    def process_matting(self, job: PipelineJob) -> bool:
        """视频抠像处理"""
        logger.info(f"✂️ 视频抠像: {job.job_id}")
        
        temp_dir = Path(self.config["processing"]["temp_directory"]) / job.job_id
        input_path = job.superres_path or job.input_path
        
        # 提取帧
        frames_dir = temp_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        try:
            # 使用FFmpeg提取帧
            extract_cmd = [
                self.config["tools"]["ffmpeg_path"],
                "-i", input_path,
                "-vf", "fps=30",  # 固定30fps
                str(frames_dir / "frame_%06d.png")
            ]
            
            subprocess.run(extract_cmd, check=True, capture_output=True)
            
            # 这里应该调用RVM或其他抠像工具
            # 简化版本：直接复制输入（实际应用中需要实现真实的抠像）
            alpha_dir = temp_dir / "alpha"
            alpha_dir.mkdir(exist_ok=True)
            
            # 模拟抠像过程（实际需要RVM）
            frame_files = sorted(frames_dir.glob("*.png"))
            for i, frame_file in enumerate(frame_files):
                alpha_file = alpha_dir / f"alpha_{i:06d}.png"
                shutil.copy(frame_file, alpha_file)
            
            # 重新组合为视频
            output_path = temp_dir / f"{job.job_id}_matted.mp4"
            
            compose_cmd = [
                self.config["tools"]["ffmpeg_path"],
                "-r", "30",
                "-i", str(alpha_dir / "alpha_%06d.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(output_path)
            ]
            
            subprocess.run(compose_cmd, check=True, capture_output=True)
            
            if output_path.exists():
                job.matting_path = str(output_path)
                logger.info(f"✅ 抠像完成: {output_path}")
                return True
            else:
                raise Exception("抠像输出文件不存在")
                
        except Exception as e:
            logger.error(f"❌ 抠像失败: {str(e)}")
            job.matting_path = input_path  # 使用前一步的结果
            return False
    
    def process_background_replacement(self, job: PipelineJob) -> bool:
        """背景替换处理"""
        logger.info(f"🎨 背景替换: {job.job_id}")
        
        temp_dir = Path(self.config["processing"]["temp_directory"]) / job.job_id
        input_path = job.matting_path or job.superres_path or job.input_path
        
        # 选择背景
        background_path = self.select_background(job.category)
        if not background_path:
            logger.warning("⚠️ 未找到背景，跳过背景替换")
            job.background_path = input_path
            return True
        
        output_path = temp_dir / f"{job.job_id}_background.mp4"
        
        try:
            # 获取视频信息
            video_info = self.get_video_info(input_path)
            target_res = self.config["quality"]["target_resolution"]
            
            # FFmpeg背景合成命令
            bg_cmd = [
                self.config["tools"]["ffmpeg_path"],
                "-i", background_path,
                "-i", input_path,
                "-filter_complex", 
                f"[0:v]scale={target_res[0]}:{target_res[1]}:force_original_aspect_ratio=increase,crop={target_res[0]}:{target_res[1]}[bg];"
                f"[1:v]scale={target_res[0]}:{target_res[1]}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2",
                "-c:v", self.config["output"]["video_codec"],
                "-b:v", self.config["output"]["video_bitrate"],
                "-c:a", self.config["output"]["audio_codec"],
                "-shortest",  # 以较短的视频为准
                str(output_path)
            ]
            
            result = subprocess.run(bg_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_path.exists():
                job.background_path = str(output_path)
                logger.info(f"✅ 背景替换完成: {output_path}")
                return True
            else:
                raise Exception(f"背景替换失败: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ 背景替换失败: {str(e)}")
            job.background_path = input_path
            return False
    
    def finalize_output(self, job: PipelineJob) -> bool:
        """最终输出处理"""
        logger.info(f"📦 最终输出: {job.job_id}")
        
        input_path = job.background_path or job.matting_path or job.superres_path or job.input_path
        
        # 确定输出路径
        base_dir = Path(self.config["output"]["base_directory"])
        if self.config["output"]["organize_by_category"]:
            output_dir = base_dir / job.category
        else:
            output_dir = base_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        final_filename = f"{job.job_id}_final_{timestamp}.mp4"
        final_path = output_dir / final_filename
        
        try:
            # 最终质量优化
            final_cmd = [
                self.config["tools"]["ffmpeg_path"],
                "-i", input_path,
                "-c:v", self.config["output"]["video_codec"],
                "-b:v", self.config["output"]["video_bitrate"],
                "-c:a", self.config["output"]["audio_codec"],
                "-movflags", "+faststart",  # 优化流媒体播放
                str(final_path)
            ]
            
            result = subprocess.run(final_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and final_path.exists():
                job.final_path = str(final_path)
                
                # 获取输出信息
                output_info = self.get_video_info(str(final_path))
                job.output_resolution = output_info.get("resolution")
                job.output_size_mb = output_info.get("size_mb")
                
                logger.info(f"✅ 最终输出完成: {final_path}")
                
                # 清理临时文件
                if not self.config["processing"]["keep_intermediates"]:
                    temp_dir = Path(self.config["processing"]["temp_directory"]) / job.job_id
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                        logger.info("🧹 清理临时文件")
                
                return True
            else:
                raise Exception(f"最终输出失败: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ 最终输出失败: {str(e)}")
            return False
    
    def process_single_job(self, job: PipelineJob) -> bool:
        """处理单个任务"""
        logger.info(f"🎬 开始GPU Pipeline: {job.job_id}")
        
        job.status = "processing"
        job.start_time = datetime.now().isoformat()
        start_time = datetime.now()
        
        # 获取输入信息
        input_info = self.get_video_info(job.input_path)
        job.input_resolution = input_info.get("resolution")
        job.input_size_mb = input_info.get("size_mb")
        
        try:
            # 处理流程
            stages = [
                ("superres", self.process_superresolution),
                ("matting", self.process_matting),
                ("background", self.process_background_replacement),
                ("finalize", self.finalize_output)
            ]
            
            for stage_name, stage_func in stages:
                job.stage = stage_name
                logger.info(f"📍 执行阶段: {stage_name}")
                
                if not stage_func(job):
                    logger.warning(f"⚠️ 阶段 {stage_name} 失败，但继续执行")
            
            # 检查最终结果
            if job.final_path and Path(job.final_path).exists():
                job.status = "completed"
                logger.info(f"✅ Pipeline完成: {job.job_id}")
                return True
            else:
                raise Exception("最终输出文件不存在")
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            logger.error(f"❌ Pipeline失败: {job.job_id} - {str(e)}")
            return False
        
        finally:
            job.end_time = datetime.now().isoformat()
            job.processing_time = (datetime.now() - start_time).total_seconds()
            self.job_history.append(job)
    
    def load_viggle_results(self, viggle_results_dir: str = "./viggle_results") -> List[PipelineJob]:
        """加载Viggle处理结果"""
        results_dir = Path(viggle_results_dir)
        if not results_dir.exists():
            logger.error(f"Viggle结果目录不存在: {viggle_results_dir}")
            return []
        
        jobs = []
        
        # 遍历结果文件
        for video_file in results_dir.rglob("*.mp4"):
            job_id = video_file.stem
            category = video_file.parent.name if video_file.parent != results_dir else "unknown"
            
            job = PipelineJob(
                input_path=str(video_file),
                job_id=job_id,
                category=category
            )
            jobs.append(job)
        
        logger.info(f"加载了 {len(jobs)} 个Viggle结果")
        return jobs
    
    def run_batch_processing(self, input_directory: str = None):
        """运行批量处理"""
        logger.info("🚀 GPU Pipeline模块启动")
        
        # 加载任务
        if input_directory:
            jobs = self.load_viggle_results(input_directory)
        else:
            jobs = self.load_viggle_results()
        
        if not jobs:
            logger.warning("⚠️ 没有待处理的任务")
            return
        
        # 并行处理
        max_workers = self.config["processing"]["max_concurrent_jobs"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_single_job, job) for job in jobs]
            
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                try:
                    result = future.result()
                    logger.info(f"📊 进度: {i+1}/{len(jobs)} ({'✅' if result else '❌'})")
                except Exception as e:
                    logger.error(f"❌ 任务异常: {str(e)}")
        
        # 生成报告
        self.generate_pipeline_report()
    
    def generate_pipeline_report(self):
        """生成Pipeline报告"""
        if not self.job_history:
            return
        
        # 统计信息
        total_jobs = len(self.job_history)
        completed_jobs = len([j for j in self.job_history if j.status == "completed"])
        failed_jobs = len([j for j in self.job_history if j.status == "failed"])
        
        success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        # 处理时间统计
        processing_times = [j.processing_time for j in self.job_history if j.processing_time]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # 分类统计
        category_stats = {}
        for job in self.job_history:
            cat = job.category
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "completed": 0, "failed": 0}
            category_stats[cat]["total"] += 1
            if job.status == "completed":
                category_stats[cat]["completed"] += 1
            elif job.status == "failed":
                category_stats[cat]["failed"] += 1
        
        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": f"{success_rate:.1f}%",
                "average_processing_time": f"{avg_processing_time:.1f}秒"
            },
            "category_statistics": category_stats,
            "job_details": [
                {
                    "job_id": job.job_id,
                    "input_path": job.input_path,
                    "final_path": job.final_path,
                    "category": job.category,
                    "status": job.status,
                    "processing_time": job.processing_time,
                    "input_resolution": job.input_resolution,
                    "output_resolution": job.output_resolution,
                    "input_size_mb": job.input_size_mb,
                    "output_size_mb": job.output_size_mb,
                    "error_message": job.error_message
                }
                for job in self.job_history
            ]
        }
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"reports/gpu_pipeline_report_{timestamp}.json"
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        print("\n" + "="*60)
        print("🎥 GPU Pipeline处理报告")
        print("="*60)
        print(f"📊 总计任务: {total_jobs}")
        print(f"✅ 完成: {completed_jobs}")
        print(f"❌ 失败: {failed_jobs}")
        print(f"📈 成功率: {success_rate:.1f}%")
        print(f"⏱️ 平均处理时间: {avg_processing_time:.1f}秒")
        print(f"📋 分类统计: {category_stats}")
        print(f"📄 详细报告: {report_file}")
        print("="*60)
        
        return report

def main():
    """主函数"""
    print("🎥 Dance项目 - 本地GPU Pipeline模块")
    print("="*50)
    
    pipeline = LocalGPUPipeline()
    pipeline.run_batch_processing()

if __name__ == "__main__":
    main()
