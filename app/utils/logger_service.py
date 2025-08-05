import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Any, Optional, Dict, List
from logging.handlers import RotatingFileHandler

class LoggerService:
    """
    日志服务类
    提供不同级别的日志记录功能，以及结构化异常信息
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

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录调试信息
        """
        self.logger.debug(message, *args, **kwargs)

    def error(self, message: str, exc_info=None, *args: Any, **kwargs: Any) -> None:
        """
        记录错误信息，包含应用代码堆栈
        
        Args:
            message: 错误消息
            exc_info: 异常信息元组 (type, value, traceback)，如果为None则使用sys.exc_info()
        """
        if exc_info is None and sys.exc_info()[0] is not None:
            exc_info = sys.exc_info()
            
        # 如果有异常信息，记录应用代码堆栈
        if exc_info and exc_info[0] is not None:
            # 记录基本错误消息
            self.logger.error(f"{message}")
            
            # 获取应用代码堆栈
            location_info = self._get_error_location(exc_info[2])
            if location_info and location_info['stack']:
                self.logger.error("应用代码堆栈:")
                for frame in location_info['stack']:
                    self.logger.error(f"  → {frame['filename']}:{frame['lineno']} in {frame['function']}()")
        else:
            # 没有异常信息，只记录消息
            self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, exc_info=None, *args: Any, **kwargs: Any) -> None:
        """
        记录严重错误信息，并附带异常详情
        """
        if exc_info is None and sys.exc_info()[0] is not None:
            exc_info = sys.exc_info()
            
        if exc_info and exc_info[0] is not None:
            # 同error方法处理结构化异常信息
            self.logger.critical(f"{message}: {exc_info[0].__name__}: {str(exc_info[1])}")
            self.logger.critical("Traceback (most recent call last):")
            
            frames = self._get_stack_frames(exc_info[2])
            for frame in frames:
                self.logger.critical(f"  File \"{frame['filename']}\", line {frame['lineno']}, in {frame['function']}")
                
                if frame['context']:
                    for line in frame['context']:
                        self.logger.critical(f"    {line}")
        else:
            self.logger.critical(message, *args, **kwargs)
    
    def _get_stack_frames(self, tb) -> List[Dict[str, Any]]:
        """
        从traceback对象获取堆栈帧信息
        
        Args:
            tb: traceback对象
            
        Returns:
            包含文件名、行号、函数名和源码上下文的堆栈帧列表
        """
        frames = []
        
        while tb:
            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            function = frame.f_code.co_name
            lineno = tb.tb_lineno
            
            # 获取源码上下文
            context_lines = []
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                    # 获取出错行前后各2行
                    start = max(0, lineno - 3)
                    end = min(len(lines), lineno + 2)
                    
                    for i in range(start, end):
                        if i + 1 == lineno:
                            # 出错行添加箭头标记
                            prefix = "→ "
                        else:
                            prefix = "  "
                        # 添加行号和代码行
                        context_lines.append(f"{prefix}{i+1}: {lines[i].rstrip()}")
            except:
                context_lines = ["无法获取源代码上下文"]
            
            # 保存帧信息，使用简短文件名
            frames.append({
                'filename': os.path.basename(filename),
                'function': function,
                'lineno': lineno,
                'context': context_lines
            })
            
            tb = tb.tb_next
        
        return frames
    
    def _get_error_location(self, tb) -> Dict[str, Any]:
        """
        获取应用代码的堆栈信息
        
        Args:
            tb: traceback对象
            
        Returns:
            包含应用代码堆栈的字典
        """
        app_stack = []
        
        while tb:
            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            function = frame.f_code.co_name
            lineno = tb.tb_lineno
            
            # 只保留应用代码，跳过框架代码
            if not self._is_framework_code(filename):
                app_stack.append({
                    'filename': os.path.basename(filename),
                    'function': function,
                    'lineno': lineno
                })
            
            tb = tb.tb_next
        
        return {'stack': app_stack}


    def _is_framework_code(self, filename: str) -> bool:
        """
        检查是否为框架内部代码
        
        Args:
            filename: 文件路径
            
        Returns:
            如果是框架代码返回True，否则返回False
        """
        # 跳过明确的第三方包路径和中间件
        skip_paths = [
            "site-packages",
            "dist-packages",
            "/usr/lib/python",
            "lib/python",
            "/Library/Frameworks/Python.framework",
            "error_handler.py",  # 跳过错误处理中间件
            "/middleware/"
        ]
        return any(path in filename for path in skip_paths)
    
    
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
                 error_message: str, exc_info=None, user_id: Optional[str] = None) -> None:
        """
        记录API错误信息，包含结构化异常堆栈
        """
        message = f"API Error - {method} {path} - Status: {status_code} - Error: {error_message}"
        if user_id:
            message += f" - User: {user_id}"
        self.error(message, exc_info=exc_info)

# 创建全局日志实例
logger = LoggerService() 