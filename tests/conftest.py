from io import BytesIO

import pytest
from PIL import Image

from pineapple_film_lab import create_app


def make_png_bytes(color=(30, 80, 140, 255), size=(12, 8)):
    image = Image.new("RGBA", size, color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


@pytest.fixture()
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SESSION_ROOT": tmp_path,
            "MAX_CONTENT_LENGTH": 1024 * 1024,
            "PREVIEW_MAX_EDGE": 64,
        }
    )
    yield app
    app.extensions["job_queue"].shutdown()
    app.extensions["session_storage"].cleanup()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def png_file():
    return BytesIO(make_png_bytes())

