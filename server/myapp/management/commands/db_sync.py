"""
数据库同步管理命令
用于数据库的备份、恢复和同步操作
"""
import os
import json
import subprocess
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = '数据库同步管理工具'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup',
            action='store_true',
            help='备份数据库'
        )
        parser.add_argument(
            '--restore',
            type=str,
            help='从备份文件恢复数据库'
        )
        parser.add_argument(
            '--export-data',
            type=str,
            help='导出数据到JSON文件'
        )
        parser.add_argument(
            '--import-data',
            type=str,
            help='从JSON文件导入数据'
        )
        parser.add_argument(
            '--sync-schema',
            action='store_true',
            help='同步数据库结构'
        )
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='backups',
            help='备份目录路径'
        )

    def handle(self, *args, **options):
        self.stdout.write('🗄️ 数据库同步管理工具')
        
        try:
            if options['backup']:
                self.backup_database(options['backup_dir'])
            elif options['restore']:
                self.restore_database(options['restore'])
            elif options['export_data']:
                self.export_data(options['export_data'])
            elif options['import_data']:
                self.import_data(options['import_data'])
            elif options['sync_schema']:
                self.sync_schema()
            else:
                self.show_help()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 操作失败: {str(e)}')
            )
            raise

    def backup_database(self, backup_dir):
        """备份数据库"""
        self.stdout.write('💾 开始备份数据库...')
        
        # 创建备份目录
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sql')
        
        # 获取数据库配置
        db_config = settings.DATABASES['default']
        
        if db_config['ENGINE'] == 'django.db.backends.mysql':
            self.backup_mysql(db_config, backup_file)
        elif db_config['ENGINE'] == 'django.db.backends.sqlite3':
            self.backup_sqlite(db_config, backup_file)
        else:
            self.stdout.write(
                self.style.ERROR('❌ 不支持的数据库类型')
            )
            return
            
        self.stdout.write(
            self.style.SUCCESS(f'✅ 数据库备份完成: {backup_file}')
        )

    def backup_mysql(self, db_config, backup_file):
        """备份MySQL数据库"""
        try:
            cmd = [
                'mysqldump',
                f'--host={db_config["HOST"]}',
                f'--port={db_config["PORT"]}',
                f'--user={db_config["USER"]}',
                f'--password={db_config["PASSWORD"]}',
                '--single-transaction',
                '--routines',
                '--triggers',
                db_config['NAME']
            ]
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                subprocess.run(cmd, stdout=f, check=True)
                
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ MySQL备份失败: {e}')
            )
            raise
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR('❌ 未找到mysqldump命令，请确保MySQL客户端已安装')
            )
            raise

    def backup_sqlite(self, db_config, backup_file):
        """备份SQLite数据库"""
        db_path = db_config['NAME']
        if not os.path.exists(db_path):
            self.stdout.write(
                self.style.ERROR(f'❌ 数据库文件不存在: {db_path}')
            )
            return
            
        shutil.copy2(db_path, backup_file)
        self.stdout.write(f'✅ SQLite数据库已复制到: {backup_file}')

    def restore_database(self, backup_file):
        """恢复数据库"""
        if not os.path.exists(backup_file):
            self.stdout.write(
                self.style.ERROR(f'❌ 备份文件不存在: {backup_file}')
            )
            return
            
        self.stdout.write('🔄 开始恢复数据库...')
        
        # 获取数据库配置
        db_config = settings.DATABASES['default']
        
        if db_config['ENGINE'] == 'django.db.backends.mysql':
            self.restore_mysql(db_config, backup_file)
        elif db_config['ENGINE'] == 'django.db.backends.sqlite3':
            self.restore_sqlite(db_config, backup_file)
        else:
            self.stdout.write(
                self.style.ERROR('❌ 不支持的数据库类型')
            )
            return
            
        self.stdout.write(
            self.style.SUCCESS('✅ 数据库恢复完成')
        )

    def restore_mysql(self, db_config, backup_file):
        """恢复MySQL数据库"""
        try:
            cmd = [
                'mysql',
                f'--host={db_config["HOST"]}',
                f'--port={db_config["PORT"]}',
                f'--user={db_config["USER"]}',
                f'--password={db_config["PASSWORD"]}',
                db_config['NAME']
            ]
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                subprocess.run(cmd, stdin=f, check=True)
                
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ MySQL恢复失败: {e}')
            )
            raise
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR('❌ 未找到mysql命令，请确保MySQL客户端已安装')
            )
            raise

    def restore_sqlite(self, db_config, backup_file):
        """恢复SQLite数据库"""
        db_path = db_config['NAME']
        
        # 备份当前数据库
        if os.path.exists(db_path):
            current_backup = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, current_backup)
            self.stdout.write(f'📋 当前数据库已备份到: {current_backup}')
        
        # 恢复数据库
        shutil.copy2(backup_file, db_path)
        self.stdout.write(f'✅ SQLite数据库已从 {backup_file} 恢复')

    def export_data(self, output_file):
        """导出数据到JSON文件"""
        self.stdout.write('📤 开始导出数据...')
        
        from myapp.models import (
            User, Tag, Classification, ScanUpdate, 
            ScanDevUpdate_scanResult, Thing, Comment,
            LoginLog, OpLog, ErrorLog, Ad, Notice,
            Script, TaskExecution, PageScriptConfig
        )
        
        # 定义要导出的模型
        models_to_export = [
            (User, 'users'),
            (Tag, 'tags'),
            (Classification, 'classifications'),
            (ScanUpdate, 'scan_updates'),
            (ScanDevUpdate_scanResult, 'scan_results'),
            (Thing, 'things'),
            (Comment, 'comments'),
            (LoginLog, 'login_logs'),
            (OpLog, 'op_logs'),
            (ErrorLog, 'error_logs'),
            (Ad, 'ads'),
            (Notice, 'notices'),
            (Script, 'scripts'),
            (TaskExecution, 'task_executions'),
            (PageScriptConfig, 'page_script_configs'),
        ]
        
        export_data = {}
        
        for model, key in models_to_export:
            try:
                data = list(model.objects.values())
                export_data[key] = data
                self.stdout.write(f'  ✓ 导出 {model._meta.verbose_name}: {len(data)} 条记录')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️ 导出 {model._meta.verbose_name} 失败: {e}')
                )
        
        # 保存到文件
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
        self.stdout.write(
            self.style.SUCCESS(f'✅ 数据导出完成: {output_file}')
        )

    def import_data(self, input_file):
        """从JSON文件导入数据"""
        if not os.path.exists(input_file):
            self.stdout.write(
                self.style.ERROR(f'❌ 导入文件不存在: {input_file}')
            )
            return
            
        self.stdout.write('📥 开始导入数据...')
        
        with open(input_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
            
        from myapp.models import (
            User, Tag, Classification, ScanUpdate, 
            ScanDevUpdate_scanResult, Thing, Comment,
            LoginLog, OpLog, ErrorLog, Ad, Notice,
            Script, TaskExecution, PageScriptConfig
        )
        
        # 定义导入顺序（考虑外键依赖）
        import_order = [
            (User, 'users'),
            (Tag, 'tags'),
            (Classification, 'classifications'),
            (ScanUpdate, 'scan_updates'),
            (ScanDevUpdate_scanResult, 'scan_results'),
            (Thing, 'things'),
            (Comment, 'comments'),
            (LoginLog, 'login_logs'),
            (OpLog, 'op_logs'),
            (ErrorLog, 'error_logs'),
            (Ad, 'ads'),
            (Notice, 'notices'),
            (Script, 'scripts'),
            (TaskExecution, 'task_executions'),
            (PageScriptConfig, 'page_script_configs'),
        ]
        
        for model, key in import_order:
            if key in import_data:
                try:
                    # 清空现有数据
                    model.objects.all().delete()
                    
                    # 导入新数据
                    for item in import_data[key]:
                        model.objects.create(**item)
                        
                    self.stdout.write(f'  ✓ 导入 {model._meta.verbose_name}: {len(import_data[key])} 条记录')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️ 导入 {model._meta.verbose_name} 失败: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS('✅ 数据导入完成')
        )

    def sync_schema(self):
        """同步数据库结构"""
        self.stdout.write('🔄 同步数据库结构...')
        
        try:
            # 运行迁移
            call_command('makemigrations')
            call_command('migrate')
            
            self.stdout.write(
                self.style.SUCCESS('✅ 数据库结构同步完成')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 数据库结构同步失败: {e}')
            )
            raise

    def show_help(self):
        """显示帮助信息"""
        self.stdout.write('\n📖 数据库同步工具使用说明:')
        self.stdout.write('=' * 50)
        self.stdout.write('备份数据库:')
        self.stdout.write('  python manage.py db_sync --backup')
        self.stdout.write('')
        self.stdout.write('恢复数据库:')
        self.stdout.write('  python manage.py db_sync --restore backups/db_backup_20231201_120000.sql')
        self.stdout.write('')
        self.stdout.write('导出数据:')
        self.stdout.write('  python manage.py db_sync --export-data data_export.json')
        self.stdout.write('')
        self.stdout.write('导入数据:')
        self.stdout.write('  python manage.py db_sync --import-data data_export.json')
        self.stdout.write('')
        self.stdout.write('同步数据库结构:')
        self.stdout.write('  python manage.py db_sync --sync-schema')
        self.stdout.write('')
        self.stdout.write('指定备份目录:')
        self.stdout.write('  python manage.py db_sync --backup --backup-dir /path/to/backups')
