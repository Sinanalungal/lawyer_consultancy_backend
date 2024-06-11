# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Thread,ChatMessage
from .serializers import ThreadSerializer,ChatMessageSerializer
from rest_framework.pagination import PageNumberPagination


class MessagesPage(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        threads = Thread.objects.by_user(user=request.user)
        # .prefetch_related('chatmessage_thread').order_by('timestamp')
        serializer = ThreadSerializer(threads, many=True, context={'request': request})
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ThreadMessagesPagination(PageNumberPagination):
    page_size = 20

class ThreadMessagesPage(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ThreadMessagesPagination

    def get(self, request, thread_id, format=None):
        try:
            thread = Thread.objects.get(id=thread_id)
            if request.user != thread.first_person and request.user != thread.second_person:
                return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
            
            messages = ChatMessage.objects.filter(thread=thread).order_by('-timestamp')
            paginator = ThreadMessagesPagination()
            result_page = paginator.paginate_queryset(messages, request)
            serializer = ChatMessageSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Thread.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)