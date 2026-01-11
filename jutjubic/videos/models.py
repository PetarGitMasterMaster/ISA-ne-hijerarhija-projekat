from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model


def validate_video_size(value):
    max_size = 200 * 1024 * 1024  # 200MB
    if value.size > max_size:
        raise ValidationError("Video file too large (max 200MB).")


def validate_mp4(value):
    if not value.name.lower().endswith(".mp4"):
        raise ValidationError("Only MP4 videos are allowed.")


class VideoPost(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="video_posts"
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()

    video = models.FileField(
        upload_to="videos/",
        validators=[validate_mp4, validate_video_size],
        null=True,
        blank=True,
    )

    thumbnail = models.ImageField(
        upload_to="thumbnails/",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    views = models.PositiveIntegerField(default=0)

    likes = models.ManyToManyField(
    settings.AUTH_USER_MODEL,
    related_name="liked_videos",
    blank=True
    )

    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while VideoPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

User = get_user_model()

