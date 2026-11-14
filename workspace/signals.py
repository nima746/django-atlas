from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task, Activity
@receiver(post_save, sender=Task)
def log_task(sender, instance, created, **kwargs):
    Activity.objects.create(task=instance, message="建立任務" if created else "更新任務：" + instance.get_status_display())
