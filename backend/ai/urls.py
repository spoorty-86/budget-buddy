from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_api, name='ai_chat'),
    path('insights/', views.insights_api, name='ai_insights'),
    path('parse-expense/', views.parse_expense_api, name='ai_parse_expense'),
    path('simulate/', views.simulate_api, name='ai_simulate'),
    path('context/', views.context_api, name='ai_context'),
]
