#!/usr/bin/env python3
"""
Базовый пример использования библиотеки yandex-panorama.
"""

import asyncio
from aiohttp import ClientSession
from yandex_panorama import find_panorama_async, download_panorama_async

# Координаты: Новосибирский театр оперы и балета (НОВАТ)
LAT = 55.030404
LON = 82.924427

async def main():
    async with ClientSession() as session:
        print(f"Поиск панорамы по координатам ({LAT}, {LON})...")
        pano = await find_panorama_async(LAT, LON, session)

        if not pano:
            print("Панорама не найдена.")
            return

        print(f"Найдена панорама ID: {pano.id}")
        print(f"Максимальное разрешение: {pano.max_size.x} × {pano.max_size.y} px")
        print(f"Дата съёмки: {pano.date}")
        print("Скачивание...")

        # zoom=0 — максимальное разрешение
        output_file = f"sample_{pano.id}.jpg"
        await download_panorama_async(pano, output_file, session, zoom=0)
        print(f"Успешно сохранено: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
