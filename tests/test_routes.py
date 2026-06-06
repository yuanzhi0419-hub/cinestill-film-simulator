from io import BytesIO

from PIL import Image

from conftest import make_png_bytes


IDENTITY_CUBE = b"""
LUT_3D_SIZE 2
0 0 0
0 0 1
0 1 0
0 1 1
1 0 0
1 0 1
1 1 0
1 1 1
"""


def upload_asset(client, name="photo.png", data=None):
    response = client.post(
        "/api/assets",
        data={"files": (BytesIO(data or make_png_bytes()), name)},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    return response.get_json()["assets"][0]


def test_health(client):
    response = client.get("/api/health")

    assert response.get_json() == {"status": "ok", "local_only": True}


def test_presets_are_available(client):
    response = client.get("/api/presets")

    assert response.status_code == 200
    assert {item["id"] for item in response.get_json()["presets"]} == {
        "night-walk",
        "morning-light",
        "natural-negative",
        "soft-haze",
        "documentary-bw",
    }


def test_upload_returns_asset_metadata(client, png_file):
    response = client.post(
        "/api/assets",
        data={"files": (png_file, "photo.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    asset = response.get_json()["assets"][0]
    assert asset["original_name"] == "photo.png"
    assert asset["width"] == 12
    assert asset["height"] == 8


def test_upload_accepts_multiple_files(client):
    response = client.post(
        "/api/assets",
        data={
            "files": [
                (BytesIO(make_png_bytes()), "one.png"),
                (BytesIO(make_png_bytes(color=(80, 20, 30, 255))), "two.png"),
            ]
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert len(response.get_json()["assets"]) == 2


def test_upload_rejects_empty_invalid_and_oversized_requests(client):
    empty = client.post("/api/assets", data={}, content_type="multipart/form-data")
    invalid = client.post(
        "/api/assets",
        data={"files": (BytesIO(b"invalid"), "bad.png")},
        content_type="multipart/form-data",
    )
    oversized = client.post(
        "/api/assets",
        data={"files": (BytesIO(b"x" * (1024 * 1024 + 1)), "large.png")},
        content_type="multipart/form-data",
    )

    assert empty.status_code == 400
    assert invalid.status_code == 400
    assert oversized.status_code == 413
    assert "error" in invalid.get_json()


def test_thumbnail_returns_jpeg(client):
    asset = upload_asset(client)

    response = client.get(asset["thumbnail_url"])

    assert response.status_code == 200
    assert response.mimetype == "image/jpeg"
    Image.open(BytesIO(response.data)).verify()


def test_preview_returns_versioned_jpeg(client):
    asset = upload_asset(client)

    response = client.post(
        f"/api/assets/{asset['id']}/preview",
        json={
            "version": 12,
            "parameters": {
                "preset": "morning-light",
                "exposure": 0.2,
                "grain": 0.1,
            },
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "image/jpeg"
    assert response.headers["X-Preview-Version"] == "12"
    Image.open(BytesIO(response.data)).verify()


def test_asset_can_be_deleted(client):
    asset = upload_asset(client)

    response = client.delete(f"/api/assets/{asset['id']}")

    assert response.status_code == 204
    assert client.get(asset["thumbnail_url"]).status_code == 404


def test_user_cube_lut_can_be_uploaded(client):
    response = client.post(
        "/api/luts",
        data={"file": (BytesIO(IDENTITY_CUBE), "identity.cube")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert response.get_json()["lut"]["name"] == "identity.cube"
