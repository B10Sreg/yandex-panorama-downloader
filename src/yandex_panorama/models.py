from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Size:
    x: int
    y: int

    @property
    def width(self) -> int:
        return self.x

    @property
    def height(self) -> int:
        return self.y


@dataclass
class Link:
    pano_id: str
    direction: float  # в радианах

    @property
    def direction_degrees(self) -> float:
        return math.degrees(self.direction)


@dataclass
class Place:
    id: int
    name: str
    lat: float
    lon: float
    tags: List[str] = field(default_factory=list)


@dataclass
class Address:
    lat: float
    lon: float
    house_number: str
    street_and_house: str


@dataclass
class Panorama:
    id: str
    lat: float
    lon: float
    image_id: str
    tile_size: Size
    image_sizes: List[Size]
    
    heading: Optional[float] = None  # в радианах
    date: Optional[datetime] = None
    height: Optional[float] = None
    street_name: Optional[str] = None
    author: Optional[str] = None
    author_avatar_url: Optional[str] = None
    
    links: List[Link] = field(default_factory=list)
    places: List[Place] = field(default_factory=list)
    addresses: List[Address] = field(default_factory=list)
    raw_data: Optional[dict] = field(default=None, repr=False)

    @property
    def max_size(self) -> Size:
        return self.image_sizes[0] if self.image_sizes else Size(0, 0)

    @property
    def heading_degrees(self) -> Optional[float]:
        return math.degrees(self.heading) if self.heading is not None else None

    @property
    def zoom_levels(self) -> int:
        return len(self.image_sizes)
