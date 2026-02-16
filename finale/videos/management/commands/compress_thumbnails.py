from django.core.management.base import BaseCommand
from django.utils import timezone
from videos.models import VideoPost
from PIL import Image
import os

class Command(BaseCommand):
    help = "Compress thumbnails older than 1 month"

    def handle(self, *args, **kwargs):
        cutoff = timezone.now() - timezone.timedelta(days=30)
        videos = VideoPost.objects.filter(thumbnail__isnull=False, created_at__lt=cutoff)

        for video in videos:
            img_path = video.thumbnail.path
            compressed_path = img_path.replace(".jpg", "_compressed.jpg")  # adjust if png
            if os.path.exists(compressed_path):
                continue

            img = Image.open(img_path)
            img.save(compressed_path, "JPEG", optimize=True, quality=70)
            self.stdout.write(f"Compressed: {compressed_path}")


