'''
    与数据库相关的内容
'''

from django.db import models
from django_celery_results.models import TaskResult


class User(models.Model):
    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
    )
    ROLE_CHOICES = (
        ('0', '管理员'),
        ('1', '普通用户'),
    )
    STATUS_CHOICES = (
        ('0', '正常'),
        ('1', '封号'),
    )
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, null=True)
    password = models.CharField(max_length=50, null=True)
    role = models.CharField(max_length=2, blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    nickname = models.CharField(blank=True, null=True, max_length=20)
    avatar = models.FileField(upload_to='avatar/', null=True)
    mobile = models.CharField(max_length=13, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    description = models.TextField(max_length=200, null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    score = models.IntegerField(default=0, blank=True, null=True)
    push_email = models.CharField(max_length=40, blank=True, null=True)
    push_switch = models.BooleanField(blank=True, null=True, default=False)
    admin_token = models.CharField(max_length=32, blank=True, null=True)
    token = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return self.username or f"用户{self.id}"
    
    class Meta:
        db_table = "b_user"

class Plugin(models.Model):
    id = models.BigAutoField(primary_key=True)
    image = models.ImageField(upload_to='ad/', null=True)
    link = models.CharField(max_length=500, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_plugin"



# # http://172.16.34.33:8001/admin/scanUpdate 链接下展示资源扫描各项目详细信息页面关联数据库声明的字段
class ScanUpdate(models.Model):
    STATUS_CHOICES = (
        ('0', '可用'),
        ('1', '删除'),
    )
    id = models.BigAutoField(primary_key=True)
    projectname = models.CharField(max_length=30, blank=True, null=True)
    description = models.CharField(max_length=60, blank=True, null=True)
    versionnumber = models.CharField(max_length=20, blank=True, null=True)
    # auto_now_add=True会导致时间变为只可读，导致无法修改
    lastupdatetime = models.DateTimeField(auto_now_add=False, null=True)
    lastupdates = models.CharField(max_length=60, blank=True, null=True)
    director = models.CharField(max_length=20, blank=True, null=True)
    remark = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    child_url_key = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        # 关联的数据库
        db_table = "b_scanUpdateProject"

# http://172.16.34.33:8001/admin/scanUpdate/scanDevUpdate 扫描结果页签下详细信息展示内容
class ScanDevUpdate_scanResult(models.Model):
    STATUS_CHOICES = (
        ('0', '可用'),
        ('1', '删除'),
    )
    
    RESULT_TYPE_CHOICES = (
        ('manual', '手动扫描'),
        ('script', '脚本执行'),
        ('task', '任务执行'),
    )
    
    EXECUTION_STATUS_CHOICES = (
        ('SUCCESS', '成功'),
        ('FAILURE', '失败'),
        ('RUNNING', '运行中'),
        ('PENDING', '等待中'),
        ('TIMEOUT', '超时'),
        ('CANCELLED', '已取消'),
    )
    
    id = models.BigAutoField(primary_key=True)
    scandevresult_filename = models.CharField(max_length=120, blank=True, null=True)
    # auto_now_add=True会导致时间变为只可读，导致无法修改
    scandevresult_time = models.DateTimeField(auto_now_add=False, null=True)
    director = models.CharField(max_length=20, blank=True, null=True)
    remark = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    scandevresult_content = models.TextField(blank=True, null=True)
    
    # 新增字段用于脚本执行结果
    result_type = models.CharField(max_length=10, choices=RESULT_TYPE_CHOICES, default='manual', verbose_name="结果类型")
    script_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="脚本名称")
    task_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="任务ID")
    execution_time = models.FloatField(null=True, blank=True, verbose_name="执行时间(秒)")
    script_output = models.TextField(blank=True, null=True, verbose_name="脚本输出")
    error_message = models.TextField(blank=True, null=True, verbose_name="错误信息")
    
    # 执行状态和结果摘要
    execution_status = models.CharField(
        max_length=20, 
        choices=EXECUTION_STATUS_CHOICES, 
        default='PENDING', 
        verbose_name="执行状态"
    )
    result_summary = models.TextField(
        max_length=1000, 
        blank=True, 
        null=True, 
        verbose_name="结果摘要"
    )
    
    # 执行参数
    parameters = models.JSONField(
        default=dict, 
        blank=True, 
        null=True, 
        verbose_name="执行参数"
    )

    class Meta:
        # 关联的数据库
        db_table = "b_scanDevUpdate"


class Thing(models.Model):
    STATUS_CHOICES = (
        ('0', '上架'),
        ('1', '下架'),
    )
    id = models.BigAutoField(primary_key=True)
    classification = models.CharField(max_length=20, blank=True, null=True)
    tag = models.CharField(max_length=20, blank=True, null=True)
    xuehao = models.CharField(max_length=20, blank=True, null=True)
    name = models.CharField(max_length=20, blank=True, null=True)
    sex = models.CharField(max_length=20, blank=True, null=True)
    birthday = models.CharField(max_length=20, blank=True, null=True)
    jiguan = models.CharField(max_length=20, blank=True, null=True)
    sfz = models.CharField(max_length=20, blank=True, null=True)
    minzu = models.CharField(max_length=20, blank=True, null=True)
    remark = models.CharField(max_length=30, blank=True, null=True)
    cover = models.ImageField(upload_to='cover/', null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_thing"



class OpLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    re_ip = models.CharField(max_length=100, blank=True, null=True)
    re_time = models.DateTimeField(auto_now_add=True, null=True)
    re_url = models.CharField(max_length=200, blank=True, null=True)
    re_method = models.CharField(max_length=10, blank=True, null=True)
    re_content = models.CharField(max_length=200, blank=True, null=True)
    access_time = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = "b_op_log"


class ErrorLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    ip = models.CharField(max_length=100, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    method = models.CharField(max_length=10, blank=True, null=True)
    content = models.CharField(max_length=200, blank=True, null=True)
    log_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_error_log"



class Script(models.Model):
    """脚本配置表"""
    name = models.CharField(max_length=200, verbose_name="脚本名称")
    description = models.TextField(blank=True, verbose_name="描述")
    script_path = models.CharField(max_length=500, verbose_name="脚本路径")
    script_type = models.CharField(max_length=50, choices=[
        ('data_analysis', '数据分析'),
        ('report_generation', '报表生成'),
        ('data_processing', '数据处理'),
        ('machine_learning', '机器学习'),
    ], verbose_name="脚本类型")
    parameters_schema = models.JSONField(default=dict, verbose_name="参数模式")
    visualization_config = models.JSONField(default=dict, verbose_name="可视化配置")
    dialog_title = models.CharField(max_length=200, blank=True, verbose_name="脚本中文名称")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or f"脚本{self.id}"
    
    class Meta:
        db_table = 'c_scripts'
        verbose_name = "脚本配置"
        verbose_name_plural = "脚本配置"

class TaskExecution(models.Model):
    """任务执行记录表"""
    STATUS_CHOICES = [
        ('PENDING', '等待中'),
        ('STARTED', '执行中'),
        ('SUCCESS', '成功'),
        ('FAILURE', '失败'),
        ('RETRY', '重试中'),
        ('REVOKED', '已取消'),
    ]
    
    task_id = models.CharField(max_length=255, unique=True, verbose_name="任务ID", db_index=True)
    script = models.ForeignKey(Script, on_delete=models.CASCADE, verbose_name="关联脚本")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="执行用户")
    page_context = models.CharField(max_length=200, verbose_name="页面上下文")
    
    # 关联Celery任务结果
    celery_task = models.OneToOneField(
        TaskResult, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='script_execution'
    )
    
    # 执行参数和结果
    parameters = models.JSONField(default=dict, verbose_name="执行参数")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    result = models.JSONField(null=True, blank=True, verbose_name="执行结果")
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    
    # 时间统计
    execution_time = models.FloatField(null=True, verbose_name="执行时间(秒)")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # 执行统计（用于快速查询）
    processed_records = models.IntegerField(default=0, verbose_name="处理记录数")
    success_records = models.IntegerField(default=0, verbose_name="成功记录数")
    failed_records = models.IntegerField(default=0, verbose_name="失败记录数")
    
    # 资源使用情况
    memory_usage = models.FloatField(null=True, verbose_name="内存使用(MB)")
    cpu_usage = models.FloatField(null=True, verbose_name="CPU使用率")
    
    class Meta:
        db_table = 'c_task_executions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['script', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['page_context']),
        ]
        verbose_name = "任务执行记录"
        verbose_name_plural = "任务执行记录"


class LoginLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    ip = models.CharField(max_length=100, blank=True, null=True)
    ua = models.CharField(max_length=200, blank=True, null=True)
    log_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_login_log"


class PageScriptConfig(models.Model):
    """页面脚本配置表 - 支持一个页面配置多个脚本"""
    page_name = models.CharField(max_length=200, verbose_name="页面名称")
    page_route = models.CharField(max_length=200, verbose_name="页面路由")
    scripts = models.JSONField(default=list, verbose_name="脚本名称列表")
    is_enabled = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta:
        db_table = 'c_page_script_configs'
        unique_together = ['page_route']

class FileRecord(models.Model):
    """文件记录表 - 存储备份文件信息"""
    backup_time = models.DateTimeField(auto_now_add=True, verbose_name="备份时间")
    backup_file_name = models.CharField(
        max_length=255,
        verbose_name="备份文件名称",
        default='unknown_backup'  # 添加默认值
    )
    backup_path = models.CharField(
        max_length=500,
        verbose_name="备份路径",
        default='/tmp'  # 添加默认值
    )

    class Meta:
        db_table = 'c_file_records'
        unique_together = ['backup_path', 'backup_file_name']
        verbose_name = "文件记录"
        verbose_name_plural = "文件记录"

    def __str__(self):
        return f"{self.backup_path}/{self.backup_file_name}"

    @property
    def full_backup_path(self):
        """获取完整备份文件路径"""
        return f"{self.backup_path.rstrip('/')}/{self.backup_file_name}"