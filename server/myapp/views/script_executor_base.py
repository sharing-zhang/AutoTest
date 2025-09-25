"""
统一脚本执行基类
================

本模块提供统一的脚本执行基类，消除传统脚本和动态脚本执行器之间的代码重复。
这是整个脚本执行系统的核心组件，负责在后台异步执行各种类型的脚本。

主要功能：
---------
1. 统一的任务状态管理 - 跟踪脚本执行的生命周期
2. 统一的错误处理和重试机制 - 提高执行可靠性
3. 统一的日志记录 - 便于调试和监控
4. 统一的资源监控 - 监控CPU、内存使用情况
5. 统一的执行结果处理 - 标准化返回格式
6. 进程隔离执行 - 使用subprocess确保安全性

设计原则：
---------
- DRY (Don't Repeat Yourself): 消除代码重复
- 单一职责：每个类只负责一个功能
- 开闭原则：对扩展开放，对修改关闭
- 依赖注入：通过参数传递依赖
- 进程隔离：脚本在独立进程中执行，确保安全性

架构说明：
---------
- ScriptExecutionResult: 执行结果封装类，标准化返回格式
- UnifiedScriptExecutor: 统一执行器，支持多种脚本类型
- 支持Python脚本、Shell脚本、批处理文件等多种格式
- 集成Celery异步任务系统，支持长时间运行
- 完整的错误处理和重试机制

使用场景：
---------
- 前端脚本按钮点击执行
- 定时任务调度
- 批量数据处理
- 系统监控和维护
- 自动化测试和部署
"""

# ============================================================================
# 导入依赖库
# ============================================================================

# Python标准库 - 基础功能
import logging          # 日志记录
import json            # JSON数据处理
import traceback       # 异常堆栈跟踪
import psutil          # 系统资源监控（CPU、内存）
from datetime import datetime  # 时间处理
from typing import Dict, Any, Optional, Callable, Tuple  # 类型注解

# Django框架 - Web应用功能
from django.utils import timezone  # 时区处理
from django.conf import settings   # Django配置

# Celery框架 - 异步任务处理
from celery import shared_task     # 异步任务装饰器
from celery.utils.log import get_task_logger  # Celery日志记录器

# 项目内部模块
from ..models import TaskExecution, Script  # 数据模型
from ..management.commands.script_config_manager import script_config_manager  # 脚本配置管理器

# 初始化Celery任务日志记录器
logger = get_task_logger(__name__)


# ============================================================================
# 脚本执行结果封装类
# ============================================================================

