"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

    地址和视图函数的映射关系---urls.py  文件
    #谨记，视图函数写好一定要配个路由，不然没办法映射
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from server import settings

# urlpatterns列表，列表内放了url函数的执行结果
# 使用很简单，复制一行，改一下第一个参数（正则表达式），第二个参数是视图函数内存地址
# 在内部，请求来了，路径匹配成功，内部自动调用index(request),把request传入
urlpatterns = [
    path('admin/', admin.site.urls),
    path('myapp/', include('myapp.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
