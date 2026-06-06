from io import BytesIO
from time import monotonic, sleep
from zipfile import ZipFile

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


def wait_for_job(client, job_id, timeout=3):
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        job = response.get_json()["job"]
        if job["status"] in {"completed", "failed", "cancelled"}:
            return job
        sleep(0.01)
    raise AssertionError(f"job did not finish: {job_id}")


def test_health(client):
    response = client.get("/api/health")

    assert response.get_json() == {"status": "ok", "local_only": True}


def test_index_renders_local_workbench(client):
    response = client.get("/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "凤梨罐头 FILM LAB" in body
    assert "所有处理均在本机完成" in body
    assert 'id="photo-input"' in body
    assert 'id="preview-canvas"' in body
    assert 'id="queue-strip"' in body


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


def test_single_export_returns_jpeg(client):
    asset = upload_asset(client, name="portrait.png")
    response = client.post(
        "/api/exports",
        json={
            "asset_ids": [asset["id"]],
            "parameters_by_asset": {
                asset["id"]: {"preset": "natural-negative"}
            },
        },
    )

    assert response.status_code == 202
    job_id = response.get_json()["job_id"]
    assert wait_for_job(client, job_id)["status"] == "completed"
    download = client.get(f"/api/jobs/{job_id}/download")

    assert download.status_code == 200
    assert download.mimetype == "image/jpeg"
    assert "portrait-pineapple-film-lab.jpg" in download.headers[
        "Content-Disposition"
    ]
    Image.open(BytesIO(download.data)).verify()


def test_batch_export_returns_zip(client):
    first = upload_asset(client, name="first.png")
    second = upload_asset(client, name="second.png")
    asset_ids = [first["id"], second["id"]]
    response = client.post(
        "/api/exports",
        json={
            "asset_ids": asset_ids,
            "parameters_by_asset": {
                asset_id: {"preset": "natural-negative"}
                for asset_id in asset_ids
            },
        },
    )

    job_id = response.get_json()["job_id"]
    assert wait_for_job(client, job_id)["progress"] == 1.0
    download = client.get(f"/api/jobs/{job_id}/download")

    assert download.status_code == 200
    assert download.mimetype == "application/zip"
    with ZipFile(BytesIO(download.data)) as archive:
        assert archive.namelist() == [
            "first-pineapple-film-lab.jpg",
            "second-pineapple-film-lab.jpg",
        ]
        for name in archive.namelist():
            Image.open(BytesIO(archive.read(name))).verify()


def test_export_validates_assets_and_job_actions(client):
    missing = client.post(
        "/api/exports",
        json={"asset_ids": [], "parameters_by_asset": {}},
    )
    unknown_job = client.get("/api/jobs/missing")

    assert missing.status_code == 400
    assert unknown_job.status_code == 404


def test_completed_job_cannot_be_cancelled_or_retried(client):
    asset = upload_asset(client)
    response = client.post(
        "/api/exports",
        json={
            "asset_ids": [asset["id"]],
            "parameters_by_asset": {asset["id"]: {}},
        },
    )
    job_id = response.get_json()["job_id"]
    wait_for_job(client, job_id)

    assert client.post(f"/api/jobs/{job_id}/cancel").status_code == 409
    assert client.post(f"/api/jobs/{job_id}/retry").status_code == 400
