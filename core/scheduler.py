"""
任务调度模块 - 定时执行监控任务
"""

import time
import random
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from core.spider import JobSpider
from core.database import JobDatabase
from core.notifier import EmailNotifier
from config import load_company_configs, load_email_config, load_settings
from utils.logger import get_logger, log_separator

logger = get_logger(__name__)


class JobMonitorScheduler:
    """岗位监控调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.settings = load_settings()
        self.company_configs = load_company_configs()
        self.email_config = load_email_config()
        
        self.spider = JobSpider(use_proxy=self.settings.get('spider', {}).get('use_proxy', False))
        self.db = JobDatabase()
        self.notifier = EmailNotifier(self.email_config)
        
        self.scheduler = BlockingScheduler(timezone='Asia/Shanghai')
    
    def monitor_single_company(self, company_config):
        """
        监控单个公司
        
        Args:
            company_config: 公司配置
        
        Returns:
            list: 新发现的岗位列表
        """
        company_name = company_config['name']
        
        try:
            # 爬取岗位
            jobs = self.spider.scrape_company_jobs(company_config)
            
            new_jobs_found = []
            for job in jobs:
                is_new, job_hash = self.db.is_new_job(
                    company_name,
                    job['title'],
                    job['url']
                )
                
                if is_new:
                    if self.db.save_new_job(
                        company_name,
                        job['title'],
                        job['url'],
                        job_hash,
                        job.get('location', ''),
                        job.get('detail', '')
                    ):
                        new_jobs_found.append({
                            'company': company_name,
                            'company_url': company_config.get('url', ''),
                            'title': job['title'],
                            'url': job['url'],
                            'location': job.get('location', ''),
                            'detail': job.get('detail', ''),
                            'found_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        logger.info(f"新岗位: {company_name} - {job['title']}")
            
            # 记录检查日志
            self.db.log_check(
                company_name,
                len(jobs),
                len(new_jobs_found),
                'success'
            )
            
            return new_jobs_found
            
        except Exception as e:
            logger.error(f"❌ {company_name} 监控失败: {e}")
            self.db.log_check(company_name, 0, 0, 'error', str(e))
            return []
    
    def monitor_all_companies(self):
        """监控所有配置的公司"""
        log_separator(logger, "开始监控任务")
        logger.info(f"待监控公司数量: {len(self.company_configs)}")
        
        all_new_jobs = []
        
        for company_config in self.company_configs:
            if not company_config.get('enabled', True):
                logger.debug(f"跳过已禁用的公司: {company_config['name']}")
                continue
            
            new_jobs = self.monitor_single_company(company_config)
            all_new_jobs.extend(new_jobs)
            
            # 随机延迟，避免请求过快
            spider_settings = self.settings.get('spider', {})
            delay = random.uniform(
                spider_settings.get('request_delay_min', 2),
                spider_settings.get('request_delay_max', 5)
            )
            logger.debug(f"等待 {delay:.1f} 秒...")
            time.sleep(delay)
        
        log_separator(logger, "监控任务完成")
        logger.info(f"本次共发现 {len(all_new_jobs)} 个新岗位")
        
        return all_new_jobs
    
    def check_and_notify(self):
        """检查新岗位并发送通知"""
        log_separator(logger, "开始检查和通知")
        
        # 执行监控
        self.monitor_all_companies()
        
        # 获取未通知的新岗位
        unnotified_jobs = self.db.get_unnotified_jobs()
        
        if unnotified_jobs:
            logger.info(f"有 {len(unnotified_jobs)} 个新岗位待通知")
            
            # 发送邮件通知
            if self.notifier.send_notification(unnotified_jobs):
                # 标记为已通知
                job_ids = [job['id'] for job in unnotified_jobs]
                self.db.mark_jobs_as_notified(job_ids)
        else:
            logger.info("没有新岗位需要通知")
        
        # 清理过期数据
        keep_days = self.settings.get('database', {}).get('keep_days', 30)
        self.db.cleanup_old_data(keep_days)
        
        log_separator(logger, "检查和通知完成")
    
    def run_once(self):
        """立即执行一次检查"""
        logger.info("执行单次检查...")
        self.check_and_notify()
    
    def start(self):
        """启动调度器"""
        logger.info("=" * 60)
        logger.info("🚀 启动岗位监控系统")
        logger.info("=" * 60)
        
        # 获取调度时间配置
        schedule_config = self.settings.get('schedule', {})
        check_times = schedule_config.get('check_times', [
            {'hour': 13, 'minute': 0},
            {'hour': 19, 'minute': 0}
        ])
        
        # 添加定时任务
        for check_time in check_times:
            hour = check_time.get('hour', 13)
            minute = check_time.get('minute', 0)
            
            self.scheduler.add_job(
                self.check_and_notify,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=f'check_job_{hour}_{minute}',
                name=f'岗位检查任务 {hour:02d}:{minute:02d}',
                replace_existing=True
            )
            logger.info(f"📅 已添加定时任务: 每天 {hour:02d}:{minute:02d} 执行检查")
        
        # 打印统计信息
        stats = self.db.get_statistics()
        logger.info(f"📊 数据库统计: 总岗位 {stats['total_jobs']} 个, 今日新增 {stats['today_new']} 个")
        
        logger.info("-" * 60)
        logger.info("系统正在运行，等待定时任务执行...")
        logger.info("按 Ctrl+C 停止系统")
        logger.info("-" * 60)
        
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止系统...")
            self.scheduler.shutdown()
            logger.info("系统已停止")


def run_scheduler():
    """运行调度器的入口函数"""
    scheduler = JobMonitorScheduler()
    scheduler.start()


def run_once():
    """执行一次检查的入口函数"""
    scheduler = JobMonitorScheduler()
    scheduler.run_once()


if __name__ == '__main__':
    run_scheduler()
