from django.urls import path
from .views import MovieListCreateView, MovieDetailView, CinemaListCreateView, BookingListCreateView

urlpatterns = [
    path('movies/', MovieListCreateView.as_view(), name='movie-list-create'),
    path('movies/<int:pk>/', MovieDetailView.as_view(), name='movie-detail'),
    path('cinemas/', CinemaListCreateView.as_view(), name='cinema-list-create'),
    path('bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
]