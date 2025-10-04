"""全局日志工具"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


class Logger:
    """全局日志管理器"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """配置日志器"""
        # 创建 logger
        self._logger = logging.getLogger('amp-pool')
        self._logger.setLevel(logging.DEBUG)
        
        # 避免重复添加 handler
        if self._logger.handlers:
            return
        
        # 日志格式
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台 handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # 文件 handler（自动轮转）
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"app.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        # 错误日志单独文件
        error_log_file = log_dir / f"error.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self._logger.addHandler(error_handler)
    
    def debug(self, msg, *args, **kwargs):
        """调试日志"""
        self._logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """信息日志"""
        self._logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """警告日志"""
        self._logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """错误日志"""
        self._logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """严重错误日志"""
        self._logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        """异常日志（自动记录堆栈）"""
        self._logger.exception(msg, *args, **kwargs)


# 创建全局 logger 实例
logger = Logger()


# 便捷函数
def debug(msg, *args, **kwargs):
    """调试日志"""
    logger.debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """信息日志"""
    logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """警告日志"""
    logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """错误日志"""
    logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """严重错误日志"""
    logger.critical(msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    """异常日志（自动记录堆栈）"""
    logger.exception(msg, *args, **kwargs)

