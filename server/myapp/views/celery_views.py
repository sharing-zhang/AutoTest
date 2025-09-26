"""
AutoTest Celery任务和视图管理系统
=====================================

本模块整合了Celery任务执行器和Django REST API接口，提供完整的异步任务处理能力。

主要功能：
----------
1. 统一脚本执行器 (execute_script_task)
   - 支持所有类型的脚本执行
   - 完整的错误处理和重试机制
   - 资源监控和性能统计

2. DRF ViewSets
   - ScriptViewSet: 脚本管理
   - PageScriptConfigViewSet: 页面脚本配置
   - TaskExecutionViewSet: 任务执行记录

3. REST API接口
   - 脚本执行API
   - 任务状态查询API
   - 脚本配置管理API

架构设计：
----------
- 采用统一执行器架构
- 支持subprocess进程隔离
- 完整的任务生命周期管理
- 与Django ORM深度集成

使用场景：
----------
- 前端页面脚本按钮执行
- 动态脚本参数配置
- 批量任务处理
- 系统监控和日志
"""
# ============================================================================
# 导入依赖库
# ============================================================================

# Django核心模块 - Web框架基础组件
from django.http import JsonResponse                 
from django.views.decorators.csrf import csrf_exempt    # CSRF豁免装饰器
from django.utils.decorators import method_decorator    
from django.views.decorators.http import require_http_methods  
from django.utils import timezone                      
from django.conf import settings                        
from django.shortcuts import get_object_or_404        

# Django REST Framework - API框架组件
from rest_framework import viewsets, status            
from rest_framework.decorators import action, api_view, authentication_classes  
from rest_framework.response import Response           
from rest_framework.permissions import IsAuthenticated  # 认证权限

# Celery异步任务框架 - 分布式任务队列
from celery import shared_task
from celery.utils.log import get_task_logger         
from celery.result import AsyncResult

# Python标准库 - 系统级功能
import logging                                     
import json                                            
import subprocess                                    
import os                                           
import sys                                          
import traceback                                        
import signal                                           
import psutil                                           

# 项目内部模块 - 自定义业务逻辑
from ..models import Script, TaskExecution, PageScriptConfig, ScanDevUpdate_scanResult  # 数据模型
from ..serializers import ScriptSerializer, TaskExecutionSerializer, PageScriptConfigSerializer  # 序列化器
from ..management.commands.script_config_manager import script_config_manager  # 脚本配置管理器
from ..auth.authentication import AdminTokenAuthtication  # 管理员认证

# 获取Celery任务日志
logger = get_task_logger(__name__)

# ============================================================================
# 统一任务执行器 - 核心异步任务处理
# ============================================================================
# 
# 本模块包含Celery异步任务执行的核心逻辑，负责：
# 1. 脚本文件的执行和进程管理
# 2. 任务状态跟踪和错误处理
# 3. 资源监控和性能统计
# 4. 与数据库的集成和结果保存
#
# 设计特点：
# - 支持所有类型的脚本（Python、Shell、批处理等）
# - 完整的错误处理和重试机制
# - 进程隔离和资源监控
# - 与Django ORM深度集成
# ============================================================================

from celery_app.celery import app as celery_app

