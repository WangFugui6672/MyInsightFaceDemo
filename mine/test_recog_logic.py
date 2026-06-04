"""Smoke test for the recognition loop: feed a still image as if it were webcam frames."""
import os, sys, time, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import face_recog

app = face_recog.get_app()
data = np.load(face_recog.DB_PATH, allow_pickle=True)
names = data["names"]
embeddings = data["embeddings"].astype(np.float32)

img_path = os.path.join(os.path.dirname(__file__), "samples", "test_face.jpg")
img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
assert img is not None, f"test_face.jpg not found at {img_path}"

t0 = time.time()
n_total = 0
for i in range(3):
    faces = app.get(img)
    for f in faces:
        if f.normed_embedding is None:
            continue
        sims = embeddings @ f.normed_embedding
        idx = int(np.argmax(sims))
        s = float(sims[idx])
        label = str(names[idx]) if s >= face_recog.THRESHOLD else "Unknown"
        b = f.bbox.astype(int)
        sex = "M" if (f.gender is not None and int(f.gender) == 1) else "F"
        print("  bbox=({},{},{},{}) det={:.2f} age={} sex={} top1={} sim={:.3f}".format(
            b[0], b[1], b[2], b[3], float(f.det_score),
            int(f.age) if f.age is not None else -1,
            sex, label, s))
        n_total += 1
elapsed = time.time() - t0
print("Processed {} face-recognitions in {:.2f}s ({:.0f} ms/frame)".format(
    n_total, elapsed, elapsed/3*1000))
