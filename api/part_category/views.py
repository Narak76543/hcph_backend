import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, File, Form, UploadFile, Request
from sqlalchemy.orm import Session

from api.part_category.models import PartCategory
from api.part_category.schemas import PartCategoryResponse
from core.app import app
from core.db import get_db
from core.security import require_admin

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATEGORY_IMAGE_DIR = PROJECT_ROOT / "media" / "category_images"
CATEGORY_IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def _save_category_image(file: UploadFile | None, request: Request) -> str | None:
    if file is None:
        return None

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Category image must be an image file")

    ext = Path(file.filename or "").suffix.lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
    if ext and ext not in allowed_exts:
        raise HTTPException(400, "Unsupported image format")

    filename = f"{uuid4()}{ext or '.jpg'}"
    destination = CATEGORY_IMAGE_DIR / filename

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    return str(request.url_for("media", path=f"category_images/{filename}"))


def _delete_category_image_file(image_url: str | None) -> None:
    if not image_url:
        return

    parsed = urlparse(image_url)
    path = parsed.path if parsed.scheme else image_url
    if not path:
        return

    decoded_path = unquote(path)
    expected_prefix = "/media/category_images/"
    if not decoded_path.startswith(expected_prefix):
        return

    filename = decoded_path[len(expected_prefix):]
    if not filename:
        return

    file_path = CATEGORY_IMAGE_DIR / filename
    try:
        file_path.resolve().relative_to(CATEGORY_IMAGE_DIR.resolve())
    except ValueError:
        return

    if file_path.exists() and file_path.is_file():
        file_path.unlink()


# ── CREATE (admin only) ────────────────────────────────────────────────

@app.post("/part-categories/", response_model=PartCategoryResponse, status_code=201, tags=["Part Categories"])
def create_category(
    request      : Request,
    name         : str = Form(...),
    slug         : str = Form(...),
    category_image: UploadFile | None = File(None),
    db           : Session = Depends(get_db),
    _=Depends(require_admin),
):
    if db.query(PartCategory).filter(PartCategory.slug == slug).first():
        raise HTTPException(400, "Slug already exists")
    if db.query(PartCategory).filter(PartCategory.name == name).first():
        raise HTTPException(400, "Category name already exists")

    part_category_img_url = _save_category_image(category_image, request)

    category = PartCategory(
        name=name,
        slug=slug,
        part_category_img_url=part_category_img_url
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# ── GET ALL (public) ───────────────────────────────────────────────────

@app.get("/part-categories/", response_model=list[PartCategoryResponse], tags=["Part Categories"])
def get_all_categories(
    skip : int     = 0,
    limit: int     = 20,
    db   : Session = Depends(get_db),
):
    return db.query(PartCategory).offset(skip).limit(limit).all()


# ── GET ONE (public) ───────────────────────────────────────────────────

@app.get("/part-categories/{category_id}", response_model=PartCategoryResponse, tags=["Part Categories"])
def get_one_category(
    category_id: UUID,
    db: Session = Depends(get_db),
):
    category = db.query(PartCategory).filter(PartCategory.id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")
    return category

@app.get("/part-categories/slug/{slug}", response_model=PartCategoryResponse, tags=["Part Categories"])
def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    category = db.query(PartCategory).filter(PartCategory.slug == slug).first()
    if not category:
        raise HTTPException(404, "Category not found")
    return category

# ── UPDATE (admin only) ────────────────────────────────────────────────

@app.patch("/part-categories/{category_id}", response_model=PartCategoryResponse, tags=["Part Categories"])
def update_category(
    category_id: UUID,
    request    : Request,
    name       : str | None = Form(None),
    slug       : str | None = Form(None),
    category_image: UploadFile | None = File(None),
    db         : Session = Depends(get_db),
    _=Depends(require_admin),
):
    category = db.query(PartCategory).filter(PartCategory.id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")

    if slug is not None and db.query(PartCategory).filter(PartCategory.slug == slug, PartCategory.id != category_id).first():
        raise HTTPException(400, "Slug already exists")
    if name is not None and db.query(PartCategory).filter(PartCategory.name == name, PartCategory.id != category_id).first():
        raise HTTPException(400, "Category name already exists")

    if name is not None: category.name = name
    if slug is not None: category.slug = slug

    if category_image is not None:
        _delete_category_image_file(category.part_category_img_url)
        category.part_category_img_url = _save_category_image(category_image, request)

    db.commit()
    db.refresh(category)
    return category


# ── DELETE (admin only) ────────────────────────────────────────────────

@app.delete("/part-categories/{category_id}", status_code=204, tags=["Part Categories"])
def delete_category(
    category_id: UUID,
    db         : Session = Depends(get_db),
    _=Depends(require_admin),
):
    category = db.query(PartCategory).filter(PartCategory.id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")

    _delete_category_image_file(category.part_category_img_url)

    db.delete(category)
    db.commit()
    return None