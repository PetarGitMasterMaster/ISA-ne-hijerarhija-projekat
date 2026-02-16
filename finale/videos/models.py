from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth import get_user_model

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.contrib.postgres.indexes import GistIndex


from django.db.models import F, FloatField, ExpressionWrapper, Count
from django.db.models.functions import Coalesce
import subprocess
import json




# ==========================
# Validators
# ==========================

def validate_video_size(value):
    max_size = 200 * 1024 * 1024  # 200MB
    if value.size > max_size:
        raise ValidationError("Video file too large (max 200MB).")


def validate_mp4(value):
    if not value.name.lower().endswith(".mp4"):
        raise ValidationError("Only MP4 videos are allowed.")


def get_video_duration_seconds(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            path
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    data = json.loads(result.stdout)
    return int(float(data["format"]["duration"]))



# ==========================
# Custom QuerySet
# ==========================

class VideoPostQuerySet(models.QuerySet):

    def available(self):
        """Only videos that are visible right now"""
        return self.filter(
            models.Q(scheduled_at__isnull=True) |
            models.Q(scheduled_at__lte=timezone.now())
        )

    def upcoming(self):
        return self.filter(
            scheduled_at__gt=timezone.now()
        ).order_by("scheduled_at")        

    def nearby(self, point, km=5):
        """Return videos within a distance (km) from a point."""
        return self.filter(location__distance_lte=(point, D(km=km)))

    def with_distance(self, point):
        """Return videos annotated with distance from a point."""
        return self.annotate(distance=Distance("location", point)).order_by("distance")

    def nearby_with_distance(self, point, km=5):
        """Return nearby videos annotated with distance, ordered by distance."""
        return self.nearby(point, km=km).annotate(distance=Distance("location", point)).order_by("distance")

    def with_popularity(self, point=None):
        qs = self.annotate(
            likes_count=Count("likes", distinct=True),
            popularity=ExpressionWrapper(
                Coalesce(F("views"), 0) * 0.6 +
                Coalesce(F("likes_count"), 0) * 1.4,
                output_field=FloatField()
            )
        )

        if point:
            qs = qs.annotate(
                distance=Distance("location", point)
            ).order_by("distance", "-popularity")
        else:
            qs = qs.order_by("-popularity")

        return qs 


# ==========================
# Video Model
# ==========================

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

    # 🌍 Location
    location = gis_models.PointField(
        null=True,
        blank=True,
        srid=4326
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ⏱ Scheduling
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Video becomes visible at this time"
    )

    duration_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Video duration in seconds"
    )

    # 📊 Engagement
    views = models.PositiveIntegerField(default=0)

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_videos",
        blank=True
    )

    # Custom manager
    objects = VideoPostQuerySet.as_manager()

    class Meta:
        indexes = [
            GistIndex(fields=["location"]),
            models.Index(fields=["scheduled_at"]),
        ]
        ordering = ["-created_at"]

    # ==========================
    # Model Methods
    # ==========================

    #def save(self, *args, **kwargs):
     #   if not self.slug:
      #      base_slug = slugify(self.title)
       #     slug = base_slug
        #    counter = 1

         #   while VideoPost.objects.filter(slug=slug).exists():
          #      slug = f"{base_slug}-{counter}"
           #     counter += 1

            #self.slug = slug

        #super().save(*args, **kwargs)

    #def save(self, *args, **kwargs):
     #   is_new = self.pk is None

      #  if not self.slug:
       #     base_slug = slugify(self.title)
        #    slug = base_slug
         #   counter = 1
          #  while VideoPost.objects.filter(slug=slug).exists():
           #     slug = f"{base_slug}-{counter}"
            #    counter += 1
            #self.slug = slug

        #super().save(*args, **kwargs)

    # ⏱️ SET VIDEO DURATION AFTER FILE EXISTS
        #if is_new and self.video:
         #   self.duration_seconds = get_video_duration_seconds(self.video.path)
          #  super().save(update_fields=["duration_seconds"])
    

    def is_available(self):
        """Check if video is visible based on schedule"""
        if not self.scheduled_at:
            return True
        return timezone.now() >= self.scheduled_at

    #def streaming_offset_seconds(self):
        """
        Simulates how much of the video should already be playing
        if user joins after scheduled start
        """
     #   if not self.scheduled_at:
      #      return 0

       # delta = timezone.now() - self.scheduled_at
        #return max(
         #   0,
          #  min(int(delta.total_seconds()), self.duration_seconds)
        #)
    
    #def get_video_duration_seconds(self):
    """
    Extract video duration in seconds using ffprobe
    """
     #   if not self.video:
      #      return 0

       # import subprocess
        #import json

        #try:
         #   result = subprocess.run(
          #      [
           #         "ffprobe",
            #        "-v", "error",
             #       "-show_entries", "format=duration",
              #      "-of", "json",
               #     self.video.path,
                #],
                #stdout=subprocess.PIPE,
                #stderr=subprocess.PIPE,
                #text=True,
            #)

            #data = json.loads(result.stdout)
            #return int(float(data["format"]["duration"]))

        #except Exception as e:
         #   print("Duration error:", e)
          #  return 0
    # ==========================
    # VIDEO DURATION EXTRACTION
    # ==========================
    def get_video_duration_seconds(self):
        if not self.video:
            return 0

        import subprocess
        import json

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "json",
                    self.video.path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            data = json.loads(result.stdout)
            return int(float(data["format"]["duration"]))

        except Exception as e:
            print("Duration error:", e)
            return 0

    # ==========================
    # SAVE OVERRIDE
    # ==========================
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.video and self.duration_seconds == 0:
            self.duration_seconds = self.get_video_duration_seconds()
            super().save(update_fields=["duration_seconds"])

    # ==========================
    # STREAMING OFFSET
    # ==========================
    def streaming_offset_seconds(self):
        if not self.scheduled_at or self.duration_seconds == 0:
            return 0

        now = timezone.now()
        if now < self.scheduled_at:
            return 0

        elapsed = int((now - self.scheduled_at).total_seconds())
        return min(elapsed, self.duration_seconds)    


    def __str__(self):
        return self.title

class VideoView(models.Model):
    video = models.ForeignKey(VideoPost, on_delete=models.CASCADE, related_name='views_log')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"View of {self.video.title} by {self.user} at {self.timestamp}"



class PopularVideoRecord(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    video_1 = models.ForeignKey('VideoPost', on_delete=models.CASCADE, related_name='top1')
    score_1 = models.FloatField()
    video_2 = models.ForeignKey('VideoPost', on_delete=models.CASCADE, related_name='top2', null=True, blank=True)
    score_2 = models.FloatField(null=True, blank=True)
    video_3 = models.ForeignKey('VideoPost', on_delete=models.CASCADE, related_name='top3', null=True, blank=True)
    score_3 = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Popular videos at {self.timestamp}"


User = get_user_model()
