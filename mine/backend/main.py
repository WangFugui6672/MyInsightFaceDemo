import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "recognition.db"

PROJECT_DIR = BASE_DIR.parent
KNOWN_FACES_DIR = PROJECT_DIR / "known_faces"
FACE_DB_PATH = PROJECT_DIR / "face_db.npz"
IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

app = FastAPI(title="Face Recognition Backend", version="1.0.0")

if KNOWN_FACES_DIR.is_dir():
    app.mount("/api/images", StaticFiles(directory=str(KNOWN_FACES_DIR)), name="faces")


class RecognitionCreate(BaseModel):
    name: str = Field(..., examples=["Unknown"])
    score: float = Field(..., ge=-1.0, le=1.0, examples=[0.72])
    status: str = Field(..., examples=["recognized"])
    camera_id: int = Field(..., examples=[0])
    timestamp: str | None = Field(None, examples=["2026-06-05 14:30:22"])


class RecognitionRecord(RecognitionCreate):
    id: int
    created_at: str


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recognition_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score REAL NOT NULL,
                status TEXT NOT NULL,
                camera_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_recognition_events_created_at
            ON recognition_events(created_at)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_recognition_events_name
            ON recognition_events(name)
            """
        )


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(BASE_DIR / "static" / "index.html"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "true", "database": str(DB_PATH)}


@app.post("/api/recognitions", response_model=RecognitionRecord)
def create_recognition(payload: RecognitionCreate) -> RecognitionRecord:
    event_time = payload.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO recognition_events
                (name, score, status, camera_id, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (payload.name, payload.score, payload.status, payload.camera_id, event_time, created_at),
        )
        event_id = int(cur.lastrowid)

    return RecognitionRecord(
        id=event_id,
        name=payload.name,
        score=payload.score,
        status=payload.status,
        camera_id=payload.camera_id,
        timestamp=event_time,
        created_at=created_at,
    )


@app.get("/api/recognitions", response_model=list[RecognitionRecord])
def list_recognitions(limit: int = 50) -> list[RecognitionRecord]:
    limit = max(1, min(limit, 200))
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name, score, status, camera_id, timestamp, created_at
            FROM recognition_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [RecognitionRecord(**dict(row)) for row in rows]


@app.get("/api/recognitions/latest", response_model=RecognitionRecord | None)
def latest_recognition() -> RecognitionRecord | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, name, score, status, camera_id, timestamp, created_at
            FROM recognition_events
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    return RecognitionRecord(**dict(row)) if row else None


# ---------- face database management ----------

def _list_persons() -> list[dict]:
    if not KNOWN_FACES_DIR.is_dir():
        return []
    result = []
    for entry in sorted(os.listdir(KNOWN_FACES_DIR)):
        person_dir = KNOWN_FACES_DIR / entry
        if not person_dir.is_dir() or entry.startswith(("_", ".")):
            continue
        images = sorted([
            f for f in os.listdir(person_dir)
            if f.lower().endswith(IMG_EXTS)
        ])
        result.append({
            "name": entry,
            "image_count": len(images),
            "images": images,
        })
    return result


@app.get("/api/persons")
def list_persons() -> list[dict]:
    return _list_persons()


@app.get("/api/persons/{name}")
def get_person(name: str) -> dict:
    person_dir = KNOWN_FACES_DIR / name
    if not person_dir.is_dir():
        return JSONResponse({"error": "person not found"}, status_code=404)
    images = sorted([
        f for f in os.listdir(person_dir)
        if f.lower().endswith(IMG_EXTS)
    ])
    return {"name": name, "image_count": len(images), "images": images}


@app.post("/api/persons")
async def create_person(name: str = Form(...), files: list[UploadFile] = File(default=[])) -> dict:
    person_dir = KNOWN_FACES_DIR / name
    if person_dir.exists():
        return JSONResponse({"error": "person already exists"}, status_code=409)
    person_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    for f in files:
        if f.filename:
            ext = Path(f.filename).suffix.lower()
            if ext not in IMG_EXTS:
                continue
            dest = person_dir / f"01{ext}"
            n = 1
            while dest.exists():
                n += 1
                dest = person_dir / f"{n:02d}{ext}"
            content = await f.read()
            dest.write_bytes(content)
            saved += 1
    return {"name": name, "images_saved": saved, "image_count": len(os.listdir(person_dir))}


@app.post("/api/persons/{name}/images")
async def upload_images(name: str, files: list[UploadFile] = File(...)) -> dict:
    person_dir = KNOWN_FACES_DIR / name
    if not person_dir.is_dir():
        return JSONResponse({"error": "person not found"}, status_code=404)
    saved = 0
    for f in files:
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in IMG_EXTS:
            ext = ".jpg"
        existing = [p for p in person_dir.iterdir() if p.suffix.lower() in IMG_EXTS]
        n = len(existing) + 1
        dest = person_dir / f"{n:02d}{ext}"
        while dest.exists():
            n += 1
            dest = person_dir / f"{n:02d}{ext}"
        content = await f.read()
        dest.write_bytes(content)
        saved += 1
    return {"name": name, "images_saved": saved}


@app.put("/api/persons/{name}/rename")
def rename_person(name: str, new_name: str = Form(...)) -> dict:
    old_dir = KNOWN_FACES_DIR / name
    new_dir = KNOWN_FACES_DIR / new_name
    if not old_dir.is_dir():
        return JSONResponse({"error": "person not found"}, status_code=404)
    if new_dir.exists():
        return JSONResponse({"error": "target name already exists"}, status_code=409)
    old_dir.rename(new_dir)
    return {"name": new_name, "register_needed": True, "message": "重命名成功，请点击「重新注册」更新人脸库"}


@app.delete("/api/persons/{name}")
def delete_person(name: str) -> dict:
    person_dir = KNOWN_FACES_DIR / name
    if not person_dir.is_dir():
        return JSONResponse({"error": "person not found"}, status_code=404)
    shutil.rmtree(person_dir)
    return {"deleted": name}


@app.delete("/api/persons/{name}/images/{filename}")
def delete_image(name: str, filename: str) -> dict:
    person_dir = KNOWN_FACES_DIR / name
    if not person_dir.is_dir():
        return JSONResponse({"error": "person not found"}, status_code=404)
    img_path = person_dir / filename
    if not img_path.exists():
        return JSONResponse({"error": "image not found"}, status_code=404)
    img_path.unlink()
    return {"deleted": filename}


@app.post("/api/register")
def register_database() -> dict:
    script = PROJECT_DIR / "face_recog.py"
    if not script.exists():
        return JSONResponse({"error": "face_recog.py not found"}, status_code=500)
    result = subprocess.run(
        [sys.executable, str(script), "register"],
        cwd=str(PROJECT_DIR),
        capture_output=True, text=True, timeout=60,
    )
    # Force UTF-8 decode for Chinese output
    if result.returncode != 0:
        return JSONResponse({"ok": False, "stdout": result.stdout, "stderr": result.stderr}, status_code=500)
    return {"ok": True, "message": result.stdout.strip().split("\n")[-1] if result.stdout.strip() else "ok"}
