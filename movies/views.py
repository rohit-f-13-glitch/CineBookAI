from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Avg, Sum
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings

import os
import razorpay

from dotenv import load_dotenv
from groq import Groq

from .models import (
    Movie,
    Cinema,
    ShowTime,
    Seat,
    Booking,
    Payment,
    Watchlist,
    MovieReview,
    Notification,
)


# ============================================================
# ENVIRONMENT + RAZORPAY
# ============================================================

load_dotenv()

razorpay_client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET,
    )
)


# ============================================================
# HOME
# ============================================================

def home(request):
    movies = Movie.objects.filter(
        is_now_showing=True
    ).order_by("-release_date")

    return render(
        request,
        "movies/home.html",
        {
            "movies": movies,
        },
    )


# ============================================================
# MOVIE SEARCH
# ============================================================

def search_movies(request):
    query = request.GET.get("q", "").strip()
    genre = request.GET.get("genre", "").strip()
    language = request.GET.get("language", "").strip()
    rating = request.GET.get("rating", "").strip()
    sort = request.GET.get("sort", "latest").strip()

    movies = Movie.objects.filter(
        is_now_showing=True
    )

    if query:
        movies = movies.filter(
            Q(title__icontains=query)
            | Q(genre__icontains=query)
            | Q(language__icontains=query)
        )

    if genre:
        movies = movies.filter(
            genre__iexact=genre
        )

    if language:
        movies = movies.filter(
            language__iexact=language
        )

    if rating:
        try:
            rating_value = float(rating)
            movies = movies.filter(
                rating__gte=rating_value
            )
        except ValueError:
            pass

    if sort == "rating":
        movies = movies.order_by(
            "-rating",
            "-release_date"
        )

    elif sort == "oldest":
        movies = movies.order_by(
            "release_date"
        )

    elif sort == "title":
        movies = movies.order_by(
            "title"
        )

    else:
        movies = movies.order_by(
            "-release_date"
        )

    genres = (
        Movie.objects
        .filter(is_now_showing=True)
        .exclude(genre__isnull=True)
        .exclude(genre="")
        .values_list("genre", flat=True)
        .distinct()
    )

    languages = (
        Movie.objects
        .filter(is_now_showing=True)
        .exclude(language__isnull=True)
        .exclude(language="")
        .values_list("language", flat=True)
        .distinct()
    )

    return render(
        request,
        "movies/search.html",
        {
            "movies": movies,
            "query": query,
            "selected_genre": genre,
            "selected_language": language,
            "selected_rating": rating,
            "selected_sort": sort,
            "genres": genres,
            "languages": languages,
            "result_count": movies.count(),
        },
    )


# ============================================================
# MOVIE DETAIL
# ============================================================

def movie_detail(request, movie_id):
    movie = get_object_or_404(
        Movie,
        id=movie_id
    )

    showtimes = (
        ShowTime.objects
        .filter(
            movie=movie,
            starts_at__gte=timezone.now(),
        )
        .select_related(
            "cinema",
            "cinema__city",
        )
        .order_by("starts_at")
    )

    reviews = (
        movie.reviews
        .select_related("user")
        .order_by("-created_at")
    )

    review_stats = movie.reviews.aggregate(
        average_rating=Avg("rating"),
        review_count=Sum(1),
    )

    average_rating = review_stats.get(
        "average_rating"
    )

    review_count = movie.reviews.count()

    user_review = None
    is_watchlisted = False

    if request.user.is_authenticated:
        user_review = movie.reviews.filter(
            user=request.user
        ).first()

        is_watchlisted = Watchlist.objects.filter(
            user=request.user,
            movie=movie
        ).exists()

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie,
            "showtimes": showtimes,
            "reviews": reviews,
            "average_rating": average_rating,
            "review_count": review_count,
            "user_review": user_review,
            "is_watchlisted": is_watchlisted,
        },
    )


# ============================================================
# WATCHLIST
# ============================================================

@login_required(login_url="login")
def add_to_watchlist(request, movie_id):
    movie = get_object_or_404(
        Movie,
        id=movie_id
    )

    Watchlist.objects.get_or_create(
        user=request.user,
        movie=movie,
    )

    messages.success(
        request,
        f'"{movie.title}" added to your watchlist.'
    )

    return redirect(
        "movie_detail",
        movie_id=movie.id
    )


@login_required(login_url="login")
def remove_from_watchlist(request, movie_id):
    movie = get_object_or_404(
        Movie,
        id=movie_id
    )

    Watchlist.objects.filter(
        user=request.user,
        movie=movie,
    ).delete()

    messages.success(
        request,
        f'"{movie.title}" removed from your watchlist.'
    )

    return redirect(
        "movie_detail",
        movie_id=movie.id
    )


