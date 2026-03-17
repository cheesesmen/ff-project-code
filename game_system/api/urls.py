from django.urls import path
from . import views

urlpatterns = [
    # 原有的评估接口（现在支持通过 ?game=delta 切换）
    path('valuation-analytics/', views.ValuationAnalyticsView.as_view()),
    
    # 如果你还需要单独的三角洲列表原始数据，可以保留这个（需确保 views.py 有对应函数）
    path('delta/', views.get_delta_list), 
]