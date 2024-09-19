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
    is_reported = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = Blog
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False}  
        }

    def get_is_reported(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return Report.objects.filter(blog=obj, user=request.user, report=True).exists()
        return False


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
        fields = ['status']

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


class BlogSerializerForRetrieveAndUpdate(serializers.ModelSerializer):
    """
    Serializer for Blog model to handle both retrieval and update (patch).
    """

    class Meta:
        model = Blog
        fields = '__all__' 
        read_only_fields = ['user', 'created_at'] 