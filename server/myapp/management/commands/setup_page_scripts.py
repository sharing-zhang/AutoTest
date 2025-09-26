"""
页面脚本配置管理命令
用于在页面上配置脚本按钮
python manage.py setup_page_scripts --config-file D:\proj\AutoTest\server\myapp\management\commands\button_configs.json
"""
import json
import os
from django.core.management.base import BaseCommand
from django.db import models
from myapp.models import Script, PageScriptConfig
from myapp.management.commands.script_config_manager import script_config_manager


class Command(BaseCommand):
    help = '配置页面脚本按钮'

    def add_arguments(self, parser):
        parser.add_argument(
            '--page-route',
            type=str,
            help='页面路由，如 /scanDevUpdate',
        )
        parser.add_argument(
            '--script-name',
            type=str,
            help='要配置的脚本名称',
        )
        parser.add_argument(
            '--button-text',
            type=str,
            default='运行脚本',
            help='按钮显示文本',
        )
        parser.add_argument(
            '--position',
            type=str,
            choices=[
                'top-left', 'top-right', 'top-center',
                'bottom-left', 'bottom-right', 'bottom-center',
                'sidebar-left', 'sidebar-right', 
                'floating', 'custom'
            ],
            default='top-right',
            help='按钮位置',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='列出指定页面的所有脚本配置',
        )
        parser.add_argument(
            '--setup-default',
            action='store_true',
            help='为指定页面设置默认脚本配置',
        )
        parser.add_argument(
            '--button-style',
            type=str,
            help='按钮样式JSON字符串，如: {"type":"success","size":"small"}',
        )
        parser.add_argument(
            '--custom-position',
            type=str,
            help='自定义位置JSON字符串，如: {"top":"20px","right":"20px","position":"fixed"}',
        )
        parser.add_argument(
            '--copy-from-page',
            type=str,
            help='从其他页面复制脚本配置',
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='清除指定页面的所有脚本配置',
        )
        # 新增参数
        parser.add_argument(
            '--config-file',
            type=str,
            help='配置文件路径（JSON格式），批量配置多个按钮',
        )
        parser.add_argument(
            '--list-all',
            action='store_true',
            help='列出所有页面的脚本配置',
        )
        parser.add_argument(
            '--export-config',
            type=str,
            help='导出现有配置到JSON文件',
        )
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='仅验证配置文件，不执行配置',
        )

    def handle(self, *args, **options):
        # 自动更新脚本参数（在配置页面脚本之前）
        self.update_script_parameters()
        
        # 新增功能：处理配置文件
        if options['config_file']:
            self.handle_config_file(options)
            return
            
        # 新增功能：列出所有配置
        if options['list_all']:
            self.list_all_configs()
            return
            
        # 新增功能：导出配置
        if options['export_config']:
            self.export_configs(options['export_config'])
            return
        
        # 原有功能需要 page_route
        page_route = options['page_route']
        if not page_route:
            self.stdout.write(
                self.style.ERROR('请指定页面路由 (--page-route) 或使用配置文件 (--config-file)')
            )
            self.show_usage_examples()
            return
        
        if options['list']:
            self.list_page_configs(page_route)
            return
            
        if options['setup_default']:
            self.setup_default_configs(page_route)
            return
            
        if options['copy_from_page']:
            self.copy_page_configs(page_route, options['copy_from_page'])
            return
            
        if options['clear_all']:
            self.clear_page_configs(page_route)
            return
            
        script_name = options['script_name']
        if not script_name:
            self.stdout.write(
                self.style.ERROR('请指定脚本名称 (--script-name)')
            )
            return
            
        # 解析按钮样式
        button_style = {}
        if options['button_style']:
            try:
                button_style = json.loads(options['button_style'])
            except json.JSONDecodeError:
                self.stdout.write(
                    self.style.ERROR('按钮样式JSON格式错误')
                )
                return
        
        # 解析自定义位置
        custom_position = {}
        if options['custom_position']:
            try:
                custom_position = json.loads(options['custom_position'])
            except json.JSONDecodeError:
                self.stdout.write(
                    self.style.ERROR('自定义位置JSON格式错误')
                )
                return
            
        self.configure_page_script(
            page_route,
            script_name,
            options['button_text'],
            options['position'],
            button_style,
            custom_position
        )

    def handle_config_file(self, options):
        """处理配置文件批量设置"""
        config_file = options['config_file']
        
        # 检查文件是否存在
        if not os.path.exists(config_file):
            self.stdout.write(
                self.style.ERROR(f'配置文件不存在: {config_file}')
            )
            return
        
        try:
            # 读取和验证配置文件
            configs = self.load_and_validate_config(config_file)
            
            if options['validate_only']:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ 配置文件验证通过，共 {len(configs)} 个配置')
                )
                return
            
            # 执行批量配置
            self.batch_setup_configs(configs, config_file)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'处理配置文件失败: {e}')
            )

    def load_and_validate_config(self, config_file):
        """加载和验证配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f'JSON 格式错误: {e}')
        except Exception as e:
            raise ValueError(f'读取文件失败: {e}')
        
        if not isinstance(configs, list):
            raise ValueError('配置文件根节点必须是数组')
        
        # 验证每个配置项
        required_fields = ['page_route', 'script_name', 'button_text', 'position']
        valid_positions = [
            'top-left', 'top-right', 'top-center',
            'bottom-left', 'bottom-right', 'bottom-center',
            'sidebar-left', 'sidebar-right', 
            'floating', 'custom'
        ]
        
        for i, config in enumerate(configs, 1):
            # 检查必需字段
            for field in required_fields:
                if field not in config:
                    raise ValueError(f'配置 {i} 缺少必需字段: {field}')
            
            # 验证位置
            if config['position'] not in valid_positions:
                raise ValueError(f'配置 {i} 位置无效: {config["position"]}，有效值: {valid_positions}')
            
            # 验证JSON字段
            if 'button_style' in config and isinstance(config['button_style'], str):
                try:
                    json.loads(config['button_style'])
                except json.JSONDecodeError:
                    raise ValueError(f'配置 {i} button_style JSON格式错误')
            
            if 'custom_position' in config and isinstance(config['custom_position'], str):
                try:
                    json.loads(config['custom_position'])
                except json.JSONDecodeError:
                    raise ValueError(f'配置 {i} custom_position JSON格式错误')
        
        return configs

    def batch_setup_configs(self, configs, config_file):
        """批量执行配置"""
        self.stdout.write(f'📖 从 {config_file} 读取到 {len(configs)} 个配置')
        self.stdout.write('=' * 60)
        
        success_count = 0
        error_count = 0
        
        for i, config in enumerate(configs, 1):
            try:
                self.stdout.write(f'\n⚙️  配置 {i}/{len(configs)}: {config["page_route"]}')
                
                # 解析样式和位置
                button_style = {}
                if 'button_style' in config:
                    if isinstance(config['button_style'], str):
                        button_style = json.loads(config['button_style'])
                    else:
                        button_style = config['button_style']
                
                custom_position = {}
                if 'custom_position' in config:
                    if isinstance(config['custom_position'], str):
                        custom_position = json.loads(config['custom_position'])
                    else:
                        custom_position = config['custom_position']
                
                # 执行配置
                self.configure_page_script(
                    config['page_route'],
                    config['script_name'],
                    config['button_text'],
                    config['position'],
                    button_style,
                    custom_position
                )
                
                success_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ 失败: {str(e)}')
                )
                error_count += 1
        
        # 显示总结
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(f'🎉 配置完成！成功: {success_count}, 失败: {error_count}')
        )

    def list_all_configs(self):
        """列出所有页面的脚本配置"""
        try:
            configs = PageScriptConfig.objects.all().select_related('script').order_by('page_route', 'display_order')
            
            if not configs:
                self.stdout.write('暂无任何页面脚本配置')
                return
            
            # 按页面分组
            pages = {}
            for config in configs:
                if config.page_route not in pages:
                    pages[config.page_route] = []
                pages[config.page_route].append(config)
            
            self.stdout.write(f'\n当前共有 {len(pages)} 个页面，{configs.count()} 个按钮配置：')
            self.stdout.write('=' * 80)
            
            for page_route, page_configs in pages.items():
                self.stdout.write(f'\n📄 页面: {page_route}')
                self.stdout.write('-' * 40)
                
                for config in page_configs:
                    status = '✅' if config.is_enabled else '❌'
                    self.stdout.write(
                        f'  {status} {config.script.name} | {config.button_text} | {config.position}'
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'获取配置列表失败: {e}')
            )

    def export_configs(self, output_file):
        """导出现有配置到JSON文件"""
        try:
            configs = PageScriptConfig.objects.all().select_related('script').order_by('page_route', 'display_order')
            
            if not configs:
                self.stdout.write('暂无配置可导出')
                return
            
            # 转换为JSON格式
            json_configs = []
            for config in configs:
                json_config = {
                    'page_route': config.page_route,
                    'script_name': config.script.name,
                    'button_text': config.button_text,
                    'position': config.position
                }
                
                # 添加可选字段
                if config.button_style:
                    json_config['button_style'] = json.dumps(
                        config.button_style, 
                        ensure_ascii=False
                    )
                
                # 添加自定义位置字段
                if config.custom_position:
                    json_config['custom_position'] = json.dumps(
                        config.custom_position, 
                        ensure_ascii=False
                    )
                
                json_configs.append(json_config)
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_configs, f, ensure_ascii=False, indent=2)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ 已导出 {len(json_configs)} 个配置到: {output_file}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'导出配置失败: {e}')
            )

    def show_usage_examples(self):
        """显示使用示例"""
        self.stdout.write('\n📖 使用示例:')
        self.stdout.write('-' * 40)
        self.stdout.write('单个配置:')
        self.stdout.write('  python manage.py setup_page_scripts --page-route /test --script-name hellowrld --button-text "测试"')
        self.stdout.write('')
        self.stdout.write('批量配置:')
        self.stdout.write('  python manage.py setup_page_scripts --config-file button_configs.json')
        self.stdout.write('')
        self.stdout.write('验证配置文件:')
        self.stdout.write('  python manage.py setup_page_scripts --config-file button_configs.json --validate-only')
        self.stdout.write('')
        self.stdout.write('列出所有配置:')
        self.stdout.write('  python manage.py setup_page_scripts --list-all')
        self.stdout.write('')
        self.stdout.write('导出现有配置:')
        self.stdout.write('  python manage.py setup_page_scripts --export-config exported.json')

    def list_page_configs(self, page_route):
        """列出页面的脚本配置"""
        configs = PageScriptConfig.objects.filter(
            page_route=page_route
        ).select_related('script').order_by('display_order')
        
        if not configs:
            self.stdout.write(f'页面 {page_route} 暂无脚本配置')
            return
            
        self.stdout.write(f'\n页面 {page_route} 的脚本配置:')
        self.stdout.write('-' * 60)
        
        for i, config in enumerate(configs, 1):
            status = '启用' if config.is_enabled else '禁用'
            self.stdout.write(
                f'{i}. 脚本: {config.script.name}\n'
                f'   按钮文本: {config.button_text}\n'
                f'   位置: {config.position}\n'
                f'   状态: {status}\n'
                f'   显示顺序: {config.display_order}\n'
            )

    def configure_page_script(self, page_route, script_name, button_text, position, button_style=None, custom_position=None):
        """配置页面脚本"""
        try:
            script = Script.objects.get(name=script_name, is_active=True)
        except Script.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'脚本 {script_name} 不存在或已禁用')
            )
            # 列出可用脚本
            self.list_available_scripts()
            return
            
        # 检查是否已存在配置
        existing_config = PageScriptConfig.objects.filter(
            page_route=page_route,
            script=script
        ).first()
        
        if existing_config:
            # 更新现有配置
            existing_config.button_text = button_text
            existing_config.position = position
            existing_config.is_enabled = True
            if button_style:
                existing_config.button_style = button_style
            if custom_position:
                # 保存自定义位置到专门的custom_position字段
                existing_config.custom_position = custom_position
            existing_config.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ 已更新页面 {page_route} 的脚本 {script_name} 配置'
                )
            )
        else:
            # 创建新配置
            max_order = PageScriptConfig.objects.filter(
                page_route=page_route
            ).aggregate(
                models.Max('display_order')
            )['display_order__max'] or 0
            
            # 准备按钮样式和自定义位置
            final_button_style = button_style or {}
            final_custom_position = custom_position or {}
            
            PageScriptConfig.objects.create(
                page_name=page_route.split('/')[-1] or 'root',
                page_route=page_route,
                script=script,
                button_text=button_text,
                button_style=final_button_style,
                position=position,
                custom_position=final_custom_position,
                is_enabled=True,
                display_order=max_order + 1
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ 已为页面 {page_route} 添加脚本 {script_name} 配置'
                )
            )

    def setup_default_configs(self, page_route):
        """设置默认的脚本配置"""
        from django.db import models
        
        default_configs = [
            {
                'script_name': 'hellowrld',
                'button_text': '测试任务',
                'position': 'top-right'
            },
            {
                'script_name': 'check_file',
                'button_text': '文件检查',
                'position': 'top-right'
            },
            {
                'script_name': 'data_analysis',
                'button_text': '数据分析',
                'position': 'top-right'
            }
        ]
        
        success_count = 0
        
        for config in default_configs:
            try:
                script = Script.objects.get(
                    name=config['script_name'],
                    is_active=True
                )
                
                # 检查是否已存在
                existing = PageScriptConfig.objects.filter(
                    page_route=page_route,
                    script=script
                ).first()
                
                if not existing:
                    max_order = PageScriptConfig.objects.filter(
                        page_route=page_route
                    ).aggregate(
                        models.Max('display_order')
                    )['display_order__max'] or 0
                    
                    PageScriptConfig.objects.create(
                        page_name=page_route.split('/')[-1] or 'root',
                        page_route=page_route,
                        script=script,
                        button_text=config['button_text'],
                        position=config['position'],
                        is_enabled=True,
                        display_order=max_order + 1
                    )
                    success_count += 1
                    
            except Script.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'脚本 {config["script_name"]} 不存在，跳过配置'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'已为页面 {page_route} 设置 {success_count} 个默认脚本配置'
            )
        )

    def list_available_scripts(self):
        """列出可用脚本"""
        scripts = Script.objects.filter(is_active=True).order_by('name')
        
        if scripts:
            self.stdout.write('\n可用脚本列表:')
            self.stdout.write('-' * 40)
            for script in scripts:
                self.stdout.write(
                    f'• {script.name} ({script.script_type}) - {script.description}'
                )
        else:
            self.stdout.write('暂无可用脚本，请先运行 register_scripts 命令注册脚本')

    def copy_page_configs(self, target_page_route, source_page_route):
        """从其他页面复制脚本配置"""
        source_configs = PageScriptConfig.objects.filter(
            page_route=source_page_route
        ).select_related('script')
        
        if not source_configs:
            self.stdout.write(
                self.style.WARNING(f'源页面 {source_page_route} 没有脚本配置')
            )
            return
            
        copied_count = 0
        for source_config in source_configs:
            # 检查目标页面是否已存在相同脚本配置
            existing = PageScriptConfig.objects.filter(
                page_route=target_page_route,
                script=source_config.script
            ).first()
            
            if not existing:
                max_order = PageScriptConfig.objects.filter(
                    page_route=target_page_route
                ).aggregate(
                    models.Max('display_order')
                )['display_order__max'] or 0
                
                PageScriptConfig.objects.create(
                    page_name=target_page_route.split('/')[-1] or 'root',
                    page_route=target_page_route,
                    script=source_config.script,
                    button_text=source_config.button_text,
                    button_style=source_config.button_style,
                    position=source_config.position,
                    is_enabled=source_config.is_enabled,
                    display_order=max_order + 1
                )
                copied_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'已从页面 {source_page_route} 复制 {copied_count} 个脚本配置到页面 {target_page_route}'
            )
        )

    def clear_page_configs(self, page_route):
        """清除页面的所有脚本配置"""
        deleted_count = PageScriptConfig.objects.filter(
            page_route=page_route
        ).delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'已清除页面 {page_route} 的 {deleted_count} 个脚本配置'
            )
        )

    def update_script_parameters(self):
        """更新脚本参数配置"""
        try:
            self.stdout.write('正在更新脚本参数配置...')
            
            # 重新加载配置
            script_config_manager.reload_config()
            
            # 获取所有配置的脚本
            all_scripts = script_config_manager.get_all_scripts()
            
            if not all_scripts:
                self.stdout.write(self.style.WARNING('没有找到任何脚本配置'))
                return
            
            updated_count = 0
            created_count = 0
            
            for script_name in all_scripts:
                # 获取脚本配置
                script_config = script_config_manager.get_script_config(script_name)
                
                if not script_config:
                    self.stdout.write(f'跳过 {script_name}：没有找到配置')
                    continue
                
                # 查找或创建Script记录
                script_record, created = Script.objects.get_or_create(
                    name=script_name,
                    defaults={
                        'description': f'动态脚本: {script_name}',
                        'script_path': f'celery_app/{script_name}.py',
                        'script_type': 'data_processing',
                        'parameters_schema': {},
                        'visualization_config': {},
                        'is_active': True
                    }
                )
                
                # 更新参数配置
                script_record.parameters_schema = script_config
                script_record.save()
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  创建新脚本记录: {script_name}')
                else:
                    updated_count += 1
                    self.stdout.write(f'  更新脚本参数: {script_name}')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'脚本参数更新完成！创建了 {created_count} 个新记录，更新了 {updated_count} 个现有记录'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'更新脚本参数时出错: {str(e)}')
            )