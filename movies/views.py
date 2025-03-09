from django.shortcuts import render
from rest_framework import generics,status
from . models import Movie, Cinema, Booking
from .serializer import CinemaSerializer, MovieSerializer, BookingSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class SignUpview(APIView):
    permission_classes=[AllowAny]

    def post(self, request):
        username=request.data.get('username')
        email=request.data.get('email')
        password=request.data.get('password')

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        user=User.objects.create_user(username=username, email=email,password=password)
        refresh=RefreshToken.for_user(user)

        return Response({
            "username": user.username,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh)
        })



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