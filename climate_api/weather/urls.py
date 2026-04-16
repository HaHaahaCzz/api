from django.urls import path
from . import views

urlpatterns = [
    path('cities/', views.CityListCreateView.as_view(), name='city-list'),
    path('cities/<int:pk>/', views.CityRetrieveUpdateDestroyView.as_view(), name='city-detail'),
    path('weather/', views.WeatherRecordListView.as_view(), name='weather-list'),
    path('weather/<int:pk>/', views.WeatherRecordDetailView.as_view(), name='weather-detail'),

    path('analytics/temperature-trend/', views.CityTemperatureTrendView.as_view(), name='temp-trend'),
    path('analytics/air-quality-anomaly/', views.AirQualityAnomalyView.as_view(), name='aq-anomaly'),
]