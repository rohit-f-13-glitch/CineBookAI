from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from movies.models import Booking, Notification


class Command(BaseCommand):
    help = "Send notifications for upcoming movie shows"

    def handle(self, *args, **options):

        now = timezone.now()

        reminder_start = now + timedelta(minutes=55)
        reminder_end = now + timedelta(minutes=65)

        bookings = Booking.objects.filter(
            status="confirmed",
            showtime__starts_at__gte=reminder_start,
            showtime__starts_at__lte=reminder_end,
            user__isnull=False,
        ).select_related(
            "user",
            "showtime__movie",
            "showtime__cinema",
        )

        created_count = 0

        for booking in bookings:

            movie = booking.showtime.movie

            already_sent = Notification.objects.filter(
                user=booking.user,
                booking=booking,
                notification_type="show_reminder",
            ).exists()

            if already_sent:
                continue

            Notification.objects.create(
                user=booking.user,
                title="Your Movie Starts Soon 🎬",
                message=(
                    f'Your movie "{movie.title}" '
                    f'at {booking.showtime.cinema.name} '
                    f'starts in about 1 hour. '
                    f'Please arrive a little early.'
                ),
                notification_type="show_reminder",
                booking=booking,
                movie=movie,
            )

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Show reminders sent: {created_count}"
            )
        )