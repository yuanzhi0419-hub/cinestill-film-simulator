# 凤梨罐头 FILM LAB Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 从零实现一个采用 MIT 许可证、本地运行、支持批量照片处理和会话内历史的独立胶片风格图像工具。

**Architecture:** 使用 Flask 应用工厂提供本地页面与 JSON 接口；图像解码、处理步骤、任务队列和临时存储分别封装。前端使用原生 HTML/CSS/JavaScript，预览走低分辨率同步请求，原尺寸导出走进程内后台队列。

**Tech Stack:** Python 3.11、Flask、Pillow、NumPy、OpenCV、rawpy、pytest、原生 HTML/CSS/JavaScript、Gunicorn、Docker

---

## 实施约束

- 只在 `/Users/apple/Documents/凤梨罐头 FILM LAB` 中工作。
- 不读取、复制或导入旧仓库的源码、页面、测试、LUT、XMP 和样片。
- 每项功能先写失败测试，再写最小实现。
- 每个任务完成后运行指定测试并独立提交。
- 内置预设必须使用原创名称和独立参数。
- 测试图片由测试代码动态生成，不引入来源不明的二进制样片。
- 第三方依赖及许可证记录在 `THIRD_PARTY_NOTICES.md`。

## 目标目录

```text
.
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── CLEAN_ROOM.md
├── THIRD_PARTY_NOTICES.md
├── Dockerfile
├── .dockerignore
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── run.py
├── pineapple_film_lab/
│   ├── __init__.py
│   ├── config.py
│   ├── routes.py
│   ├── domain.py
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── decode.py
│   │   ├── adjustments.py
│   │   ├── effects.py
│   │   ├── pipeline.py
│   │   ├── presets.py
│   │   └── cube.py
│   ├── jobs/
│   │   ├── __init__.py
│   │   └── queue.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── session.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── app.css
│       └── app.js
└── tests/
    ├── conftest.py
    ├── test_config.py
    ├── test_domain.py
    ├── test_storage.py
    ├── test_decode.py
    ├── test_adjustments.py
    ├── test_effects.py
    ├── test_pipeline.py
    ├── test_presets.py
    ├── test_cube.py
    ├── test_jobs.py
    └── test_routes.py
```

### Task 1: 建立全新开源项目骨架

**Files:**
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `README.md`
- Create: `CONTRIBUTING.md`
- Create: `CLEAN_ROOM.md`
- Create: `THIRD_PARTY_NOTICES.md`
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `pineapple_film_lab/__init__.py`
- Create: `pineapple_film_lab/config.py`
- Create: `run.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing configuration test**

```python
from pineapple_film_lab import create_app


def test_create_app_uses_local_upload_limit(tmp_path):
    app = create_app({
        "TESTING": True,
        "SESSION_ROOT": tmp_path,
        "MAX_CONTENT_LENGTH": 100 * 1024 * 1024,
    })

    assert app.config["TESTING"] is True
    assert app.config["MAX_CONTENT_LENGTH"] == 100 * 1024 * 1024
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest tests/test_config.py -v
```

Expected: FAIL because `pineapple_film_lab.create_app` does not exist.

**Step 3: Add project metadata and pinned dependencies**

`requirements.txt`:

```text
Flask==3.1.3
Pillow==12.2.0
numpy==2.4.6
opencv-python-headless==4.13.0.92
rawpy==0.27.0
gunicorn==26.0.0
```

`requirements-dev.txt`:

```text
-r requirements.txt
pytest==9.0.3
```

`pyproject.toml`:

```toml
[project]
name = "pineapple-film-lab"
version = "0.1.0"
description = "Local, privacy-preserving photo processing workbench."
requires-python = ">=3.11"
license = { text = "MIT" }

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 4: Implement the minimal app factory**

`pineapple_film_lab/__init__.py`:

```python
from flask import Flask

from .config import DefaultConfig


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(DefaultConfig)
    if overrides:
        app.config.update(overrides)
    return app
```

`pineapple_film_lab/config.py`:

```python
import tempfile
from pathlib import Path


class DefaultConfig:
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    SESSION_ROOT = Path(tempfile.gettempdir()) / "pineapple-film-lab"
    PREVIEW_MAX_EDGE = 1600
    JPEG_QUALITY = 92
```

`run.py`:

```python
from pineapple_film_lab import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
```

**Step 5: Write ownership and clean-room documents**

