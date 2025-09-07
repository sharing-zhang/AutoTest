from django.urls import path, include
from rest_framework.routers import DefaultRouter

from myapp import views
from myapp.views import celery_views

# 创建DRF路由器
router = DefaultRouter()
router.register(r'scripts', celery_views.ScriptViewSet, basename='script')
router.register(r'page-configs', celery_views.PageScriptConfigViewSet, basename='page-config') 
router.register(r'task-executions', celery_views.TaskExecutionViewSet, basename='task-execution')

app_name = 'myapp'
urlpatterns = [
    # api
    path('admin/overview/count', views.admin.overview.count),
    path('admin/overview/sysInfo', views.admin.overview.sysInfo),
    # scanUpdate资源扫描各项目详细信息页面接口路由,记得在views/admin/__init__.py也加上新增的路由
    path('admin/scanUpdate/list', views.admin.scanUpdate.list_api),
    path('admin/scanUpdate/detail', views.admin.scanUpdate.detail),
    path('admin/scanUpdate/create', views.admin.scanUpdate.create),
    path('admin/scanUpdate/update', views.admin.scanUpdate.update),
    path('admin/scanUpdate/delete', views.admin.scanUpdate.delete),
    # scanDevUpdate是国内资源扫描项目下的接口
    path('admin/scanDevUpdate/scanResultlist', views.admin.scanDevUpdate.list_api),
    path('admin/scanDevUpdate/scanResultcreate', views.admin.scanDevUpdate.create),
    path('admin/scanDevUpdate/scanResultupdate', views.admin.scanDevUpdate.update),
    path('admin/scanDevUpdate/scanResultdelete', views.admin.scanDevUpdate.delete),
    path('admin/scanDevUpdate/scanResultdetail', views.admin.scanDevUpdate.detail),

    path('admin/thing/list', views.admin.thing.list_api),
    path('admin/thing/detail', views.admin.thing.detail),
    path('admin/thing/create', views.admin.thing.create),
    path('admin/thing/update', views.admin.thing.update),
    path('admin/thing/delete', views.admin.thing.delete),

    path('admin/plugin/list', views.admin.thing.list_api),
    path('admin/plugin/detail', views.admin.thing.detail),
    path('admin/plugin/create', views.admin.thing.create),
    path('admin/plugin/update', views.admin.thing.update),
    path('admin/plugin/delete', views.admin.thing.delete),

    path('admin/comment/list', views.admin.comment.list_api),
    path('admin/comment/create', views.admin.comment.create),
    path('admin/comment/update', views.admin.comment.update),
    path('admin/comment/delete', views.admin.comment.delete),
    path('admin/classification/list', views.admin.classification.list_api),
    path('admin/classification/create', views.admin.classification.create),
    path('admin/classification/update', views.admin.classification.update),
    path('admin/classification/delete', views.admin.classification.delete),
    path('admin/tag/list', views.admin.tag.list_api),
    path('admin/tag/create', views.admin.tag.create),
    path('admin/tag/update', views.admin.tag.update),
    path('admin/tag/delete', views.admin.tag.delete),
    path('admin/ad/list', views.admin.ad.list_api),
    path('admin/ad/create', views.admin.ad.create),
    path('admin/ad/update', views.admin.ad.update),
    path('admin/ad/delete', views.admin.ad.delete),
    path('admin/notice/list', views.admin.notice.list_api),
    path('admin/notice/create', views.admin.notice.create),
    path('admin/notice/update', views.admin.notice.update),
    path('admin/notice/delete', views.admin.notice.delete),
    path('admin/loginLog/list', views.admin.loginLog.list_api),
    path('admin/loginLog/create', views.admin.loginLog.create),
    path('admin/loginLog/update', views.admin.loginLog.update),
    path('admin/loginLog/delete', views.admin.loginLog.delete),
    path('admin/opLog/list', views.admin.opLog.list_api),
    path('admin/errorLog/list', views.admin.errorLog.list_api),
    path('admin/user/list', views.admin.user.list_api),
    path('admin/user/create', views.admin.user.create),
    path('admin/user/update', views.admin.user.update),
    path('admin/user/updatePwd', views.admin.user.updatePwd),
    path('admin/user/delete', views.admin.user.delete),
    path('admin/user/info', views.admin.user.info),
    path('admin/adminLogin', views.admin.user.admin_login),

    # 方案1 - DRF API路由
    path('api/', include(router.urls)),
    
    # celery任务相关接口
    path('admin/celery/execute-script', views.celery_views.execute_script_task),
    path('admin/celery/script-task-result', views.celery_views.get_script_task_result),
    path('admin/celery/scripts', views.celery_views.list_scripts),
    path('admin/celery/scripts/<int:script_id>', views.celery_views.get_script_detail),
    
    # 动态脚本配置管理接口
    path('api/script-configs/', views.celery_views.get_script_configs),
    path('api/execute-dynamic-script/', views.celery_views.execute_dynamic_script),
    path('api/get-script-task-result/', views.celery_views.get_script_task_result),
    path('api/reload-script-configs/', views.celery_views.reload_script_configs),

]
