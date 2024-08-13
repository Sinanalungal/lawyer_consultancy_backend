from rest_framework import serializers
from .models import Blog, Like, Comment,Saved,Report
from .image_serializer import Base64ImageField
from api.models import CustomUser



class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model.

    This serializer converts the CustomUser model instances into JSON format
    and provides the fields needed for user data.

    Fields:
        email (str): The email address of the user.
        full_name (str): The full name of the user.
        profile (str): The URL of the user's profile picture.
    """

    class Meta:
        model = CustomUser
        fields = ['profile_image', 'full_name' ,'role']
        


class BlogSerializer(serializers.ModelSerializer):
    """
    Serializer for the Blog model.

    Fields:
        image (ImageField): The image associated with the blog post.
        user (UserSerializer): The user associated with the blog post.
        like_count (IntegerField): The number of likes for the blog post.
        saved_count (IntegerField): The number of saves for the blog post.
    """

    image = serializers.ImageField(required=False)
    like_count = serializers.SerializerMethodField()
    saved_count = serializers.SerializerMethodField()
    report_count = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)  

    class Meta:
        model = Blog
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False}  
        }

    def get_like_count(self, obj):
        """Return the count of likes for the blog."""
        return Like.objects.filter(blog=obj).count()

    def get_saved_count(self, obj):
        """Return the count of saves for the blog."""
        return Saved.objects.filter(blog=obj).count()
    
    def get_report_count(self, obj):
        """Return the count of reports for the blog."""
        return Report.objects.filter(blog=obj).count()
    

class BlogUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the Blog model.

    Fields:
        image (ImageField): The image associated with the blog post.
        user (UserSerializer): The user associated with the blog post.
        like_count (IntegerField): The number of likes for the blog post.
        saved_count (IntegerField): The number of saves for the blog post.
        is_liked (BooleanField): Indicates if the current user liked the blog post.
        is_saved (BooleanField): Indicates if the current user saved the blog post.
    """
    image = serializers.ImageField(required=False)
    like_count = serializers.SerializerMethodField()
    saved_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = Blog
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False}  
        }

    def get_like_count(self, obj):
        """Return the count of likes for the blog."""
        return Like.objects.filter(blog=obj).count()

    def get_saved_count(self, obj):
        """Return the count of saves for the blog."""
        return Saved.objects.filter(blog=obj).count()

    def get_is_liked(self, obj):
        """Return whether the current user has liked the blog."""
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return Like.objects.filter(blog=obj, user=request.user, like=True).exists()
        return False

    def get_is_saved(self, obj):
        """Return whether the current user has saved the blog."""
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return Saved.objects.filter(blog=obj, user=request.user, saved=True).exists()
        return False
    
    
class BlogUpdateIsListedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ['is_listed']

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['like']

class UserCommentSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['profile_image_url', 'full_name', 'role']

    def get_profile_image_url(self, obj):
        request = self.context.get('request')
        if obj.profile_image:
            return request.build_absolute_uri(obj.profile_image.url)
        return None

class CommentSerializer(serializers.ModelSerializer):
    user = UserCommentSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ['id', 'user', 'blog', 'content', 'created_at']
        read_only_fields = ['user', 'blog', 'created_at']

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['note']

class SavedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Saved
        fields = ['saved']
        
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['email', 'full_name', 'profile']

# # class ReportSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Report
# #         fields = ['id', 'user', 'blog', 'note', 'report']

# class BlogSerializer(serializers.ModelSerializer):
#     image = serializers.ImageField(required=False)
#     likes_count = serializers.SerializerMethodField()
#     is_liked = serializers.SerializerMethodField()
#     is_saved = serializers.SerializerMethodField()
#     # user = UserSerializer(read_only=True)
#     # report=ReportSerializer(read_only=True)


#     class Meta:
#         model = Blog
#         fields = '__all__'

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         print(instance)
#         print(data)
#         data['id'] = instance.id
#         data['user'] = UserSerializer(instance.user).data
#         # data['user'] = instance.user.email
#         # data['profile'] = instance.user.profile
#         print(instance.valid)
#         # data['total_likes'] = self.get_likes_count(instance)
#         # data['is_liked'] = self.get_is_liked(instance)
#         # print(data)
#         return data

#     def get_likes_count(self, obj):
#         total_count = Like.objects.filter(blog=obj, like=True).count()
#         # print(total_count)
#         return total_count

#     def get_is_liked(self, obj):
#         user = self.context['request'].user
#         # print(user)
#         if user.is_authenticated:
#             return Like.objects.filter(user=user, blog=obj, like=True).exists()
#         return False
    
    
#     def get_is_saved(self, obj):
#         user = self.context['request'].user 
#         print(user)
#         if user.is_authenticated:
#             return Saved.objects.filter(user=user, blog=obj, saved=True).exists()
#         return False  

    
# class LikeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Like
#         fields = '__all__'

# class SavedSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Saved
#         fields = '__all__'

#     # def to_representation(self, instance):
#     #     data = super().to_representation(instance)
#     #     # Change the value of the 'like' field to its opposite
#     #     if instance.like == True:
#     #         instance.like = False
#     #     else:
#     #         instance.like = True
#     #     instance.save()
#     #     data['like'] = instance.like
#     #     return data


# class CommentSerializer(serializers.ModelSerializer):
#     # user = UserSerializer(read_only=True)

#     class Meta:
#         model = Comment
#         fields = '__all__'

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data['id'] = instance.id
#         data['user'] = UserSerializer(instance.user).data
#         print(data, instance.id)
#         return data
    
# class ReportSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Report
#         fields = ['id', 'user', 'blog', 'note', 'report']
# class BlogReportSerializer(serializers.ModelSerializer):
#     user = UserSerializer(read_only=True)
#     likes_count = serializers.SerializerMethodField()
#     is_liked = serializers.SerializerMethodField()
#     is_saved = serializers.SerializerMethodField()
#     reports = ReportSerializer(many=True, read_only=True, source='report_set')

#     class Meta:
#         model = Blog
#         fields = '__all__'

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data['id'] = instance.id
#         data['user'] = UserSerializer(instance.user).data
#         return data

#     def get_likes_count(self, obj):
#         return Like.objects.filter(blog=obj, like=True).count()

#     def get_is_liked(self, obj):
#         user = self.context['request'].user
#         if user.is_authenticated:
#             return Like.objects.filter(user=user, blog=obj, like=True).exists()
#         return False
    
#     def get_is_saved(self, obj):
#         user = self.context['request'].user
#         if user.is_authenticated:
#             return Saved.objects.filter(user=user, blog=obj, saved=True).exists()
#         return False  
    
# class BlogValidUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Blog
#         fields = ['valid']

