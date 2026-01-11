from django.urls import path
from . import views

app_name = "comments"

urlpatterns = [
    path("delete/<int:pk>/", views.comment_delete, name="delete"),
]