@celery_app.task(bind=True)
def execute_script_task(self, task_execution_id, script_info, parameters, user_id, page_context):
    """
    统一脚本执行器 - Celery异步任务的核心执行函数
    
    这是整个脚本执行系统的核心组件，负责在后台异步执行各种类型的脚本。
    支持Python脚本、Shell脚本、批处理文件等多种格式。
    
    参数说明:
    ---------
    task_execution_id : int
        任务执行记录ID，用于关联数据库中的TaskExecution记录
    script_info : dict
        脚本信息字典，包含：
        - name: 脚本名称
        - path: 脚本文件路径
        - id: 脚本数据库ID（可选）
    parameters : dict
        脚本执行参数，由前端传递的动态参数
    user_id : int
        执行用户ID，用于权限控制和数据隔离
    page_context : str
        页面上下文，标识脚本调用的来源页面
        
    返回结果:
    ---------
    dict : 执行结果字典
        - status: 执行状态 ('success'/'error')
        - result: 执行结果数据（成功时）
        - error: 错误信息（失败时）
        - execution_time: 执行时间（秒）
        - memory_usage: 内存使用量（MB）
        
    执行流程:
    ---------
    1. 导入统一脚本执行器 (UnifiedScriptExecutor)
    2. 调用执行器的统一执行方法
    3. 处理执行结果和异常
    4. 实现重试机制（最多x次）
    5. 返回标准化的结果格式
        
    异常处理:
    ---------
    - 自动重试机制：失败时最多重试x次，每次间隔xx秒
    - 详细错误日志：记录完整的异常堆栈信息
    - 优雅降级：重试失败后返回错误结果而非崩溃
        
    使用场景:
    ---------
    - 前端脚本按钮点击执行
    - 定时任务调度
    - 批量数据处理
    - 系统监控和维护
    """
    from .script_executor_base import UnifiedScriptExecutor
    from myapp.models import TaskExecution
    
    logger.info(f"开始执行脚本: task_id={self.request.id}, script={script_info.get('name', 'unknown')}")
    
    # 检查任务是否已经执行过（防止重复执行）
    try:
        task_execution = TaskExecution.objects.get(id=task_execution_id)
        if task_execution.status in ['SUCCESS', 'FAILURE']:
            logger.warning(f"任务 {task_execution_id} 已经执行过，状态: {task_execution.status}，跳过重复执行")
            return {
                'status': 'skipped',
                'message': f'任务已执行过，状态: {task_execution.status}',
                'script_name': script_info.get('name', 'unknown')
            }
    except TaskExecution.DoesNotExist:
        logger.error(f"任务执行记录 {task_execution_id} 不存在")
        return {
            'status': 'error',
            'error': f'任务执行记录 {task_execution_id} 不存在',
            'script_name': script_info.get('name', 'unknown')
        }
    
    try:
        # 使用统一执行器
        result = UnifiedScriptExecutor.execute_unified(
            task_execution_id,
            script_info,
            parameters,
            user_id,
            page_context
        )
        
        return result.to_dict()
        
    except Exception as exc:
        logger.error(f"脚本执行失败: {exc}")
        
        # 重试机制
        if self.request.retries < 3:
            logger.info(f"任务重试: 第 {self.request.retries + 1} 次")
            raise self.retry(exc=exc, countdown=60, max_retries=3)
        
        # 返回错误结果
        return {
            'status': 'error',
            'error': str(exc),
            'script_name': script_info.get('name', 'unknown')
        }

# ============================================================================
# Django REST Framework ViewSets - API视图集
# ============================================================================
#
# 本模块包含Django REST Framework的ViewSet类，提供RESTful API接口：
# 1. ScriptViewSet: 脚本管理API（CRUD操作）
# 2. PageScriptConfigViewSet: 页面脚本配置API（只读）
# 3. TaskExecutionViewSet: 任务执行记录API（查询和取消）
#
# 设计特点：
# - 遵循RESTful API设计原则
# - 完整的权限控制和数据隔离
# - 自动化的序列化和反序列化
# - 标准化的错误处理和响应格式
#
# 认证机制：
# - ScriptViewSet: 管理员认证 (AdminTokenAuthtication)
# - PageScriptConfigViewSet: 用户认证 (IsAuthenticated)
# - TaskExecutionViewSet: 用户认证 (IsAuthenticated)
# ============================================================================

