from yandex_panorama.url_parser import parse_target


def test_parse_url_with_id_and_point():
    url = (
        "https://yandex.ru/maps/org/theatre/12345/?"
        "ll=82.924605%2C55.030425&"
        "panorama%5Bid%5D=1568394220_680807728_23_1715116379&"
        "panorama%5Bpoint%5D=82.922570%2C55.030230"
    )
    info = parse_target(url)
    assert info.id == "1568394220_680807728_23_1715116379"
    assert info.lat == 55.030230
    assert info.lon == 82.922570


def test_parse_url_point_only():
    url = (
        "https://yandex.ru/maps/?panorama%5Bpoint%5D=82.923511%2C55.030321"
    )
    info = parse_target(url)
    assert info.id is None
    assert info.lat == 55.030321
    assert info.lon == 82.923511


def test_parse_coordinates_string():
    info = parse_target("55.030404, 82.924427")
    assert info.lat == 55.030404
    assert info.lon == 82.924427

    # Обратный порядок (lon, lat)
    info2 = parse_target("82.924427, 55.030404")
    assert info2.lat == 55.030404
    assert info2.lon == 82.924427


def test_parse_raw_id():
    pano_id = "1568399834_680806783_23_1584674300"
    info = parse_target(pano_id)
    assert info.id == pano_id
    assert info.lat is None
    assert info.lon is None