@login_required(login_url="login")
def my_watchlist(request):
    watchlist = (
        Watchlist.objects
        .filter(user=request.user)
        .select_related("movie")
        .order_by("-added_at")
    )

    return render(
        request,
        "movies/watchlist.html",
        {
            "watchlist": watchlist,
        },
    )


# ============================================================
# MOVIE REVIEWS
# ============================================================

@login_required(login_url="login")
def submit_movie_review(request, movie_id):
    movie = get_object_or_404(
        Movie,
        id=movie_id
    )

    if request.method != "POST":
        return redirect(
            "movie_detail",
            movie_id=movie.id
        )

    try:
        rating = int(
            request.POST.get("rating", 0)
        )
    except (TypeError, ValueError):
        rating = 0

    review_text = request.POST.get(
        "review_text",
        ""
    ).strip()

    if rating < 1 or rating > 5:
        messages.error(
            request,
            "Please select a rating between 1 and 5."
        )

        return redirect(
            "movie_detail",
            movie_id=movie.id
        )

    MovieReview.objects.update_or_create(
        user=request.user,
        movie=movie,
        defaults={
            "rating": rating,
            "review_text": review_text,
        },
    )

    messages.success(
        request,
        "Your review has been saved successfully."
    )

    return redirect(
        "movie_detail",
        movie_id=movie.id
    )


@login_required(login_url="login")
def delete_movie_review(request, movie_id):
    movie = get_object_or_404(
        Movie,
        id=movie_id
    )

    if request.method == "POST":
        MovieReview.objects.filter(
            user=request.user,
            movie=movie,
        ).delete()

        messages.success(
            request,
            "Your review has been deleted."
        )

    return redirect(
        "movie_detail",
        movie_id=movie.id
    )


# ============================================================
# CINEMA SEATS
# ============================================================

def ensure_cinema_seats(cinema):
    seat_numbers = []

    rows = "ABCDEFGHIJ"

    for row in rows:
        for number in range(1, 21):
            seat_numbers.append(
                f"{row}{number}"
            )

    existing_seats = {
        seat_number: seat
        for seat in Seat.objects.filter(
            cinema=cinema
        )
        for seat_number in [seat.seat_number]
    }

    seats_to_update = []

    for seat_number, seat in existing_seats.items():

        row = seat_number[0]

        if row in "ABCD":
            seat_type = "normal"
            seat_price = 150

        elif row in "EFGH":
            seat_type = "premium"
            seat_price = 200

        else:
            seat_type = "luxury"
            seat_price = 270

        if (
            seat.seat_type != seat_type
            or seat.seat_price != seat_price
        ):
            seat.seat_type = seat_type
            seat.seat_price = seat_price
            seats_to_update.append(seat)

    if seats_to_update:
        Seat.objects.bulk_update(
            seats_to_update,
            [
                "seat_type",
                "seat_price",
            ],
        )

    new_seats = []

    for seat_number in seat_numbers:

        if seat_number in existing_seats:
            continue

        row = seat_number[0]

        if row in "ABCD":
            seat_type = "normal"
            seat_price = 150

        elif row in "EFGH":
            seat_type = "premium"
            seat_price = 200

        else:
            seat_type = "luxury"
            seat_price = 270

        new_seats.append(
            Seat(
                cinema=cinema,
                seat_number=seat_number,
                seat_type=seat_type,
                seat_price=seat_price,
            )
        )

    if new_seats:
        Seat.objects.bulk_create(
            new_seats,
            ignore_conflicts=True,
        )


# ============================================================
# SEAT SELECTION
# ============================================================

@login_required(login_url="login")
def seat_selection(request, showtime_id):
    showtime = get_object_or_404(
        ShowTime.objects.select_related(
            "movie",
            "cinema",
            "cinema__city",
        ),
        id=showtime_id,
        starts_at__gte=timezone.now(),
    )

    ensure_cinema_seats(
        showtime.cinema
    )

    seats = (
        Seat.objects
        .filter(cinema=showtime.cinema)
        .order_by("seat_number")
    )

    booked_seat_ids = (
        Seat.objects
        .filter(
            bookings__showtime=showtime,
            bookings__status="confirmed",
        )
        .values_list(
            "id",
            flat=True
        )
        .distinct()
    )

    return render(
        request,
        "movies/seat_selection.html",
        {
            "showtime": showtime,
            "seats": seats,
            "booked_seat_ids": set(
                booked_seat_ids
            ),
        },
    )


# ============================================================
# BOOKING DETAILS
# ============================================================

