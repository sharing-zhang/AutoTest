"""
方案1 - 统一的Celery任务和视图管理
整合了任务执行器和API接口，简化代码结构
"""
from rest_framework.decorators import api_view
from rest_framework import status
import logging
import json
import subprocess
import os
import sys
import traceback
import signal
import psutil
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings

# DRF相关导入
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

# Celery相关导入
from celery import shared_task
from celery.utils.log import get_task_logger
from celery.result import AsyncResult
from celery_app.celery import app as celery_app

# 模型和序列化器
from ..models import Script, TaskExecution, PageScriptConfig, ScanDevUpdate_scanResult
from ..serializers import ScriptSerializer, TaskExecutionSerializer, PageScriptConfigSerializer

# 配置管理器
from ..management.commands.script_config_manager import script_config_manager

# 获取Celery任务日志器
logger = get_task_logger(__name__)

# ============================================================================
# 方案1 - 统一任务执行器 (原 tasks.py 内容)
# ============================================================================

@shared_task(bind=True)
def execute_python_script(self, task_execution_id, script_id, parameters, user_id, page_context):
    """方案1统一任务执行器 - 执行Python脚本任务"""
    task_execution = None
    process = None
    
    try:
        logger.info(f"开始执行脚本任务: task_id={self.request.id}, script_id={script_id}")
        
        # 获取任务记录
        task_execution = TaskExecution.objects.get(id=task_execution_id)
        task_execution.status = 'STARTED'
        task_execution.started_at = timezone.now()
        task_execution.save()
        
        # 获取脚本配置
        script = Script.objects.get(id=script_id)
        logger.info(f"执行脚本: {script.name} ({script.script_path})")
        
        # 记录开始时间和资源使用情况
        start_time = timezone.now()
        process_info = psutil.Process()
        initial_memory = process_info.memory_info().rss / 1024 / 1024  # MB
        
        # 执行脚本
        result = run_script(script.script_path, parameters, page_context, script.name)
        
        # 计算执行时间和资源使用
        execution_time = (timezone.now() - start_time).total_seconds()
        final_memory = process_info.memory_info().rss / 1024 / 1024  # MB
        memory_usage = final_memory - initial_memory
        
        # 更新任务状态
        task_execution.status = 'SUCCESS'
        task_execution.result = result
        task_execution.execution_time = execution_time
        task_execution.memory_usage = memory_usage
        task_execution.completed_at = timezone.now()
        task_execution.save()
        
        logger.info(f"脚本执行成功: 耗时 {execution_time:.2f}s, 内存使用 {memory_usage:.2f}MB")
        
        return {
            'status': 'success',
            'result': result,
            'execution_time': execution_time,
            'memory_usage': memory_usage,
            'script_name': script.name
        }
        
    except Exception as exc:
        error_message = str(exc)
        error_traceback = traceback.format_exc()
        
        logger.error(f"脚本执行失败: {error_message}")
        logger.error(f"错误堆栈: {error_traceback}")
        
        if task_execution:
            task_execution.status = 'FAILURE'
            task_execution.error_message = f"{error_message}\n\n{error_traceback}"
            task_execution.completed_at = timezone.now()
            task_execution.save()
        
        # 清理进程
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                pass
        
        # 重试机制
        if self.request.retries < 3:
            logger.info(f"任务重试: 第 {self.request.retries + 1} 次")
            raise self.retry(exc=exc, countdown=60, max_retries=3)
        
        return {
            'status': 'error',
            'error': error_message,
            'traceback': error_traceback,
            'script_name': script.name if 'script' in locals() else 'unknown'
        }

def run_script(script_path, parameters, page_context, script_name):
    """运行脚本的核心逻辑 - 方案1实现"""
    # 验证脚本路径
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"脚本文件不存在: {script_path}")
    
    # 确保脚本路径是绝对路径
    if not os.path.isabs(script_path):
        # 如果是相对路径，基于项目根目录解析
        script_path = os.path.join(settings.BASE_DIR, script_path)
    
    logger.info(f"执行脚本文件: {script_path}")
    
    # 根据文件类型执行不同的处理
    if script_path.endswith('.py'):
        return run_python_file(script_path, parameters, page_context, script_name)
    elif script_path.endswith('.sh'):
        return run_shell_script(script_path, parameters, page_context, script_name)
    else:
        raise ValueError(f"不支持的脚本类型: {os.path.splitext(script_path)[1]}")

