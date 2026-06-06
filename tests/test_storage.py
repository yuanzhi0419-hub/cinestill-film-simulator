import pytest

from pineapple_film_lab.storage.session import SessionStorage


def test_storage_creates_isolated_directories(tmp_path):
    storage = SessionStorage(tmp_path)

    assert storage.root.parent == tmp_path
    assert storage.inputs.exists()
    assert storage.previews.exists()
    assert storage.exports.exists()
    assert storage.luts.exists()


def test_storage_rejects_path_traversal(tmp_path):
    storage = SessionStorage(tmp_path)

    with pytest.raises(ValueError):
        storage.path_for("inputs", "../secret.jpg")


def test_storage_uses_generated_input_name_and_metadata(tmp_path):
    storage = SessionStorage(tmp_path)

    asset = storage.store_input(
        original_name="../../holiday photo.png",
        media_type="image/png",
        data=b"image bytes",
    )

    assert asset.original_name == "holiday photo.png"
    assert asset.path.parent == storage.inputs
    assert asset.path.name != "holiday photo.png"
    assert asset.path.read_bytes() == b"image bytes"
    assert storage.get_asset(asset.id) == asset


def test_cleanup_removes_session_only(tmp_path):
    marker = tmp_path / "keep.txt"
    marker.write_text("keep")
    storage = SessionStorage(tmp_path)
    root = storage.root

    storage.cleanup()
    storage.cleanup()

    assert not root.exists()
    assert marker.exists()