@login_required(login_url="login")
def booking_details(request, showtime_id):
    showtime = get_object_or_404(
        ShowTime.objects.select_related(
            "movie",
            "cinema",
            "cinema__city",
        ),
        id=showtime_id,
        starts_at__gte=timezone.now(),
    )

    if request.method == "GET":
        selected_seat_ids = request.session.get(
            "selected_seat_ids"
        )

        booking_showtime_id = request.session.get(
            "booking_showtime_id"
        )

        if (
            not selected_seat_ids
            or booking_showtime_id != showtime.id
        ):
            messages.error(
                request,
                "Please select your seats first."
            )

            return redirect(
                "seat_selection",
                showtime_id=showtime.id
            )

        seats = Seat.objects.filter(
            id__in=selected_seat_ids,
            cinema=showtime.cinema,
        )

        if seats.count() != len(
            selected_seat_ids
        ):
            messages.error(
                request,
                "Some selected seats are no longer available."
            )

            return redirect(
                "seat_selection",
                showtime_id=showtime.id
            )

        total_amount = (
            seats.aggregate(
                total=Sum("seat_price")
            ).get("total")
            or 0
        )

        return render(
            request,
            "movies/booking_details.html",
            {
                "showtime": showtime,
                "seats": seats,
                "total_amount": total_amount,
            },
        )

    # --------------------------------------------------------
    # FIRST STEP: SELECT SEATS
    # --------------------------------------------------------

    seats_input = request.POST.getlist(
        "seats"
    )

    if not request.POST.get(
        "confirm_booking"
    ):
        if not seats_input:
            messages.error(
                request,
                "Please select at least one seat."
            )

            return redirect(
                "seat_selection",
                showtime_id=showtime.id
            )

        seats = Seat.objects.filter(
            id__in=seats_input,
            cinema=showtime.cinema,
        )

        if seats.count() != len(
            seats_input
        ):
            messages.error(
                request,
                "Invalid seat selection."
            )

            return redirect(
                "seat_selection",
                showtime_id=showtime.id
            )

        already_booked = (
            Seat.objects
            .filter(
                id__in=seats_input,
                bookings__showtime=showtime,
                bookings__status="confirmed",
            )
            .exists()
        )

        if already_booked:
            messages.error(
                request,
                "One or more selected seats have already been booked."
            )

            return redirect(
                "seat_selection",
                showtime_id=showtime.id
            )

        request.session[
            "selected_seat_ids"
        ] = list(
            seats.values_list(
                "id",
                flat=True
            )
        )

        request.session[
            "booking_showtime_id"
        ] = showtime.id

        total_amount = (
            seats.aggregate(
                total=Sum("seat_price")
            ).get("total")
            or 0
        )

        return render(
            request,
            "movies/booking_details.html",
            {
                "showtime": showtime,
                "seats": seats,
                "total_amount": total_amount,
            },
        )

    # --------------------------------------------------------
    # SECOND STEP: CREATE PENDING BOOKING
    # --------------------------------------------------------

    selected_seat_ids = request.session.get(
        "selected_seat_ids"
    )

    booking_showtime_id = request.session.get(
        "booking_showtime_id"
    )

    if (
        not selected_seat_ids
        or booking_showtime_id != showtime.id
    ):
        messages.error(
            request,
            "Your seat selection has expired. Please select your seats again."
        )

        return redirect(
            "seat_selection",
            showtime_id=showtime.id
        )

    seats = Seat.objects.filter(
        id__in=selected_seat_ids,
        cinema=showtime.cinema,
    )

    if seats.count() != len(
        selected_seat_ids
    ):
        messages.error(
            request,
            "Some selected seats are no longer available."
        )

        return redirect(
            "seat_selection",
            showtime_id=showtime.id
        )

    customer_name = request.POST.get(
        "customer_name",
        ""
    ).strip()

    customer_email = request.POST.get(
        "customer_email",
        ""
    ).strip()

    if not customer_name or not customer_email:
        messages.error(
            request,
            "Please enter your name and email."
        )

        total_amount = (
            seats.aggregate(
                total=Sum("seat_price")
            ).get("total")
            or 0
        )

        return render(
            request,
            "movies/booking_details.html",
            {
                "showtime": showtime,
                "seats": seats,
                "total_amount": total_amount,
            },
        )

    total_amount = (
        seats.aggregate(
            total=Sum("seat_price")
        ).get("total")
        or 0
    )

    with transaction.atomic():

        already_booked = (
            Seat.objects
            .filter(
                id__in=selected_seat_ids,
                bookings__showtime=showtime,
                bookings__status="confirmed",
            )
            .exists()
        )

        if already_booked:
            messages.error(
                request,
                "One or more selected seats were just booked by another user."
            )

            return redirect(
                "seat_selection",
                showtime_id=showtime.id
            )

        booking = Booking.objects.create(
            user=request.user,
            customer_name=customer_name,
            customer_email=customer_email,
            total_amount=total_amount,
            showtime=showtime,
            status="pending",
        )

        booking.seats.set(
            seats
        )

        Payment.objects.create(
            booking=booking,
            amount=total_amount,
            payment_method="upi",
            status="pending",
        )

    request.session[
        "last_booking_id"
    ] = booking.id

    request.session.pop(
        "selected_seat_ids",
        None
    )

    request.session.pop(
        "booking_showtime_id",
        None
    )

    return redirect(
        "payment_page",
        booking_id=booking.id
    )


