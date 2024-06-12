# serializers.py
from rest_framework import serializers
from .models import Thread, ChatMessage
from api.serializers import UserDetailSerializer
from api.models import CustomUser

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'

# class ThreadSerializer(serializers.ModelSerializer):
#     # chatmessage_thread = ChatMessageSerializer(many=True, read_only=True)
#     first_person = UserDetailSerializer()
#     second_person = UserDetailSerializer()

#     class Meta:
#         model = Thread
#         fields = '__all__'


class ThreadSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = ['id', 'timestamp', 'other_user']

    def get_other_user(self, obj):
        request_user = self.context['request'].user
        if obj.first_person == request_user:
            return UserDetailSerializer(obj.second_person).data
        return UserDetailSerializer(obj.first_person).data

class ChatUserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id']


class ChatMessageSerializer(serializers.ModelSerializer):
    send_by = serializers.PrimaryKeyRelatedField(read_only=True, source='user')
    class Meta:
        model = ChatMessage
        fields = ['id', 'message', 'timestamp','thread', 'send_by']