import os
import ssl
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from weather.models import City, WeatherRecord
from dotenv import load_dotenv

# 禁用 SSL 验证（临时解决网络问题）
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


class Command(BaseCommand):
    help = '从 OpenWeatherMap 获取真实天气数据'

    def handle(self, *args, **kwargs):
        api_key = os.getenv('OPENWEATHER_API_KEY')

        # 调试：打印 API Key 前几位
        if api_key:
            self.stdout.write(f'🔑 API Key 已加载: {api_key[:8]}...')
        else:
            self.stdout.write(self.style.ERROR('❌ 未找到 API Key'))
            return

        cities = City.objects.all()

        if not cities:
            self.stdout.write(self.style.ERROR('❌ 没有找到城市数据'))
            return

        self.stdout.write(f'📡 开始获取 {len(cities)} 个城市的天气数据...\n')

        success_count = 0

        for city in cities:
            self.stdout.write(f'正在获取 {city.name} 的天气...', ending='')

            url = 'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'q': f"{city.name},{city.country}",
                'appid': api_key,
                'units': 'metric',
            }

            try:
                # 禁用 SSL 验证
                response = requests.get(url, params=params, timeout=10, verify=False)

                if response.status_code == 200:
                    data = response.json()

                    WeatherRecord.objects.update_or_create(
                        city=city,
                        date=datetime.now().date(),
                        defaults={
                            'temperature': data['main']['temp'],
                            'humidity': data['main']['humidity'],
                            'wind_speed': data['wind']['speed'],
                            'pm25': 50,
                        }
                    )

                    self.stdout.write(self.style.SUCCESS(f' ✓ {data["main"]["temp"]}°C, 💧{data["main"]["humidity"]}%'))
                    success_count += 1
                elif response.status_code == 401:
                    self.stdout.write(self.style.ERROR(f' ✗ API Key 无效，请检查 .env 文件'))
                    return  # 停止执行
                else:
                    self.stdout.write(self.style.ERROR(f' ✗ HTTP {response.status_code}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f' ✗ 错误: {str(e)[:50]}'))

        self.stdout.write(f'\n✅ 成功获取 {success_count}/{len(cities)} 个城市的天气数据')