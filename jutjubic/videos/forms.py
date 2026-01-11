from django import forms
from .models import VideoPost
from comments.models import Comment


class VideoPostForm(forms.ModelForm):
    class Meta:
        model = VideoPost
        fields = ["title", "description", "video", "thumbnail"]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Add a comment..."
            })
        }     