class ScriptViewSet(viewsets.ModelViewSet):
    """
    脚本管理ViewSet - 脚本资源的完整CRUD操作
    
    提供脚本管理的完整RESTful API接口，支持脚本的创建、读取、更新和删除操作。
    主要用于管理员对系统中可用脚本的管理和维护。
    
    API端点:
    --------
    - GET    /api/scripts/           - 获取脚本列表（支持分页和过滤）
    - POST   /api/scripts/           - 创建新脚本
    - GET    /api/scripts/{id}/      - 获取指定脚本的详细信息
    - PUT    /api/scripts/{id}/      - 完整更新脚本信息
    - PATCH  /api/scripts/{id}/      - 部分更新脚本信息
    - DELETE /api/scripts/{id}/      - 删除脚本（软删除）
    
    权限控制:
    --------
    - 认证方式: AdminTokenAuthtication（管理员Token认证）
    - 权限要求: 需要管理员权限
    - 数据隔离: 所有管理员共享脚本资源
    
    数据模型:
    --------
    - 基础模型: Script（脚本信息表）
    - 过滤条件: is_active=True（只显示激活的脚本）
    - 序列化器: ScriptSerializer（自动序列化/反序列化）
    
    特殊功能:
    --------
    - 自定义list方法: 返回前端兼容的脚本列表格式
    - 自动任务生成: 为每个脚本自动生成默认任务配置
    - 执行方法标识: 标记使用统一执行器架构
    
    使用场景:
    --------
    - 管理员添加新的脚本文件
    - 更新脚本的描述和配置信息
    - 启用/禁用特定脚本
    - 查看脚本的执行历史和统计
    """
    queryset = Script.objects.filter(is_active=True)
    serializer_class = ScriptSerializer
    authentication_classes = [AdminTokenAuthtication]
    permission_classes = []  # 使用自定义认证，不需要额外权限检查
    
    def list(self, request):
        """
        获取脚本列表 - 自定义格式以兼容前端
        """
        page_route = request.query_params.get('page_route')
        script_type = request.query_params.get('script_type')
        
        scripts_query = Script.objects.filter(is_active=True)
        
        if script_type:
            scripts_query = scripts_query.filter(script_type=script_type)
        
        scripts = []
        for script in scripts_query:
            script_data = {
                'id': script.id,
                'name': script.name,
                'description': script.description,
                'script_type': script.script_type,
                'script_path': script.script_path,
                'parameters_schema': script.parameters_schema,
                'created_at': script.created_at.isoformat(),
                'tasks': []
            }
            
            # 每个脚本有一个"统一执行任务"
            script_data['tasks'].append({
                'name': 'unified_execution',
                'full_name': f'统一执行器.{script.name}',
                'parameters': script.parameters_schema or {},
                'description': f'通过统一执行器运行 {script.name}'
            })
            
            scripts.append(script_data)
        
        return Response({
            'success': True,
            'scripts': scripts,
            'execution_method': 'scheme_1_unified_executor'
        })
    
    def get_permissions(self):
        """
        根据不同的action返回不同的权限
        list方法不需要认证，其他方法需要管理员认证
        """
        if self.action == 'list':
            return []  # 列表方法不需要认证
        return [AdminTokenAuthtication()]  # 其他方法需要管理员认证

class PageScriptConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """
    页面脚本配置ViewSet - 页面脚本配置的只读API
    
    提供页面脚本配置的查询操作，用于前端获取特定页面的脚本按钮配置信息。
    支持按页面路由过滤，返回该页面可用的脚本按钮列表。
    
    API端点:
    --------
    - GET /api/page-script-configs/                    - 获取所有页面配置
    - GET /api/page-script-configs/?page_route=xxx     - 获取特定页面的配置
    - GET /api/page-script-configs/{id}/               - 获取指定配置的详细信息
    
    查询参数:
    --------
    page_route : str (可选)
        页面路由，用于筛选特定页面的配置
        例如: /scanDevUpdate, /scanUpdate, /thing 等
        如果不提供，返回所有启用的配置
    
    权限控制:
    --------
    - 认证方式: 无认证要求（公开接口）
    - 权限要求: 无需登录即可访问
    - 数据隔离: 所有用户共享配置资源
    
    数据模型:
    --------
    - 基础模型: PageScriptConfig（页面脚本配置表）
    - 过滤条件: is_enabled=True（只显示启用的配置）
    - 排序规则: display_order（按显示顺序排序）
    - 序列化器: PageScriptConfigSerializer
    
    返回数据格式:
    ------------
    每个配置项包含：
    - script_id: 关联的脚本ID
    - button_text: 按钮显示文本
    - button_style: 按钮样式配置
    - position: 按钮位置（top-left, top-right等）
    - display_order: 显示顺序
    - dialog_title: 参数弹窗标题
    
    使用场景:
    --------
    - 前端页面加载时获取脚本按钮配置
    - 动态生成页面上的脚本执行按钮
    - 根据用户权限过滤可用脚本
    - 支持多页面共享脚本配置
    """
    serializer_class = PageScriptConfigSerializer
    permission_classes = []  # 页面配置是公开的，不需要认证
    
    def get_queryset(self):
        """根据查询参数返回相应的页面脚本配置"""
        page_route = self.request.query_params.get('page_route')
        if page_route:
            # 返回特定页面的配置，按显示顺序排序
            return PageScriptConfig.objects.filter(
                page_route=page_route, 
                is_enabled=True
            ).order_by('display_order')
        # 返回所有启用的配置
        return PageScriptConfig.objects.filter(is_enabled=True)

