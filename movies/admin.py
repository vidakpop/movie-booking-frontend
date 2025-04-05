from django.contrib import admin
from .models import Cinema, Movie, Booking, Transaction

admin.site.register(Cinema)
admin.site.register(Movie)
admin.site.register(Booking)
admin.site.register(Transaction)