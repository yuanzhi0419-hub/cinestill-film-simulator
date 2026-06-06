from pathlib import Path


def test_required_release_files_exist():
    for name in [
        "LICENSE",
        "README.md",
        "CONTRIBUTING.md",
        "CLEAN_ROOM.md",
        "THIRD_PARTY_NOTICES.md",
        "Dockerfile",
    ]:
        assert Path(name).is_file()


def test_repository_contains_no_bundled_lut_or_xmp():
    forbidden = {".cube", ".xmp"}
    ignored_roots = {".git", ".venv", ".pytest_cache", "__pycache__"}
    repository_files = [
        path
        for path in Path(".").rglob("*")
        if path.is_file() and not ignored_roots.intersection(path.parts)
    ]

    assert not [
        path for path in repository_files if path.suffix.lower() in forbidden
    ]
