"""
日志模块 - 统一的日志记录
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def get_logger(name=None, log_level=logging.INFO):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，默认为调用模块的名称
        log_level: 日志级别
    
    Returns:
        logging.Logger: 日志记录器实例
    """
    if name is None:
        name = "job_monitor"
    
    logger = logging.getLogger(name)
    
    # 如果已经有处理器，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    
    # 创建日志目录
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志文件路径
    log_file = log_dir / "job_monitor.log"
    
    # 格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # 文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def log_separator(logger, title=""):
    """打印分隔线"""
    if title:
        logger.info(f"{'='*20} {title} {'='*20}")
    else:
        logger.info("=" * 50)


def log_job_found(logger, company, title, url):
    """记录发现的新岗位"""
    logger.info(f"🆕 新岗位 | {company} | {title}")
    logger.debug(f"   链接: {url}")
