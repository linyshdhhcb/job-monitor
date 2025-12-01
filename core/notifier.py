"""
通知模块 - 邮件通知
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class EmailNotifier:
    """邮件通知类"""
    
    def __init__(self, email_config):
        """
        初始化邮件通知器
        
        Args:
            email_config: 邮件配置字典
        """
        self.smtp_server = email_config.get('smtp_server', 'smtp.qq.com')
        self.smtp_port = email_config.get('smtp_port', 465)
        self.use_ssl = email_config.get('use_ssl', True)
        self.sender_email = email_config.get('sender_email')
        self.sender_password = email_config.get('sender_password')
        self.receiver_email = email_config.get('receiver_email')
        self.subject_prefix = email_config.get('subject_prefix', '【新岗位提醒】')
        self.max_retry = email_config.get('max_retry', 3)
        self.retry_delay = email_config.get('retry_delay', 5)
        
        # 加载邮件模板
        self.template = self._load_template()
    
    def _load_template(self):
        """加载邮件HTML模板"""
        template_path = Path(__file__).parent.parent / "templates" / "email_template.html"
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # 返回默认模板
            return self._get_default_template()
    
    def _get_default_template(self):
        """获取默认邮件模板"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .header .count { font-size: 48px; font-weight: bold; margin: 10px 0; }
        .company-section { margin-bottom: 25px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }
        .company-header { background-color: #f5f5f5; padding: 12px 20px; font-weight: bold; font-size: 16px; border-bottom: 2px solid #667eea; }
        .job-list { padding: 15px 20px; }
        .job-item { padding: 10px 0; border-bottom: 1px solid #eee; }
        .job-item:last-child { border-bottom: none; }
        .job-title { font-size: 15px; font-weight: 600; color: #1a73e8; text-decoration: none; }
        .job-title:hover { text-decoration: underline; }
        .job-meta { font-size: 12px; color: #666; margin-top: 4px; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>新岗位提醒</h1>
        <div class="count">{total_count}</div>
        <p>发现 {total_count} 个新发布的职位</p>
    </div>
    
    {job_sections}
    
    <div class="footer">
        <p>系统自动监控 | 生成时间: {timestamp}</p>
        <p>© 2024 岗位监控系统 | 本邮件由系统自动发送</p>
    </div>
</body>
</html>
'''
    
    def _render_email(self, jobs):
        """
        渲染邮件内容
        
        Args:
            jobs: 岗位列表
        
        Returns:
            str: HTML内容
        """
        # 按公司分组
        jobs_by_company = {}
        for job in jobs:
            company = job['company']
            if company not in jobs_by_company:
                jobs_by_company[company] = []
            jobs_by_company[company].append(job)
        
        # 生成公司分区HTML
        sections_html = ""
        for company, company_jobs in jobs_by_company.items():
            # 获取公司URL（从第一个job里取）
            company_url = company_jobs[0].get('company_url', '') if company_jobs else ''
            
            jobs_html = ""
            for job in company_jobs:
                meta_parts = []
                if job.get('location'):
                    meta_parts.append(f"{job['location']}")
                if job.get('detail'):
                    meta_parts.append(job['detail'])
                if job.get('found_time'):
                    meta_parts.append(f"{job['found_time']}")
                meta_str = " | ".join(meta_parts) if meta_parts else ""
                
                jobs_html += f'''
                <div class="job-item">
                    <div class="job-title">{job['title']}</div>
                    <div class="job-meta">{meta_str}</div>
                </div>
                '''
            
            # 公司名称做成可点击链接
            if company_url:
                company_link = f'<a href="{company_url}" target="_blank" style="color: #1a73e8; text-decoration: none;">🏢 {company}</a>'
            else:
                company_link = f'🏢 {company}'
            
            sections_html += f'''
            <div class="company-section">
                <div class="company-header">{company_link} ({len(company_jobs)} 个新岗位)</div>
                <div class="job-list">
                    {jobs_html}
                </div>
            </div>
            '''
        
        # 替换模板变量
        html = self.template.replace('{total_count}', str(len(jobs)))
        html = html.replace('{job_sections}', sections_html)
        html = html.replace('{timestamp}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return html
    
    def send_notification(self, jobs):
        """
        发送岗位通知邮件
        
        Args:
            jobs: 岗位列表
        
        Returns:
            bool: 是否发送成功
        """
        if not jobs:
            logger.info("没有新岗位，不发送邮件")
            return True
        
        if not self.sender_email or not self.sender_password:
            logger.error("邮件配置不完整，无法发送")
            return False
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'{self.subject_prefix}发现 {len(jobs)} 个新职位'
        msg['From'] = self.sender_email
        msg['To'] = self.receiver_email
        
        # 渲染HTML内容
        html_content = self._render_email(jobs)
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 发送邮件
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                server.starttls()
            
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, self.receiver_email, msg.as_string())
            
            try:
                server.quit()
            except:
                pass  # 忽略关闭连接时的错误
            
            logger.info(f"邮件发送成功！通知了 {len(jobs)} 个新岗位")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"邮箱认证失败，请检查邮箱和授权码是否正确: {e}")
            return False
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def send_test_email(self):
        """发送测试邮件"""
        test_jobs = [
            {
                'company': '测试公司',
                'title': 'Java后端开发实习生',
                'url': 'https://example.com/job/1',
                'location': '北京',
                'found_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'company': '测试公司',
                'title': 'Python开发工程师',
                'url': 'https://example.com/job/2',
                'location': '上海',
                'found_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        logger.info("发送测试邮件...")
        return self.send_notification(test_jobs)
    
    def send_daily_summary(self, stats):
        """
        发送每日摘要邮件
        
        Args:
            stats: 统计信息
        """
        html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; padding: 20px; }}
        .summary {{ background: #1296db; padding: 20px; border-radius: 8px; }}
        .stat-item {{ margin: 10px 0; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
    </style>
</head>
<body>
    <h2>每日监控摘要</h2>
    <div class="summary">
        <div class="stat-item">
            <span>今日新增岗位：</span>
            <span class="stat-value">{stats.get('today_new', 0)}</span>
        </div>
        <div class="stat-item">
            <span>总记录岗位：</span>
            <span class="stat-value">{stats.get('total_jobs', 0)}</span>
        </div>
    </div>
    <p style="color: #999; font-size: 12px; margin-top: 20px;">
        生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </p>
</body>
</html>
'''
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'{self.subject_prefix}每日监控摘要'
        msg['From'] = self.sender_email
        msg['To'] = self.receiver_email
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        
        try:
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30)
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, self.receiver_email, msg.as_string())
            try:
                server.quit()
            except:
                pass
            logger.info("每日摘要邮件发送成功")
            return True
        except Exception as e:
            logger.error(f"每日摘要邮件发送失败: {e}")
            return False
