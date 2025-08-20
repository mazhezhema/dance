#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库功能测试脚本
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.task_database import task_db, TaskStatus
from datetime import datetime

def test_database():
    """测试数据库功能"""
    print("🧪 开始测试数据库功能...")
    
    # 测试添加任务
    print("\n1. 测试添加任务...")
    test_task = TaskStatus(
        task_id="test_123456",
        input_file="test_video.mp4",
        status="pending",
        created_at=datetime.now().isoformat(),
        file_size_mb=15.5,
        video_duration=60.0
    )
    
    success = task_db.add_task(test_task)
    print(f"✅ 添加任务: {'成功' if success else '失败'}")
    
    # 测试获取任务
    print("\n2. 测试获取任务...")
    retrieved_task = task_db.get_task("test_123456")
    if retrieved_task:
        print(f"✅ 获取任务成功: {retrieved_task.task_id}")
        print(f"   文件: {retrieved_task.input_file}")
        print(f"   状态: {retrieved_task.status}")
    else:
        print("❌ 获取任务失败")
    
    # 测试更新任务状态
    print("\n3. 测试更新任务状态...")
    success = task_db.update_task_status(
        "test_123456", 
        "processing",
        started_at=datetime.now().isoformat(),
        account_id="test@example.com"
    )
    print(f"✅ 更新状态: {'成功' if success else '失败'}")
    
    # 测试添加日志
    print("\n4. 测试添加日志...")
    task_db.add_task_log("test_123456", "INFO", "开始处理任务")
    task_db.add_task_log("test_123456", "INFO", "文件上传完成")
    task_db.add_task_log("test_123456", "WARNING", "生成时间较长")
    print("✅ 添加日志完成")
    
    # 测试获取日志
    print("\n5. 测试获取日志...")
    logs = task_db.get_task_logs("test_123456", 10)
    print(f"✅ 获取到 {len(logs)} 条日志")
    for log in logs:
        print(f"   [{log['timestamp'][:19]}] {log['level']}: {log['message']}")
    
    # 测试更新账号统计
    print("\n6. 测试更新账号统计...")
    task_db.update_account_stats("test@example.com", True, 120.5)
    print("✅ 更新账号统计完成")
    
    # 测试获取账号统计
    print("\n7. 测试获取账号统计...")
    stats = task_db.get_account_stats("test@example.com")
    if stats:
        print(f"✅ 账号统计: {stats['account_id']}")
        print(f"   总任务数: {stats['total_tasks']}")
        print(f"   成功任务: {stats['completed_tasks']}")
        print(f"   成功率: {stats['success_rate']:.1f}%")
    else:
        print("❌ 获取账号统计失败")
    
    # 测试获取总体统计
    print("\n8. 测试获取总体统计...")
    overall_stats = task_db.get_overall_stats()
    print(f"✅ 总体统计:")
    print(f"   任务总数: {overall_stats.get('total_tasks', 0)}")
    print(f"   已完成: {overall_stats.get('completed_tasks', 0)}")
    print(f"   成功率: {overall_stats.get('success_rate', 0):.1f}%")
    
    # 测试导出统计
    print("\n9. 测试导出统计...")
    success = task_db.export_stats_to_json("tasks/test_stats.json")
    print(f"✅ 导出统计: {'成功' if success else '失败'}")
    
    print("\n🎉 数据库功能测试完成！")

if __name__ == "__main__":
    test_database()
