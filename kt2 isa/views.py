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
from django.contrib.gis.measure import D
from ipware import get_client_ip
import geoip2.database
import time



@login_required
def video_create(request):
    if request.method == "POST":
        form = VideoPostForm(request.POST, request.FILES)
        if form.is_valid():
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
        return HttpResponseForbidden()
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
        return HttpResponseForbidden()
    if request.method == "POST":
        video.delete()
        return redirect("videos:list")
    return render(request, "videos/video_confirm_delete.html", {"video": video})



@login_required
def video_like_toggle(request, slug):
    video = get_object_or_404(VideoPost, slug=slug)
    if request.user in video.likes.all():
        video.likes.remove(request.user)
    else:
        video.likes.add(request.user)
    return redirect("videos:detail", slug=video.slug)


def video_list(request):
    query = request.GET.get("q", "")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius_km = request.GET.get("radius", 5)  
    strategy = request.GET.get("strategy", "realtime")  

    point = None
    if lat and lng:
        try:
            point = Point(float(lng), float(lat), srid=4326)
        except ValueError:
            pass

 
    start = time.perf_counter()

    
    if strategy == "global":
        qs = VideoPost.objects.global_popularity()
    elif strategy == "cached":
        qs = VideoPost.objects.cached_popularity(point)
    else:
        qs = VideoPost.objects.with_popularity(point)

    
    videos = list(qs[:50])  

    end = time.perf_counter()
    response_time_ms = (end - start) * 1000
 

    
    if query:
        videos = [v for v in videos if query.lower() in v.title.lower() or query.lower() in v.description.lower()]

    
    paginator = Paginator(videos, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "videos/video_list.html", {
        "page_obj": page_obj,
        "query": query,
        "point": point,
        "radius_km": radius_km,
        "strategy": strategy,
        "response_time_ms": round(response_time_ms, 2),
    })




def video_detail(request, slug):
    video = get_object_or_404(VideoPost, slug=slug)

    
    VideoPost.objects.filter(pk=video.pk).update(views=F("views") + 1)
    video.refresh_from_db(fields=["views"])

    
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    point = None

    if lat and lng:
        try:
            point = Point(float(lng), float(lat), srid=4326)
        except ValueError:
            point = None
    else:
        
        ip, is_routable = get_client_ip(request)
        if ip:

            point = Point(20.46, 44.81, srid=4326)

    
    if point:
        video = VideoPost.objects.filter(pk=video.pk).with_distance(point).with_popularity(point).first()

    
    comments = video.comments.select_related("author")

    
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

    return render(
        request,
        "videos/video_detail.html",
        {
            "video": video,
            "comments": comments,
            "form": form,
            "point": point,  
        },
    )



def nearby_videos(request):
    """
    Return videos nearby the user (AJAX) with distance and popularity.
    Accepts:
    - lat, lng: coordinates (optional if using IP fallback)
    - radius: search radius in km (default 5 km)
    """
    try:
        
        radius = float(request.GET.get("radius", 5))

        
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")

        if lat and lng:
            user_location = Point(float(lng), float(lat), srid=4326)
        else:
            
            client_ip, is_routable = get_client_ip(request)
            if client_ip:
                import requests
                try:
                    r = requests.get(f"https://ipapi.co/{client_ip}/json/")
                    if r.status_code == 200:
                        data = r.json()
                        user_location = Point(float(data.get("longitude", 20.46)),
                                              float(data.get("latitude", 44.81)),
                                              srid=4326)
                    else:
                        
                        user_location = Point(20.46, 44.81, srid=4326)
                except Exception:
                    user_location = Point(20.46, 44.81, srid=4326)
            else:
                
                user_location = Point(20.46, 44.81, srid=4326)

        
        videos = VideoPost.objects.nearby_with_distance(user_location, km=radius).with_popularity(user_location)

        data = [
            {
                "title": v.title,
                "distance": round(v.distance.km, 2) if hasattr(v, "distance") else None,
                "popularity": round(v.popularity, 2) if hasattr(v, "popularity") else None,
                "id": v.id,
            }
            for v in videos
        ]

        return JsonResponse({"videos": data})

    except (TypeError, ValueError):
        return JsonResponse({"videos": []})
