import tempfile
from pathlib import Path


class DefaultConfig:
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    SESSION_ROOT = Path(tempfile.gettempdir()) / "pineapple-film-lab"
    PREVIEW_MAX_EDGE = 1600
    JPEG_QUALITY = 92

