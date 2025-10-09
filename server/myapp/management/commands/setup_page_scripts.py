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


class Command(BaseCommand):
    help = '配置页面脚本按钮'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config-file',
            type=str,
            help='配置文件路径',
        )
        parser.add_argument(
            '--page-route',
            type=str,
            help='页面路由，如 /scanDevUpdate',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='列出指定页面的所有脚本配置',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新配置，覆盖现有配置',
        )

    def handle(self, *args, **options):
        config_file = options.get('config_file')
        page_route = options.get('page_route')
        list_mode = options.get('list', False)
        force = options.get('force', False)

        if list_mode and page_route:
            self.list_page_configs(page_route)
            return

        if not config_file:
            # 使用默认配置文件
            config_file = os.path.join(
                os.path.dirname(__file__),
                'button_configs.json'
            )

        if not os.path.exists(config_file):
            self.stdout.write(
                self.style.ERROR(f'配置文件不存在: {config_file}')
            )
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)

            self.stdout.write(f'开始处理配置文件: {config_file}')
            self.process_configs(configs, force)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'处理配置文件失败: {str(e)}')
            )

    def process_configs(self, configs, force=False):
        """处理配置文件"""
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for config in configs:
            page_route = config.get('page_route')
            scripts = config.get('scripts', [])

            if not page_route or not scripts:
                self.stdout.write(
                    self.style.WARNING(f'跳过无效配置: {config}')
                )
                skipped_count += 1
                continue

            # 检查脚本是否存在
            missing_scripts = []
            for script_name in scripts:
                if not Script.objects.filter(name=script_name, is_active=True).exists():
                    missing_scripts.append(script_name)

            if missing_scripts:
                self.stdout.write(
                    self.style.WARNING(
                        f'页面 {page_route} 的脚本不存在: {missing_scripts}'
                    )
                )
                skipped_count += 1
                continue

            # 检查是否已存在配置
            existing_config = PageScriptConfig.objects.filter(
                page_route=page_route
            ).first()

            if existing_config:
                if force:
                    # 强制更新
                    existing_config.scripts = scripts
                    existing_config.is_enabled = True
                    existing_config.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'更新页面配置: {page_route} -> {scripts}'
                        )
                    )
                else:
                    # 跳过现有配置
                    self.stdout.write(
                        self.style.WARNING(
                            f'页面 {page_route} 已存在配置，使用 --force 强制更新'
                        )
                    )
                    skipped_count += 1
            else:
                # 创建新配置
                PageScriptConfig.objects.create(
                    page_name=page_route.replace('/', '').replace('_', ' ').title(),
                    page_route=page_route,
                    scripts=scripts,
                    is_enabled=True
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'创建页面配置: {page_route} -> {scripts}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'配置处理完成! 创建: {created_count}, 更新: {updated_count}, 跳过: {skipped_count}'
            )
        )

    def list_page_configs(self, page_route):
        """列出指定页面的配置"""
        configs = PageScriptConfig.objects.filter(page_route=page_route)
        
        if not configs.exists():
            self.stdout.write(
                self.style.WARNING(f'页面 {page_route} 没有配置')
            )
            return

        self.stdout.write(f'页面 {page_route} 的配置:')
        for config in configs:
            self.stdout.write(f'  - 脚本: {config.scripts}')
            self.stdout.write(f'  - 启用: {config.is_enabled}')
            self.stdout.write(f'  - 创建时间: {config.created_at}')
            self.stdout.write('')
