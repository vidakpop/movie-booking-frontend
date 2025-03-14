from django.shortcuts import get_object_or_404
from rest_framework import generics,status
from . models import Movie, Cinema, Booking
from .serializer import CinemaSerializer, MovieSerializer, BookingSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction

class SeatAvailabilityView(APIView):
    #RETURNS seats availabity for cinema
    def get(self,request,cinema_id):
        cinema=get_object_or_404(Cinema,id=cinema_id)
        return Response({"seating_chart": cinema.seating_chart}, status=status.HTTP_200_OK)

    
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
    serializer_class=CinemaSerializer
    def get_queryset(self):
        queryset=Cinema.objects.all()
        movie_id=self.request.query_params.get('movie_id')

        if movie_id:
            queryset=queryset.filter(movies__id=movie_id)
        return queryset

#list and create bookings
class BookingListCreateView(APIView):
    permission_classes=[IsAuthenticated]  

    def get(self,request):
        bookings=Booking.objects.filter(user=request.user)
        serializer=BookingSerializer(bookings,many=True)
        return Response(serializer.data)

    @transaction.atomic  
    def post(self,request):
        #new booking with seat selection
        user=request.user
        movie_id=request.data.get('movie_id')
        cinema_id=request.data.get('cinema_id')
        selected_seats=request.data.get('seats',[])

        """try:
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
            return Response({"message":"Cinema not found"},status=status.HTTP_404_NOT_FOUND)"
            """
        if not selected_seats:
            return Response({"message": "No seats selected"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            movie = get_object_or_404(Movie, id=movie_id)
            cinema = get_object_or_404(Cinema, id=cinema_id)

            # Lock cinema to prevent race conditions
            with transaction.atomic():
                cinema.refresh_from_db()

                # Check seat availability
                for row, col in selected_seats:
                    if cinema.seating_chart[row][col] == 'X':
                        return Response({"message": f"Seat {row},{col} is already booked"}, status=status.HTTP_400_BAD_REQUEST)

                # Mark seats as booked
                for row, col in selected_seats:
                    cinema.seating_chart[row][col] = 'X'
                
                cinema.save()

                # Save booking
                booking = Booking.objects.create(user=user, movie=movie, cinema=cinema, seats=selected_seats)

                return Response({"message": "Booking successful", "booked_seats": selected_seats}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
