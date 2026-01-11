from django.shortcuts import get_object_or_404, render
from django.contrib.auth import get_user_model
from videos.models import VideoPost

User = get_user_model()

def profile_detail(request, username):
    user = get_object_or_404(User, username=username)

    uploaded_videos = VideoPost.objects.filter(author=user)
    liked_videos = VideoPost.objects.filter(likes=user)

    return render(
        request,
        "profiles/profile_detail.html",
        {
            "profile_user": user,
            "uploaded_videos": uploaded_videos,
            "liked_videos": liked_videos,
        }
    )


