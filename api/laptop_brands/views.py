import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, File, Form, UploadFile, Request
from sqlalchemy.orm import Session

from core.db import get_db
from core.security import require_admin
from api.laptop_brands.models import LaptopBrand
from api.laptop_brands.schemas import LaptopBrandResponse

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


def register_laptop_brand_routes(app):

    @app.post("/laptop-brands/", response_model=LaptopBrandResponse, status_code=201, tags=["Laptop Brands"])
    def create_brand(
        request      : Request,
        name         : str = Form(...),
        slug         : str = Form(...),
        brand_image  : UploadFile | None = File(None),
        db           : Session = Depends(get_db),
        _=Depends(require_admin)
    ):
        if db.query(LaptopBrand).filter(LaptopBrand.slug == slug).first():
            raise HTTPException(400, "Slug already exists")
        if db.query(LaptopBrand).filter(LaptopBrand.name == name).first():
            raise HTTPException(400, "Brand name already exists")
        
        brand_img_url = _save_brand_image(brand_image, request)
        
        brand = LaptopBrand(name=name, slug=slug, brand_img_url=brand_img_url)
        db.add(brand)
        db.commit()
        db.refresh(brand)
        return brand

    @app.get("/laptop-brands/", response_model=list[LaptopBrandResponse], tags=["Laptop Brands"])
    def get_all_brands(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
        return db.query(LaptopBrand).offset(skip).limit(limit).all()

    @app.get("/laptop-brands/{brand_id}", response_model=LaptopBrandResponse, tags=["Laptop Brands"])
    def get_one_brand(brand_id: UUID, db: Session = Depends(get_db)):
        brand = db.query(LaptopBrand).filter(LaptopBrand.id == brand_id).first()
        if not brand:
            raise HTTPException(404, "Brand not found")
        return brand

    @app.patch("/laptop-brands/{brand_id}", response_model=LaptopBrandResponse, tags=["Laptop Brands"])
    def update_brand(
        brand_id     : UUID,
        request      : Request,
        name         : str | None = Form(None),
        slug         : str | None = Form(None),
        brand_image  : UploadFile | None = File(None),
        db           : Session = Depends(get_db),
        _=Depends(require_admin)
    ):
        brand = db.query(LaptopBrand).filter(LaptopBrand.id == brand_id).first()
        if not brand:
            raise HTTPException(404, "Brand not found")
        
        if name is not None: brand.name = name
        if slug is not None: brand.slug = slug
        
        if brand_image is not None:
            _delete_brand_image_file(brand.brand_img_url)
            brand.brand_img_url = _save_brand_image(brand_image, request)
            
        db.commit()
        db.refresh(brand)
        return brand

    @app.delete("/laptop-brands/{brand_id}", status_code=204, tags=["Laptop Brands"])
    def delete_brand(brand_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
        brand = db.query(LaptopBrand).filter(LaptopBrand.id == brand_id).first()
        if not brand:
            raise HTTPException(404, "Brand not found")
        
        # Also clean up the image file when deleting the brand
        _delete_brand_image_file(brand.brand_img_url)
            
        db.delete(brand)
        db.commit()