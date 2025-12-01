"""
数据库模块 - SQLite数据库操作
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class JobDatabase:
    """岗位数据库管理类"""
    
    def __init__(self, db_path="data/jobs.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        # 确保路径是相对于项目根目录的
        project_root = Path(__file__).parent.parent
        self.db_path = project_root / db_path
        
        # 确保数据目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库表
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
        return conn
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建岗位表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                job_title TEXT NOT NULL,
                job_url TEXT NOT NULL,
                job_hash TEXT UNIQUE NOT NULL,
                location TEXT DEFAULT '',
                detail TEXT DEFAULT '',
                found_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new',
                notified INTEGER DEFAULT 0
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_hash ON jobs(job_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_found_time ON jobs(found_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_company ON jobs(company)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)')
        
        # 数据库迁移：添加detail列（如果不存在）
        try:
            cursor.execute("ALTER TABLE jobs ADD COLUMN detail TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # 列已存在
        
        # 创建检查记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS check_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                jobs_found INTEGER DEFAULT 0,
                new_jobs INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                error_message TEXT DEFAULT ''
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.debug("数据库初始化完成")
    
    @staticmethod
    def get_job_hash(company, title, url):
        """
        生成岗位唯一标识
        
        Args:
            company: 公司名称
            title: 岗位标题
            url: 岗位链接
        
        Returns:
            str: MD5哈希值
        """
        # 使用公司名+标题+URL生成唯一标识
        combined = f"{company.strip().lower()}|{title.strip().lower()}|{url.strip().lower()}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def is_new_job(self, company, title, url):
        """
        检查是否为新岗位
        
        Args:
            company: 公司名称
            title: 岗位标题
            url: 岗位链接
        
        Returns:
            tuple: (是否新岗位, 岗位哈希值)
        """
        job_hash = self.get_job_hash(company, title, url)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM jobs WHERE job_hash = ?", (job_hash,))
        result = cursor.fetchone()
        conn.close()
        
        return result is None, job_hash
    
    def save_new_job(self, company, title, url, job_hash, location="", detail=""):
        """
        保存新岗位到数据库
        
        Args:
            company: 公司名称
            title: 岗位标题
            url: 岗位链接
            job_hash: 岗位哈希值
            location: 工作地点
            detail: 详细信息（部门等）
        
        Returns:
            bool: 是否保存成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO jobs (company, job_title, job_url, job_hash, location, detail)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (company, title, url, job_hash, location, detail))
            conn.commit()
            logger.debug(f"保存新岗位: {company} - {title}")
            return True
        except sqlite3.IntegrityError:
            logger.debug(f"岗位已存在: {company} - {title}")
            return False
        finally:
            conn.close()
    
    def get_unnotified_jobs(self):
        """
        获取未通知的新岗位
        
        Returns:
            list: 未通知的岗位列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, company, job_title, job_url, location, detail, found_time
            FROM jobs
            WHERE notified = 0 AND status = 'new'
            ORDER BY found_time DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row['id'],
                'company': row['company'],
                'title': row['job_title'],
                'url': row['job_url'],
                'location': row['location'],
                'detail': row['detail'],
                'found_time': row['found_time']
            }
            for row in results
        ]
    
    def mark_jobs_as_notified(self, job_ids):
        """
        标记岗位为已通知
        
        Args:
            job_ids: 岗位ID列表
        """
        if not job_ids:
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join('?' for _ in job_ids)
        cursor.execute(f'''
            UPDATE jobs SET notified = 1, status = 'processed'
            WHERE id IN ({placeholders})
        ''', job_ids)
        
        conn.commit()
        conn.close()
        logger.debug(f"标记 {len(job_ids)} 个岗位为已通知")
    
    def get_new_jobs_since(self, hours=24):
        """
        获取指定时间内的新岗位
        
        Args:
            hours: 时间范围（小时）
        
        Returns:
            list: 岗位列表
        """
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT company, job_title, job_url, location, found_time
            FROM jobs
            WHERE found_time > ?
            ORDER BY found_time DESC
        ''', (since_time,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'company': row['company'],
                'title': row['job_title'],
                'url': row['job_url'],
                'location': row['location'],
                'found_time': row['found_time']
            }
            for row in results
        ]
    
    def log_check(self, company, jobs_found, new_jobs, status='success', error_message=''):
        """
        记录检查日志
        
        Args:
            company: 公司名称
            jobs_found: 找到的岗位数量
            new_jobs: 新岗位数量
            status: 状态
            error_message: 错误信息
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO check_logs (company, jobs_found, new_jobs, status, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (company, jobs_found, new_jobs, status, error_message))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        """
        获取统计信息
        
        Returns:
            dict: 统计信息
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 总岗位数
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]
        
        # 今日新增
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE DATE(found_time) = ?", (today,))
        today_new = cursor.fetchone()[0]
        
        # 各公司岗位数
        cursor.execute('''
            SELECT company, COUNT(*) as count
            FROM jobs
            GROUP BY company
            ORDER BY count DESC
        ''')
        by_company = {row['company']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total_jobs': total_jobs,
            'today_new': today_new,
            'by_company': by_company
        }
    
    def cleanup_old_data(self, keep_days=30):
        """
        清理过期数据
        
        Args:
            keep_days: 保留天数
        """
        cutoff_time = (datetime.now() - timedelta(days=keep_days)).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 删除过期岗位
        cursor.execute("DELETE FROM jobs WHERE found_time < ?", (cutoff_time,))
        deleted_jobs = cursor.rowcount
        
        # 删除过期日志
        cursor.execute("DELETE FROM check_logs WHERE check_time < ?", (cutoff_time,))
        deleted_logs = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_jobs > 0 or deleted_logs > 0:
            logger.info(f"清理过期数据: 删除 {deleted_jobs} 条岗位记录, {deleted_logs} 条日志")
