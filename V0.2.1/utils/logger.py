import logging
import os
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any, List
import json

class LogFilter:
    def __init__(self, level: int = logging.NOTSET, **kwargs):
        self.level = level
        self.filters = kwargs
    
    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < self.level:
            return False
        
        for key, value in self.filters.items():
            if hasattr(record, key) and getattr(record, key) != value:
                return False
        return True

class JsonFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.extra_fields = kwargs
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.module,
            "line": record.lineno,
            "message": record.getMessage()
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        for key, value in self.extra_fields.items():
            if callable(value):
                log_data[key] = value()
            else:
                log_data[key] = value
        
        # 添加record的额外属性
        for key, value in record.__dict__.items():
            if key not in ["args", "exc_info", "exc_text", "msg", "message"]:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 创建主日志记录器
        self.logger = logging.getLogger('BedTools')
        self.logger.setLevel(logging.DEBUG)
        
        # 清除现有的处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 创建文件处理器 - 按大小轮转
        main_log = os.path.join(self.log_dir, 'bedtools.log')
        file_handler = RotatingFileHandler(
            main_log,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 创建每日轮转的文件处理器
        daily_log = os.path.join(self.log_dir, 'bedtools_daily.log')
        daily_handler = TimedRotatingFileHandler(
            daily_log,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        daily_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式化器
        standard_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] - %(message)s'
        )
        json_formatter = JsonFormatter(
            app_name="BedTools",
            app_version="1.0.0",
            environment=os.getenv("ENV", "development")
        )
        
        # 应用格式化器
        file_handler.setFormatter(json_formatter)
        daily_handler.setFormatter(standard_formatter)
        console_handler.setFormatter(standard_formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(daily_handler)
        self.logger.addHandler(console_handler)
        
        # 初始化过滤器
        self.filters: Dict[str, LogFilter] = {}
    
    def add_filter(self, name: str, level: int = logging.NOTSET, **kwargs):
        """添加日志过滤器"""
        filter_obj = LogFilter(level, **kwargs)
        self.filters[name] = filter_obj
        for handler in self.logger.handlers:
            handler.addFilter(filter_obj)
    
    def remove_filter(self, name: str):
        """移除日志过滤器"""
        if name in self.filters:
            filter_obj = self.filters[name]
            for handler in self.logger.handlers:
                handler.removeFilter(filter_obj)
            del self.filters[name]
    
    @classmethod
    def get_logger(cls) -> logging.Logger:
        return cls().logger
    
    def log_operation(self, operation: str, status: bool, details: Optional[str] = None):
        """记录操作日志"""
        level = logging.INFO if status else logging.ERROR
        message = f"操作: {operation} - 状态: {'成功' if status else '失败'}"
        if details:
            message += f" - 详情: {details}"
        extra = {
            "operation_type": operation,
            "status": status,
            "details": details
        }
        self.logger.log(level, message, extra=extra)
    
    def log_security(self, event_type: str, description: str, severity: str = "INFO"):
        """记录安全事件"""
        level = getattr(logging, severity.upper(), logging.INFO)
        extra = {
            "event_type": event_type,
            "severity": severity
        }
        self.logger.log(level, f"安全事件 [{event_type}] - {description}", extra=extra)
    
    def log_error(self, error: Exception, context: Optional[str] = None):
        """记录错误信息"""
        message = f"错误: {str(error)}"
        if context:
            message = f"{context} - {message}"
        extra = {
            "error_type": error.__class__.__name__,
            "context": context
        }
        self.logger.error(message, exc_info=True, extra=extra)
    
    def log_plugin(self, plugin_name: str, action: str, status: bool, details: Optional[str] = None):
        """记录插件相关日志"""
        level = logging.INFO if status else logging.ERROR
        message = f"插件 [{plugin_name}] {action} - 状态: {'成功' if status else '失败'}"
        if details:
            message += f" - 详情: {details}"
        extra = {
            "plugin_name": plugin_name,
            "action": action,
            "status": status,
            "details": details
        }
        self.logger.log(level, message, extra=extra)
    
    def get_logs(self, 
                 level: int = logging.NOTSET,
                 start_time: Optional[float] = None,
                 end_time: Optional[float] = None,
                 **filters) -> List[Dict[str, Any]]:
        """获取符合条件的日志记录"""
        logs = []
        log_file = os.path.join(self.log_dir, 'bedtools.log')
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        if self._match_log_filters(log_entry, level, start_time, end_time, **filters):
                            logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
        
        return logs
    
    def _match_log_filters(self,
                          log_entry: Dict[str, Any],
                          level: int,
                          start_time: Optional[float],
                          end_time: Optional[float],
                          **filters) -> bool:
        """检查日志记录是否匹配过滤条件"""
        # 检查日志级别
        if level != logging.NOTSET:
            log_level = getattr(logging, log_entry.get("level", "NOTSET"))
            if log_level < level:
                return False
        
        # 检查时间范围
        log_time = datetime.strptime(log_entry["timestamp"], "%Y-%m-%d %H:%M:%S,%f").timestamp()
        if start_time and log_time < start_time:
            return False
        if end_time and log_time > end_time:
            return False
        
        # 检查其他过滤条件
        for key, value in filters.items():
            if key not in log_entry or log_entry[key] != value:
                return False
        
        return True 