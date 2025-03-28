from django.urls import path
from .views import signup_view, verify_otp, resendotp, login,logout_view, profile_view, refresh_token,reset_password, reset_password_confirm,send_reset_otp,upload_image, update_username, verify_identity

urlpatterns = [
    path('signup/', signup_view, name="signup"),
    path('verifyotp/', verify_otp, name="verifyotp"),
    path('resendotp/', resendotp, name="resendotp"),
    path('login/', login, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('refresh/', refresh_token, name='refresh'),
    path('reset-password/', reset_password, name='reset-password'),
    path('identityverify/', reset_password_confirm, name='identityverify'),
    path('send_reset_otp/', send_reset_otp, name='send_reset_otp'),
    path('upload_image/', upload_image, name='upload_image'),
    path('update_username/', update_username, name='update_username'),
    path('verify_identity/', verify_identity, name='verify_identity'),
]
