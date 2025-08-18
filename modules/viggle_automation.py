#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle自动化模块
基于预处理队列，使用Playwright进行批量自动化处理
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

# 复用之前的优化版Playwright代码
from scripts.viggle_playwright_optimized import ViggleProcessor, ViggleTask

logger = logging.getLogger(__name__)

@dataclass
class ViggleJob:
    """Viggle处理任务"""
    video_path: str
    video_id: str
    priority: int
    estimated_credits: int
    category: str
    status: str = "pending"  # pending, processing, completed, failed
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    actual_credits: Optional[int] = None

class ViggleAutomationModule:
    def __init__(self, config_path: str = "config/viggle_automation_config.json"):
        self.config = self.load_config(config_path)
        self.processor = ViggleProcessor()
        self.job_history = []
        
    def load_config(self, config_path: str) -> dict:
        """加载自动化配置"""
        default_config = {
            "queue_settings": {
                "input_queue_file": "./modules/processing_queue.json",
                "batch_size": 5,
                "max_concurrent_jobs": 2,
                "priority_threshold": 5
            },
            "viggle_settings": {
                "max_daily_credits": 100,
                "max_retries_per_video": 3,
                "timeout_minutes": 15,
                "cool_down_minutes": 2
            },
            "output_settings": {
                "result_directory": "./viggle_results",
                "organize_by_category": True,
                "keep_originals": True
            },
            "monitoring": {
                "enable_notifications": False,
                "webhook_url": "",
                "log_level": "INFO"
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
    
    def load_processing_queue(self) -> List[ViggleJob]:
        """加载预处理队列"""
        queue_file = self.config["queue_settings"]["input_queue_file"]
        
        if not Path(queue_file).exists():
            logger.error(f"队列文件不存在: {queue_file}")
            return []
        
        try:
            with open(queue_file, 'r', encoding='utf-8') as f:
                queue_data = json.load(f)
            
            jobs = []
            for video_path in queue_data.get("queue", []):
                # 从预处理报告中获取详细信息
                video_id = Path(video_path).stem
                jobs.append(ViggleJob(
                    video_path=video_path,
                    video_id=video_id,
                    priority=7,  # 默认优先级，实际应从预处理结果获取
                    estimated_credits=2,  # 默认积分，实际应从预处理结果获取
                    category="unknown"  # 默认分类，实际应从预处理结果获取
                ))
            
            logger.info(f"加载了 {len(jobs)} 个待处理任务")
            return jobs
            
        except Exception as e:
            logger.error(f"加载队列失败: {str(e)}")
            return []
    
    def filter_jobs_by_credits(self, jobs: List[ViggleJob]) -> List[ViggleJob]:
        """根据积分限制筛选任务"""
        max_credits = self.config["viggle_settings"]["max_daily_credits"]
        
        # 按优先级排序
        sorted_jobs = sorted(jobs, key=lambda x: -x.priority)
        
        selected_jobs = []
        total_credits = 0
        
        for job in sorted_jobs:
            if total_credits + job.estimated_credits <= max_credits:
                selected_jobs.append(job)
                total_credits += job.estimated_credits
            else:
                logger.info(f"积分限制，跳过任务: {job.video_id}")
        
        logger.info(f"按积分筛选后剩余 {len(selected_jobs)} 个任务，预计消耗 {total_credits} 积分")
        return selected_jobs
    
    def organize_output_path(self, job: ViggleJob, result_filename: str) -> str:
        """组织输出路径"""
        base_dir = Path(self.config["output_settings"]["result_directory"])
        
        if self.config["output_settings"]["organize_by_category"]:
            output_dir = base_dir / job.category
        else:
            output_dir = base_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)
        return str(output_dir / result_filename)
    
    async def process_single_job(self, job: ViggleJob) -> bool:
        """处理单个任务"""
        logger.info(f"🎬 开始处理任务: {job.video_id}")
        
        job.status = "processing"
        job.start_time = datetime.now().isoformat()
        
        try:
            # 创建Viggle任务
            viggle_task = ViggleTask(
                src_path=job.video_path,
                task_id=job.video_id,
                account_id="primary"  # 简化版，实际应支持多账号
            )
            
            # 处理任务
            result_path = await self.processor.process_single_task(viggle_task)
            
            if result_path:
                # 组织输出文件
                result_filename = Path(result_path).name
                organized_path = self.organize_output_path(job, result_filename)
                
                # 移动文件到组织化目录
                Path(result_path).rename(organized_path)
                
                job.status = "completed"
                job.result_path = organized_path
                job.end_time = datetime.now().isoformat()
                
                logger.info(f"✅ 任务完成: {job.video_id} -> {organized_path}")
                return True
            else:
                raise Exception("处理结果为空")
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.end_time = datetime.now().isoformat()
            
            logger.error(f"❌ 任务失败: {job.video_id} - {str(e)}")
            return False
        
        finally:
            self.job_history.append(job)
    
    async def run_batch_processing(self):
        """运行批量处理"""
        logger.info("🚀 Viggle自动化模块启动")
        
        # 加载队列
        jobs = self.load_processing_queue()
        if not jobs:
            logger.warning("⚠️ 没有待处理的任务")
            return
        
        # 根据积分限制筛选
        selected_jobs = self.filter_jobs_by_credits(jobs)
        if not selected_jobs:
            logger.warning("⚠️ 积分限制，没有可处理的任务")
            return
        
        # 批量处理
        batch_size = self.config["queue_settings"]["batch_size"]
        max_concurrent = self.config["queue_settings"]["max_concurrent_jobs"]
        
        for i in range(0, len(selected_jobs), batch_size):
            batch = selected_jobs[i:i+batch_size]
            logger.info(f"📦 处理批次 {i//batch_size + 1}: {len(batch)} 个任务")
            
            # 控制并发
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(job):
                async with semaphore:
                    return await self.process_single_job(job)
            
            # 并发处理当前批次
            results = await asyncio.gather(
                *[process_with_semaphore(job) for job in batch],
                return_exceptions=True
            )
            
            # 统计结果
            success_count = sum(1 for r in results if r is True)
            logger.info(f"📊 批次完成: {success_count}/{len(batch)} 成功")
            
            # 批次间冷却
            if i + batch_size < len(selected_jobs):
                cool_down = self.config["viggle_settings"]["cool_down_minutes"] * 60
                logger.info(f"😴 批次间冷却 {cool_down/60:.1f} 分钟...")
                await asyncio.sleep(cool_down)
        
        # 生成处理报告
        self.generate_processing_report()
    
    def generate_processing_report(self):
        """生成处理报告"""
        if not self.job_history:
            return
        
        # 统计信息
        total_jobs = len(self.job_history)
        completed_jobs = len([j for j in self.job_history if j.status == "completed"])
        failed_jobs = len([j for j in self.job_history if j.status == "failed"])
        
        success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        # 积分统计
        total_estimated_credits = sum(j.estimated_credits for j in self.job_history)
        
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
                "total_estimated_credits": total_estimated_credits
            },
            "category_statistics": category_stats,
            "job_details": [
                {
                    "video_id": job.video_id,
                    "video_path": job.video_path,
                    "category": job.category,
                    "priority": job.priority,
                    "status": job.status,
                    "result_path": job.result_path,
                    "error_message": job.error_message,
                    "start_time": job.start_time,
                    "end_time": job.end_time,
                    "estimated_credits": job.estimated_credits
                }
                for job in self.job_history
            ]
        }
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"reports/viggle_automation_report_{timestamp}.json"
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        print("\n" + "="*60)
        print("🎭 Viggle自动化处理报告")
        print("="*60)
        print(f"📊 总计任务: {total_jobs}")
        print(f"✅ 完成: {completed_jobs}")
        print(f"❌ 失败: {failed_jobs}")
        print(f"📈 成功率: {success_rate:.1f}%")
        print(f"💰 消耗积分: {total_estimated_credits}")
        print(f"📋 分类统计: {category_stats}")
        print(f"📄 详细报告: {report_file}")
        print("="*60)
        
        return report

async def main():
    """主函数"""
    print("🎭 Dance项目 - Viggle自动化模块")
    print("="*50)
    
    automation = ViggleAutomationModule()
    await automation.run_batch_processing()

if __name__ == "__main__":
    asyncio.run(main())
