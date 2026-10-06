from __future__ import annotations

import os
from typing import Optional
from PIL import Image

from .models import Panorama


def inject_metadata(image_path: str, pano: Panorama, width: int, height: int) -> bool:
    """
    Вшивает сферические метаданные (Google Photo Sphere / GPano XMP) и EXIF GPS
    в сохранённое изображение JPEG для поддержки 360° в VR и веб-плеерах.
    """
    try:
        import pyexiv2
        pyexiv2.set_log_level(4)
        
        with pyexiv2.Image(image_path) as img:
            # XMP GPano метаданные
            xmp_data = {
                "Xmp.GPano.UsePanoramaViewer": "True",
                "Xmp.GPano.ProjectionType": "equirectangular",
                "Xmp.GPano.CroppedAreaImageWidthPixels": str(width),
                "Xmp.GPano.CroppedAreaImageHeightPixels": str(height),
                "Xmp.GPano.FullPanoWidthPixels": str(width),
                "Xmp.GPano.FullPanoHeightPixels": str(height),
                "Xmp.GPano.CroppedAreaLeftPixels": "0",
                "Xmp.GPano.CroppedAreaTopPixels": "0",
            }
            
            if pano.heading_degrees is not None:
                # В GPano 0 градусов указывает на Север (по часовой стрелке)
                xmp_data["Xmp.GPano.PoseHeadingDegrees"] = f"{pano.heading_degrees:.2f}"

            img.modify_xmp(xmp_data)

            # EXIF метаданные
            exif_data = {
                "Exif.Image.Make": pano.author or "Yandex",
                "Exif.Image.Model": "Yandex Panoramas",
                "Exif.Image.Software": "yandex-panorama-downloader",
            }
            
            if pano.date:
                dt_str = pano.date.strftime("%Y:%m:%d %H:%M:%S")
                exif_data["Exif.Image.DateTime"] = dt_str
                exif_data["Exif.Photo.DateTimeOriginal"] = dt_str

            img.modify_exif(exif_data)
            
        return True
    except ImportError:
        # pyexiv2 не установлен - пропускаем XMP GPano без ошибки
        return False
    except Exception:
        return False
