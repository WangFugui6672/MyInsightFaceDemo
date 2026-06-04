# known_faces 人脸库

每个子目录 = 一个人，子目录名为该人的名字。
子目录中放该人的 1~N 张人脸图片（jpg/jpeg/png）。

```
known_faces/
  张三/
    01.jpg
    02.jpg
  李四/
    01.jpg
    side.jpg
  _example/      <- 前缀下划线的目录会被忽略
```

> 提示：尽量用 1~3 张高质量的正面照，覆盖不同光照/角度越多越好；
> 每张图中只放一个人脸效果最佳（多张脸只会用最大那张）。

注册：

```powershell
python face_recog.py register --folder known_faces
```

实时识别：

```powershell
python face_recog.py run --cam 0
```

按 `q` 退出，按 `s` 保存当前帧到 `snapshot_时间戳.jpg`。
