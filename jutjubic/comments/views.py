from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .models import Comment
from .forms import CommentForm


@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if comment.author != request.user:
        return HttpResponseForbidden("You are not allowed to delete this comment.")

    if request.method == "POST":
        video_slug = comment.video.slug
        comment.delete()
        return redirect("videos:detail", slug=video_slug)

    return render(request, "comments/comment_confirm_delete.html", {"comment": comment})




#from django.shortcuts import render

# Create your views here.
