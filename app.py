from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

GEOCODE_API = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"


@dataclass
class PlaceResult:
    name: str
    country: str
    latitude: float
    longitude: float
    timezone: str


WEATHER_CODE_MAP = {
    0: "晴朗",
    1: "基本晴",
    2: "局部多云",
    3: "阴天",
    45: "有雾",
    48: "冻雾",
    51: "小毛毛雨",
    53: "中毛毛雨",
    55: "大毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小阵雨",
    81: "中阵雨",
    82: "大阵雨",
    85: "小阵雪",
    86: "大阵雪",
    95: "雷暴",
    96: "雷暴伴小冰雹",
    99: "雷暴伴大冰雹",
}


def get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    final_url = f"{url}?{urlencode(params, doseq=True)}"
    with urlopen(final_url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def geocode_place(place_name: str) -> PlaceResult | None:
    data = get_json(
        GEOCODE_API,
        {"name": place_name, "count": 1, "language": "zh", "format": "json"},
    )
    results = data.get("results", [])
    if not results:
        return None

    first = results[0]
    return PlaceResult(
        name=first.get("name", place_name),
        country=first.get("country", "未知国家"),
        latitude=first["latitude"],
        longitude=first["longitude"],
        timezone=first.get("timezone", "auto"),
    )


def get_weather(place: PlaceResult) -> dict[str, Any]:
    data = get_json(
        WEATHER_API,
        {
            "latitude": place.latitude,
            "longitude": place.longitude,
            "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "weather_code"],
            "daily": ["temperature_2m_max", "temperature_2m_min"],
            "timezone": "auto",
        },
    )

    current = data.get("current", {})
    daily = data.get("daily", {})
    code = current.get("weather_code")

    return {
        "location": f"{place.name}, {place.country}",
        "latitude": place.latitude,
        "longitude": place.longitude,
        "timezone": data.get("timezone", place.timezone),
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "weather_code": code,
        "weather_desc": WEATHER_CODE_MAP.get(code, "未知天气"),
        "today_max": (daily.get("temperature_2m_max") or [None])[0],
        "today_min": (daily.get("temperature_2m_min") or [None])[0],
        "source": "Open-Meteo 官方公开API",
        "source_url": "https://open-meteo.com/",
    }


class WeatherHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.serve_file(TEMPLATES_DIR / "index.html", "text/html; charset=utf-8")
            return

        if parsed.path.startswith("/static/"):
            static_path = STATIC_DIR / parsed.path.replace("/static/", "", 1)
            self.serve_static(static_path)
            return

        if parsed.path == "/api/weather":
            self.handle_weather(parsed.query)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def serve_static(self, file_path: Path) -> None:
        if not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.serve_file(file_path, content_type)

    def serve_file(self, file_path: Path, content_type: str) -> None:
        if not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def handle_weather(self, query_string: str) -> None:
        query = parse_qs(query_string)
        place_name = (query.get("place", [""])[0] or "").strip()
        if not place_name:
            self.send_json({"error": "请先输入地理名称"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            place = geocode_place(place_name)
            if place is None:
                self.send_json({"error": "未找到该地点，请尝试更具体的名称"}, HTTPStatus.NOT_FOUND)
                return

            self.send_json(get_weather(place), HTTPStatus.OK)
        except Exception:
            self.send_json({"error": "天气服务暂时不可用，请稍后重试"}, HTTPStatus.BAD_GATEWAY)

    def send_json(self, payload: dict[str, Any], status: HTTPStatus) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), WeatherHandler)
    print("Server started at http://127.0.0.1:8000")
    server.serve_forever()
