# Yandex Panorama Downloader (ypano) 🌐📸

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Высокоскоростной инструмент командной строки (CLI) и Python-библиотека для скачивания **360° сферических эквидистантных панорам Яндекс Карт** в максимальном исходном качестве (до **14K / 95 Мп**) без лишних тяжеловесных зависимостей (без PyTorch и CUDA).

---

## ✨ Возможности

- 🚀 **Максимальная скорость**: Асинхронное параллельное скачивание тайлов через `aiohttp` (панорама 45 Мп скачивается и сшивается менее чем за **2 секунды**).
- 🧭 **Умный парсер**: Принимает любые ссылки Яндекс Карт (десктоп, мобильные, организации), координаты (`широта, долгота`) или прямые ID панорам.
- 🥽 **Готовность к VR и 360-просмотрщикам**: Автоматически вшивает метаданные **Google Photo Sphere (GPano XMP)** и **EXIF GPS**, благодаря чему панорамы сразу корректно распознаются в VR-шлемах, Varwin XR, Facebook и веб-плеерах.
- 🎨 **Красивый интерфейс**: Информативные таблицы, индикаторы процесса и прогресс-бары на базе `rich`.
- 📁 **Пакетная обработка**: Загрузка списков ссылок из текстового файла (`--file urls.txt`) с автогенерацией `manifest.json`.
- 🎚️ **Гибкое управление качеством**: Выбор уровня зума от оригинального (`zoom=0`, до 14K) до превью.
- 🐍 **Чистый Python API**: Удобно встраивать в собственные скрипты и пайплайны.
- 🪶 **Легковесность**: Никаких гигабайтов CUDA или машинного обучения — только `aiohttp`, `Pillow`, `requests` и `rich`.

---

## 📦 Установка

### Через pip (рекомендуется):
```bash
pip install yandex-panorama-downloader
```

Для полной поддержки записи расширенных сферических метаданных (GPano XMP):
```bash
pip install yandex-panorama-downloader[metadata]
```

### Из исходного кода:
```bash
git clone https://github.com/B10Sreg/yandex-panorama-downloader.git
cd yandex-panorama-downloader
pip install -e .
```

---

## 🚀 Использование CLI (`ypano`)

После установки доступна команда `ypano` (и псевдоним `yandex-panorama`):

### 1. Скачивание по ссылке на Яндекс Карты:
```bash
ypano "https://yandex.ru/maps/org/novosibirskiy_teatr_opery_i_baleta/1062011780/?panorama[point]=82.924427%2C55.030404"
```

### 2. Скачивание по координатам:
```bash
ypano "55.030404, 82.924427" -o stage.jpg
```

### 3. Скачивание по ID панорамы:
```bash
ypano 1568405298_680805921_23_1584682900 -o hall.jpg
```

### 4. Выбор уровня разрешения (`-z` / `--zoom`):
- `-z 0` *(по умолчанию)* — максимальное исходное разрешение (до 13824 × 6912 px)
- `-z 1` — высокое разрешение (~7168 × 3584 px)
- `-z 2` — среднее разрешение (~3584 × 1792 px)

```bash
ypano "55.030404, 82.924427" -z 1
```

### 5. Пакетная загрузка из файла:
Создайте текстовый файл `urls.txt`:
```text
# Фасад театра
https://yandex.ru/maps/?panorama[point]=82.922570%2C55.030230
# Большой зал
https://yandex.ru/maps/?panorama[point]=82.924427%2C55.030404
```

И запустите скачивание всей пачки в папку с генерацией манифеста:
```bash
ypano --file urls.txt -o ./panoramas/ --manifest ./panoramas/manifest.json
```

### 6. Только просмотр информации о панораме (`--info`):
```bash
ypano "55.030404, 82.924427" --info
```

---

## 🐍 Использование как Python-библиотеки

### Асинхронный пример (максимальная производительность):

```python
import asyncio
from aiohttp import ClientSession
from yandex_panorama import find_panorama_async, download_panorama_async

async def main():
    async with ClientSession() as session:
        # Поиск панорамы по координатам
        pano = await find_panorama_async(55.030404, 82.924427, session)
        
        if pano:
            print(f"Найдена: {pano.id}, макс. размер: {pano.max_size.x}x{pano.max_size.y}")
            # Скачивание в оригинальном качестве (zoom=0)
            await download_panorama_async(pano, "panorama.jpg", session, zoom=0)
            print("Готово!")

asyncio.run(main())
```

### Простой синхронный пример:

```python
from yandex_panorama import find_panorama, download_panorama

# Поиск по координатам
pano = find_panorama(55.030404, 82.924427)

if pano:
    # Скачивание панорамы
    download_panorama(pano, "stage.jpg", zoom=0)
```

### Поиск по ID:

```python
from yandex_panorama import find_panorama_by_id, download_panorama

pano = find_panorama_by_id("1568405298_680805921_23_1584682900")
if pano:
    download_panorama(pano, "auditorium.jpg")
```

---

## ⚙️ Опции командной строки

```text
ypano [-h] [-f FILE] [-o OUTPUT] [-z ZOOM] [-c CONCURRENCY]
      [-q QUALITY] [--info] [--manifest MANIFEST] [-v]
      [targets ...]

Позиционные аргументы:
  targets              Ссылки на Яндекс Карты, координаты 'lat,lon' или ID панорам

Опции:
  -f, --file FILE      Файл со списком ссылок (по одной на строку)
  -o, --output OUTPUT  Имя файла или папка назначения
  -z, --zoom ZOOM      Уровень зума (0 = максимальный, по умолчанию: 0)
  -c, --concurrency N  Число одновременных потоков скачивания (по умолчанию: 24)
  -q, --quality N      Качество сжатия JPEG 1-100 (по умолчанию: 95)
  --info               Показать информацию без скачивания файлов
  --manifest PATH      Сохранить JSON-манифест со всеми метаданными
  -v, --version        Показать версию программы
```

---

## 🛠 Тестирование

```bash
pytest tests/
```

---

## 📄 Лицензия

Проект распространяется под открытой лицензией [MIT](LICENSE).

Автор: **B10Sreg** (<iam171181@gmail.com>)
