# AGENTS.md

## Scope
- Treat `mine/` as the project. Run normal commands from `mine/`; `reference/insightface/` is a cloned upstream reference tree and should stay read-only unless the user explicitly asks otherwise.
- Root `README.md` is only an index; `mine/README.md` has the project-specific behavior and command details.

## Commands
- Install runtime deps: `cd mine && python -m pip install -r requirements.txt` or run `mine/setup.bat` on Windows.
- Rebuild the local face database after changing `known_faces/`: `cd mine && python face_recog.py register`.
- Start webcam recognition: `cd mine && python face_recog.py run --cam 0`; try `--cam 1`/`2` if the camera fails.
- Focused no-camera smoke test: `cd mine && python test_recog_logic.py`. It requires `face_db.npz` and `samples/test_face.jpg`.
- Single-image demo: `cd mine && python face_analysis_demo.py`; it writes `samples/test_face_result.jpg`.

## Runtime Details
- The scripts anchor most project paths with `os.path.dirname(__file__)`, so absolute script invocation works, but `--save out.mp4` in `face_recog.py run` is relative to the current working directory.
- `face_recog.py` uses InsightFace `buffalo_sc`, `CPUExecutionProvider`, `allowed_modules=["detection", "recognition"]`, and `det_size=(320, 320)` for CPU speed.
- Models are loaded from `mine/models/` because `root=SCRIPT_DIR`; do not assume InsightFace's default `~/.insightface` cache.
- `register` overwrites `mine/face_db.npz`; ignored person folders start with `_` or `.` and each source image uses the largest detected face.

## Data And Artifacts
- `known_faces/`, `face_db.npz`, `snapshots/`, videos, and generated sample outputs can contain sensitive face data; avoid committing, uploading, or exposing them.
- `mine/.gitignore` ignores model folders, `face_db.npz`, and `snapshots/`; keep large/sensitive runtime artifacts out of changes unless the user asks.
- `requirements.txt` currently installs `onnxruntime-directml`, but the app code forces CPU inference via `CPUExecutionProvider`.

## Verification
- There is no repo-wide lint/typecheck/test runner or CI config. Prefer the smallest relevant runtime check: `test_recog_logic.py` for recognition logic, `register` for database changes, or the webcam command only when camera access is needed.
