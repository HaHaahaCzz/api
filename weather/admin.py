from django.contrib import admin
from .models import City, WeatherRecord

admin.site.register(City)
admin.site.register(WeatherRecord)