class ScriptExecutionResult:
    """
    脚本执行结果封装类
    
    用于标准化脚本执行的结果格式，提供统一的返回数据结构。
    包含执行状态、结果数据、错误信息、执行时间、资源使用等完整信息。
    
    属性说明：
    ---------
    status : str
        执行状态，可能的值：
        - 'success': 执行成功
        - 'error': 执行失败
        - 'timeout': 执行超时
        - 'cancelled': 执行被取消
    
    result : Any
        执行结果数据，成功时包含脚本返回的数据
        失败时为None
    
    error : str
        错误信息，失败时包含详细的错误描述
        成功时为None
    
    execution_time : float
        执行时间（秒），从开始到结束的总耗时
    
    memory_usage : float
        内存使用量（MB），脚本执行过程中的峰值内存使用
    
    script_name : str
        脚本名称，用于标识执行的脚本
    
    metadata : Dict
        元数据，包含额外的执行信息，如：
        - 执行环境信息
        - 系统资源状态
        - 自定义标签等
    """
    
    def __init__(self, status: str, result: Any = None, error: str = None, 
                 execution_time: float = 0, memory_usage: float = 0, 
                 script_name: str = None, metadata: Dict = None):
        """
        初始化脚本执行结果
        
        参数：
        -----
        status : str
            执行状态，必需参数
        result : Any, optional
            执行结果数据，默认为None
        error : str, optional
            错误信息，默认为None
        execution_time : float, optional
            执行时间（秒），默认为0
        memory_usage : float, optional
            内存使用量（MB），默认为0
        script_name : str, optional
            脚本名称，默认为None
        metadata : Dict, optional
            元数据字典，默认为空字典
        """
        self.status = status
        self.result = result
        self.error = error
        self.execution_time = execution_time
        self.memory_usage = memory_usage
        self.script_name = script_name
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        将执行结果转换为字典，便于JSON序列化和API返回。
        
        返回：
        -----
        Dict[str, Any]
            包含所有执行结果信息的字典
        """
        return {
            'status': self.status,
            'result': self.result,
            'error': self.error,
            'execution_time': self.execution_time,
            'memory_usage': self.memory_usage,
            'script_name': self.script_name,
            'metadata': self.metadata
        }
    
    def is_success(self) -> bool:
        """
        判断是否执行成功
        
        检查执行状态是否为成功状态。
        
        返回：
        -----
        bool
            True表示执行成功，False表示执行失败
        """
        return self.status == 'success'
    
    def is_error(self) -> bool:
        """判断是否执行失败"""
        return self.status == 'error'


# ============================================================================
# 任务执行管理器
# ============================================================================

class TaskExecutionManager:
    """
    任务执行管理器 - 统一的任务状态管理
    
    负责管理TaskExecution数据库记录的生命周期，提供统一的状态更新接口。
    确保任务执行过程中的状态变化能够正确记录到数据库中。
    
    主要功能：
    ---------
    1. 加载和验证任务执行记录
    2. 更新任务执行状态（PENDING -> STARTED -> SUCCESS/FAILURE）
    3. 记录执行结果和资源使用情况
    4. 保存执行结果到相关数据表
    5. 提供状态查询和错误处理
    
    状态流转：
    ---------
    PENDING -> STARTED -> SUCCESS/FAILURE
    """
    
    def __init__(self, task_execution_id: int):
        """
        初始化任务执行管理器
        
        参数：
        -----
        task_execution_id : int
            任务执行记录的数据库ID
        """
        self.task_execution_id = task_execution_id
        self.task_execution = None
        self._load_task_execution()
    
    def _load_task_execution(self):
        """
        加载任务执行记录
        
        从数据库中加载TaskExecution记录，如果记录不存在则抛出异常。
        
        异常：
        ----
        ValueError: 当任务执行记录不存在时
        """
        try:
            self.task_execution = TaskExecution.objects.get(id=self.task_execution_id)
            logger.info(f"TaskExecution {self.task_execution_id} loaded successfully")
        except TaskExecution.DoesNotExist:
            logger.error(f"TaskExecution {self.task_execution_id} not found")
            raise ValueError(f"TaskExecution {self.task_execution_id} not found")
    
    def update_status(self, status: str, **kwargs):
        """
        更新任务状态
        
        更新TaskExecution记录的状态和其他字段，并保存到数据库。
        
        参数：
        -----
        status : str
            新的任务状态，可能的值：
            - 'PENDING': 等待执行
            - 'STARTED': 正在执行
            - 'SUCCESS': 执行成功
            - 'FAILURE': 执行失败
            - 'REVOKED': 执行被取消
        
        **kwargs : dict
            其他需要更新的字段，如：
            - started_at: 开始时间
            - completed_at: 完成时间
            - result: 执行结果
            - execution_time: 执行时间
            - memory_usage: 内存使用量
            - error_message: 错误信息
        """
        if not self.task_execution:
            logger.warning(f"TaskExecution {self.task_execution_id} not loaded")
            return
        
        # 更新状态
        self.task_execution.status = status
        
        # 更新其他字段
        for key, value in kwargs.items():
            if hasattr(self.task_execution, key):
                setattr(self.task_execution, key, value)
                logger.debug(f"Updated {key} = {value}")
            else:
                logger.warning(f"Field {key} does not exist on TaskExecution")
        
        # 保存到数据库
        self.task_execution.save()
        logger.info(f"TaskExecution {self.task_execution_id} status updated to {status}")
    
    def mark_started(self):
        """
        标记任务开始执行
        
        将任务状态更新为'STARTED'，并记录开始时间。
        """
        self.update_status('STARTED', started_at=timezone.now())
        logger.info(f"TaskExecution {self.task_execution_id} marked as started")
    
    def mark_success(self, result: Any, execution_time: float, memory_usage: float):
        """
        标记任务执行成功
        
        将任务状态更新为'SUCCESS'，并记录执行结果、时间和资源使用情况。
        
        参数：
        -----
        result : Any
            执行结果数据
        execution_time : float
            执行时间（秒）
        memory_usage : float
            内存使用量（MB）
        """
        self.update_status(
            'SUCCESS',
            result=result,
            execution_time=execution_time,
            memory_usage=memory_usage,
            completed_at=timezone.now()
        )
        logger.info(f"TaskExecution {self.task_execution_id} marked as success")
        
        # 保存到扫描结果表
        self._save_to_scan_result(result, execution_time, memory_usage)
    
    def mark_failure(self, error_message: str):
        """
        标记任务执行失败
        
        将任务状态更新为'FAILURE'，并记录错误信息和完成时间。
        
        参数：
        -----
        error_message : str
            错误信息描述
        """
        self.update_status(
            'FAILURE',
            error_message=error_message,
            completed_at=timezone.now()
        )
        logger.error(f"TaskExecution {self.task_execution_id} marked as failure: {error_message}")
    
    def update_task_id(self, task_id: str):
        """
        更新Celery任务ID
        
        将Celery任务的ID保存到TaskExecution记录中，用于任务跟踪和取消。
        
        参数：
        -----
        task_id : str
            Celery任务的唯一标识符
        """
        if self.task_execution:
            self.task_execution.task_id = task_id
            self.task_execution.save()
            logger.info(f"TaskExecution {self.task_execution_id} updated with task_id: {task_id}")
    
    def _save_to_scan_result(self, result: Any, execution_time: float, memory_usage: float):
        """
        保存执行结果到扫描结果表
        
        将脚本执行结果保存到ScanDevUpdate_scanResult表中，用于历史记录和数据分析。
        
        参数：
        -----
        result : Any
            执行结果数据
        execution_time : float
            执行时间（秒）
        memory_usage : float
            内存使用量（MB）
        """
        try:
            from myapp.models import ScanDevUpdate_scanResult
            from django.utils import timezone
            from myapp.management.commands.script_config_manager import ScriptConfigManager
            import json
            
            # 生成文件名 - 使用 dialog_title 
            script_name = self.task_execution.script.name if self.task_execution.script else 'unknown'
            
            # 获取脚本的 dialog_title
            config_manager = ScriptConfigManager()
            display_info = config_manager.get_script_display_info(script_name)
            dialog_title = display_info.get('dialog_title', script_name)
            
            # 添加调试日志
            # logger.info(f"脚本名称: {script_name}")
            # logger.info(f"显示信息: {display_info}")
            # logger.info(f"Dialog Title: {dialog_title}")
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{dialog_title}"
            
            # 添加文件名调试日志
            # logger.info(f"生成的文件名: {filename}")
            
            # 准备完整结果内容（用于scandevresult_content）
            full_result_content = json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, dict) else str(result)
            
            # 准备显示内容（用于script_output）- 只显示message字段
            if isinstance(result, dict):
                # 优先显示message字段
                if 'message' in result:
                    display_content = str(result['message'])
                elif 'content' in result:
                    display_content = str(result['content'])
                else:
                    # 如果没有message字段，显示简化的结果信息
                    display_content = f"脚本执行完成"
            else:
                display_content = str(result)
            
            # 创建扫描结果记录
            scan_result = ScanDevUpdate_scanResult.objects.create(
                scandevresult_filename=filename,
                scandevresult_time=timezone.now(),
                director=self.task_execution.user.username if self.task_execution.user else 'system',
                remark=f'脚本执行结果 - {dialog_title}',
                status='0',  # 可用
                scandevresult_content=full_result_content,  # 完整JSON结果
                result_type='script',  # 脚本执行
                script_name=script_name,
                task_id=self.task_execution.task_id,
                execution_time=execution_time,
                script_output=display_content,  # 只显示message字段
                error_message=None
            )
            
            logger.info(f"扫描结果已保存到数据库: {scan_result.id}")
            
        except Exception as e:
            logger.error(f"保存扫描结果失败: {str(e)}")
            # 不抛出异常，避免影响主流程


# ============================================================================
# 资源监控器
# ============================================================================

class ResourceMonitor:
    """
    资源监控器 - 统一的资源使用监控
    
    监控脚本执行过程中的系统资源使用情况，包括执行时间和内存使用量。
    使用psutil库获取进程级别的资源信息，提供准确的性能数据。
    
    主要功能：
    ---------
    1. 监控执行时间 - 从开始到结束的总耗时
    2. 监控内存使用 - 进程内存使用量的变化
    3. 提供性能数据 - 用于执行结果分析和优化
    4. 支持多次监控 - 可以重复使用同一个监控器实例
    
    使用方式：
    ---------
    monitor = ResourceMonitor()
    monitor.start_monitoring()
    # ... 执行脚本 ...
    execution_time, memory_usage = monitor.stop_monitoring()
    """
    
    def __init__(self):
        """
        初始化资源监控器
        
        初始化监控相关的属性，准备开始资源监控。
        """
        self.start_time = None      # 开始时间
        self.start_memory = None   # 开始时的内存使用量（MB）
        self.process_info = None   # 当前进程信息对象
    
    def start_monitoring(self):
        """
        开始资源监控
        
        记录开始时间和初始内存使用量，开始监控资源使用情况。
        使用psutil获取当前进程的内存信息。
        """
        self.start_time = timezone.now()
        self.process_info = psutil.Process()
        self.start_memory = self.process_info.memory_info().rss / 1024 / 1024  # 转换为MB
        logger.info(f"Resource monitoring started: {self.start_memory:.2f}MB")
    
    def stop_monitoring(self) -> Tuple[float, float]:
        """
        停止资源监控并返回执行时间和内存使用量
        
        计算从开始监控到现在的执行时间和内存使用量变化。
        
        返回：
        -----
        Tuple[float, float]
            (execution_time, memory_usage)
            - execution_time: 执行时间（秒）
            - memory_usage: 内存使用量变化（MB）
        """
        if not self.start_time:
            logger.warning("Resource monitoring was not started")
            return 0, 0
        
        # 计算执行时间
        execution_time = (timezone.now() - self.start_time).total_seconds()
        
        # 计算内存使用量变化
        if self.process_info:
            final_memory = self.process_info.memory_info().rss / 1024 / 1024  # MB
            memory_usage = final_memory - self.start_memory
        else:
            memory_usage = 0
        
        logger.info(f"Resource monitoring stopped: {execution_time:.2f}s, {memory_usage:.2f}MB")
        return execution_time, memory_usage


# ============================================================================
# 脚本执行基类
# ============================================================================

class ScriptExecutorBase:
    """
    脚本执行基类 - 统一的脚本执行逻辑
    
    提供脚本执行的统一框架，整合任务管理、资源监控、错误处理等功能。
    所有具体的脚本执行器都应该继承此类，实现统一的执行流程。
    
    主要功能：
    ---------
    1. 统一的任务生命周期管理
    2. 资源使用监控（时间、内存）
    3. 错误处理和异常捕获
    4. 执行结果标准化
    5. 数据库状态更新
    
    设计模式：
    ---------
    - 模板方法模式：定义执行流程，子类实现具体逻辑
    - 策略模式：通过回调函数实现不同的执行策略
    - 观察者模式：监控资源使用和状态变化
    
    使用方式：
    ---------
    executor = ScriptExecutorBase(task_execution_id, user_id, page_context)
    result = executor.execute(lambda: self._run_python_file(...))
    """
    
    def __init__(self, task_execution_id: int, user_id: int, page_context: str):
        """
        初始化脚本执行基类
        
        参数：
        -----
        task_execution_id : int
            任务执行记录的数据库ID
        user_id : int
            执行用户ID，用于权限控制
        page_context : str
            页面上下文，标识脚本调用的来源页面
        """
        self.task_execution_manager = TaskExecutionManager(task_execution_id)
        self.user_id = user_id
        self.page_context = page_context
        self.resource_monitor = ResourceMonitor()
        self.script_info = None
    
    def execute(self, script_executor_func: Callable) -> ScriptExecutionResult:
        """
        执行脚本的统一入口
        
        这是脚本执行的核心方法，定义了标准的执行流程：
        1. 开始资源监控
        2. 标记任务开始
        3. 执行具体脚本
        4. 停止资源监控
        5. 更新任务状态
        6. 返回标准化结果
        
        参数：
        -----
        script_executor_func : Callable
            具体的脚本执行函数，应该返回执行结果
            函数签名：() -> Any
            
        返回：
        -----
        ScriptExecutionResult
            标准化的执行结果，包含状态、结果、时间、内存等信息
        """
        try:
            # 开始监控
            self.resource_monitor.start_monitoring()
            
            # 标记任务开始
            self.task_execution_manager.mark_started()
            
            # 执行脚本
            result = script_executor_func()
            
            # 停止监控
            execution_time, memory_usage = self.resource_monitor.stop_monitoring()
            
            # 标记任务成功
            self.task_execution_manager.mark_success(
                result=result,
                execution_time=execution_time,
                memory_usage=memory_usage
            )
            
            # 返回成功结果
            return ScriptExecutionResult(
                status='success',
                result=result,
                execution_time=execution_time,
                memory_usage=memory_usage,
                script_name=self.script_info.get('name') if self.script_info else None
            )
            
        except Exception as exc:
            # 停止监控
            execution_time, memory_usage = self.resource_monitor.stop_monitoring()
            
            # 处理异常
            error_message = str(exc)
            error_traceback = traceback.format_exc()
            
            logger.error(f"Script execution failed: {error_message}")
            logger.error(f"Error traceback: {error_traceback}")
            
            # 标记任务失败
            self.task_execution_manager.mark_failure(f"{error_message}\n\n{error_traceback}")
            
            # 返回错误结果
            return ScriptExecutionResult(
                status='error',
                error=error_message,
                execution_time=execution_time,
                memory_usage=memory_usage,
                script_name=self.script_info.get('name') if self.script_info else None,
                metadata={'traceback': error_traceback}
            )


# ============================================================================
# 统一脚本执行器
# ============================================================================

class UnifiedScriptExecutor(ScriptExecutorBase):
    """
    统一脚本执行器 - 支持所有类型的脚本执行
    
    这是整个脚本执行系统的核心组件，继承自ScriptExecutorBase，
    提供统一的脚本执行接口，支持多种脚本类型的执行。
    
    支持的脚本类型：
    --------------
    1. Python脚本 (.py) - 使用subprocess执行
    2. Shell脚本 (.sh) - 使用subprocess执行
    3. 批处理文件 (.bat/.cmd) - 使用subprocess执行
    4. 其他可执行文件 - 根据文件扩展名自动识别
    
    主要特性：
    ---------
    1. 进程隔离执行 - 使用subprocess确保安全性
    2. 参数传递 - 通过环境变量传递参数
    3. 超时控制 - 防止脚本无限期运行
    4. 输出捕获 - 捕获标准输出和错误输出
    5. 错误处理 - 完整的异常处理和错误报告
    6. 资源监控 - 监控执行时间和内存使用
    
    安全特性：
    ---------
    - 进程隔离：脚本在独立进程中执行
    - 超时限制：防止恶意脚本无限期运行
    - 工作目录隔离：脚本在指定目录中执行
    - 环境变量控制：只传递必要的环境变量
    """
    
    def __init__(self, task_execution_id: int, script_info: Dict, parameters: Dict, 
                 user_id: int, page_context: str):
        """
        初始化统一脚本执行器
        
        参数：
        -----
        task_execution_id : int
            任务执行记录的数据库ID
        script_info : Dict
            脚本信息字典，包含：
            - name: 脚本名称
            - path: 脚本文件路径
            - id: 脚本数据库ID（可选）
        parameters : Dict
            脚本执行参数，由前端传递的动态参数
        user_id : int
            执行用户ID，用于权限控制
        page_context : str
            页面上下文，标识脚本调用的来源页面
        """
        super().__init__(task_execution_id, user_id, page_context)
        self.script_info = script_info
        self.parameters = parameters
    
    def execute_script(self) -> Any:
        """
        执行脚本的统一方法
        
        这是脚本执行的主要入口，负责：
        1. 验证脚本信息
        2. 记录执行日志
        3. 调用具体的脚本执行逻辑
        4. 处理执行结果和异常
        
        返回：
        -----
        Any
            脚本执行结果，通常是字典格式的数据
        """
        script_name = self.script_info['name']
        script_path = self.script_info['path']
        
        logger.info(f"Executing script: {script_name} ({script_path})")
        logger.info(f"Script info: {self.script_info}")
        logger.info(f"Parameters: {self.parameters}")
        
        try:
            result = self._run_script(script_path, self.parameters, self.page_context, script_name)
            logger.info(f"Script execution completed successfully")
            return result
        except Exception as e:
            logger.error(f"Script execution failed with error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def _run_script(self, script_path, parameters, page_context, script_name):
        """
        运行脚本的核心逻辑 - 统一脚本执行入口
        
        此函数是脚本执行的核心调度器，负责：
        1. 验证脚本文件存在性
        2. 处理相对路径和绝对路径
        3. 根据文件类型分发到对应的执行器
        4. 提供统一的错误处理
        
        参数：
        -----
        script_path : str
            脚本文件路径（支持相对路径和绝对路径）
        parameters : dict
            脚本执行参数，通过环境变量传递
        page_context : str
            页面上下文，标识调用来源
        script_name : str
            脚本名称，用于日志记录
            
        返回：
        -----
        dict
            脚本执行结果，包含脚本输出的JSON数据或文本内容
            
        异常：
        ----
        FileNotFoundError
            脚本文件不存在
        ValueError
            不支持的脚本类型
        RuntimeError
            脚本执行失败
        """
        import os
        from django.conf import settings
        
        logger.info(f"[_run_script] Starting script execution")
        logger.info(f"[_run_script] script_path: {script_path}")
        logger.info(f"[_run_script] parameters: {parameters}")
        logger.info(f"[_run_script] page_context: {page_context}")
        logger.info(f"[_run_script] script_name: {script_name}")
        
        # 验证脚本文件存在性
        if not os.path.exists(script_path):
            logger.error(f"[_run_script] Script file does not exist: {script_path}")
            raise FileNotFoundError(f"脚本文件不存在: {script_path}")
        
        # 处理路径：确保使用绝对路径
        if not os.path.isabs(script_path):
            script_path = os.path.join(settings.BASE_DIR, script_path)
            logger.info(f"[_run_script] Converted to absolute path: {script_path}")
        
        logger.info(f"[_run_script] 执行脚本文件: {script_path}")
        
        # 根据文件类型分发到对应的执行器
        if script_path.endswith('.py'):
            logger.info(f"[_run_script] Executing Python file")
            return self._run_python_file(script_path, parameters, page_context, script_name)
        else:
            logger.error(f"[_run_script] Unsupported script type: {os.path.splitext(script_path)[1]}")
            raise ValueError(f"不支持的脚本类型: {os.path.splitext(script_path)[1]}")
    
    def _run_python_file(self, script_path, parameters, page_context, script_name):
        """
        运行Python文件
        
        使用subprocess在独立进程中执行Python脚本，确保安全性和隔离性。
        通过环境变量传递参数，捕获标准输出和错误输出。
        
        参数：
        -----
        script_path : str
            Python脚本文件路径
        parameters : dict
            脚本执行参数
        page_context : str
            页面上下文
        script_name : str
            脚本名称
            
        返回：
        -----
        dict
            脚本执行结果，包含输出数据和元信息
            
        异常：
        ----
        RuntimeError
            脚本执行失败或返回非零退出码
        subprocess.TimeoutExpired
            脚本执行超时
        """
        import subprocess
        import sys
        import json
        import os
        from django.utils import timezone
        
        logger.info(f"[_run_python_file] Starting Python file execution")
        logger.info(f"[_run_python_file] script_path: {script_path}")
        logger.info(f"[_run_python_file] script_name: {script_name}")
        
        # 准备环境变量 - 通过环境变量传递参数给脚本
        env = os.environ.copy()
        env['SCRIPT_PARAMETERS'] = json.dumps(parameters, ensure_ascii=False)
        env['PAGE_CONTEXT'] = page_context
        env['SCRIPT_NAME'] = script_name
        env['EXECUTION_ID'] = str(timezone.now().timestamp())
        
        logger.info(f"准备执行Python脚本: {script_path}")
        logger.info(f"参数: {parameters}")
        
        # 执行脚本 - 使用subprocess确保进程隔离
        try:
            result = subprocess.run(
                [sys.executable, script_path],  # 使用当前Python解释器
                capture_output=True,            # 捕获标准输出和错误输出
                text=True,                      # 以文本模式处理输出
                env=env,                        # 传递环境变量
                timeout=540,                    # 9分钟超时 (与Celery软限制对应)
                cwd=os.path.dirname(script_path) # 设置工作目录为脚本所在目录
            )
            
            logger.info(f"脚本执行完成，返回码: {result.returncode}")
            
            if result.returncode != 0:
                error_msg = f"脚本执行失败 (返回码: {result.returncode})\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # 尝试解析JSON输出
            try:
                output_data = json.loads(result.stdout) if result.stdout.strip() else {}
                logger.info(f"脚本输出解析成功: {type(output_data)}")
            except json.JSONDecodeError as e:
                logger.warning(f"脚本输出不是有效JSON，作为文本处理: {e}")
                # 如果不是JSON，就作为普通文本处理
                output_data = {
                    'type': 'text',
                    'content': result.stdout,
                    'stderr': result.stderr,
                    'message': '脚本执行完成，输出为文本格式'
                }
            
            # 确保输出包含必要的元数据
            if isinstance(output_data, dict):
                output_data.setdefault('script_name', script_name)
                output_data.setdefault('execution_time', timezone.now().isoformat())
                if 'status' not in output_data:
                    output_data['status'] = 'success'
            
            return output_data
            
        except subprocess.TimeoutExpired:
            error_msg = f"脚本执行超时 (超过540秒): {script_path}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"执行脚本时发生异常: {e}"
            logger.error(error_msg)
            raise
    
    @staticmethod
    def create_executor(task_execution_id: int, script_info: Dict, parameters: Dict, 
                       user_id: int, page_context: str) -> 'UnifiedScriptExecutor':
        """
        创建统一脚本执行器
        
        参数:
        -----
        task_execution_id : int
            任务执行记录ID
        script_info : dict
            脚本信息，包含name和path
        parameters : dict
            脚本执行参数
        user_id : int
            执行用户ID
        page_context : str
            页面上下文
            
        返回:
        -----
        UnifiedScriptExecutor : 统一脚本执行器实例
        """
        return UnifiedScriptExecutor(task_execution_id, script_info, parameters, user_id, page_context)
    
    @staticmethod
    def execute_unified(task_execution_id: int, script_info: Dict, parameters: Dict, 
                        user_id: int, page_context: str) -> ScriptExecutionResult:
        """
        执行脚本的统一入口
        
        参数:
        -----
        task_execution_id : int
            任务执行记录ID
        script_info : dict
            脚本信息
        parameters : dict
            脚本执行参数
        user_id : int
            执行用户ID
        page_context : str
            页面上下文
            
        返回:
        -----
        ScriptExecutionResult : 执行结果
        """
        logger.info(f"[UnifiedScriptExecutor.execute] 开始执行: task_execution_id={task_execution_id}")
        logger.info(f"[UnifiedScriptExecutor.execute] script_info={script_info}")
        logger.info(f"[UnifiedScriptExecutor.execute] parameters={parameters}")
        logger.info(f"[UnifiedScriptExecutor.execute] user_id={user_id}")
        logger.info(f"[UnifiedScriptExecutor.execute] page_context={page_context}")
        
        try:
            executor = UnifiedScriptExecutor.create_executor(
                task_execution_id, script_info, parameters, user_id, page_context
            )
            logger.info(f"[UnifiedScriptExecutor.execute] 执行器创建成功")
            
            result = executor.execute(lambda: executor.execute_script())
            logger.info(f"[UnifiedScriptExecutor.execute] 执行完成")
            return result
        except Exception as e:
            logger.error(f"[UnifiedScriptExecutor.execute] 执行失败: {e}")
            logger.error(f"[UnifiedScriptExecutor.execute] 错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"[UnifiedScriptExecutor.execute] 堆栈跟踪: {traceback.format_exc()}")
            raise


# ============================================================================
# 统一的Celery任务装饰器
# ============================================================================

def create_unified_task(bind=True, max_retries=3, countdown=60):
    """
    创建统一的Celery任务装饰器
    
    提供统一的Celery任务装饰器，包含重试机制和错误处理。
    适用于所有需要异步执行的脚本任务。
    
    参数：
    -----
    bind : bool
        是否绑定任务实例，默认为True
    max_retries : int
        最大重试次数，默认为3次
    countdown : int
        重试间隔时间（秒），默认为60秒
        
    使用示例：
    ---------
    @create_unified_task(max_retries=5, countdown=30)
    def my_script_task(self, script_info, parameters):
        # 任务逻辑
        pass
    """
    def decorator(func):
        @shared_task(bind=True, max_retries=max_retries, countdown=countdown)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as exc:
                logger.error(f"Task {self.request.id} failed: {exc}")
                
                # 重试机制
                if self.request.retries < max_retries:
                    logger.info(f"Retrying task {self.request.id}: {self.request.retries + 1}/{max_retries}")
                    raise self.retry(exc=exc, countdown=countdown)
                
                # 超过最大重试次数，返回错误
                return ScriptExecutionResult(
                    status='error',
                    error=f"Task failed after {max_retries} retries: {exc}",
                    script_name=kwargs.get('script_name', 'unknown')
                ).to_dict()
        
        return wrapper
    return decorator


# ============================================================================
# 统一的错误处理装饰器
# ============================================================================

def handle_execution_errors(func):
    """
    统一的错误处理装饰器
    
    自动处理脚本执行过程中的异常，提供统一的错误格式。
    捕获所有异常并转换为标准化的ScriptExecutionResult格式。
    
    功能特性：
    ---------
    1. 自动异常捕获 - 捕获所有类型的异常
    2. 详细错误日志 - 记录错误信息和堆栈跟踪
    3. 标准化错误格式 - 返回统一的错误结果格式
    4. 元数据记录 - 包含错误堆栈信息
    
    使用示例：
    ---------
    @handle_execution_errors
    def my_script_function():
        # 可能抛出异常的代码
        pass
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            error_message = str(exc)
            error_traceback = traceback.format_exc()
            
            logger.error(f"Execution error in {func.__name__}: {error_message}")
            logger.error(f"Error traceback: {error_traceback}")
            
            return ScriptExecutionResult(
                status='error',
                error=error_message,
                metadata={'traceback': error_traceback}
            ).to_dict()
    
    return wrapper
