from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import views

urlpatterns = [
    # ── 认证 ──
    path('api-token-auth/', obtain_auth_token, name='api-token-auth'),

    # ── Cities ──
    path('cities/', views.CityListCreateView.as_view(), name='city-list'),
    path('cities/<int:pk>/', views.CityRetrieveUpdateDestroyView.as_view(), name='city-detail'),

    # ── Weather ──
    path('weather/', views.WeatherRecordListView.as_view(), name='weather-list'),
    path('weather/live/', views.LiveWeatherView.as_view(), name='weather-live'),
    path('weather/<int:pk>/', views.WeatherRecordDetailView.as_view(), name='weather-detail'),

    # ── Analytics ──
    path('analytics/temperature-trend/', views.CityTemperatureTrendView.as_view(), name='temp-trend'),
    path('analytics/air-quality-anomaly/', views.AirQualityAnomalyView.as_view(), name='aq-anomaly'),
]