from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Set
from enum import Enum
import time
from ..utils.error_handler import error_handler, OperationError
from ..utils.logger import Logger
from ..config.config_manager import ConfigManager

class ToolStatus(Enum):
    """工具状态枚举"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    CLEANING = "cleaning"
    CLEANED = "cleaned"

class ProgressInfo:
    """进度信息"""
    def __init__(self):
        self.current: int = 0
        self.total: int = 0
        self.message: str = ""
        self.details: Dict[str, Any] = {}
        self.start_time: float = 0
        self.last_update_time: float = 0
    
    def update(self, current: int, total: int, message: str = "", **details):
        """更新进度信息"""
        self.current = current
        self.total = total
        self.message = message
        self.details.update(details)
        self.last_update_time = time.time()
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.last_update_time = self.start_time
    
    def get_progress(self) -> Dict[str, Any]:
        """获取进度信息"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        percentage = (self.current / self.total * 100) if self.total > 0 else 0
        
        return {
            "current": self.current,
            "total": self.total,
            "percentage": percentage,
            "message": self.message,
            "details": self.details,
            "elapsed_time": elapsed,
            "estimated_remaining": (elapsed / percentage * (100 - percentage)) if percentage > 0 else 0
        }

class ResourceUsage:
    """资源使用情况"""
    def __init__(self):
        self.memory_usage: int = 0
        self.cpu_usage: float = 0
        self.disk_usage: int = 0
        self.network_usage: int = 0
        self.start_time: float = 0
        self.last_update_time: float = 0
    
    def update(self, memory: int, cpu: float, disk: int, network: int):
        """更新资源使用情况"""
        self.memory_usage = memory
        self.cpu_usage = cpu
        self.disk_usage = disk
        self.network_usage = network
        self.last_update_time = time.time()
    
    def get_usage(self) -> Dict[str, Any]:
        """获取资源使用情况"""
        return {
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "disk_usage": self.disk_usage,
            "network_usage": self.network_usage,
            "last_update": self.last_update_time
        }

class ToolBase(ABC):
    """工具基类"""
    
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigManager()
        self.status = ToolStatus.UNINITIALIZED
        self.progress = ProgressInfo()
        self.resource_usage = ResourceUsage()
        self.dependencies: Set[str] = set()
        self.required_permissions: Set[str] = set()
        self.config_schema: Dict[str, Any] = {}
        self._error: Optional[Exception] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """工具版本"""
        pass
    
    @property
    def error(self) -> Optional[Exception]:
        """获取最后一次错误"""
        return self._error
    
    @error_handler
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """初始化工具"""
        try:
            self.status = ToolStatus.INITIALIZING
            
            # 验证配置
            if config:
                if not self.validate_config(config):
                    raise OperationError("配置验证失败")
                self.config = config
            
            # 检查依赖
            self._check_dependencies()
            
            # 检查权限
            self._check_permissions()
            
            # 执行具体的初始化逻辑
            result = self._initialize()
            
            if result:
                self.status = ToolStatus.READY
            else:
                self.status = ToolStatus.ERROR
                
            return result
            
        except Exception as e:
            self.status = ToolStatus.ERROR
            self._error = e
            raise
    
    @abstractmethod
    def _initialize(self) -> bool:
        """具体的初始化逻辑"""
        pass
    
    @error_handler
    def cleanup(self):
        """清理工具资源"""
        try:
            self.status = ToolStatus.CLEANING
            self._cleanup()
            self.status = ToolStatus.CLEANED
        except Exception as e:
            self.status = ToolStatus.ERROR
            self._error = e
            raise
    
    @abstractmethod
    def _cleanup(self):
        """具体的清理逻辑"""
        pass
    
    @error_handler
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        if not self.config_schema:
            return True
            
        try:
            self._validate_config_schema(config, self.config_schema)
            return True
        except Exception as e:
            self._error = e
            return False
    
    def _validate_config_schema(self, config: Dict[str, Any], schema: Dict[str, Any]):
        """递归验证配置schema"""
        for key, value_schema in schema.items():
            if key not in config:
                if value_schema.get("required", True):
                    raise OperationError(f"缺少必需的配置项: {key}")
                continue
            
            value = config[key]
            if isinstance(value_schema, dict):
                if "type" in value_schema:
                    self._validate_type(value, value_schema["type"], key)
                if "values" in value_schema:
                    self._validate_values(value, value_schema["values"], key)
                if "schema" in value_schema:
                    self._validate_config_schema(value, value_schema["schema"])
    
    def _validate_type(self, value: Any, expected_type: str, key: str):
        """验证值类型"""
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict
        }
        if not isinstance(value, type_map.get(expected_type, object)):
            raise OperationError(f"配置项 {key} 类型错误，期望 {expected_type}")
    
    def _validate_values(self, value: Any, valid_values: List[Any], key: str):
        """验证值范围"""
        if value not in valid_values:
            raise OperationError(f"配置项 {key} 的值必须是以下之一: {valid_values}")
    
    @error_handler
    def execute(self, *args, **kwargs) -> Any:
        """执行工具功能"""
        if self.status != ToolStatus.READY:
            raise OperationError(f"工具 {self.name} 状态不正确: {self.status}")
            
        try:
            self.status = ToolStatus.RUNNING
            self.progress.start()
            
            result = self._execute(*args, **kwargs)
            
            self.status = ToolStatus.READY
            return result
            
        except Exception as e:
            self.status = ToolStatus.ERROR
            self._error = e
            raise
    
    @abstractmethod
    def _execute(self, *args, **kwargs) -> Any:
        """实际的工具执行逻辑"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取工具状态"""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "progress": self.progress.get_progress(),
            "resource_usage": self.resource_usage.get_usage(),
            "error": str(self._error) if self._error else None
        }
    
    def update_progress(self, current: int, total: int, message: str = "", **details):
        """更新进度信息"""
        self.progress.update(current, total, message, **details)
    
    def update_resource_usage(self, memory: int, cpu: float, disk: int, network: int):
        """更新资源使用情况"""
        self.resource_usage.update(memory, cpu, disk, network)
    
    def _check_dependencies(self):
        """检查依赖"""
        for dep in self.dependencies:
            if not self._check_dependency(dep):
                raise OperationError(f"缺少依赖: {dep}")
    
    def _check_dependency(self, dependency: str) -> bool:
        """检查单个依赖"""
        try:
            __import__(dependency)
            return True
        except ImportError:
            return False
    
    def _check_permissions(self):
        """检查权限"""
        for perm in self.required_permissions:
            if not self._check_permission(perm):
                raise OperationError(f"缺少权限: {perm}")
    
    def _check_permission(self, permission: str) -> bool:
        """检查单个权限"""
        # 这里实现具体的权限检查逻辑
        return True
    
    def pause(self):
        """暂停工具执行"""
        if self.status == ToolStatus.RUNNING:
            self.status = ToolStatus.PAUSED
    
    def resume(self):
        """恢复工具执行"""
        if self.status == ToolStatus.PAUSED:
            self.status = ToolStatus.RUNNING
    
    def reset(self):
        """重置工具状态"""
        self.status = ToolStatus.UNINITIALIZED
        self.progress = ProgressInfo()
        self.resource_usage = ResourceUsage()
        self._error = None 