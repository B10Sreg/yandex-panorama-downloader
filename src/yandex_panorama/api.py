from __future__ import annotations

import re
import math
import json
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, List, Tuple

import aiohttp
import requests

from .models import Panorama, Size, Link, Place, Address

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

BASE_API_URL = "https://api-maps.yandex.ru/services/panoramas/1.x/"


def build_find_url(lat: float, lon: float, lang: str = "ru_RU") -> str:
    params = {
        "l": "stv",
        "lang": lang,
        "ll": f"{lon},{lat}",
        "origin": "userAction",
        "provider": "streetview",
    }
    return f"{BASE_API_URL}?{urllib.parse.urlencode(params)}"


def build_by_id_url(panoid: str, lang: str = "ru_RU") -> str:
    params = {
        "l": "stv",
        "lang": lang,
        "oid": panoid,
        "origin": "userAction",
        "provider": "streetview",
    }
    return f"{BASE_API_URL}?{urllib.parse.urlencode(params)}"


def parse_panorama_payload(payload: dict) -> Optional[Panorama]:
    if not payload or payload.get("status") != "success":
        return None

    data_wrapper = payload.get("data", {})
    if not data_wrapper or "Data" not in data_wrapper:
        return None

    data = data_wrapper["Data"]
    annotation = data_wrapper.get("Annotation", {})
    panoid = data["panoramaId"]

    # Координаты
    coords = data.get("Point", {}).get("coordinates", [0, 0, 0])
    lon = float(coords[0])
    lat = float(coords[1])
    height = float(coords[2]) if len(coords) > 2 else None
    street_name = data.get("Point", {}).get("name")

    # Ракурс съемки (heading)
    heading_raw = data.get("EquirectangularProjection", {}).get("Origin", [0])[0]
    heading = math.radians(float(heading_raw)) if heading_raw is not None else None

    # Изображения и тайлы
    images = data.get("Images", {})
    image_id = images.get("imageId", "")
    tiles_meta = images.get("Tiles", {})
    tile_size = Size(
        int(tiles_meta.get("width", 256)),
        int(tiles_meta.get("height", 256)),
    )

    # Уровни приближения (zooms)
    zooms = images.get("Zooms", [])
    image_sizes: List[Size] = [None] * len(zooms)
    for z in zooms:
        idx = int(z["level"])
        image_sizes[idx] = Size(int(z["width"]), int(z["height"]))

    # Дата из ID панорамы (последняя секция - unix timestamp)
    date_val = None
    try:
        ts = int(panoid.split("_")[-1])
        date_val = datetime.fromtimestamp(ts, timezone.utc)
    except Exception:
        pass

    # Связи (переходы в соседние панорамы)
    links: List[Link] = []
    for tf in annotation.get("Thoroughfares", []):
        href = tf.get("Connection", {}).get("href", "")
        direction_val = tf.get("Direction", [0])[0]
        match = re.search(r"oid=([^&]+)", href)
        if match:
            links.append(Link(pano_id=match.group(1), direction=math.radians(float(direction_val))))

    # Организации / места
    places: List[Place] = []
    for comp in annotation.get("Companies", []):
        props = comp.get("properties", {})
        geom = comp.get("geometry", {}).get("coordinates", [0, 0])
        places.append(
            Place(
                id=int(props.get("id", 0)),
                name=props.get("name", ""),
                lat=geom[1],
                lon=geom[0],
                tags=props.get("tags", []),
            )
        )

    # Адреса
    addresses: List[Address] = []
    for marker in annotation.get("Markers", []):
        coords_m = marker.get("geometry", {}).get("coordinates", [0, 0, 0])
        props = marker.get("properties", {})
        if len(coords_m) > 2 and coords_m[2] == 7:  # адресные метки
            addresses.append(
                Address(
                    lat=coords_m[1],
                    lon=coords_m[0],
                    house_number=props.get("name", ""),
                    street_and_house=props.get("description", ""),
                )
            )

    author = data_wrapper.get("Author", {}).get("name")
    avatar = data_wrapper.get("Author", {}).get("avatarUrlTemplate")

    return Panorama(
        id=panoid,
        lat=lat,
        lon=lon,
        heading=heading,
        image_id=image_id,
        tile_size=tile_size,
        image_sizes=image_sizes,
        date=date_val,
        height=height,
        street_name=street_name,
        author=author,
        author_avatar_url=avatar,
        links=links,
        places=places,
        addresses=addresses,
        raw_data=data_wrapper,
    )


# --- Синхронные методы ---

def find_panorama(lat: float, lon: float, lang: str = "ru_RU", session: Optional[requests.Session] = None) -> Optional[Panorama]:
    """Находит ближайшую панораму к координатам (lat, lon)."""
    url = build_find_url(lat, lon, lang)
    headers = {"User-Agent": USER_AGENT}
    s = session or requests.Session()
    resp = s.get(url, headers=headers)
    resp.raise_for_status()
    return parse_panorama_payload(resp.json())


def find_panorama_by_id(panoid: str, lang: str = "ru_RU", session: Optional[requests.Session] = None) -> Optional[Panorama]:
    """Получает метаданные панорамы по её ID."""
    url = build_by_id_url(panoid, lang)
    headers = {"User-Agent": USER_AGENT}
    s = session or requests.Session()
    resp = s.get(url, headers=headers)
    resp.raise_for_status()
    return parse_panorama_payload(resp.json())


# --- Асинхронные методы ---

async def find_panorama_async(lat: float, lon: float, session: aiohttp.ClientSession, lang: str = "ru_RU") -> Optional[Panorama]:
    """Асинхронно находит ближайшую панораму к координатам (lat, lon)."""
    url = build_find_url(lat, lon, lang)
    headers = {"User-Agent": USER_AGENT}
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            return None
        payload = await resp.json(content_type=None)
        return parse_panorama_payload(payload)


async def find_panorama_by_id_async(panoid: str, session: aiohttp.ClientSession, lang: str = "ru_RU") -> Optional[Panorama]:
    """Асинхронно получает метаданные панорамы по её ID."""
    url = build_by_id_url(panoid, lang)
    headers = {"User-Agent": USER_AGENT}
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            return None
        payload = await resp.json(content_type=None)
        return parse_panorama_payload(payload)
