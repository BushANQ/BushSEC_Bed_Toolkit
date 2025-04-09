from typing import Optional, Callable, Any, Dict, List
from functools import wraps
import traceback
import time
from datetime import datetime
from .logger import Logger

class ErrorCode:
    """错误代码枚举"""
    UNKNOWN = "ERR_UNKNOWN"
    VALIDATION = "ERR_VALIDATION"
    SECURITY = "ERR_SECURITY"
    PLUGIN = "ERR_PLUGIN"
    OPERATION = "ERR_OPERATION"
    CONFIGURATION = "ERR_CONFIG"
    NETWORK = "ERR_NETWORK"
    DATABASE = "ERR_DATABASE"
    PERMISSION = "ERR_PERMISSION"
    RESOURCE = "ERR_RESOURCE"

class ErrorSeverity:
    """错误严重程度枚举"""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

class ErrorCategory:
    """错误类别枚举"""
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    BUSINESS = "BUSINESS"
    VALIDATION = "VALIDATION"
    PLUGIN = "PLUGIN"
    NETWORK = "NETWORK"
    DATABASE = "DATABASE"
    UI = "UI"

class BedToolsError(Exception):
    """基础异常类"""
    def __init__(self, 
                 message: str, 
                 error_code: str = ErrorCode.UNKNOWN,
                 severity: str = ErrorSeverity.ERROR,
                 category: str = ErrorCategory.SYSTEM,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.severity = severity
        self.category = category
        self.details = details or {}
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()

class ValidationError(BedToolsError):
    """验证错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            error_code=ErrorCode.VALIDATION,
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.VALIDATION,
            details=details
        )

class SecurityError(BedToolsError):
    """安全相关错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            error_code=ErrorCode.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SECURITY,
            details=details
        )

class PluginError(BedToolsError):
    """插件相关错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            error_code=ErrorCode.PLUGIN,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.PLUGIN,
            details=details
        )

class OperationError(BedToolsError):
    """操作错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            error_code=ErrorCode.OPERATION,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.BUSINESS,
            details=details
        )