class TaskExecutionViewSet(viewsets.ModelViewSet):
    """
    任务执行记录ViewSet - 任务执行历史的管理和查询
    
    提供任务执行记录的完整管理功能，包括查询历史记录、监控任务状态、
    取消正在执行的任务等操作。所有操作都基于用户权限进行数据隔离。
    
    API端点:
    --------
    - GET    /api/task-executions/                      - 获取当前用户的任务执行记录
    - GET    /api/task-executions/{id}/                 - 获取指定任务的详细信息
    - GET    /api/task-executions/task_status/          - 查询任务状态（支持多种查询方式）
    - POST   /api/task-executions/{id}/cancel_task/     - 取消正在执行的任务
    
    权限控制:
    --------
    - 认证方式: IsAuthenticated（用户认证）
    - 权限要求: 需要用户登录
    - 数据隔离: 只能访问当前用户的任务记录
    - 安全机制: 自动过滤用户数据，防止越权访问
    
    数据模型:
    --------
    - 基础模型: TaskExecution（任务执行记录表）
    - 关联模型: Script（脚本信息）、User（用户信息）
    - 过滤条件: user=request.user（用户数据隔离）
    - 序列化器: TaskExecutionSerializer
    
    特殊功能:
    --------
    - task_status: 支持通过task_id或execution_id查询任务状态
    - cancel_task: 安全的任务取消机制，支持进程终止
    - 状态同步: 自动同步Celery状态到数据库
    - 实时监控: 提供任务执行的实时状态更新
    
    任务状态:
    --------
    - PENDING: 任务已创建，等待执行
    - STARTED: 任务正在执行中
    - SUCCESS: 任务执行成功
    - FAILURE: 任务执行失败
    - REVOKED: 任务已被取消
    
    使用场景:
    --------
    - 用户查看自己的任务执行历史
    - 监控长时间运行的任务状态
    - 取消误操作或不需要的任务
    - 任务执行结果的查看和分析
    """
    serializer_class = TaskExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """返回当前用户的任务执行记录"""
        return TaskExecution.objects.filter(user=self.request.user)
    
    
