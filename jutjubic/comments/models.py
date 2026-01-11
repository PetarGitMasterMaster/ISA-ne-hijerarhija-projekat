from django.conf import settings
from django.db import models
from videos.models import VideoPost

class Comment(models.Model):
    video = models.ForeignKey(
        VideoPost,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} on {self.video}"


