import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import UUID, uuid4
from fastapi import Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import Session
from core.security import (
    hash_password, verify_password,
    create_access_token, get_current_user, require_admin
)
from core.app import app
from core.db import get_db
from api.users.models import User
from api.users.schemas import (
    UserResponse, TokenResponse
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_IMAGE_DIR = PROJECT_ROOT / "media" / "profile_images"
PROFILE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def _save_profile_image(file: UploadFile | None, request: Request) -> str | None:
    if file is None:
        return None

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Profile image must be an image file")

    ext = Path(file.filename or "").suffix.lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    if ext and ext not in allowed_exts:
        raise HTTPException(400, "Unsupported image format")

    filename = f"{uuid4()}{ext or '.jpg'}"
    destination = PROFILE_IMAGE_DIR / filename

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    return str(request.url_for("media", path=f"profile_images/{filename}"))


def _delete_profile_image_file(image_url: str | None) -> None:
    if not image_url:
        return

    parsed = urlparse(image_url)
    path = parsed.path if parsed.scheme else image_url
    if not path:
        return

    decoded_path = unquote(path)
    expected_prefix = "/media/profile_images/"
    if not decoded_path.startswith(expected_prefix):
        return

    filename = decoded_path[len(expected_prefix):]
    if not filename:
        return

    file_path = PROFILE_IMAGE_DIR / filename
    try:
        file_path.resolve().relative_to(PROFILE_IMAGE_DIR.resolve())
    except ValueError:
        return

    if file_path.exists() and file_path.is_file():
        file_path.unlink()


# - for user register 
@app.post("/users/register", response_model=UserResponse, status_code=201, tags=["Users"])
def register(
    request      : Request,
    firstname    : str               = Form(...),
    lastname     : str               = Form(...),
    firstname_lc : str | None        = Form(None),
    lastname_lc  : str | None        = Form(None),
    username     : str               = Form(...),
    email        : EmailStr          = Form(...),
    phone_number : str               = Form(...),
    password     : str               = Form(...),
    profile_image: UploadFile | None = File(None),
    db           : Session           = Depends(get_db),
):

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email already registered")
    
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "Username already taken")
    
    if db.query(User).filter(User.phone_number == phone_number).first():
        raise HTTPException(400, "Phone number already used")

    profile_image_url = _save_profile_image(profile_image, request)
    normalized_firstname_lc = (firstname_lc or firstname).strip().lower()
    normalized_lastname_lc = (lastname_lc or lastname).strip().lower()

    user = User(

        firstname         = firstname,
        firstname_lc      = normalized_firstname_lc,
        lastname          = lastname,
        lastname_lc       = normalized_lastname_lc,
        username          = username,
        email             = email,
        phone_number      = phone_number,
        password_hash     = hash_password(password),
        profile_image_url = profile_image_url,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# - log in
@app.post("/users/login", response_model=TokenResponse, tags=["Users"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(User).filter(
        or_(User.email == form_data.username, User.username == form_data.username)
    ).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": user}

# - get current user
@app.get("/users/me", response_model=UserResponse, tags=["Users"])
def get_me(current_user=Depends(get_current_user)):
    return current_user

# - for User update profile
@app.patch("/users/me", response_model=UserResponse, tags=["Users"])
def update_me(
    request         : Request,
    firstname       : str | None        = Form(None),
    lastname        : str | None        = Form(None),
    firstname_lc    : str | None        = Form(None),
    lastname_lc     : str | None        = Form(None),
    username        : str | None        = Form(None),
    phone_number    : str | None        = Form(None),
    profile_image_url: str | None       = Form(None),
    profile_image   : UploadFile | None = File(None),
    db              : Session           = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if firstname is not None:
        user.firstname = firstname
        user.firstname_lc = (firstname_lc or firstname).strip().lower()
    elif firstname_lc is not None:
        user.firstname_lc = firstname_lc.strip().lower()

    if lastname is not None:
        user.lastname = lastname
        user.lastname_lc = (lastname_lc or lastname).strip().lower()
    elif lastname_lc is not None:
        user.lastname_lc = lastname_lc.strip().lower()

    if username is not None:
        if db.query(User).filter(User.username == username, User.id != user.id).first():
            raise HTTPException(400, "Username already taken")
        user.username = username

    if phone_number is not None:
        if db.query(User).filter(User.phone_number == phone_number, User.id != user.id).first():
            raise HTTPException(400, "Phone number already used")
        user.phone_number = phone_number

    if profile_image is not None:
        _delete_profile_image_file(user.profile_image_url)
        user.profile_image_url = _save_profile_image(profile_image, request)
    elif profile_image_url is not None:
        user.profile_image_url = profile_image_url

    db.commit()
    db.refresh(user)
    return user

# - for admin get all user
@app.get("/users", response_model=list[UserResponse], tags=["Users"])
def get_all(
    skip : int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    return db.query(User).offset(skip).limit(limit).all()

# - for admin get one user by id 
@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_one(
    user_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user

# - for admin delete user
@app.delete("/users/{user_id}", status_code=204, tags=["Users"])
def delete(
    user_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    _delete_profile_image_file(user.profile_image_url)
    db.delete(user)
    db.commit()
