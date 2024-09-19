from django.urls import path
from . import views

urlpatterns = [
    path('create-blog/', views.BlogCreateAPIView.as_view(), name='blog-create'),
    path('blogs/', views.BlogListAPIView.as_view(), name='blog-list'),
    path('blogs/users/', views.BlogUserListView.as_view(), name='blog-list-users'),
    path('blogs/update_is_listed/', views.BlogUpdateIsListedView.as_view(), name='blog-update-is-listed'),
    path('blogs/like/', views.LikeBlogView.as_view(), name='like-blog'),
    path('blogs/comments/', views.CommentBlogView.as_view(), name='comment-blog'),
    path('blogs/report/<int:pk>/', views.ReportBlogView.as_view(), name='report-blog'),
    path('blogs/save/', views.SaveBlogView.as_view(), name='save-blog'),
    path('comments/edit/<int:pk>/', views.CommentEditView.as_view(), name='edit-comment'),
    path('comments/delete/<int:pk>/', views.CommentDeleteView.as_view(), name='delete-comment'),
    path('blog-update/<int:id>/', views.BlogDetailUpdateDeleteView.as_view(), name='blog-detail-update-delete'),
    # path('blogs/<int:pk>/', views.BlogDetailAPIView.as_view(), name='blog-detail'),
    # path('likes/', views.LikeAPIView.as_view(), name='like-create'),
    # path('comments/', views.CommentCreateAPIView.as_view(), name='comment-create'),
    # path('saved/', views.SaveAPIView.as_view(), name='save-create'),
    # path('saved-blogs/', views.UserSavedBlogs.as_view(), name='saved-blogs'),
    # path('checking-blog/', views.CheckingBlogs.as_view(), name='checking-blog'),
    # path('validate-blog/', views.ValidatingBlogs.as_view(), name='validate-blog'),
    # path('report-blog/', views.ReportBlogAPIView.as_view(), name='report-blog'),
    # path('admin-report-blog/', views.AdminReportSerializer.as_view(), name='admin-report-blog'),

    # path('likes/<int:pk>/', views.LikeDetailAPIView.as_view(), name='like-detail'),
    # path('comments/', views.CommentCreateAPIView.as_view(), name='comment-create'),
    # path('blogpage_admin/', views.GetBlogs.as_view()),
    # path('comments/<int:pk>/', views.CommentDetailAPIView.as_view(), name='comment-detail'),
]