@action(detail=False, methods=['get'])
def task_status(self, request):
    """
    查询任务状态 - 支持多种查询方式
    
    提供灵活的任务状态查询接口，支持：
    1. 通过Celery任务ID查询
    2. 通过任务执行记录ID查询
    3. 自动同步Celery状态到数据库
    4. 实时状态更新
    
    查询参数:
    --------
    task_id : str (可选)
        Celery任务ID，用于查询异步任务状态
    execution_id : int (可选)
        任务执行记录ID，用于查询数据库记录
        
    注意: task_id 和 execution_id 至少需要提供一个
    
    返回:
    -----
    Response : 任务状态信息
        - id: 任务执行记录ID
        - task_id: Celery任务ID
        - status: 任务状态 (PENDING/STARTED/SUCCESS/FAILURE/REVOKED)
        - result: 任务结果（成功时）
        - error_message: 错误信息（失败时）
        - created_at: 创建时间
        - execution_time: 执行时间
    """
    task_id = request.query_params.get('task_id')
    execution_id = request.query_params.get('execution_id')
    
    if execution_id:
        # 通过执行记录ID查询
        task_execution = get_object_or_404(TaskExecution, id=execution_id, user=request.user)
        return Response(self.get_serializer(task_execution).data)
    elif task_id:
        # 通过Celery任务ID查询
        celery_result = AsyncResult(task_id)
        task_execution = get_object_or_404(TaskExecution, task_id=task_id, user=request.user)
        
        # 同步Celery状态到数据库
        if celery_result.ready() and task_execution.status in ['PENDING', 'STARTED']:
            if celery_result.successful():
                task_execution.status = 'SUCCESS'
                task_execution.result = celery_result.result
            else:
                task_execution.status = 'FAILURE'
                task_execution.error_message = str(celery_result.result)
            task_execution.save()
        
        return Response(self.get_serializer(task_execution).data)
    else:
        return Response({'error': '缺少task_id或execution_id参数'}, status=400)
    
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def cancel_task(request, execution_id):
    """
    取消任务 - 安全的任务终止机制
    
    提供任务取消功能，支持：
    1. 检查任务状态是否可取消
    2. 终止Celery异步任务
    3. 更新数据库状态为已取消
    4. 防止重复取消
    
    可取消状态:
    ----------
    - PENDING: 任务等待执行
    - STARTED: 任务正在执行
    
    不可取消状态:
    ------------
    - SUCCESS: 任务已成功完成
    - FAILURE: 任务已失败
    - REVOKED: 任务已被取消
    
    参数:
    -----
    execution_id : int
        任务执行记录的主键ID
        
    返回:
    -----
    Response : 取消结果
        - message: 取消成功消息
        - error: 取消失败原因（如果适用）
    """
    try:
        # 获取任务执行记录
        task_execution = TaskExecution.objects.get(id=execution_id, user=request.user)
        
        if task_execution.status in ['PENDING', 'STARTED']:
            # 取消Celery任务
            celery_task = AsyncResult(task_execution.task_id)
            
            # 检查任务状态
            if celery_task.state in ['PENDING', 'STARTED']:
                # 尝试取消任务（Windows threads池下使用温和取消）
                try:
                    # 先尝试温和取消
                    celery_task.revoke(terminate=False)
                    logger.info(f'任务 {task_execution.task_id} 已发送取消信号（温和模式）')
                    
                    # 如果是PENDING状态，尝试强制终止
                    if celery_task.state == 'PENDING':
                        try:
                            celery_task.revoke(terminate=True)
                            logger.info(f'任务 {task_execution.task_id} 已发送强制终止信号')
                        except Exception as terminate_error:
                            logger.warning(f'强制终止失败（threads池不支持）: {str(terminate_error)}')
                            
                except Exception as revoke_error:
                    logger.warning(f'取消任务失败: {str(revoke_error)}')
                    # 即使取消失败，也标记为已取消
                
                # 更新状态
                task_execution.status = 'REVOKED'
                task_execution.save()
                
                return Response({'message': '任务已取消'})
            else:
                # 任务已经完成，更新状态
                task_execution.status = 'REVOKED'
                task_execution.save()
                return Response({'message': '任务已标记为取消'})
        else:
            return Response({'error': '任务无法取消'}, status=400)
    except TaskExecution.DoesNotExist:
        return Response({'error': '任务不存在'}, status=404)
    except Exception as e:
        logger.error(f'取消任务失败: {str(e)}')
        return Response({'error': '取消任务失败'}, status=500)

# execute_script 方法已移至 ScriptExecutionViewSet

