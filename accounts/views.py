import logging
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
    VerifyEmailSerializer
)
from accounts.permissions import IsAdmin, IsOwnerOrAdmin
from accounts.models import VerificationCode
from utils import (
    send_registration_verification,
    send_password_reset_verification,
    verify_code
)

logger = logging.getLogger(__name__)
User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = ['is_active', 'is_staff']
    search_fields = ['email', 'full_name', 'phone_number']
    ordering_fields = ['date_joined', 'full_name', 'email']
    ordering = ['-date_joined']

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        elif self.action == "list":
            return [IsAuthenticated(), IsAdmin()]
        elif self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):       
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'User activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):       
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'User deactivated'})


class AuthViewSet(viewsets.GenericViewSet):    
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    
    def get_serializer_class(self):
        if self.action == 'register':
            return UserRegistrationSerializer
        elif self.action == 'login':
            return CustomTokenObtainPairSerializer
        elif self.action == 'verify_email':
            return VerifyEmailSerializer
        elif self.action == 'password_reset_request':
            return PasswordResetRequestSerializer
        elif self.action == 'password_reset_confirm':
            return PasswordResetConfirmSerializer
        return CustomTokenObtainPairSerializer
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new user and send verification email"""
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():           
            user = serializer.save()           
   
            try:
                send_registration_verification(user)
                return Response({
                    "message": "Registration successful. Verification code sent to email.",
                    "email": user.email
                }, status=status.HTTP_201_CREATED)
            except Exception as e:               
                return Response({
                    "message": "Registration successful but failed to send verification email.",
                    "email": user.email,
                    "error": str(e)
                }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_email(self, request):
        """Verify user's email with verification code"""
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
     
        is_valid, verification_code, error_message = verify_code(
            email=email,
            code=code,
            label=VerificationCode.REGISTER
        )

        if not is_valid:
            return Response(
                {"error": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
   
        try:
            user = User.objects.get(email=email)
            user.is_active = True
            user.save()           
     
            verification_code.email_verified = True
            verification_code.save()            
        
            # Generate JWT tokens with custom claims
            refresh = RefreshToken.for_user(user)
            
            # Add custom claims to tokens
            refresh['full_name'] = user.full_name
            refresh['phone_number'] = user.phone_number
            refresh['email'] = user.email
            refresh['user_type'] = user.user_type
            
            return Response({
                "message": "Email verified successfully",
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def resend_verification(self, request):
        """Resend verification code to user's email"""
        email = request.data.get('email')
        
        if not email:
            return Response(
                {"error": "Email address is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)           
      
            if user.is_active:
                logger.warning(f"Verification resend attempted for already verified email: {email}")
                return Response(
                    {"error": "This email address is already verified. You can log in now."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                send_registration_verification(user)
                logger.info(f"Verification code resent to {email}")
                return Response({
                    "message": "A new verification code has been sent to your email."
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Failed to resend verification to {email}: {str(e)}")
                return Response({
                    "error": "Failed to send verification email. Please try again later."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except User.DoesNotExist:
            logger.warning(f"Verification resend attempted for non-existent email: {email}")
            return Response(
                {"error": "No account found with this email address. Please register first."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login with email and password, returns JWT tokens with custom claims"""
        serializer = CustomTokenObtainPairSerializer(data=request.data, context={'request': request})
        
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout by blacklisting the refresh token"""
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        """Request password reset code"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                verification_code = send_password_reset_verification(email)
                
                if verification_code:
                    logger.info(f"Password reset code sent to {email}")
                    return Response({
                        'message': 'A password reset code has been sent to your email address.',
                    }, status=status.HTTP_200_OK)
                else:
                    logger.warning(f"Password reset requested for non-existent email: {email}")
                    return Response(
                        {'error': 'No account found with this email address.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            except Exception as e:
                logger.error(f"Failed to send password reset to {email}: {str(e)}")
                return Response(
                    {'error': 'Failed to send password reset email. Please try again later.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request):
        """Confirm password reset with verification code"""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']
            
            is_valid, verification_code, error_message = verify_code(
                email=email,
                code=code,
                label=VerificationCode.RESET_PASSWORD
            )
            
            if not is_valid:
                logger.warning(f"Failed password reset attempt for {email}: {error_message}")
                return Response(
                    {'error': error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                verification_code.email_verified = True
                verification_code.save()
                
                logger.info(f"Password reset successful for {email}")
                
                return Response(
                    {'message': 'Password has been reset successfully. You can now log in with your new password.'},
                    status=status.HTTP_200_OK
                )
            
            except User.DoesNotExist:
                logger.error(f"User not found during password reset: {email}")
                return Response(
                    {'error': 'User account not found. Please register again.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.GenericViewSet):
    """ViewSet for user profile operations"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user's profile"""
        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change current user's password"""
        serializer = ChangePasswordSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response(
                {'message': 'Password changed successfully'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)