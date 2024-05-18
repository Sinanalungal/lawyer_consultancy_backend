from django.urls import path
from . import views

urlpatterns = [
    path('blogs/', views.BlogListCreateAPIView.as_view(), name='blog-list-create'),
    path('blogs/<int:pk>/', views.BlogDetailAPIView.as_view(), name='blog-detail'),
    path('likes/', views.LikeAPIView.as_view(), name='like-create'),
    path('comments/', views.CommentCreateAPIView.as_view(), name='comment-create'),
    path('saved/', views.SaveAPIView.as_view(), name='save-create'),
    # path('likes/<int:pk>/', views.LikeDetailAPIView.as_view(), name='like-detail'),
    path('comments/', views.CommentCreateAPIView.as_view(), name='comment-create'),
    # path('comments/<int:pk>/', views.CommentDetailAPIView.as_view(), name='comment-detail'),
]
