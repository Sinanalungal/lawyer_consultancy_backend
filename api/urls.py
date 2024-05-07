# urls.py
from django.urls import path
from .views import UserRegistrationAPIView,OtpVerificationView,ResendOtp,ResetPasswordView,OtpSendGoogleAuthView,LoginWithGoogleView,ForgetPasswordView,SaveDataRequestView

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view()),
    path('otpvalidation/', OtpVerificationView.as_view()),
    path('resendotp/', ResendOtp.as_view()),
    path('forgotpassword/', ForgetPasswordView.as_view()),
    path('resetpassword/', ResetPasswordView.as_view()),
    path('login-with-google/', LoginWithGoogleView.as_view()),
    path('save-data-request/', SaveDataRequestView.as_view()),
    path('otpsend/', OtpSendGoogleAuthView.as_view()),
]
