# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于playwright的自动化学习程序
项目目标：实现目标网站的学习任务自动化

## 开发环境要求
- Python 3.13.5
- 自动化框架：Playwright
- 浏览器：Firefox（通过Playwright调用）
- 运行环境：Python venv虚拟环境
- 验证码识别：ddddocr（已验证高识别率）
- 数据存储：本地数据库（SQLite推荐）

## 项目基础信息
项目网站目标网址 https://edu.nxgbjy.org.cn/nxxzxy/index.html#/
必修课程列表（需要登陆） https://edu.nxgbjy.org.cn/nxxzxy/index.html#/study_center/tool_box/required?id=275 
必修课视频播放页面示例：https://edu.nxgbjy.org.cn/nxxzxy/index.html#/video_page?id=10598&name=%E5%AD%A6%E5%91%98%E4%B8%AD%E5%BF%83&user_course_id=1988340
选修课程列表（需要登陆） https://edu.nxgbjy.org.cn/nxxzxy/index.html#/study_center/my_study/my_elective_courses?active_menu=2
选修课视频播放页面示例： https://edu.nxgbjy.org.cn/nxxzxy/index.html#/video_page?id=11187&user_course_id=1991799&name=%E5%AD%A6%E4%B9%A0%E4%B8%AD%E5%BF%83
登陆信息：用户名：640302198607120020 密码：My2062660

## 项目运行逻辑
1.程序启动后进入主界面，同时检测登陆状态，如果登陆状态为假，则执行登陆程序
2.1用户选择“获取（更新）课程信息”
2.2程序根据已经提供的必修课程列表网址和选修课程列表网址，分析两个列表的内容，获取“课程信息”（课程信息包含课程名称、必修课/选修课、课程学习进度、课程视频播放网址）并将这些信息经用户确认无误后持久化存储在本地数据库中，随后返回主界面
3.1用户选择“开始自动学习”
3.2程序根据课程列表数据库的信息，选择进度非100%的的课程，进入视频播放页面进行学习（一次同时只能播放一个课程）


## 项目结构

建议的目录结构：
```
auto_study_advanced/
├── src/                    # 主要源代码
│   ├── main.py            # 主程序入口
│   ├── login.py           # 登录模块
│   ├── course_parser.py   # 课程信息解析
│   ├── auto_study.py      # 自动学习模块
│   ├── captcha_solver.py  # 验证码识别（ddddocr）
│   └── database.py        # 数据库操作
├── tests/                 # 测试文件
├── data/                  # 数据文件和数据库
├── config/                # 配置文件
├── venv/                  # Python虚拟环境
└── requirements.txt       # Python依赖
```

## 常用命令

### 环境设置
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install firefox
```

### 开发命令
```bash
# 运行主程序
python src/main.py

# 运行测试
python -m pytest tests/

# 安装新依赖后更新requirements.txt
pip freeze > requirements.txt
```

## 核心架构

### 主要模块
1. **主界面模块** (main.py) - 程序入口和用户交互
2. **登录模块** (login.py) - 处理登录逻辑和验证码识别
3. **课程解析模块** (course_parser.py) - 解析必修课和选修课列表
4. **自动学习模块** (auto_study.py) - 自动播放视频和学习进度管理
5. **数据库模块** (database.py) - 本地数据持久化

### 工作流程
1. 启动 → 检测登录状态 → 执行登录（如需要）
2. 获取课程信息 → 解析课程列表 → 存储到数据库
3. 自动学习 → 选择未完成课程 → 视频播放 → 更新进度

### 关键技术点
- Playwright Firefox 自动化控制
- ddddocr 验证码识别
- SQLite 本地数据存储
- 异步/多线程处理（如需要）

## 开发指南

- 使用中文进行交流和文档编写
- 遵循 Python PEP 8 代码规范
- 每个模块保持单一职责原则
- 使用异常处理确保程序稳定性
- 登录信息和敏感数据应从配置文件读取，不要硬编码
- 实现适当的错误重试机制
- 注意网页加载时间，使用显式等待

## 注意事项

- 项目包含真实登录凭据，需要妥善保护敏感信息
- 自动化操作需要遵守目标网站的使用条款
- 建议添加适当的延时以避免过于频繁的请求
- 验证码识别可能不是100%准确，需要错误处理机制