- `LICENSE`: standard MIT license with copyright holder `yuanzhi0419-hub`.
- `CLEAN_ROOM.md`: state that implementation is based only on the approved specification and excludes the previous repository and bundled third-party presets.
- `README.md`: describe local-only behavior, planned features, Python requirement, and development status.
- `CONTRIBUTING.md`: require contributors to certify they own submitted code/assets.
- `THIRD_PARTY_NOTICES.md`: list Flask, Pillow, NumPy, OpenCV, rawpy and Gunicorn with official project links and license names.
- `.gitignore`: ignore `.venv/`, `__pycache__/`, `.pytest_cache/`, coverage output, editor files, runtime sessions and exported images.

**Step 6: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_config.py -v
```

Expected: 1 passed.

**Step 7: Commit**

```bash
git add .
git commit -m "chore: establish clean-room project foundation"
```

### Task 2: 定义参数、资源和任务领域模型

**Files:**
- Create: `pineapple_film_lab/domain.py`
- Create: `tests/test_domain.py`

**Step 1: Write failing domain tests**

```python
import pytest

from pineapple_film_lab.domain import EditParameters, JobStatus


def test_parameters_reject_out_of_range_values():
    with pytest.raises(ValueError, match="exposure"):
        EditParameters.from_mapping({"exposure": 9})


def test_parameters_supply_stable_defaults():
    params = EditParameters.from_mapping({})
    assert params.exposure == 0.0
    assert params.preset_strength == 1.0
    assert params.grain == 0.0


def test_job_status_has_terminal_states():
    assert JobStatus.COMPLETED.is_terminal
    assert JobStatus.FAILED.is_terminal
    assert not JobStatus.RUNNING.is_terminal
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_domain.py -v
```

Expected: FAIL because `domain.py` does not exist.

**Step 3: Implement immutable validated models**

Create:

```python
from dataclasses import dataclass
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    DECODING = "decoding"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self):
        return self in {self.COMPLETED, self.FAILED, self.CANCELLED}


@dataclass(frozen=True)
class EditParameters:
    preset: str = "natural-negative"
    preset_strength: float = 1.0
    exposure: float = 0.0
    contrast: float = 0.0
    highlights: float = 0.0
    shadows: float = 0.0
    temperature: float = 0.0
    saturation: float = 0.0
    halation: float = 0.0
    grain: float = 0.0
    vignette: float = 0.0
    lut_id: str | None = None

    @classmethod
    def from_mapping(cls, values):
        allowed = set(cls.__dataclass_fields__)
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"unknown parameters: {', '.join(sorted(unknown))}")

        numeric_fields = allowed - {"preset", "lut_id"}
        normalized = dict(values)
        for name in numeric_fields & values.keys():
            normalized[name] = float(values[name])

        result = cls(**normalized)
        ranges = {
            "preset_strength": (0.0, 1.0),
            "exposure": (-3.0, 3.0),
            "contrast": (-1.0, 1.0),
            "highlights": (-1.0, 1.0),
            "shadows": (-1.0, 1.0),
            "temperature": (-1.0, 1.0),
            "saturation": (-1.0, 1.0),
            "halation": (0.0, 1.0),
            "grain": (0.0, 1.0),
            "vignette": (0.0, 1.0),
        }
        for name, (minimum, maximum) in ranges.items():
            value = getattr(result, name)
            if not minimum <= value <= maximum:
                raise ValueError(f"{name} must be between {minimum} and {maximum}")
        return result
```

Use explicit ranges:

```text
preset_strength: 0.0..1.0
exposure: -3.0..3.0
contrast/highlights/shadows/temperature/saturation: -1.0..1.0
halation/grain/vignette: 0.0..1.0
```

Unknown keys must raise `ValueError`, rather than being silently ignored.

**Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_domain.py -v
```

Expected: 3 passed.

**Step 5: Commit**

```bash
git add pineapple_film_lab/domain.py tests/test_domain.py
git commit -m "feat: add validated edit and job models"
```

### Task 3: 实现安全的临时会话存储

**Files:**
- Create: `pineapple_film_lab/storage/__init__.py`
- Create: `pineapple_film_lab/storage/session.py`
- Create: `tests/test_storage.py`

**Step 1: Write failing storage tests**

