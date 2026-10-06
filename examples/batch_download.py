#!/usr/bin/env python3
"""
Пример пакетной загрузки списка панорам из массива ссылок.
"""

import asyncio
from aiohttp import ClientSession
from yandex_panorama import parse_target, find_panorama_by_id_async, find_panorama_async, download_panorama_async

URLS = [
    "https://yandex.ru/maps/?panorama[point]=82.922570%2C55.030230",  # Площадь
    "https://yandex.ru/maps/?panorama[point]=82.924427%2C55.030404",  # Зал
]

async def main():
    async with ClientSession() as session:
        for idx, url in enumerate(URLS, 1):
            target = parse_target(url)
            pano = None
            if target.has_id:
                pano = await find_panorama_by_id_async(target.id, session)
            elif target.has_coords:
                pano = await find_panorama_async(target.lat, target.lon, session)

            if pano:
                out_name = f"batch_{idx}_{pano.id}.jpg"
                print(f"[{idx}/{len(URLS)}] Скачивание {pano.id} в {out_name}...")
                await download_panorama_async(pano, out_name, session, zoom=1)  # zoom 1 (~7K)
                print(f"  ✔ Сохранено: {out_name}")

if __name__ == "__main__":
    asyncio.run(main())
