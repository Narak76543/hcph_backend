from pathlib import Path

from fastapi import Request
from fastapi.staticfiles import StaticFiles

from core.app import app
from api.register import register_routes

MEDIA_DIR = Path(__file__).resolve().parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# Register all module endpoints here
register_routes()

@app.get("/{full_path:path}", include_in_schema=False)
async def catch_all(request: Request, full_path: str):
    print(f"!!!!!!!!!! DEBUG: 404 CATCH-ALL ROUTE HIT !!!!!!!!!!! -> /{full_path}")
    return {"detail": f"Not Found: The server doesn't have a route for /{full_path}"}