```python
from pathlib import Path

import pytest

from pineapple_film_lab.storage.session import SessionStorage


def test_storage_creates_isolated_directories(tmp_path):
    storage = SessionStorage(tmp_path)
    assert storage.root.parent == tmp_path
    assert storage.inputs.exists()
    assert storage.previews.exists()
    assert storage.exports.exists()


def test_storage_rejects_path_traversal(tmp_path):
    storage = SessionStorage(tmp_path)
    with pytest.raises(ValueError):
        storage.path_for("inputs", "../secret.jpg")


def test_cleanup_removes_session_only(tmp_path):
    marker = tmp_path / "keep.txt"
    marker.write_text("keep")
    storage = SessionStorage(tmp_path)
    root = storage.root
    storage.cleanup()
    assert not root.exists()
    assert marker.exists()
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_storage.py -v
```

Expected: FAIL because `SessionStorage` does not exist.

**Step 3: Implement session storage**

Requirements:

- Create a UUID-named directory under configured `SESSION_ROOT`.
- Create `inputs`, `previews`, `exports` and `luts`.
- Generate stored names from UUIDs, never directly from user filenames.
- Keep a small in-memory metadata mapping containing original filename, media type and paths.
- Resolve paths and verify `candidate.is_relative_to(session_root)`.
- Make `cleanup()` idempotent.
- Task 10 registers cleanup through the Flask application lifecycle; storage itself must never globally delete the configured root.

**Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_storage.py -v
```

Expected: 3 passed.

**Step 5: Commit**

```bash
git add pineapple_film_lab/storage tests/test_storage.py
git commit -m "feat: add isolated session storage"
```

### Task 4: 独立实现图片解码与标准化

**Files:**
- Create: `pineapple_film_lab/processing/__init__.py`
- Create: `pineapple_film_lab/processing/decode.py`
- Create: `tests/test_decode.py`

**Step 1: Write failing decoder tests**

Generate images in memory:

```python
from io import BytesIO

import numpy as np
from PIL import Image

from pineapple_film_lab.processing.decode import decode_image


def png_bytes(mode="RGB"):
    image = Image.new(mode, (8, 6), (20, 40, 60, 128) if mode == "RGBA" else (20, 40, 60))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_decode_png_returns_float_rgb():
    decoded = decode_image(png_bytes())
    assert decoded.shape == (6, 8, 3)
    assert decoded.dtype == np.float32
    assert 0.0 <= decoded.min() <= decoded.max() <= 1.0


def test_transparent_png_is_composited_on_neutral_background():
    decoded = decode_image(png_bytes("RGBA"), alpha_background=(0.5, 0.5, 0.5))
    assert decoded.shape == (6, 8, 3)
```

Add tests for invalid bytes, EXIF orientation and a mocked rawpy decoder.

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_decode.py -v
```

Expected: FAIL because decoder does not exist.

**Step 3: Implement decoder**

Requirements:

- Accept bytes, not arbitrary filesystem paths.
- Try Pillow first and call `ImageOps.exif_transpose`.
- Convert grayscale and palette images to RGB.
- Composite RGBA onto configurable neutral gray before RGB conversion.
- If Pillow cannot identify the image, write bytes to a `NamedTemporaryFile` scoped inside session storage and use `rawpy.imread`.
- RAW postprocess output must use camera white balance, 16-bit output and no automatic brightness.
- Convert all results to contiguous `float32` RGB arrays in range `0..1`.
- Raise a domain-specific `DecodeError` with safe user-facing messages.

**Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_decode.py -v
```

Expected: all decoder tests pass.

**Step 5: Commit**

```bash
git add pineapple_film_lab/processing tests/test_decode.py
git commit -m "feat: add independent image decoder"
```

### Task 5: 实现基础色调调整

**Files:**
- Create: `pineapple_film_lab/processing/adjustments.py`
- Create: `tests/test_adjustments.py`

**Step 1: Write failing mathematical tests**

```python
import numpy as np

from pineapple_film_lab.processing.adjustments import (
    apply_exposure,
    apply_tone,
    apply_temperature,
    apply_saturation,
)


def test_zero_adjustments_are_identity():
    image = np.full((4, 4, 3), 0.4, dtype=np.float32)
    result = apply_saturation(
        apply_temperature(
            apply_tone(apply_exposure(image, 0), 0, 0, 0),
            0,
        ),
        0,
    )
    np.testing.assert_allclose(result, image, atol=1e-6)


