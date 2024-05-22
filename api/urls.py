# urls.py
from django.urls import path
from .views import UserRegistrationAPIView,PasswordUpdate,ResetLinkValidationCheck,OtpVerificationView,ResendOtp,UserDetailView,UserUpdateView,ResetPasswordView,OtpSendGoogleAuthView,LoginWithGoogleView,ForgetPasswordView,SaveDataRequestView

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view()),
    path('otpvalidation/', OtpVerificationView.as_view()),
    path('resendotp/', ResendOtp.as_view()),
    path('forgotpassword/', ForgetPasswordView.as_view()),
    path('resetpassword/', ResetPasswordView.as_view()),
    path('resetvalidation/', ResetLinkValidationCheck.as_view()),
    path('login-with-google/', LoginWithGoogleView.as_view()),
    path('save-data-request/', SaveDataRequestView.as_view()),
    path('otpsend/', OtpSendGoogleAuthView.as_view()),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('update_password/', PasswordUpdate.as_view(), name='user-update'),
]
