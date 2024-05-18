from rest_framework import generics
from .models import Blog, Like, Comment,Saved
from .serializer import BlogSerializer, LikeSerializer, CommentSerializer,SavedSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from api.models import CustomUser


class BlogListCreateAPIView(generics.ListCreateAPIView):
    queryset = Blog.objects.all().order_by('created_at')
    serializer_class = BlogSerializer
    parser_classes = (MultiPartParser, FormParser)

    # permission_classes = [IsAuthenticatedOrReadOnly]  # Example permission class

    def get_queryset(self):
        param=self.request.query_params.get('all', False)
        if param:
            return Blog.objects.all().order_by('-created_at')
        user_id = self.request.user.id 
        return Blog.objects.filter(user_id=user_id).order_by('-created_at')
    


    # Optionally, you can customize pagination
    # pagination_class = MyCustomPaginationClass

class BlogDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Blog.objects.all().order_by('-created_at')
    serializer_class = BlogSerializer
    parser_classes = (MultiPartParser, FormParser)

    
    # def perform_create(self, serializer):
    #     # Customize the creation process to include the creator field
    #     serializer.save(user=self.request.user)
    # permission_classes = [IsAuthenticatedOrReadOnly]  

class LikeAPIView(APIView):
    def post(self, request, *args, **kwargs):
        user_id=self.request.data.get('user')
        blog_id=self.request.data.get('blog')
        
        userObj=CustomUser.objects.filter(id=user_id).first()
        blogObj=Blog.objects.filter(id=blog_id).first()

        likeObj=Like.objects.filter(user_id=user_id,blog_id=blog_id).first()
        if likeObj:
            likeObj.like= not (likeObj.like)
            likeObj.save()
        else:
            likeObj=Like.objects.create(user_id=user_id,blog_id=blog_id,like=True)
        seriaized=LikeSerializer(likeObj)
        return Response(seriaized.data)

class SaveAPIView(APIView):
    def post(self, request, *args, **kwargs):
        user_id=self.request.data.get('user')
        blog_id=self.request.data.get('blog')
        
        userObj=CustomUser.objects.filter(id=user_id).first()
        blogObj=Blog.objects.filter(id=blog_id).first()

        savedObj=Saved.objects.filter(user_id=user_id,blog_id=blog_id).first()
        if savedObj:
            savedObj.saved= not (savedObj.saved)
            savedObj.save()
        else:
            savedObj=Saved.objects.create(user_id=user_id,blog_id=blog_id,saved=True)
        seriaized=SavedSerializer(savedObj)
        return Response(seriaized.data)
   

    # permission_classes = [IsAuthenticatedOrReadOnly]  

# class LikeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Like.objects.all()
#     serializer_class = LikeSerializer
#     # permission_classes = [IsAuthenticatedOrReadOnly]  

class CommentCreateAPIView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    def get_queryset(self):
        blog_id = self.request.query_params.get('blog_id')
        print(blog_id)
        if blog_id:
            result=Comment.objects.filter(blog_id=blog_id).all().order_by('-created_at')
            print(result)
            return result
        else:
            return Comment.objects.all().order_by('created_at')
    
    # permission_classes = [IsAuthenticatedOrReadOnly] 

class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly] 

