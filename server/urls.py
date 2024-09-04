"""
URL configuration for server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from graphene_django.views import GraphQLView
from api.views import MyTokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/userdata/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/', include('api.urls')),
    path('adminside/', include('adminside.urls')),
    path('blogsession/', include('blog.urls')),
    path('subscriptions/', include('subscription.urls')),
    path('chat/', include('chat.urls')),
    path('case-manage/', include('case.urls')),
    path('schedule/', include('schedule.urls')),
    path('userside/', include('userside.urls')),
    path('wallet/', include('wallet.urls')),
    path('dashboard/', include('dashboard.urls')),
    # path("graphql/", GraphQLView.as_view(graphiql=True)),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)