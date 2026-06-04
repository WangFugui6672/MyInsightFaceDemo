"""
InsightFace Face Analysis demo
- Detection + Alignment + Recognition (embedding) + Age/Gender
- Uses buffalo_l model pack, CPU
- Default input/output are under samples/ in the script directory
"""
import os
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(SCRIPT_DIR, "samples")
ROOT = SCRIPT_DIR                       # 模型根目录：mine/models/buffalo_l/
IMG_PATH = os.path.join(SAMPLES_DIR, "test_face.jpg")
OUT_PATH = os.path.join(SAMPLES_DIR, "test_face_result.jpg")


def draw_face(img, face):
    box = face.bbox.astype(int)
    cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)

    if face.kps is not None:
        for (x, y) in face.kps.astype(int):
            cv2.circle(img, (int(x), int(y)), 2, (0, 0, 255), -1)

    for lmk_key in ("landmark_3d_68", "landmark_2d_106"):
        lmk = getattr(face, lmk_key, None)
        if lmk is not None:
            for (x, y) in lmk[:, :2].astype(int):
                cv2.circle(img, (int(x), int(y)), 1, (255, 0, 0), -1)
            break

    label_parts = []
    if face.gender is not None and face.age is not None:
        g = "M" if int(face.gender) == 1 else "F"
        label_parts.append(f"{g}/{int(face.age)}")
    if face.det_score is not None:
        label_parts.append(f"score={face.det_score:.2f}")
    if face.embedding is not None:
        label_parts.append(f"emb={face.embedding.shape[0]}d")

    if label_parts:
        cv2.putText(img, " ".join(label_parts), (box[0], max(box[1] - 8, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)


def main():
    print("[INFO] Loading model buffalo_sc (CPU, fast)...")
    app = FaceAnalysis(
        name="buffalo_sc",
        root=ROOT,
        providers=["CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0, det_size=(320, 320))

    img = cv2.imdecode(np.fromfile(IMG_PATH, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(IMG_PATH)
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    print(f"[INFO] Input image shape: {img.shape}")

    print("[INFO] Running face analysis...")
    faces = app.get(img)
    print(f"[INFO] Detected {len(faces)} face(s)")

    for i, face in enumerate(faces):
        print(f"--- Face {i} ---")
        print(f"  bbox       = {face.bbox}")
        print(f"  det_score  = {face.det_score}")
        lmk_3d = getattr(face, "landmark_3d_68", None)
        lmk_2d = getattr(face, "landmark_2d_106", None)
        print(f"  kps(5pt)   = shape {None if face.kps is None else face.kps.shape}")
        print(f"  landmark_3d_68  = {None if lmk_3d is None else lmk_3d.shape}")
        print(f"  landmark_2d_106 = {None if lmk_2d is None else lmk_2d.shape}")
        print(f"  age        = {face.age}")
        print(f"  gender     = {face.gender}")
        print(f"  embedding  = shape {face.embedding.shape}, norm={np.linalg.norm(face.embedding):.4f}")
        draw_face(img, face)

    cv2.imencode(".jpg", img)[1].tofile(OUT_PATH)
    print(f"[INFO] Saved annotated image to {OUT_PATH}")


if __name__ == "__main__":
    main()
