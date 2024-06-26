from rest_framework import generics
from .models import Blog, Like, Comment,Saved
from .serializer import BlogSerializer, LikeSerializer, CommentSerializer,SavedSerializer,ReportSerializer,BlogReportSerializer,BlogValidUpdateSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly,IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from api.models import CustomUser
from rest_framework import status
from django.db.models import Q
from server.permissions import IsAdmin
from django.db.models import Count
from rest_framework.pagination import PageNumberPagination




class BlogListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = BlogSerializer
    parser_classes = (MultiPartParser, FormParser)
    # permission_classes = [IsAuthenticatedOrReadOnly]  # Example permission class

    def get_queryset(self):
        param=self.request.query_params.get('all', False)
        # print(param,'this isi t')
        if param:
            return Blog.objects.filter(Q(checked=True), Q(valid=True)).all().order_by('-id')
        user_id = self.request.user.id 
        return Blog.objects.filter(user_id=user_id).order_by('-id')
    

# class GetBlogs(APIView):
#     def get(self, request):
#         param = request.query_params.get('checked')
#         if param :
#             data = Blog.objects.filter(checked=param).all().order_by('-created_at')
#             seriaized=BlogSerializer(data,many=True,context={"request":request})
#             return Response(seriaized.data)
#         else :
#             return Response({'message':'there is a problem with fetching the data '},status=status.HTTP_400_BAD_REQUEST)
        
    # Optionally, you can customize pagination
    # pagination_class = MyCustomPaginationClass

class BlogDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Blog.objects.all().order_by('-id')
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
class CheckingBlogs(APIView):
    def post(self, request, *args, **kwargs):
        blog_id = request.data.get('blog')
        
        if not blog_id:
            return Response({"error": "Blog ID not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        blogObj = Blog.objects.filter(id=blog_id).first()
        
        if not blogObj:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
        
        blogObj.checked = True
        blogObj.save()
        
        serializer = BlogSerializer(blogObj, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class ValidatingBlogs(APIView):
    def post(self, request, *args, **kwargs):
        blog_id = request.data.get('blog')
        
        if not blog_id:
            return Response({"error": "Blog ID not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        blogObj = Blog.objects.filter(id=blog_id).first()
        
        if not blogObj:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
        
        blogObj.valid = not blogObj.valid
        blogObj.save()
        
        serializer = BlogReportSerializer(blogObj, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserSavedBlogs(APIView):
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        saved_blogs = Saved.objects.filter(user_id=user_id, saved=True).select_related('blog').all().order_by('-id')
        
        if not saved_blogs:
            return Response({"message": "No saved blogs found"}, status=status.HTTP_404_NOT_FOUND)
        
        blogs = [saved.blog for saved in saved_blogs]
        serializer = BlogSerializer(blogs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

# class LikeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Like.objects.all()
#     serializer_class = LikeSerializer
#     # permission_classes = [IsAuthenticatedOrReadOnly]  

class CommentCreateAPIView(generics.ListCreateAPIView):
    queryset = Comment.objects.all().order_by('-id')
    serializer_class = CommentSerializer
    def get_queryset(self):
        blog_id = self.request.query_params.get('blog_id')
        print(blog_id)
        if blog_id:
            result=Comment.objects.filter(blog_id=blog_id).all().order_by('-id')
            print(result)
            return result
        else:
            return Comment.objects.all().order_by('-id')
    
    # permission_classes = [IsAuthenticatedOrReadOnly] 

class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all().order_by('-id')
    serializer_class = CommentSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly] 


class ReportBlogPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class ReportBlogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [IsAdmin]
        return super().get_permissions()

    def post(self, request, *args, **kwargs):
        data = request.data
        data['user'] = request.user.id 
        serializer = ReportSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Blog reported successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, *args, **kwargs):
        blogs_with_reports = Blog.objects.annotate(report_count=Count('report')).filter(report_count__gte=5)
        
        paginator = ReportBlogPagination()
        result_page = paginator.paginate_queryset(blogs_with_reports, request)
        serializer = BlogReportSerializer(result_page, many=True, context={'request': request})
        
        return paginator.get_paginated_response(serializer.data)
    
class AdminReportSerializer(APIView):
    def post(self, request, *args, **kwargs):
        blog_id = request.data.get('blog_id')
        if not blog_id:
            return Response({"error": "blog_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            blog = Blog.objects.get(id=blog_id)
        except Blog.DoesNotExist:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BlogValidUpdateSerializer(blog, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)