from django.core.management.base import BaseCommand

from weather.openweather import get_api_key, sync_all_cities


class Command(BaseCommand):
    help = "Same as fetch_real_weather: import live data from OpenWeatherMap for all cities"

    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.WARNING(
                "import_weather now uses OpenWeatherMap (not random data). "
                "Prefer: python manage.py fetch_real_weather"
            )
        )
        self.stdout.write("")

        api_key = get_api_key()
        if not api_key:
            self.stdout.write(self.style.ERROR("OPENWEATHER_API_KEY not set. Add it to climate_api/.env"))
            return

        success = 0
        for city, record, err in sync_all_cities():
            if err:
                self.stdout.write(self.style.ERROR(f"{city.name}: {err}"))
                if "401" in err or "Invalid" in err:
                    return
                continue
            success += 1
            self.stdout.write(
                self.style.SUCCESS(f"{city.name}: {record.temperature}°C (record id={record.pk})")
            )

        self.stdout.write(self.style.SUCCESS(f"\nImported {success} live record(s)."))
