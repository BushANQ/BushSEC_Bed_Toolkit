import json
import os
import time
from typing import Any, Dict, List, Callable, Optional
from ..utils.error_handler import error_handler, ValidationError

class ConfigChangeEvent:
    def __init__(self, key: str, old_value: Any, new_value: Any):
        self.key = key
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = time.time()

class ConfigValidator:
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置是否符合schema"""
        try:
            self._validate_dict(config, self.schema)
            return True
        except ValidationError:
            return False
    
    def _validate_dict(self, config: Dict[str, Any], schema: Dict[str, Any]):
        for key, value_schema in schema.items():
            if key not in config:
                if isinstance(value_schema, dict) and value_schema.get("required", True):
                    raise ValidationError(f"缺少必需的配置项: {key}")
                continue
            
            value = config[key]
            if isinstance(value_schema, dict):
                if "type" in value_schema:
                    self._validate_type(value, value_schema["type"], key)
                if "values" in value_schema:
                    self._validate_values(value, value_schema["values"], key)
                if "schema" in value_schema:
                    self._validate_dict(value, value_schema["schema"])
            else:
                self._validate_type(value, value_schema, key)
    
    def _validate_type(self, value: Any, expected_type: str, key: str):
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict
        }
        if not isinstance(value, type_map.get(expected_type, object)):
            raise ValidationError(f"配置项 {key} 类型错误，期望 {expected_type}")
    
    def _validate_values(self, value: Any, valid_values: List[Any], key: str):
        if value not in valid_values:
            raise ValidationError(f"配置项 {key} 的值必须是以下之一: {valid_values}")

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.config_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        self.config: Dict[str, Any] = {}
        self.version = "1.0.0"
        self.listeners: List[Callable[[ConfigChangeEvent], None]] = []
        self.validator = ConfigValidator(self._get_config_schema())
        self.load_config()
    
    @error_handler
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    if self._validate_version(loaded_config.get("_version", "0.0.0")):
                        self.config = loaded_config
                    else:
                        self.config = self._migrate_config(loaded_config)
            else:
                self.config = self._get_default_config()
            
            if not self.validator.validate(self.config):
                raise ValidationError("配置验证失败")
                
            self.save_config()
        except Exception as e:
            self.config = self._get_default_config()
            raise e
    
    @error_handler
    def save_config(self):
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            config_to_save = self.config.copy()
            config_to_save["_version"] = self.version
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise e
    
    def add_listener(self, listener: Callable[[ConfigChangeEvent], None]):
        """添加配置变更监听器"""
        if listener not in self.listeners:
            self.listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[ConfigChangeEvent], None]):
        """移除配置变更监听器"""
        if listener in self.listeners:
            self.listeners.remove(listener)
    
    def _notify_listeners(self, event: ConfigChangeEvent):
        """通知所有监听器"""
        for listener in self.listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"配置监听器执行失败: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    
    @error_handler
    def set(self, key: str, value: Any):
        """设置配置项"""
        old_value = self.config.get(key)
        if old_value != value:
            self.config[key] = value
            event = ConfigChangeEvent(key, old_value, value)
            self._notify_listeners(event)
            self.save_config()
    
    def _validate_version(self, version: str) -> bool:
        """验证配置版本"""
        return version == self.version
    
    def _migrate_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """迁移旧版本配置"""
        # 这里实现配置迁移逻辑
        new_config = self._get_default_config()
        # 合并旧配置中的有效配置
        for key, value in old_config.items():
            if key in new_config and not key.startswith('_'):
                new_config[key] = value
        return new_config
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """获取配置schema"""
        return {
            "ui": {
                "type": "dict",
                "schema": {
                    "theme": {
                        "type": "str",
                        "values": ["dark", "light"]
                    },
                    "language": {
                        "type": "str",
                        "values": ["zh_CN", "en_US"]
                    },
                    "window_size": {
                        "type": "dict",
                        "schema": {
                            "width": {"type": "int"},
                            "height": {"type": "int"}
                        }
                    }
                }
            },
            "injection": {
                "type": "dict",
                "schema": {
                    "default_method": {
                        "type": "str",
                        "values": ["new_section", "code_cave", "existing_section"]
                    },
                    "encryption_type": {
                        "type": "str",
                        "values": ["xor", "custom_xor", "rc4", "aes"]
                    },
                    "obfuscation_level": {
                        "type": "str",
                        "values": ["low", "medium", "high", "extreme"]
                    }
                }
            },
            "process": {
                "type": "dict",
                "schema": {
                    "refresh_interval": {"type": "int"},
                    "show_system_processes": {"type": "bool"}
                }
            },
            "security": {
                "type": "dict",
                "schema": {
                    "backup_files": {"type": "bool"},
                    "verify_signatures": {"type": "bool"},
                    "log_operations": {"type": "bool"}
                }
            },
            "plugins": {
                "type": "dict",
                "schema": {
                    "enabled": {"type": "list"},
                    "auto_update": {"type": "bool"}
                }
            }
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "ui": {
                "theme": "dark",
                "language": "zh_CN",
                "window_size": {
                    "width": 1200,
                    "height": 800
                }
            },
            "injection": {
                "default_method": "new_section",
                "encryption_type": "xor",
                "obfuscation_level": "medium"
            },
            "process": {
                "refresh_interval": 5,
                "show_system_processes": False
            },
            "security": {
                "backup_files": True,
                "verify_signatures": True,
                "log_operations": True
            },
            "plugins": {
                "enabled": [],
                "auto_update": True
            }
        } 