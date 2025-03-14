from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
import json

class Cinema(models.Model):
    name=models.CharField(max_length=300)
    location=models.CharField(max_length=300)
    capacity=models.IntegerField()
    seating_chart=JSONField(default=list) #store seat layout in 2d array
    def __str__(self):
        return self.name
    
    def initialize_seats(self,rows=5,cols=10):
        #initialize a default seating chart 

        if not self.seating_chart:
            self.seating_chart = [['O' for _ in range(cols)] for _ in range(rows)]
            self.capacity=rows*cols
            self.save()
    
class Movie(models.Model):
    title=models.CharField(max_length=300)
    description=models.TextField()
    genre=models.CharField(max_length=100)
    release_date=models.DateField()
    duration=models.IntegerField(help_text='Duration in minutes')
    poster=models.ImageField(upload_to='posters/',null=True, blank=True)
    price=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    cinemas=models.ManyToManyField(Cinema,related_name='movies')
    def __str__(self):
        return self.title

class Booking(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    movie=models.ForeignKey(Movie,on_delete=models.CASCADE)
    cinema=models.ForeignKey(Cinema,on_delete=models.CASCADE)
    seats=models.IntegerField(default=0)
    booked_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.movie.title} at {self.cinema.name}"