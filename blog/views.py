from rest_framework import generics
from .models import Blog, Like, Comment, Saved, Report
from .serializer import BlogSerializer,LikedBlogSerializer,SavedBlogSerializer,BlogSerializerForRetrieveAndUpdate, BlogUpdateIsListedSerializer,BlogUserSerializer, ReportSerializer, CommentSerializer
# BlogReportSerializer,BlogValidUpdateSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from api.models import CustomUser
from rest_framework import status
from django.db.models import Q
from server.permissions import IsAdmin,SavedBlogAccess, IsAdminOrLawyer,VerifiedUser,IsOwner
from django.db.models import Count
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from rest_framework import serializers  



class BlogCreateAPIView(generics.CreateAPIView):
    """
    API view to create a new blog post.
    """
    serializer_class = BlogSerializer
    permission_classes = [IsAdminOrLawyer,VerifiedUser]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        """Save the blog post with the user from the request."""
        serializer.save(user=self.request.user)


class BlogListAPIView(generics.ListAPIView):
    """
    API view to retrieve a paginated list of blog posts.
    """
    serializer_class = BlogSerializer
    permission_classes = [IsAdmin,VerifiedUser] 
    pagination_class = PageNumberPagination
    page_size = 10

    def get_queryset(self):
        """Return the list of blogs."""
        queryset = Blog.objects.all()

        is_admin = self.request.user.role=='admin'

        status = self.request.query_params.get('status')
        print(status)
        if status  and is_admin:
            print('getting into this')
            queryset = queryset.filter(status=status)
            

        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        return queryset
    
class BlogUserListView(generics.ListAPIView):
    """
    API view to retrieve a paginated list of blog posts.
    """
    serializer_class = BlogUserSerializer
    permission_classes = [IsAuthenticated,VerifiedUser] 
    pagination_class = PageNumberPagination
    page_size = 12

    def get_queryset(self):
        """Return the list of blogs."""
        queryset = Blog.objects.filter(status='Listed', user__is_verified=True)
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        return queryset

    def get_serializer_context(self):
        """Add request context to the serializer."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class LikeBlogView(generics.RetrieveUpdateAPIView):
    queryset = Blog.objects.all()
    permission_classes = [IsAuthenticated,VerifiedUser]

    def update(self, request, *args, **kwargs):
        blog_id = request.data.get('blog_id')
        if not blog_id:
            return Response({'detail': 'Blog ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            blog = Blog.objects.get(pk=blog_id)
        except Blog.DoesNotExist:
            return Response({'detail': 'Blog not found'}, status=status.HTTP_404_NOT_FOUND)
        
        like, created = Like.objects.get_or_create(user=request.user, blog=blog)
        like.like = not like.like
        
        if not like.like:
            like.delete() 
            return Response({'like': False}, status=status.HTTP_200_OK)
        
        like.save()
        return Response({'like': True}, status=status.HTTP_200_OK)

class CommentPagination(PageNumberPagination):
    page_size = 10

class CommentBlogView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated,VerifiedUser]

    def perform_create(self, serializer):
        blog_id = self.request.data.get('blog_id')
        if not blog_id:
            raise ValidationError({'error': 'Blog ID is required'})
        
        try:
            blog = Blog.objects.get(pk=int(blog_id))
        except Blog.DoesNotExist:
            raise ValidationError({'error': 'Invalid Blog ID'})
        
        serializer.save(user=self.request.user, blog=blog)

    def get(self, request, *args, **kwargs):
        blog_id = request.query_params.get('blog_id')
        if not blog_id:
            return Response({'error': 'Blog ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        comments = Comment.objects.filter(blog_id=blog_id).order_by('-created_at')
        paginator = CommentPagination()
        paginated_comments = paginator.paginate_queryset(comments, request)
        serializer = CommentSerializer(paginated_comments, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    
class ReportBlogView(generics.CreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, VerifiedUser]

    def perform_create(self, serializer):
        blog_id = self.kwargs.get('pk')
        user = self.request.user
        blog = Blog.objects.get(pk=blog_id)

        # Check if the user has already reported this blog
        existing_report = Report.objects.filter(user=user, blog=blog).first()
        
        if existing_report:
            raise serializers.ValidationError("You have already reported this blog.")

        # If no report exists, create a new one
        serializer.save(user=user, blog=blog)



class SaveBlogView(generics.RetrieveUpdateAPIView):
    queryset = Blog.objects.all()
    permission_classes = [IsAuthenticated,VerifiedUser]

    def update(self, request, *args, **kwargs):
        blog_id = request.data.get('blog_id')
        if not blog_id:
            return Response({'detail': 'Blog ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            blog = Blog.objects.get(pk=blog_id)
        except Blog.DoesNotExist:
            return Response({'detail': 'Blog not found'}, status=status.HTTP_404_NOT_FOUND)
        
        saved, created = Saved.objects.get_or_create(user=request.user, blog=blog)
        saved.saved = not saved.saved
        
        if not saved.saved:
            saved.delete()  
            return Response({'saved': False}, status=status.HTTP_200_OK)
        
        saved.save()
        return Response({'saved': True}, status=status.HTTP_200_OK)

class BlogUpdateIsListedView(generics.UpdateAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogUpdateIsListedSerializer
    permission_classes = [IsAdmin,VerifiedUser]

    def update(self, request, *args, **kwargs):
        blog_id = request.data.get('blog_id')
        status_data= request.data.get('status')
        if not blog_id:
            return Response({'detail': 'Blog ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            blog = Blog.objects.get(pk=blog_id)
        except Blog.DoesNotExist:
            return Response({'detail': 'Blog not found'}, status=status.HTTP_404_NOT_FOUND)
        if status:
            blog.status = status_data
        blog.save()
        return Response({'status': blog.status}, status=status.HTTP_200_OK)


class CommentEditView(generics.RetrieveUpdateAPIView):
    """
    API view to edit a comment.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, VerifiedUser]

    def get_object(self):
        """
        Override to ensure only the owner of the comment can edit it.
        """
        comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        if comment.user != self.request.user:
            raise ValidationError({'detail': 'You do not have permission to edit this comment.'})
        return comment


