from background_task import background
from django.utils import timezone
from videos.models import VideoPost, PopularVideoRecord
from datetime import timedelta

@background(schedule=0)  # run immediately when scheduled
def generate_popular_videos():
    now = timezone.now()
    video_scores = []

    for video in VideoPost.objects.all():
        score = 0
        for i in range(7):
            day = now - timedelta(days=i)
            views = video.views_log.filter(timestamp__date=day.date()).count()
            weight = 7 - i
            score += views * weight
        video_scores.append((video, score))

    video_scores.sort(key=lambda x: x[1], reverse=True)
    top3 = video_scores[:3]

    record = PopularVideoRecord(
        video_1=top3[0][0] if len(top3) > 0 else None,
        score_1=top3[0][1] if len(top3) > 0 else 0,
        video_2=top3[1][0] if len(top3) > 1 else None,
        score_2=top3[1][1] if len(top3) > 1 else 0,
        video_3=top3[2][0] if len(top3) > 2 else None,
        score_3=top3[2][1] if len(top3) > 2 else 0,
    )
    record.save()
