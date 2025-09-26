"""
Django管理命令：启动Celery Beat定时任务调度器
"""
from django.core.management.base import BaseCommand
import subprocess
import sys

class Command(BaseCommand):
    help = '启动Celery Beat定时任务调度器'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            help='日志级别 (default: info)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('启动Celery Beat...')
        )
        
        # 构建命令
        cmd = [
            sys.executable, '-m', 'celery',
            '-A', 'celery_app',
            'beat',
            '--loglevel', options['loglevel'],
            '--scheduler', 'django_celery_beat.schedulers:DatabaseScheduler'
        ]
        
        try:
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Celery Beat已停止')
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'启动失败: {e}')
            )
