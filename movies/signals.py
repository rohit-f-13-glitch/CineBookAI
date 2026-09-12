from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Movie, Notification


@receiver(post_save, sender=Movie)
def create_new_movie_notifications(sender, instance, created, **kwargs):
    if not created:
        return

    users = User.objects.filter(is_active=True)

    notifications = []

    for user in users:
        notifications.append(
            Notification(
                user=user,
                title="New Movie Added",
                message=(
                    f'A new movie "{instance.title}" '
                    f'is now available on CineBookAI.'
                ),
                notification_type="new_movie",
                movie=instance,
            )
        )

    Notification.objects.bulk_create(notifications)