#!/usr/bin/env python3
"""
运行此脚本来设置celery的所有必要配置
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.core.management import call_command
from myapp.models import Script, PageScriptConfig

def main():
    print("🚀 开始设置方案1 - 统一任务执行器")
    print("=" * 50)
    
    # 1. 注册脚本
    print("📝 1. 扫描和注册脚本...")
    try:
        call_command('register_scripts', '--force')
        print("✅ 脚本注册完成")
    except Exception as e:
        print(f"❌ 脚本注册失败: {e}")
        return
    
    # 2. 设置页面配置
    print("\n🔧 2. 设置页面按钮配置...")
    try:
        call_command('setup_page_scripts')
        print("✅ 页面配置完成")
    except Exception as e:
        print(f"❌ 页面配置失败: {e}")
        # 继续执行，不中断
    
    # 3. 验证配置
    print("\n🔍 3. 验证方案1配置...")
    
    scripts = Script.objects.filter(is_active=True)
    print(f"📊 已注册脚本数量: {scripts.count()}")
    
    for script in scripts:
        print(f"  - {script.name}: {script.script_path}")
        if script.name in ['print_test_script', 'example_script']:
            print(f"    ✅ 方案1脚本: {script.description}")
    
    # 4. 显示测试指南
    print("\n🎯 4. 测试指南")
    print("-" * 30)
    print("现在你可以测试方案1的实现：")
    print("")
    print("启动服务:")
    print("  1. redis-server")
    print("  2. cd server && celery -A celery_app worker --loglevel=info")  
    print("  3. cd server && python manage.py runserver")
    print("")
    print("测试API:")
    print("  GET  /myapp/admin/celery/scripts?page_route=/scanDevUpdate")
    print("  POST /myapp/admin/celery/execute-script")
    print("       {\"script_id\": 脚本ID, \"parameters\": {\"greeting\": \"Hello!\"}}")
    print("")
    print("前端测试:")
    print("  打开 http://localhost:8000/scanDevUpdate")
    print("  点击 '运行Print测试 (方案1)' 按钮")
    print("")
    
    # 5. 显示可用脚本
    print("📋 5. 可用的方案1脚本:")
    v1_scripts = scripts.filter(
        name__in=['print_test_script', 'example_script']
    )
    
    for script in v1_scripts:
        print(f"\n🔸 {script.name}")
        print(f"   描述: {script.description}")
        print(f"   路径: {script.script_path}")
        print(f"   参数: {script.parameters_schema}")
    
    print("\n🎉 方案1设置完成!")
    print("=" * 50)

if __name__ == '__main__':
    main()
