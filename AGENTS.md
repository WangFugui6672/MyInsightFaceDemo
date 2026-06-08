# AGENTS.md

## Scope
- Treat `mine/` as the project. Run normal commands from `mine/`; `reference/insightface/` is a cloned upstream reference tree and should stay read-only unless the user explicitly asks otherwise.
- Use `mine/README.md`, `mine/backend/README.md`, and `mine/docs/` for project-specific behavior and command details. There is currently no root-level `README.md`.
- Answer the user in Chinese unless they explicitly ask otherwise.
- Do not change files under `reference/insightface/`, generated slide/report artifacts, or sensitive face-data artifacts unless the user explicitly asks.

## Commands
- Install runtime deps: `cd mine && python -m pip install -r requirements.txt` or run `mine/scripts/setup.bat` on Windows.
- Rebuild the local face database after changing `known_faces/`: `cd mine && python face_recog.py register`.
- Start webcam recognition: `cd mine && python face_recog.py run --cam 0`; try `--cam 1`/`2` if the camera fails.
- Start the FastAPI dashboard/backend: `cd mine && python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`, then open `http://127.0.0.1:8000/`.
- Send recognition records to the backend while running the camera: `cd mine && python face_recog.py run --cam 0 --api http://127.0.0.1:8000/api/recognitions`.
- Windows helper scripts live in `mine/scripts/`: `setup.bat`, `run_register.bat`, `run_backend.bat`, and `run_camera.bat`.
- Focused no-camera smoke test: `cd mine && python test_recog_logic.py`. It requires `face_db.npz` and `samples/test_face.jpg`.
- Single-image demo: `cd mine && python face_analysis_demo.py`; it writes `samples/test_face_result.jpg`.

## Runtime Details
- The scripts anchor most project paths with `os.path.dirname(__file__)`, so absolute script invocation works, but `--save out.mp4` in `face_recog.py run` is relative to the current working directory.
- `face_recog.py` uses InsightFace `buffalo_sc`, `CPUExecutionProvider`, `allowed_modules=["detection", "recognition"]`, and `det_size=(320, 320)` for CPU speed.
- Models are loaded from `mine/models/` because `root=SCRIPT_DIR`; do not assume InsightFace's default `~/.insightface` cache.
- `register` overwrites `mine/face_db.npz`; ignored person folders start with `_` or `.` and each source image uses the largest detected face.
- The backend is FastAPI + SQLite in `mine/backend/`; static dashboard files live in `mine/backend/static/`, and recognition logs are stored in `mine/backend/data/recognition.db`.
- The dashboard can manage `known_faces/` entries and trigger `/api/register`; changing people or photos still requires rebuilding `face_db.npz`.

## Data And Artifacts
- `known_faces/`, `face_db.npz`, `snapshots/`, `backend/data/recognition.db`, videos, and generated sample outputs can contain sensitive face data; avoid committing, uploading, or exposing them.
- `mine/.gitignore` ignores model folders, `face_db.npz`, and `snapshots/`; keep large/sensitive runtime artifacts out of changes unless the user asks.
- `requirements.txt` currently installs `onnxruntime-directml`, but the app code forces CPU inference via `CPUExecutionProvider`.
- `models/` contains local ONNX model files and should be treated as large runtime assets.

## Verification
- There is no repo-wide lint/typecheck/test runner or CI config. Prefer the smallest relevant runtime check: `test_recog_logic.py` for recognition logic, `register` for database changes, or the webcam command only when camera access is needed.
- For backend-only changes, prefer importing/starting `backend.main` or checking the FastAPI endpoint locally; avoid camera tests unless the changed behavior depends on live capture.
- If Python commands fail because of Windows session/sandbox issues, report the environment error separately from code failures.
