from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .models import CustomUser
from django.core.mail import send_mail
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

import random
import os
User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    """
    Signup View: Creates a new user and sends OTP.
    """
    name=request.data.get("name")
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")
    phone = request.data.get("phone")

    if not username or not email or not password or not name:
        return Response({"error": "All fields (username, email, password) are required."}, status=status.HTTP_400_BAD_REQUEST)

    if CustomUser.objects.filter(email=email).exists():
        return Response({"error": "Email already exists"}, status=status.HTTP_409_CONFLICT)
    if CustomUser.objects.filter(username=username).exists():
        return Response({"error": "Username not available"}, status=status.HTTP_409_CONFLICT)

    print(name,username,password, email,phone)
    user = CustomUser.objects.create_user(username=username, first_name=name, email=email, password=password)
    user.generate_otp()
    send_otp_email(user.email, user.otp)

    return Response({
        "message": "Signup successful. OTP sent to email.",
        "email": user.email
    }, status=status.HTTP_201_CREATED)


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
        return Response({
            "message": "OTP verified. You can now login.",
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
@permission_classes([AllowAny])  # Allow any user to try to log in
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")
    user = CustomUser.objects.filter(email=email).first()
    if user and user.check_password(password):
        if not user.is_verified:
            return Response({"error": "User is not verified. Please verify OTP."}, status=403)

        # Generate JWT token for the user
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        return Response({
            "message": "Login successful",
            "access_token": str(access_token),  # Send access token as response
            "refresh_token": str(refresh),  # Optional: Send refresh token as well
            "email": user.email,
            "username": user.username
        }, status=200)
    else:
        return Response({"error": "Invalid email or password"}, status=401)
    
@api_view(['POST'])
@permission_classes([AllowAny])  # Allow any user to try to log in
def reset_password(request):
    email = request.data.get("email")
    user = CustomUser.objects.filter(email=email).first()
    # Generate JWT token for the user
    refresh = RefreshToken.for_user(user)   
    access_token = refresh.access_token
    return Response({
        "message": "Login successful",
        "access_token": str(access_token),  # Send access token as response
        "refresh_token": str(refresh),  # Optional: Send refresh token as well
        "email": user.email,
        "username": user.username
    }, status=200)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        # Token Authentication
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()

        # JWT Refresh Token Blacklisting
        refresh_token = request.data.get('refresh_token', None)
        if refresh_token:
            try:

                RefreshToken(refresh_token).blacklist()
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Session Logout (for session-based authentication)
        logout(request)

        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Returns user profile data (username, email, profileImage).
    """

    user = request.user
    if(user.profile_picture):
        image_url = request.build_absolute_uri(user.profile_picture.url)
    data = {
        "username": user.username,
        "email": user.email,
        "profileImage": image_url if user.profile_picture else "/default-profile.png"
    }
    return Response(data)


@api_view(['POST'])
def refresh_token(request):
    try:
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Decode refresh token to get the user
        try:
            token = RefreshToken(refresh_token)
            user_id = token.payload.get("user_id")  # Extract user ID from token payload
            user = User.objects.get(id=user_id)  # Fetch user from DB
        except TokenError:
            return Response({"error": "Invalid refresh token."}, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_403_FORBIDDEN)

        # Generate a new refresh token for the user
        new_refresh = RefreshToken.for_user(user)

        # Blacklist the old refresh token *after* issuing a new one
        try:
            token.blacklist()
        except AttributeError:
            pass  # If token blacklisting is not enabled, skip this step

        return Response({
            "access_token": str(new_refresh.access_token),
            "refresh_token": str(new_refresh)
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def reset_password_confirm(request):
    email = request.data.get("email")
    otp = request.data.get("otp")
    new_password = request.data.get("new_password")

    if not email or not otp or not new_password:
        return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)

        # Check if OTP matches
        if str(user.otp) != str(otp):
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        # Reset password
        user.password = make_password(new_password)
        user.reset_otp = None  # Clear OTP after use
        user.save()

        return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
def send_reset_otp(request):
    email = request.data.get("email")

    if not email:
        return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

    # Generate OTP (6-digit random number)
    otp = random.randint(100000, 999999)

    # Store OTP in the user model or a separate OTP table
    user.otp = otp
    user.save()

    # Send OTP via email
    send_mail(
        "Password Reset OTP",
        f"Your OTP for password reset is: {otp}",
        "noreply@yourdomain.com",
        [email],
        fail_silently=False,
    )

    return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_username(request):
    user = request.user
    new_username = request.data.get("username")

    if not new_username:
        return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=new_username).exists():
        return Response({"error": "This username is already taken."}, status=status.HTTP_409_CONFLICT)

    user.username = new_username
    user.save()

    return Response({"message": "Username updated successfully.", "username": user.username}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image(request):
    user = request.user
    profile_image = request.FILES.get('profile_image')

    if not profile_image:
        return Response({"error": "Profile image is required."}, status=status.HTTP_400_BAD_REQUEST)

    valid_extensions = ['.jpg', '.jpeg', '.png']
    file_extension = os.path.splitext(profile_image.name)[1].lower()

    if file_extension not in valid_extensions:
        return Response({"error": "Invalid file type. Only JPEG, JPG, and PNG are allowed."}, status=status.HTTP_400_BAD_REQUEST)

    if profile_image.size > 5 * 1024 * 1024:
        return Response({"error": "File size exceeds 5MB. "}, status=status.HTTP_400_BAD_REQUEST)

    user.profile_picture = profile_image
    user.save()
    image_url = request.build_absolute_uri(user.profile_picture.url)
    return Response({"message": "Profile image uploaded successfully.", "profileImage": image_url}, status=status.HTTP_200_OK)