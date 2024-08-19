from django.db import models
from api.models import CustomUser
from django.db.models import Q


class ThreadManager(models.Manager):
    def by_user(self, **kwargs):
        print(kwargs)
        user = kwargs.get('user')
        lookup = Q(first_person=user) | Q(second_person=user)
        qs = self.get_queryset().filter(lookup).distinct()
        # print(qs,'this is the queryset of perticulat user')
        return qs
    
    def involving_both_users(self, user1_id, user2_id):
        lookup = (
            (Q(first_person__id=user1_id) & Q(second_person__id=user2_id)) |
            (Q(first_person__id=user2_id) & Q(second_person__id=user1_id))
        )
        return self.get_queryset().filter(lookup).distinct()

class Thread(models.Model):
    first_person = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True,related_name='thread_first_person')
    second_person = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True,related_name='thread_second_person')
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_listed = models.BooleanField(default=True)
    
    objects = ThreadManager()
    class Meta:
        unique_together = ['first_person', 'second_person']

# class ChatMessage(models.Model):
#     thread = models.ForeignKey(Thread,null=True,blank=True,on_delete=models.CASCADE,related_name='chatmessage_thread')
#     user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
#     message = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('text', 'Text'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('image', 'Image'),
    ]

    thread = models.ForeignKey('Thread', null=True, blank=True, on_delete=models.CASCADE, related_name='chatmessage_thread')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    message = models.TextField(blank=True, null=True)
    audio = models.FileField(upload_to='audio/', blank=True, null=True)
    video = models.FileField(upload_to='video/', blank=True, null=True)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.user} in thread {self.thread} at {self.timestamp}"

    # def is_text_message(self):
    #     return self.content_type == 'text' and self.message

    # def is_audio_message(self):
    #     return self.content_type == 'audio' and self.audio

    # def is_video_message(self):
    #     return self.content_type == 'video' and self.video

    # def is_image_message(self):
    #     return self.content_type == 'image' and self.image