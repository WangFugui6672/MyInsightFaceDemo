"""
InsightFace 摄像头实时人脸识别
用法:
  python face_recog.py register --folder known_faces
  python face_recog.py run --cam 0
"""
import argparse
import os
import time
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP = None
ROOT = SCRIPT_DIR                       # 模型根目录：mine/models/buffalo_l/
DB_PATH = os.path.join(SCRIPT_DIR, "face_db.npz")
SNAPSHOT_DIR = os.path.join(SCRIPT_DIR, "snapshots")
THRESHOLD = 0.4          # 余弦相似度阈值，>该值认为同一个人
IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def get_app():
    global APP
    if APP is None:
        APP = FaceAnalysis(
            name="buffalo_sc",                # 小模型：CPU 也快
            root=ROOT,
            providers=["CPUExecutionProvider"],
            allowed_modules=["detection", "recognition"],  # 只跑检测+识别，更快
        )
        APP.prepare(ctx_id=0, det_size=(320, 320))
    return APP


# ---------- 注册 ----------
def register(folder: str) -> None:
    app = get_app()
    if not os.path.isdir(folder):
        raise SystemExit(f"目录不存在: {folder}")

    db = {}  # name -> list of normalized embeddings
    for person in sorted(os.listdir(folder)):
        person_dir = os.path.join(folder, person)
        if not os.path.isdir(person_dir) or person.startswith(("_", ".")):
            continue

        embs = []
        for fname in sorted(os.listdir(person_dir)):
            if not fname.lower().endswith(IMG_EXTS):
                continue
            path = os.path.join(person_dir, fname)
            img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                print(f"  [skip] 读不到: {path}")
                continue
            faces = app.get(img)
            if not faces:
                print(f"  [skip] 没检测到人脸: {path}")
                continue
            face = max(
                faces,
                key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
            )
            emb = face.normed_embedding
            if emb is None:
                continue
            embs.append(emb)
            print(f"  + {person} <- {fname}  (det_score={face.det_score:.2f})")

        if not embs:
            print(f"[warn] {person} 没有任何可用人脸，跳过")
            continue
        mean = np.mean(np.stack(embs), axis=0)
        mean = mean / (np.linalg.norm(mean) + 1e-9)
        db[person] = mean
        print(f"[ok] {person} 注册 {len(embs)} 张，平均 embedding 维度 {mean.shape[0]}")

    if not db:
        raise SystemExit("人脸库为空，请先在 known_faces/<名字>/ 下放照片")

    names = np.array(list(db.keys()), dtype=object)
    embeddings = np.stack(list(db.values())).astype(np.float32)
    np.savez(DB_PATH, names=names, embeddings=embeddings)
    print(f"\n[done] 已保存 {DB_PATH}  共 {len(db)} 人")


# ---------- 实时识别 ----------
def run(cam_id: int, save_video: str = None) -> None:
    app = get_app()
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"未找到 {DB_PATH}，请先 register")

    data = np.load(DB_PATH, allow_pickle=True)
    names = data["names"]
    embeddings = data["embeddings"].astype(np.float32)
    print(f"[info] 加载人脸库 {len(names)} 人: {list(names)}")

    cap = cv2.VideoCapture(cam_id)
    if not cap.isOpened():
        raise SystemExit(f"无法打开摄像头 {cam_id}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    print(f"[info] 按 q 退出，按 s 保存当前帧到 {SNAPSHOT_DIR}/snapshot_时间戳.jpg")

    writer = None
    if save_video:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(save_video, fourcc, fps, (w, h))
        print(f"[info] 录制到 {save_video}")

    t0, frames, fps_disp = time.time(), 0, 0.0
    while True:
        ok, frame = cap.read()
        if not ok:
            print("[warn] 摄像头读取失败")
            break
        frames += 1

        faces = app.get(frame)
        for face in faces:
            box = face.bbox.astype(int)
            emb = face.normed_embedding
            label, score = "Unknown", 0.0
            if emb is not None:
                sims = embeddings @ emb
                best = int(np.argmax(sims))
                score = float(sims[best])
                if score >= THRESHOLD:
                    label = str(names[best])
            color = (0, 255, 0) if label != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
            txt = f"{label} {score:.2f}" if label != "Unknown" else f"Unknown ({score:.2f})"
            (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (box[0], box[1] - th - 8), (box[0] + tw, box[1]), color, -1)
            cv2.putText(frame, txt, (box[0], box[1] - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            if face.age is not None and face.gender is not None:
                g = "M" if int(face.gender) == 1 else "F"
                cv2.putText(frame, f"{g}/{int(face.age)}", (box[0], box[3] + 18),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        if frames % 10 == 0:
            fps_disp = frames / (time.time() - t0)
        cv2.putText(frame, f"FPS: {fps_disp:.1f}  faces: {len(faces)}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("InsightFace Recognition (q=quit, s=snapshot)", frame)
        if writer is not None:
            writer.write(frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("s"):
            path = os.path.join(SNAPSHOT_DIR, f"snapshot_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
            cv2.imwrite(path, frame)
            print(f"[snap] saved {path}")

    cap.release()
    if writer is not None:
        writer.release()
    cv2.destroyAllWindows()


# ---------- main ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    p_reg = sub.add_parser("register", help="从文件夹构建人脸库")
    p_reg.add_argument("--folder", default=os.path.join(SCRIPT_DIR, "known_faces"),
                       help="包含子目录的根目录（默认：脚本同目录的 known_faces）")
    p_run = sub.add_parser("run", help="打开摄像头实时识别")
    p_run.add_argument("--cam", type=int, default=0, help="摄像头设备 id，默认 0")
    p_run.add_argument("--save", default=None, help="可选：保存带标注的视频路径，如 out.mp4")
    args = parser.parse_args()

    if args.mode == "register":
        register(args.folder)
    elif args.mode == "run":
        run(args.cam, args.save)
