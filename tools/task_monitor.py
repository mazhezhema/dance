#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务监控和状态查看工具
提供任务状态查询、统计信息查看等功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from scripts.task_database import task_db

def print_header(title: str):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"🎭 {title}")
    print(f"{'='*60}")

def print_task_status(task):
    """打印任务状态"""
    status_icons = {
        "pending": "⏳",
        "processing": "🔄", 
        "completed": "✅",
        "failed": "❌"
    }
    
    icon = status_icons.get(task.status, "❓")
    print(f"{icon} {task.task_id}")
    print(f"   文件: {Path(task.input_file).name}")
    print(f"   状态: {task.status}")
    print(f"   账号: {task.account_id or '未分配'}")
    print(f"   创建时间: {task.created_at}")
    
    if task.started_at:
        print(f"   开始时间: {task.started_at}")
    if task.completed_at:
        print(f"   完成时间: {task.completed_at}")
    if task.processing_time:
        print(f"   处理时间: {task.processing_time:.1f}秒")
    if task.output_file:
        print(f"   输出文件: {Path(task.output_file).name}")
    if task.error_message:
        print(f"   错误信息: {task.error_message}")
    if task.file_size_mb:
        print(f"   文件大小: {task.file_size_mb:.1f}MB")
    if task.video_duration:
        print(f"   视频时长: {task.video_duration:.1f}秒")
    print()

def show_overall_stats():
    """显示总体统计信息"""
    print_header("总体统计信息")
    
    stats = task_db.get_overall_stats()
    if not stats:
        print("暂无统计数据")
        return
    
    print(f"📊 任务总数: {stats['total_tasks']}")
    print(f"✅ 已完成: {stats['completed_tasks']}")
    print(f"❌ 失败: {stats['failed_tasks']}")
    print(f"⏳ 待处理: {stats['pending_tasks']}")
    print(f"🔄 处理中: {stats['processing_tasks']}")
    print(f"📈 成功率: {stats['success_rate']:.1f}%")
    print(f"⏱️ 平均处理时间: {stats['avg_processing_time']:.1f}秒")
    print(f"🕐 总处理时间: {stats['total_processing_time']:.1f}秒")

def show_recent_tasks(limit: int = 10):
    """显示最近的任务"""
    print_header(f"最近 {limit} 个任务")
    
    tasks = task_db.get_completed_tasks(limit)
    if not tasks:
        print("暂无已完成的任务")
        return
    
    for task in tasks:
        print_task_status(task)

def show_pending_tasks():
    """显示待处理任务"""
    print_header("待处理任务")
    
    tasks = task_db.get_pending_tasks()
    if not tasks:
        print("暂无待处理任务")
        return
    
    for task in tasks:
        print_task_status(task)

def show_task_details(task_id: str):
    """显示任务详细信息"""
    print_header(f"任务详情: {task_id}")
    
    task = task_db.get_task(task_id)
    if not task:
        print(f"❌ 未找到任务: {task_id}")
        return
    
    print_task_status(task)
    
    # 显示任务日志
    print("📝 任务日志:")
    logs = task_db.get_task_logs(task_id, 20)
    for log in logs:
        level_icons = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}
        icon = level_icons.get(log["level"], "ℹ️")
        timestamp = log["timestamp"][:19]  # 只显示到秒
        print(f"   {icon} [{timestamp}] {log['message']}")

def show_account_stats(account_id: str = None):
    """显示账号统计信息"""
    if account_id:
        print_header(f"账号统计: {account_id}")
        stats = task_db.get_account_stats(account_id)
        if not stats:
            print(f"❌ 未找到账号: {account_id}")
            return
    else:
        print_header("所有账号统计")
        # 这里可以扩展为显示所有账号的统计
        print("功能开发中...")
        return
    
    print(f"📧 账号: {stats['account_id']}")
    print(f"📊 总任务数: {stats['total_tasks']}")
    print(f"✅ 成功任务: {stats['completed_tasks']}")
    print(f"❌ 失败任务: {stats['failed_tasks']}")
    print(f"📈 成功率: {stats['success_rate']:.1f}%")
    print(f"⏱️ 总处理时间: {stats['total_processing_time']:.1f}秒")
    print(f"📅 每日限制: {stats['daily_limit']}")
    print(f"📅 今日已用: {stats['daily_used']}")
    print(f"📅 重置日期: {stats['reset_date']}")
    print(f"🕐 最后使用: {stats['last_used']}")

def export_stats():
    """导出统计信息"""
    print_header("导出统计信息")
    
    success = task_db.export_stats_to_json()
    if success:
        print("✅ 统计信息已导出到: tasks/stats_export.json")
    else:
        print("❌ 导出失败")

def show_help():
    """显示帮助信息"""
    print_header("任务监控工具使用说明")
    print("用法: python scripts/task_monitor.py [命令] [参数]")
    print()
    print("可用命令:")
    print("  stats              - 显示总体统计信息")
    print("  recent [数量]      - 显示最近完成的任务 (默认10个)")
    print("  pending            - 显示待处理任务")
    print("  task <任务ID>      - 显示指定任务的详细信息")
    print("  account <账号>     - 显示指定账号的统计信息")
    print("  export             - 导出统计信息到JSON文件")
    print("  help               - 显示此帮助信息")
    print()
    print("示例:")
    print("  python scripts/task_monitor.py stats")
    print("  python scripts/task_monitor.py recent 20")
    print("  python scripts/task_monitor.py task abc123def456")
    print("  python scripts/task_monitor.py account account1@example.com")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "stats":
            show_overall_stats()
        elif command == "recent":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            show_recent_tasks(limit)
        elif command == "pending":
            show_pending_tasks()
        elif command == "task":
            if len(sys.argv) < 3:
                print("❌ 请提供任务ID")
                return
            task_id = sys.argv[2]
            show_task_details(task_id)
        elif command == "account":
            account_id = sys.argv[2] if len(sys.argv) > 2 else None
            show_account_stats(account_id)
        elif command == "export":
            export_stats()
        elif command == "help":
            show_help()
        else:
            print(f"❌ 未知命令: {command}")
            show_help()
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")
        show_help()

if __name__ == "__main__":
    main()
