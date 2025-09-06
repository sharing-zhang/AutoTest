"""
Celery任务相关视图
"""
from rest_framework.decorators import api_view
from rest_framework import status
import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.utils import timezone

# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from celery.result import AsyncResult
from ..models import Script, TaskExecution, PageScriptConfig, ScanDevUpdate_scanResult
from myapp.tasks import execute_python_script
from ..serializers import ScriptSerializer, TaskExecutionSerializer, PageScriptConfigSerializer
from celery_app.celery import app as celery_app

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
        """执行脚本"""
        script_id = request.data.get('script_id')
        parameters = request.data.get('parameters', {})
        page_context = request.data.get('page_context', '')
        
        script = get_object_or_404(Script, id=script_id, is_active=True)
        
        # 创建任务执行记录
        task_execution = TaskExecution.objects.create(
            task_id='',  # 先创建，稍后更新
            script=script,
            user=request.user,
            page_context=page_context,
            parameters=parameters,
            status='PENDING'
        )
        
        # 启动Celery任务
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
            'status': 'started',
            'message': '脚本开始执行'
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

# 动态脚本执行API
@csrf_exempt
@require_http_methods(["POST"])
def execute_script_task(request):
    """执行脚本任务API"""
    try:
        data = json.loads(request.body) if request.body else {}
        script_id = data.get('script_id')
        task_name = data.get('task_name')
        parameters = data.get('parameters', {})
        
        if not script_id or not task_name:
            return JsonResponse({
                'success': False,
                'error': '缺少script_id或task_name参数'
            }, status=400)
        
        # 获取脚本配置
        try:
            script = Script.objects.get(id=script_id, is_active=True)
        except Script.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '脚本不存在或已禁用'
            }, status=404)
        
        # 创建任务执行记录
        task_execution = TaskExecution.objects.create(
            task_id='',  # 先创建，稍后更新
            script=script,
            user_id=1,  # TODO: 从request中获取真实用户ID
            page_context=data.get('page_context', 'manual'),
            parameters=parameters,
            status='PENDING'
        )
        
        # 动态调用任务
        from celery_app.celery import app as celery_app
        task_result = celery_app.send_task(task_name, kwargs=parameters)
        
        # 更新任务ID
        task_execution.task_id = task_result.id
        task_execution.save()
        
        return JsonResponse({
            'code': 200,
            'success': True,
            'task_id': task_result.id,
            'execution_id': task_execution.id,
            'message': f'脚本 {script.name} 已启动执行',
            'status': 'PENDING'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '启动脚本执行失败'
        }, status=500)

# 简单的测试任务API (保留向后兼容)
@csrf_exempt
@require_http_methods(["POST"])
def run_test_task(request):
    """运行测试任务API"""
    try:
        logging.info("Frontend requested to start debug_task")
        # 启动celery任务
        task = debug_task.delay()
        logging.info(f"Debug task started with ID: {task.id}, status: {task.status}")
        
        return JsonResponse({
            'code': 200,
            'success': True,
            'task_id': task.id,
            'message': '测试任务已启动',
            'status': 'PENDING'
        })
        
    except Exception as e:
        logging.exception(f"Error starting debug task: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '启动任务失败'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_task_result(request):
    """获取任务结果API"""
    task_id = request.GET.get('task_id')
    logging.info(f"Frontend requested task status for task_id: {task_id}")
    
    if not task_id:
        return JsonResponse({
            'success': False,
            'error': '缺少task_id参数'
        }, status=400)
    
    try:
        # 使用正确的Celery app实例获取任务结果
        result = AsyncResult(task_id, app=celery_app)
        logging.info(f"AsyncResult for {task_id}: status={result.status}, ready={result.ready()}, successful={result.successful()}")
        
        response_data = {
            'code': 200,
            'task_id': task_id,
            'status': result.status,
            'ready': result.ready()
        }
        
        if result.ready():
            if result.successful():
                task_result = result.result
                response_data.update({
                    'code': 200,
                    'success': True,
                    'result': task_result
                })
                logging.info(f"Task {task_id} is successful. Result: {task_result}")
                
                # 如果任务成功，将结果存储到数据库
                if isinstance(task_result, dict) and task_result.get('status') == 'success':
                    try:
                        # 创建扫描结果记录
                        scan_result = ScanDevUpdate_scanResult.objects.create(
                            scandevresult_filename=f"测试任务结果_{task_id[:8]}.json",
                            scandevresult_time=timezone.now(),
                            director="系统自动",
                            remark=f"Celery测试任务执行结果",
                            scandevresult_content=json.dumps(task_result, ensure_ascii=False, indent=2),
                            status='0',
                            # 新增字段
                            result_type='task',
                            script_name='hellowrld',
                            task_id=task_id,
                            script_output=task_result.get('message', ''),
                            error_message=task_result.get('error', '') if task_result.get('status') == 'error' else None
                        )
                        response_data['saved_to_db'] = True
                        response_data['db_record_id'] = scan_result.id
                        logging.info(f"Task result for {task_id} saved to DB as ScanDevUpdate_scanResult ID: {scan_result.id}")
                    except Exception as db_error:
                        response_data['db_save_error'] = str(db_error)
                        logging.error(f"Failed to save task result for {task_id} to DB: {db_error}")
                        
            else:
                response_data.update({
                    'success': False,
                    'error': str(result.result)
                })
                logging.warning(f"Task {task_id} is ready but not successful. Error: {result.result}")
        else:
            response_data.update({
                'success': None,
                'message': '任务正在执行中...'
            })
            logging.info(f"Task {task_id} is not ready yet. Status: {result.status}")
            
        return JsonResponse(response_data)
        
    except Exception as e:
        logging.exception(f"Error getting task status for {task_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '获取任务状态失败'
        }, status=500)

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
                            script_output=task_result.get('message', ''),
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

# 脚本管理API
@csrf_exempt
@require_http_methods(["GET"])
def list_scripts(request):
    """获取脚本列表API"""
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
                'parameters_schema': script.parameters_schema,
                'created_at': script.created_at.isoformat(),
                'tasks': []
            }
            
            # 从参数模式中提取任务信息
            if script.parameters_schema and isinstance(script.parameters_schema, dict):
                for task_name, task_params in script.parameters_schema.items():
                    script_data['tasks'].append({
                        'name': task_name,
                        'full_name': f'celery_app.{script.name}.{task_name}',
                        'parameters': task_params
                    })
            else:
                # 如果没有参数模式，根据脚本名称添加实际存在的任务
               
                if script.name == 'print_test':
                    script_data['tasks'].append({
                        'name': 'hello_task',
                        'full_name': 'celery_app.print_test.hello_task',
                        'parameters': {}
                    })
                else:
                    # 其他脚本的默认处理
                    script_data['tasks'].append({
                        'name': 'default_task',
                        'full_name': f'celery_app.{script.name}.default_task',
                        'parameters': {}
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
            'page_configs': page_configs
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