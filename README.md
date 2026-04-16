# WEB_API — City Climate Data REST API

A small **Django 4.2** + **Django REST Framework** backend for CRUD on cities and weather records, plus analytics for temperature trends and air-quality anomalies. Uses **SQLite** by default.

## Features

- **City**: name, country, latitude, longitude
- **WeatherRecord**: per city and date — temperature, humidity, PM2.5, wind speed (unique on city + date)
- **Analytics**: monthly temperature trend (with average PM2.5), days where PM2.5 exceeds a threshold

## Tech stack

| Component | Role |
|-----------|------|
| Python 3 | Runtime |
| Django 4.2 | Web framework |
| Django REST Framework | REST API |
| SQLite | Default database (`climate_api/db.sqlite3`) |

Also used: `requests`, `python-dotenv`, `urllib3` (see Installation).

## Project layout

```
WEB_API/
├── climate_api/              # Django project root (run manage.py here)
│   ├── climate_api/          # Project settings and URL config
│   ├── weather/              # App: models, views, serializers, commands
│   ├── manage.py
│   └── db.sqlite3            # Created after migrate
└── README.md
```

## Requirements

- Python 3.10+ (match your local virtual environment if you use one)

## Installation and run

1. **Go to the project directory**

   ```bash
   cd climate_api
   ```

2. **Create and activate a virtual environment (optional)**

   ```bash
   python -m venv .venv
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies** (if you do not have a `requirements.txt` yet, install manually)

   ```bash
   pip install "Django>=4.2,<5" djangorestframework requests python-dotenv urllib3
   ```

4. **Apply migrations**

   ```bash
   python manage.py migrate
   ```

5. **Start the dev server**

   ```bash
   python manage.py runserver
   ```

   Default URL: <http://127.0.0.1:8000/>

6. **Admin site** (create a superuser first)

   ```bash
   python manage.py createsuperuser
   ```

   Open: <http://127.0.0.1:8000/admin/>

## Environment variables (live weather)

The `fetch_real_weather` management command pulls current weather from [OpenWeatherMap](https://openweathermap.org/api). Add a `.env` file under `climate_api`:

```env
OPENWEATHER_API_KEY=your_api_key_here
```

Do not commit a `.env` file that contains real secrets.

## API

All app routes are under **`/api/`**.

### Cities

| Method | Path | Description |
|--------|------|-------------|
| GET / POST | `/api/cities/` | List / create |
| GET / PUT / PATCH / DELETE | `/api/cities/<id>/` | Retrieve / update / delete |

### Weather records

| Method | Path | Description |
|--------|------|-------------|
| GET / POST | `/api/weather/` | List / create |
| GET / PUT / PATCH / DELETE | `/api/weather/<id>/` | Retrieve / update / delete |

### Analytics

| Method | Path | Query params | Description |
|--------|------|----------------|-------------|
| GET | `/api/analytics/temperature-trend/` | `city_id` (required) | Monthly aggregates: avg/max/min temperature, avg PM2.5 |
| GET | `/api/analytics/air-quality-anomaly/` | `city_id` (required), `threshold` (optional, default 75) | Days above PM2.5 threshold and detail rows |

Examples:

```http
GET http://127.0.0.1:8000/api/analytics/temperature-trend/?city_id=1
GET http://127.0.0.1:8000/api/analytics/air-quality-anomaly/?city_id=1&threshold=75
```

## Management commands

Run from the `climate_api` directory:

| Command | What it does |
|---------|----------------|
| `python manage.py import_weather` | Generates random test data for roughly the **last 30 days** for existing cities (create cities via Admin or API first) |
| `python manage.py fetch_real_weather` | Uses `OPENWEATHER_API_KEY` from `.env` to fetch **today’s** live weather per city and upsert into the database |

## Development and deployment notes

- In `climate_api/climate_api/settings.py`, `DEBUG = True` and the default `SECRET_KEY` are for local development only. Before production, turn off debug, set a new secret, and configure `ALLOWED_HOSTS`.
- `fetch_real_weather` disables HTTPS certificate verification (`verify=False`) for certain network setups; in production you should enable verification and handle errors and rate limits appropriately.

## License

Add a license file in the repository if this project is shared publicly.
