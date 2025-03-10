from django.db import models

class Cinema(models.Model):
    name=models.CharField(max_length=300)
    location=models.CharField(max_length=300)
    capacity=models.IntegerField()
    def __str__(self):
        return self.name
    
class Movie(models.Model):
    title=models.CharField(max_length=300)
    description=models.TextField()
    genre=models.CharField(max_length=100)
    release_date=models.DateField()
    duration=models.IntegerField(help_text='Duration in minutes')
    poster=models.ImageField(upload_to='posters/',null=True, blank=True)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    cinemas=models.ManyToManyField(Cinema,related_name='movies')
    def __str__(self):
        return self.title

class Booking(models.Model):
    user_name=models.CharField(max_length=300)
    user_email=models.EmailField()
    movie=models.ForeignKey(Movie,on_delete=models.CASCADE)
    cinema=models.ForeignKey(Cinema,on_delete=models.CASCADE)
    seat_number=models.CharField(max_length=10)
    booking_date=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} - {self.movie.title} at {self.cinema.name}"