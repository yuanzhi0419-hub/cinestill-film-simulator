from pineapple_film_lab import create_app


def test_create_app_uses_local_upload_limit(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SESSION_ROOT": tmp_path,
            "MAX_CONTENT_LENGTH": 100 * 1024 * 1024,
        }
    )

    assert app.config["TESTING"] is True
    assert app.config["MAX_CONTENT_LENGTH"] == 100 * 1024 * 1024
