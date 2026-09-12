from .models import Notification


def notification_context(request):
    """
    Adds the unread notification count to every template.
    """

    notification_unread_count = 0

    if request.user.is_authenticated:

        notification_unread_count = (
            Notification.objects
            .filter(
                user=request.user,
                is_read=False,
            )
            .count()
        )

    return {
        "notification_unread_count": notification_unread_count,
    }