from __future__ import annotations

import io
import math
import time
import asyncio
from typing import Optional, Callable

import aiohttp
from PIL import Image

from .models import Panorama
from .metadata import inject_metadata

# Отключаем лимит пикселей Pillow для сверхвысоких разрешений (14K+)
Image.MAX_IMAGE_PIXELS = None

TILE_URL_TEMPLATE = "https://pano.maps.yandex.net/{image_id}/{zoom}.{x}.{y}"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


async def _fetch_tile(
    session: aiohttp.ClientSession,
    url: str,
    sem: asyncio.Semaphore,
    max_retries: int = 3,
) -> Optional[bytes]:
    for attempt in range(max_retries):
        try:
            async with sem:
                async with session.get(url, headers={"User-Agent": USER_AGENT}) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    elif resp.status == 404:
                        # Некоторые крайние тайлы могут отсутствовать на сервере
                        return None
        except Exception:
            if attempt < max_retries - 1:
                await asyncio.sleep(0.3 * (attempt + 1))
            else:
                return None
    return None


async def download_panorama_async(
    pano: Panorama,
    output_path: str,
    session: aiohttp.ClientSession,
    zoom: int = 0,
    concurrency: int = 24,
    quality: int = 95,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> str:
    """
    Асинхронно скачивает панораму, сшивает тайлы и сохраняет эквидистантное изображение.
    
    :param pano: Объект Panorama
    :param output_path: Путь для сохранения .jpg файла
    :param session: aiohttp.ClientSession
    :param zoom: Уровень зума (0 = максимальное исходное разрешение)
    :param concurrency: Количество одновременных загрузок тайлов (по умолчанию 24)
    :param quality: Качество сохранения JPEG (по умолчанию 95)
    :param progress_callback: Функция обратного вызова (completed, total)
    :return: Итоговый путь к файлу
    """
    if not pano.image_sizes:
        raise ValueError(f"Панорама {pano.id} не содержит информации о размерах.")

    zoom = max(0, min(zoom, len(pano.image_sizes) - 1))
    img_size = pano.image_sizes[zoom]
    tile_w = pano.tile_size.x
    tile_h = pano.tile_size.y

    cols = math.ceil(img_size.x / tile_w)
    rows = math.ceil(img_size.y / tile_h)
    total_tiles = cols * rows

    canvas = Image.new("RGB", (img_size.x, img_size.y), (0, 0, 0))
    sem = asyncio.Semaphore(concurrency)
    completed = 0

    async def process_tile(x: int, y: int):
        nonlocal completed
        url = TILE_URL_TEMPLATE.format(
            image_id=pano.image_id,
            zoom=zoom,
            x=x,
            y=y,
        )
        data = await _fetch_tile(session, url, sem)
        if data:
            try:
                tile_img = Image.open(io.BytesIO(data))
                canvas.paste(tile_img, (x * tile_w, y * tile_h))
            except Exception:
                pass
        completed += 1
        if progress_callback:
            progress_callback(completed, total_tiles)

    tasks = [process_tile(x, y) for y in range(rows) for x in range(cols)]
    await asyncio.gather(*tasks)

    # Сохранение на диск
    canvas.save(output_path, "JPEG", quality=quality)
    
    # Вшивание метаданных 360 Photo Sphere (GPano)
    inject_metadata(output_path, pano, img_size.x, img_size.y)

    return output_path


def download_panorama(
    pano: Panorama,
    output_path: str,
    zoom: int = 0,
    concurrency: int = 24,
    quality: int = 95,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> str:
    """
    Синхронная обёртка для загрузки панорамы.
    """
    async def _runner():
        async with aiohttp.ClientSession() as session:
            return await download_panorama_async(
                pano,
                output_path,
                session=session,
                zoom=zoom,
                concurrency=concurrency,
                quality=quality,
                progress_callback=progress_callback,
            )

    return asyncio.run(_runner())
