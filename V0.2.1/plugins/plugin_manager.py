import os
import sys
import importlib
import inspect
import json
import time
from typing import Dict, List, Type, Any, Optional, Set
from abc import ABC, abstractmethod
from ..utils.error_handler import error_handler, PluginError
from ..utils.logger import Logger
from ..config.config_manager import ConfigManager

class PluginMetadata:
    def __init__(self, data: Dict[str, Any]):
        self.name = data["name"]
        self.version = data["version"]
        self.description = data["description"]
        self.author = data.get("author", "Unknown")
        self.dependencies = data.get("dependencies", {})
        self.required_version = data.get("required_version", "1.0.0")
        self.load_order = data.get("load_order", 100)
        self.enabled = data.get("enabled", True)

class PluginBase(ABC):
    """插件基类"""
    
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigManager()
        self._metadata: Optional[PluginMetadata] = None
        self._initialized = False
    
    @property
    def metadata(self) -> PluginMetadata:
        if not self._metadata:
            raise PluginError("插件元数据未加载")
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: PluginMetadata):
        self._metadata = value
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理插件资源"""
        pass
    
    @property
    def name(self) -> str:
        return self.metadata.name
    
    @property
    def version(self) -> str:
        return self.metadata.version
    
    @property
    def description(self) -> str:
        return self.metadata.description
    
    def get_status(self) -> Dict[str, Any]:
        """获取插件状态"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "initialized": self._initialized,
            "author": self.metadata.author,
            "dependencies": self.metadata.dependencies,
            "load_order": self.metadata.load_order,
            "enabled": self.metadata.enabled
        }

class PluginManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.logger = Logger()
        self.config = ConfigManager()
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_dir = os.path.dirname(__file__)
        self.metadata_cache: Dict[str, PluginMetadata] = {}
        self.file_watchers: Dict[str, float] = {}
        self.disabled_plugins: Set[str] = set()
        
        # 添加插件目录到Python路径
        if self.plugin_dir not in sys.path:
            sys.path.append(self.plugin_dir)
    
    @error_handler
    def discover_plugins(self) -> List[str]:
        """发现可用的插件"""
        plugin_files = []
        for item in os.listdir(self.plugin_dir):
            if item.endswith('.py') and item != '__init__.py':
                metadata_file = os.path.join(self.plugin_dir, f"{item[:-3]}.json")
                if os.path.exists(metadata_file):
                    plugin_files.append(item[:-3])
        return plugin_files
    
    @error_handler
    def load_plugin(self, plugin_name: str) -> bool:
        """加载指定的插件"""
        if plugin_name in self.disabled_plugins:
            return False
            
        try:
            # 加载插件元数据
            metadata = self._load_plugin_metadata(plugin_name)
            if not metadata.enabled:
                self.disabled_plugins.add(plugin_name)
                return False
            
            # 检查版本兼容性
            if not self._check_version_compatibility(metadata.required_version):
                raise PluginError(f"插件 {plugin_name} 需要版本 {metadata.required_version}")
            
            # 检查并加载依赖
            self._load_dependencies(metadata.dependencies)
            
            # 导入插件模块
            module = importlib.import_module(plugin_name)
            
            # 如果是重新加载，先重新加载模块
            if plugin_name in self.plugins:
                module = importlib.reload(module)
            
            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginBase) and 
                    obj != PluginBase):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                raise PluginError(f"插件 {plugin_name} 中未找到有效的插件类")
            
            # 实例化插件
            plugin = plugin_class()
            plugin.metadata = metadata
            
            # 初始化插件
            if plugin.initialize():
                plugin._initialized = True
                self.plugins[plugin.name] = plugin
                self.metadata_cache[plugin.name] = metadata
                self._update_file_watcher(plugin_name)
                self.logger.log_plugin(plugin.name, "load", True)
                return True
            
            return False
            
        except Exception as e:
            self.logger.log_plugin(plugin_name, "load", False, str(e))
            raise PluginError(f"加载插件 {plugin_name} 失败: {str(e)}")
    
    @error_handler
    def load_all_plugins(self) -> Dict[str, bool]:
        """加载所有可用的插件"""
        results = {}
        plugins = self.discover_plugins()
        
        # 按加载顺序排序插件
        plugin_order = []
        for plugin_name in plugins:
            try:
                metadata = self._load_plugin_metadata(plugin_name)
                plugin_order.append((plugin_name, metadata.load_order))
            except Exception:
                continue
        
        plugin_order.sort(key=lambda x: x[1])
        
        # 按顺序加载插件
        for plugin_name, _ in plugin_order:
            results[plugin_name] = self.load_plugin(plugin_name)
        
        return results
    
    @error_handler
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载指定的插件"""
        if plugin_name in self.plugins:
            try:
                # 检查是否有其他插件依赖此插件
                dependents = self._find_dependent_plugins(plugin_name)
                if dependents:
                    raise PluginError(f"无法卸载插件 {plugin_name}，以下插件依赖它: {', '.join(dependents)}")
                
                plugin = self.plugins[plugin_name]
                plugin.cleanup()
                del self.plugins[plugin_name]
                if plugin_name in self.metadata_cache:
                    del self.metadata_cache[plugin_name]
                if plugin_name in self.file_watchers:
                    del self.file_watchers[plugin_name]
                
                self.logger.log_plugin(plugin_name, "unload", True)
                return True
            except Exception as e:
                self.logger.log_plugin(plugin_name, "unload", False, str(e))
                raise PluginError(f"卸载插件 {plugin_name} 失败: {str(e)}")
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """获取指定的插件实例"""
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, PluginBase]:
        """获取所有已加载的插件"""
        return self.plugins.copy()
    
    @error_handler
    def execute_plugin_method(self, plugin_name: str, method_name: str, *args, **kwargs) -> Any:
        """执行插件的指定方法"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise PluginError(f"插件 {plugin_name} 未加载")
            
        if not plugin._initialized:
            raise PluginError(f"插件 {plugin_name} 未初始化")
            
        if not hasattr(plugin, method_name):
            raise PluginError(f"插件 {plugin_name} 不支持方法 {method_name}")
            
        method = getattr(plugin, method_name)
        if not callable(method):
            raise PluginError(f"插件 {plugin_name} 的 {method_name} 不是可调用的方法")
            
        try:
            return method(*args, **kwargs)
        except Exception as e:
            self.logger.log_plugin(plugin_name, f"execute_{method_name}", False, str(e))
            raise
    
    def check_updates(self) -> Dict[str, bool]:
        """检查插件更新"""
        results = {}
        for plugin_name in self.plugins:
            try:
                if self._check_plugin_update(plugin_name):
                    results[plugin_name] = True
                    self.reload_plugin(plugin_name)
                else:
                    results[plugin_name] = False
            except Exception as e:
                self.logger.log_plugin(plugin_name, "check_update", False, str(e))
                results[plugin_name] = False
        return results
    
    @error_handler
    def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件"""
        if plugin_name in self.plugins:
            if self.unload_plugin(plugin_name):
                return self.load_plugin(plugin_name)
        return False
    
    def _load_plugin_metadata(self, plugin_name: str) -> PluginMetadata:
        """加载插件元数据"""
        metadata_file = os.path.join(self.plugin_dir, f"{plugin_name}.json")
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return PluginMetadata(json.load(f))
        except Exception as e:
            raise PluginError(f"加载插件 {plugin_name} 的元数据失败: {str(e)}")
    
    def _check_version_compatibility(self, required_version: str) -> bool:
        """检查版本兼容性"""
        # 这里实现版本比较逻辑
        return True
    
    def _load_dependencies(self, dependencies: Dict[str, str]):
        """加载插件依赖"""
        for dep_name, dep_version in dependencies.items():
            if dep_name not in self.plugins:
                if not self.load_plugin(dep_name):
                    raise PluginError(f"无法加载依赖插件 {dep_name}")
            # 这里可以添加版本检查逻辑
    
    def _find_dependent_plugins(self, plugin_name: str) -> List[str]:
        """查找依赖指定插件的其他插件"""
        dependents = []
        for name, metadata in self.metadata_cache.items():
            if plugin_name in metadata.dependencies:
                dependents.append(name)
        return dependents
    
    def _update_file_watcher(self, plugin_name: str):
        """更新文件监视器"""
        plugin_file = os.path.join(self.plugin_dir, f"{plugin_name}.py")
        self.file_watchers[plugin_name] = os.path.getmtime(plugin_file)
    
    def _check_plugin_update(self, plugin_name: str) -> bool:
        """检查插件文件是否已更新"""
        if plugin_name not in self.file_watchers:
            return False
            
        plugin_file = os.path.join(self.plugin_dir, f"{plugin_name}.py")
        current_mtime = os.path.getmtime(plugin_file)
        return current_mtime > self.file_watchers[plugin_name] 