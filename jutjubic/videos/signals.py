import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import VideoPost


@receiver(post_delete, sender=VideoPost)
def delete_files_on_post_delete(sender, instance, **kwargs):
    if instance.video:
        if os.path.isfile(instance.video.path):
            os.remove(instance.video.path)

    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)



@receiver(pre_save, sender=VideoPost)
def delete_old_files_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = VideoPost.objects.get(pk=instance.pk)
    except VideoPost.DoesNotExist:
        return

    if old_instance.video and old_instance.video != instance.video:
        if os.path.isfile(old_instance.video.path):
            os.remove(old_instance.video.path)


    if old_instance.thumbnail and old_instance.thumbnail != instance.thumbnail:
        if os.path.isfile(old_instance.thumbnail.path):
            os.remove(old_instance.thumbnail.path)



     




