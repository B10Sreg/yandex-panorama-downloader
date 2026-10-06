import math
from yandex_panorama.models import Panorama, Size, Link


def test_size_properties():
    s = Size(13824, 6912)
    assert s.width == 13824
    assert s.height == 6912


def test_link_properties():
    link = Link(pano_id="test_id", direction=math.pi / 2)
    assert abs(link.direction_degrees - 90.0) < 1e-4


def test_panorama_properties():
    sizes = [Size(13824, 6912), Size(7168, 3584)]
    pano = Panorama(
        id="test_pano_123",
        lat=55.03,
        lon=82.92,
        image_id="abc123xyz",
        tile_size=Size(256, 256),
        image_sizes=sizes,
        heading=math.pi,
    )
    assert pano.max_size.width == 13824
    assert pano.zoom_levels == 2
    assert abs(pano.heading_degrees - 180.0) < 1e-4
