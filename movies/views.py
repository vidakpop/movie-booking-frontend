from django.shortcuts import render
from rest_framework import generics
from, models import Movie, Cinema, Booking
from .serializer import CinemaSerializer, MovieSerializer, BookingSerializer

#List and create Movies
class MovieListCreateView(generics.ListCreateAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
