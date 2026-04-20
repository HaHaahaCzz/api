from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from .models import City, WeatherRecord


class CityAPITests(APITestCase):
    def setUp(self):
        self.city = City.objects.create(
            name="TestCity",
            country="CN",
            latitude=39.9042,
            longitude=116.4074,
        )
        # 创建认证用户 + Token
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)

    # ── 读取：公开，无需认证 ──

    def test_list_cities(self):
        url = reverse("city-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "TestCity")

    def test_retrieve_city(self):
        url = reverse("city-detail", args=[self.city.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.city.pk)

    # ── 写入：需要 Token 认证 ──

    def test_create_city_unauthenticated(self):
        """未认证用户创建城市应返回 401"""
        url = reverse("city-list")
        payload = {
            "name": "Shanghai",
            "country": "CN",
            "latitude": 31.2304,
            "longitude": 121.4737,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_city(self):
        """认证用户创建城市应返回 201"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        url = reverse("city-list")
        payload = {
            "name": "Shanghai",
            "country": "CN",
            "latitude": 31.2304,
            "longitude": 121.4737,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(City.objects.count(), 2)
        self.assertEqual(response.data["name"], "Shanghai")

    def test_update_city_patch(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        url = reverse("city-detail", args=[self.city.pk])
        response = self.client.patch(url, {"name": "Beijing"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.city.refresh_from_db()
        self.assertEqual(self.city.name, "Beijing")

    def test_delete_city(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        url = reverse("city-detail", args=[self.city.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(City.objects.count(), 0)


class WeatherRecordAPITests(APITestCase):
    def setUp(self):
        self.city = City.objects.create(
            name="TestCity",
            country="CN",
            latitude=39.9042,
            longitude=116.4074,
        )
        self.record = WeatherRecord.objects.create(
            city=self.city,
            date=date(2024, 6, 15),
            temperature=22.5,
            humidity=60,
            pm25=45.0,
            wind_speed=3.2,
        )
        # 创建认证用户 + Token
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)

    # ── 读取：公开 ──

    def test_list_weather_records(self):
        url = reverse("weather-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_weather_record(self):
        url = reverse("weather-detail", args=[self.record.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.record.pk)

    # ── 写入：需要 Token ──

    def test_create_weather_record_unauthenticated(self):
        """未认证用户创建天气记录应返回 401"""
        url = reverse("weather-list")
        payload = {
            "city": self.city.pk,
            "date": "2024-06-16",
            "temperature": 25.0,
            "humidity": 55,
            "pm25": 30.0,
            "wind_speed": 2.0,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_weather_record(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        url = reverse("weather-list")
        payload = {
            "city": self.city.pk,
            "date": "2024-06-16",
            "temperature": 25.0,
            "humidity": 55,
            "pm25": 30.0,
            "wind_speed": 2.0,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WeatherRecord.objects.count(), 2)

    def test_update_weather_record(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        url = reverse("weather-detail", args=[self.record.pk])
        response = self.client.patch(url, {"temperature": 20.0}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.record.refresh_from_db()
        self.assertEqual(self.record.temperature, 20.0)

    def test_delete_weather_record(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        url = reverse("weather-detail", args=[self.record.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(WeatherRecord.objects.count(), 0)


class AnalyticsAPITests(APITestCase):
    def setUp(self):
        self.city = City.objects.create(
            name="TrendCity",
            country="CN",
            latitude=30.0,
            longitude=120.0,
        )
        WeatherRecord.objects.create(
            city=self.city,
            date=date(2024, 3, 10),
            temperature=10.0,
            humidity=50,
            pm25=40.0,
            wind_speed=1.0,
        )
        WeatherRecord.objects.create(
            city=self.city,
            date=date(2024, 3, 20),
            temperature=12.0,
            humidity=52,
            pm25=42.0,
            wind_speed=1.5,
        )

    def test_temperature_trend_missing_city_id(self):
        url = reverse("temp-trend")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_temperature_trend_no_data(self):
        empty_city = City.objects.create(
            name="EmptyCity",
            country="CN",
            latitude=31.0,
            longitude=121.0,
        )
        url = reverse("temp-trend")
        response = self.client.get(url, {"city_id": empty_city.pk})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_temperature_trend_success(self):
        url = reverse("temp-trend")
        response = self.client.get(url, {"city_id": self.city.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row["year"], 2024)
        self.assertEqual(row["month"], 3)
        self.assertEqual(row["avg_temperature"], 11.0)

    def test_air_quality_missing_city_id(self):
        url = reverse("aq-anomaly")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_air_quality_anomaly_success(self):
        WeatherRecord.objects.create(
            city=self.city,
            date=date(2024, 4, 1),
            temperature=20.0,
            humidity=60,
            pm25=90.0,
            wind_speed=2.0,
        )
        url = reverse("aq-anomaly")
        response = self.client.get(
            url,
            {"city_id": self.city.pk, "threshold": 75},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city_id"], str(self.city.pk))
        self.assertEqual(response.data["threshold"], 75)
        self.assertEqual(response.data["anomaly_count"], 1)


class LiveWeatherAPITests(APITestCase):
    def setUp(self):
        self.city = City.objects.create(
            name="LiveCity",
            country="CN",
            latitude=39.9,
            longitude=116.4,
        )
        self.record = WeatherRecord.objects.create(
            city=self.city,
            date=date(2024, 7, 1),
            temperature=28.0,
            humidity=70,
            pm25=55.0,
            wind_speed=4.0,
        )

    def test_live_missing_city_id(self):
        url = reverse("weather-live")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_live_city_not_found(self):
        url = reverse("weather-live")
        response = self.client.get(url, {"city_id": 99999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("weather.views.fetch_and_save_city")
    def test_live_upstream_error(self, mock_fetch):
        mock_fetch.return_value = (None, "OPENWEATHER_API_KEY is not configured.")
        url = reverse("weather-live")
        response = self.client.get(url, {"city_id": self.city.pk})
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", response.data)

    @patch("weather.views.fetch_and_save_city")
    def test_live_success(self, mock_fetch):
        mock_fetch.return_value = (self.record, None)
        url = reverse("weather-live")
        response = self.client.get(url, {"city_id": self.city.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source"], "openweathermap")
        self.assertEqual(response.data["id"], self.record.pk)
