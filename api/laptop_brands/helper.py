from pathlib import Path
import shutil
from urllib.parse import unquote, urlparse
from uuid import uuid4
from fastapi import HTTPException, Request, UploadFile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRAND_IMAGE_DIR = PROJECT_ROOT / "media" / "brand_images"
BRAND_IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def _save_brand_image(file: UploadFile | None, request: Request) -> str | None:
    if file is None:
        return None

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Brand image must be an image file")

    ext = Path(file.filename or "").suffix.lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
    if ext and ext not in allowed_exts:
        raise HTTPException(400, "Unsupported image format")

    filename = f"{uuid4()}{ext or '.jpg'}"
    destination = BRAND_IMAGE_DIR / filename

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    return str(request.url_for("media", path=f"brand_images/{filename}"))


def _delete_brand_image_file(image_url: str | None) -> None:
    if not image_url:
        return

    parsed = urlparse(image_url)
    path = parsed.path if parsed.scheme else image_url
    if not path:
        return

    decoded_path = unquote(path)
    expected_prefix = "/media/brand_images/"
    if not decoded_path.startswith(expected_prefix):
        return

    filename = decoded_path[len(expected_prefix):]
    if not filename:
        return

    file_path = BRAND_IMAGE_DIR / filename
    try:
        file_path.resolve().relative_to(BRAND_IMAGE_DIR.resolve())
    except ValueError:
        return

    if file_path.exists() and file_path.is_file():
        file_path.unlink()