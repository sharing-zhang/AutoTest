from django.urls import path, include
from rest_framework.routers import DefaultRouter

from myapp import views
from myapp.views import celery_views

# 创建DRF路由器
router = DefaultRouter()
router.register(r'scripts', celery_views.ScriptViewSet, basename='script')
router.register(r'page-configs', celery_views.PageScriptConfigViewSet, basename='page-config') 
router.register(r'task-executions', celery_views.TaskExecutionViewSet, basename='task-execution')
router.register(r'script-executions', celery_views.ScriptExecutionViewSet, basename='script-execution')

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
    path('admin/scanDevUpdate/scanResultsendmessage', views.admin.scanDevUpdate.sendmessage),

    path('admin/thing/list', views.admin.thing.list_api),
    path('admin/thing/detail', views.admin.thing.detail),
    path('admin/thing/create', views.admin.thing.create),
    path('admin/thing/update', views.admin.thing.update),
    path('admin/thing/delete', views.admin.thing.delete),

    path('admin/plugin/list', views.admin.plugin.list_api),
    path('admin/plugin/create', views.admin.plugin.create),
    path('admin/plugin/update', views.admin.plugin.update),
    path('admin/plugin/delete', views.admin.plugin.delete),
    path('admin/plugin/upload', views.admin.plugin.upload_exe),
    path('admin/plugin/listExe', views.admin.plugin.list_exe),
    path('admin/plugin/download', views.admin.plugin.download_exe),
    
    # 动态创建前端页面的API
    path('api/create-frontend-page/', views.page_creator.create_frontend_page),

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
    
    # 普通用户接口
    path('api/user/userLogin', views.user_views.user_login),
    path('api/user/userRegister', views.user_views.user_register),

    # 方案1 - DRF API路由
    path('api/', include(router.urls)),
    
    # 脚本配置管理接口（保留）
    path('api/script-configs/', views.celery_views.get_script_configs),
    path('api/reload-script-configs/', views.celery_views.reload_script_configs),
    

]
