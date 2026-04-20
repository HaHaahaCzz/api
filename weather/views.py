from django.db.models import Avg, Max, Min, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import City, WeatherRecord
from .openweather import fetch_and_save_city
from .serializers import CitySerializer, WeatherRecordSerializer


# ── 自定义权限：读公开，写需认证 ──────────────────────────
class IsAuthenticatedOrReadOnly(IsAuthenticatedOrReadOnly):
    """GET/HEAD/OPTIONS 公开；POST/PUT/PATCH/DELETE 需认证。"""
    pass


# City 的 CRUD
class CityListCreateView(generics.ListCreateAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class CityRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# WeatherRecord 的查询
class WeatherRecordListView(generics.ListCreateAPIView):
    queryset = WeatherRecord.objects.all()
    serializer_class = WeatherRecordSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        city_id = request.query_params.get("city_id")
        city_name = request.query_params.get("city_name")

        city_filters = {}
        if city_id:
            city_filters["id"] = city_id
        if city_name and city_name.strip():
            city_filters["name__iexact"] = city_name.strip()

        filtered_cities = City.objects.filter(**city_filters).order_by("id")

        # Allow clients to opt into raw historical rows.
        history = request.query_params.get("history", "").lower()
        if history in {"1", "true", "yes"}:
            records = (
                WeatherRecord.objects.filter(city__in=filtered_cities)
                .order_by("-date", "-id")
            )
            serializer = WeatherRecordSerializer(records, many=True)
            return Response(serializer.data)

        latest_record_id = Subquery(
            WeatherRecord.objects.filter(city_id=OuterRef("pk"))
            .order_by("-date", "-id")
            .values("id")[:1]
        )
        cities = filtered_cities.annotate(latest_record_id=latest_record_id)
        records = WeatherRecord.objects.filter(
            id__in=[city.latest_record_id for city in cities if city.latest_record_id]
        )
        record_map = {record.id: record for record in records}

        payload = []
        for city in cities:
            record = record_map.get(city.latest_record_id)
            if record:
                payload.append(WeatherRecordSerializer(record).data)
                continue
            payload.append(
                {
                    "id": None,
                    "city": city.id,
                    "date": None,
                    "temperature": None,
                    "humidity": None,
                    "pm25": None,
                    "wind_speed": None,
                }
            )
        return Response(payload)

class WeatherRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WeatherRecord.objects.all()
    serializer_class = WeatherRecordSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class LiveWeatherView(APIView):
    """GET: pull live weather from OpenWeatherMap for one city and upsert today's record."""

    def get(self, request):
        city_id = request.query_params.get("city_id")
        if not city_id:
            return Response(
                {"error": "请提供 city_id 参数"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        city = get_object_or_404(City, pk=city_id)
        record, err = fetch_and_save_city(city)
        if err:
            return Response(
                {"error": err},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        payload = dict(WeatherRecordSerializer(record).data)
        payload["source"] = "openweathermap"
        return Response(payload)


class CityTemperatureTrendView(APIView):
    """获取城市的温度趋势（月平均）"""

    def get(self, request):
        city_id = request.query_params.get('city_id')

        if not city_id:
            return Response(
                {"error": "请提供 city_id 参数"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 获取该城市的所有天气记录
        records = WeatherRecord.objects.filter(city_id=city_id)

        if not records.exists():
            return Response(
                {"error": "该城市没有天气数据"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 按月分组计算平均温度
        monthly_trend = (
            records.values('date__year', 'date__month')
            .annotate(
                avg_temp=Avg('temperature'),
                max_temp=Max('temperature'),
                min_temp=Min('temperature'),
                avg_pm25=Avg('pm25')
            )
            .order_by('date__year', 'date__month')
        )

        # 格式化输出
        result = []
        for item in monthly_trend:
            result.append({
                'year': item['date__year'],
                'month': item['date__month'],
                'avg_temperature': round(item['avg_temp'], 1),
                'max_temperature': round(item['max_temp'], 1),
                'min_temperature': round(item['min_temp'], 1),
                'avg_pm25': round(item['avg_pm25'], 1)
            })

        return Response(result)


class AirQualityAnomalyView(APIView):
    """检测空气质量异常天数（PM2.5 超标）"""

    def get(self, request):
        city_id = request.query_params.get('city_id')
        threshold = int(request.query_params.get('threshold', 75))  # 默认 PM2.5 > 75 为异常

        if not city_id:
            return Response(
                {"error": "请提供 city_id 参数"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 找出 PM2.5 超过阈值的天数
        anomalies = WeatherRecord.objects.filter(
            city_id=city_id,
            pm25__gt=threshold
        ).order_by('-date')

        serializer = WeatherRecordSerializer(anomalies, many=True)

        return Response({
            'city_id': city_id,
            'threshold': threshold,
            'anomaly_count': anomalies.count(),
            'anomalies': serializer.data
        })