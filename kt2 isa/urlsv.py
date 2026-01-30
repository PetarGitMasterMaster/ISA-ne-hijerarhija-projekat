"""
URL configuration for jutjubic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

app_name = "videos"

urlpatterns = [
    path("", views.video_list, name="list"),
    path("upload/", views.video_create, name="create"),
    path("nearby/", views.nearby_videos, name="nearby_videos"),
    path("<slug:slug>/", views.video_detail, name="detail"),
    path("<slug:slug>/edit/", views.video_update, name="edit"),
    path("<slug:slug>/delete/", views.video_delete, name="delete"),
    path("<slug:slug>/like/", views.video_like_toggle, name="like"),
    


]

