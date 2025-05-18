import logging
import os
from datetime import datetime
from typing import Any, Optional
from logging.handlers import RotatingFileHandler

class LoggerService:
    """
    日志服务类
    提供不同级别的日志记录功能
    """
    def __init__(self, name: str = "app", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.propagate = False  # 防止日志向上传播
        self.logger.setLevel(logging.DEBUG)
        
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器 - 按日期分割
        today = datetime.now().strftime('%Y-%m-%d')
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, f'app_{today}.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 错误日志文件处理器
        error_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, f'error_{today}.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录调试信息
        """
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录一般信息
        """
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录警告信息
        """
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录错误信息
        """
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录严重错误信息
        """
        self.logger.critical(message, *args, **kwargs)
    
    def api_request(self, method: str, path: str, status_code: int, 
                   response_time: float, user_id: Optional[str] = None) -> None:
        """
        记录API请求信息
        """
        message = f"API Request - {method} {path} - Status: {status_code} - Time: {response_time:.2f}ms"
        if user_id:
            message += f" - User: {user_id}"
        self.info(message)

    def api_error(self, method: str, path: str, status_code: int, 
                 error_message: str, user_id: Optional[str] = None) -> None:
        """
        记录API错误信息
        """
        message = f"API Error - {method} {path} - Status: {status_code} - Error: {error_message}"
        if user_id:
            message += f" - User: {user_id}"
        self.error(message)

# 创建全局日志实例
logger = LoggerService() 