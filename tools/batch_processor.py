#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单账号大批量处理器
针对200个视频，10个人物，10个背景的优化配置
"""

import asyncio
import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
import logging

# 添加src目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.task_database import task_db, TaskStatus
from src.automation.viggle_automation import ViggleEnhancedProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/batch_processor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self):
        self.config = self.load_config()
        self.processor = ViggleEnhancedProcessor()
        
    def load_config(self):
        """加载配置"""
        config_file = Path("config/viggle_config.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    async def estimate_processing_time(self, video_count: int) -> dict:
        """估算处理时间"""
        # 单视频处理时间估算
        avg_video_duration = 60  # 假设平均60秒
        processing_time_per_video = avg_video_duration * 2  # 处理时间约为视频时长的2倍
        rate_limit_avg = (self.config.get("processing", {}).get("rate_limit_min", 60) + 
                         self.config.get("processing", {}).get("rate_limit_max", 120)) / 2
        
        total_processing_time = video_count * processing_time_per_video
        total_wait_time = video_count * rate_limit_avg
        total_time = total_processing_time + total_wait_time
        
        # 转换为小时
        hours = total_time / 3600
        
        return {
            "video_count": video_count,
            "avg_video_duration": avg_video_duration,
            "processing_time_per_video": processing_time_per_video,
            "rate_limit_avg": rate_limit_avg,
            "total_processing_time": total_processing_time,
            "total_wait_time": total_wait_time,
            "total_time_hours": hours,
            "estimated_completion": datetime.now() + timedelta(hours=hours)
        }
    
    async def check_system_requirements(self) -> bool:
        """检查系统要求"""
        logger.info("🔍 检查系统要求...")
        
        # 检查输入目录
        input_dir = Path("tasks_in")
        if not input_dir.exists():
            logger.error("❌ 输入目录不存在: tasks_in/")
            return False
        
        video_files = list(input_dir.glob("*.mp4"))
        logger.info(f"📁 找到 {len(video_files)} 个视频文件")
        
        # 检查人物图片
        people_dir = Path("input/people")
        if not people_dir.exists():
            logger.warning("⚠️ 人物图片目录不存在: input/people/")
        else:
            people_files = list(people_dir.glob("*.jpg")) + list(people_dir.glob("*.png"))
            logger.info(f"👤 找到 {len(people_files)} 个人物图片")
        
        # 检查背景图片
        bg_dir = Path("backgrounds")
        if not bg_dir.exists():
            logger.warning("⚠️ 背景图片目录不存在: backgrounds/")
        else:
            bg_files = list(bg_dir.glob("*.jpg")) + list(bg_dir.glob("*.png"))
            logger.info(f"🎨 找到 {len(bg_files)} 个背景图片")
        
        # 检查账号配置
        accounts_file = Path("config/accounts.json")
        if not accounts_file.exists():
            logger.error("❌ 账号配置文件不存在: config/accounts.json")
            return False
        
        with open(accounts_file, 'r', encoding='utf-8') as f:
            accounts_config = json.load(f)
        
        if not accounts_config.get("accounts"):
            logger.error("❌ 未配置账号信息")
            return False
        
        logger.info(f"✅ 系统检查通过，配置了 {len(accounts_config['accounts'])} 个账号")
        return True
    
    async def create_batch_tasks(self, batch_size: int = 50) -> list:
        """创建分批任务"""
        logger.info(f"📋 创建分批任务，批次大小: {batch_size}")
        
        input_dir = Path("tasks_in")
        video_files = sorted(list(input_dir.glob("*.mp4")))
        
        batches = []
        for i in range(0, len(video_files), batch_size):
            batch = video_files[i:i + batch_size]
            batches.append(batch)
            logger.info(f"批次 {len(batches)}: {len(batch)} 个视频")
        
        return batches
    
    async def process_batch(self, batch_files: list, batch_num: int) -> dict:
        """处理单个批次"""
        logger.info(f"🚀 开始处理批次 {batch_num} ({len(batch_files)} 个视频)")
        
        start_time = time.time()
        results = {
            "batch_num": batch_num,
            "total_files": len(batch_files),
            "completed": 0,
            "failed": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration": 0
        }
        
        try:
            # 运行Viggle处理
            await self.processor.run_batch_processing()
            
            # 统计结果
            completed_tasks = task_db.get_completed_tasks()
            failed_tasks = task_db.get_failed_tasks()
            
            results["completed"] = len(completed_tasks)
            results["failed"] = len(failed_tasks)
            
        except Exception as e:
            logger.error(f"❌ 批次 {batch_num} 处理失败: {str(e)}")
            results["failed"] = len(batch_files)
        
        results["end_time"] = datetime.now().isoformat()
        results["duration"] = time.time() - start_time
        
        logger.info(f"✅ 批次 {batch_num} 完成: {results['completed']} 成功, {results['failed']} 失败")
        return results
    
    async def run_full_batch_processing(self):
        """运行完整批量处理"""
        logger.info("🎯 单账号大批量处理器启动")
        logger.info("=" * 60)
        
        # 检查系统要求
        if not await self.check_system_requirements():
            logger.error("❌ 系统检查失败，请检查配置")
            return
        
        # 估算处理时间
        video_count = len(list(Path("tasks_in").glob("*.mp4")))
        time_estimate = await self.estimate_processing_time(video_count)
        
        logger.info("⏱️ 处理时间估算:")
        logger.info(f"   视频数量: {time_estimate['video_count']}")
        logger.info(f"   预计总时间: {time_estimate['total_time_hours']:.1f} 小时")
        logger.info(f"   预计完成时间: {time_estimate['estimated_completion']}")
        
        # 确认开始处理
        confirm = input("\n是否开始处理？(y/N): ").strip().lower()
        if confirm != 'y':
            logger.info("❌ 用户取消处理")
            return
        
        # 创建分批任务
        batch_size = self.config.get("batch_processing", {}).get("batch_size", 50)
        batches = await self.create_batch_tasks(batch_size)
        
        # 处理每个批次
        all_results = []
        for i, batch in enumerate(batches, 1):
            logger.info(f"\n📦 处理批次 {i}/{len(batches)}")
            
            # 处理批次
            result = await self.process_batch(batch, i)
            all_results.append(result)
            
            # 批次间暂停
            if i < len(batches):
                pause_time = self.config.get("batch_processing", {}).get("pause_between_batches", 1800)
                logger.info(f"😴 批次间暂停 {pause_time} 秒...")
                await asyncio.sleep(pause_time)
        
        # 输出最终统计
        await self.print_final_statistics(all_results)
    
    async def print_final_statistics(self, results: list):
        """输出最终统计"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 批量处理完成统计")
        logger.info("=" * 60)
        
        total_files = sum(r["total_files"] for r in results)
        total_completed = sum(r["completed"] for r in results)
        total_failed = sum(r["failed"] for r in results)
        total_duration = sum(r["duration"] for r in results)
        
        logger.info(f"📁 总文件数: {total_files}")
        logger.info(f"✅ 成功处理: {total_completed}")
        logger.info(f"❌ 处理失败: {total_failed}")
        logger.info(f"📈 成功率: {(total_completed/total_files*100):.1f}%")
        logger.info(f"⏱️ 总耗时: {total_duration/3600:.1f} 小时")
        
        # 保存统计报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": total_files,
                "total_completed": total_completed,
                "total_failed": total_failed,
                "success_rate": total_completed/total_files*100,
                "total_duration_hours": total_duration/3600
            },
            "batch_results": results
        }
        
        report_file = Path("logs/batch_processing_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 详细报告已保存: {report_file}")

async def main():
    """主函数"""
    processor = BatchProcessor()
    await processor.run_full_batch_processing()

if __name__ == "__main__":
    asyncio.run(main())
