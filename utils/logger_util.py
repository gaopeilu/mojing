import logging
from datetime import datetime
from utils.path_util import get_project_abs_path
import os

# 日志保存的根目录
LOG_ROOT = get_project_abs_path("logs")    # 只是创建一个路径
# 确保日志目录的存在  不存在就创建
os.makedirs(LOG_ROOT, exist_ok=True)    # 该路径不存在的话就创建文件夹 存在就不创建 makedirs 是创建多级目录
# 日志的格式配置 时间 名字 级别 触发日志的文件名 行数 日志信息
DEFAULT_LOG_FORMAT = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)


def get_logger(
        name: str = "agent",
        console_level: int = logging.INFO,  # 日志级别 控制台
        file_level: int = logging.DEBUG,   # 日志级别 文件
        log_file=None,    # 日志文件名字
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(console_handler)
    if not log_file:
        log_file = os.path.join(LOG_ROOT, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(file_handler)
    return logger


logger = get_logger()


if __name__ == '__main__':
    logger.info("hello world")
    logger.error("hello world")
    logger.debug("hello world")
    logger.warning("hello world")

