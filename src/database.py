import sqlite3
import os
from typing import List, Dict, Optional
from config.config import Config

class DatabaseManager:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建课程表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_name TEXT NOT NULL,
                    course_type TEXT NOT NULL,  -- 'required' or 'elective'
                    progress REAL DEFAULT 0.0,  -- 学习进度 0-100
                    video_url TEXT,
                    user_course_id TEXT,
                    is_completed INTEGER DEFAULT 0,  -- 0: 未完成, 1: 已完成
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建学习记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_end TIMESTAMP,
                    duration_minutes REAL,
                    progress_before REAL,
                    progress_after REAL,
                    status TEXT,  -- 'completed', 'interrupted', 'error'
                    notes TEXT,
                    FOREIGN KEY (course_id) REFERENCES courses (id)
                )
            ''')
            
            conn.commit()
    
    def add_or_update_course(self, course_name: str, course_type: str, 
                           video_url: str = None, user_course_id: str = None, 
                           progress: float = 0.0) -> int:
        """添加或更新课程信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查课程是否已存在
            cursor.execute(
                'SELECT id, progress FROM courses WHERE course_name = ? AND course_type = ?',
                (course_name, course_type)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有课程
                cursor.execute('''
                    UPDATE courses 
                    SET video_url = ?, user_course_id = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (video_url, user_course_id, existing[0]))
                return existing[0]
            else:
                # 添加新课程
                cursor.execute('''
                    INSERT INTO courses (course_name, course_type, video_url, 
                                       user_course_id, progress)
                    VALUES (?, ?, ?, ?, ?)
                ''', (course_name, course_type, video_url, user_course_id, progress))
                return cursor.lastrowid
    
    def get_incomplete_courses(self) -> List[Dict]:
        """获取未完成的课程列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM courses 
                WHERE is_completed = 0 AND progress < 100.0
                ORDER BY course_type, course_name
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_course_progress(self, course_id: int, progress: float):
        """更新课程学习进度"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            is_completed = 1 if progress >= 100.0 else 0
            
            cursor.execute('''
                UPDATE courses 
                SET progress = ?, is_completed = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (progress, is_completed, course_id))
            
            conn.commit()
    
    def add_learning_log(self, course_id: int, duration_minutes: float = None,
                        progress_before: float = None, progress_after: float = None,
                        status: str = 'completed', notes: str = None):
        """添加学习记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO learning_logs 
                (course_id, duration_minutes, progress_before, progress_after, status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (course_id, duration_minutes, progress_before, progress_after, status, notes))
            
            conn.commit()
    
    def get_all_courses(self) -> List[Dict]:
        """获取所有课程"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM courses 
                ORDER BY course_type, is_completed, course_name
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_learning_statistics(self) -> Dict:
        """获取学习统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 总课程数
            cursor.execute('SELECT COUNT(*) FROM courses')
            total_courses = cursor.fetchone()[0]
            
            # 已完成课程数
            cursor.execute('SELECT COUNT(*) FROM courses WHERE is_completed = 1')
            completed_courses = cursor.fetchone()[0]
            
            # 平均进度
            cursor.execute('SELECT AVG(progress) FROM courses')
            avg_progress = cursor.fetchone()[0] or 0
            
            # 必修课和选修课统计
            cursor.execute('''
                SELECT course_type, COUNT(*) as count, AVG(progress) as avg_progress,
                       SUM(is_completed) as completed_count
                FROM courses 
                GROUP BY course_type
            ''')
            type_stats = cursor.fetchall()
            
            return {
                'total_courses': total_courses,
                'completed_courses': completed_courses,
                'completion_rate': (completed_courses / total_courses * 100) if total_courses > 0 else 0,
                'average_progress': avg_progress,
                'course_type_stats': {
                    row[0]: {
                        'count': row[1],
                        'avg_progress': row[2],
                        'completed': row[3]
                    } for row in type_stats
                }
            }
    
    def clear_all_data(self) -> bool:
        """清空所有数据库数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取清空前的统计信息
                stats_before = self.get_learning_statistics()
                
                # 清空所有表数据
                cursor.execute('DELETE FROM learning_logs')
                cursor.execute('DELETE FROM courses')
                
                # 重置自增ID
                cursor.execute('DELETE FROM sqlite_sequence WHERE name="learning_logs"')
                cursor.execute('DELETE FROM sqlite_sequence WHERE name="courses"')
                
                conn.commit()
                
                return True
                
        except Exception as e:
            print(f"清空数据库时发生错误: {str(e)}")
            return False
    
    def get_database_info(self) -> Dict:
        """获取数据库基本信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取各表的记录数量
                cursor.execute('SELECT COUNT(*) FROM courses')
                courses_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM learning_logs')
                logs_count = cursor.fetchone()[0]
                
                # 获取数据库文件大小
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    'database_path': self.db_path,
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / 1024 / 1024, 2),
                    'courses_count': courses_count,
                    'learning_logs_count': logs_count,
                    'tables': ['courses', 'learning_logs']
                }
                
        except Exception as e:
            return {
                'database_path': self.db_path,
                'error': str(e)
            }

# 全局数据库实例
db = DatabaseManager()