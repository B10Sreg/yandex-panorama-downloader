from __future__ import annotations

import os
import sys
import time
import json
import asyncio
import argparse
from typing import List, Optional

import re
import aiohttp
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    DownloadColumn,
)

from . import __version__
from .models import Panorama
from .url_parser import parse_target, TargetInfo
from .api import find_panorama_async, find_panorama_by_id_async
from .downloader import download_panorama_async

# Настройка UTF-8 для Windows консоли (cmd.exe / PowerShell)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    # WindowsSelectorEventLoopPolicy предотвращает RuntimeError: Event loop is closed в aiohttp на Windows
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

console = Console(highlight=False)


def sanitize_filename(filename: str) -> str:
    """Очищает имя файла от запрещённых символов Windows: \\ / : * ? \" < > |"""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)


def display_banner():
    banner = f"[bold cyan]Yandex Panorama Downloader[/bold cyan] [dim]v{__version__}[/dim]\n" \
             f"[dim]Скачивание 360° эквидистантных панорам Яндекс Карт в оригинальном качестве[/dim]"
    console.print(Panel(banner, border_style="cyan"))


def display_panorama_info(pano: Panorama, zoom: int):
    table = Table(title="[bold]Информация о панораме[/bold]", show_header=False, border_style="dim")
    table.add_column("Параметр", style="bold cyan")
    table.add_column("Значение", style="white")

    table.add_row("ID панорамы", pano.id)
    table.add_row("Координаты", f"{pano.lat:.6f}, {pano.lon:.6f}")
    if pano.street_name:
        table.add_row("Адрес / Улица", pano.street_name)
    if pano.date:
        table.add_row("Дата съёмки", pano.date.strftime("%Y-%m-%d %H:%M:%S UTC"))
    if pano.author:
        table.add_row("Автор", pano.author)

    available_sizes = pano.image_sizes or []
    if available_sizes:
        actual_zoom = max(0, min(zoom, len(available_sizes) - 1))
        chosen_size = available_sizes[actual_zoom]
        table.add_row("Выбранное разрешение", f"[green]{chosen_size.x} × {chosen_size.y} px[/green] (zoom {actual_zoom})")
        
        all_zooms = ", ".join(f"{s.x}×{s.y}" for s in available_sizes)
        table.add_row("Доступные уровни", all_zooms)

    if pano.links:
        table.add_row("Связанных панорам", f"{len(pano.links)} переходов")

    console.print(table)


async def resolve_panorama(target_info: TargetInfo, session: aiohttp.ClientSession) -> Optional[Panorama]:
    pano = None
    if target_info.has_id:
        try:
            pano = await find_panorama_by_id_async(target_info.id, session)
        except Exception:
            pass

    if pano is None and target_info.has_coords:
        try:
            pano = await find_panorama_async(target_info.lat, target_info.lon, session)
        except Exception:
            pass

    return pano


