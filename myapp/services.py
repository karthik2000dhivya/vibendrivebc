from django.core.mail import send_mail
from django.conf import settings
from .models import OTP
from .utils import generate_otp

def send_email_otp(user):
    otp_code = generate_otp()

    OTP.objects.create(
        user=user,
        otp=otp_code,
        purpose='email'
    )

    send_mail(
        subject='Your Email Verification OTP',
        message=f'Your OTP is {otp_code}. It is valid for 5 minutes.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_phone_otp(user):
    otp_code = generate_otp()

    OTP.objects.create(
        user=user,
        otp=otp_code,
        purpose='phone'
    )

    # DEV MODE (safe)
    print(f"PHONE OTP for {user.phone} is {otp_code}")

    # 🔜 Later integrate SMS provider
