from django.shortcuts import render
from rest_framework import generics
from . models import Movie, Cinema, Booking
from .serializer import CinemaSerializer, MovieSerializer, BookingSerializer

#List and create Movies
class MovieListCreateView(generics.ListCreateAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

#Retrieve, update and delete Movies
class MovieDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

#List and create Cinemas
class CinemaListCreateView(generics.ListCreateAPIView):
    queryset = Cinema.objects.all()
    serializer_class=CinemaSerializer

#list and create bookings
class BookingListCreateView(generics.ListCreateAPIView):
    queryset = Booking.objects.all()
    serializer_class=BookingSerializer