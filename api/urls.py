# urls.py
from django.urls import path
from .views import UserRegistrationAPIView,OtpVerificationView,ResendOtp,ResetPasswordView,ForgetPasswordView

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view()),
    path('otpvalidation/', OtpVerificationView.as_view()),
    path('resendotp/', ResendOtp.as_view()),
    path('forgotpassword/', ForgetPasswordView.as_view()),
    path('resetpassword/', ResetPasswordView.as_view()),
]
