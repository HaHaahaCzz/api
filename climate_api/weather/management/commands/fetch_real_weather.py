from django.core.management.base import BaseCommand

from weather.openweather import get_api_key, sync_all_cities


class Command(BaseCommand):
    help = "Fetch live weather from OpenWeatherMap for all cities and save today's records"

    def handle(self, *args, **kwargs):
        api_key = get_api_key()
        if not api_key:
            self.stdout.write(self.style.ERROR("OPENWEATHER_API_KEY not set. Add it to climate_api/.env"))
            return

        self.stdout.write(f"API key loaded: {api_key[:8]}...")
        self.stdout.write("")

        success = 0
        for city, record, err in sync_all_cities():
            if err:
                self.stdout.write(self.style.ERROR(f"{city.name}: {err}"))
                if "401" in err or "Invalid" in err:
                    return
                continue
            success += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"{city.name}: saved id={record.pk} — {record.temperature}°C, "
                    f"humidity {record.humidity}%, PM2.5 {record.pm25}"
                )
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Done. Saved {success} city record(s)."))