def test_positive_exposure_doubles_linear_values():
    image = np.full((1, 1, 3), 0.2, dtype=np.float32)
    np.testing.assert_allclose(apply_exposure(image, 1), 0.4, atol=1e-6)
```

Add monotonicity tests for contrast, highlights, shadows, temperature and saturation.

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_adjustments.py -v
```

Expected: FAIL because adjustment functions do not exist.

**Step 3: Implement the adjustment functions**

Independent definitions:

- Exposure: multiply linear RGB by `2 ** stops`.
- Contrast: smooth S-curve around middle gray, blended by signed strength.
- Highlights and shadows: luminance masks produced from smoothstep functions.
- Temperature: apply bounded red/blue gains while preserving mean luminance.
- Saturation: blend RGB with Rec.709 luminance; allow signed reduction or increase.
- Clip only at the public function boundary, not between every internal operation.

Each function:

- Accepts and returns `float32 RGB`.
- Does not mutate input.
- Validates finite values.

**Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_adjustments.py -v
```

Expected: all adjustment tests pass.

**Step 5: Commit**

```bash
git add pineapple_film_lab/processing/adjustments.py tests/test_adjustments.py
git commit -m "feat: implement base tone adjustments"
```

### Task 6: 实现原创光晕、颗粒和暗角效果

**Files:**
- Create: `pineapple_film_lab/processing/effects.py`
- Create: `tests/test_effects.py`

**Step 1: Write failing effect tests**

```python
import numpy as np

from pineapple_film_lab.processing.effects import add_grain, add_halation, add_vignette


def test_halation_only_changes_bright_neighborhood():
    image = np.zeros((31, 31, 3), dtype=np.float32)
    image[15, 15] = 1.0
    result = add_halation(image, amount=1.0)
    assert result[15, 16, 0] > image[15, 16, 0]
    assert result[0, 0].max() < 0.01


def test_grain_is_repeatable_with_seed():
    image = np.full((16, 16, 3), 0.5, dtype=np.float32)
    first = add_grain(image, amount=0.5, seed=7)
    second = add_grain(image, amount=0.5, seed=7)
    np.testing.assert_allclose(first, second)


def test_vignette_preserves_center_more_than_corner():
    image = np.ones((21, 21, 3), dtype=np.float32)
    result = add_vignette(image, amount=1.0)
    assert result[10, 10, 0] > result[0, 0, 0]
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_effects.py -v
```

Expected: FAIL because effects do not exist.

**Step 3: Implement independent effect definitions**

- Halation:
  1. Calculate luminance.
  2. Build a smooth high-luminance mask.
  3. Apply Gaussian blur using a radius derived from image dimensions.
  4. Tint energy with a warm red vector.
  5. Additively blend with a bounded amount.
- Grain:
  1. Create deterministic normal noise from a supplied seed.
  2. Scale noise by a luminance-dependent mask.
  3. Apply mostly monochrome noise with a small independent channel component.
- Vignette:
  1. Create a normalized elliptical distance field.
  2. Build a smooth radial attenuation mask.
  3. Multiply by a bounded strength.

Do not name or describe these effects as replicas of a commercial film stock.

**Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_effects.py -v
```

Expected: all effect tests pass.

**Step 5: Commit**

```bash
git add pineapple_film_lab/processing/effects.py tests/test_effects.py
git commit -m "feat: add original local film effects"
```

### Task 7: 定义自研预设和处理管线

**Files:**
- Create: `pineapple_film_lab/processing/presets.py`
- Create: `pineapple_film_lab/processing/pipeline.py`
- Create: `tests/test_presets.py`
- Create: `tests/test_pipeline.py`

**Step 1: Write failing preset and pipeline tests**

```python
import numpy as np

from pineapple_film_lab.domain import EditParameters
from pineapple_film_lab.processing.pipeline import process_image
from pineapple_film_lab.processing.presets import PRESETS


def test_expected_original_presets_exist():
    assert set(PRESETS) == {
        "night-walk",
        "morning-light",
        "natural-negative",
        "soft-haze",
        "documentary-bw",
    }


def test_default_pipeline_is_bounded_and_same_shape():
    image = np.full((24, 32, 3), 0.5, dtype=np.float32)
    result = process_image(image, EditParameters())
    assert result.shape == image.shape
    assert result.dtype == np.float32
    assert 0.0 <= result.min() <= result.max() <= 1.0
```

Add a monkeypatch test proving processing order:

