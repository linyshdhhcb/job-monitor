# 互联网大厂招聘官网岗位监控

为什么会有这个项目？是我自己在找大厂后端开发的实习，自己在Boss投的多，大厂招聘官网我会浏览，但是发现公司多有些麻烦，而且岗位新增也不是每天都有合适的，所以搞了这个，自动监控互联网大厂招聘官网，发现新岗位及时邮件通知。为你提供一下方便（因为我是Java开发，对Python就是学校了应付考试的程度，这项目功能就是有些简单的，我主要是自用，感觉足够，你可以自己扩展功能）

## 技术栈

- **语言**：Python  
- **爬虫**：`requests` + `BeautifulSoup`，可选 `Selenium`  
- **调度**：APScheduler 定时任务  
- **存储**：SQLite  
- **通知**：SMTP 邮件（已适配 QQ 邮箱）  

##  功能特点

- **自动监控**：定时检查配置的企业招聘页面
- **新岗位检测**：自动识别新发布的岗位
- **岗位去重与历史记录**：使用 SQLite 数据库存储历史岗位，避免重复通知  
-  **邮件通知**：发现新岗位立即邮件通知
- **简单易用**：双击bat文件即可运行
- **可扩展公司列表**：通过 [config/companies.yaml](cci:7://file:///c:/Code_Concenter/PyCharm/JobMonitorSystem/config/companies.yaml:0:0-0:0) 自定义要监控的公司和页面 
- **反爬与重试机制**：随机 UA、请求间隔、重试次数可配置，尽量降低被封风险  

## 当前已适配公司

以下公司已在 `config/companies.yaml` 中预置好示例配置（实际可根据需要增删）：

- [网易](https://hr.163.com/job-list.html?workType=1)
- [美团](https://zhaopin.meituan.com/web/position?hiringType=2_6&jfJgList=11001_1100109)
- [快手](https://zhaopin.kuaishou.cn/recruit/e/#/official/trainee/?workLocationCode=domestic&positionCategoryCode=J0012&pageNum=1)
- [哔哩哔哩](https://jobs.bilibili.com/campus/positions?code=01&practiceTypes=1&type=0)
- [携程](https://campus.ctrip.com/campus-recruitment/trip/37757/#/jobs?keyword=&page=1&anchorName=jobsList)
- [小红书](https://job.xiaohongshu.com/campus/position?campusRecruitTypes=term_intern%2Cterm_regular&positionName=&jobTypes=tech)
- [滴滴](https://app.mokahr.com/apply/didiglobal/6222#/jobs?zhineng=48460)
- [哈啰](https://careers.hellobike.com/#/recruit/%E5%AE%9E%E4%B9%A0%E7%94%9F%E6%8B%9B%E8%81%98)

---

##  快速开始（超详细教程）

### 第一步：安装Python

1. 打开浏览器，访问 https://www.python.org/downloads/
2. 点击 **"Download Python 3.x.x"** 下载最新版Python
3. 运行下载的安装程序
4. **重要！** 勾选  **"Add Python to PATH"**（添加到环境变量）
5. 点击 **"Install Now"** 开始安装
6. 安装完成后点击 **"Close"**

**验证安装是否成功：**
1. 按 `Win + R` 打开运行对话框
2. 输入 `cmd` 并回车，打开命令提示符
3. 输入 `python --version` 并回车
4. 如果显示 `Python 3.x.x` 则安装成功

---

### 第二步：首次运行

1. 双击 **`启动监控.bat`** 文件
2. 首次运行会自动：
   - 创建虚拟环境
   - 安装所需依赖（需要联网）
3. 等待安装完成（大约1-3分钟）

---

### 第三步：测试邮件是否正常

1. 双击 **`发送测试邮件.bat`** 文件
2. 如果显示"测试邮件发送成功"，去QQ邮箱查看是否收到邮件
3. 如果发送失败，请检查邮箱配置（见下方配置说明）

---

### 第四步：开始监控

1. 双击 **`启动监控.bat`** 文件
2. 程序会在后台运行，到了设定时间（13:00 和 19:00）自动检查
3. 如果发现新岗位，会自动发送邮件通知
4. 按 `Ctrl + C` 可以停止程序

---

## ⚙️ 配置说明

### 邮箱配置

编辑 `config/email_config.yaml` 文件：

```yaml
email:
  smtp_server: "smtp.qq.com"
  smtp_port: 465
  use_ssl: true
  
  # 发件人（你的QQ邮箱）
  sender_email: "你的QQ号@qq.com"
  sender_password: "你的授权码"  # 不是QQ密码！
  
  # 收件人（接收通知的邮箱）
  receiver_email: "你的QQ号@qq.com"
```

**如何获取QQ邮箱授权码：**
1. 登录 QQ邮箱 (mail.qq.com)
2. 点击顶部 **"设置"**
3. 点击 **"账户"** 标签
4. 向下滚动找到 **"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"**
5. 点击 **"开启"** 旁边的 **"生成授权码"**
6. 用手机发送短信验证
7. 复制生成的授权码到配置文件

---

### 监控时间配置

编辑 `config/settings.yaml` 文件：

```yaml
schedule:
  # 定时检查时间（24小时制）
  check_times:
    - hour: 13    # 下午1点检查
      minute: 0
    - hour: 19    # 晚上7点检查
      minute: 0
  
  # 检查间隔（分钟）
  check_interval_minutes: 5
  
  # 单次检查超时时间（秒）
  request_timeout: 30
```

---

### 爬虫配置

编辑 `config/settings.yaml` 文件：

```yaml
spider:
  # 是否使用代理
  use_proxy: false
  
  # 请求间隔（秒）- 每个公司之间的请求间隔
  request_delay_min: 2
  request_delay_max: 5
  
  # 最大重试次数
  max_retries: 3
  
  # 是否只爬取匹配关键词的岗位
  filter_by_keywords: true
```

---

### 浏览器配置（Selenium）

如果需要爬取动态页面（`requires_selenium: true`），需要配置Chrome浏览器路径。

编辑 `core/spider.py` 文件中的 `chrome_paths` 列表：

```python
chrome_paths = [
    r"C:\Users\你的用户名\AppData\Local\GptChrome\GptBrowser.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
```

**说明：**
- 程序会按顺序查找可用的Chrome浏览器
- 如果使用默认Chrome安装路径，通常无需修改
- 如果使用自定义浏览器（如GptChrome），需要添加对应路径

---

### 公司配置

编辑 `config/companies.yaml` 文件：

```yaml
companies:
  - name: "腾讯"                    # 公司名称
    url: "https://..."              # 招聘页面URL
    job_selector: ".job-item"       # 岗位列表CSS选择器
    title_selector: ".job-title"    # 标题CSS选择器
    url_selector: "a"               # 链接CSS选择器
    requires_selenium: false        # 是否需要Selenium（动态页面设为true）
    enabled: true                   # 是否启用
    keywords:[]                       # 关键词过滤
```

**说明：**
- `enabled: false` 可以临时禁用某个公司
- `keywords` 只有标题包含这些关键词的岗位才会被记录
- CSS选择器需要根据实际网页结构调整

---

## 📁 文件说明

```
JobMonitorSystem/
├── 启动获取.bat              # 启动定时监控（主程序）
├── 定时获取.bat              # 定时执行检查
├── 发送测试邮件.bat          # 测试邮件功能
├── main.py                  # Python主程序
├── requirements.txt         # Python依赖列表
├── config/                  # 配置文件目录
│   ├── __init__.py          # 配置模块初始化
│   ├── companies.yaml       # 公司配置
│   ├── email_config.yaml    # 邮箱配置
│   ├── settings.yaml        # 系统设置
│   └── proxy_list.txt       # 代理列表
├── core/                    # 核心代码
│   ├── __init__.py          # 核心模块初始化
│   ├── database.py          # 数据库操作（SQLite存储岗位数据）
│   ├── notifier.py          # 邮件通知（SMTP发送）
│   ├── scheduler.py         # 定时调度（APScheduler）
│   └── spider.py            # 爬虫逻辑（requests + BeautifulSoup + Selenium）
├── utils/                   # 工具代码
│   ├── __init__.py          # 工具模块初始化
│   ├── anti_crawl.py        # 反爬虫策略
│   └── logger.py            # 日志工具
├── templates/               # 邮件模板
│   └── email_template.html  # 邮件HTML模板
├── data/                    # 数据库（自动创建）
│   └── jobs.db              # SQLite数据库
└── logs/                    # 日志文件（自动创建）
    └── job_monitor.log      # 运行日志
```

---

## ❓ 常见问题

### Q1: 提示"未检测到Python"
**解决方法：**
1. 确认已安装Python
2. 安装时是否勾选了"Add Python to PATH"
3. 如果没勾选，重新运行安装程序，选择"Modify"，勾选"Add to PATH"

### Q2: 邮件发送失败
**可能原因：**
1. 授权码错误 - 重新生成授权码
2. SMTP服务未开启 - 在QQ邮箱设置中开启SMTP服务
3. 网络问题 - 检查网络连接

### Q3: 爬取不到岗位
**可能原因：**
1. 网站结构变化 - CSS选择器需要更新
2. 需要Selenium - 将 `requires_selenium` 设为 `true`
3. 被反爬 - 等待一段时间后重试

### Q4: 如何添加新公司？
在 `config/companies.yaml` 中添加新的公司配置：
1. 打开目标公司招聘页面
2. 按F12打开开发者工具
3. 找到岗位列表的HTML结构
4. 确定CSS选择器
5. 添加到配置文件

---

## 🔧 进阶用法

### 命令行参数

```bash
# 启动定时监控
python main.py

# 立即执行一次检查
python main.py --once

# 发送测试邮件
python main.py --test

# 查看统计信息
python main.py --stats

# 查看配置信息
python main.py --config
```

### 让程序开机自启动

1. 按 `Win + R`，输入 `shell:startup`，回车
2. 这会打开"启动"文件夹
3. 将 `启动监控.bat` 的快捷方式拖到这个文件夹
4. 下次开机会自动运行

### 后台运行（不显示窗口）

创建一个 `后台启动.vbs` 文件：

```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "启动监控.bat" & Chr(34), 0
Set WshShell = Nothing
```

双击这个VBS文件即可后台运行。

---

## 免责声明

- 本工具仅供个人学习、技术研究使用，不对任何使用结果承担法律责任
- 请严格遵守各目标网站的服务条款（Terms of Service）与 robots.txt 规则
- 请合理设置访问频率，避免对目标网站造成过大压力或影响其正常服务
- 不得将本工具获取的数据用于任何形式的商业用途或非法用途
- 使用本工具进行的所有行为及其后果均由使用者本人承担，与本人无关
- 如目标网站对爬虫/自动访问有禁止性规定，请立即停止对该网站的所有访问

---

## 提示

如果遇到任何问题，可以查看 `logs/job_monitor.log` 文件获取详细日志信息。
