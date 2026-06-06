import shutil
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from uuid import uuid4


@dataclass(frozen=True)
class StoredAsset:
    id: str
    original_name: str
    media_type: str
    path: Path


class SessionStorage:
    _BUCKET_NAMES = ("inputs", "previews", "exports", "luts")

    def __init__(self, base_root):
        base = Path(base_root).expanduser().resolve()
        base.mkdir(parents=True, exist_ok=True)

        self.root = base / uuid4().hex
        self.root.mkdir(mode=0o700)
        for bucket in self._BUCKET_NAMES:
            path = self.root / bucket
            path.mkdir()
            setattr(self, bucket, path)

        self._assets = {}
        self._lock = RLock()

    def path_for(self, bucket, filename):
        if bucket not in self._BUCKET_NAMES:
            raise ValueError(f"unknown storage bucket: {bucket}")

        relative = Path(filename)
        if relative.is_absolute() or len(relative.parts) != 1:
            raise ValueError("filename must not contain a path")

        directory = getattr(self, bucket).resolve()
        candidate = (directory / relative).resolve()
        if not candidate.is_relative_to(directory):
            raise ValueError("path escapes the session directory")
        return candidate

    def store_input(self, original_name, media_type, data):
        safe_original_name = Path(str(original_name).replace("\\", "/")).name
        if not safe_original_name:
            safe_original_name = "unnamed"

        asset_id = uuid4().hex
        suffix = Path(safe_original_name).suffix.lower()
        if len(suffix) > 16:
            suffix = ""
        path = self.path_for("inputs", f"{asset_id}{suffix}")
        path.write_bytes(data)

        asset = StoredAsset(
            id=asset_id,
            original_name=safe_original_name,
            media_type=str(media_type or "application/octet-stream"),
            path=path,
        )
        with self._lock:
            self._assets[asset_id] = asset
        return asset

    def get_asset(self, asset_id):
        with self._lock:
            try:
                return self._assets[asset_id]
            except KeyError as error:
                raise KeyError(f"unknown asset: {asset_id}") from error

    def cleanup(self):
        with self._lock:
            self._assets.clear()
        shutil.rmtree(self.root, ignore_errors=True)