def run_python_file(script_path, parameters, page_context, script_name):
    """运行Python文件 - 方案1增强版"""
    # 准备环境变量
    env = os.environ.copy()
    env['SCRIPT_PARAMETERS'] = json.dumps(parameters, ensure_ascii=False)
    env['PAGE_CONTEXT'] = page_context
    env['SCRIPT_NAME'] = script_name
    env['EXECUTION_ID'] = str(timezone.now().timestamp())
    
    logger.info(f"准备执行Python脚本: {script_path}")
    logger.info(f"参数: {parameters}")
    
    # 执行脚本
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            env=env,
            timeout=540,  # 9分钟超时 (与Celery软限制对应)
            cwd=os.path.dirname(script_path)
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

def run_shell_script(script_path, parameters, page_context, script_name):
    """运行Shell脚本 - 方案1扩展支持"""
    # 准备环境变量
    env = os.environ.copy()
    env['SCRIPT_PARAMETERS'] = json.dumps(parameters, ensure_ascii=False)
    env['PAGE_CONTEXT'] = page_context
    env['SCRIPT_NAME'] = script_name
    
    logger.info(f"准备执行Shell脚本: {script_path}")
    
    try:
        # Windows下使用PowerShell，Linux/Mac使用bash
        if os.name == 'nt':
            cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path]
        else:
            cmd = ['bash', script_path]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=540,
            cwd=os.path.dirname(script_path)
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Shell脚本执行失败: {result.stderr}")
        
        return {
            'type': 'shell_output',
            'content': result.stdout,
            'stderr': result.stderr,
            'script_name': script_name,
            'status': 'success',
            'message': 'Shell脚本执行完成'
        }
        
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Shell脚本执行超时: {script_path}")
    except Exception as e:
        logger.error(f"执行Shell脚本失败: {e}")
        raise

# ============================================================================
# DRF ViewSets (原有的视图集)
# ============================================================================

class ScriptViewSet(viewsets.ModelViewSet):
    queryset = Script.objects.filter(is_active=True)
    serializer_class = ScriptSerializer
    permission_classes = [IsAuthenticated]

class PageScriptConfigViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PageScriptConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        page_route = self.request.query_params.get('page_route')
        if page_route:
            return PageScriptConfig.objects.filter(
                page_route=page_route, 
                is_enabled=True
            ).order_by('display_order')
        return PageScriptConfig.objects.filter(is_enabled=True)

class TaskExecutionViewSet(viewsets.ModelViewSet):
    serializer_class = TaskExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TaskExecution.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def execute_script(self, request):
        """方案1 - 统一脚本执行接口"""
        script_id = request.data.get('script_id')
        parameters = request.data.get('parameters', {})
        page_context = request.data.get('page_context', '')
        
        # 验证脚本存在
        script = get_object_or_404(Script, id=script_id, is_active=True)
        
        # 验证脚本路径
        if not script.script_path:
            return Response({
                'error': '脚本路径未配置',
                'code': 400
            }, status=400)
        
        # 创建任务执行记录
        task_execution = TaskExecution.objects.create(
            task_id='',  # 先创建，稍后更新
            script=script,
            user=request.user,
            page_context=page_context,
            parameters=parameters,
            status='PENDING'
        )
        
        # 启动方案1的统一任务执行器
        celery_task = execute_python_script.delay(
            task_execution.id,
            script_id,
            parameters,
            request.user.id,
            page_context
        )
        
        # 更新任务ID
        task_execution.task_id = celery_task.id
        task_execution.save()
        
        return Response({
            'task_id': celery_task.id,
            'execution_id': task_execution.id,
            'script_name': script.name,
            'script_type': script.script_type,
            'status': 'started',
            'message': f'脚本 "{script.name}" 开始执行 (方案1)'
        })
    
    @action(detail=False, methods=['get'])
    def task_status(self, request):
        """查询任务状态"""
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
    
    @action(detail=True, methods=['post'])
    def cancel_task(self, request, pk=None):
        """取消任务"""
        task_execution = self.get_object()
        
        if task_execution.status in ['PENDING', 'STARTED']:
            # 取消Celery任务
            celery_task = AsyncResult(task_execution.task_id)
            celery_task.revoke(terminate=True)
            
            # 更新状态
            task_execution.status = 'REVOKED'
            task_execution.save()
            
            return Response({'message': '任务已取消'})
        else:
            return Response({'error': '任务无法取消'}, status=400)

