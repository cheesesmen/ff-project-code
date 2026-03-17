from django.contrib import admin
from django.urls import path, include # 必须有 include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')), # 告诉总路由去 api 文件夹找子路由
]