```text
exposure -> tone -> temperature -> saturation -> halation -> grain -> vignette
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_presets.py tests/test_pipeline.py -v
```

Expected: FAIL because presets and pipeline do not exist.

**Step 3: Implement presets and processing order**

Represent each preset as an immutable `EditParameters` baseline. Merge the preset and user values by `preset_strength`, then apply the fixed processing order.

Independent starter values:

```python
PRESETS = {
    "night-walk": {"contrast": 0.18, "temperature": -0.08, "saturation": 0.08, "halation": 0.35, "grain": 0.18},
    "morning-light": {"exposure": 0.15, "contrast": -0.08, "temperature": 0.16, "highlights": -0.12, "grain": 0.08},
    "natural-negative": {"contrast": 0.06, "saturation": -0.05, "highlights": -0.08, "shadows": 0.05, "grain": 0.10},
    "soft-haze": {"contrast": -0.18, "highlights": -0.10, "shadows": 0.12, "halation": 0.16, "grain": 0.06},
    "documentary-bw": {"saturation": -1.0, "contrast": 0.20, "grain": 0.28, "vignette": 0.16},
}
```

**Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_presets.py tests/test_pipeline.py -v
```

Expected: all preset and pipeline tests pass.

**Step 5: Commit**

```bash
git add pineapple_film_lab/processing/presets.py pineapple_film_lab/processing/pipeline.py tests/test_presets.py tests/test_pipeline.py
git commit -m "feat: add original presets and processing pipeline"
```

### Task 8: 实现用户 `.cube` LUT 导入

**Files:**
- Create: `pineapple_film_lab/processing/cube.py`
- Create: `tests/test_cube.py`

**Step 1: Write failing parser tests**

Use inline text fixtures:

```python
import numpy as np
import pytest

from pineapple_film_lab.processing.cube import CubeLut, parse_cube


IDENTITY_2 = """
TITLE "Identity"
LUT_3D_SIZE 2
DOMAIN_MIN 0 0 0
DOMAIN_MAX 1 1 1
0 0 0
0 0 1
0 1 0
0 1 1
1 0 0
1 0 1
1 1 0
1 1 1
"""


def test_parse_identity_cube():
    lut = parse_cube(IDENTITY_2)
    assert lut.size == 2


def test_identity_cube_preserves_pixels():
    image = np.array([[[0.2, 0.4, 0.8]]], dtype=np.float32)
    result = parse_cube(IDENTITY_2).apply(image)
    np.testing.assert_allclose(result, image, atol=1e-5)


def test_parser_rejects_wrong_row_count():
    with pytest.raises(ValueError, match="row count"):
        parse_cube("LUT_3D_SIZE 2\n0 0 0")
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_cube.py -v
```

Expected: FAIL because cube support does not exist.

**Step 3: Implement constrained `.cube` parsing**

Requirements:

- Support only `LUT_3D_SIZE`, `DOMAIN_MIN`, `DOMAIN_MAX`, comments and RGB rows.
- Reject 1D LUTs in v1 with a clear message.
- Limit cube size to 64 and input text to 10 MB.
- Require exactly `size ** 3` rows.
- Reject non-finite values.
- Use trilinear interpolation.
- Keep uploaded LUTs in session storage and identify them by generated ID.
- Do not bundle third-party LUTs.

**Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_cube.py tests/test_pipeline.py -v
```

Expected: cube tests and existing pipeline tests pass.

**Step 5: Commit**

```bash
git add pineapple_film_lab/processing/cube.py tests/test_cube.py
git commit -m "feat: support user-provided cube luts"
```

### Task 9: 实现可取消的进程内任务队列

**Files:**
- Create: `pineapple_film_lab/jobs/__init__.py`
- Create: `pineapple_film_lab/jobs/queue.py`
- Create: `tests/test_jobs.py`

**Step 1: Write failing queue tests**

```python
from threading import Event

from pineapple_film_lab.domain import JobStatus
from pineapple_film_lab.jobs.queue import JobQueue


def test_queue_completes_job():
    queue = JobQueue(worker_count=1)
    job = queue.submit(lambda context: "done")
    finished = queue.wait(job.id, timeout=2)
    assert finished.status == JobStatus.COMPLETED
    assert finished.result == "done"
    queue.shutdown()


def test_job_failure_does_not_stop_next_job():
    queue = JobQueue(worker_count=1)
    failed = queue.submit(lambda context: 1 / 0)
    passed = queue.submit(lambda context: "ok")
    assert queue.wait(failed.id, 2).status == JobStatus.FAILED
    assert queue.wait(passed.id, 2).status == JobStatus.COMPLETED
    queue.shutdown()
```

