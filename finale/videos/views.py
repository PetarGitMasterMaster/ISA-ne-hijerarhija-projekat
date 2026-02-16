from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F

from django.contrib.gis.geos import Point

from .models import VideoPost
from .forms import VideoPostForm, CommentForm
from comments.models import Comment

from ipware import get_client_ip
import time

from django.utils import timezone

from videos.models import PopularVideoRecord, VideoView


# ==========================
# Create / Update / Delete
# ==========================

@login_required
def video_create(request):
    if request.method == "POST":
        form = VideoPostForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                video = form.save(commit=False)
                video.author = request.user
                video.save()

            messages.success(request, "Video uploaded successfully.")
            return redirect("videos:list")
    else:
        form = VideoPostForm()

    return render(request, "videos/video_form.html", {"form": form})


@login_required
def video_update(request, slug):
    video = get_object_or_404(VideoPost, slug=slug)

    if video.author != request.user:
        return HttpResponseForbidden("You are not allowed to edit this video.")

    if request.method == "POST":
        form = VideoPostForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            form.save()
            return redirect("videos:detail", slug=video.slug)
    else:
        form = VideoPostForm(instance=video)

    return render(request, "videos/video_form.html", {"form": form})


@login_required
def video_delete(request, slug):
    video = get_object_or_404(VideoPost, slug=slug)

    if video.author != request.user:
        return HttpResponseForbidden("You are not allowed to delete this video.")

    if request.method == "POST":
        video.delete()
        return redirect("videos:list")

    return render(request, "videos/video_confirm_delete.html", {"video": video})


# ==========================
# Likes
# ==========================

@login_required
def video_like_toggle(request, slug):
    video = get_object_or_404(VideoPost, slug=slug)

    if request.user in video.likes.all():
        video.likes.remove(request.user)
    else:
        video.likes.add(request.user)

    return redirect("videos:detail", slug=video.slug)


# ==========================
# Video List (Feed)
# ==========================

def video_list(request):
    query = request.GET.get("q", "")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius_km = float(request.GET.get("radius", 5))

    point = None
    if lat and lng:
        try:
            point = Point(float(lng), float(lat), srid=4326)
        except ValueError:
            point = None

    start = time.perf_counter()

    # Only include videos that are available AND have a slug
    qs = VideoPost.objects.available().exclude(slug="")

    if point:
        qs = qs.nearby(point, km=radius_km).with_popularity(point)
    else:
        qs = qs.with_popularity()

    if query:
        qs = qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    qs = qs.select_related("author").distinct()

    end = time.perf_counter()
    response_time_ms = round((end - start) * 1000, 2)

    paginator = Paginator(qs, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)


    top_videos = []
    if request.user.is_authenticated:
        latest_record = PopularVideoRecord.objects.order_by("-timestamp").first()
        if latest_record:
            top_videos = [
                v for v in [latest_record.video_1, latest_record.video_2, latest_record.video_3] if v
            ] 


    return render(
        request,
        "videos/video_list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "point": point,
            "radius_km": radius_km,
            "response_time_ms": response_time_ms,
            "top_videos" : top_videos,
        },
    )


# ==========================
# Video Detail
# ==========================

def video_detail(request, slug):
    video = get_object_or_404(VideoPost, slug=slug)

    # 🚫 Block before scheduled release
    if not video.is_available():
        return render(request, "videos/video_countdown.html", {"video": video})

    # Increment views safely
    VideoPost.objects.filter(pk=video.pk).update(views=F("views") + 1)
    video.refresh_from_db(fields=["views"])
    
    # Log the view with timestamp
    VideoView.objects.create(
        video=video,
        user=request.user if request.user.is_authenticated else None
    )

    # Location
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    point = None

    if lat and lng:
        try:
            point = Point(float(lng), float(lat), srid=4326)
        except ValueError:
            point = None
    else:
        ip, _ = get_client_ip(request)
        if ip:
            # Default fallback (Belgrade)
            point = Point(20.46, 44.81, srid=4326)

    if point:
        video = (
            VideoPost.objects
            .filter(pk=video.pk)
            .with_distance(point)
            .with_popularity(point)
            .first()
        )

    comments = video.comments.select_related("author")

    is_liked = False
    if request.user.is_authenticated:
        is_liked = video.likes.filter(id=request.user.id).exists()

    if request.method == "POST" and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.video = video
            comment.author = request.user
            comment.save()
            return redirect("videos:detail", slug=slug)
    else:
        form = CommentForm()
    

    offset_seconds = 0
    if video.scheduled_at:
        now = timezone.now() 
        
        if now < video.scheduled_at:
            seconds_until_start = int((video.scheduled_at - now).total_seconds())

        else:
            seconds_until_start = 0
            delta = now - video.scheduled_at
            offset_seconds = int(delta.total_seconds())

            if video.duration_seconds:
                offset_seconds = min(offset_seconds, video.duration_seconds)          
    else:
        seconds_until_start = 0


    return render(
        request,
        "videos/video_detail.html",
        {
            "video": video,
            "comments": comments,
            "form": form,
            "is_liked": is_liked,
            "point": point,
            "offset_seconds": offset_seconds,  
            "seconds_until_start": seconds_until_start,
        }
    )

def upcoming_videos(request):
    videos = (
        VideoPost.objects
        .upcoming()
        .select_related("author")
        .only("id", "title", "scheduled_at", "author__username")
    )

    return render(request, "videos/upcoming.html", {
        "videos": videos
    })



# ==========================
# Nearby Videos (AJAX)
# ==========================

def nearby_videos(request):
    try:
        radius = float(request.GET.get("radius", 5))
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")

        if lat and lng:
            point = Point(float(lng), float(lat), srid=4326)
        else:
            point = Point(20.46, 44.81, srid=4326)

        videos = (
            VideoPost.objects
            .available()
            .nearby(point, km=radius)
            .with_distance(point)
            .with_popularity(point)
        )

        data = [
            {
                "id": v.id,
                "title": v.title,
                "distance": round(v.distance.km, 2) if hasattr(v, "distance") else None,
                "popularity": round(v.popularity, 2) if hasattr(v, "popularity") else None,
            }
            for v in videos
        ]

        return JsonResponse({"videos": data})

    except Exception:
        return JsonResponse({"videos": []})