async def process_target(
    target_str: str,
    output_arg: Optional[str],
    zoom: int,
    concurrency: int,
    quality: int,
    info_only: bool,
    session: aiohttp.ClientSession,
) -> Optional[dict]:
    target_info = parse_target(target_str)

    with console.status(f"[cyan]Поиск панорамы: {target_str[:60]}...[/cyan]"):
        pano = await resolve_panorama(target_info, session)

    if not pano:
        console.print(f"[red]❌ Панорама не найдена:[/red] {target_str}")
        return None

    display_panorama_info(pano, zoom)

    if info_only:
        return None

    # Определение пути сохранения
    actual_zoom = max(0, min(zoom, len(pano.image_sizes) - 1))
    img_size = pano.image_sizes[actual_zoom]

    default_filename = sanitize_filename(f"panorama_{pano.id}_{img_size.x}x{img_size.y}.jpg")
    if not output_arg:
        output_path = default_filename
    elif os.path.isdir(output_arg) or output_arg.endswith("/") or output_arg.endswith("\\"):
        os.makedirs(output_arg, exist_ok=True)
        output_path = os.path.join(output_arg, default_filename)
    else:
        out_dir = os.path.dirname(os.path.abspath(output_arg))
        base_name = sanitize_filename(os.path.basename(output_arg))
        output_path = os.path.join(out_dir, base_name)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Прогресс-бар скачивания тайлов
    start_time = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[cyan]{task.completed}/{task.total} тайлов[/cyan]"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(f"[bold yellow]Загрузка тайлов[/bold yellow]", total=100)

        def on_progress(completed: int, total: int):
            progress.update(task_id, total=total, completed=completed)

        await download_panorama_async(
            pano=pano,
            output_path=output_path,
            session=session,
            zoom=actual_zoom,
            concurrency=concurrency,
            quality=quality,
            progress_callback=on_progress,
        )

    duration = time.time() - start_time
    filesize_mb = os.path.getsize(output_path) / (1024 * 1024)

    console.print(
        f"[green]✔ Сохранено:[/green] [bold]{output_path}[/bold] "
        f"[dim]({filesize_mb:.2f} MB, {duration:.1f} сек)[/dim]\n"
    )

    return {
        "id": pano.id,
        "image_id": pano.image_id,
        "filename": os.path.basename(output_path),
        "path": os.path.abspath(output_path),
        "width": img_size.x,
        "height": img_size.y,
        "filesize_mb": round(filesize_mb, 2),
        "lat": pano.lat,
        "lon": pano.lon,
        "date": str(pano.date) if pano.date else None,
        "author": pano.author,
        "source": target_str,
    }


def parse_targets_file(file_path: str) -> List[str]:
    targets = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                targets.append(line)
    return targets


async def async_main():
    parser = argparse.ArgumentParser(
        prog="ypano",
        description="Высокоскоростная загрузка 360° эквидистантных панорам Яндекс Карт в исходном качестве.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  ypano "https://yandex.ru/maps/..."
  ypano "55.030404, 82.924427" -o stage.jpg
  ypano 1568405298_680805921_23_1584682900 -z 1
  ypano --file urls.txt -o ./panoramas/ --manifest manifest.json
        """,
    )

    parser.add_argument(
        "targets",
        nargs="*",
        help="Ссылки на Яндекс Карты, координаты 'lat,lon' или ID панорам",
    )
    parser.add_argument(
        "-f", "--file",
        help="Текстовый файл со списком ссылок/координат (по одной на строку)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Путь для сохранения файла или директория",
    )
    parser.add_argument(
        "-z", "--zoom",
        type=int,
        default=0,
        help="Уровень зума: 0 = максимальное исходное качество (по умолчанию), 1 = ~7K, 2 = ~3.5K",
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=24,
        help="Количество параллельных потоков скачивания тайлов (по умолчанию: 24)",
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=95,
        help="Качество сжатия JPEG (по умолчанию: 95)",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Вывести метаданные панорамы без скачивания файлов",
    )
    parser.add_argument(
        "--manifest",
        help="Сохранить JSON-манифест со всеми метаданными скачанных панорам",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    # Сбор всех целей
    all_targets: List[str] = list(args.targets)
    if args.file:
        if not os.path.exists(args.file):
            console.print(f"[red]Ошибка: файл {args.file} не найден.[/red]")
            sys.exit(1)
        all_targets.extend(parse_targets_file(args.file))

    if not all_targets:
        display_banner()
        parser.print_help()
        sys.exit(0)

    display_banner()

    manifest_entries = []
    async with aiohttp.ClientSession() as session:
        for idx, target in enumerate(all_targets, 1):
            if len(all_targets) > 1:
                console.print(f"[bold cyan]— [Цель {idx}/{len(all_targets)}][/bold cyan]")

            res = await process_target(
                target_str=target,
                output_arg=args.output,
                zoom=args.zoom,
                concurrency=args.concurrency,
                quality=args.quality,
                info_only=args.info,
                session=session,
            )
            if res:
                manifest_entries.append(res)

    if args.manifest and manifest_entries:
        with open(args.manifest, "w", encoding="utf-8") as f:
            json.dump(manifest_entries, f, ensure_ascii=False, indent=2)
        console.print(f"[bold green]✔ Манифест сохранён:[/bold green] {args.manifest}")


def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Загрузка прервана пользователем.[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
