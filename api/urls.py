from django.urls import path
from .views import (
    UserRegistrationAPIView, PasswordChangeView, DepartmentLanguageStateView,
    UserProfileImageUpdateView, UserListAPIView, UpdateLawyerVerificationAPIView,
    LawyerListAPIView, UpdateUserVerificationAPIView, DepartmentView,
    LawyerDetails, PasswordUpdate, ResetLinkValidationCheck, OtpVerificationView,
    ResendOtp, UserDetailView, UserUpdateView, ResetPasswordView, OtpSendGoogleAuthView,
    LoginWithGoogleView, ForgetPasswordView, SaveDataRequestView
)

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
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('update_password/', PasswordUpdate.as_view(), name='user-update'),
    path('lawyer-list/', LawyerDetails.as_view(), name='lawyer-details'),
    path('departments/', DepartmentView.as_view(), name='departments'),
    path('user/profile-image/', UserProfileImageUpdateView.as_view(), name='update_profile_image'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),

    # ------------------------ADMINS-------------------------------------
    path('filter-user/', UserListAPIView.as_view(), name='filter-user'),
    path('users/update_verification/', UpdateUserVerificationAPIView.as_view(),
         name='update-user-verification'),
    path('filter-lawyer/', LawyerListAPIView.as_view(), name='filter-lawyer'),
    path('lawyer/update_verification/', UpdateLawyerVerificationAPIView.as_view(),
         name='update-lawyer-verification'),
    path('departments-languages/', DepartmentLanguageStateView.as_view(), name='departments-languages'),
]
