# InsightFace 本地人脸识别 Demo

基于 `deepinsight/insightface` 的本地人脸识别项目。项目默认使用本机摄像头完成检测、注册、实时识别，并可把识别结果写入本地 FastAPI + SQLite 后端网页。

所有相对路径默认以本目录 `mine/` 为基准。建议日常命令都先进入本目录：

```powershell
cd E:\XMUT\3down\人工智能\faceRecognition\mine
```

## 快速开始

### 方式一：Windows 双击脚本

适合演示、部署到同学或老师电脑、非开发环境。

1. 双击 `scripts/setup.bat` 安装依赖。
2. 把人脸照片放到 `known_faces/<人名>/`。
3. 双击 `scripts/run_register.bat` 生成人脸库。
4. 双击 `scripts/run_backend.bat` 打开后端网页。
5. 双击 `scripts/run_camera.bat` 开始摄像头识别。

后端网页地址：

```text
http://127.0.0.1:8000/
```

### 方式二：命令行

```powershell
python -m pip install -r requirements.txt
python face_recog.py register
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
python face_recog.py run --cam 0 --api http://127.0.0.1:8000/api/recognitions
```

如果摄像头打不开，尝试把 `--cam 0` 改成 `--cam 1` 或 `--cam 2`。

## 文档导航

| 文档 | 用途 |
| --- | --- |
| `docs/DEPLOY.md` | 把项目拷贝到其他 Windows 电脑时看这份 |
| `docs/FACE_RECOGNITION_TECH.md` | 讲解检测、embedding、人脸库、相似度阈值等技术原理 |
| `docs/AI_COURSE_FINAL_REPORT.md` | 人工智能基础课程期末项目说明和答辩材料 |
| `docs/chinese-rendering.md` | 说明为什么用 Pillow 绘制中文标签 |
| `backend/README.md` | 后端网页、SQLite 数据库和 API 接口说明 |
| `known_faces/README.md` | 人脸照片目录的放置规则 |

## 目录结构

```text
mine/
├── README.md
├── requirements.txt
├── face_recog.py              # 主程序：register / run
├── face_analysis_demo.py      # 单张图片分析 demo
├── test_recog_logic.py        # 无摄像头冒烟测试
├── scripts/                   # Windows 双击脚本
│   ├── setup.bat
│   ├── run_register.bat
│   ├── run_camera.bat
│   └── run_backend.bat
├── backend/                   # FastAPI 后端和网页
│   ├── main.py
│   ├── README.md
│   ├── static/
│   └── data/                  # recognition.db 自动生成
├── docs/
├── known_faces/               # 原始人脸照片
├── models/                    # 本地 ONNX 模型
├── samples/
└── snapshots/                 # 摄像头截图
```

上级目录里的 `reference/insightface/` 是官方源码参考树，不参与运行和部署。

## 常用命令

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

注册人脸库：

```powershell
python face_recog.py register
```

实时识别：

```powershell
python face_recog.py run --cam 0
```

启动后端网页：

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

实时识别并写入后端：

```powershell
python face_recog.py run --cam 0 --api http://127.0.0.1:8000/api/recognitions
```

离线冒烟测试：

```powershell
python test_recog_logic.py
```

单张图片 demo：

```powershell
python face_analysis_demo.py
```

## 人脸库规则

每个人一个子目录，目录名就是显示出来的人名：

```text
known_faces/
  张三/
    01.jpg
    02.jpg
  李四/
    front.png
  _unused/
    ignored.jpg
```

以 `_` 或 `.` 开头的目录会被忽略。每张图片建议只放一个人脸；如果图片里有多张脸，程序会取最大的人脸。

注册会覆盖生成 `face_db.npz`。增删人员后重新运行：

```powershell
python face_recog.py register
```

## 当前技术配置

| 项目 | 当前配置 |
| --- | --- |
| 模型包 | `buffalo_sc` |
| 执行后端 | `CPUExecutionProvider` |
| 启用模块 | `detection`, `recognition` |
| 检测尺寸 | `(320, 320)` |
| 相似度阈值 | `0.4` |
| 人脸库文件 | `face_db.npz` |
| 后端数据库 | `backend/data/recognition.db` |

如果需要更完整的原理说明，看 `docs/FACE_RECOGNITION_TECH.md`。

## 数据安全

以下内容可能包含人脸、身份或识别日志，不要提交到公开仓库，也不要随意上传：

| 数据 | 位置 |
| --- | --- |
| 原始人脸照片 | `known_faces/<人名>/` |
| 人脸特征库 | `face_db.npz` |
| 识别日志数据库 | `backend/data/recognition.db` |
| 摄像头截图 | `snapshots/` |
| 录像输出 | 运行命令时指定的 `--save` 路径 |

推理过程默认在本地运行，不会把摄像头画面或人脸照片发送到云端。首次缺少模型时，InsightFace 可能需要联网下载公开模型文件。

## 依赖

依赖以 `requirements.txt` 为准：

```text
insightface
opencv-python
Pillow
onnxruntime-directml
numpy
fastapi
uvicorn[standard]
python-multipart
```

当前代码强制使用 CPU 推理；即使安装了 `onnxruntime-directml`，也不会自动切换到 GPU。

## License & 致谢

- 项目代码：MIT
- 模型权重：遵循 InsightFace 官方许可，通常仅供非商业研究
- 上游参考：`../reference/insightface/`
