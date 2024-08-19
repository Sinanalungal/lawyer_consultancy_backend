# serializers.py
from rest_framework import serializers
from .models import Thread, ChatMessage
from api.serializers import UserDetailSerializer
from api.models import CustomUser

# class ChatMessageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ChatMessage
#         fields = '__all__'


# class UserDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['id', 'full_name', 'profile_image']

# class ThreadSerializer(serializers.ModelSerializer):
#     other_user = UserDetailSerializer()

#     class Meta:
#         model = Thread
#         fields = ['id', 'timestamp', 'other_user']

#     def get_other_user(self, obj):
#         request_user = self.context['request'].user
#         if obj.first_person == request_user:
#             return UserDetailSerializer(obj.second_person).data
#         return UserDetailSerializer(obj.first_person).data


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'message', 'timestamp', 'user']

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'profile_image']

class ThreadSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = ['id', 'timestamp', 'other_user', 'last_message']

    def get_other_user(self, obj):
        request_user = self.context['request'].user
        if obj.first_person == request_user:
            return UserDetailSerializer(obj.second_person).data
        return UserDetailSerializer(obj.first_person).data

    def get_last_message(self, obj):
        # Fetch the last message in the thread
        last_message = ChatMessage.objects.filter(thread=obj).order_by('-timestamp').first()
        if last_message:
            return ChatMessageSerializer(last_message).data
        return None

class ChatUserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id']


class ChatMessageSerializer(serializers.ModelSerializer):
    send_by = serializers.PrimaryKeyRelatedField(read_only=True, source='user')
    class Meta:
        model = ChatMessage
        fields = ['id', 'message', 'timestamp','thread', 'send_by']