Add cancellation, progress, retry and shutdown tests.

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_jobs.py -v
```

Expected: FAIL because queue does not exist.

**Step 3: Implement queue**

Requirements:

- Use `queue.Queue`, worker threads and locks.
- Store job ID, status, progress, result, safe error message and original callable.
- Provide `submit`, `get`, `wait`, `cancel`, `retry` and `shutdown`.
- Pass a context object exposing `cancelled` and `set_progress`.
- Cancellation is cooperative between processing stages.
- A failed callable must not terminate a worker.
- `shutdown` stops accepting jobs, signals workers, joins with timeout and leaves no non-daemon worker hanging.

**Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_jobs.py -v
```

Expected: all queue tests pass.

**Step 5: Commit**

```bash
git add pineapple_film_lab/jobs tests/test_jobs.py
git commit -m "feat: add in-process export queue"
```

### Task 10: 建立 Flask 上传、预览和资源接口

**Files:**
- Create: `pineapple_film_lab/routes.py`
- Create: `tests/conftest.py`
- Create: `tests/test_routes.py`
- Modify: `pineapple_film_lab/__init__.py`

**Step 1: Add app fixtures and failing route tests**

`tests/conftest.py`:

```python
import pytest

from pineapple_film_lab import create_app


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SESSION_ROOT": tmp_path,
        "MAX_CONTENT_LENGTH": 1024 * 1024,
    })
    yield app
    app.extensions["session_storage"].cleanup()


@pytest.fixture()
def client(app):
    return app.test_client()
```

Tests:

```python
def test_health(client):
    response = client.get("/api/health")
    assert response.get_json() == {"status": "ok", "local_only": True}


def test_upload_returns_asset_metadata(client, png_file):
    response = client.post(
        "/api/assets",
        data={"files": (png_file, "photo.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    assert response.get_json()["assets"][0]["original_name"] == "photo.png"
```

Add tests for multiple files, invalid bytes, empty upload, oversized request, thumbnail JPEG and deleting an asset.

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_routes.py -v
```

Expected: FAIL because routes are not registered.

**Step 3: Register application services**

In `create_app`:

- Create `SessionStorage`.
- Create `JobQueue`.
- Store both under `app.extensions`.
- Register blueprint.
- Register JSON handlers for 400, 404, 413 and 500.
- Register `atexit` cleanup for queue and session storage.

**Step 4: Implement routes**

Initial interface:

```text
GET    /api/health
GET    /api/presets
POST   /api/assets
GET    /api/assets/<asset_id>/thumbnail
DELETE /api/assets/<asset_id>
POST   /api/assets/<asset_id>/preview
POST   /api/luts
```

Preview request:

```json
{
  "version": 12,
  "parameters": {
    "preset": "natural-negative",
    "exposure": 0.2,
    "grain": 0.1
  }
}
```

Preview response must be JPEG bytes with `X-Preview-Version: 12`.

**Step 5: Run tests**

Run:

```bash
python -m pytest tests/test_routes.py -v
```

Expected: upload, thumbnail, preview and error tests pass.

**Step 6: Commit**

```bash
git add pineapple_film_lab/__init__.py pineapple_film_lab/routes.py tests/conftest.py tests/test_routes.py
git commit -m "feat: add local asset and preview api"
```

### Task 11: 实现原尺寸导出和 ZIP 下载

**Files:**
- Modify: `pineapple_film_lab/routes.py`
- Modify: `pineapple_film_lab/processing/pipeline.py`
- Modify: `tests/test_routes.py`

**Step 1: Write failing export tests**

Cover:

```text
POST /api/exports
GET  /api/jobs/<job_id>
POST /api/jobs/<job_id>/cancel
POST /api/jobs/<job_id>/retry
GET  /api/jobs/<job_id>/download
```

Representative test:

```python
def test_batch_export_returns_zip(client, uploaded_assets):
    response = client.post("/api/exports", json={
        "asset_ids": uploaded_assets,
        "parameters_by_asset": {
            asset_id: {"preset": "natural-negative"}
            for asset_id in uploaded_assets
        },
    })
    job_id = response.get_json()["job_id"]
    wait_for_job(client, job_id)
    download = client.get(f"/api/jobs/{job_id}/download")
    assert download.status_code == 200
    assert download.mimetype == "application/zip"
