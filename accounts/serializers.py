from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from accounts.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name',
            'phone_number', 'user_type', 'is_active', 'is_staff', 'is_admin',
            'date_joined', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'updated_at', 'is_staff', 'is_admin']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserRegistrationSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'full_name', 'email', 'phone_number', 'password', 'password_confirm'
        ]
    
    def validate_phone_number(self, value):
        """Validate and normalize phone number to Rwandan format"""
        phone = value.replace(' ', '').replace('-', '')
        
        # Convert +250 format to 0
        if phone.startswith('+250'):
            phone = '0' + phone[4:]
        
        # Add leading 0 if missing for 9-digit numbers
        if len(phone) == 9 and not phone.startswith('0'):
            phone = '0' + phone
        
        # Validate format: 10 digits starting with 0
        if not (len(phone) == 10 and phone.startswith('0') and phone.isdigit()):
            raise serializers.ValidationError(
                "Phone number must be 10 digits starting with 0 (e.g., 0780000000)"
            )
        
        return phone
    
    def validate_email(self, value):     
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value
    
    def validate(self, attrs):      
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs
    
    def create(self, validated_data):        
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Create user with is_active=False (will be activated after email verification)
        user = User.objects.create_user(
            **validated_data,
            password=password,
            is_active=False  
        )
        return user


class VerifyEmailSerializer(serializers.Serializer):
    """
    Serializer for verifying email using 6-digit code
    Requires both email and code for verification
    """
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate_code(self, value):
        """Validate that code is 6 digits"""
        if not value.isdigit():
            raise serializers.ValidationError("Code must be 6 digits")
        if len(value) != 6:
            raise serializers.ValidationError("Code must be exactly 6 digits")
        return value

    def validate(self, attrs):
        """Verify the code and extract user"""
        from accounts.models import VerificationCode  # Import here to avoid circular import
        
        email = attrs['email']
        code = attrs['code']
        
        # Find verification code
        try:
            verification = VerificationCode.objects.get(
                email=email,
                code=code,
                label=VerificationCode.REGISTER,
                is_verified=False
            )
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError("Invalid verification code or email")
        
        # Check if expired
        if verification.is_expired:
            raise serializers.ValidationError("Verification code has expired")
        
       # Get user
        user = verification.user
        
        # Check if already verified
        if user.is_active:
            raise serializers.ValidationError("Email already verified")
        
        attrs['user'] = user
        attrs['verification'] = verification
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):    
    
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):  
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):       
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "User with this email does not exist."
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset using 6-digit code
    Requires email, code, and new password
    """
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_code(self, value):
        """Validate that code is 6 digits"""
        if not value.isdigit():
            raise serializers.ValidationError("Code must be 6 digits")
        if len(value) != 6:
            raise serializers.ValidationError("Code must be exactly 6 digits")
        return value
    
    def validate(self, attrs):
        """Verify passwords match and code is valid"""
        from accounts.models import VerificationCode  # Import here to avoid circular import
        
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )
        
        email = attrs['email']
        code = attrs['code']
        
        # Find verification code
        try:
            verification = VerificationCode.objects.get(
                email=email,
                code=code,
                label=VerificationCode.RESET_PASSWORD,
                is_verified=False
            )
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError("Invalid reset code or email")
        
        # Check if expired
        if verification.is_expired:
            raise serializers.ValidationError("Reset code has expired")
        
        # Get user
        user = verification.user
        
        attrs['user'] = user
        attrs['verification'] = verification
        
        return attrs


class EmailChangeRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting email change
    Requires new email and current password for security
    """
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate_new_email(self, value):
        """Validate that new email is not already in use"""
        # Normalize email
        value = value.lower().strip()
        
        # Check if email already exists
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email address is already in use."
            )
        
        # Check if it's the same as current email
        user = self.context['request'].user
        if user.email.lower() == value:
            raise serializers.ValidationError(
                "New email must be different from current email."
            )
        
        return value
    
    def validate_password(self, value):
        """Verify current password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Current password is incorrect."
            )
        return value


class EmailChangeConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming email change using 6-digit code
    Requires new email and verification code
    """
    new_email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    
    def validate_code(self, value):
        """Validate that code is 6 digits"""
        if not value.isdigit():
            raise serializers.ValidationError("Code must be 6 digits")
        if len(value) != 6:
            raise serializers.ValidationError("Code must be exactly 6 digits")
        return value
    
    def validate(self, attrs):
        """Verify the code and validate email change"""
        from accounts.models import VerificationCode  # Import here to avoid circular import
        
        user = self.context['request'].user
        new_email = attrs['new_email'].lower().strip()
        code = attrs['code']
        
        # Check if new email is already taken (could have been taken since request)
        if User.objects.filter(email=new_email).exclude(id=user.id).exists():
            raise serializers.ValidationError({
                "new_email": "This email address is already in use."
            })
        
        # Find verification code
        try:
            verification = VerificationCode.objects.get(
                user=user,
                email=new_email,
                code=code,
                label=VerificationCode.EMAIL_CHANGE,
                is_verified=False
            )
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid verification code or email."
            )
        
        # Check if expired
        if verification.is_expired:
            raise serializers.ValidationError(
                "Verification code has expired. Please request a new one."
            )
        
        attrs['user'] = user
        attrs['verification'] = verification
        attrs['new_email'] = new_email
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):  
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name',
            'phone_number', 'user_type', 'is_active', 'is_staff', 'is_admin',
            'date_joined', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email', 'date_joined', 'updated_at', 
            'is_staff', 'is_admin', 'user_type'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer with email-based authentication and custom claims"""
    
    username_field = 'email'  
    
    def validate(self, attrs):
        data = super().validate(attrs)

        # Check if email is verified (user is active)
        if not self.user.is_active:
            raise serializers.ValidationError(
                "Please verify your email address before logging in."
            )
        
        # Add user data to response
        data['user'] = UserSerializer(self.user).data

        return data

    @classmethod
    def get_token(cls, user):
        """Add custom claims to token"""
        # Update last login
        User.objects.filter(id=user.id).update(last_login=timezone.now())      
        token = super().get_token(user)        
        
        # Add custom claims
        token["full_name"] = user.full_name
        token["phone_number"] = user.phone_number
        token["email"] = user.email
        token["user_type"] = user.user_type
        
        return token