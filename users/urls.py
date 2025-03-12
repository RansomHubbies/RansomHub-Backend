from django.urls import path
from .views import signup_view, verify_otp, resendotp, login

urlpatterns = [
    path('signup/', signup_view, name="signup"),
    path('verifyotp/', verify_otp, name="verifyotp"),
    path('resendotp/', resendotp, name="resendotp"),
    path('login/', login, name='login'),
]
