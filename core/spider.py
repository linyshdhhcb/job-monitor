"""
爬虫核心模块 - 爬取企业招聘页面
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import urljoin, urlparse
from utils.anti_crawl import get_random_headers, get_random_delay, get_random_proxy
from utils.logger import get_logger

logger = get_logger(__name__)

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JobSpider:
    """岗位爬虫类"""
    
    def __init__(self, use_proxy=False):
        """
        初始化爬虫
        
        Args:
            use_proxy: 是否使用代理
        """
        self.use_proxy = use_proxy
        self.session = requests.Session()
        self.session.headers.update(get_random_headers())
    
    def _get_with_retry(self, url, max_retries=3, timeout=30):
        """
        带重试的HTTP GET请求
        
        Args:
            url: 请求URL
            max_retries: 最大重试次数
            timeout: 超时时间
        
        Returns:
            requests.Response: 响应对象
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 更新User-Agent
                self.session.headers.update(get_random_headers())
                
                # 设置代理
                proxies = None
                if self.use_proxy:
                    proxy = get_random_proxy()
                    if proxy:
                        proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
                
                response = self.session.get(
                    url,
                    timeout=timeout,
                    proxies=proxies,
                    verify=False  # 忽略SSL验证
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    delay = get_random_delay(2, 5) * (attempt + 1)
                    logger.debug(f"等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
        
        raise last_error
    
    def scrape_static_page(self, url, job_selector, title_selector, url_selector, keywords=None):
        """
        爬取静态页面
        
        Args:
            url: 页面URL
            job_selector: 岗位列表CSS选择器
            title_selector: 标题CSS选择器
            url_selector: 链接CSS选择器
            keywords: 关键词过滤列表
        
        Returns:
            list: 岗位列表
        """
        try:
            response = self._get_with_retry(url)
            response.encoding = response.apparent_encoding or 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.select(job_selector)
            
            logger.debug(f"找到 {len(job_elements)} 个岗位元素")
            
            jobs = []
            for element in job_elements:
                try:
                    # 获取标题
                    title_element = element.select_one(title_selector)
                    if not title_element:
                        # 尝试从元素本身获取文本
                        title = element.get_text(strip=True)
                    else:
                        title = title_element.get_text(strip=True)
                    
                    if not title:
                        continue
                    
                    # 获取链接
                    url_element = element.select_one(url_selector)
                    if url_element and url_element.get('href'):
                        job_url = url_element['href']
                    elif element.name == 'a' and element.get('href'):
                        job_url = element['href']
                    else:
                        # 尝试从父元素或子元素找链接
                        link = element.find('a', href=True)
                        if link:
                            job_url = link['href']
                        else:
                            job_url = url  # 使用页面URL作为后备
                    
                    # 处理相对URL
                    if job_url.startswith('/'):
                        job_url = urljoin(url, job_url)
                    elif not job_url.startswith('http'):
                        job_url = urljoin(url, job_url)
                    
                    # 关键词过滤
                    if keywords:
                        if not self._match_keywords(title, keywords):
                            continue
                    
                    jobs.append({
                        'title': title.strip(),
                        'url': job_url.strip()
                    })
                    
                except Exception as e:
                    logger.debug(f"解析岗位元素失败: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"爬取页面失败: {url}, 错误: {e}")
            return []
    
    def scrape_dynamic_page(self, url, job_selector, title_selector, url_selector, keywords=None):
        """
        爬取动态页面（使用Selenium）
        注意：这需要安装Selenium和ChromeDriver
        
        如果没有安装Selenium，将尝试使用静态方法爬取
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                use_webdriver_manager = True
            except ImportError:
                use_webdriver_manager = False
            
            # 配置Chrome选项
            options = Options()
            options.add_argument('--headless')  # 无头模式
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'user-agent={get_random_headers()["User-Agent"]}')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            driver = None
            try:
                if use_webdriver_manager:
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                else:
                    driver = webdriver.Chrome(options=options)
                
                logger.info(f"使用Selenium访问: {url}")
                driver.get(url)
                
                # 等待页面加载
                time.sleep(random.uniform(3, 5))
                
                # 获取页面源码
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                job_elements = soup.select(job_selector)
                
                logger.debug(f"找到 {len(job_elements)} 个岗位元素")
                
                jobs = []
                for element in job_elements:
                    try:
                        title_element = element.select_one(title_selector)
                        title = title_element.get_text(strip=True) if title_element else element.get_text(strip=True)
                        
                        if not title:
                            continue
                        
                        url_element = element.select_one(url_selector)
                        if url_element and url_element.get('href'):
                            job_url = url_element['href']
                        elif element.name == 'a' and element.get('href'):
                            job_url = element['href']
                        else:
                            link = element.find('a', href=True)
                            job_url = link['href'] if link else url
                        
                        if job_url.startswith('/'):
                            job_url = urljoin(url, job_url)
                        elif not job_url.startswith('http'):
                            job_url = urljoin(url, job_url)
                        
                        if keywords and not self._match_keywords(title, keywords):
                            continue
                        
                        jobs.append({
                            'title': title.strip(),
                            'url': job_url.strip()
                        })
                        
                    except Exception as e:
                        logger.debug(f"解析动态页面岗位元素失败: {e}")
                        continue
                
                return jobs
                
            finally:
                if driver:
                    driver.quit()
                    
        except ImportError:
            logger.warning("Selenium未安装，尝试使用静态方法爬取...")
            return self.scrape_static_page(url, job_selector, title_selector, url_selector, keywords)
        except Exception as e:
            logger.error(f"Selenium爬取失败: {e}，尝试使用静态方法...")
            return self.scrape_static_page(url, job_selector, title_selector, url_selector, keywords)
    
    def _match_keywords(self, title, keywords):
        """
        检查标题是否包含关键词
        
        Args:
            title: 岗位标题
            keywords: 关键词列表
        
        Returns:
            bool: 是否匹配
        """
        if not keywords:
            return True
        
        title_lower = title.lower()
        return any(kw.lower() in title_lower for kw in keywords)
    
    def scrape_company_jobs(self, company_config):
        """
        爬取指定公司的岗位
        
        Args:
            company_config: 公司配置字典
        
        Returns:
            list: 岗位列表
        """
        company_name = company_config['name']
        url = company_config['url']
        keywords = company_config.get('keywords', [])
        
        logger.info(f"开始爬取 {company_name} 的岗位...")
        
        try:
            if company_config.get('requires_selenium', False):
                jobs = self._scrape_with_selenium(url, company_config)
            else:
                jobs = self.scrape_static_page(
                    url,
                    company_config['job_selector'],
                    company_config['title_selector'],
                    company_config.get('url_selector', 'a'),
                    keywords
                )
            
            logger.info(f"{company_name} 爬取完成，找到 {len(jobs)} 个岗位")
            return jobs
            
        except Exception as e:
            logger.error(f"{company_name} 爬取失败: {e}")
            return []
    
    def _scrape_with_selenium(self, url, config):
        """使用Selenium爬取动态页面"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            import os
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'user-agent={get_random_headers()["User-Agent"]}')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # 查找Chrome可执行文件路径
            chrome_paths = [
                r"C:\Users\a1830\AppData\Local\GptChrome\GptBrowser.exe",
                r"C:\Users\a1830\AppData\Local\GptChrome\Application\chrome.exe",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    options.binary_location = path
                    logger.info(f"使用Chrome: {path}")
                    break
            
            driver = None
            try:
                # 使用 webdriver_manager 自动下载匹配版本的 ChromeDriver
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    from webdriver_manager.core.driver_cache import DriverCacheManager
                    # 清除缓存，强制下载新版本
                    service = Service(ChromeDriverManager(driver_version="128.0.6613.137").install())
                    driver = webdriver.Chrome(service=service, options=options)
                except Exception as e:
                    logger.warning(f"webdriver_manager失败: {e}, 尝试直接启动...")
                    driver = webdriver.Chrome(options=options)
                
                logger.info(f"Selenium访问: {url}")
                driver.get(url)
                time.sleep(8)  # 百度等页面加载较慢，等待更长时间
                
                # 保存页面用于调试
                page_source = driver.page_source
                debug_file = "debug_page.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                logger.info(f"页面已保存到 {debug_file} 用于调试")
                
                soup = BeautifulSoup(page_source, 'html.parser')
                job_elements = soup.select(config['job_selector'])
                
                logger.info(f"找到 {len(job_elements)} 个岗位元素")
                
                jobs = []
                for element in job_elements:
                    try:
                        # 获取标题
                        title_el = element.select_one(config['title_selector'])
                        title = title_el.get_text(strip=True) if title_el else ""
                        if not title:
                            continue
                        
                        # 获取地点
                        location = ""
                        if config.get('location_selector'):
                            loc_el = element.select_one(config['location_selector'])
                            location = loc_el.get_text(strip=True) if loc_el else ""
                        
                        # 获取详情（部门等）
                        detail = ""
                        if config.get('detail_selector'):
                            detail_el = element.select_one(config['detail_selector'])
                            detail = detail_el.get_text(strip=True) if detail_el else ""
                        
                        # 关键词过滤（空列表不过滤）
                        keywords = config.get('keywords', [])
                        if keywords and not self._match_keywords(title, keywords):
                            continue
                        
                        jobs.append({
                            'title': title,
                            'url': url,  # 直接用列表页URL
                            'location': location,
                            'detail': detail
                        })
                        
                    except Exception as e:
                        logger.debug(f"解析岗位失败: {e}")
                        continue
                
                return jobs
                
            finally:
                if driver:
                    driver.quit()
                    
        except ImportError:
            logger.error("Selenium未安装，请运行: pip install selenium webdriver-manager")
            return []
        except Exception as e:
            logger.error(f"Selenium爬取失败: {e}")
            return []


class SimplifiedSpider:
    """
    简化版爬虫 - 针对一些常见招聘网站的专门爬虫
    不依赖Selenium，更容易使用
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(get_random_headers())
    
    def _request(self, url, method='GET', **kwargs):
        """发送请求"""
        self.session.headers.update(get_random_headers())
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=30, verify=False, **kwargs)
            else:
                response = self.session.post(url, timeout=30, verify=False, **kwargs)
            
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
            return None
    
    def scrape_lagou(self, keywords="Java", city="全国"):
        """爬取拉勾网"""
        # 拉勾网需要特殊处理，这里只是示例
        logger.info("拉勾网爬取（需要API或Selenium）")
        return []
    
    def scrape_zhipin(self, keywords="Java", city="全国"):
        """爬取Boss直聘"""
        # Boss直聘反爬较严，这里只是示例
        logger.info("Boss直聘爬取（需要API或Selenium）")
        return []
    
    def scrape_51job(self, keywords="Java实习"):
        """爬取前程无忧"""
        url = f"https://search.51job.com/list/000000,000000,0000,00,9,99,{keywords},2,1.html"
        logger.info(f"爬取前程无忧: {keywords}")
        
        response = self._request(url)
        if not response:
            return []
        
        # 解析页面
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = []
        
        # 51job的页面结构可能变化，这里是示例
        for item in soup.select('.joblist-item, .j_joblist .e'):
            try:
                title = item.select_one('.jname, .t1 a')
                if title:
                    job = {
                        'title': title.get_text(strip=True),
                        'url': title.get('href', '')
                    }
                    jobs.append(job)
            except:
                continue
        
        return jobs
