# 配置文件
class Config:
    # 网站相关配置
    BASE_URL = "https://edu.nxgbjy.org.cn/nxxzxy/index.html#/"
    # 学习中心相关URL
    STUDY_CENTER_URL = "https://edu.nxgbjy.org.cn/nxxzxy/index.html#/study_center"
    # 必修课程通过"进入班级"链接访问，选修课通过"本年选修"链接访问
    REQUIRED_COURSES_URL = "https://edu.nxgbjy.org.cn/nxxzxy/index.html#/study_center/tool_box/required?id=275"  
    ELECTIVE_COURSES_URL = "https://edu.nxgbjy.org.cn/nxxzxy/index.html#/study_center/my_study/my_elective_courses?active_menu=2"
    
    # 登录信息（生产环境应从环境变量读取）
    USERNAME = "640302198607120020"
    PASSWORD = "My2062660"
    
    # 数据库配置
    DATABASE_PATH = "data/courses.db"
    
    # 浏览器配置
    BROWSER_TYPE = "firefox"
    HEADLESS = False  # 设为True可无头运行
    DEBUG_MODE = True  # 调试模式，显示更多信息
    
    # 浏览器窗口大小配置
    VIEWPORT_WIDTH = 1440
    VIEWPORT_HEIGHT = 900
    
    # 延时配置（毫秒）
    PAGE_LOAD_TIMEOUT = 30000
    ELEMENT_WAIT_TIMEOUT = 10000
    VIDEO_CHECK_INTERVAL = 5000  # 视频进度检查间隔
    
    # 验证码相关
    CAPTCHA_MAX_RETRIES = 3