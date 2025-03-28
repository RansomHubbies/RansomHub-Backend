from django.urls import path
from .views import send_message


urlpatterns = [
    path("message", send_message, name="message"),
]
