# game_system/api/urls.py
from django.urls import path
from .views import ValuationAnalyticsView

urlpatterns = [
    path('valuation-analytics/', ValuationAnalyticsView.as_view()),
]