class CommentDeleteView(generics.DestroyAPIView):
    """
    API view to delete a comment.
    """
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated, VerifiedUser]

    def get_object(self):
        """
        Override to ensure only the owner of the comment can delete it.
        """
        comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        if comment.user != self.request.user:
            raise ValidationError({'detail': 'You do not have permission to delete this comment.'})
        return comment

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy method to provide custom response on delete.
        """
        comment = self.get_object()
        comment.delete()
        return Response({'detail': 'Comment deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

class BlogDetailUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset=Blog.objects.all()
    serializer_class=BlogSerializerForRetrieveAndUpdate
    permission_classes = [IsOwner, VerifiedUser]
    lookup_field = 'id'
    

class PersonalBlogListAPIView(generics.ListAPIView):
    """
    API view to retrieve a paginated list of blog posts.
    """
    serializer_class = BlogSerializer
    permission_classes = [IsOwner,VerifiedUser] 
    pagination_class = PageNumberPagination
    page_size = 10

    def get_queryset(self):
        """Return the list of blogs."""
        queryset = Blog.objects.all()


        status = self.request.query_params.get('status')
        print(status)
        if status :
            print('getting into this')
            queryset = queryset.filter(status=status,user=self.request.user)
            

        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        return queryset
    
# class UserSavedBlogs(generics.ListAPIView):
#     serializer_class = SavedBlogSerializer
#     permission_classes = [SavedBlogAccess]

#     def get_queryset(self):
#         return Saved.objects.filter(user=self.request.user).order_by('-updated_at')
    
# class UserLikedBlogs(generics.ListAPIView):
#     serializer_class = LikedBlogSerializer
#     permission_classes = [SavedBlogAccess]

#     def get_queryset(self):
#         return Like.objects.filter(user=self.request.user).order_by('-updated_at')
    

class UserSavedBlogs(APIView):
    permission_classes = [SavedBlogAccess]

    def get(self, request):
        saved_blogs = Saved.objects.filter(user=self.request.user,blog__status='Listed').order_by('-updated_at')
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(saved_blogs, request)
        serializer = SavedBlogSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class UserLikedBlogs(APIView):
    permission_classes = [SavedBlogAccess]

    def get(self, request):
        liked_blogs = Like.objects.filter(user=self.request.user,blog__status='Listed').order_by('-updated_at')
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(liked_blogs, request)
        serializer = LikedBlogSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)