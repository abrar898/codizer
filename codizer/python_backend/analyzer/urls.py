from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze_code, name='analyze_code'),
    path('history/', views.get_analysis_history, name='analysis_history'),
] 