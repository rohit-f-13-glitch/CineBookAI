from django.contrib import admin

from .models import (
    Movie,
    City,
    Cinema,
    Screen,
    ShowTime,
    Seat,
    Booking,
    Payment,
    Watchlist,
    MovieReview,
)

from .tmdb_utils import fetch_tmdb_movie


# ========================================================
# MOVIE ADMIN
# ========================================================

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "genre",
        "language",
        "rating",
        "release_date",
        "is_now_showing",
    )

    list_filter = (
        "genre",
        "language",
        "is_now_showing",
    )

    search_fields = (
        "title",
        "genre",
        "description",
    )

    ordering = (
        "-release_date",
    )

    def save_model(self, request, obj, form, change):
        """
        Automatically fetch movie information from TMDB
        when a TMDB ID is provided in Django Admin.
        """

        if obj.tmdb_id:
            try:
                tmdb_data = fetch_tmdb_movie(obj.tmdb_id)

                # Automatically update poster
                if tmdb_data["poster_url"]:
                    obj.poster_url = tmdb_data["poster_url"]

                # Automatically update description
                if tmdb_data["description"]:
                    obj.description = tmdb_data["description"]

                # Automatically update duration
                if tmdb_data["duration_minutes"]:
                    obj.duration_minutes = tmdb_data["duration_minutes"]

                # Automatically update rating
                if tmdb_data["rating"]:
                    obj.rating = tmdb_data["rating"]

                # Automatically update release date
                if tmdb_data["release_date"]:
                    obj.release_date = tmdb_data["release_date"]

                # Automatically update genre
                if tmdb_data["genres"]:
                    obj.genre = tmdb_data["genres"]

                # Automatically update title
                if tmdb_data["title"]:
                    obj.title = tmdb_data["title"]

            except Exception as e:
                self.message_user(
                    request,
                    f"TMDB fetch failed: {e}",
                    level="error",
                )
                return

        super().save_model(request, obj, form, change)


# ========================================================
# CITY ADMIN
# ========================================================

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )


# ========================================================
# CINEMA ADMIN
# ========================================================

@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "address",
        "screen_count",
    )

    list_filter = (
        "city",
    )

    search_fields = (
        "name",
        "address",
        "city__name",
    )

    ordering = (
        "name",
    )

    list_select_related = (
        "city",
    )

    @admin.display(
        description="Screens"
    )
    def screen_count(self, obj):
        return obj.screens.count()


# ========================================================
# SCREEN ADMIN
# ========================================================

@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "cinema",
        "city_name",
        "capacity",
        "showtime_count",
    )

    list_filter = (
        "cinema",
        "cinema__city",
    )

    search_fields = (
        "name",
        "cinema__name",
        "cinema__city__name",
    )

    ordering = (
        "cinema",
        "name",
    )

    list_select_related = (
        "cinema",
        "cinema__city",
    )

    @admin.display(
        description="City"
    )
    def city_name(self, obj):
        return obj.cinema.city.name

    @admin.display(
        description="Showtimes"
    )
    def showtime_count(self, obj):
        return obj.showtimes.count()


# ========================================================
# SHOWTIME ADMIN
# ========================================================

@admin.register(ShowTime)
class ShowTimeAdmin(admin.ModelAdmin):
    list_display = (
        "movie",
        "cinema",
        "screen",
        "starts_at",
        "price",
    )

    list_filter = (
        "cinema__city",
        "cinema",
        "screen",
        "movie",
    )

    search_fields = (
        "movie__title",
        "cinema__name",
        "cinema__city__name",
        "screen__name",
    )

    ordering = (
        "starts_at",
    )

    list_select_related = (
        "movie",
        "cinema",
        "cinema__city",
        "screen",
    )

    date_hierarchy = "starts_at"


# ========================================================
# SEAT ADMIN
# ========================================================

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = (
        "seat_number",
        "cinema",
        "city_name",
    )

    list_filter = (
        "cinema",
        "cinema__city",
    )

    search_fields = (
        "seat_number",
        "cinema__name",
        "cinema__city__name",
    )

    ordering = (
        "cinema",
        "seat_number",
    )

    list_select_related = (
        "cinema",
        "cinema__city",
    )

    @admin.display(
        description="City"
    )
    def city_name(self, obj):
        return obj.cinema.city.name


# ========================================================
# BOOKING ADMIN
# ========================================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "showtime",
        "seat_count",
        "total_amount",
        "payment_status",
        "status",
        "booking_time",
    )

    list_filter = (
        "status",
        "booking_time",
        "showtime__cinema",
        "showtime__movie",
        "showtime__cinema__city",
    )

    search_fields = (
        "customer_name",
        "customer_email",
        "showtime__movie__title",
        "showtime__cinema__name",
    )

    ordering = (
        "-booking_time",
    )

    list_select_related = (
        "user",
        "showtime",
        "showtime__movie",
        "showtime__cinema",
        "showtime__cinema__city",
    )

    @admin.display(
        description="Seats"
    )
    def seat_count(self, obj):
        return obj.seats.count()

    @admin.display(
        description="Payment"
    )
    def payment_status(self, obj):
        try:
            return obj.payment.status.title()
        except Payment.DoesNotExist:
            return "Not Created"


# ========================================================
# PAYMENT ADMIN
# ========================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "booking",
        "customer_name",
        "amount",
        "payment_method",
        "status",
        "transaction_id",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_method",
        "created_at",
    )

    search_fields = (
        "transaction_id",
        "booking__customer_name",
        "booking__customer_email",
        "booking__showtime__movie__title",
    )

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "booking",
        "booking__showtime",
        "booking__showtime__movie",
    )

    @admin.display(
        description="Customer"
    )
    def customer_name(self, obj):
        return obj.booking.customer_name


# ========================================================
# WATCHLIST ADMIN
# ========================================================

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "movie",
        "added_at",
    )

    list_filter = (
        "added_at",
        "movie",
    )

    search_fields = (
        "user__username",
        "user__email",
        "movie__title",
    )

    ordering = (
        "-added_at",
    )

    list_select_related = (
        "user",
        "movie",
    )


# ========================================================
# MOVIE REVIEW & RATING ADMIN
# ========================================================

@admin.register(MovieReview)
class MovieReviewAdmin(admin.ModelAdmin):
    list_display = (
        "movie",
        "user",
        "rating",
        "review_text",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "rating",
        "created_at",
        "updated_at",
        "movie",
    )

    search_fields = (
        "movie__title",
        "user__username",
        "user__email",
        "review_text",
    )

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "user",
        "movie",
    )