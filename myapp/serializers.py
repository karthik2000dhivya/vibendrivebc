from rest_framework import serializers
from .models import User, OTP
from .utils import generate_otp


from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "password",
        )
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already registered")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user

    
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    purpose = serializers.ChoiceField(choices=['email', 'phone'])

    def validate(self, data):
        from .models import OTP

        email = data['email'].lower().strip()

        otp_obj = OTP.objects.filter(
            user__email=email,
            otp=data['otp'],
            purpose=data['purpose'],
            is_used=False
        ).first()

        if not otp_obj:
            raise serializers.ValidationError("Invalid OTP")

        if otp_obj.is_expired():
            raise serializers.ValidationError("OTP expired")

        data['otp_obj'] = otp_obj
        return data
from rest_framework import serializers
from django.utils.timezone import now, timedelta
from .models import User, OTP

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=['email', 'phone'])

    def validate(self, data):
        email = data['email'].lower().strip()
        purpose = data['purpose']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        # ⏱ 1. Rate limit: 60 seconds
        recent_otp = OTP.objects.filter(
            user=user,
            purpose=purpose
        ).order_by('-created_at').first()

        if recent_otp and (now() - recent_otp.created_at).seconds < 60:
            raise serializers.ValidationError(
                "Please wait 60 seconds before requesting another OTP"
            )

        # 🔢 2. Max 5 OTPs per hour
        otp_count = OTP.objects.filter(
            user=user,
            purpose=purpose,
            created_at__gte=now() - timedelta(hours=1)
        ).count()

        if otp_count >= 5:
            raise serializers.ValidationError(
                "OTP limit exceeded. Try again after 1 hour"
            )

        data['user'] = user
        return data
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data['email'].lower().strip()
        password = data['password']

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        # 🚫 BLOCK LOGIN IF EMAIL NOT VERIFIED
        if not user.is_email_verified:
            raise serializers.ValidationError(
                "Email is not verified. Please verify your email before login."
            )

        data['user'] = user
        return data
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
