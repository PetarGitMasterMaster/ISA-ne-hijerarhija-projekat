from django.core.management.base import BaseCommand
from django.utils import timezone
from videos.models import VideoPost, PopularVideo
from django.db.models import Count
from datetime import timedelta

#class Command(BaseCommand):
 #   help = "Generate list of popular videos (ETL pipeline)"

  #  def handle(self, *args, **kwargs):
   #     PopularVideo.objects.all().delete()  # Clear previous results

#        now = timezone.now()
 #       top_videos = []

#        for video in VideoPost.objects.all():
 #           score = 0
  #          for i in range(7):
   #             day = now - timedelta(days=i)
    #            views = video.views_last_n_days(day, day + timedelta(days=1))  # We'll define this method
     #           weight = 7 - i
      #          score += views * weight
#
   #         if score > 0:
    #            top_videos.append((video, score))

     #   top_videos.sort(key=lambda x: x[1], reverse=True)
      #  for video, score in top_videos[:3]:  # Top 3
       #     PopularVideo.objects.create(video=video, score=score)
        #    self.stdout.write(f"{video.title} - {score}")


class Command(BaseCommand):
    help = "Generate daily popular videos based on recent views"

    def handle(self, *args, **options):
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)

        video_scores = []

        # Extract and Transform
        for video in VideoPost.objects.all():
            score = 0
            for i in range(7):
                day = now - timedelta(days=i)
                # Count views for that day
                views = video.views_log.filter(
                    timestamp__date=day.date()
                ).count()
                weight = 7 - i  # 7 for yesterday, 1 for 7 days ago
                score += views * weight
            video_scores.append((video, score))

        # Sort by score descending
        video_scores.sort(key=lambda x: x[1], reverse=True)

        # Take top 3
        top3 = video_scores[:3]

        # Load into PopularVideoRecord
        record = PopularVideoRecord(
            video_1=top3[0][0] if len(top3) > 0 else None,
            score_1=top3[0][1] if len(top3) > 0 else 0,
            video_2=top3[1][0] if len(top3) > 1 else None,
            score_2=top3[1][1] if len(top3) > 1 else 0,
            video_3=top3[2][0] if len(top3) > 2 else None,
            score_3=top3[2][1] if len(top3) > 2 else 0,
        )
        record.save()

        self.stdout.write(self.style.SUCCESS('Popular videos ETL completed successfully.'))