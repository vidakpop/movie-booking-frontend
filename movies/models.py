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
    cinemas=models.ManyToManyField(Cinema,related_name='movies')
    def __str__(self):
        return self.title

