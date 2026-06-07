"""
InsightFace 摄像头实时人脸识别
用法:
  python face_recog.py register --folder known_faces
  python face_recog.py run --cam 0
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import insightface
from insightface.app import FaceAnalysis


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP = None
ROOT = SCRIPT_DIR                       # 模型根目录：mine/models/buffalo_l/
DB_PATH = os.path.join(SCRIPT_DIR, "face_db.npz")
SNAPSHOT_DIR = os.path.join(SCRIPT_DIR, "snapshots")
THRESHOLD = 0.4          # 余弦相似度阈值，>该值认为同一个人
IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def post_recognition(api_url: str, payload: dict) -> bool:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"[api warn] 发送识别结果失败: {exc}")
        return False


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


# ---------- 中文渲染 ----------
_FONT_CACHE = {}

def _get_cv_font(size=20):
    key = size
    if key not in _FONT_CACHE:
        for candidate in [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyhbd.ttc",
        ]:
            if os.path.exists(candidate):
                _FONT_CACHE[key] = ImageFont.truetype(candidate, size)
                break
        else:
            _FONT_CACHE[key] = None
    return _FONT_CACHE[key]


def _text_size(text, font_scale=0.6):
    font_size = max(14, int(font_scale * 32))
    if text.isascii():
        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
        return w, h
    font = _get_cv_font(font_size)
    if font is None:
        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
        return w, h
    left, top, right, bottom = font.getbbox(text)
    return right - left, bottom - top


def _put_text(img, text, pos, font_scale=0.6, color=(255, 255, 255), thickness=2):
    x, y = pos
    b, g, r = color
    if text.isascii():
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (b, g, r), thickness)
        return
    font_size = max(14, int(font_scale * 32))
    font = _get_cv_font(font_size)
    if font is None:
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (b, g, r), thickness)
        return
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    draw.text((x, y - font_size), text, font=font, fill=(r, g, b))
    img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


# ---------- 实时识别 ----------
def run(cam_id: int, save_video: str = None, api_url: str = None, api_interval: float = 5.0) -> None:
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

    last_sent = {}
    if api_url:
        print(f"[info] 识别结果将发送到 {api_url}，同一标签间隔 {api_interval:.1f}s")

    def _confidence_color(score: float):
        if score >= THRESHOLD:
            return (0, 255, 0)
        elif score >= 0.3:
            return (0, 200, 255)
        return (0, 0, 255)

    def _draw_info_panel(img, lines, position=(10, 30), line_h=22):
        x, y = position
        for i, line in enumerate(lines):
            cv2.putText(img, line, (x, y + i * line_h),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    paused = False
    show_help = False
    flash_frame = None
    db_size = len(names)

    t0, frames, fps_disp = time.time(), 0, 0.0
    while True:
        if not paused:
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
                color = _confidence_color(score)

                if api_url:
                    now = time.time()
                    key = (label, cam_id)
                    if now - last_sent.get(key, 0.0) >= api_interval:
                        payload = {
                            "name": label,
                            "score": score,
                            "status": "recognized" if label != "Unknown" else "unknown",
                            "camera_id": cam_id,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        if post_recognition(api_url, payload):
                            last_sent[key] = now

                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                txt = f"{label} {score:.2f}" if label != "Unknown" else f"Unknown ({score:.2f})"
                tw, th = _text_size(txt, 0.6)
                cv2.rectangle(frame, (box[0], box[1] - th - 10), (box[0] + tw + 6, box[1]), color, -1)
                _put_text(frame, txt, (box[0] + 3, box[1] - 6), 0.6, (0, 0, 0))

                if face.age is not None and face.gender is not None:
                    g = "M" if int(face.gender) == 1 else "F"
                    _put_text(frame, f"{g}/{int(face.age)}", (box[0], box[3] + 4), 0.5, color, 1)

            if frames % 10 == 0:
                fps_disp = frames / (time.time() - t0)

            # copy for paused overlay
            flash_frame = frame.copy()

        # --- always draw HUD (even when paused) ---
        disp = flash_frame if paused and flash_frame is not None else frame
        ov = disp.copy()

        # semi-transparent top bar
        cv2.rectangle(ov, (0, 0), (disp.shape[1], 85), (0, 0, 0), -1)
        disp = cv2.addWeighted(disp, 0.7, ov, 0.3, 0)

        api_status = f"API {'Connected' if api_url else 'Off'}"
        pause_tag = "  [PAUSED]" if paused else ""
        info_lines = [
            f"Personnel: {db_size}  |  FPS: {fps_disp:.1f}  |  Faces: {len(faces)}  |  {api_status}{pause_tag}",
            "[H] Help  [Q] Quit  [S] Snapshot  [P] Pause",
        ]
        _draw_info_panel(disp, info_lines)

        # help overlay
        if show_help:
            help_y = disp.shape[0] - 130
            cv2.rectangle(ov, (10, help_y - 10), (400, help_y + 100), (0, 0, 0), -1)
            disp = cv2.addWeighted(disp, 0.6, ov, 0.4, 0)
            help_text = [
                "Q / ESC  Quit",
                "S         Save snapshot",
                "P         Pause / Resume",
                "H         Toggle this help",
                "",
                "demo by InsightFace",
            ]
            for i, line in enumerate(help_text):
                cv2.putText(disp, line, (25, help_y + i * 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255) if line else (100, 100, 100), 1)

        cv2.imshow("InsightFace Recognition", disp)
        if writer is not None and not paused:
            writer.write(frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("s") and flash_frame is not None:
            path = os.path.join(SNAPSHOT_DIR, f"snapshot_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
            cv2.imwrite(path, flash_frame)
            print(f"[snap] saved {path}")
        if key == ord("p"):
            paused = not paused
            print(f"[info] {'Paused' if paused else 'Resumed'}")
        if key == ord("h"):
            show_help = not show_help

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
    p_run.add_argument("--api", default=None, help="可选：识别结果 POST 接口，如 http://127.0.0.1:8000/api/recognitions")
    p_run.add_argument("--api-interval", type=float, default=5.0, help="同一标签发送间隔秒数，默认 5")
    args = parser.parse_args()

    if args.mode == "register":
        register(args.folder)
    elif args.mode == "run":
        run(args.cam, args.save, args.api, args.api_interval)
