import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.part_category.models import PartCategory
from api.part_specs.models import (
    PartSpecBattery,
    PartSpecCharger,
    PartSpecDisplay,
    PartSpecFan,
    PartSpecHDD,
    PartSpecRAM,
    PartSpecSSD,
    PartSpecThermal,
)
from api.part_specs.schemas import (
    BatterySpecCreate,
    ChargerSpecCreate,
    DisplaySpecCreate,
    FanSpecCreate,
    HDDSpecCreate,
    RAMSpecCreate,
    SSDSpecCreate,
    ThermalSpecCreate,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PART_IMAGE_DIR = PROJECT_ROOT / "media" / "part_images"
PART_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_HARDWARE_SPECS = {
    "ram": {"schema": RAMSpecCreate, "model": PartSpecRAM},
    "ssd": {"schema": SSDSpecCreate, "model": PartSpecSSD},
    "hdd": {"schema": HDDSpecCreate, "model": PartSpecHDD},
    "battery": {"schema": BatterySpecCreate, "model": PartSpecBattery},
    "display": {"schema": DisplaySpecCreate, "model": PartSpecDisplay},
    "charger": {"schema": ChargerSpecCreate, "model": PartSpecCharger},
    "fan": {"schema": FanSpecCreate, "model": PartSpecFan},
    "thermal": {"schema": ThermalSpecCreate, "model": PartSpecThermal},
}

HARDWARE_CATEGORY_ALIASES = {
    "ram": "ram",
    "memory": "ram",
    "ram-memory": "ram",
    "ssd": "ssd",
    "storage": "ssd",
    "ssd-storage": "ssd",
    "hdd": "hdd",
    "hard-drive": "hdd",
    "hard-disk": "hdd",
    "hdd-hard-drive": "hdd",
    "hdd-hard-disk": "hdd",
    "battery": "battery",
    "display": "display",
    "screen": "display",
    "display-screen": "display",
    "charger": "charger",
    "adapter": "charger",
    "power-adapter": "charger",
    "power-adapter-charger": "charger",
    "fan": "fan",
    "cooling-fan": "fan",
    "thermal": "thermal",
    "thermal-paste": "thermal",
}


def normalize_category_key(value: str) -> str:
    normalized = value.strip().lower().replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def save_part_image(file: UploadFile, request: Request) -> str:
    print(f"🔧 save_part_image called with file: {file.filename}, content_type: {file.content_type}")
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Product image must be an image file")

    ext = Path(file.filename or "").suffix.lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    if ext and ext not in allowed_exts:
        raise HTTPException(400, "Unsupported image format")

    filename = f"{uuid4()}{ext or '.jpg'}"
    destination = PART_IMAGE_DIR / filename
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"✅ Image saved successfully to: {destination}")
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        raise
    finally:
        file.file.close()
    
    url = str(request.url_for("media", path=f"part_images/{filename}"))
    print(f"📍 Generated image URL: {url}")
    return url


def delete_part_image_file(image_url: str | None) -> None:
    if not image_url:
        return

    parsed = urlparse(image_url)
    path = parsed.path if parsed.scheme else image_url
    if not path:
        return

    decoded_path = unquote(path)
    expected_prefix = "/media/part_images/"
    if not decoded_path.startswith(expected_prefix):
        return

    filename = decoded_path[len(expected_prefix):]
    file_path = PART_IMAGE_DIR / filename
    try:
        file_path.resolve().relative_to(PART_IMAGE_DIR.resolve())
    except ValueError:
        return

    if file_path.exists() and file_path.is_file():
        file_path.unlink()


def resolve_hardware_type(category: PartCategory) -> str:
    for key in (category.slug, category.name):
        normalized = normalize_category_key(key)
        if normalized in HARDWARE_CATEGORY_ALIASES:
            return HARDWARE_CATEGORY_ALIASES[normalized]

    supported = ", ".join(sorted(SUPPORTED_HARDWARE_SPECS.keys()))
    raise HTTPException(400, f"Unsupported hardware category. Supported types: {supported}")


def get_category(
    db: Session,
    category_id: UUID | None,
    category_slug: str | None,
) -> PartCategory:
    category = None
    if category_id is not None:
        category = db.query(PartCategory).filter(PartCategory.id == category_id).first()
    elif category_slug:
        category = db.query(PartCategory).filter(PartCategory.slug == category_slug).first()
        if category is None:
            category = db.query(PartCategory).filter(PartCategory.name.ilike(category_slug)).first()
    else:
        raise HTTPException(400, "Provide category_id or category_slug")

    if not category:
        raise HTTPException(404, "Category not found")
    return category


def payload_to_dict(payload):
    return payload.dict() if hasattr(payload, "dict") else payload.model_dump()


def parse_part_specs(raw_part_specs):
    if raw_part_specs is None:
        return None
    if isinstance(raw_part_specs, dict):
        return raw_part_specs
    if isinstance(raw_part_specs, str):
        if not raw_part_specs.strip():
            return None
        try:
            parsed = json.loads(raw_part_specs)
        except json.JSONDecodeError as exc:
            raise HTTPException(400, f"part_specs must be valid JSON: {exc.msg}") from exc
        if parsed is None:
            return None
        if not isinstance(parsed, dict):
            raise HTTPException(400, "part_specs must be a JSON object")
        return parsed
    raise HTTPException(400, "part_specs must be a JSON object")


def create_hardware_spec(
    db: Session,
    category: PartCategory,
    part_id: UUID,
    raw_part_specs: dict | None,
):
    if not raw_part_specs:
        return None

    hardware_type = resolve_hardware_type(category)
    spec_config = SUPPORTED_HARDWARE_SPECS[hardware_type]

    try:
        spec_payload = spec_config["schema"].parse_obj({
            **raw_part_specs,
            "part_id": part_id,
        })
    except ValidationError as exc:
        raise HTTPException(422, exc.errors()) from exc

    spec = spec_config["model"](**payload_to_dict(spec_payload))
    db.add(spec)
    return spec
