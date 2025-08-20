#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务状态管理数据库模块
使用SQLite管理任务状态、进度跟踪和统计信息
"""

import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class TaskStatus:
    """任务状态数据类"""
    task_id: str
    input_file: str
    output_file: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed
    account_id: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time: Optional[float] = None
    retries: int = 0
    max_retries: int = 2
    error_message: Optional[str] = None
    file_size_mb: Optional[float] = None
    video_duration: Optional[float] = None

class TaskDatabase:
    """任务状态数据库管理器"""
    
    def __init__(self, db_path: str = "tasks/task_status.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建任务状态表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    input_file TEXT NOT NULL,
                    output_file TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    account_id TEXT,
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    processing_time REAL,
                    retries INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 2,
                    error_message TEXT,
                    file_size_mb REAL,
                    video_duration REAL,
                    updated_at TEXT
                )
            """)
            
            # 创建处理日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    log_level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            """)
            
            # 创建账号使用统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_stats (
                    account_id TEXT PRIMARY KEY,
                    total_tasks INTEGER DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    total_processing_time REAL DEFAULT 0,
                    last_used TEXT,
                    daily_limit INTEGER DEFAULT 30,
                    daily_used INTEGER DEFAULT 0,
                    reset_date TEXT
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_account ON tasks(account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_task ON task_logs(task_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON task_logs(timestamp)")
            
            conn.commit()
            logger.info(f"数据库初始化完成: {self.db_path}")
    
    def add_task(self, task: TaskStatus) -> bool:
        """添加新任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO tasks (
                        task_id, input_file, output_file, status, account_id,
                        created_at, started_at, completed_at, processing_time,
                        retries, max_retries, error_message, file_size_mb,
                        video_duration, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.task_id, task.input_file, task.output_file, task.status,
                    task.account_id, task.created_at, task.started_at, task.completed_at,
                    task.processing_time, task.retries, task.max_retries, task.error_message,
                    task.file_size_mb, task.video_duration, datetime.now().isoformat()
                ))
                conn.commit()
                logger.info(f"任务已添加: {task.task_id}")
                return True
        except Exception as e:
            logger.error(f"添加任务失败: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
                row = cursor.fetchone()
                
                if row:
                    return TaskStatus(
                        task_id=row[0], input_file=row[1], output_file=row[2],
                        status=row[3], account_id=row[4], created_at=row[5],
                        started_at=row[6], completed_at=row[7], processing_time=row[8],
                        retries=row[9], max_retries=row[10], error_message=row[11],
                        file_size_mb=row[12], video_duration=row[13]
                    )
                return None
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None
    
    def update_task_status(self, task_id: str, status: str, **kwargs) -> bool:
        """更新任务状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建更新字段
                update_fields = ["status = ?", "updated_at = ?"]
                values = [status, datetime.now().isoformat()]
                
                for key, value in kwargs.items():
                    if key in ['output_file', 'account_id', 'started_at', 'completed_at', 
                              'processing_time', 'retries', 'error_message', 'file_size_mb', 'video_duration']:
                        update_fields.append(f"{key} = ?")
                        values.append(value)
                
                values.append(task_id)
                
                query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = ?"
                cursor.execute(query, values)
                conn.commit()
                
                logger.info(f"任务状态已更新: {task_id} -> {status}")
                return True
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False
    
    def get_pending_tasks(self) -> List[TaskStatus]:
        """获取待处理任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM tasks 
                    WHERE status IN ('pending', 'failed') 
                    AND retries < max_retries
                    ORDER BY created_at ASC
                """)
                
                tasks = []
                for row in cursor.fetchall():
                    task = TaskStatus(
                        task_id=row[0], input_file=row[1], output_file=row[2],
                        status=row[3], account_id=row[4], created_at=row[5],
                        started_at=row[6], completed_at=row[7], processing_time=row[8],
                        retries=row[9], max_retries=row[10], error_message=row[11],
                        file_size_mb=row[12], video_duration=row[13]
                    )
                    tasks.append(task)
                
                return tasks
        except Exception as e:
            logger.error(f"获取待处理任务失败: {e}")
            return []
    
    def get_completed_tasks(self, limit: int = 100) -> List[TaskStatus]:
        """获取已完成任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM tasks 
                    WHERE status = 'completed'
                    ORDER BY completed_at DESC
                    LIMIT ?
                """, (limit,))
                
                tasks = []
                for row in cursor.fetchall():
                    task = TaskStatus(
                        task_id=row[0], input_file=row[1], output_file=row[2],
                        status=row[3], account_id=row[4], created_at=row[5],
                        started_at=row[6], completed_at=row[7], processing_time=row[8],
                        retries=row[9], max_retries=row[10], error_message=row[11],
                        file_size_mb=row[12], video_duration=row[13]
                    )
                    tasks.append(task)
                
                return tasks
        except Exception as e:
            logger.error(f"获取已完成任务失败: {e}")
            return []
    
    def add_task_log(self, task_id: str, level: str, message: str):
        """添加任务日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO task_logs (task_id, log_level, message, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (task_id, level, message, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"添加任务日志失败: {e}")
    
    def get_task_logs(self, task_id: str, limit: int = 50) -> List[Dict]:
        """获取任务日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT log_level, message, timestamp 
                    FROM task_logs 
                    WHERE task_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (task_id, limit))
                
                logs = []
                for row in cursor.fetchall():
                    logs.append({
                        "level": row[0],
                        "message": row[1],
                        "timestamp": row[2]
                    })
                
                return logs
        except Exception as e:
            logger.error(f"获取任务日志失败: {e}")
            return []
    
    def update_account_stats(self, account_id: str, task_completed: bool = True, 
                           processing_time: float = 0):
        """更新账号统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查是否需要重置每日计数
                cursor.execute("SELECT reset_date, daily_used FROM account_stats WHERE account_id = ?", (account_id,))
                row = cursor.fetchone()
                
                today = datetime.now().strftime("%Y-%m-%d")
                if row:
                    reset_date, daily_used = row
                    if reset_date != today:
                        daily_used = 0
                else:
                    daily_used = 0
                
                if task_completed:
                    daily_used += 1
                
                cursor.execute("""
                    INSERT OR REPLACE INTO account_stats (
                        account_id, total_tasks, completed_tasks, failed_tasks,
                        total_processing_time, last_used, daily_limit, daily_used, reset_date
                    ) VALUES (?, 
                        COALESCE((SELECT total_tasks FROM account_stats WHERE account_id = ?), 0) + 1,
                        COALESCE((SELECT completed_tasks FROM account_stats WHERE account_id = ?), 0) + ?,
                        COALESCE((SELECT failed_tasks FROM account_stats WHERE account_id = ?), 0) + ?,
                        COALESCE((SELECT total_processing_time FROM account_stats WHERE account_id = ?), 0) + ?,
                        ?, ?, ?, ?
                    )
                """, (
                    account_id, account_id, account_id, 1 if task_completed else 0,
                    account_id, 0 if task_completed else 1, account_id, processing_time,
                    datetime.now().isoformat(), 30, daily_used, today
                ))
                
                conn.commit()
        except Exception as e:
            logger.error(f"更新账号统计失败: {e}")
    
    def get_account_stats(self, account_id: str) -> Optional[Dict]:
        """获取账号统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM account_stats WHERE account_id = ?", (account_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "account_id": row[0],
                        "total_tasks": row[1],
                        "completed_tasks": row[2],
                        "failed_tasks": row[3],
                        "total_processing_time": row[4],
                        "last_used": row[5],
                        "daily_limit": row[6],
                        "daily_used": row[7],
                        "reset_date": row[8],
                        "success_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0
                    }
                return None
        except Exception as e:
            logger.error(f"获取账号统计失败: {e}")
            return None
    
    def get_overall_stats(self) -> Dict:
        """获取总体统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 任务统计
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_tasks,
                        SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing_tasks,
                        AVG(processing_time) as avg_processing_time,
                        SUM(processing_time) as total_processing_time
                    FROM tasks
                """)
                
                row = cursor.fetchone()
                if row:
                    total_tasks, completed_tasks, failed_tasks, pending_tasks, processing_tasks, avg_time, total_time = row
                    
                    return {
                        "total_tasks": total_tasks or 0,
                        "completed_tasks": completed_tasks or 0,
                        "failed_tasks": failed_tasks or 0,
                        "pending_tasks": pending_tasks or 0,
                        "processing_tasks": processing_tasks or 0,
                        "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                        "avg_processing_time": avg_time or 0,
                        "total_processing_time": total_time or 0
                    }
                
                return {}
        except Exception as e:
            logger.error(f"获取总体统计失败: {e}")
            return {}
    
    def export_stats_to_json(self, output_path: str = "tasks/stats_export.json"):
        """导出统计信息到JSON文件"""
        try:
            stats = {
                "overall_stats": self.get_overall_stats(),
                "recent_tasks": [asdict(task) for task in self.get_completed_tasks(50)],
                "export_time": datetime.now().isoformat()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            logger.info(f"统计信息已导出到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出统计信息失败: {e}")
            return False

# 全局数据库实例
task_db = TaskDatabase()
