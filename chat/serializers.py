# serializers.py
from rest_framework import serializers
from .models import Thread, ChatMessage
from api.models import CustomUser
from decouple import config


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
            return UserDetailSerializer(obj.second_person, context=self.context).data
        return UserDetailSerializer(obj.first_person, context=self.context).data

    def get_last_message(self, obj):
        last_message = ChatMessage.objects.filter(
            thread=obj).order_by('-timestamp').first()
        if last_message:
            return ChatMessageSerializer(last_message).data
        return None


class ThreadForSiganlsSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = ['id', 'timestamp', 'other_user', 'last_message']

    def get_other_user(self, obj):
        request_user = self.context.get('request_user')
        if obj.first_person == request_user:
            return UserDetailSerializer(obj.second_person).data
        return UserDetailSerializer(obj.first_person).data

    def get_last_message(self, obj):
        # Fetch the last message in the thread
        last_message = ChatMessage.objects.filter(
            thread=obj).order_by('-timestamp').first()
        if last_message:
            return ChatMessageSerializer(last_message).data
        return None


class ChatUserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id']


class ChatMessageSerializer(serializers.ModelSerializer):
    send_by = serializers.PrimaryKeyRelatedField(read_only=True, source='user')
    audio = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'message', 'timestamp',
                  'thread', 'send_by', 'content_type', 'audio']

    def get_audio(self, obj):
        if obj.audio:
            return f"{config('BACKEND_URL')}{obj.audio.url}"
        return None