# 方案1 - 脚本执行API (简化版)
@csrf_exempt
@require_http_methods(["POST"])
def execute_script_task(request):
    """方案1 - 统一脚本执行API"""
    try:
        data = json.loads(request.body) if request.body else {}
        script_id = data.get('script_id')
        parameters = data.get('parameters', {})
        page_context = data.get('page_context', 'api')
        
        if not script_id:
            return JsonResponse({
                'success': False,
                'error': '缺少script_id参数'
            }, status=400)
        
        # 获取脚本配置
        try:
            script = Script.objects.get(id=script_id, is_active=True)
        except Script.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '脚本不存在或已禁用'
            }, status=404)
        
        # 验证脚本路径
        if not script.script_path:
            return JsonResponse({
                'success': False,
                'error': '脚本路径未配置'
            }, status=400)
        
        # 创建任务执行记录
        task_execution = TaskExecution.objects.create(
            task_id='',  # 先创建，稍后更新
            script=script,
            user_id=1,  # TODO: 从request中获取真实用户ID
            page_context=page_context,
            parameters=parameters,
            status='PENDING'
        )
        
        # 调用方案1的统一任务执行器
        celery_task = execute_python_script.delay(
            task_execution.id,
            script_id,
            parameters,
            1,  # user_id
            page_context
        )
        
        # 更新任务ID
        task_execution.task_id = celery_task.id
        task_execution.save()
        
        return JsonResponse({
            'code': 200,
            'success': True,
            'task_id': celery_task.id,
            'execution_id': task_execution.id,
            'script_name': script.name,
            'message': f'脚本 "{script.name}" 已启动执行 (方案1)',
            'status': 'PENDING'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '启动脚本执行失败'
        }, status=500)

# 方案2测试任务已删除，请使用方案1的脚本执行接口

# 方案2通用任务结果API已删除，请使用 get_script_task_result

# 动态脚本任务结果获取API
@csrf_exempt
@require_http_methods(["GET"])
def get_script_task_result(request):
    """获取动态脚本任务结果API"""
    task_id = request.GET.get('task_id')
    execution_id = request.GET.get('execution_id')
    
    logging.info(f"Getting script task result for task_id: {task_id}, execution_id: {execution_id}")
    
    if not task_id:
        return JsonResponse({
            'success': False,
            'error': '缺少task_id参数'
        }, status=400)
    
    try:
        # 获取任务执行记录
        task_execution = None
        if execution_id:
            try:
                task_execution = TaskExecution.objects.get(id=execution_id)
            except TaskExecution.DoesNotExist:
                logging.warning(f"TaskExecution {execution_id} not found")
        
        # 使用Celery获取任务结果
        result = AsyncResult(task_id, app=celery_app)
        logging.info(f"AsyncResult for {task_id}: status={result.status}, ready={result.ready()}")
        
        response_data = {
            'code': 200,
            'task_id': task_id,
            'execution_id': execution_id,
            'status': result.status,
            'ready': result.ready()
        }
        
        if result.ready():
            if result.successful():
                task_result = result.result
                response_data.update({
                    'success': True,
                    'result': task_result
                })
                
                # 更新TaskExecution记录
                if task_execution:
                    try:
                        task_execution.status = 'SUCCESS'
                        task_execution.result = json.dumps(task_result) if task_result else None
                        task_execution.end_time = timezone.now()
                        task_execution.save()
                        logging.info(f"Updated TaskExecution {execution_id} status to SUCCESS")
                    except Exception as update_error:
                        logging.error(f"Failed to update TaskExecution {execution_id}: {update_error}")
                
                # 保存所有脚本任务结果到ScanDevUpdate_scanResult表
                if isinstance(task_result, dict) and task_result.get('status') == 'success':
                    try:
                        # 获取脚本信息
                        script_name = "unknown"
                        script_description = ""
                        if task_execution:
                            script_name = task_execution.script.name
                            script_description = task_execution.script.description or script_name
                        
                        # 统一存储到ScanDevUpdate_scanResult表
                        scan_result = ScanDevUpdate_scanResult.objects.create(
                            scandevresult_filename=f"{script_name}_执行结果_{task_id[:8]}.json",
                            scandevresult_time=timezone.now(),
                            director="系统自动",
                            remark=f"脚本执行结果 - {script_description}",
                            scandevresult_content=json.dumps(task_result, ensure_ascii=False, indent=2),
                            status='0',
                            # 新增字段
                            result_type='script',
                            script_name=script_name,
                            task_id=task_id,
                            execution_time=task_execution.execution_time if task_execution else None,
                            script_output=task_result.get('message', '') or (task_result.get('result', {}).get('message', '') if isinstance(task_result.get('result'), dict) else ''),
                            error_message=task_result.get('error', '') if task_result.get('status') == 'error' else None
                        )
                        response_data['saved_to_db'] = True
                        response_data['db_record_id'] = scan_result.id
                        response_data['db_table'] = 'ScanDevUpdate_scanResult'
                        logging.info(f"Script task result for {task_id} ({script_name}) saved to ScanDevUpdate_scanResult ID: {scan_result.id}")
                        
                    except Exception as db_error:
                        response_data['db_save_error'] = str(db_error)
                        logging.error(f"Failed to save script task result for {task_id} to DB: {db_error}")
                        
            else:
                response_data.update({
                    'success': False,
                    'error': str(result.result)
                })
                logging.warning(f"Script task {task_id} failed: {result.result}")
                
                # 更新TaskExecution记录为失败状态
                if task_execution:
                    try:
                        task_execution.status = 'FAILURE'
                        task_execution.result = json.dumps({'error': str(result.result)})
                        task_execution.end_time = timezone.now()
                        task_execution.save()
                    except Exception as update_error:
                        logging.error(f"Failed to update TaskExecution {execution_id} to FAILURE: {update_error}")
        else:
            response_data.update({
                'success': None,
                'message': '任务正在执行中...'
            })
            logging.info(f"Script task {task_id} is not ready yet. Status: {result.status}")
            
        return JsonResponse(response_data)
        
    except Exception as e:
        logging.exception(f"Error getting script task result for {task_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '获取动态脚本任务结果失败'
        }, status=500)

