from django.urls import path
from .views import ValuationAnalyticsView, trigger_sync

urlpatterns = [
    path('valuation-analytics/', ValuationAnalyticsView.as_view()),
    path('sync-market/', trigger_sync),
]