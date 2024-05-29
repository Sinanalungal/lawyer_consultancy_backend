from rest_framework import serializers
from .models import Blog, Like, Comment,Saved
from .image_serializer import Base64ImageField
from api.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'profile']

class BlogSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)


    class Meta:
        model = Blog
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = instance.id
        data['user'] = UserSerializer(instance.user).data
        # data['user'] = instance.user.email
        # data['profile'] = instance.user.profile
        print(instance.valid)
        # data['total_likes'] = self.get_likes_count(instance)
        # data['is_liked'] = self.get_is_liked(instance)
        # print(data)
        return data

    def get_likes_count(self, obj):
        total_count = Like.objects.filter(blog=obj, like=True).count()
        # print(total_count)
        return total_count

    def get_is_liked(self, obj):
        user = self.context['request'].user
        # print(user)
        if user.is_authenticated:
            return Like.objects.filter(user=user, blog=obj, like=True).exists()
        return False
    
    
    def get_is_saved(self, obj):
        user = self.context['request'].user
        print(user)
        if user.is_authenticated:
            return Saved.objects.filter(user=user, blog=obj, saved=True).exists()
        return False  

    
class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'

class SavedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Saved
        fields = '__all__'

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     # Change the value of the 'like' field to its opposite
    #     if instance.like == True:
    #         instance.like = False
    #     else:
    #         instance.like = True
    #     instance.save()
    #     data['like'] = instance.like
    #     return data


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = instance.id
        data['user'] = UserSerializer(instance.user).data
        print(data, instance.id)
        return data