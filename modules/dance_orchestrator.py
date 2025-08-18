#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dance项目编排器
协调各个模块的执行，管理整体数据流
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

# 导入各模块
from modules.video_preprocessor import VideoPreprocessor
from modules.viggle_automation import ViggleAutomationModule  
from modules.local_gpu_pipeline import LocalGPUPipeline

logger = logging.getLogger(__name__)

@dataclass
class DanceProject:
    """Dance项目信息"""
    project_id: str
    project_name: str
    input_videos_count: int
    target_output_count: int
    estimated_credits: int
    estimated_time_hours: float
    
    # 执行状态
    status: str = "created"  # created, preprocessing, viggle_processing, gpu_processing, completed, failed
    current_stage: str = "none"
    
    # 结果统计
    preprocessed_videos: int = 0
    viggle_completed: int = 0
    gpu_completed: int = 0
    final_outputs: int = 0
    
    # 时间记录
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    stage_times: Dict[str, float] = None
    
    def __post_init__(self):
        if self.stage_times is None:
            self.stage_times = {}

class DanceOrchestrator:
    def __init__(self, config_path: str = "config/orchestrator_config.json"):
        self.config = self.load_config(config_path)
        self.project_history = []
        
        # 初始化各模块
        self.preprocessor = VideoPreprocessor()
        self.viggle_automation = ViggleAutomationModule()
        self.gpu_pipeline = LocalGPUPipeline()
        
        # 设置日志
        self.setup_logging()
        
    def load_config(self, config_path: str) -> dict:
        """加载编排器配置"""
        default_config = {
            "project_settings": {
                "auto_progression": True,
                "pause_between_stages": False,
                "stage_timeout_hours": 24,
                "cleanup_intermediates": True
            },
            "notifications": {
                "enable_stage_notifications": True,
                "enable_completion_notifications": True,
                "webhook_url": ""
            },
            "quality_control": {
                "enable_quality_checks": True,
                "min_success_rate": 0.8,
                "auto_retry_failed": True,
                "max_retries": 2
            },
            "directories": {
                "projects": "./projects",
                "archives": "./archives",
                "reports": "./reports"
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
    
    def setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 创建专门的orchestrator日志
        log_file = log_dir / "dance_orchestrator.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def create_project(self, project_name: str, input_directory: str) -> DanceProject:
        """创建新项目"""
        project_id = f"dance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 统计输入视频
        input_path = Path(input_directory)
        video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(input_path.glob(ext))
            video_files.extend(input_path.glob(ext.upper()))
        
        input_count = len(video_files)
        
        # 估算项目规模
        estimated_credits = input_count * 2  # 平均每个视频2积分
        estimated_time = input_count * 0.2   # 平均每个视频12分钟
        
        project = DanceProject(
            project_id=project_id,
            project_name=project_name,
            input_videos_count=input_count,
            target_output_count=input_count,
            estimated_credits=estimated_credits,
            estimated_time_hours=estimated_time
        )
        
        logger.info(f"🎬 创建项目: {project_name} ({input_count}个视频)")
        return project
    
    async def execute_preprocessing_stage(self, project: DanceProject, input_directory: str) -> bool:
        """执行预处理阶段"""
        logger.info(f"📋 开始预处理阶段: {project.project_id}")
        project.current_stage = "preprocessing"
        stage_start = time.time()
        
        try:
            # 配置预处理器输入目录
            self.preprocessor.config["directories"]["input"] = input_directory
            
            # 执行预处理
            results = self.preprocessor.batch_process(input_directory)
            
            if results:
                # 生成报告
                report = self.preprocessor.generate_report(results)
                
                # 创建处理队列
                queue = self.preprocessor.create_processing_queue(results, min_priority=5)
                
                project.preprocessed_videos = len(results)
                project.stage_times["preprocessing"] = time.time() - stage_start
                
                logger.info(f"✅ 预处理完成: {len(results)}个视频，{len(queue)}个进入队列")
                return True
            else:
                raise Exception("预处理未产生结果")
                
        except Exception as e:
            logger.error(f"❌ 预处理失败: {str(e)}")
            project.status = "failed"
            return False
    
    async def execute_viggle_stage(self, project: DanceProject) -> bool:
        """执行Viggle处理阶段"""
        logger.info(f"🎭 开始Viggle处理阶段: {project.project_id}")
        project.current_stage = "viggle_processing"
        stage_start = time.time()
        
        try:
            # 执行Viggle自动化
            await self.viggle_automation.run_batch_processing()
            
            # 统计完成数量
            completed_count = len([j for j in self.viggle_automation.job_history if j.status == "completed"])
            
            project.viggle_completed = completed_count
            project.stage_times["viggle_processing"] = time.time() - stage_start
            
            logger.info(f"✅ Viggle处理完成: {completed_count}个视频")
            
            # 质量检查
            if self.config["quality_control"]["enable_quality_checks"]:
                success_rate = completed_count / project.preprocessed_videos if project.preprocessed_videos > 0 else 0
                min_rate = self.config["quality_control"]["min_success_rate"]
                
                if success_rate < min_rate:
                    logger.warning(f"⚠️ Viggle成功率 {success_rate:.1%} 低于要求 {min_rate:.1%}")
                    
                    if self.config["quality_control"]["auto_retry_failed"]:
                        logger.info("🔄 自动重试失败的任务")
                        # 这里可以实现重试逻辑
            
            return completed_count > 0
            
        except Exception as e:
            logger.error(f"❌ Viggle处理失败: {str(e)}")
            return False
    
    async def execute_gpu_pipeline_stage(self, project: DanceProject) -> bool:
        """执行GPU Pipeline阶段"""
        logger.info(f"🎥 开始GPU Pipeline阶段: {project.project_id}")
        project.current_stage = "gpu_processing"
        stage_start = time.time()
        
        try:
            # 执行GPU Pipeline
            self.gpu_pipeline.run_batch_processing()
            
            # 统计完成数量
            completed_count = len([j for j in self.gpu_pipeline.job_history if j.status == "completed"])
            
            project.gpu_completed = completed_count
            project.final_outputs = completed_count
            project.stage_times["gpu_processing"] = time.time() - stage_start
            
            logger.info(f"✅ GPU Pipeline完成: {completed_count}个视频")
            
            return completed_count > 0
            
        except Exception as e:
            logger.error(f"❌ GPU Pipeline失败: {str(e)}")
            return False
    
    def send_notification(self, message: str, notification_type: str = "info"):
        """发送通知"""
        if not self.config["notifications"]["enable_stage_notifications"]:
            return
        
        webhook_url = self.config["notifications"]["webhook_url"]
        if webhook_url:
            # 这里可以实现webhook通知
            logger.info(f"📢 通知: {message}")
        else:
            logger.info(f"📢 {message}")
    
    def archive_project(self, project: DanceProject):
        """归档项目"""
        archive_dir = Path(self.config["directories"]["archives"])
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        project_archive = archive_dir / f"{project.project_id}.json"
        
        # 保存项目信息
        project_data = {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "status": project.status,
            "input_videos_count": project.input_videos_count,
            "final_outputs": project.final_outputs,
            "stage_times": project.stage_times,
            "start_time": project.start_time,
            "end_time": project.end_time,
            "archived_time": datetime.now().isoformat()
        }
        
        with open(project_archive, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📦 项目已归档: {project_archive}")
    
    async def run_full_pipeline(self, project_name: str, input_directory: str) -> DanceProject:
        """运行完整pipeline"""
        logger.info(f"🚀 启动Dance完整Pipeline: {project_name}")
        
        # 创建项目
        project = self.create_project(project_name, input_directory)
        project.status = "preprocessing"
        project.start_time = datetime.now().isoformat()
        
        try:
            # 阶段1: 预处理
            self.send_notification(f"开始预处理阶段 - 项目: {project_name}")
            success = await self.execute_preprocessing_stage(project, input_directory)
            
            if not success:
                raise Exception("预处理阶段失败")
            
            # 阶段间暂停
            if self.config["project_settings"]["pause_between_stages"]:
                logger.info("⏸️ 阶段间暂停，按Enter继续...")
                input()
            
            # 阶段2: Viggle处理
            self.send_notification(f"开始Viggle处理阶段 - 项目: {project_name}")
            project.status = "viggle_processing"
            success = await self.execute_viggle_stage(project)
            
            if not success:
                raise Exception("Viggle处理阶段失败")
            
            # 阶段间暂停
            if self.config["project_settings"]["pause_between_stages"]:
                logger.info("⏸️ 阶段间暂停，按Enter继续...")
                input()
            
            # 阶段3: GPU Pipeline
            self.send_notification(f"开始GPU Pipeline阶段 - 项目: {project_name}")
            project.status = "gpu_processing"
            success = await self.execute_gpu_pipeline_stage(project)
            
            if not success:
                raise Exception("GPU Pipeline阶段失败")
            
            # 项目完成
            project.status = "completed"
            project.end_time = datetime.now().isoformat()
            
            # 生成最终报告
            final_report = self.generate_final_report(project)
            
            # 发送完成通知
            if self.config["notifications"]["enable_completion_notifications"]:
                self.send_notification(f"项目完成 - {project_name}: {project.final_outputs}/{project.input_videos_count} 视频成功处理")
            
            # 归档项目
            self.archive_project(project)
            
            logger.info(f"🎉 项目完成: {project_name}")
            return project
            
        except Exception as e:
            project.status = "failed"
            project.end_time = datetime.now().isoformat()
            
            logger.error(f"💥 项目失败: {project_name} - {str(e)}")
            
            # 归档失败的项目
            self.archive_project(project)
            
            return project
        
        finally:
            self.project_history.append(project)
    
    def generate_final_report(self, project: DanceProject) -> Dict:
        """生成最终项目报告"""
        total_time = 0
        if project.start_time and project.end_time:
            start = datetime.fromisoformat(project.start_time)
            end = datetime.fromisoformat(project.end_time)
            total_time = (end - start).total_seconds() / 3600  # 小时
        
        success_rate = (project.final_outputs / project.input_videos_count * 100) if project.input_videos_count > 0 else 0
        
        report = {
            "project_info": {
                "project_id": project.project_id,
                "project_name": project.project_name,
                "status": project.status,
                "start_time": project.start_time,
                "end_time": project.end_time,
                "total_time_hours": total_time
            },
            "pipeline_summary": {
                "input_videos": project.input_videos_count,
                "preprocessed": project.preprocessed_videos,
                "viggle_completed": project.viggle_completed,
                "gpu_completed": project.gpu_completed,
                "final_outputs": project.final_outputs,
                "success_rate": f"{success_rate:.1f}%"
            },
            "stage_performance": project.stage_times,
            "estimates_vs_actual": {
                "estimated_credits": project.estimated_credits,
                "estimated_time_hours": project.estimated_time_hours,
                "actual_time_hours": total_time
            }
        }
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"{self.config['directories']['reports']}/final_report_{project.project_id}_{timestamp}.json"
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        print("\n" + "="*70)
        print(f"🎊 项目最终报告: {project.project_name}")
        print("="*70)
        print(f"📊 输入视频: {project.input_videos_count}")
        print(f"✅ 最终输出: {project.final_outputs}")
        print(f"📈 成功率: {success_rate:.1f}%")
        print(f"⏱️ 总耗时: {total_time:.1f}小时")
        print(f"📋 阶段耗时: {project.stage_times}")
        print(f"📄 详细报告: {report_file}")
        print("="*70)
        
        return report
    
    def get_project_status(self, project_id: str) -> Optional[Dict]:
        """获取项目状态"""
        project = next((p for p in self.project_history if p.project_id == project_id), None)
        if project:
            return {
                "project_id": project.project_id,
                "status": project.status,
                "current_stage": project.current_stage,
                "progress": {
                    "preprocessed": project.preprocessed_videos,
                    "viggle_completed": project.viggle_completed,
                    "gpu_completed": project.gpu_completed,
                    "final_outputs": project.final_outputs
                }
            }
        return None
    
    def list_projects(self) -> List[Dict]:
        """列出所有项目"""
        return [
            {
                "project_id": p.project_id,
                "project_name": p.project_name,
                "status": p.status,
                "input_count": p.input_videos_count,
                "output_count": p.final_outputs,
                "start_time": p.start_time
            }
            for p in self.project_history
        ]

async def main():
    """主函数"""
    print("🎬 Dance项目 - 编排器")
    print("="*50)
    
    orchestrator = DanceOrchestrator()
    
    # 示例：运行完整pipeline
    project_name = input("请输入项目名称: ").strip() or "dance_project_test"
    input_dir = input("请输入视频目录路径: ").strip() or "./input_videos"
    
    if not Path(input_dir).exists():
        print(f"❌ 目录不存在: {input_dir}")
        return
    
    project = await orchestrator.run_full_pipeline(project_name, input_dir)
    
    print(f"\n🎉 项目执行完成: {project.status}")

if __name__ == "__main__":
    asyncio.run(main())