# ============================================================
# PAYMENT PAGE
# ============================================================

@login_required(login_url="login")
def payment_page(request, booking_id):

    booking = get_object_or_404(
        Booking.objects
        .select_related(
            "showtime",
            "showtime__movie",
            "showtime__cinema",
            "showtime__cinema__city",
        )
        .prefetch_related("seats"),
        id=booking_id,
        user=request.user,
    )

    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            "amount": booking.total_amount,
            "payment_method": "upi",
            "status": "pending",
        },
    )

    # --------------------------------------------------------
    # ALREADY SUCCESSFUL
    # --------------------------------------------------------

    if (
        payment.status == "success"
        and booking.status == "confirmed"
    ):
        return redirect(
            "booking_confirmation",
            booking_id=booking.id
        )

    # --------------------------------------------------------
    # CANCELLED BOOKING
    # --------------------------------------------------------

    if booking.status == "cancelled":
        messages.error(
            request,
            "This booking has been cancelled. Please create a new booking."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # PAYMENT SUCCESS BUT BOOKING NOT CONFIRMED
    # --------------------------------------------------------

    if (
        payment.status == "success"
        and booking.status != "confirmed"
    ):
        messages.error(
            request,
            "This payment cannot be processed because the booking is not confirmed."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # RESET FAILED PAYMENT IF BOOKING IS STILL PENDING
    # --------------------------------------------------------

    if (
        payment.status == "failed"
        and booking.status == "pending"
    ):
        payment.status = "pending"
        payment.transaction_id = None
        payment.razorpay_order_id = None

        payment.save(
            update_fields=[
                "status",
                "transaction_id",
                "razorpay_order_id",
                "updated_at",
            ]
        )

    # --------------------------------------------------------
    # PAYMENT AMOUNT VALIDATION
    # --------------------------------------------------------

    if payment.amount != booking.total_amount:

        payment.status = "failed"

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        booking.status = "cancelled"

        booking.save(
            update_fields=[
                "status",
            ]
        )

        messages.error(
            request,
            "Payment amount mismatch. Please start a new booking."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # CREATE RAZORPAY ORDER
    # --------------------------------------------------------

    if not payment.razorpay_order_id:

        amount_paise = int(
            round(
                float(
                    booking.total_amount
                ) * 100
            )
        )

        razorpay_order = (
            razorpay_client.order.create(
                {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": (
                        f"cinebook_booking_{booking.id}"
                    ),
                    "notes": {
                        "booking_id": str(
                            booking.id
                        ),
                        "movie": (
                            booking.showtime.movie.title
                        ),
                    },
                }
            )
        )

        payment.razorpay_order_id = (
            razorpay_order["id"]
        )

        payment.status = "pending"

        payment.save(
            update_fields=[
                "razorpay_order_id",
                "status",
                "updated_at",
            ]
        )

    return render(
        request,
        "movies/payment.html",
        {
            "booking": booking,
            "payment": payment,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "razorpay_order_id": payment.razorpay_order_id,
            "amount": int(
                round(
                    float(
                        payment.amount
                    ) * 100
                )
            ),
            "currency": "INR",
        },
    )


# ============================================================
# RAZORPAY PAYMENT SUCCESS VERIFICATION
# ============================================================

@login_required(login_url="login")
def verify_razorpay_payment(request):

    if request.method != "POST":
        return redirect(
            "my_bookings"
        )

    razorpay_payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    razorpay_order_id = request.POST.get(
        "razorpay_order_id"
    )

    razorpay_signature = request.POST.get(
        "razorpay_signature"
    )

    booking_id = request.POST.get(
        "booking_id"
    )

    if not all(
        [
            razorpay_payment_id,
            razorpay_order_id,
            razorpay_signature,
            booking_id,
        ]
    ):
        messages.error(
            request,
            "Payment verification data is incomplete."
        )

        return redirect(
            "my_bookings"
        )

    booking = get_object_or_404(
        Booking.objects.select_related(
            "showtime",
            "showtime__movie",
        ),
        id=booking_id,
        user=request.user,
    )

    payment = getattr(
        booking,
        "payment",
        None
    )

    if not payment:
        messages.error(
            request,
            "Payment record was not found."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # IDEMPOTENCY
    # --------------------------------------------------------

    if (
        payment.status == "success"
        and booking.status == "confirmed"
    ):
        request.session[
            "last_booking_id"
        ] = booking.id

        messages.success(
            request,
            "This booking has already been confirmed."
        )

        return redirect(
            "booking_confirmation",
            booking_id=booking.id
        )

    # --------------------------------------------------------
    # NEVER PROCESS CANCELLED BOOKING
    # --------------------------------------------------------

    if booking.status == "cancelled":
        messages.error(
            request,
            "This booking has already been cancelled."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # VERIFY ORDER ID
    # --------------------------------------------------------

    if payment.razorpay_order_id != razorpay_order_id:

        with transaction.atomic():

            payment.status = "failed"

            payment.transaction_id = (
                razorpay_payment_id
            )

            payment.save(
                update_fields=[
                    "status",
                    "transaction_id",
                    "updated_at",
                ]
            )

            booking.status = "cancelled"

            booking.save(
                update_fields=[
                    "status",
                ]
            )

        messages.error(
            request,
            "Payment order verification failed. The booking has been cancelled."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # DON'T PROCESS A KNOWN FAILED PAYMENT
    # --------------------------------------------------------

    if payment.status == "failed":

        messages.error(
            request,
            "This payment has already failed."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # RAZORPAY SIGNATURE VERIFICATION
    # --------------------------------------------------------

    verification_data = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    }

    try:

        razorpay_client.utility.verify_payment_signature(
            verification_data
        )

    except razorpay.errors.SignatureVerificationError:

        with transaction.atomic():

            payment.status = "failed"
            payment.transaction_id = (
                razorpay_payment_id
            )

            payment.save(
                update_fields=[
                    "status",
                    "transaction_id",
                    "updated_at",
                ]
            )

            booking.status = "cancelled"

            booking.save(
                update_fields=[
                    "status",
                ]
            )

        messages.error(
            request,
            "Payment verification failed. The booking has been cancelled."
        )

        return redirect(
            "my_bookings"
        )

    except Exception:

        messages.error(
            request,
            "An unexpected payment verification error occurred."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # PAYMENT SUCCESS
    # --------------------------------------------------------

    with transaction.atomic():

        booking.refresh_from_db()
        payment.refresh_from_db()

        if (
            payment.status == "success"
            and booking.status == "confirmed"
        ):
            request.session[
                "last_booking_id"
            ] = booking.id

            return redirect(
                "booking_confirmation",
                booking_id=booking.id
            )

        if booking.status == "cancelled":
            messages.error(
                request,
                "This booking has already been cancelled."
            )

            return redirect(
                "my_bookings"
            )

        payment.status = "success"
        payment.transaction_id = (
            razorpay_payment_id
        )

        payment.save(
            update_fields=[
                "status",
                "transaction_id",
                "updated_at",
            ]
        )

        booking.status = "confirmed"

        booking.save(
            update_fields=[
                "status",
            ]
        )

    # --------------------------------------------------------
    # BOOKING CONFIRMATION NOTIFICATION
    # --------------------------------------------------------

    Notification.objects.create(
        user=request.user,
        title="Booking Confirmed",
        message=(
            f"Your booking for "
            f"{booking.showtime.movie.title} "
            f"(Booking #{booking.id}) "
            f"has been confirmed successfully."
        ),
        notification_type="booking_confirmed",
        booking=booking,
        movie=booking.showtime.movie,
    )

    request.session[
        "last_booking_id"
    ] = booking.id

    messages.success(
        request,
        "Payment successful! Your booking has been confirmed."
    )

    return redirect(
        "booking_confirmation",
        booking_id=booking.id
    )


# ============================================================
# RAZORPAY PAYMENT FAILURE
# ============================================================

@login_required(login_url="login")
def razorpay_payment_failed(request):

    if request.method != "POST":
        return redirect(
            "my_bookings"
        )

    booking_id = request.POST.get(
        "booking_id"
    )

    razorpay_order_id = request.POST.get(
        "razorpay_order_id"
    )

    razorpay_payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    error_description = request.POST.get(
        "error_description",
        "Payment was cancelled or failed."
    )

    if not booking_id:
        messages.error(
            request,
            "Booking information was not provided."
        )

        return redirect(
            "my_bookings"
        )

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user,
    )

    payment = getattr(
        booking,
        "payment",
        None
    )

    if not payment:
        messages.error(
            request,
            "Payment record was not found."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # NEVER OVERWRITE A SUCCESSFUL PAYMENT
    # --------------------------------------------------------

    if payment.status == "success":

        messages.error(
            request,
            "This payment was already successful."
        )

        return redirect(
            "booking_confirmation",
            booking_id=booking.id
        )

    # --------------------------------------------------------
    # VERIFY ORDER ID
    # --------------------------------------------------------

    if (
        razorpay_order_id
        and payment.razorpay_order_id
        != razorpay_order_id
    ):

        messages.error(
            request,
            "Payment order mismatch."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # IDEMPOTENCY
    # --------------------------------------------------------

    if (
        payment.status == "failed"
        and booking.status == "cancelled"
    ):
        messages.error(
            request,
            f"Payment failed: {error_description}"
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # MARK PAYMENT + BOOKING AS FAILED/CANCELLED
    # --------------------------------------------------------

    with transaction.atomic():

        payment.status = "failed"

        if razorpay_payment_id:
            payment.transaction_id = (
                razorpay_payment_id
            )

        payment.save(
            update_fields=[
                "status",
                "transaction_id",
                "updated_at",
            ]
        )

        booking.status = "cancelled"

        booking.save(
            update_fields=[
                "status",
            ]
        )

    # --------------------------------------------------------
    # PAYMENT FAILURE NOTIFICATION
    # --------------------------------------------------------

    Notification.objects.create(
        user=request.user,
        title="Payment Failed",
        message=(
            f"Payment for your booking "
            f"(Booking #{booking.id}) failed or was cancelled. "
            f"Please create a new booking to try again."
        ),
        notification_type="booking_cancelled",
        booking=booking,
        movie=booking.showtime.movie,
    )

    messages.error(
        request,
        f"Payment failed: {error_description}"
    )

    return redirect(
        "my_bookings"
    )


# ============================================================
# BOOKING CONFIRMATION / DIGITAL TICKET
# ============================================================

@login_required(login_url="login")
def booking_confirmation(request, booking_id):

    booking = get_object_or_404(
        Booking.objects
        .select_related(
            "showtime",
            "showtime__movie",
            "showtime__cinema",
            "showtime__cinema__city",
        )
        .prefetch_related("seats"),
        id=booking_id,
        user=request.user,
    )

    # --------------------------------------------------------
    # CANCELLED BOOKING
    # --------------------------------------------------------

    if booking.status == "cancelled":

        messages.error(
            request,
            "This booking was cancelled. A digital ticket is not available."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # ONLY CONFIRMED BOOKINGS MAY HAVE A DIGITAL TICKET
    # --------------------------------------------------------

    if booking.status != "confirmed":

        messages.error(
            request,
            "This booking has not been confirmed yet."
        )

        return redirect(
            "my_bookings"
        )

    payment = getattr(
        booking,
        "payment",
        None
    )

    # --------------------------------------------------------
    # PAYMENT RECORD CHECK
    # --------------------------------------------------------

    if not payment:

        messages.error(
            request,
            "Payment information was not found."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # PAYMENT MUST BE SUCCESSFUL
    # --------------------------------------------------------

    if payment.status != "success":

        messages.error(
            request,
            "Payment has not been completed."
        )

        return redirect(
            "my_bookings"
        )

    # --------------------------------------------------------
    # DIGITAL TICKET
    # --------------------------------------------------------

    return render(
        request,
        "movies/booking_confirmation.html",
        {
            "booking": booking,
            "payment": payment,
        },
    )


# ============================================================
# MY BOOKINGS
# ============================================================

@login_required(login_url="login")
def my_bookings(request):

    bookings = (
        Booking.objects
        .filter(user=request.user)
        .select_related(
            "showtime",
            "showtime__movie",
            "showtime__cinema",
            "showtime__cinema__city",
        )
        .prefetch_related("seats")
        .order_by("-booking_time")
    )

    return render(
        request,
        "movies/my_bookings.html",
        {
            "bookings": bookings,
            "now": timezone.now(),
        },
    )


# ============================================================
# CANCEL BOOKING
# ============================================================

@login_required(login_url="login")
def cancel_booking(request, booking_id):

    booking = get_object_or_404(
        Booking.objects.select_related(
            "showtime",
            "showtime__movie",
        ),
        id=booking_id,
        user=request.user,
    )

    if request.method != "POST":
        return redirect(
            "my_bookings"
        )

    if booking.status == "cancelled":

        messages.error(
            request,
            "This booking is already cancelled."
        )

        return redirect(
            "my_bookings"
        )

    if booking.showtime.starts_at <= timezone.now():

        messages.error(
            request,
            "This booking cannot be cancelled because the show has already started."
        )

        return redirect(
            "my_bookings"
        )

    booking.status = "cancelled"

    booking.save(
        update_fields=[
            "status",
        ]
    )

    Notification.objects.create(
        user=request.user,
        title="Booking Cancelled",
        message=(
            f"Your booking for "
            f"{booking.showtime.movie.title} "
            f"(Booking #{booking.id}) "
            f"has been cancelled."
        ),
        notification_type="booking_cancelled",
        booking=booking,
        movie=booking.showtime.movie,
    )

    messages.success(
        request,
        "Booking cancelled successfully."
    )

    return redirect(
        "my_bookings"
    )


# ============================================================
# PROFILE
# ============================================================

@login_required(login_url="login")
def profile(request):

    recent_bookings = (
        Booking.objects
        .filter(user=request.user)
        .select_related(
            "showtime",
            "showtime__movie",
        )
        .order_by("-booking_time")[:5]
    )

    total_bookings = Booking.objects.filter(
        user=request.user
    ).count()

    total_watchlist = Watchlist.objects.filter(
        user=request.user
    ).count()

    total_reviews = MovieReview.objects.filter(
        user=request.user
    ).count()

    total_spent = (
        Payment.objects
        .filter(
            booking__user=request.user,
            booking__status="confirmed",
            status="success",
        )
        .aggregate(
            total=Sum("amount")
        )
        .get("total")
        or 0
    )

    return render(
        request,
        "movies/profile.html",
        {
            "recent_bookings": recent_bookings,
            "total_bookings": total_bookings,
            "total_watchlist": total_watchlist,
            "total_reviews": total_reviews,
            "total_spent": total_spent,
        },
    )


# ============================================================
# EDIT PROFILE
# ============================================================

@login_required(login_url="login")
def edit_profile(request):

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        current_password = request.POST.get(
            "current_password",
            ""
        )

        new_password = request.POST.get(
            "new_password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if not username or not email:

            messages.error(
                request,
                "Username and email are required."
            )

            return render(
                request,
                "movies/edit_profile.html"
            )

        username_exists = (
            User.objects
            .filter(username=username)
            .exclude(id=request.user.id)
            .exists()
        )

        if username_exists:

            messages.error(
                request,
                "That username is already taken."
            )

            return render(
                request,
                "movies/edit_profile.html"
            )

        email_exists = (
            User.objects
            .filter(email=email)
            .exclude(id=request.user.id)
            .exists()
        )

        if email_exists:

            messages.error(
                request,
                "That email is already registered."
            )

            return render(
                request,
                "movies/edit_profile.html"
            )

        changing_password = any(
            [
                current_password,
                new_password,
                confirm_password,
            ]
        )

        if changing_password:

            if not current_password:
                messages.error(
                    request,
                    "Enter your current password."
                )

                return render(
                    request,
                    "movies/edit_profile.html"
                )

            if not request.user.check_password(
                current_password
            ):

                messages.error(
                    request,
                    "Current password is incorrect."
                )

                return render(
                    request,
                    "movies/edit_profile.html"
                )

            if len(new_password) < 8:

                messages.error(
                    request,
                    "New password must contain at least 8 characters."
                )

                return render(
                    request,
                    "movies/edit_profile.html"
                )

            if new_password != confirm_password:

                messages.error(
                    request,
                    "New passwords do not match."
                )

                return render(
                    request,
                    "movies/edit_profile.html"
                )

        request.user.username = username
        request.user.email = email

        if changing_password:
            request.user.set_password(
                new_password
            )

        request.user.save()

        if changing_password:
            login(
                request,
                request.user,
                backend="django.contrib.auth.backends.ModelBackend",
            )

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect(
            "profile"
        )

    return render(
        request,
        "movies/edit_profile.html"
    )


# ============================================================
# AI RECOMMENDATIONS
# ============================================================

@login_required(login_url="login")
def ai_recommend(request):

    movies = (
        Movie.objects
        .filter(is_now_showing=True)
        .order_by("-rating")[:20]
    )

    movie_data = []

    for movie in movies:
        movie_data.append(
            {
                "title": movie.title,
                "genre": movie.genre,
                "language": movie.language,
                "rating": float(
                    movie.rating or 0
                ),
                "description": movie.description,
            }
        )

    recommendations = []

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

    if api_key:

        try:

            client = Groq(
                api_key=api_key
            )

            prompt = f"""
You are CineBookAI's movie recommendation assistant.

Only recommend movies from the database below.

Do not invent movie titles.

Recommend up to 5 movies.

For every recommendation provide:
- title
- genre
- rating
- short reason

Database movies:

{movie_data}
"""

            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.7,
            )

            recommendations = (
                response
                .choices[0]
                .message
                .content
            )

        except Exception as exc:

            recommendations = (
                f"AI recommendation error: {exc}"
            )

    else:

        recommendations = (
            "GROQ_API_KEY is not configured."
        )

    return render(
        request,
        "movies/ai_recommend.html",
        {
            "recommendations": recommendations,
            "movies": movies,
            "recommended_movies": movies[:5],
        },
    )


# ============================================================
# AI MOVIE ASSISTANT
# ============================================================

@login_required(login_url="login")
def ai_chat(request):

    answer = ""

    if request.method == "POST":

        user_message = request.POST.get(
            "message",
            ""
        ).strip()

        movies = (
            Movie.objects
            .filter(is_now_showing=True)
            .order_by("-rating")[:30]
        )

        movie_data = []

        for movie in movies:

            movie_data.append(
                {
                    "title": movie.title,
                    "genre": movie.genre,
                    "language": movie.language,
                    "rating": float(
                        movie.rating or 0
                    ),
                    "description": movie.description,
                }
            )

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not user_message:

            answer = (
                "Please enter a message."
            )

        elif not api_key:

            answer = (
                "GROQ_API_KEY is not configured."
            )

        else:

            try:

                client = Groq(
                    api_key=api_key
                )

                prompt = f"""
You are CineBookAI's AI Movie Assistant.

User message:
{user_message}

Available movies:
{movie_data}

Rules:
1. Only discuss movie-related topics.
2. Only recommend movies from the available database.
3. Never invent movies.
4. Never claim that a booking has been completed.
5. Be helpful, concise and friendly.
6. If the user asks about booking, guide them to the appropriate movie/showtime/booking page.
"""

                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    temperature=0.7,
                )

                answer = (
                    response
                    .choices[0]
                    .message
                    .content
                )

            except Exception as exc:

                answer = (
                    f"AI assistant error: {exc}"
                )

    return render(
        request,
        "movies/ai_chat.html",
        {
            "answer": answer,
        },
    )


# ============================================================
# SIGN UP
# ============================================================

def signup_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if not username or not email or not password:

            messages.error(
                request,
                "Please fill in all required fields."
            )

            return render(
                request,
                "movies/signup.html"
            )

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return render(
                request,
                "movies/signup.html"
            )

        if User.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                "Email is already registered."
            )

            return render(
                request,
                "movies/signup.html"
            )

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return render(
                request,
                "movies/signup.html"
            )

        if len(password) < 8:

            messages.error(
                request,
                "Password must contain at least 8 characters."
            )

            return render(
                request,
                "movies/signup.html"
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        login(
            request,
            user
        )

        messages.success(
            request,
            "Account created successfully. Welcome to CineBookAI!"
        )

        return redirect(
            "home"
        )

    return render(
        request,
        "movies/signup.html"
    )


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:

            login(
                request,
                user
            )

            messages.success(
                request,
                "Welcome back!"
            )

            next_url = request.GET.get(
                "next"
            )

            if next_url:
                return redirect(
                    next_url
                )

            return redirect(
                "home"
            )

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "movies/login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@login_required(login_url="login")
def logout_view(request):

    logout(
        request
    )

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect(
        "home"
    )


# ============================================================
# ADMIN ACCESS
# ============================================================

def admin_user_required(user):
    return (
        user.is_authenticated
        and user.is_staff
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@user_passes_test(
    admin_user_required,
    login_url="login"
)
def admin_dashboard(request):

    total_movies = Movie.objects.count()

    total_cinemas = Cinema.objects.count()

    total_showtimes = ShowTime.objects.count()

    total_bookings = Booking.objects.count()

    successful_payments = Payment.objects.filter(
        status="success"
    )

    successful_payment_count = (
        successful_payments.count()
    )

    pending_payment_count = Payment.objects.filter(
        status="pending"
    ).count()

    failed_payment_count = Payment.objects.filter(
        status="failed"
    ).count()

    total_revenue = (
        successful_payments
        .aggregate(
            total=Sum("amount")
        )
        .get("total")
        or 0
    )

    confirmed_bookings = Booking.objects.filter(
        status="confirmed"
    ).count()

    cancelled_bookings = Booking.objects.filter(
        status="cancelled"
    ).count()

    recent_bookings = (
        Booking.objects
        .select_related(
            "user",
            "showtime",
            "showtime__movie",
            "showtime__cinema",
        )
        .prefetch_related("seats")
        .order_by("-booking_time")[:8]
    )

    return render(
        request,
        "movies/admin_dashboard.html",
        {
            "total_movies": total_movies,
            "total_cinemas": total_cinemas,
            "total_showtimes": total_showtimes,
            "total_bookings": total_bookings,
            "successful_payment_count": successful_payment_count,
            "pending_payment_count": pending_payment_count,
            "failed_payment_count": failed_payment_count,
            "total_revenue": total_revenue,
            "confirmed_bookings": confirmed_bookings,
            "cancelled_bookings": cancelled_bookings,
            "recent_bookings": recent_bookings,
        },
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

@login_required(login_url="login")
def notifications(request):

    notification_list = (
        Notification.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).count()

    return render(
        request,
        "movies/notifications.html",
        {
            "notifications": notification_list,
            "unread_count": unread_count,
        },
    )


@login_required(login_url="login")
def mark_notification_read(
    request,
    notification_id
):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user,
    )

    notification.is_read = True

    notification.save(
        update_fields=[
            "is_read",
        ]
    )

    return redirect(
        "notifications"
    )


@login_required(login_url="login")
def mark_all_notifications_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).update(
        is_read=True
    )

    return redirect(
        "notifications"
    )