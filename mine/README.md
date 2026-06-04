# InsightFace 本地人脸识别 Demo — 使用说明

> 基于 [deepinsight/insightface](https://github.com/deepinsight/insightface) 构建，**完全离线运行**，不向任何云端发送照片或人脸数据。

> **路径约定**：本文档中出现的所有相对路径都以 **`mine/`** 为基准。
> 例如 `face_recog.py` 指的是 `mine/face_recog.py`，`known_faces/` 指的是 `mine/known_faces/`，以此类推。
> 三个脚本内部都已用 `os.path.dirname(__file__)` 锚定到自身所在目录，**从任意位置调用都行**。

---

## 1. 项目简介

本项目使用 insightface 的 `buffalo_sc` 模型包（CPU 优化版，仅检测+识别）实现：

| 能力       | 说明                                                |
| ---------- | --------------------------------------------------- |
| 人脸检测   | RetinaFace-500MF，CPU 实时                          |
| 人脸识别   | MobileFaceNet @ 512 维 embedding，余弦相似度匹配    |
| 注册管理   | 从文件夹构建本地人脸库，存储为 `face_db.npz`        |
| 实时识别   | 打开本地摄像头，逐帧检测+识别+显示                  |

> **关键点定位 / 性别年龄**：`buffalo_sc` 不含这些模型。如需要请改用 `buffalo_s`（同等精度，+landmark+age）或 `buffalo_l`（精度更高，+landmark+age）。

---

## 2. 目录结构

```
planB/
├── README.md              # 顶层索引
│
├── mine/                  # ★ 我的项目（所有命令都在这里跑）
│   ├── README.md          # 本文档
│   ├── DEPLOY.md          # 部署到其他电脑的指南
│   ├── requirements.txt   # pip 依赖清单
│   ├── setup.bat          # 双击 ① 装依赖（一次性）
│   ├── run_register.bat   # 双击 ② 注册人脸
│   ├── run_camera.bat     # 双击 ③ 开摄像头
│   ├── face_recog.py      # 主程序：register / run 两个子命令
│   ├── face_analysis_demo.py
│   ├── test_recog_logic.py
│   ├── face_db.npz        # 生成产物：人脸库 embedding
│   ├── models/            # ★ ONNX 模型（跟项目走，~30 MB）
│   │   ├── buffalo_sc.zip
│   │   └── buffalo_sc/*.onnx
│   ├── known_faces/       # 人脸库根目录
│   │   ├── README.md
│   │   └── <人名>/<照片>
│   ├── samples/           # 测试用图片（test_face.jpg 等）
│   └── snapshots/         # 摄像头按 s 时存到这里
│
└── reference/             # 官方参考（只读，不参与部署）
    └── insightface/       # git clone 下来的原仓库
```

---

## 3. 环境要求

- Windows 10/11（已验证），macOS / Linux 理论可
- Python 3.10+（本机 3.14 已验证）
- 摄像头（运行 `run` 命令时需要）

---

## 4. 安装

```powershell
cd E:\XMUT\3down\人工智能\planB\mine

# 已安装：insightface 1.0.1、onnxruntime 1.26.0、opencv-python 4.13.0
# 换机器需重装：
python -m pip install insightface opencv-python onnxruntime numpy
```

**模型放在 `mine/models/` 下，跟项目走**（不进用户目录的 `~/.insightface/`）。

首次运行会自动从 GitHub 下载 `buffalo_l.zip`（约 288 MB）到
`mine/models/`，解压到 `mine/models/buffalo_l/*.onnx`。

> 下载不稳定时，可手动下载
> `https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip`
> 后解压到 `mine/models/`，再 `mine/models/buffalo_l.zip` 和 `buffalo_l/` 两个位置都要有。
>
> 想换到默认的 `~/.insightface/` 路径，把 `face_recog.py` 和 `face_analysis_demo.py` 里的
> `root=ROOT` 删掉、`ROOT = SCRIPT_DIR` 改成 `ROOT = os.path.expanduser('~/.insightface')` 即可。

---

## 5. 使用流程

> **给其他电脑用（不是开发者）？** → 看 [DEPLOY.md](DEPLOY.md)，三个 `.bat` 双击就能跑。

### 5.1 注册人脸库

在 `known_faces/` 下为每个人建一个子目录，目录名即该人的名字，把照片放进去：

```
mine/known_faces/
  张三/
      01.jpg        ← 支持 jpg/jpeg/png/bmp/webp
      02.jpg
  李四/
      front.png
  _unused/          ← 以 _ 或 . 开头的目录会被忽略
```

**照片建议**

- 每张图尽量只放一个人脸（多张脸时只取最大那张）
- 每人 1~5 张为宜，覆盖正面 / 侧面 / 不同光照
- 像素 ≥ 200，避免过度模糊

**执行注册**

```powershell
cd mine
python face_recog.py register
# 或者：python face_recog.py register --folder known_faces
# 绝对路径也行：python face_recog.py register --folder E:\...\mine\known_faces
```

输出示例：

```
  + 张三 <- 01.jpg  (det_score=0.91)
  + 张三 <- 02.jpg  (det_score=0.88)
[ok] 张三 注册 2 张，平均 embedding 维度 512
  + 李四 <- front.png  (det_score=0.95)
[ok] 李四 注册 1 张，平均 embedding 维度 512

[done] 已保存 mine\face_db.npz  共 2 人
```

注册完成会生成 `face_db.npz`（约 2.7 KB / 人）。要增删人：改文件夹后再跑一次即可（**会覆盖** `face_db.npz`）。

### 5.2 实时摄像头识别

```powershell
cd mine
python face_recog.py run --cam 0
```

**画面对照**

- 🟩 绿框 + 名字 + 相似度 → 已识别
- 🟥 红框 + `Unknown` + 相似度 → 未知
- 框下方：`M/35` 或 `F/28`（性别 / 年龄）
- 左上角：实时 FPS 与当前帧人脸数

**按键**

| 按键 | 作用                                  |
| ---- | ------------------------------------- |
| `q`  | 退出                                  |
| `s`  | 保存当前帧到 `snapshots/snapshot_时间戳.jpg` |

**可选：录像**

```powershell
python face_recog.py run --cam 0 --save out.mp4
# 视频默认保存在当前工作目录（建议 cd mine 后再跑）
```

### 5.3 单张图片分析（参考）

```powershell
cd mine
python face_analysis_demo.py
# 输入：mine\samples\test_face.jpg
# 输出：mine\samples\test_face_result.jpg
```

### 5.4 离线 / 无摄像头环境测试

```powershell
cd mine
python test_recog_logic.py
```

用 `samples/test_face.jpg` 模拟 3 帧输入，验证完整识别链路。

---

## 6. 关键参数

修改 `face_recog.py` 顶部常量 / `get_app()`：

| 变量           | 当前默认值                                       | 说明                                                 |
| -------------- | ------------------------------------------------ | ---------------------------------------------------- |
| `DB_PATH`      | `mine/face_db.npz`（自动锚定脚本目录）           | 注册库存储位置                                       |
| `SNAPSHOT_DIR` | `mine/snapshots/`（自动锚定脚本目录）            | `s` 键保存路径                                       |
| `THRESHOLD`    | `0.4`                                            | 余弦相似度阈值，>该值判为同一人；调高更严格         |
| `IMG_EXTS`     | jpg/jpeg/png/bmp/webp                            | 注册时接受的图片后缀                                 |
| `name`         | `"buffalo_sc"`                                   | 当前模型包（CPU 优化）                              |
| `providers`    | `["CPUExecutionProvider"]`                       | 当前执行后端                                          |
| `allowed_modules` | `["detection", "recognition"]`                 | 当前只跑检测+识别（提速关键）                       |
| `det_size`     | `(320, 320)`                                     | 检测输入尺寸（已用最小档）                          |

### 当前配置实测 FPS

| 人脸数/帧 | 延迟      | FPS  |
| --------- | --------- | ---- |
| 1         | ~150 ms   | ~6   |
| 3         | ~250 ms   | ~4   |
| 21（密集）| ~420 ms   | ~2.4 |

### 模型选择速查

| 模型包       | 检测       | 识别    | landmark | 性别年龄 | 体积   | CPU 速度 |
| ------------ | ---------- | ------- | -------- | -------- | ------ | -------- |
| `buffalo_l`  | RetinaFace-10GF | ResNet50@WebFace600K | ✅ | ✅ | 281 MB | 慢       |
| `buffalo_m`  | RetinaFace-2.5GF | ResNet50@WebFace600K | ✅ | ✅ | 270 MB | 中       |
| `buffalo_s`  | RetinaFace-500MF | MBF@WebFace600K      | ✅ | ✅ | 130 MB | 中       |
| `buffalo_sc` | RetinaFace-500MF | MBF@WebFace600K      | ❌ | ❌ |  16 MB | 快（**当前**）|

切换到更大的模型（需要 keypoint / 性别年龄时）：

```python
APP = FaceAnalysis(
    name="buffalo_s",                  # 换 s / l 都行
    root=ROOT,
    providers=["CPUExecutionProvider"],
    # 把 allowed_modules 删掉 → 跑全部子模型
)
APP.prepare(ctx_id=0, det_size=(480, 480))
```

---

## 7. 数据安全与隐私

| 项目              | 存储位置                                          | 是否敏感          | 建议                                       |
| ----------------- | ------------------------------------------------- | ----------------- | ------------------------------------------ |
| ONNX 模型         | `mine/models/buffalo_sc/*.onnx`                   | 否（公开模型）    | 公开仓库即可下载；已加入 `.gitignore`      |
| 原始人脸照片      | `mine/known_faces/<名字>/*.jpg`                   | **是**            | 不要上传到云盘 / 仓库 / 聊天群              |
| `face_db.npz`     | `mine/face_db.npz`                                | **是**            | 512 维向量，虽无法还原照片，但属生物特征     |
| `out.mp4` 录像    | 运行时所在目录（建议在 `mine/` 下运行）           | **是**            | 用完及时删除                               |
| `snapshot_*.jpg`  | `mine/snapshots/`                                 | **是**            | 同上                                       |

**网络行为**

- 唯一一次外网请求：首次加载模型时从 GitHub Releases 下载 `buffalo_sc.zip`
- 推理过程 0 网络请求
- 摄像头数据 0 网络请求

**自检方法**

1. 关闭 WiFi → 重新 `run` 摄像头，能正常用 → 确认无云依赖
2. 跑 demo 时监控：
   ```powershell
   Get-NetTCPConnection -OwningProcess (Get-Process python).Id
   ```
   应只看到本地连接

### 关于 GPU 加速（已知未启用）

- 已装 `onnxruntime-directml 1.24.4`（DirectX 12），但**当前未在用**——它的 DirectML.dll 版本太老，跑 SCRFD 在 RTX 5060 (Blackwell) 上崩
- 当前执行后端是 CPU，跑 buffalo_sc + 只跑检测+识别 + det=320
- 等网络好时，可手动替换 `onnxruntime/capi/DirectML.dll` 为最新版本（从 Microsoft NuGet 的 `Microsoft.AI.DirectML` 包取 `DirectML.dll`）
- 或装 CUDA toolkit + onnxruntime-gpu（重 ~3 GB）

---

## 8. 性能调优

| 现象                  | 调整                                                         |
| --------------------- | ------------------------------------------------------------ |
| CPU 卡顿（FPS 低）    | 当前已是 CPU 最快档（`buffalo_sc` + `det=320` + 只跑检测+识别）；想再快只能等 GPU |
| 误识别（不同人撞名）  | 提高 `THRESHOLD`（如 0.5）；增加每人注册张数；换更清晰样本   |
| 漏识别（识别不出）    | 降低 `THRESHOLD`（如 0.3）；检查 `face_db.npz` 是不是空的     |
| 需要关键点 / 性别年龄 | 换 `buffalo_s`（同精度 + landmark + age），删掉 `allowed_modules` |
| 摄像头打开失败        | 试 `--cam 1` 或 `2`；检查 Windows 隐私设置里是否允许应用访问摄像头 |
| `face_db.npz` 损坏    | 重新跑 `register` 即可覆盖                                   |
| 想用 GPU 加速         | 见 §7 末"关于 GPU 加速"                                      |

---

## 9. 常见问题

**Q: `face_db.npz` 里是什么？**
A: numpy 数组，包含 `names`（人名列表，object dtype）和 `embeddings`（float32，每行 512 维）。**不包含任何原始像素**。

**Q: 我可以传多张脸在同张照片里注册吗？**
A: 当前实现只取最大那张脸（脚本里 `max(..., key=lambda f: 面积)`）。一张图一人最稳。

**Q: 不在 `known_faces/` 里时 `run` 会怎样？**
A: 会立刻报错退出：`未找到 face_db.npz，请先 register`。

**Q: 怎么删除一个人？**
A: 在 `known_faces/` 里删掉对应目录，再 `register` 一次。

**Q: 录像 (`--save out.mp4`) 存在哪里？**
A: 存在**当前工作目录**（不是 `mine/`）。建议 `cd mine` 后再跑，文件就会落在 `mine/out.mp4`。

**Q: 三个脚本能跨目录调用吗？**
A: 可以。所有相对路径都锚定到脚本自身所在目录：
```powershell
python E:\XMUT\3down\人工智能\planB\mine\face_recog.py run --cam 0
```

**Q: InsightFace 1.0 那个 GUI 桌面程序 (`insightface-gui`) 和这个 CLI 什么关系？**
A: 它是官方提供的图形界面版本（带人脸库管理、报告、换脸试验），是另一个独立产品；本项目用的是同一个 Python 包，纯 CLI。

**Q: 商业用途能用吗？**
A: 代码是 MIT，但**模型权重是非商用**——见 insightface 的 LICENSE。商用要联系 `contact@insightface.ai`。

---

## 10. 命令速查

```powershell
# 推荐：先 cd 到 mine
cd E:\XMUT\3down\人工智能\planB\mine

# 注册（默认读取 mine/known_faces/）
python face_recog.py register

# 实时识别
python face_recog.py run --cam 0

# 录像
python face_recog.py run --cam 0 --save out.mp4

# 单图 demo（输入输出在 mine/samples/）
python face_analysis_demo.py

# 离线冒烟测试
python test_recog_logic.py
```

> 想从任意目录调用，传入绝对路径即可：
> ```powershell
> python E:\XMUT\3down\人工智能\planB\mine\face_recog.py run --cam 0 --folder E:\XMUT\3down\人工智能\planB\mine\known_faces
> ```

---

## 11. 依赖

```
insightface       == 1.0.1
onnxruntime       == 1.24.4    (via onnxruntime-directml)
opencv-python     == 4.13.0
numpy             == 2.4.4
```

`pip install insightface opencv-python onnxruntime-directml numpy` 即可一键装齐。

> 当前依赖的是 `onnxruntime-directml`（不装普通 `onnxruntime`）。如果未来想换 CUDA，把 `onnxruntime-directml` 换成 `onnxruntime-gpu` + 装 CUDA toolkit 即可。

---

## 12. License & 致谢

- 代码：MIT
- 模型权重：InsightFace 团队，仅供非商业研究
- 本项目：基于 `deepinsight/insightface` 仓库构建 demo
- 官方仓库快照位于 `../reference/insightface/`，仅作查阅参考
