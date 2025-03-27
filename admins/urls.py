from django.urls import path
from .views import *

urlpatterns = [
    path('users/', list_users, name='list_users'),
    path('users/<int:user_id>/', remove_user, name='remove_user'),
    path('users/<int:user_id>/toggle_suspension/', toggle_user_suspension, name='toggle_user_suspension'),
    path('logs/', list_activity_logs, name='list_activity_logs'),
    path('logs/create/', create_log_entry, name='create_log_entry'),
]
