from pathlib import Path

from fastapi.staticfiles import StaticFiles

from core.app import app
from api.register import register_routes

MEDIA_DIR = Path(__file__).resolve().parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# Register all module endpoints here
register_routes()