class ScriptExecutionViewSet(viewsets.ViewSet):
    """
    脚本执行ViewSet - 专门处理脚本执行相关操作
    
    职责：
    - 脚本执行
    - 执行状态查询
    - 执行结果获取
    
    设计原则：
    - 专注于脚本执行逻辑
    - 不管理TaskExecution记录的CRUD
    - 提供统一的脚本执行接口
    """
    authentication_classes = [AdminTokenAuthtication]  # 支持管理员认证
    permission_classes = []  # 脚本执行是公开的，不需要权限检查
    
    @action(detail=False, methods=['post'])
    def execute(self, request):
        """
        执行脚本 - 统一脚本执行接口
        
        这是整个脚本执行系统的统一入口，前端通过此接口执行各种类型的脚本。
        支持传统脚本、动态脚本、自定义脚本等多种执行方式。
        
        请求参数:
        --------
        script_id : int (可选)
            脚本的数据库ID，用于已注册的传统脚本
            优先级最高，如果提供则忽略其他参数
        script_name : str (可选)
            脚本名称，用于动态脚本或未注册的脚本
            系统会根据名称自动构建脚本路径
        script_path : str (可选)
            脚本文件路径，如果提供则直接使用
            用于自定义脚本或特殊路径的脚本
        parameters : dict
            脚本执行参数，由前端传递的动态参数
            支持各种数据类型：字符串、数字、布尔值、数组等
        page_context : str
            页面上下文，标识脚本调用的来源页面
            用于日志记录和权限控制
            
        返回结果:
        --------
        Response : 执行结果JSON响应
            - success: bool - 是否成功启动任务
            - task_id: str - Celery任务ID，用于状态查询
            - execution_id: int - 任务执行记录ID
            - script_name: str - 脚本名称
            - message: str - 执行消息
            - error: str - 错误信息（失败时）
        """
        print("=== ScriptExecutionViewSet.execute 方法被调用 ===")
        try:
            logger.info(f"ScriptExecutionViewSet.execute 开始处理请求")
            print("=== 开始处理请求 ===")
            data = request.data
            logger.info(f"请求数据: {data}")
            
            script_id = data.get('script_id')
            script_name = data.get('script_name')
            script_path = data.get('script_path')
            parameters = data.get('parameters', {})
            page_context = data.get('page_context', 'api')
            
            logger.info(f"解析参数: script_name={script_name}, script_path={script_path}, page_context={page_context}")
            
            # 确定脚本信息
            script_info = None
            
            if script_id:
                # 从数据库获取脚本信息
                try:
                    script = Script.objects.get(id=script_id, is_active=True)
                    script_info = {
                        'id': script.id,
                        'name': script.name,
                        'path': script.script_path
                    }
                except Script.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': '脚本不存在或已禁用'
                    }, status=404)
            elif script_name and script_path:
                # 直接使用提供的脚本信息
                script_info = {
                    'name': script_name,
                    'path': script_path
                }
            elif script_name:
                # 根据脚本名称构建路径
                import os
                from django.conf import settings
                script_path = os.path.join(settings.BASE_DIR, 'celery_app', f'{script_name}.py')
                script_info = {
                    'name': script_name,
                    'path': script_path
                }
            else:
                return Response({
                    'success': False,
                    'error': '必须提供script_id、script_name或script_path'
                }, status=400)
            
            # 验证脚本文件是否存在
            if not os.path.exists(script_info['path']):
                return Response({
                    'success': False,
                    'error': f'脚本文件不存在: {script_info["path"]}'
                }, status=404)
            
            # 创建或获取Script记录
            script_obj, created = Script.objects.get_or_create(
                name=script_info['name'],
                defaults={
                    'script_path': script_info['path'],
                    'script_type': 'python',
                    'description': f'动态脚本: {script_info["name"]}',
                    'is_active': True
                }
            )
            
            # 创建TaskExecution记录
            logger.info(f"创建TaskExecution记录")
            import uuid
            temp_task_id = f"temp_{uuid.uuid4().hex[:8]}"  # 生成临时唯一ID
            task_execution = TaskExecution.objects.create(
                script=script_obj,
                user=request.user,
                parameters=parameters,
                page_context=page_context,
                status='PENDING',
                task_id=temp_task_id  # 使用临时ID
            )
            logger.info(f"TaskExecution创建成功: ID={task_execution.id}, temp_task_id={temp_task_id}")
            
            # 启动Celery任务
            logger.info(f"准备启动Celery任务")
            logger.info(f"任务参数: task_execution_id={task_execution.id}, script_info={script_info}")
            
            # 检查任务函数是否可用
            logger.info(f"execute_script_task函数: {execute_script_task}")
            logger.info(f"execute_script_task类型: {type(execute_script_task)}")
            
            try:
                # 使用Celery异步执行
                logger.info("启动Celery异步任务...")
                task = execute_script_task.delay(
                    task_execution.id,
                    script_info,
                    parameters,
                    request.user.id,
                    page_context
                )
                logger.info(f"Celery任务启动成功: task_id={task.id}")
                
            except Exception as task_error:
                logger.error(f"Celery任务启动失败: {str(task_error)}")
                import traceback
                logger.error(f"任务启动错误堆栈: {traceback.format_exc()}")
                raise task_error
            
            # 更新任务ID
            task_execution.task_id = task.id
            task_execution.save()
            logger.info(f"TaskExecution更新完成")
            
            return Response({
                'success': True,
                'task_id': task.id,
                'execution_id': task_execution.id,
                'script_name': script_info['name'],
                'message': '脚本执行已启动'
            })
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"=== 异常发生 ===")
            print(f"错误: {str(e)}")
            print(f"类型: {type(e).__name__}")
            print(f"堆栈: {error_traceback}")
            print(f"===============")
            
            logger.error(f'脚本执行失败: {str(e)}')
            logger.error(f'错误堆栈: {error_traceback}')
            return Response({
                'success': False,
                'error': f'脚本执行失败: {str(e)}',
                'traceback': error_traceback
            }, status=500)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        查询任务状态 - 支持多种查询方式
        
        提供灵活的任务状态查询接口，支持：
        1. 通过Celery任务ID查询
        2. 通过任务执行记录ID查询
        3. 自动同步Celery状态到数据库
        4. 实时状态更新
        
        查询参数:
        --------
        task_id : str (可选)
            Celery任务ID，用于查询异步任务状态
        execution_id : int (可选)
            任务执行记录ID，用于查询数据库记录
            
        注意: task_id 和 execution_id 至少需要提供一个
        
        返回:
        -----
        Response : 任务状态信息
            - id: 任务执行记录ID
            - task_id: Celery任务ID
            - status: 任务状态 (PENDING/STARTED/SUCCESS/FAILURE/REVOKED)
            - result: 任务结果（成功时）
            - error_message: 错误信息（失败时）
            - created_at: 创建时间
            - execution_time: 执行时间
        """
        task_id = request.query_params.get('task_id')
        execution_id = request.query_params.get('execution_id')
        
        if execution_id:
            # 通过执行记录ID查询
            task_execution = get_object_or_404(TaskExecution, id=execution_id, user=request.user)
            serializer = TaskExecutionSerializer(task_execution)
            data = serializer.data
            
            # 添加前端需要的字段
            if task_execution.task_id:
                celery_result = AsyncResult(task_execution.task_id)
                data['ready'] = celery_result.ready()
                data['success'] = celery_result.successful() if celery_result.ready() else None
            else:
                data['ready'] = task_execution.status in ['SUCCESS', 'FAILURE', 'REVOKED']
                data['success'] = task_execution.status == 'SUCCESS'
            
            return Response(data)
        elif task_id:
            # 通过Celery任务ID查询
            celery_result = AsyncResult(task_id)
            task_execution = get_object_or_404(TaskExecution, task_id=task_id, user=request.user)
            
            # 同步Celery状态到数据库
            if celery_result.ready() and task_execution.status in ['PENDING', 'STARTED']:
                if celery_result.successful():
                    task_execution.status = 'SUCCESS'
                    task_execution.result = celery_result.result
                else:
                    task_execution.status = 'FAILURE'
                    task_execution.error_message = str(celery_result.result)
                task_execution.save()
            
            serializer = TaskExecutionSerializer(task_execution)
            data = serializer.data
            
            # 添加前端需要的字段
            data['ready'] = celery_result.ready()
            data['success'] = celery_result.successful() if celery_result.ready() else None
            
            return Response(data)
        else:
            return Response({'error': '缺少task_id或execution_id参数'}, status=400)

# ============================================================================
#
# 本模块包含统一的脚本执行API接口，作为前端调用的主要入口：
# 1. get_script_configs: 脚本配置查询接口
# 2. reload_script_configs: 配置热更新接口
#
# 设计特点：
# - 统一的参数格式和响应格式
# - 完整的错误处理和验证
# - 支持多种脚本类型和执行方式
# - 与Celery异步任务深度集成
# ============================================================================
# 动态脚本配置管理 API
# ============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def get_script_configs(request):
    """
    获取脚本配置信息API - 动态脚本参数管理
    
    提供动态脚本的参数配置查询功能，支持获取单个脚本的详细配置
    或所有可用脚本的列表信息。主要用于前端动态生成脚本参数表单。
    
    查询参数:
    --------
    script_name : str (可选)
        指定脚本名称，获取该脚本的详细参数配置
        格式: 脚本文件名（不含.py后缀），如 "scanner_file"
        如果不提供，则返回所有脚本的列表信息
        
    返回格式:
    --------
    单个脚本配置响应:
    {
        "success": true,
        "script_config": {
            "dialog_title": "脚本参数配置",
            "parameters": [
                {
                    "name": "page",
                    "type": "number",
                    "default": 1,
                    "required": true,
                    "description": "页码"
                }
            ],
            "visualization": {...}
        }
    }
    
    所有脚本列表响应:
    {
        "success": true,
        "scripts": [
            {
                "script_name": "scanner_file",
                "display_name": "Scanner File",
                "parameter_count": 3,
                "has_required_params": true
            }
        ],
        "total_count": 5
    }
    
    参数配置说明:
    ------------
    每个参数配置包含：
    - name: 参数名称
    - type: 参数类型 (string/number/boolean)
    - default: 默认值
    - required: 是否必填
    - description: 参数描述
    - validation: 验证规则
    
    异常处理:
    --------
    - 脚本不存在：返回成功但配置为空
    - 配置解析失败：返回500错误
    - 参数格式错误：返回400错误
        
    使用场景:
    --------
    - 前端动态生成脚本参数表单
    - 脚本参数验证和类型检查
    - 脚本列表展示和选择
    - 参数配置的实时预览
    """
    try:
        script_name = request.GET.get('script_name')
        
        if script_name:
            # 获取单个脚本配置
            config = script_config_manager.get_parameter_schema(script_name)
            return JsonResponse({
                'success': True,
                'script_config': config
            })
        else:
            # 获取所有脚本列表
            all_scripts = script_config_manager.get_all_scripts()
            scripts_info = []
            
            for script in all_scripts:
                config = script_config_manager.get_script_config(script)
                scripts_info.append({
                    'script_name': script,
                    'display_name': script.replace('.py', '').replace('_', ' ').title(),
                    'parameter_count': len(config),
                    'has_required_params': any(p.get('required', False) for p in config)
                })
            
            return JsonResponse({
                'success': True,
                'scripts': scripts_info,
                'total_count': len(scripts_info)
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '获取脚本配置失败'
        }, status=500)


@csrf_exempt  
@require_http_methods(["POST"])
def reload_script_configs(request):
    """
    重新加载脚本配置API - 配置热更新
    
    提供脚本配置的热更新功能，无需重启服务即可更新脚本参数配置。
    主要用于开发环境和生产环境的配置管理，支持实时配置更新。
    
    请求参数:
    --------
    无特殊参数要求，发送POST请求即可触发重新加载
    请求体可以为空或包含配置更新信息
        
    返回格式:
    --------
    成功响应:
    {
        "success": true,
        "message": "脚本配置已重新加载",
        "total_scripts": 5,
        "scripts": ["script1", "script2", "script3"]
    }
    
    失败响应:
    {
        "success": false,
        "error": "配置加载失败",
        "message": "具体错误信息"
    }
    
    功能说明:
    --------
    - 重新读取script_configs.json配置文件
    - 更新内存中的配置缓存
    - 验证配置格式正确性
    - 刷新脚本参数定义和验证规则
    - 更新脚本元数据和显示信息
    - 清理过期的配置缓存
    
    执行流程:
    --------
    1. 调用脚本配置管理器重新加载
    2. 扫描和解析配置文件
    3. 验证配置格式和完整性
    4. 更新内存缓存
    5. 返回加载结果统计
        
    异常处理:
    --------
    - 配置文件不存在：返回错误信息
    - 配置格式错误：返回详细错误信息
    - 文件访问失败：记录错误日志
    - 系统异常：返回500错误
        
    使用场景:
    --------
    - 开发环境配置调试和测试
    - 生产环境配置更新和维护
    - 脚本参数修改后的热更新
    - 系统维护和配置管理
    - CI/CD流水线中的配置部署
    """

    try:
        # 重新加载当前进程的配置
        script_config_manager.reload_config()
        
        # 如果使用Celery，还需要通知所有worker进程
        from celery import current_app
        current_app.control.broadcast('reload_script_configs')
        
        return JsonResponse({
            'success': True,
            'message': '脚本配置已重新加载',
            'total_scripts': len(script_config_manager.get_all_scripts())
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '重新加载脚本配置失败'
        }, status=500)