# 方案1 - 脚本管理API
@csrf_exempt
@require_http_methods(["GET"])
def list_scripts(request):
    """方案1 - 获取脚本列表API"""
    try:
        page_route = request.GET.get('page_route')
        script_type = request.GET.get('script_type')
        
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
            
            # 方案1: 每个脚本只有一个"统一执行任务"
            # 实际的参数来自parameters_schema
            script_data['tasks'].append({
                'name': 'unified_execution',
                'full_name': f'方案1统一执行器.{script.name}',
                'parameters': script.parameters_schema or {},
                'description': f'通过方案1统一执行器运行 {script.name}'
            })
            
            scripts.append(script_data)
        
        # 如果指定了页面路由，还要获取页面配置
        page_configs = []
        if page_route:
            configs = PageScriptConfig.objects.filter(
                page_route=page_route,
                is_enabled=True
            ).select_related('script').order_by('display_order')
            
            for config in configs:
                page_configs.append({
                    'id': config.id,
                    'script_id': config.script.id,
                    'script_name': config.script.name,
                    'button_text': config.button_text,
                    'button_style': config.button_style,
                    'position': config.position,
                    'display_order': config.display_order
                })
        
        return JsonResponse({
            'code': 200,
            'success': True,
            'scripts': scripts,
            'page_configs': page_configs,
            'execution_method': 'scheme_1_unified_executor'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '获取脚本列表失败'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_script_detail(request, script_id):
    """获取脚本详情API"""
    try:
        script = Script.objects.get(id=script_id, is_active=True)
        
        # 获取最近的执行记录
        recent_executions = TaskExecution.objects.filter(
            script=script
        ).order_by('-created_at')[:10]
        
        executions = []
        for execution in recent_executions:
            executions.append({
                'id': execution.id,
                'task_id': execution.task_id,
                'status': execution.status,
                'created_at': execution.created_at.isoformat(),
                'execution_time': execution.execution_time,
                'error_message': execution.error_message
            })
        
        return JsonResponse({
            'success': True,
            'script': {
                'id': script.id,
                'name': script.name,
                'description': script.description,
                'script_type': script.script_type,
                'script_path': script.script_path,
                'parameters_schema': script.parameters_schema,
                'created_at': script.created_at.isoformat(),
                'updated_at': script.updated_at.isoformat()
            },
            'recent_executions': executions
        })
        
    except Script.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '脚本不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '获取脚本详情失败'
        }, status=500)