```

Add assertions that ZIP entries use safe generated output names and contain valid JPEG data.

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_routes.py -k export -v
```

Expected: FAIL because export endpoints do not exist.

**Step 3: Implement export workflow**

- Decode original bytes at export time.
- Process with the same `process_image` definition used by preview.
- Generate `original-stem-pineapple-film-lab.jpg`.
- For one asset, store JPEG and serve it directly.
- For multiple assets, create ZIP using generated output names.
- Update progress after each pipeline stage and each asset.
- Check cancellation between assets and major stages.
- Do not expose local filesystem paths in responses.

**Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_routes.py tests/test_jobs.py tests/test_pipeline.py -v
```

Expected: export, queue and pipeline tests pass.

**Step 5: Commit**

```bash
git add pineapple_film_lab/routes.py pineapple_film_lab/processing/pipeline.py tests/test_routes.py
git commit -m "feat: add queued jpeg and zip exports"
```

### Task 12: 构建暗房轻量工作台前端

**Files:**
- Create: `pineapple_film_lab/templates/index.html`
- Create: `pineapple_film_lab/static/app.css`
- Create: `pineapple_film_lab/static/app.js`
- Modify: `pineapple_film_lab/routes.py`
- Modify: `tests/test_routes.py`

**Step 1: Write failing page tests**

```python
def test_index_renders_local_workbench(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "凤梨罐头 FILM LAB" in body
    assert "所有处理均在本机完成" in body
    assert 'id="photo-input"' in body
    assert 'id="preview-canvas"' in body
    assert 'id="queue-strip"' in body
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_routes.py::test_index_renders_local_workbench -v
```

Expected: FAIL because `/` does not render a page.

**Step 3: Implement semantic page structure**

Required regions:

```text
header.app-toolbar
aside.preset-panel
main.preview-workspace
aside.adjustment-panel
section.queue-strip
div.status-region[aria-live=polite]
```

Required behavior:

- Drag/drop and file input support multiple files.
- First valid upload is selected automatically.
- Preset selection updates current asset.
- Slider and numeric input stay synchronized.
- Preview requests use a 180 ms debounce and monotonically increasing version.
- Ignore responses whose version is not the latest.
- Before/after modes: original, processed and draggable split.
- “应用到全部” copies current parameters to queued assets.
- Export, cancel, retry, remove and download controls call corresponding APIs.
- Errors are rendered inline and in the status region; no `alert()`.

**Step 4: Implement darkroom visual system**

CSS tokens:

```css
:root {
  --bg: #0c0d0d;
  --panel: #202220;
  --panel-raised: #292c29;
  --border: #444844;
  --text: #f2f0e8;
  --muted: #a4aaa4;
  --selected: #f0bd2d;
  --primary: #e4543e;
  --feedback: #58a9b8;
  --danger: #ed6a5a;
}
```

Layout:

- Desktop: fixed toolbar, `76px minmax(0, 1fr) 300px` workspace and stable queue height.
- Tablet: narrower preset rail and collapsible adjustment panel.
- Mobile: preview first; presets and adjustments in tabs; horizontal queue.
- Cards use at most 8px radius.
- Icon buttons use familiar symbols or an installed icon package only if added explicitly.
- Do not use decorative gradients or nested cards.

**Step 5: Run route tests**

Run:

```bash
python -m pytest tests/test_routes.py -v
```

Expected: all route tests pass.

**Step 6: Commit**

```bash
git add pineapple_film_lab/templates pineapple_film_lab/static pineapple_film_lab/routes.py tests/test_routes.py
git commit -m "feat: build darkroom photo workbench"
```

### Task 13: 浏览器验证并修复完整交互

**Files:**
- Modify as required: `pineapple_film_lab/templates/index.html`
- Modify as required: `pineapple_film_lab/static/app.css`
- Modify as required: `pineapple_film_lab/static/app.js`
- Create only if useful: `tests/browser/README.md`

**Step 1: Run the full automated suite**

Run:

```bash
python -m pytest -v
```

Expected: all tests pass.

**Step 2: Start local service**

Run:

```bash
python run.py
```

Expected: service available at `http://127.0.0.1:5000`.

**Step 3: Use @browser frontend testing workflow**

The flow under test is:

```text
app loads -> upload generated PNG files -> select preset -> adjust slider ->
split preview updates -> apply to all -> export -> download ZIP
```

Check:

- Page identity and meaningful content.
- No framework error overlay.
- No relevant browser console warnings or errors.
- Desktop viewport 1280×800.
- Mobile viewport 390×844.
- No clipping, overlap, text overflow or layout shifts.
- Preview updates after adjustment.
- Stale preview results do not replace newer ones.
- Batch progress is visible.
- Failed upload is shown inline.
- Remove, retry, cancel and download states work.

**Step 4: Fix only observed issues**

After each fix:

```text
reload -> repeat failing interaction -> verify DOM state -> capture screenshot
```

**Step 5: Rerun tests**

Run:

```bash
python -m pytest -v
```

Expected: all tests pass after UI fixes.

**Step 6: Commit**

```bash
git add pineapple_film_lab tests
git commit -m "fix: complete responsive workbench interactions"
```

### Task 14: 添加 Docker、启动说明和发布检查

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `THIRD_PARTY_NOTICES.md`
- Create: `tests/test_release_files.py`

**Step 1: Write failing release-file test**

```python
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
    tracked = [path for path in Path(".").rglob("*") if ".git" not in path.parts]
    assert not [path for path in tracked if path.suffix.lower() in forbidden]
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_release_files.py -v
```

Expected: FAIL until release files are complete.

**Step 3: Add container and documentation**

`Dockerfile`:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "4", "run:app"]
```

README must include:

- Project purpose and local privacy guarantee.
- Supported input and output formats.
- macOS/Linux and Windows setup.
- Exact start command.
- Docker build/run.
- Full usage flow.
- User LUT ownership warning.
- Testing commands.
- MIT license and clean-room link.

**Step 4: Verify local production server**

Run:

```bash
gunicorn --bind 127.0.0.1:7860 --workers 1 --threads 4 run:app
```

Verify:

```bash
curl --fail http://127.0.0.1:7860/api/health
```

Expected:

```json
{"local_only":true,"status":"ok"}
```

**Step 5: Verify Docker**

Run:

```bash
docker build -t pineapple-film-lab .
docker run --rm -p 7861:7860 pineapple-film-lab
curl --fail http://127.0.0.1:7861/api/health
```

Expected: image builds and health endpoint succeeds.

**Step 6: Run final checks**

Run:

```bash
python -m pytest -v
python -m compileall pineapple_film_lab tests
git grep -n -i -E "cinestill|zhirendashu|植人大树" -- . ':!docs/superpowers/specs/*' ':!docs/plans/*'
find . -type f \( -name '*.cube' -o -name '*.xmp' \) -not -path './.git/*'
git status --short
```

Expected:

- Tests pass.
- Compilation succeeds.
- Brand/source grep has no product-code matches.
- No bundled LUT/XMP files.
- Worktree contains only intentional release changes.

**Step 7: Commit**

```bash
git add .
git commit -m "docs: prepare first local release"
```

### Task 15: 最终验收和公开仓库准备

**Files:**
- Modify only if verification finds defects.

**Step 1: Review commit history**

Run:

```bash
git log --oneline --decorate --reverse
```

Expected: root design commit followed by small implementation commits; no imported old history.

**Step 2: Run clean-room source audit**

Run:

```bash
git ls-files
git grep -n -i -E "cinestill|zhirendashu|植人大树" -- \
  ':!docs/superpowers/specs/*' \
  ':!docs/plans/*'
git grep -n -E "Copyright|License|SPDX"
```

Expected:

- No old project branding in product code or UI.
- MIT ownership and third-party notices are explicit.
- No third-party media assets are tracked.

**Step 3: Run full acceptance**

Run:

```bash
python -m pytest -v
gunicorn --bind 127.0.0.1:7860 --workers 1 --threads 4 run:app
```

Browser acceptance:

```text
upload JPG + transparent PNG -> preview -> preset -> parameter adjustment ->
apply to all -> export -> ZIP download -> remove asset -> invalid-file error
```

Expected: all paths pass on desktop and mobile viewport.

**Step 4: Record release candidate**

Create an annotated tag only after user approval:

```bash
git tag -a v0.1.0 -m "凤梨罐头 FILM LAB v0.1.0"
```

Do not create or push a public GitHub repository without separate user confirmation.
