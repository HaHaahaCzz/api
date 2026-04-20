"""
OpenWeatherMap integration: current weather + air pollution (PM2.5).
https://openweathermap.org/api
"""
from __future__ import annotations

import os
from typing import Optional

import requests
from django.conf import settings
from django.utils import timezone

from .models import City, WeatherRecord

CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
AIR_POLLUTION_URL = "https://api.openweathermap.org/data/2.5/air_pollution"


def _verify_ssl() -> bool:
    v = os.environ.get("OPENWEATHER_VERIFY_SSL", "true").lower()
    verify = v not in ("0", "false", "no")
    if not verify:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return verify


def get_api_key() -> str:
    key = getattr(settings, "OPENWEATHER_API_KEY", None) or ""
    if not key:
        key = os.environ.get("OPENWEATHER_API_KEY", "") or ""
    return key.strip()


def fetch_pm25(lat: float, lon: float, api_key: str) -> Optional[float]:
    """One Call Air Pollution API — returns µg/m³ PM2.5 or None if unavailable."""
    try:
        r = requests.get(
            AIR_POLLUTION_URL,
            params={"lat": lat, "lon": lon, "appid": api_key},
            timeout=15,
            verify=_verify_ssl(),
        )
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    data = r.json()
    comps = (data.get("list") or [{}])[0].get("components") or {}
    v = comps.get("pm2_5")
    return float(v) if v is not None else None


def fetch_and_save_city(city: City) -> tuple[Optional[WeatherRecord], Optional[str]]:
    """
    Fetch live weather for ``city`` from OpenWeatherMap and upsert today's row.
    Returns (WeatherRecord, None) on success, or (None, error_message).
    """
    api_key = get_api_key()
    if not api_key:
        return None, "OPENWEATHER_API_KEY is not configured. Set it in .env or environment."

    params = {
        "q": f"{city.name},{city.country}",
        "appid": api_key,
        "units": "metric",
    }
    try:
        r = requests.get(
            CURRENT_WEATHER_URL,
            params=params,
            timeout=15,
            verify=_verify_ssl(),
        )
    except requests.RequestException as e:
        return None, f"Network error: {e}"

    if r.status_code == 401:
        return None, "Invalid or missing OpenWeather API key (HTTP 401)."
    if r.status_code != 200:
        return None, f"OpenWeather API error: HTTP {r.status_code}"

    data = r.json()
    main = data.get("main") or {}
    wind = data.get("wind") or {}

    temp = main.get("temp")
    humidity = main.get("humidity")
    wind_speed = wind.get("speed", 0)
    if temp is None or humidity is None:
        return None, "Unexpected API response: missing temperature or humidity."

    pm25 = fetch_pm25(city.latitude, city.longitude, api_key)

    today = timezone.now().date()
    defaults = {
        "temperature": float(temp),
        "humidity": int(humidity),
        "wind_speed": float(wind_speed),
        "pm25": pm25,
    }
    record, _ = WeatherRecord.objects.update_or_create(
        city=city,
        date=today,
        defaults=defaults,
    )
    return record, None


def sync_all_cities():
    """Fetch and save live weather for every city. Yields (city, record|None, error|None)."""
    for city in City.objects.all():
        record, err = fetch_and_save_city(city)
        yield city, record, err
