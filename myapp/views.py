from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *

from .services import *
# class RegisterAPIView(APIView):
#     def post(self, request):
#         serializer = UserSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()

#         send_email_otp(user)
#         send_phone_otp(user) 

#         return Response(
#             {"message": "Registered. Verify email & phone."},
#             status=201
#         )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RegisterSerializer
from .services import send_email_otp


class RegisterAPIView(APIView):
    def post(self, request):
        # serializer = RegisterSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)

        # user = serializer.save()   # ✅ USER CREATED HERE
        print(request.data)
        #send_email_otp(user)       # ✅ OTP SENT TO SAME USER
        #send_phone_otp(user)
        serializer = User(username=request.data['name'],email=request.data['email'],phone=request.data['mobileNumber'])
        serializer.set_password(request.data['password'])
        if serializer.is_valid():
            serializer.save()
        return Response(
            {
                "message": "Registration successful. OTP sent to email."
            },
            status=status.HTTP_201_CREATED
        )

    
class VerifyOTPAPIView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp_obj = serializer.validated_data['otp_obj']
        user = otp_obj.user

        otp_obj.is_used = True
        otp_obj.save()

        if otp_obj.purpose == 'email':
            user.is_email_verified = True
        else:
            user.is_phone_verified = True

        user.save()

        return Response(
            {"message": "OTP verified successfully"},
            status=status.HTTP_200_OK
        )
    
from .services import send_email_otp, send_phone_otp

class ResendOTPAPIView(APIView):
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        purpose = serializer.validated_data['purpose']

        # Invalidate old OTPs
        OTP.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False
        ).update(is_used=True)

        if purpose == 'email':
            send_email_otp(user)
        else:
            send_phone_otp(user)

        return Response(
            {"message": f"{purpose.capitalize()} OTP sent successfully"},
            status=status.HTTP_200_OK
        )

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed

class LoginAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = User.objects.filter(email=email).first()

        if not user:
            raise AuthenticationFailed("User not found")

        if not user.check_password(password):
            raise AuthenticationFailed("Invalid password")

        if not user.is_email_verified:
            raise AuthenticationFailed("Email not verified")

        if not user.is_phone_verified:
            raise AuthenticationFailed("Phone not verified")

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })
from rest_framework.permissions import IsAuthenticated

class UserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        return response