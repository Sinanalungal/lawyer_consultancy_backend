from django.db import models
from api.models import CustomUser

class Blog(models.Model):
    user = models.ForeignKey(CustomUser,null=False,blank=False,on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    image = models.ImageField(upload_to='blog/')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    checked = models.BooleanField(default=False)
    valid=models.BooleanField(default=False)
    

    def __str__(self):
        return self.title


class Like(models.Model):
    user = models.ForeignKey(CustomUser,null=False,blank=False,on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog,null=False,blank=False,on_delete=models.CASCADE)
    like = models.BooleanField(default=False)
    # created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    

class Comment(models.Model):

    user = models.ForeignKey(CustomUser,null=False,blank=False,on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog,null=False,blank=False,on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content
    
class Saved(models.Model):
    user = models.ForeignKey(CustomUser,null=False,blank=False,on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog,null=False,blank=False,on_delete=models.CASCADE)
    saved=models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.username