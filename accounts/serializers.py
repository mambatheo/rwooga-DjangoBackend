from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from .models import User, VerificationCode
import datetime


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
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'full_name','email','phone_number','password','password_confirm'
        ]
    
    def validate_phone_number(self, value):      
        phone = value.replace(' ', '').replace('-', '')        
       
        if phone.startswith('+250'):
            phone = '0' + phone[4:]        
       
        if len(phone) == 9 and not phone.startswith('0'):
            phone = '0' + phone        
       
        if not (len(phone) == 10 and phone.startswith('0') and phone.isdigit()):
            raise serializers.ValidationError(
                "Phone number must be 10 digits starting with 0, or in +250 format"
            )
        
        return phone
    
    def validate(self, attrs):        
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs 
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user


class UserLoginSerializer(serializers.Serializer):
    
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
        else:
            raise serializers.ValidationError('Must include "email" and "password".')
        
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
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
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
  
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, max_length=6)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class VerificationCodeSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = VerificationCode
        fields = ['id', 'code', 'label', 'email',  'created_on', 'is_valid']
        read_only_fields = ['id', 'created_on', 'is_valid']


class UserProfileSerializer(serializers.ModelSerializer):
  
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
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        User.objects.filter(id=user.id).update(
            last_login=datetime.datetime.now())
        user.save()
        token = super().get_token(user)
        # Add custom claims
        token["full_name"] = user.full_name
        token["phone_number"] = user.phone_number
        token["email"] = user.email
        token["user_type"] = user.user_type
        return token

