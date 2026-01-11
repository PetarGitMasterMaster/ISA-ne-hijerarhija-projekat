from django.db import transaction
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import F

from .models import VideoPost
from comments.models import Comment
from .forms import VideoPostForm, CommentForm


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

    videos = VideoPost.objects.all().order_by("-created_at")

    if query:
        videos = videos.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    paginator = Paginator(videos, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "videos/video_list.html",
        {
            "page_obj": page_obj,
            "query": query,
        },
    )    


def video_detail(request, slug):
    video = get_object_or_404(VideoPost, slug=slug)

    VideoPost.objects.filter(pk=video.pk).update(views=F("views") + 1)
    video.refresh_from_db(fields=["views"])

    is_liked = False
    if request.user.is_authenticated:
        is_liked = video.likes.filter(id=request.user.id).exists()

    comments = video.comments.select_related("author")

    if request.method == "POST" and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.video = video
            comment.author = request.user
            comment.save()
            return redirect("videos:detail", slug=video.slug)
    else:
        form = CommentForm()

    return render(request, "videos/video_detail.html", {
        "video": video,
        "comments": comments,
        "form": form,
        "is_liked": is_liked,
    })

