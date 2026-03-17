from django.urls import path
from . import views

urlpatterns = [
    # 核心评估接口
    path('valuation-analytics/', views.ValuationAnalyticsView.as_view()),
    
    # 如果你的前端 AccountList.vue 还在请求 /api/delta/，
    # 暂时把这个路由指向一个新的函数，或者先注释掉。
    # path('delta/', views.get_delta_list), 
]