from rest_framework import serializers
from .models import Movie, Cinema,  Booking

class CinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cinema
        fields = '__all__'
