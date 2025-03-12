from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .models import CustomUser
from django.core.mail import send_mail
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt

@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    """
    Signup View: Creates a new user and sends OTP.
    """
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if not username or not email or not password:
        return Response({"error": "All fields (username, email, password) are required."}, status=status.HTTP_400_BAD_REQUEST)

    if CustomUser.objects.filter(email=email).exists():
        return Response({"error": "Email already exists"}, status=status.HTTP_409_CONFLICT)

    print(username,password, email)
    user = CustomUser.objects.create_user(username=username, email=email, password=password)
    user.generate_otp()
    send_otp_email(user.email, user.otp)

    return Response({
        "message": "Signup successful. OTP sent to email.",
        "email": user.email
    }, status=status.HTTP_201_CREATED)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get("email")
    otp = request.data.get("otp")
    print(f"Received email: {email}, OTP: {otp}")  # Debug print
    print(email)
    user = CustomUser.objects.filter(email=email).first()
    print(user)
    if not user:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    if user.otp == otp:
        user.is_verified = True
        user.otp = None
        user.save()

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return Response({
            "message": "OTP verified. You can now login.",
            "token": token.key,
            "email": user.email,
            "username": user.username
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def resendotp(request):
    """
    Resend OTP View: Generates and resends OTP.
    """
    email = request.data.get("email")
    user = CustomUser.objects.filter(email=email).first()

    if not user:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    user.generate_otp()
    send_otp_email(user.email, user.otp)
    print("okay darling")
    return Response({
        "message": "OTP Resent.",
        "email": user.email
    }, status=status.HTTP_201_CREATED)


def send_otp_email(email, otp):
    """
    Function to send OTP via email.
    """
    subject = "Your OTP for Account Verification"
    message = f"Your OTP is: {otp}. Please enter it in the app to verify your account."
    sender_email = "your-email@example.com"  
    send_mail(subject, message, sender_email, [email])

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login View: Authenticates user and returns a token.
    """
    email = request.data.get("email")
    password = request.data.get("password")
    print(email, password)
    print("yaad rakh")
    user = CustomUser.objects.filter(email=email).first()
    print(user)
    if user and user.check_password(password):
        valid=1
    else:
        valid=0
    
    print(user)
    if valid:
        if not user.is_verified:
            return Response({"error": "User is not verified. Please verify OTP."}, status=403)

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return Response({
            "message": "Login successful",
            "token": token.key, 
            "user_id": user.id,
            "email": user.email,
            "username": user.username
        }, status=200)
    else:
        return Response({"error": "Invalid email or password"}, status=401)