# ============================================================================
# 动态脚本配置管理 API
# ============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def get_script_configs(request):
    """获取所有脚本的参数配置"""
    try:
        script_name = request.GET.get('script_name')
        print(f"API请求脚本配置: {script_name}")
        
        if script_name:
            # 获取单个脚本配置
            config = script_config_manager.get_parameter_schema(script_name)
            print(f"返回配置: {config}")
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
        print(f"获取脚本配置失败: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '获取脚本配置失败'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def execute_dynamic_script(request):
    """执行动态配置的脚本"""
    try:
        data = json.loads(request.body) if request.body else {}
        script_name = data.get('script_name')
        parameters = data.get('parameters', {})
        page_context = data.get('page_context', 'dynamic_execution')
        
        if not script_name:
            return JsonResponse({
                'success': False,
                'error': '缺少script_name参数'
            }, status=400)
        
        # 验证参数
        validation_result = script_config_manager.validate_parameters(script_name, parameters)
        
        if not validation_result['valid']:
            return JsonResponse({
                'success': False,
                'error': '参数验证失败',
                'validation_errors': validation_result['errors']
            }, status=400)
        
        # 使用验证后的参数
        validated_params = validation_result['processed_params']
        
        # 构建脚本路径
        script_path = os.path.join(settings.BASE_DIR, 'celery_app', script_name)
        if not script_name.endswith('.py'):
            script_path += '.py'
        
        # 验证脚本文件是否存在
        if not os.path.exists(script_path):
            return JsonResponse({
                'success': False,
                'error': f'脚本文件不存在: {script_name}'
            }, status=404)
        
        # 为动态脚本创建或获取Script记录
        script_record, created = Script.objects.get_or_create(
            name=script_name,
            defaults={
                'description': f'动态脚本: {script_name}',
                'script_path': script_path,
                'script_type': 'data_processing',
                'parameters_schema': {},
                'visualization_config': {},
                'is_active': True
            }
        )
        
        # 创建任务执行记录
        task_execution = TaskExecution.objects.create(
            task_id='',  # 先创建，稍后更新
            script=script_record,
            user_id=1,  # TODO: 从request中获取真实用户ID
            page_context=page_context,
            parameters=validated_params,
            status='PENDING'
        )
        
        # 启动脚本执行任务
        celery_task = execute_dynamic_script_task.delay(
            task_execution.id,
            script_name,
            script_path,
            validated_params,
            1,  # user_id
            page_context
        )
        
        # 更新任务ID
        task_execution.task_id = celery_task.id
        task_execution.save()
        
        return JsonResponse({
            'success': True,
            'task_id': celery_task.id,
            'execution_id': task_execution.id,
            'script_name': script_name,
            'validated_parameters': validated_params,
            'message': f'动态脚本 "{script_name}" 已启动执行',
            'status': 'PENDING'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '请求数据格式错误'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '执行动态脚本失败'
        }, status=500)

@csrf_exempt  
@require_http_methods(["POST"])
def reload_script_configs(request):
    """重新加载脚本配置"""
    try:
        script_config_manager.reload_config()
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

# ============================================================================
# 动态脚本执行任务
# ============================================================================

@shared_task(bind=True)
def execute_dynamic_script_task(self, task_execution_id, script_name, script_path, parameters, user_id, page_context):
    """动态脚本执行任务"""
    task_execution = None
    
    try:
        logger.info(f"开始执行动态脚本: task_id={self.request.id}, script={script_name}")
        
        # 获取任务记录
        task_execution = TaskExecution.objects.get(id=task_execution_id)
        task_execution.status = 'STARTED'
        task_execution.started_at = timezone.now()
        task_execution.save()
        
        logger.info(f"执行动态脚本: {script_name} ({script_path})")
        
        # 记录开始时间
        start_time = timezone.now()
        
        # 执行脚本
        result = run_script(script_path, parameters, page_context, script_name)
        
        # 计算执行时间
        execution_time = (timezone.now() - start_time).total_seconds()
        
        # 更新任务状态
        task_execution.status = 'SUCCESS'
        task_execution.result = result
        task_execution.execution_time = execution_time
        task_execution.completed_at = timezone.now()
        task_execution.save()
        
        logger.info(f"动态脚本执行成功: 耗时 {execution_time:.2f}s")
        
        return {
            'status': 'success',
            'result': result,
            'execution_time': execution_time,
            'script_name': script_name
        }
        
    except Exception as exc:
        error_message = str(exc)
        error_traceback = traceback.format_exc()
        
        logger.error(f"动态脚本执行失败: {error_message}")
        logger.error(f"错误堆栈: {error_traceback}")
        
        if task_execution:
            task_execution.status = 'FAILURE'
            task_execution.error_message = f"{error_message}\n\n{error_traceback}"
            task_execution.completed_at = timezone.now()
            task_execution.save()
        
        # 重试机制
        if self.request.retries < 3:
            logger.info(f"动态脚本任务重试: 第 {self.request.retries + 1} 次")
            raise self.retry(exc=exc, countdown=60, max_retries=3)
        
        return {
            'status': 'error',
            'error': error_message,
            'traceback': error_traceback,
            'script_name': script_name
        }