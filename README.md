# BushSEC_Bed_Toolkit
#### 目前还是半成品，先留个坑，欢迎各位师傅交PR完善它，
#### 本项目旨在为文件分析和初步混淆以避免静态识别的工具集合，目标是能够成为一个用于红(混淆)蓝(文件分析，溯源)对抗环境的基础工具集
#### PE注入模块基于：https://github.com/BushANQ/BushSEC-PE-injected
#### 杀毒软件检测模块基于：用python实现的Get_AV：https://github.com/BushANQ/Get_AV
#### MalwareHuntuer灵感来源于https://github.com/Fadouse/MalwareBazaarHunter
## 📝 TODO
* [x] 

依赖安装
```bash
pip install -r requirements.txt
```
主要功能包括:

#### 1. 文件分析功能(请等待V2.5)
- **基本文件信息分析**
  - 文件名、大小、创建/修改时间
  - MD5/SHA1/SHA256哈希值计算
  - PE文件结构分析
  
- **深入分析**
  - 导入表分析
  - 区段信息分析
  - 字符串提取与分析
  - 熵值分析
  - 数字签名验证(暂未完成证书链的验证)

- **AI研判功能** (测试阶段，暂未公布)
  - 支持接入自定义API进行智能分析
  - 提供全面的软件评估报告
  - 可定制分析维度和深度

#### 2. PE文件注入功能(测试阶段，可能暂不可用)

- **注入方法**
  - 新增区段注入
  - 代码洞注入
  - 已有区段注入

- **加密选项**
  - XOR单字节加密
  - XOR多字节加密
  - RC4加密
  - AES加密

- **高级免杀特性**
  - 代码混淆
  - 反调试技术
  - 时间戳操纵
  - PE头随机化
  - 区段名称随机化
  - 添加虚假证书

#### 3. 进程注入功能

- **注入方式**
  - 经典远程线程注入
  - APC注入
  - 线程劫持
  - PE加载注入

- **配套功能**
  - 进程列表实时刷新
  - shellcode加密保护
  - 内存保护机制
  - 注入过程监控

#### 4. 代码混淆功能(测试阶段，可能暂不可用)

- **支持文件类型**
  - EXE可执行文件
  - DLL动态链接库
  - Shellcode代码

- **混淆方法**
  - 代码混淆
  - 加密壳保护
  - 多态变形
  - 虚拟化保护

- **高级选项**
  - 字符串加密
  - API调用混淆
  - 控制流混淆
  - 反调试保护

#### 5. 杀软检测功能

- **本地杀软检测**
  - 检测已安装杀毒软件
  - 显示详细进程信息
  - 实时状态监控

- **服务分析**
  - 分析系统服务信息
  - 识别安全软件服务
  - 显示服务运行状态

#### 6. 辅助工具集(暂未完成)

包含多个红队渗透测试常用工具:
- 信息收集工具
- 漏洞利用工具
- 权限提升工具
- 横向移动工具
- 持久化工具
- 数据窃取工具

#### 技术特性

- 使用PyQt5构建现代化GUI界面
- 多线程处理保证界面响应
- 模块化设计便于扩展
- 详细的状态反馈和错误处理
- 支持自定义工具和命令执行

#### 6. MalwareHuntuer(恶意样本猎手)(内测中...)
支持通过tag标签搜索，VT检测率筛选以及完善的UI设计，灵感来源于https://github.com/Fadouse/MalwareBazaarHunter

#### 使用说明

1. 需要Python 3.x环境
2. 安装必要的依赖包:
   ```bash
   pip install PyQt5 pefile psutil
   ```
3. 运行主程序:
   ```bash
   python V3.0.py
   ```

#### 注意事项

- 仅供安全研究使用
- 使用前请确认具有相应权限
- 建议在测试环境中使用
- 遵守当地法律法规

## 更新日志
#### V1.0 TO v2.0
* [x] ---- 1.新增核心功能模块：

- **进程注入功能**
```python
def process_injection(pid, shellcode_file, injection_method='classic'):
    # 支持多种注入方法
    # - 经典远程线程注入
    # - APC注入 
    # - 线程劫持注入
    # - PE加载注入
```
- **代码混淆功能**
```python
def perform_obfuscation(input_file, output_file, options):
    # 多种混淆技术:
    # - 字符串加密
    # - API调用混淆
    # - 控制流混淆
    # - 反调试技术
```
- **杀毒软件检测**
```python
def detect_av_processes():
    # 检测超过100种杀毒软件
    # 详细的进程状态监控
    # 实时检测与更新
```
新增辅助功能：

  - 文件完整性验证
  - 进程权限管理
  - 内存保护机制
  - 日志记录系统

* [x] ---- 2.用户界面升级

UI框架改进：
```python
class AdvancedPEInjector(QWidget):
    def __init__(self):
        # 新增特性:
        # - 多标签页设计
        # - 黑色风格
        # - 动态状态栏
        # - 进度显示
```

交互优化：
- 添加工具栏和菜单栏
- 增加快捷键支持
- 实时状态反馈
- 操作历史记录

* [x] ---- 3.注入技术升级

多种注入方式：
```python
def patch_pe(pe_file_path, shellcode_path, output_file_path, options):
    # 支持:
    # - 新增区段注入
    # - 代码洞注入
    # - 已有区段注入
    # - 入口点修改
```

加密与混淆：
```python
# 新增多层加密支持
def multi_layer_encryption(shellcode, layers=3):
    # - XOR加密
    # - RC4加密
    # - AES加密
    # - 自定义加密算法
```

* [x] ---- 4.反检测技术

新增多重反检测机制：
```python
def add_anti_analysis(shellcode):
    # 包含:
    # - 调试器检测
    # - 虚拟机检测
    # - 沙箱检测
    # - 时间延迟检测
```

PE文件伪装：
```python
# 新增PE文件伪装技术
def manipulate_headers(pe):
    # - 时间戳修改
    # - 节表随机化
    # - 导入表混淆
    # - 签名伪造
```

* [x] ---- 5.错误处理与日志

错误处理：
```python
try:
    # 操作代码
except Exception as e:
    import traceback
    traceback.print_exc()
    logging.error(f"错误详情: {str(e)}")
```

* [x] ---- 6.代码架构优化

模块化设计：
  - 核心功能模块化
  - 界面与逻辑分离
  - 配置文件独立

性能优化：
  - 多线程支持
  - 内存管理优化
  - 资源释放机制
  - 缓存系统

* [x] ---- 7.安全性提升

新增安全特性：
  - 进程权限校验
  - 内存保护机制
  - 操作验证
  - 数据加密存储

代码保护：
  - 代码混淆
  - 字符串加密
  - 反调试技术
  - 完整性校验

