# backend/app/modules/maps/uploads.py
from __future__ import annotations

import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.shared.errors import Validation

_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_MAP_IMAGE_BYTES = 25 * 1024 * 1024
MAX_TOKEN_IMAGE_BYTES = 5 * 1024 * 1024


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def store_image(
    data: bytes, filename: str, subdir: str, media_dir: Path, max_bytes: int
) -> tuple[str, int, int]:
    """Validate and persist an uploaded image. Returns (relative_path, width, height).
    Raises Validation on any problem — never a raw I/O or Pillow exception."""
    ext = _extension(filename)
    if ext not in _ALLOWED_EXTENSIONS:
        raise Validation("Unsupported image type.")
    if len(data) > max_bytes:
        raise Validation("Image too large.")

    dest_dir = media_dir / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_name = f"{uuid.uuid4().hex}.{ext}"
    dest_path = dest_dir / dest_name

    try:
        from io import BytesIO

        with Image.open(BytesIO(data)) as image:
            width, height = image.size
            image.verify()
    except UnidentifiedImageError as exc:
        raise Validation("Unreadable image.") from exc
    except (OSError, SyntaxError, ValueError) as exc:
        # Image.open() succeeding (header parses, .size is readable) does not guarantee
        # the pixel data is intact — .verify() can raise a range of exception types for
        # truncated/corrupt bytes depending on format and where the corruption is, not
        # just UnidentifiedImageError. Catch broadly here (this is the only place in the
        # call chain validating untrusted upload bytes) and translate all of it into the
        # same clean Validation error rather than leaking a raw Pillow/stdlib exception
        # as an unhandled 500.
        raise Validation("Unreadable image.") from exc

    dest_path.write_bytes(data)
    return f"{subdir}/{dest_name}", width, height


def store_map_image(data: bytes, filename: str, media_dir: Path) -> tuple[str, int, int]:
    return store_image(data, filename, "maps", media_dir, MAX_MAP_IMAGE_BYTES)


def store_token_image(data: bytes, filename: str, media_dir: Path) -> tuple[str, int, int]:
    return store_image(data, filename, "tokens", media_dir, MAX_TOKEN_IMAGE_BYTES)
