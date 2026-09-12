from django.urls import path

from . import views


urlpatterns = [

    # ========================================================
    # HOME
    # ========================================================

    path(
        "",
        views.home,
        name="home",
    ),


    # ========================================================
    # SEARCH
    # ========================================================

    path(
        "search/",
        views.search_movies,
        name="search_movies",
    ),


    # ========================================================
    # MOVIE DETAILS
    # ========================================================

    path(
        "movie/<int:movie_id>/",
        views.movie_detail,
        name="movie_detail",
    ),


    # ========================================================
    # WATCHLIST
    # ========================================================

    path(
        "movie/<int:movie_id>/watchlist/add/",
        views.add_to_watchlist,
        name="add_to_watchlist",
    ),

    path(
        "movie/<int:movie_id>/watchlist/remove/",
        views.remove_from_watchlist,
        name="remove_from_watchlist",
    ),

    path(
        "watchlist/",
        views.my_watchlist,
        name="my_watchlist",
    ),


    # ========================================================
    # MOVIE REVIEWS
    # ========================================================

    path(
        "movie/<int:movie_id>/review/",
        views.submit_movie_review,
        name="submit_movie_review",
    ),

    path(
        "movie/<int:movie_id>/review/delete/",
        views.delete_movie_review,
        name="delete_movie_review",
    ),


    # ========================================================
    # SEAT SELECTION
    # ========================================================

    path(
        "showtime/<int:showtime_id>/seats/",
        views.seat_selection,
        name="seat_selection",
    ),


    # ========================================================
    # BOOKING
    # ========================================================

    path(
        "showtime/<int:showtime_id>/booking/",
        views.booking_details,
        name="booking_details",
    ),


    # ========================================================
    # PAYMENT
    # ========================================================

    path(
        "booking/<int:booking_id>/payment/",
        views.payment_page,
        name="payment_page",
    ),

    path(
        "payment/verify/",
        views.verify_razorpay_payment,
        name="verify_razorpay_payment",
    ),

    # NEW: Razorpay payment failure handler
    path(
        "payment/failed/",
        views.razorpay_payment_failed,
        name="razorpay_payment_failed",
    ),


    # ========================================================
    # BOOKING CONFIRMATION
    # ========================================================

    path(
        "booking/<int:booking_id>/confirmation/",
        views.booking_confirmation,
        name="booking_confirmation",
    ),


    # ========================================================
    # MY BOOKINGS
    # ========================================================

    path(
        "my-bookings/",
        views.my_bookings,
        name="my_bookings",
    ),


    # ========================================================
    # CANCEL BOOKING
    # ========================================================

    path(
        "booking/<int:booking_id>/cancel/",
        views.cancel_booking,
        name="cancel_booking",
    ),


    # ========================================================
    # PROFILE
    # ========================================================

    path(
        "profile/",
        views.profile,
        name="profile",
    ),

    path(
        "profile/edit/",
        views.edit_profile,
        name="edit_profile",
    ),


    # ========================================================
    # AI FEATURES
    # ========================================================

    path(
        "ai-recommend/",
        views.ai_recommend,
        name="ai_recommend",
    ),

    path(
        "ai-chat/",
        views.ai_chat,
        name="ai_chat",
    ),


    # ========================================================
    # ADMIN DASHBOARD
    # ========================================================

    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),


    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    path(
        "notifications/",
        views.notifications,
        name="notifications",
    ),

    path(
        "notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),

    path(
        "notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),


    # ========================================================
    # AUTHENTICATION
    # ========================================================

    path(
        "signup/",
        views.signup_view,
        name="signup",
    ),

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),
]