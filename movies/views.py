from django.shortcuts import render
from rest_framework import generics,status
from . models import Movie, Cinema, Booking
from .serializer import CinemaSerializer, MovieSerializer, BookingSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


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
class BookingListCreateView(APIView):
    permission_classes=[IsAuthenticated]    
    def post(self,request):
        user=request.user
        movie_id=request.data.get('movie_id')
        cinema_id=request.data.get('cinema_id')
        seats=request.data.get('seats')

        try:
            movie=Movie.objects.get(id=movie_id)
            cinema=Cinema.objects.get(id=cinema_id)
            if cinema.capacity<seats:
                return Response({"message":"Not enough seats available"},status=status.HTTP_400_BAD_REQUEST)
            cinema.capacity-=seats
            cinema.save()
            booking=Booking(user=user,movie=movie,cinema=cinema,seats=seats)
            booking.save()
            return Response({"message":"Booking successful"},status=status.HTTP_201_CREATED)
        except Movie.DoesNotExist:
            return Response({"message":"Movie not found"},status=status.HTTP_404_NOT_FOUND)
        except Cinema.DoesNotExist:
            return Response({"message":"Cinema not found"},status=status.HTTP_404_NOT_FOUND)