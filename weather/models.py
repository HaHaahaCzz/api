from django.db import models

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=50)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.name}, {self.country}"

    class Meta:
        verbose_name_plural = "Cities"


class WeatherRecord(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='weather_records')
    date = models.DateField()
    temperature = models.FloatField()
    humidity = models.IntegerField()
    pm25 = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField()

    class Meta:
        unique_together = ['city', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.city.name} - {self.date}: {self.temperature}°C"
