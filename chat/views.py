# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Thread,ChatMessage
from .serializers import ThreadSerializer,ChatMessageSerializer
from rest_framework.pagination import PageNumberPagination
from api.models import CustomUser

class MessagesPage(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        threads = Thread.objects.by_user(user=request.user).filter(is_listed=True)
        serializer = ThreadSerializer(threads, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        lawyer_id = request.data.get('lawyer_id')
        if not lawyer_id:
            return Response({'detail': 'Lawyer ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lawyer = CustomUser.objects.get(id=lawyer_id)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Lawyer not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.id == lawyer_id:
            return Response({'detail': 'You cannot start a chat with yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        thread_qs = Thread.objects.involving_both_users(user1_id=request.user.id, user2_id=lawyer_id)
        if thread_qs.exists():
            thread = thread_qs.first()
        else:
            thread = Thread.objects.create(first_person=request.user, second_person=lawyer)

        serializer = ThreadSerializer(thread, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ThreadMessagesPage(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        thread_id = request.data.get('thread_id')
        if not thread_id:
            return Response({'detail': 'Thread ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            thread = Thread.objects.get(id=thread_id)
            if request.user not in [thread.first_person, thread.second_person]:
                return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

            messages = ChatMessage.objects.filter(thread=thread).order_by('-timestamp')[::-1]
            serializer = ChatMessageSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Thread.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


# class MessagesPage(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         print(self.request.user.id)
#         threads = Thread.objects.by_user(user=request.user).filter(is_listed=True)
#         print(threads)
#         # .prefetch_related('chatmessage_thread').order_by('timestamp')
#         serializer = ThreadSerializer(threads, many=True, context={'request': request})
#         print(serializer.data)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#     def post(self, request, *args, **kwargs):
#         lawyer_id = request.query_params.get('lawyer')
#         thread_qs = Thread.objects.involving_both_users(user1_id=self.request.user.id,user2_id=lawyer_id)
#         print(thread_qs,'this is thread qs')
#         if (thread_qs.exists()):
#             print('entered in to the inside')
#             thread_qs.first()          
#         else:
#             print('new thread object is created')
#             Thread.objects.create(first_person=self.request.user,second_person__pk=lawyer_id)

# class MessagesPage(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         # Fetch threads where the user is either the first or second person
#         threads = Thread.objects.by_user(user=request.user).filter(is_listed=True)
#         serializer = ThreadSerializer(threads, many=True, context={'request': request})
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     def post(self, request, *args, **kwargs):
#         lawyer_id = request.query_params.get('lawyer')
#         if not lawyer_id:
#             return Response({'detail': 'Lawyer ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             lawyer = CustomUser.objects.get(id=lawyer_id)
#         except CustomUser.DoesNotExist:
#             return Response({'detail': 'Lawyer not found.'}, status=status.HTTP_404_NOT_FOUND)

#         if request.user.id == lawyer_id:
#             return Response({'detail': 'You cannot start a chat with yourself.'}, status=status.HTTP_400_BAD_REQUEST)

#         thread_qs = Thread.objects.involving_both_users(user1_id=request.user.id, user2_id=lawyer_id)
#         if thread_qs.exists():
#             thread = thread_qs.first()
#         else:
#             # Ensure that the users involved in the thread are correct
#             thread = Thread.objects.create(first_person=request.user, second_person=lawyer)

#         # Serialize and return the thread data
#         serializer = ThreadSerializer(thread, context={'request': request})
#         return Response(serializer.data, status=status.HTTP_201_CREATED)


# # class ThreadMessagesPagination(PageNumberPagination):
# #     page_size = 20

# class ThreadMessagesPage(APIView):
#     permission_classes = [IsAuthenticated]
#     # pagination_class = ThreadMessagesPagination

#     # def get(self, request, thread_id, format=None):
#     #     try:
#     #         thread = Thread.objects.get(id=thread_id)
#     #         if request.user != thread.first_person and request.user != thread.second_person:
#     #             return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
            
#     #         # Fetch the last 20 messages and reverse their order
#     #         messages = ChatMessage.objects.filter(thread=thread).order_by('-timestamp')[::-1]
#     #         # paginator = ThreadMessagesPagination()
#     #         # result_page = paginator.paginate_queryset(messages, request)
#     #         serializer = ChatMessageSerializer(messages, many=True)
#     #         print(serializer.data)
#     #         return Response(serializer.data,status=status.HTTP_200_OK)
#     #     except Thread.DoesNotExist:
#     #         return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
#     def get(self, request, thread_id, format=None):
#         try:
#             # Fetch the thread and ensure the user is a participant
#             thread = Thread.objects.get(id=thread_id)
#             if request.user not in [thread.first_person, thread.second_person]:
#                 return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

#             # Fetch the last 20 messages and reverse their order
#             messages = ChatMessage.objects.filter(thread=thread).order_by('-timestamp')[::-1]
#             serializer = ChatMessageSerializer(messages, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except Thread.DoesNotExist:
#             return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        
