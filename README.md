# 自动化学习程序

基于Playwright的网页自动化学习系统，可以自动完成在线课程学习。

## 功能特性

- 自动登录（支持验证码识别）
- 课程信息获取和管理
- 自动视频播放和进度跟踪
- 学习记录和统计
- 友好的命令行界面

## 环境要求

- Python 3.8+
- Firefox浏览器（由Playwright控制）
- 网络连接

## 安装和设置

### 1. 创建虚拟环境

```bash
python3 -m venv venv
```

### 2. 激活虚拟环境

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装Playwright浏览器

```bash
playwright install firefox
```

## 运行程序

### 方法1: 使用启动脚本
```bash
python run.py
```

### 方法2: 直接运行主程序
```bash
python src/main.py
```

## 使用说明

1. **首次运行**: 程序会自动进行登录，如果验证码识别失败可能需要多试几次
2. **获取课程信息**: 选择菜单选项1，程序会解析所有必修课和选修课信息
3. **开始自动学习**: 选择菜单选项2，程序会自动播放视频并跟踪学习进度
4. **查看进度**: 可以随时查看课程列表和学习统计

## 注意事项

- 请合理使用，遵守网站使用条款
- 程序运行时请保持网络连接稳定
- 验证码识别有一定失败率，程序会自动重试
- 可以随时按Ctrl+C中断学习过程

## 目录结构

```
auto_study_advanced/
├── src/                    # 主要源代码
│   ├── main.py            # 主程序入口
│   ├── login.py           # 登录模块
│   ├── course_parser.py   # 课程信息解析
│   ├── auto_study.py      # 自动学习模块
│   ├── captcha_solver.py  # 验证码识别
│   └── database.py        # 数据库操作
├── config/                # 配置文件
├── data/                  # 数据文件和数据库
├── venv/                  # Python虚拟环境
├── requirements.txt       # Python依赖
└── run.py                 # 启动脚本
```

## 故障排除

### 常见问题

1. **导入错误**: 确保虚拟环境已激活且依赖已安装
2. **浏览器启动失败**: 确保已运行 `playwright install firefox`
3. **登录失败**: 检查网络连接和登录凭据
4. **验证码识别失败**: 程序会自动重试，通常几次后会成功

### 日志文件

程序运行日志保存在 `data/auto_study.log`，可以查看详细的错误信息。