from django.core.management.base import BaseCommand
from weather.models import City, WeatherRecord
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = '导入测试天气数据'

    def handle(self, *args, **kwargs):
        # 获取所有城市
        cities = City.objects.all()

        if not cities:
            self.stdout.write(self.style.ERROR('没有找到城市，请先添加城市数据'))
            return

        # 为每个城市生成过去30天的天气数据
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        weather_data = []
        current_date = start_date

        while current_date <= end_date:
            for city in cities:
                # 根据城市生成合理的温度范围
                city_temps = {
                    'Beijing': (-5, 35),
                    'Shanghai': (5, 38),
                    'Chengdu': (0, 35),
                }

                temp_range = city_temps.get(city.name, (0, 30))

                # 生成随机但合理的天气数据
                weather_record = WeatherRecord(
                    city=city,
                    date=current_date,
                    temperature=round(random.uniform(temp_range[0], temp_range[1]), 1),
                    humidity=random.randint(30, 90),
                    pm25=random.randint(20, 150),
                    wind_speed=round(random.uniform(0, 20), 1)
                )
                weather_data.append(weather_record)

            current_date += timedelta(days=1)

        # 批量插入数据库
        WeatherRecord.objects.bulk_create(weather_data, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f'成功导入 {len(weather_data)} 条天气记录'))

        # 显示统计信息
        total_records = WeatherRecord.objects.count()
        self.stdout.write(f'数据库中共有 {total_records} 条天气记录')