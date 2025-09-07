"""
脚本注册管理命令
用于扫描celery_app目录下的脚本文件并注册到数据库
"""
import os
import json
import ast
import inspect
from django.core.management.base import BaseCommand
from django.conf import settings
from myapp.models import Script, PageScriptConfig


class ScriptAnalyzer(ast.NodeVisitor):
    """脚本分析器，用于提取脚本的元信息"""
    
    def __init__(self):
        self.functions = []
        self.tasks = []
        self.docstring = None
        self.imports = []
        
    def visit_FunctionDef(self, node):
        """访问函数定义"""
        func_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'args': [arg.arg for arg in node.args.args],
            'is_task': any(
                isinstance(decorator, ast.Name) and decorator.id in ['task', 'shared_task']
                or isinstance(decorator, ast.Attribute) and decorator.attr == 'task'
                for decorator in node.decorator_list
            )
        }
        
        if func_info['is_task']:
            self.tasks.append(func_info)
        else:
            self.functions.append(func_info)
            
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """访问import语句"""
        for alias in node.names:
            self.imports.append(alias.name)
    
    def visit_ImportFrom(self, node):
        """访问from import语句"""
        if node.module:
            for alias in node.names:
                self.imports.append(f"{node.module}.{alias.name}")


class Command(BaseCommand):
    help = '扫描并注册celery_app目录下的脚本'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新注册所有脚本',
        )
        parser.add_argument(
            '--script',
            type=str,
            help='指定要注册的脚本文件名',
        )

    def handle(self, *args, **options):
        self.stdout.write('开始扫描celery_app目录下的脚本...')
        
        celery_app_path = os.path.join(settings.BASE_DIR, 'celery_app')
        
        if not os.path.exists(celery_app_path):
            self.stdout.write(
                self.style.ERROR(f'celery_app目录不存在: {celery_app_path}')
            )
            return
            
        registered_count = 0
        updated_count = 0
        
        for filename in os.listdir(celery_app_path):
            if not filename.endswith('.py') or filename.startswith('__'):
                continue
                
            if filename in ['celery.py']:  # 跳过配置文件
                continue
                
            if options['script'] and filename != options['script']:
                continue
                
            filepath = os.path.join(celery_app_path, filename)
            
            try:
                result = self.analyze_script(filepath, filename)
                if result:
                    if self.register_script(result, options['force']):
                        registered_count += 1
                    else:
                        updated_count += 1
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'处理脚本 {filename} 时出错: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'脚本注册完成! 新注册: {registered_count}, 更新: {updated_count}'
            )
        )

    def analyze_script(self, filepath, filename):
        """分析脚本文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.strip():
                return None
                
            tree = ast.parse(content)
            analyzer = ScriptAnalyzer()
            analyzer.visit(tree)
            
            # 获取模块级别的文档字符串
            module_docstring = ast.get_docstring(tree)
            
            # 确定脚本类型
            script_type = self.determine_script_type(filename, analyzer.imports, content)
            
            # 提取参数模式 - 支持方案1的参数提取
            parameters_schema = self.extract_parameters_schema_v1(filename, content, analyzer.tasks)
            
            # 转换为相对路径 (相对于server目录)
            relative_path = os.path.relpath(filepath, settings.BASE_DIR)
            
            return {
                'name': filename.replace('.py', ''),
                'description': module_docstring or f'方案1脚本: {filename}',
                'script_path': relative_path,
                'script_type': script_type,
                'parameters_schema': parameters_schema,
                'tasks': analyzer.tasks,
                'functions': analyzer.functions,
                'imports': analyzer.imports,
                'is_v1_script': self.is_v1_script(content)
            }
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'分析脚本 {filename} 失败: {str(e)}')
            )
            return None

    def determine_script_type(self, filename, imports, content):
        """根据文件名、导入和内容确定脚本类型"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # 根据文件名判断
        if any(keyword in filename_lower for keyword in ['report', '报告']):
            return 'report_generation'
        elif any(keyword in filename_lower for keyword in ['analysis', '分析']):
            return 'data_analysis'
        elif any(keyword in filename_lower for keyword in ['ml', 'machine', 'learning', '机器学习']):
            return 'machine_learning'
        elif any(keyword in filename_lower for keyword in ['process', '处理']):
            return 'data_processing'
            
        # 根据导入判断
        ml_imports = ['sklearn', 'tensorflow', 'torch', 'keras', 'numpy', 'pandas']
        if any(imp in str(imports) for imp in ml_imports):
            return 'machine_learning'
            
        analysis_imports = ['matplotlib', 'seaborn', 'plotly', 'scipy']
        if any(imp in str(imports) for imp in analysis_imports):
            return 'data_analysis'
            
        # 默认为数据处理
        return 'data_processing'

    def extract_parameters_schema(self, tasks):
        """从任务函数中提取参数模式"""
        schema = {}
        
        for task in tasks:
            if task['args']:
                task_schema = {}
                for arg in task['args']:
                    if arg not in ['self', 'cls']:
                        task_schema[arg] = {
                            'type': 'string',
                            'required': True,
                            'description': f'参数: {arg}'
                        }
                schema[task['name']] = task_schema
                
        return schema

    def extract_parameters_schema_v1(self, filename, content, tasks):
        """方案1专用：提取参数模式"""
        # 预定义的脚本参数模式
        predefined_schemas = {
            'print_test_script': {
                'greeting': {
                    'type': 'string',
                    'default': '你好！',
                    'description': '问候语',
                    'required': False
                },
                'author': {
                    'type': 'string', 
                    'default': '阿青',
                    'description': '作者名称',
                    'required': False
                }
            },
            'example_script': {
                'message': {
                    'type': 'string',
                    'default': 'Hello from example script!',
                    'description': '要处理的消息',
                    'required': False
                },
                'multiplier': {
                    'type': 'integer',
                    'default': 1,
                    'description': '重复次数',
                    'required': False
                },
                'delay': {
                    'type': 'number',
                    'default': 1,
                    'description': '延迟时间(秒)',
                    'required': False
                }
            }
        }
        
        script_name = filename.replace('.py', '')
        
        # 如果有预定义的参数模式，使用它
        if script_name in predefined_schemas:
            return predefined_schemas[script_name]
        
        # 如果是方案1脚本，尝试从注释中提取参数
        if self.is_v1_script(content):
            return self.parse_v1_parameters_from_content(content)
        
        # 否则使用原有的任务参数提取
        return self.extract_parameters_schema(tasks)

    def is_v1_script(self, content):
        """判断是否为方案1脚本"""
        indicators = [
            'SCRIPT_PARAMETERS',  # 环境变量获取参数
            'get_script_parameters',  # 参数获取函数
            'PAGE_CONTEXT',  # 页面上下文
            'os.environ.get',  # 环境变量使用
            'json.dumps(output'  # JSON输出
        ]
        
        return any(indicator in content for indicator in indicators)

    def parse_v1_parameters_from_content(self, content):
        """从方案1脚本内容中解析参数"""
        # 基本的参数解析逻辑
        # 寻找 parameters.get('key', 'default') 模式
        import re
        
        param_pattern = r"parameters\.get\(['\"](\w+)['\"],?\s*([^)]*)\)"
        matches = re.findall(param_pattern, content)
        
        schema = {}
        for param_name, default_value in matches:
            # 尝试推断类型
            param_type = 'string'
            default_val = default_value.strip(' \'"')
            
            if default_val.isdigit():
                param_type = 'integer'
                default_val = int(default_val)
            elif default_val.replace('.', '').isdigit():
                param_type = 'number'
                default_val = float(default_val)
            elif default_val.lower() in ['true', 'false']:
                param_type = 'boolean'
                default_val = default_val.lower() == 'true'
            
            schema[param_name] = {
                'type': param_type,
                'default': default_val,
                'description': f'脚本参数: {param_name}',
                'required': False
            }
        
        return schema

    def register_script(self, script_info, force_update=False):
        """注册脚本到数据库"""
        script_name = script_info['name']
        
        # 检查是否已存在
        existing_script = Script.objects.filter(name=script_name).first()
        
        if existing_script and not force_update:
            # 更新现有脚本
            existing_script.description = script_info['description']
            existing_script.script_path = script_info['script_path']
            existing_script.script_type = script_info['script_type']
            existing_script.parameters_schema = script_info['parameters_schema']
            existing_script.save()
            
            self.stdout.write(f'  更新脚本: {script_name}')
            return False
        else:
            # 创建新脚本
            if existing_script:
                existing_script.delete()
                
            Script.objects.create(
                name=script_name,
                description=script_info['description'],
                script_path=script_info['script_path'],
                script_type=script_info['script_type'],
                parameters_schema=script_info['parameters_schema'],
                is_active=True
            )
            
            self.stdout.write(f'  注册新脚本: {script_name}')
            return True
