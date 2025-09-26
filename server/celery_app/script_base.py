#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本基础库 - 轻量化脚本开发工具
================================

本模块提供统一的脚本开发基础功能，简化脚本编写流程，提供标准化的参数处理、
日志输出、结果格式化等功能。这是所有脚本的基础依赖库。

主要功能：
--------
1. 统一的参数管理 - 从环境变量获取和解析JSON参数
2. 标准化的日志输出 - 提供debug、info、warning、error四个级别
3. 统一的结果格式 - 标准化的成功/失败结果结构
4. 自动错误处理 - 捕获异常并生成标准错误报告
5. 执行时间统计 - 自动计算脚本执行耗时
6. 兼容性支持 - 提供函数式接口保持向后兼容

设计原则：
--------
- 轻量化：最小化依赖，只包含核心功能
- 标准化：统一的接口和输出格式
- 易用性：简化脚本开发流程
- 可扩展：支持复杂脚本的扩展需求

使用场景：
--------
- 简单脚本：直接使用create_simple_script函数
- 复杂脚本：继承ScriptBase类实现自定义逻辑
- 传统脚本：使用兼容性函数保持现有代码不变

架构说明：
--------
ScriptBase类提供核心功能，create_simple_script提供快捷入口，
兼容性函数确保现有脚本无需修改即可使用新功能。
"""

import os
import json
import sys
import time
import traceback
from typing import Dict, Any, Optional


class ScriptBase:
    """
    脚本基础类，提供核心功能
    
    这是所有脚本的基础类，提供统一的参数处理、日志输出、结果格式化等功能。
    脚本开发者可以继承此类或直接使用create_simple_script函数。
    
    属性：
    -----
    script_name : str
        脚本名称，从环境变量SCRIPT_NAME获取，默认为'unknown_script'
    parameters : Dict[str, Any]
        脚本参数，从环境变量SCRIPT_PARAMETERS解析JSON获取
    page_context : str
        页面上下文，从环境变量PAGE_CONTEXT获取，默认为'unknown'
    start_time : float
        脚本开始执行的时间戳，用于计算执行耗时
    
    示例：
    -----
    # 方式1：直接使用
    script = ScriptBase('my_script')
    result = script.success_result('执行成功', {'data': 'some_data'})
    
    # 方式2：继承使用
    class MyScript(ScriptBase):
        def run(self):
            # 自定义逻辑
            return self.success_result('自定义执行完成')
    """
    
    def __init__(self, script_name: Optional[str] = None):
        """
        初始化脚本环境
        
        从环境变量中获取脚本名称、参数和页面上下文，初始化执行环境。
        自动记录开始时间用于后续计算执行耗时。
        
        参数：
        -----
        script_name : Optional[str]
            脚本名称，如果为None则从环境变量SCRIPT_NAME获取
            
        环境变量：
        --------
        SCRIPT_NAME : str
            脚本名称标识
        SCRIPT_PARAMETERS : str
            JSON格式的脚本参数
        PAGE_CONTEXT : str
            页面上下文信息，用于标识脚本来源页面
            
        示例：
        -----
        # 从环境变量获取
        script = ScriptBase()  # 使用SCRIPT_NAME环境变量
        
        # 直接指定
        script = ScriptBase('my_custom_script')
        """
        # 获取脚本名称，优先使用传入参数，其次环境变量，最后使用默认值
        self.script_name = script_name or os.environ.get('SCRIPT_NAME', 'unknown_script')
        
        # 解析脚本参数
        self.parameters = self._get_parameters()
        
        # 获取页面上下文信息
        self.page_context = os.environ.get('PAGE_CONTEXT', 'unknown')
        
        # 记录开始时间，用于计算执行耗时
        self.start_time = time.time()
        
        # 输出初始化信息
        self.info(f"{self.script_name} 开始执行")
    
    def _get_parameters(self) -> Dict[str, Any]:
        """
        从环境变量获取脚本参数
        
        从环境变量SCRIPT_PARAMETERS中解析JSON格式的参数。
        如果解析失败或环境变量不存在，返回空字典。
        
        返回：
        -----
        Dict[str, Any]
            解析后的参数字典
            
        异常处理：
        --------
        json.JSONDecodeError
            当JSON格式错误时，返回空字典而不是抛出异常
            
        示例：
        -----
        # 环境变量: SCRIPT_PARAMETERS='{"param1":"value1","param2":123}'
        params = self._get_parameters()
        # 返回: {"param1": "value1", "param2": 123}
        """
        try:
            # 从环境变量获取JSON字符串
            params_str = os.environ.get('SCRIPT_PARAMETERS', '{}')
            # 解析JSON为Python字典
            return json.loads(params_str)
        except json.JSONDecodeError:
            # JSON解析失败时返回空字典，避免脚本崩溃
            return {}
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        获取指定参数
        
        从参数字典中获取指定键的值，如果键不存在则返回默认值。
        
        参数：
        -----
        key : str
            参数键名
        default : Any
            默认值，当键不存在时返回
            
        返回：
        -----
        Any
            参数值或默认值
            
        示例：
        -----
        # 获取必需参数
        search_string = script.get_parameter('search_string')
        
        # 获取可选参数，带默认值
        timeout = script.get_parameter('timeout', 30)
        
        # 获取布尔参数
        verbose = script.get_parameter('verbose', False)
        """
        return self.parameters.get(key, default)
    
    def debug(self, message: str):
        """
        输出调试信息
        
        输出调试级别的日志信息，用于开发调试阶段。
        输出到stderr，避免与脚本结果输出混淆。
        
        参数：
        -----
        message : str
            调试信息内容
            
        示例：
        -----
        script.debug("开始处理文件列表")
        script.debug(f"找到 {len(files)} 个文件")
        """
        print(f"[DEBUG] {message}", file=sys.stderr)
    
    def info(self, message: str):
        """
        输出信息
        
        输出信息级别的日志，用于记录脚本执行的关键步骤。
        输出到stderr，避免与脚本结果输出混淆。
        
        参数：
        -----
        message : str
            信息内容
            
        示例：
        -----
        script.info("脚本开始执行")
        script.info("处理完成，共处理100个文件")
        """
        print(f"[INFO] {message}", file=sys.stderr)
    
    def warning(self, message: str):
        """
        输出警告
        
        输出警告级别的日志，用于记录可能的问题或异常情况。
        输出到stderr，避免与脚本结果输出混淆。
        
        参数：
        -----
        message : str
            警告信息内容
            
        示例：
        -----
        script.warning("配置文件不存在，使用默认配置")
        script.warning("网络连接超时，尝试重试")
        """
        print(f"[WARNING] {message}", file=sys.stderr)
    
    def error(self, message: str):
        """
        输出错误
        
        输出错误级别的日志，用于记录错误信息。
        输出到stderr，避免与脚本结果输出混淆。
        
        参数：
        -----
        message : str
            错误信息内容
            
        示例：
        -----
        script.error("无法读取文件: /path/to/file.txt")
        script.error("数据库连接失败")
        """
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def success_result(self, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建成功结果
        
        创建标准化的成功结果格式，包含状态、消息、数据和元数据。
        自动计算执行耗时并包含在元数据中。
        
        参数：
        -----
        message : str
            成功消息
        data : Optional[Dict[str, Any]]
            返回的数据，可选
            
        返回：
        -----
        Dict[str, Any]
            标准化的成功结果格式
            
        结果格式：
        --------
        {
            "status": "success",
            "message": "成功消息",
            "data": {...},  # 可选的数据
            "metadata": {
                "script_name": "脚本名称",
                "execution_duration": 1.23,  # 执行耗时（秒）
                "execution_context": "页面上下文"
            }
        }
        
        示例：
        -----
        result = script.success_result(
            "文件处理完成",
            {"processed_files": 100, "errors": 0}
        )
        """
        # 计算执行耗时
        execution_time = time.time() - self.start_time
        
        return {
            'status': 'success',
            'message': message,
            'data': data or {},
            'metadata': {
                'script_name': self.script_name,
                'execution_duration': execution_time,
                'execution_context': self.page_context
            }
        }
    
    def error_result(self, error_message: str, error_type: str = 'RuntimeError') -> Dict[str, Any]:
        """
        创建错误结果
        
        创建标准化的错误结果格式，包含状态、错误消息、错误类型和元数据。
        自动计算执行耗时并包含在结果中。
        
        参数：
        -----
        error_message : str
            错误消息
        error_type : str
            错误类型，默认为'RuntimeError'
            
        返回：
        -----
        Dict[str, Any]
            标准化的错误结果格式
            
        结果格式：
        --------
        {
            "status": "error",
            "message": "脚本名称执行出错: 错误消息",
            "script_name": "脚本名称",
            "error_type": "错误类型",
            "execution_duration": 1.23  # 执行耗时（秒）
        }
        
        示例：
        -----
        result = script.error_result("文件不存在", "FileNotFoundError")
        """
        # 计算执行耗时
        execution_time = time.time() - self.start_time
        
        return {
            'status': 'error',
            'message': f'{self.script_name}执行出错: {error_message}',
            'script_name': self.script_name,
            'error_type': error_type,
            'execution_duration': execution_time
        }
    
    def output_result(self, result: Dict[str, Any]):
        """
        输出结果到stdout
        
        将结果字典格式化为JSON并输出到标准输出。
        使用ensure_ascii=True确保中文字符正确显示。
        
        参数：
        -----
        result : Dict[str, Any]
            要输出的结果字典
            
        异常处理：
        --------
        UnicodeEncodeError
            当编码错误时，尝试使用默认编码重新输出
            
        示例：
        -----
        result = script.success_result("执行完成")
        script.output_result(result)
        # 输出到stdout: {"status": "success", "message": "执行完成", ...}
        """
        try:
            # 输出JSON格式的结果，确保中文字符正确显示
            print(json.dumps(result, ensure_ascii=True, indent=2))
        except UnicodeEncodeError:
            # 如果编码失败，尝试使用默认编码
            print(json.dumps(result, ensure_ascii=True, indent=2))
    
    def run_with_error_handling(self, main_func):
        """
        运行主函数并处理错误
        
        执行主函数并自动处理异常，生成标准化的错误报告。
        如果主函数返回非字典结果，会自动包装为成功结果。
        
        参数：
        -----
        main_func : callable
            主函数，接受ScriptBase实例作为参数
            
        异常处理：
        --------
        捕获所有异常，生成错误结果并退出程序
            
        示例：
        -----
        def my_main_logic(script):
            # 脚本逻辑
            return script.success_result("执行完成")
        
        script = ScriptBase('my_script')
        script.run_with_error_handling(my_main_logic)
        """
        try:
            # 执行主函数
            result = main_func(self)
            
            if isinstance(result, dict):
                # 如果返回字典，直接输出
                self.output_result(result)
            else:
                # 如果返回非字典，包装为成功结果
                success_result = self.success_result(str(result) if result else "脚本执行完成")
                self.output_result(success_result)
                
        except Exception as e:
            # 捕获所有异常
            error_msg = str(e)
            error_type = type(e).__name__
            
            # 输出错误日志
            self.error(f"脚本执行失败: {error_msg}")
            self.error(f"错误堆栈: {traceback.format_exc()}")
            
            # 生成错误结果并输出
            error_result = self.error_result(error_msg, error_type)
            self.output_result(error_result)
            
            # 退出程序，返回错误码
            sys.exit(1)


def create_simple_script(script_name: str, main_logic):
    """
    创建简单脚本的快捷函数
    
    这是创建脚本的快捷方式，自动处理ScriptBase实例化和错误处理。
    适用于大多数简单脚本的开发。
    
    参数：
    -----
    script_name : str
        脚本名称
    main_logic : callable
        主逻辑函数，接受ScriptBase实例作为参数
        
    使用流程：
    --------
    1. 创建ScriptBase实例
    2. 调用run_with_error_handling执行主逻辑
    3. 自动处理异常和结果输出
    
    示例：
    -----
    def my_main_logic(script):
        # 获取参数
        param1 = script.get_parameter('param1')
        
        # 执行业务逻辑
        script.info("开始处理...")
        
        # 返回结果
        return script.success_result("处理完成", {"result": "data"})
    
    # 创建并运行脚本
    create_simple_script('my_script', my_main_logic)
    """
    # 创建脚本实例
    script = ScriptBase(script_name)
    # 运行主逻辑并处理错误
    script.run_with_error_handling(main_logic)


# ============================================================================
# 兼容性函数 - 保持向后兼容
# ============================================================================

def get_script_parameters() -> Dict[str, Any]:
    """
    获取脚本参数（兼容性函数）
    
    为了保持与现有脚本的兼容性而提供的函数式接口。
    建议新脚本使用ScriptBase.get_parameter()方法。
    
    返回：
    -----
    Dict[str, Any]
        脚本参数字典
        
    示例：
    -----
    params = get_script_parameters()
    search_string = params.get('search_string', '')
    """
    try:
        # 从环境变量获取JSON字符串并解析
        params_str = os.environ.get('SCRIPT_PARAMETERS', '{}')
        return json.loads(params_str)
    except json.JSONDecodeError:
        # JSON解析失败时返回空字典
        return {}


def get_page_context() -> str:
    """
    获取页面上下文（兼容性函数）
    
    为了保持与现有脚本的兼容性而提供的函数式接口。
    建议新脚本使用ScriptBase.page_context属性。
    
    返回：
    -----
    str
        页面上下文信息
        
    示例：
    -----
    context = get_page_context()
    print(f"当前页面上下文: {context}")
    """
    return os.environ.get('PAGE_CONTEXT', 'unknown')


def get_script_name() -> str:
    """
    获取脚本名称（兼容性函数）
    
    为了保持与现有脚本的兼容性而提供的函数式接口。
    建议新脚本使用ScriptBase.script_name属性。
    
    返回：
    -----
    str
        脚本名称
        
    示例：
    -----
    name = get_script_name()
    print(f"当前脚本: {name}")
    """
    return os.environ.get('SCRIPT_NAME', 'unknown_script')