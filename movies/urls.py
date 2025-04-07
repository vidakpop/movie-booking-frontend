from django.urls import path
from .views import (
    SeatAvailabilityView,
    MovieListCreateView,
    MovieDetailView,
    CinemaListCreateView,
    BookingListCreateView,
    initiate_payment,
    stk_status_view,
    release_seats,
    update_payment_status
)

urlpatterns = [
    # Seat availability
    path("cinemas/<int:cinema_id>/seats/", SeatAvailabilityView.as_view(), name="seat-availability"),

    # Movies
    path("movies/", MovieListCreateView.as_view(), name="movie-list-create"),
    path("movies/<int:pk>/", MovieDetailView.as_view(), name="movie-detail"),

    # Cinemas
    path("cinemas/", CinemaListCreateView.as_view(), name="cinema-list-create"),

    # Bookings
    path("bookings/", BookingListCreateView.as_view(), name="booking-list-create"),

    # M-Pesa STK push initiate
    path("payment/initiate/", initiate_payment, name="initiate-payment"),

    # STK push status
    path("payment/status/", stk_status_view, name="stk-status"),

    # Release seats
    path("release-seats/", release_seats, name="release-seats"),

    # Update payment status
    path("update-payment/", update_payment_status, name="update-payment-status"),
]
