#!/usr/bin/env python
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from myapp.models import ScanDevUpdate_scanResult

def clear_scan_data():
    """清空扫描结果数据"""
    count = ScanDevUpdate_scanResult.objects.count()
    print(f"删除前，b_scanDevUpdate表中有 {count} 条记录")
    
    if count > 0:
        # 显示前5条记录
        print("前5条记录:")
        for item in ScanDevUpdate_scanResult.objects.all().order_by('-scandevresult_time')[:5]:
            print(f"ID: {item.id}, 文件名: {item.scandevresult_filename}, 时间: {item.scandevresult_time}")
        
        # 确认删除
        confirm = input(f"\n确定要删除这 {count} 条记录吗？(y/N): ")
        if confirm.lower() == 'y':
            ScanDevUpdate_scanResult.objects.all().delete()
            print("数据删除成功！")
        else:
            print("取消删除操作")
    else:
        print("表中没有数据")

if __name__ == "__main__":
    clear_scan_data()
