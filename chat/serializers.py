# serializers.py
from rest_framework import serializers
from .models import Thread, ChatMessage
from api.serializers import UserDetailSerializer

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
    

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'