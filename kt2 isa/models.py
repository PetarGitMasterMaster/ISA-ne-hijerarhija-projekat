from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.contrib.postgres.indexes import GistIndex

from django.db.models import F, FloatField, ExpressionWrapper, Count
from django.utils.timezone import now
from django.db.models import Func
from django.utils import timezone
import math
from datetime import timedelta
from django.db.models.functions import Coalesce

#from django.db.models.functions import ExtractEpoch



def validate_video_size(value):
    max_size = 200 * 1024 * 1024  # 200MB
    if value.size > max_size:
        raise ValidationError("Video file too large (max 200MB).")

def validate_mp4(value):
    if not value.name.lower().endswith(".mp4"):
        raise ValidationError("Only MP4 videos are allowed.")


class VideoPostQuerySet(models.QuerySet):

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

    location = gis_models.PointField(null=True, blank=True, srid=4326)

    created_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_videos",
        blank=True
    )

    
    objects = VideoPostQuerySet.as_manager()

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

    class Meta:
        indexes = [
            GistIndex(fields=["location"]),  # spatial index for PostGIS
        ]

    def __str__(self):
        return self.title


User = get_user_model()




