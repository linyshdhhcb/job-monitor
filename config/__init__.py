"""
配置模块 - 加载和管理配置文件
"""

import os
import yaml
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def load_yaml_config(filename):
    """加载YAML配置文件"""
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_company_configs():
    """加载公司配置"""
    config = load_yaml_config('companies.yaml')
    # 只返回启用的公司
    companies = config.get('companies', [])
    return [c for c in companies if c.get('enabled', True)]


def load_email_config():
    """加载邮件配置"""
    config = load_yaml_config('email_config.yaml')
    return config.get('email', {})


def load_settings():
    """加载系统设置"""
    return load_yaml_config('settings.yaml')


def load_proxy_list():
    """加载代理IP列表"""
    proxy_file = CONFIG_DIR / "proxy_list.txt"
    if not proxy_file.exists():
        return []
    
    proxies = []
    with open(proxy_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                proxies.append(line)
    return proxies
