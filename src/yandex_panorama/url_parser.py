from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from typing import Optional


@dataclass
class TargetInfo:
    raw: str
    id: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    direction: Optional[str] = None
    span: Optional[str] = None

    @property
    def has_coords(self) -> bool:
        return self.lat is not None and self.lon is not None

    @property
    def has_id(self) -> bool:
        return bool(self.id)


def parse_target(target: str) -> TargetInfo:
    """
    Разбирает входную строку (URL Яндекс Карт, координаты или ID панорамы).
    
    Поддерживаемые форматы:
    - https://yandex.ru/maps/.../?panorama[id]=...&panorama[point]=lon,lat...
    - https://yandex.ru/maps/.../?ll=lon,lat&panorama[point]=lon,lat
    - "55.030404, 82.924427" или "82.924427, 55.030404"
    - "1568405298_680805921_23_1584682900"
    """
    target = target.strip()
    
    # 1. Ссылка на Яндекс Карты
    if "yandex" in target or "maps" in target or target.startswith("http://") or target.startswith("https://"):
        parsed = urllib.parse.urlparse(target)
        params = urllib.parse.parse_qs(parsed.query)

        pano_id = params.get("panorama[id]", [None])[0] or params.get("oid", [None])[0]
        point = params.get("panorama[point]", [None])[0]
        ll = params.get("ll", [None])[0]
        direction = params.get("panorama[direction]", [None])[0]
        span = params.get("panorama[span]", [None])[0]

        lat = None
        lon = None
        coords_str = point or ll
        if coords_str:
            parts = coords_str.split(",")
            if len(parts) == 2:
                try:
                    lon = float(parts[0])
                    lat = float(parts[1])
                except ValueError:
                    pass

        return TargetInfo(
            raw=target,
            id=pano_id,
            lat=lat,
            lon=lon,
            direction=direction,
            span=span,
        )

    # 2. Координаты вида "lat, lon" или "lon, lat"
    coord_match = re.match(r"^([+-]?\d+(?:\.\d+)?)[,\s]+([+-]?\d+(?:\.\d+)?)$", target)
    if coord_match:
        val1 = float(coord_match.group(1))
        val2 = float(coord_match.group(2))
        
        # Эвристика определения порядка координат:
        # Широта (lat) ограничена [-90, 90]. Долгота (lon) [-180, 180].
        # В РФ широта обычно 40..80, долгота 20..180.
        if val1 > 90 or (val1 > 80 and val2 <= 80):
            lon, lat = val1, val2
        else:
            lat, lon = val1, val2
            
        return TargetInfo(raw=target, lat=lat, lon=lon)

    # 3. Иначе считаем это прямым ID панорамы (или oid)
    return TargetInfo(raw=target, id=target)
