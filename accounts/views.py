import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from accounts.serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserRegistrationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
)
from accounts.permissions import IsAdmin, IsOwnerOrAdmin
from utils.registration_verification import send_registration_verification
from utils.password_reset_verification import send_password_reset_verification

logger = logging.getLogger(__name__)
User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = ["is_active", "is_staff"]
    search_fields = ["email", "full_name", "phone_number"]
    ordering_fields = ["date_joined", "full_name", "email"]
    ordering = ["-date_joined"]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        elif self.action == "list":
            return [IsAuthenticated(), IsAdmin()]
        elif self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegistrationSerializer
        return UserSerializer

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({"status": "User activated"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({"status": "User deactivated"})


class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def get_serializer_class(self):
        if self.action == "register":
            return UserRegistrationSerializer
        elif self.action == "login":
            return CustomTokenObtainPairSerializer
        elif self.action == "verify_email":
            return VerifyEmailSerializer
        elif self.action == "password_reset_request":
            return PasswordResetRequestSerializer
        elif self.action == "password_reset_confirm":
            return PasswordResetConfirmSerializer
        return CustomTokenObtainPairSerializer

    @action(detail=False, methods=["post"])
    def register(self, request):
        """Register a new user and send verification code via email"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            try:
                send_registration_verification(user)
                return Response(
                    {
                        "message": "Registration successful. Verification code sent to email.",
                        "email": user.email,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                logger.error(f"Failed to send verification email: {str(e)}")
                return Response(
                    {
                        "message": "Registration successful but failed to send verification email.",
                        "email": user.email,
                        "error": str(e),
                    },
                    status=status.HTTP_201_CREATED,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def verify_email(self, request):
        """
        Verify user's email using 6-digit code
        """
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        verification = serializer.validated_data["verification"]

        # Activate user
        user.is_active = True
        user.save(update_fields=["is_active"])
        
        # Mark verification code as used
        verification.is_verified = True
        verification.save(update_fields=["is_verified"])

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        refresh["full_name"] = user.full_name
        refresh["phone_number"] = user.phone_number
        refresh["email"] = user.email
        refresh["user_type"] = user.user_type

        return Response(
            {
                "message": "Email verified successfully",
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def resend_verification(self, request):
        """Resend verification code to user's email"""
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email address is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response(
                    {"error": "This email address is already verified. You can log in now."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            send_registration_verification(user)
            return Response(
                {"message": "A new verification code has been sent to your email."}, 
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "No account found with this email address. Please register first."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = CustomTokenObtainPairSerializer(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except TokenError as e:
            raise InvalidToken(e.args[0])

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Successfully logged out"})

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def refresh_token(self, request):
        """Refresh access token using refresh token"""
        try:
            refresh_token_str = request.data.get("refresh")
            if not refresh_token_str:
                return Response(
                    {"error": "Refresh token is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token_str)
            new_access_token = str(token.access_token)
            response_data = {"access": new_access_token}

           
            simple_jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
            if simple_jwt_settings.get('ROTATE_REFRESH_TOKENS', False):
                try:
                    token.blacklist()
                except Exception:
                    pass
                user_id = token.payload.get('user_id')
                user = User.objects.get(id=user_id)
                new_refresh_token = RefreshToken.for_user(user)
                response_data["refresh"] = str(new_refresh_token)

            logger.info(f"Token refreshed successfully for user {token.payload.get('user_id')}")
            return Response(response_data, status=status.HTTP_200_OK)

        except TokenError as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return Response(
                {"error": "Invalid or expired refresh token"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return Response(
                {"error": "Token refresh failed"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def password_reset_request(self, request):
        """Send password reset code to user's email"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            send_password_reset_verification(user)
            return Response(
                {"message": "Password reset code sent to your email."}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return Response(
                {"message": "Failed to send reset email.", "error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def password_reset_confirm(self, request):
        """
        Confirm password reset using 6-digit code and set new password
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        verification = serializer.validated_data["verification"]
        
        # Set new password
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        
        # Mark reset code as used
        verification.is_verified = True
        verification.save(update_fields=["is_verified"])

        return Response(
            {"message": "Password has been reset successfully."}, 
            status=status.HTTP_200_OK
        )


class ProfileViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["put", "patch"])
    def update_profile(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Password changed successfully"}, 
            status=status.HTTP_200_OK
        )