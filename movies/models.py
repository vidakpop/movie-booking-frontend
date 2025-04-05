from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
import json

class Cinema(models.Model):
    name = models.CharField(max_length=300)
    location = models.CharField(max_length=300)
    capacity = models.IntegerField()
    seating_chart = JSONField(default=list)  # Store seat layout as 2D array

    def __str__(self):
        return self.name  

    def initialize_seats(self, rows=5, cols=10):
        """Initialize a default seating chart"""
        if not self.seating_chart:
            self.seating_chart = [['O' for _ in range(cols)] for _ in range(rows)]  # 'O' means open seat
            self.capacity = rows * cols  # Update capacity to match seats
            self.save()
# Automatically initialize seating chart when a new cinema is created
@receiver(post_save, sender=Cinema)
def create_seating_chart(sender, instance, created, **kwargs):
    if created:
        instance.initialize_seats()
    
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
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('booked', 'Booked'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE)
    seats = JSONField(default=list)  # Stores booked seats as [(row, col), (row, col)]
    booked_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user.username} - {self.movie.title} at {self.cinema.name}"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE,related_name='transactions')