class ErrorStats:
    """错误统计"""
    def __init__(self):
        self.total_errors = 0
        self.errors_by_code: Dict[str, int] = {}
        self.errors_by_severity: Dict[str, int] = {}
        self.errors_by_category: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.last_error_time: Optional[datetime] = None
    
    def record_error(self, error: BedToolsError):
        """记录错误统计"""
        self.total_errors += 1
        self.errors_by_code[error.error_code] = self.errors_by_code.get(error.error_code, 0) + 1
        self.errors_by_severity[error.severity] = self.errors_by_severity.get(error.severity, 0) + 1
        self.errors_by_category[error.category] = self.errors_by_category.get(error.category, 0) + 1
        
        error_info = {
            "timestamp": error.timestamp,
            "error_code": error.error_code,
            "severity": error.severity,
            "category": error.category,
            "message": str(error),
            "details": error.details,
            "traceback": error.traceback
        }
        self.error_history.append(error_info)
        self.last_error_time = error.timestamp
        
        # 保持历史记录在合理范围内
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return {
            "total_errors": self.total_errors,
            "errors_by_code": self.errors_by_code,
            "errors_by_severity": self.errors_by_severity,
            "errors_by_category": self.errors_by_category,
            "last_error_time": self.last_error_time
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的错误记录"""
        return self.error_history[-limit:]
    
    def clear_stats(self):
        """清除统计信息"""
        self.__init__()

class ErrorRecoveryStrategy:
    """错误恢复策略"""
    def __init__(self):
        self.recovery_handlers: Dict[str, Callable] = {}
    
    def register_handler(self, error_code: str, handler: Callable):
        """注册错误恢复处理器"""
        self.recovery_handlers[error_code] = handler
    
    def try_recover(self, error: BedToolsError) -> bool:
        """尝试恢复错误"""
        handler = self.recovery_handlers.get(error.error_code)
        if handler:
            try:
                handler(error)
                return True
            except Exception:
                return False
        return False

class ErrorHandler:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.logger = Logger()
        self.error_handlers: Dict[str, Callable] = {}
        self.error_stats = ErrorStats()
        self.recovery_strategy = ErrorRecoveryStrategy()
        self._register_default_handlers()
        self._register_default_recovery_handlers()
    
    def _register_default_handlers(self):
        """注册默认的错误处理器"""
        self.register_handler("ValidationError", self._handle_validation_error)
        self.register_handler("SecurityError", self._handle_security_error)
        self.register_handler("PluginError", self._handle_plugin_error)
        self.register_handler("OperationError", self._handle_operation_error)
    
    def _register_default_recovery_handlers(self):
        """注册默认的错误恢复处理器"""
        self.recovery_strategy.register_handler(
            ErrorCode.VALIDATION,
            lambda error: None  # 验证错误通常需要用户修正，无自动恢复
        )
        self.recovery_strategy.register_handler(
            ErrorCode.PLUGIN,
            lambda error: self._try_reload_plugin(error)
        )
        # 可以添加更多默认恢复处理器
    
    def register_handler(self, error_type: str, handler: Callable):
        """注册错误处理器"""
        self.error_handlers[error_type] = handler
    
    def handle_error(self, error: Exception, context: Optional[str] = None) -> Any:
        """处理错误"""
        # 如果是自定义错误类型，记录统计信息
        if isinstance(error, BedToolsError):
            self.error_stats.record_error(error)
            
            # 尝试自动恢复
            if self.recovery_strategy.try_recover(error):
                self.logger.log_operation(
                    "error_recovery",
                    True,
                    f"成功恢复错误: {error.error_code}"
                )
        
        error_type = error.__class__.__name__
        handler = self.error_handlers.get(error_type, self._handle_default_error)
        return handler(error, context)
    
    def _handle_validation_error(self, error: ValidationError, context: Optional[str] = None):
        """处理验证错误"""
        self.logger.log_error(error, f"验证错误 - {context if context else ''}")
        return {
            "status": "error",
            "error_code": error.error_code,
            "message": str(error),
            "type": "validation",
            "severity": error.severity,
            "category": error.category,
            "details": error.details,
            "timestamp": error.timestamp.isoformat()
        }
    
    def _handle_security_error(self, error: SecurityError, context: Optional[str] = None):
        """处理安全错误"""
        self.logger.log_security("ERROR", str(error), "CRITICAL")
        return {
            "status": "error",
            "error_code": error.error_code,
            "message": str(error),
            "type": "security",
            "severity": error.severity,
            "category": error.category,
            "details": error.details,
            "timestamp": error.timestamp.isoformat()
        }
    
    def _handle_plugin_error(self, error: PluginError, context: Optional[str] = None):
        """处理插件错误"""
        self.logger.log_plugin("Unknown", "error", False, str(error))
        return {
            "status": "error",
            "error_code": error.error_code,
            "message": str(error),
            "type": "plugin",
            "severity": error.severity,
            "category": error.category,
            "details": error.details,
            "timestamp": error.timestamp.isoformat()
        }
    
    def _handle_operation_error(self, error: OperationError, context: Optional[str] = None):
        """处理操作错误"""
        self.logger.log_operation("Unknown", False, str(error))
        return {
            "status": "error",
            "error_code": error.error_code,
            "message": str(error),
            "type": "operation",
            "severity": error.severity,
            "category": error.category,
            "details": error.details,
            "timestamp": error.timestamp.isoformat()
        }
    
    def _handle_default_error(self, error: Exception, context: Optional[str] = None):
        """处理默认错误"""
        self.logger.log_error(error, context)
        return {
            "status": "error",
            "error_code": ErrorCode.UNKNOWN,
            "message": str(error),
            "type": "unknown",
            "severity": ErrorSeverity.ERROR,
            "category": ErrorCategory.SYSTEM,
            "traceback": traceback.format_exc(),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
    
    def _try_reload_plugin(self, error: PluginError) -> bool:
        """尝试重新加载插件"""
        try:
            plugin_name = error.details.get("plugin_name")
            if plugin_name:
                from ..plugins.plugin_manager import PluginManager
                plugin_manager = PluginManager()
                return plugin_manager.reload_plugin(plugin_name)
        except Exception:
            return False
        return False
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return self.error_stats.get_stats()
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的错误记录"""
        return self.error_stats.get_recent_errors(limit)
    
    def clear_error_stats(self):
        """清除错误统计信息"""
        self.error_stats.clear_stats()

def error_handler(func: Callable) -> Callable:
    """错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handler = ErrorHandler()
            return handler.handle_error(e, func.__name__)
    return wrapper 