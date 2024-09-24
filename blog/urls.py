from django.urls import path
from . import views

urlpatterns = [
    path('create-blog/', views.BlogCreateAPIView.as_view(), name='blog-create'),
    path('blogs/', views.BlogListAPIView.as_view(), name='blog-list'),
    path('personal-blogs/', views.PersonalBlogListAPIView.as_view(), name='blog-list'),
    path('blogs/users/', views.BlogUserListView.as_view(), name='blog-list-users'),
    path('blogs/update_is_listed/', views.BlogUpdateIsListedView.as_view(), name='blog-update-is-listed'),
    path('blogs/like/', views.LikeBlogView.as_view(), name='like-blog'),
    path('blogs/comments/', views.CommentBlogView.as_view(), name='comment-blog'),
    path('blogs/report/<int:pk>/', views.ReportBlogView.as_view(), name='report-blog'),
    path('blogs/save/', views.SaveBlogView.as_view(), name='save-blog'),
    path('comments/edit/<int:pk>/', views.CommentEditView.as_view(), name='edit-comment'),
    path('comments/delete/<int:pk>/', views.CommentDeleteView.as_view(), name='delete-comment'),
    path('blog-update/<int:id>/', views.BlogDetailUpdateDeleteView.as_view(), name='blog-detail-update-delete'),
    path('user-saved-blogs/',views.UserSavedBlogs.as_view(),name='user-saved-blogs'),
    path('user-liked-blogs/',views.UserLikedBlogs.as_view(),name='user-liked-blogs'),
]
