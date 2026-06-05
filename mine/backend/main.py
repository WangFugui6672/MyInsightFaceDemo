from datetime import datetime
from pathlib import Path
import sqlite3

from fastapi import FastAPI
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "recognition.db"

app = FastAPI(title="Face Recognition Backend", version="1.0.0")


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
