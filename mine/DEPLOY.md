# 部署到其他 Windows 电脑

> 目标机器：Windows 10/11，已装 Python 3.10+，能联网下 pip 包。

## 步骤 1：拷贝文件夹

把整个 `mine/` 文件夹复制到目标机器（U盘、网盘、共享文件夹都行）。

**整个 mine/ 大约 410 MB**（绝大部分是 `models/buffalo_sc/*.onnx` 约 62 MB + `models/buffalo_sc.zip` 约 67 MB，剩余来自其他依赖/输出）。

> ⚠️ **不需要**拷贝 `reference/insightface/`（那只是参考源码），也**不需要**拷贝 `planB/` 这一层。把 `mine/` 整个目录拷过去即可。

## 步骤 2：第一次运行 setup.bat

双击 `mine/setup.bat`：

```
[OK] Python 已安装
Python 3.14.0

[1/2] 升级 pip ...
[2/2] 安装依赖（insightface / opencv / onnxruntime-directml / numpy）...
...
[OK] 安装完成
下一步：双击 run_camera.bat 启动摄像头识别
```

大约 1~3 分钟（取决于网络）。

## 步骤 3：注册人脸

把要识别的人的照片放到 `mine/known_faces/<人名>/` 下，比如：

```
mine\known_faces\
  张三\
      01.jpg
  李四\
      01.jpg
```

双击 `mine/run_register.bat`，看到 `[done] 已保存 face_db.npz  共 X 人` 即成功。

> 第一次部署时，`face_db.npz` 已经包含你这边注册过的 3 个人（demo_person / hcj / 洪伟X），不需要再注册。可以直接进步骤 4。
> 想换人 → 改 `known_faces/` 后再跑 `run_register.bat`（会覆盖 `face_db.npz`）。

## 步骤 4：开摄像头

双击 `mine/run_camera.bat`：

```
正在打开摄像头 ...（按 q 退出，按 s 截图）

# 实时画面：绿框=认识，红框=Unknown，左上角 FPS
```

- 按 `q` 退出
- 按 `s` 截图存到 `mine/snapshots/`

## 常见部署问题

| 问题 | 解决 |
| --- | --- |
| 双击 setup.bat 闪退 | 右键 → 编辑，看不到内容是因为 console 关太快。改用 cmd 进入该目录运行 `setup.bat` 看报错 |
| 双击 .bat 时中文乱码 | `setup.bat` 顶部已加 `chcp 65001`；如果还乱码说明 Windows 不是中文版系统，需要把 bat 里所有中文改成英文 |
| Python 不在 PATH | 重新装 Python，安装时勾上"Add Python to PATH" |
| 摄像头打不开 | Windows 设置 → 隐私 → 摄像头 → 允许桌面应用访问摄像头 |
| 模型加载慢（首次） | 第一次会从 `models/` 加载 ONNX 到内存，后续秒开 |

## 文件清单

`mine/` 下需要一起拷贝的：

```
mine/
├── README.md
├── requirements.txt
├── setup.bat          ← 双击 ① 装依赖
├── run_register.bat   ← 双击 ② 注册人脸
├── run_camera.bat     ← 双击 ③ 开摄像头
├── face_recog.py
├── face_analysis_demo.py
├── test_recog_logic.py
├── face_db.npz        ← 人脸库
├── known_faces/       ← 源照片（可选，要不要带看隐私需求）
├── models/            ← ONNX 模型（62 MB）
│   └── buffalo_sc/
├── samples/
├── snapshots/
└── .gitignore
```

`known_faces/` 是可选的：
- **带上**：目标机器可以重训 / 增删人
- **不带**：只能用现成的 `face_db.npz`，不能再注册新的人

## 升级 / 重装

要彻底重装：
1. 删掉目标机器的 `mine/`
2. 重新拷贝一份新的过去
3. 重新跑 `setup.bat`
