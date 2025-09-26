from django.contrib import admin

# Register your models here.
from myapp.models import Thing, User, OpLog, ErrorLog, LoginLog, Script, TaskExecution, PageScriptConfig, ScanDevUpdate_scanResult

# 注册基础模型
admin.site.register(Thing)
admin.site.register(User)

# 注册日志模型
@admin.register(OpLog)
class OpLogAdmin(admin.ModelAdmin):
    """操作日志管理"""
    list_display = ['id', 're_ip', 're_method', 're_url', 're_time', 'access_time']
    list_filter = ['re_method', 're_time']
    search_fields = ['re_ip', 're_url']
    readonly_fields = ['re_time']
    ordering = ['-re_time']
    list_per_page = 50

@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    """错误日志管理"""
    list_display = ['id', 'ip', 'method', 'url', 'log_time']
    list_filter = ['method', 'log_time']
    search_fields = ['ip', 'url', 'content']
    readonly_fields = ['log_time']
    ordering = ['-log_time']
    list_per_page = 50

@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    """登录日志管理"""
    list_display = ['id', 'ip', 'username', 'log_time', 'ua']
    list_filter = ['log_time']
    search_fields = ['ip', 'username']
    readonly_fields = ['log_time']
    ordering = ['-log_time']
    list_per_page = 50

# 注册脚本相关模型
@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    """脚本管理"""
    list_display = ['id', 'name', 'script_path', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'script_type']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

@admin.register(TaskExecution)
class TaskExecutionAdmin(admin.ModelAdmin):
    """任务执行记录管理"""
    list_display = ['id', 'get_script_name', 'get_user_name', 'status', 'created_at', 'completed_at', 'execution_time']
    list_filter = ['status', 'created_at', 'script']
    search_fields = ['script__name', 'user__username', 'task_id']
    readonly_fields = ['created_at', 'task_id']
    ordering = ['-created_at']
    list_per_page = 50
    
    def get_script_name(self, obj):
        """获取脚本名称"""
        return obj.script.name if obj.script else '-'
    get_script_name.short_description = '脚本名称'
    get_script_name.admin_order_field = 'script__name'
    
    def get_user_name(self, obj):
        """获取用户名"""
        return obj.user.username if obj.user else '-'
    get_user_name.short_description = '执行用户'
    get_user_name.admin_order_field = 'user__username'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('task_id', 'script', 'user', 'page_context', 'status')
        }),
        ('执行参数', {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
        ('执行结果', {
            'fields': ('result', 'error_message'),
            'classes': ('collapse',)
        }),
        ('时间统计', {
            'fields': ('created_at', 'started_at', 'completed_at', 'execution_time')
        }),
        ('资源使用', {
            'fields': ('memory_usage', 'cpu_usage'),
            'classes': ('collapse',)
        }),
        ('执行统计', {
            'fields': ('processed_records', 'success_records', 'failed_records'),
            'classes': ('collapse',)
        })
    )

@admin.register(PageScriptConfig)
class PageScriptConfigAdmin(admin.ModelAdmin):
    """页面脚本配置管理"""
    list_display = ['id', 'script', 'page_route', 'button_text', 'position', 'is_enabled']
    list_filter = ['page_route', 'position', 'is_enabled']
    search_fields = ['script__name', 'page_route', 'button_text']
    ordering = ['page_route', 'display_order']

@admin.register(ScanDevUpdate_scanResult)
class ScanDevUpdateScanResultAdmin(admin.ModelAdmin):
    """扫描结果管理"""
    list_display = ['id', 'scandevresult_filename', 'result_type', 'script_name', 'scandevresult_time', 'status']
    list_filter = ['result_type', 'status', 'scandevresult_time']
    search_fields = ['scandevresult_filename', 'script_name', 'remark']
    readonly_fields = ['scandevresult_time']
    ordering = ['-scandevresult_time']
    list_per_page = 50
