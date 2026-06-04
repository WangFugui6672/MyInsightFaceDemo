# planB — 本地人脸识别 Demo

基于 [deepinsight/insightface](https://github.com/deepinsight/insightface) 的**完全离线**人脸检测 / 识别 demo。

> **当前配置**：CPU + `buffalo_sc` + `det=320` + 只跑检测/识别
> 实测 FPS：1 张人脸 ~6，3 张 ~4，21 张密集 ~2.4
> 详见 `mine/README.md`

> 隐私：本项目**不上传任何数据到云端**。仅首次运行会从 GitHub 下载公开的 ONNX 模型。
> 详见 `mine/README.md` 的"数据安全与隐私"章节。

## 目录结构

```
planB/
├── mine/                 # 我的项目（所有命令都在这里跑）
│   ├── README.md         # 详细使用说明（看这个）
│   ├── face_recog.py     # 主程序：register / run
│   ├── face_analysis_demo.py
│   ├── test_recog_logic.py
│   ├── face_db.npz       # 人脸库 embedding
│   ├── models/           # ONNX 模型（buffalo_sc，跟项目走）
│   ├── known_faces/      # 人脸库图片（按人分子目录）
│   ├── samples/          # 测试图片
│   ├── snapshots/        # 摄像头快照（按 s 时生成）
│   └── .gitignore
│
└── reference/            # 官方参考（克隆自 GitHub，仅作查阅）
    └── insightface/      # git clone 下来的原仓库
```

## 快速开始

### 给自己用（命令行）
```powershell
cd mine
python face_recog.py register      # 注册
python face_recog.py run --cam 0   # 开摄像头
```

### 给别人用（不写代码）
直接拷贝 `mine/` 整个目录过去，对方双击：
1. `setup.bat` — 装依赖（一次性）
2. `run_register.bat` — 注册人脸
3. `run_camera.bat` — 开摄像头

详细步骤见 **[mine/DEPLOY.md](mine/DEPLOY.md)**

完整文档、参数说明、性能调优、数据安全 → **[mine/README.md](mine/README.md)**

## 三个 Python 脚本

| 脚本                        | 用途                       | 是否需要摄像头 |
| --------------------------- | -------------------------- | -------------- |
| `mine/face_recog.py`        | 主程序（注册 / 实时识别）  | 是（run 模式） |
| `mine/face_analysis_demo.py`| 单张图片分析 + 可视化      | 否             |
| `mine/test_recog_logic.py`  | 离线冒烟测试（无摄像头）   | 否             |

> 三个脚本都已用 `os.path.dirname(__file__)` 锚定到自身所在目录，
> 传入绝对路径也能从任意位置调用，例如：
> `python E:\XMUT\3down\人工智能\planB\mine\face_recog.py run --cam 0`

## 官方参考

`reference/insightface/` 是用 `git clone` 拉下来的官方仓库，**只读参考**，不要在里面写东西。常用入口：

- `reference/insightface/README.md` — 官方总览
- `reference/insightface/python-package/` — Python 包源码
- `reference/insightface/examples/` — 官方示例
- `reference/insightface/model_zoo/` — 模型清单
