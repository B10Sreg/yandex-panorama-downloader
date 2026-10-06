from yandex_panorama.api import parse_panorama_payload


def test_parse_panorama_payload():
    mock_payload = {
        "status": "success",
        "data": {
            "Data": {
                "panoramaId": "1568394220_680807728_23_1715116379",
                "Point": {
                    "coordinates": ["82.922570", "55.030230", "150"],
                    "name": "Красный проспект"
                },
                "EquirectangularProjection": {
                    "Origin": ["90.0", "0.0", "0.0"]
                },
                "Images": {
                    "imageId": "eqBxo8kjMPVT",
                    "Tiles": {
                        "width": "256",
                        "height": "256"
                    },
                    "Zooms": [
                        {"level": "0", "width": "13824", "height": "6912"},
                        {"level": "1", "width": "7168", "height": "3584"}
                    ]
                }
            },
            "Annotation": {
                "Thoroughfares": [
                    {
                        "Connection": {"href": "https://maps.yandex.ru/?oid=neighbor_123&other=val"},
                        "Direction": ["45.0", "0.0"]
                    }
                ]
            },
            "Author": {
                "name": "Siberia360"
            }
        }
    }

    pano = parse_panorama_payload(mock_payload)
    assert pano is not None
    assert pano.id == "1568394220_680807728_23_1715116379"
    assert pano.lat == 55.030230
    assert pano.lon == 82.922570
    assert pano.image_id == "eqBxo8kjMPVT"
    assert pano.author == "Siberia360"
    assert pano.street_name == "Красный проспект"
    assert len(pano.image_sizes) == 2
    assert pano.max_size.width == 13824
    assert len(pano.links) == 1
    assert pano.links[0].pano_id == "neighbor_123"


def test_parse_invalid_payload():
    assert parse_panorama_payload({"status": "error"}) is None
    assert parse_panorama_payload({}) is None
