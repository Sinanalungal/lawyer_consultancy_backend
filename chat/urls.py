# urls.py
from django.urls import path
from .views import MessagesPage, ThreadMessagesPage

urlpatterns = [
    path('messages/', MessagesPage.as_view(), name='messages_page'),
    path('messages/thread/', ThreadMessagesPage.as_view(),
         name='thread_messages_page'),
]
