from io import BytesIO
from pathlib import Path
import re
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

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


@api.post("/api/exports")
def create_export():
    payload = request.get_json(silent=True) or {}
    asset_ids = payload.get("asset_ids")
    parameters_by_asset = payload.get("parameters_by_asset") or {}
    if not isinstance(asset_ids, list) or not asset_ids:
        abort(400, description="请选择至少一张照片")
    if len(set(asset_ids)) != len(asset_ids):
        abort(400, description="导出列表包含重复照片")

    assets = []
    parameter_sets = {}
    luts = {}
    try:
        for asset_id in asset_ids:
            asset = _get_asset(asset_id)
            parameters = EditParameters.from_mapping(
                parameters_by_asset.get(asset_id, {})
            )
            assets.append(asset)
            parameter_sets[asset_id] = parameters
            luts[asset_id] = _get_lut(parameters.lut_id)
    except (ValueError, DecodeError) as error:
        abort(400, description=str(error))

    storage = _storage()
    quality = current_app.config["JPEG_QUALITY"]
    export_id = uuid4().hex

    def export_work(context):
        outputs = []
        used_names = set()
        total = len(assets)
        for index, asset in enumerate(assets):
            if context.cancelled:
                return None
            image = decode_image(
                asset.path.read_bytes(),
                raw_temp_dir=storage.root,
            )
            context.set_progress((index + 0.25) / total)
            result = process_image(
                image,
                parameter_sets[asset.id],
                grain_seed=_stable_seed(asset.id),
                lut=luts[asset.id],
            )
            if context.cancelled:
                return None
            output_name = _unique_output_name(
                asset.original_name,
                used_names,
            )
            outputs.append((output_name, _encode_jpeg(result, quality)))
            context.set_progress((index + 1) / total)

        if len(outputs) == 1:
            name, data = outputs[0]
            path = storage.path_for("exports", f"{export_id}.jpg")
            path.write_bytes(data)
            return {
                "path": path,
                "download_name": name,
                "mimetype": "image/jpeg",
            }

        path = storage.path_for("exports", f"{export_id}.zip")
        with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
            for name, data in outputs:
                archive.writestr(name, data)
        return {
            "path": path,
            "download_name": "pineapple-film-lab-export.zip",
            "mimetype": "application/zip",
        }

    job = current_app.extensions["job_queue"].submit(export_work)
    return {"job_id": job.id}, 202


@api.get("/api/jobs/<job_id>")
def job_status(job_id):
    job = _get_job(job_id)
    return {"job": _job_payload(job)}


@api.post("/api/jobs/<job_id>/cancel")
def cancel_job(job_id):
    queue = current_app.extensions["job_queue"]
    _get_job(job_id)
    if not queue.cancel(job_id):
        abort(409, description="任务已经结束")
    return {"job": _job_payload(queue.get(job_id))}


@api.post("/api/jobs/<job_id>/retry")
def retry_job(job_id):
    queue = current_app.extensions["job_queue"]
    _get_job(job_id)
    try:
        retried = queue.retry(job_id)
    except ValueError as error:
        abort(400, description=str(error))
    return {"job_id": retried.id}, 202


@api.get("/api/jobs/<job_id>/download")
def download_job(job_id):
    job = _get_job(job_id)
    if job.status.value != "completed" or not isinstance(job.result, dict):
        abort(409, description="任务尚未完成")
    path = job.result["path"]
    if not path.is_file():
        abort(404, description="导出文件不存在")
    return send_file(
        path,
        mimetype=job.result["mimetype"],
        as_attachment=True,
        download_name=job.result["download_name"],
    )


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


def _get_job(job_id):
    try:
        return current_app.extensions["job_queue"].get(job_id)
    except KeyError:
        abort(404, description="任务不存在")


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


def _encode_jpeg(image, quality=None):
    pixels = np.clip(image * 255.0 + 0.5, 0, 255).astype(np.uint8)
    output = BytesIO()
    if quality is None:
        quality = current_app.config["JPEG_QUALITY"]
    Image.fromarray(pixels, "RGB").save(
        output,
        format="JPEG",
        quality=quality,
        optimize=True,
    )
    return output.getvalue()


def _stable_seed(value):
    return int(value[:8], 16)


def _job_payload(job):
    return {
        "id": job.id,
        "status": job.status.value,
        "progress": job.progress,
        "error": job.error,
        "download_url": (
            f"/api/jobs/{job.id}/download"
            if job.status.value == "completed" and isinstance(job.result, dict)
            else None
        ),
    }


def _unique_output_name(original_name, used_names):
    stem = Path(original_name.replace("\\", "/")).stem
    stem = re.sub(r"[^\w.-]+", "-", stem, flags=re.UNICODE).strip("._-")
    if not stem:
        stem = "photo"
    base = f"{stem}-pineapple-film-lab"
    candidate = f"{base}.jpg"
    number = 2
    while candidate in used_names:
        candidate = f"{base}-{number}.jpg"
        number += 1
    used_names.add(candidate)
    return candidate
