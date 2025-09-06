"""
Django管理命令：启动Celery Worker
"""
from django.core.management.base import BaseCommand
import subprocess
import sys
import os

class Command(BaseCommand):
    help = '启动Celery Worker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            help='日志级别 (default: info)'
        )
        parser.add_argument(
            '--concurrency',
            type=int,
            default=4,
            help='并发进程数 (default: 4)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('启动Celery Worker...')
        )
        
        # 构建命令
        cmd = [
            sys.executable, '-m', 'celery',
            '-A', 'server',
            'worker',
            '--loglevel', options['loglevel'],
            '--concurrency', str(options['concurrency'])
        ]
        
        # 在Windows上添加gevent池
        if os.name == 'nt':
            cmd.extend(['--pool', 'solo'])
        
        try:
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Celery Worker已停止')
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'启动失败: {e}')
            )
