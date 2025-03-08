from django.db import models

class Cinema(models.Model):
    name=models.CharField(max_length=300)
    location=models.CharField(max_length=300)
    capacity=models.IntegerField()
    def __str__(self):
        return self.name
    

