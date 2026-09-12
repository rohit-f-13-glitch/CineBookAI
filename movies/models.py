from django.db import models
from django.contrib.auth.models import User


# ========================================================
# CITY
# ========================================================

class City(models.Model):

    name = models.CharField(
        max_length=100
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ========================================================
# CINEMA
# ========================================================

class Cinema(models.Model):

    name = models.CharField(
        max_length=150
    )

    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="cinemas",
    )

    address = models.TextField(
        blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.city.name}"


# ========================================================
# MOVIE
# ========================================================

class Movie(models.Model):

    title = models.CharField(
        max_length=150
    )

    tmdb_id = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True,
    )

    genre = models.CharField(
        max_length=100
    )

    language = models.CharField(
        max_length=50,
        default="English",
    )

    duration_minutes = models.PositiveIntegerField()

    release_date = models.DateField()

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
    )

    # ====================================================
    # MOVIE POSTER
    # ====================================================

    poster_url = models.URLField(
        blank=True,
        null=True,
    )

    description = models.TextField(
        blank=True
    )

    is_now_showing = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["-release_date"]

    def __str__(self):
        return self.title


# ========================================================
# WATCHLIST / FAVORITES
# ========================================================

class Watchlist(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watchlist",
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="watchlisted_by",
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-added_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "movie",
                ],
                name="unique_user_movie_watchlist",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.movie.title}"
        )


# ========================================================
# MOVIE REVIEW & RATING
# ========================================================

class MovieReview(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="movie_reviews",
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    rating = models.PositiveIntegerField(
        choices=[
            (1, "1 Star"),
            (2, "2 Stars"),
            (3, "3 Stars"),
            (4, "4 Stars"),
            (5, "5 Stars"),
        ]
    )

    review_text = models.TextField(
        max_length=1000,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "movie",
                ],
                name="unique_user_movie_review",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.movie.title} - "
            f"{self.rating}/5"
        )


# ========================================================
# SCREEN
# ========================================================

class Screen(models.Model):

    cinema = models.ForeignKey(
        Cinema,
        on_delete=models.CASCADE,
        related_name="screens",
    )

    name = models.CharField(
        max_length=100
    )

    capacity = models.PositiveIntegerField(
        default=100
    )

    class Meta:
        ordering = [
            "cinema",
            "name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "cinema",
                    "name",
                ],
                name="unique_screen_per_cinema",
            )
        ]

    def __str__(self):
        return (
            f"{self.cinema.name} - "
            f"{self.name}"
        )


# ========================================================
# SHOWTIME
# ========================================================

class ShowTime(models.Model):

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="showtimes",
    )

    cinema = models.ForeignKey(
        Cinema,
        on_delete=models.CASCADE,
        related_name="showtimes",
    )

    screen = models.ForeignKey(
        Screen,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="showtimes",
    )

    starts_at = models.DateTimeField()

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return (
            f"{self.movie.title} - "
            f"{self.cinema.name} - "
            f"{self.starts_at}"
        )


# ========================================================
# SEAT
# ========================================================

class Seat(models.Model):

    cinema = models.ForeignKey(
        Cinema,
        on_delete=models.CASCADE,
        related_name="seats",
    )

    seat_number = models.CharField(
        max_length=20
    )

    class Meta:
        ordering = ["seat_number"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "cinema",
                    "seat_number",
                ],
                name="unique_seat_per_cinema",
            )
        ]

    def __str__(self):
        return (
            f"{self.cinema.name} - "
            f"{self.seat_number}"
        )


# ========================================================
# BOOKING
# ========================================================

class Booking(models.Model):

    # ====================================================
    # BOOKING STATUS
    # ====================================================

    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )

    customer_name = models.CharField(
        max_length=150
    )

    customer_email = models.EmailField()

    total_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    booking_time = models.DateTimeField(
        auto_now_add=True
    )

    showtime = models.ForeignKey(
        ShowTime,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    seats = models.ManyToManyField(
        Seat,
        related_name="bookings",
    )

    # ====================================================
    # STATUS FIELD
    # ====================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="confirmed",
    )

    class Meta:
        ordering = ["-booking_time"]

    def __str__(self):
        return (
            f"Booking #{self.id} - "
            f"{self.customer_name}"
        )


# ========================================================
# PAYMENT
# ========================================================

class Payment(models.Model):

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("upi", "UPI"),
        ("card", "Credit / Debit Card"),
        ("netbanking", "Net Banking"),
        ("wallet", "Wallet"),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="payment",
    )

    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        default="upi",
    )

    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )

    # ====================================================
    # RAZORPAY ORDER ID
    # ====================================================

    razorpay_order_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"Payment #{self.id} - "
            f"Booking #{self.booking.id} - "
            f"{self.status}"
        )


# ========================================================
# NOTIFICATION
# ========================================================

class Notification(models.Model):

    # ====================================================
    # NOTIFICATION TYPES
    # ====================================================

    NOTIFICATION_TYPE_CHOICES = [
        ("booking_confirmed", "Booking Confirmed"),
        ("payment_successful", "Payment Successful"),
        ("booking_cancelled", "Booking Cancelled"),
        ("new_movie", "New Movie"),
        ("show_reminder", "Show Reminder"),
        ("watchlist", "Watchlist"),
        ("review", "Review"),
        ("ai", "CineBookAI"),
        ("general", "General"),
    ]

    # ====================================================
    # USER
    # ====================================================

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    # ====================================================
    # NOTIFICATION CONTENT
    # ====================================================

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        default="general",
    )

    # ====================================================
    # OPTIONAL RELATED OBJECTS
    # ====================================================

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    # ====================================================
    # READ / UNREAD
    # ====================================================

    is_read = models.BooleanField(
        default=False
    )

    # ====================================================
    # TIMESTAMP
    # ====================================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ====================================================
    # ORDERING
    # ====================================================

    class Meta:
        ordering = ["-created_at"]

    # ====================================================
    # STRING REPRESENTATION
    # ====================================================

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.title}"
        )