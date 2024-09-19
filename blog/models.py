from django.db import models
from api.models import CustomUser


class Blog(models.Model):
    """
    Represents a blog post with status management.

    Attributes:
        user (ForeignKey): The user who created the blog post.
        title (CharField): The title of the blog post.
        description (CharField): A brief description of the blog post.
        image (ImageField): An image associated with the blog post.
        content (TextField): The main content of the blog post.
        created_at (DateTimeField): The date and time when the blog post was created.
        status (CharField): The status of the blog post (Pending, Listed, Blocked).
    """

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Listed', 'Listed'),
        ('Blocked', 'Blocked'),
    ]

    user = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    image = models.ImageField(upload_to='blog/')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        """Return the title of the blog post."""
        return f"{self.pk}"


class Like(models.Model):
    """
    Represents a like on a blog post.

    Attributes:
        user (ForeignKey): The user who liked the blog post.
        blog (ForeignKey): The blog post that was liked.
        like (BooleanField): Indicates if the blog post is liked.
        updated_at (DateTimeField): The date and time when the like was updated.
    """
    user = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, null=False, blank=False, on_delete=models.CASCADE)
    like = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return the username of the user who liked the blog post."""
        return self.user.username


class Comment(models.Model):
    """
    Represents a comment on a blog post.

    Attributes:
        user (ForeignKey): The user who made the comment.
        blog (ForeignKey): The blog post that was commented on.
        content (TextField): The content of the comment.
        created_at (DateTimeField): The date and time when the comment was created.
    """
    user = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, null=False, blank=False, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the content of the comment."""
        return self.content


class Saved(models.Model):
    """
    Represents a saved blog post.

    Attributes:
        user (ForeignKey): The user who saved the blog post.
        blog (ForeignKey): The blog post that was saved.
        saved (BooleanField): Indicates if the blog post is saved.
        updated_at (DateTimeField): The date and time when the save was updated.
    """
    user = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, null=False, blank=False, on_delete=models.CASCADE)
    saved = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return the username of the user who saved the blog post."""
        return self.user.username


class Report(models.Model):
    """
    Represents a report for a blog post.

    Attributes:
        user (ForeignKey): The user who reported the blog post.
        blog (ForeignKey): The blog post that was reported.
        note (TextField): The reason for reporting the blog post.
        report (BooleanField): Indicates if the blog post is reported.
    """
    user = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, null=False, blank=False, on_delete=models.CASCADE)
    note = models.TextField(blank=False, null=False)
    report = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'blog')

    def __str__(self):
        """Return the primary key of the report."""
        return str(self.pk)


