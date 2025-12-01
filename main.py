#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
企业招聘岗位监控系统 - 主程序入口

功能：
1. 定时监控配置的企业招聘页面
2. 检测新发布的岗位
3. 通过邮件通知用户

使用方法：
    python main.py              # 启动定时监控
    python main.py --once       # 立即执行一次检查
    python main.py --test       # 发送测试邮件
    python main.py --stats      # 显示统计信息

作者：JobMonitorSystem
版本：1.0.0
"""

import sys
import argparse
from pathlib import Path

# 确保项目根目录在Python路径中
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger, log_separator
from config import load_email_config, load_company_configs, load_settings

logger = get_logger("main")


def print_banner():
    """打印启动横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           🔍 企业招聘岗位监控系统 v1.0.0                      ║
║                                                               ║
║     自动监控企业招聘官网，发现新岗位及时通知                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def show_config_info():
    """显示配置信息"""
    try:
        # 加载配置
        email_config = load_email_config()
        company_configs = load_company_configs()
        settings = load_settings()
        
        print("\n📧 邮件配置:")
        print(f"   发件邮箱: {email_config.get('sender_email', '未配置')}")
        print(f"   收件邮箱: {email_config.get('receiver_email', '未配置')}")
        print(f"   SMTP服务器: {email_config.get('smtp_server', '未配置')}")
        
        print(f"\n🏢 监控公司 ({len(company_configs)} 个):")
        for i, company in enumerate(company_configs[:5], 1):  # 只显示前5个
            status = "✅" if company.get('enabled', True) else "❌"
            print(f"   {i}. {status} {company['name']}")
        if len(company_configs) > 5:
            print(f"   ... 还有 {len(company_configs) - 5} 个公司")
        
        print(f"\n⏰ 定时任务:")
        check_times = settings.get('schedule', {}).get('check_times', [])
        for check_time in check_times:
            hour = check_time.get('hour', 0)
            minute = check_time.get('minute', 0)
            print(f"   每天 {hour:02d}:{minute:02d} 执行检查")
        
    except Exception as e:
        logger.error(f"加载配置失败: {e}")


def show_statistics():
    """显示统计信息"""
    from core.database import JobDatabase
    
    db = JobDatabase()
    stats = db.get_statistics()
    
    print("\n📊 数据统计:")
    print(f"   总记录岗位数: {stats['total_jobs']}")
    print(f"   今日新增岗位: {stats['today_new']}")
    
    if stats['by_company']:
        print("\n   各公司岗位数:")
        for company, count in list(stats['by_company'].items())[:10]:
            print(f"      {company}: {count}")


def run_test_email():
    """发送测试邮件"""
    from core.notifier import EmailNotifier
    
    print("\n📧 发送测试邮件...")
    email_config = load_email_config()
    notifier = EmailNotifier(email_config)
    
    if notifier.send_test_email():
        print("✅ 测试邮件发送成功！请检查收件箱。")
    else:
        print("❌ 测试邮件发送失败，请检查邮箱配置。")


def run_once():
    """执行一次检查"""
    from core.scheduler import JobMonitorScheduler
    
    print("\n🔍 执行单次检查...")
    scheduler = JobMonitorScheduler()
    scheduler.run_once()
    print("\n✅ 检查完成！")


def run_scheduler():
    """启动定时调度器"""
    from core.scheduler import JobMonitorScheduler
    
    scheduler = JobMonitorScheduler()
    scheduler.start()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='企业招聘岗位监控系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py              启动定时监控
  python main.py --once       立即执行一次检查
  python main.py --test       发送测试邮件
  python main.py --stats      显示统计信息
        '''
    )
    
    parser.add_argument('--once', '-o', action='store_true',
                       help='立即执行一次检查，不启动定时任务')
    parser.add_argument('--test', '-t', action='store_true',
                       help='发送测试邮件，验证邮箱配置')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='显示数据库统计信息')
    parser.add_argument('--config', '-c', action='store_true',
                       help='显示当前配置信息')
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    try:
        if args.config:
            show_config_info()
        elif args.stats:
            show_statistics()
        elif args.test:
            run_test_email()
        elif args.once:
            run_once()
        else:
            # 显示配置信息
            show_config_info()
            print("\n" + "=" * 60)
            # 启动定时调度
            run_scheduler()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断，系统已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"系统错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
