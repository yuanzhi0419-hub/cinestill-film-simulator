from io import BytesIO
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from flask import Blueprint, abort, current_app, request, send_file
from PIL import Image

from pineapple_film_lab.domain import EditParameters
from pineapple_film_lab.processing.cube import parse_cube
from pineapple_film_lab.processing.decode import DecodeError, decode_image
from pineapple_film_lab.processing.pipeline import process_image
from pineapple_film_lab.processing.presets import serialize_presets


api = Blueprint("api", __name__)


@api.get("/api/health")
def health():
    return {"status": "ok", "local_only": True}


@api.get("/api/presets")
def presets():
    return {"presets": serialize_presets()}


@api.post("/api/assets")
def upload_assets():
    files = [item for item in request.files.getlist("files") if item.filename]
    if not files:
        abort(400, description="请选择至少一张照片")

    decoded_files = []
    for uploaded in files:
        data = uploaded.read()
        try:
            image = decode_image(
                data,
                raw_temp_dir=_storage().root,
            )
        except DecodeError as error:
            abort(400, description=f"{uploaded.filename}: {error}")
        decoded_files.append((uploaded, data, image))

    assets = []
    for uploaded, data, image in decoded_files:
        asset = _storage().store_input(
            uploaded.filename,
            uploaded.mimetype,
            data,
        )
        thumbnail = _resize_for_preview(
            image,
            current_app.config["PREVIEW_MAX_EDGE"],
        )
        thumbnail_path = _storage().path_for(
            "previews",
            f"{asset.id}.jpg",
        )
        thumbnail_path.write_bytes(_encode_jpeg(thumbnail))
        assets.append(_asset_payload(asset, image))

    return {"assets": assets}, 201


@api.get("/api/assets/<asset_id>/thumbnail")
def asset_thumbnail(asset_id):
    _get_asset(asset_id)
    path = _storage().path_for("previews", f"{asset_id}.jpg")
    if not path.is_file():
        abort(404, description="缩略图不存在")
    return send_file(path, mimetype="image/jpeg")


@api.delete("/api/assets/<asset_id>")
def delete_asset(asset_id):
    try:
        _storage().remove_asset(asset_id)
    except KeyError:
        abort(404, description="照片不存在")
    return "", 204


@api.post("/api/assets/<asset_id>/preview")
def preview_asset(asset_id):
    asset = _get_asset(asset_id)
    payload = request.get_json(silent=True) or {}
    try:
        version = int(payload.get("version", 0))
        parameters = EditParameters.from_mapping(payload.get("parameters", {}))
        image = decode_image(
            asset.path.read_bytes(),
            raw_temp_dir=_storage().root,
        )
        image = _resize_for_preview(
            image,
            current_app.config["PREVIEW_MAX_EDGE"],
        )
        lut = _get_lut(parameters.lut_id)
        result = process_image(
            image,
            parameters,
            grain_seed=_stable_seed(asset_id),
            lut=lut,
        )
    except (ValueError, DecodeError) as error:
        abort(400, description=str(error))

    response = current_app.response_class(
        _encode_jpeg(result),
        mimetype="image/jpeg",
    )
    response.headers["X-Preview-Version"] = str(version)
    response.headers["Cache-Control"] = "no-store"
    return response


@api.post("/api/luts")
def upload_lut():
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        abort(400, description="请选择 .cube 文件")
    if Path(uploaded.filename).suffix.lower() != ".cube":
        abort(400, description="只支持 .cube 文件")

    data = uploaded.read()
    try:
        lut = parse_cube(data)
    except ValueError as error:
        abort(400, description=str(error))

    lut_id = uuid4().hex
    path = _storage().path_for("luts", f"{lut_id}.cube")
    path.write_bytes(data)
    safe_name = Path(uploaded.filename.replace("\\", "/")).name
    current_app.extensions["luts"][lut_id] = {
        "lut": lut,
        "name": safe_name,
        "path": path,
    }
    return {"lut": {"id": lut_id, "name": safe_name, "size": lut.size}}, 201


def _storage():
    return current_app.extensions["session_storage"]


def _get_asset(asset_id):
    try:
        return _storage().get_asset(asset_id)
    except KeyError:
        abort(404, description="照片不存在")


def _get_lut(lut_id):
    if lut_id is None:
        return None
    try:
        return current_app.extensions["luts"][lut_id]["lut"]
    except KeyError as error:
        raise ValueError("所选 LUT 不存在") from error


def _asset_payload(asset, image):
    return {
        "id": asset.id,
        "original_name": asset.original_name,
        "media_type": asset.media_type,
        "width": int(image.shape[1]),
        "height": int(image.shape[0]),
        "thumbnail_url": f"/api/assets/{asset.id}/thumbnail",
    }


def _resize_for_preview(image, max_edge):
    height, width = image.shape[:2]
    scale = min(1.0, float(max_edge) / max(height, width))
    if scale == 1.0:
        return image
    target = (max(1, round(width * scale)), max(1, round(height * scale)))
    return cv2.resize(image, target, interpolation=cv2.INTER_AREA)


def _encode_jpeg(image):
    pixels = np.clip(image * 255.0 + 0.5, 0, 255).astype(np.uint8)
    output = BytesIO()
    Image.fromarray(pixels, "RGB").save(
        output,
        format="JPEG",
        quality=current_app.config["JPEG_QUALITY"],
        optimize=True,
    )
    return output.getvalue()


def _stable_seed(value):
    return int(value[:8], 16)
