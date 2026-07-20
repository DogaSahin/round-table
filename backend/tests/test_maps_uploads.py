# backend/tests/test_maps_uploads.py
from __future__ import annotations

import io

import pytest
from PIL import Image

from app.modules.maps.uploads import (
    MAX_MAP_IMAGE_BYTES,
    MAX_TOKEN_IMAGE_BYTES,
    store_image,
    store_map_image,
    store_token_image,
)
from app.shared.errors import Validation


def _image_bytes(fmt: str, size: tuple[int, int] = (10, 10)) -> bytes:
    image = Image.new("RGB", size, color=(120, 60, 200))
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    return buf.getvalue()


def _solid_png_of_size(width: int, height: int) -> bytes:
    """A genuinely valid, decodable PNG whose byte size tracks its raw pixel
    size (compress_level=0 disables PNG's deflate compression, so a
    solid-color image doesn't collapse to a tiny file). Used to test the
    map/token size-cap boundary with a real image instead of garbage bytes."""
    image = Image.new("RGB", (width, height), color=(10, 20, 30))
    buf = io.BytesIO()
    image.save(buf, format="PNG", compress_level=0)
    return buf.getvalue()


@pytest.mark.parametrize(
    ("fmt", "ext"),
    [("PNG", "png"), ("JPEG", "jpg"), ("WEBP", "webp"), ("GIF", "gif")],
)
def test_store_image_accepts_valid_image_and_returns_dimensions(
    tmp_path, fmt: str, ext: str
) -> None:
    data = _image_bytes(fmt, size=(37, 21))

    rel_path, width, height = store_image(
        data, f"upload.{ext}", "maps", tmp_path, MAX_MAP_IMAGE_BYTES
    )

    assert width == 37
    assert height == 21
    assert rel_path.startswith("maps/")
    assert rel_path.endswith(f".{ext}")

    written = tmp_path / rel_path
    assert written.is_file()
    assert written.read_bytes() == data


def test_store_image_rejects_unsupported_extension(tmp_path) -> None:
    data = _image_bytes("PNG")

    with pytest.raises(Validation):
        store_image(data, "file.bmp", "maps", tmp_path, MAX_MAP_IMAGE_BYTES)


def test_store_image_rejects_non_image_extension(tmp_path) -> None:
    data = _image_bytes("PNG")

    with pytest.raises(Validation):
        store_image(data, "file.txt", "maps", tmp_path, MAX_MAP_IMAGE_BYTES)


def test_store_image_rejects_extensionless_filename(tmp_path) -> None:
    data = _image_bytes("PNG")

    with pytest.raises(Validation):
        store_image(data, "file", "maps", tmp_path, MAX_MAP_IMAGE_BYTES)


def test_store_image_rejects_oversized_bytes(tmp_path) -> None:
    oversized = b"x" * (MAX_MAP_IMAGE_BYTES + 1)

    with pytest.raises(Validation):
        store_image(oversized, "file.png", "maps", tmp_path, MAX_MAP_IMAGE_BYTES)


def test_store_image_rejects_unparseable_bytes_without_leaking_pillow_exception(tmp_path) -> None:
    garbage = b"not an image" * 100

    with pytest.raises(Validation):
        store_image(garbage, "file.png", "maps", tmp_path, MAX_MAP_IMAGE_BYTES)


def test_store_map_image_enforces_25mb_cap(tmp_path) -> None:
    oversized = b"x" * (MAX_MAP_IMAGE_BYTES + 1)

    with pytest.raises(Validation):
        store_map_image(oversized, "file.png", tmp_path)


def test_store_token_image_enforces_5mb_cap(tmp_path) -> None:
    oversized = b"x" * (MAX_TOKEN_IMAGE_BYTES + 1)

    with pytest.raises(Validation):
        store_token_image(oversized, "file.png", tmp_path)


def test_map_and_token_caps_are_enforced_differently(tmp_path) -> None:
    """A real, valid PNG sized between the token cap (5MB) and the map cap
    (25MB) is accepted by store_map_image but rejected by store_token_image —
    confirms the two functions enforce genuinely different limits, not just
    that each independently rejects something oversized for itself."""
    data = _solid_png_of_size(2200, 1600)
    assert MAX_TOKEN_IMAGE_BYTES < len(data) < MAX_MAP_IMAGE_BYTES

    rel_path, width, height = store_map_image(data, "big.png", tmp_path)
    assert width == 2200
    assert height == 1600
    assert (tmp_path / rel_path).is_file()

    with pytest.raises(Validation):
        store_token_image(data, "big.png", tmp_path)
