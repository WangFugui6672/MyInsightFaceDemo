# 识别结果后端接口

本目录是 FastAPI + SQLite 后端，用于接收 `face_recog.py` 发送的人脸识别结果，并保存到本地数据库。

## 数据库存储位置

SQLite 数据库文件会自动创建在：

```text
mine/backend/data/recognition.db
```

该文件包含识别日志，可能涉及人员身份和时间记录，默认不应提交到 GitHub。

## 启动服务

先安装依赖：

```powershell
cd mine
python -m pip install -r requirements.txt
```

启动后端：

```powershell
cd mine
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/health
```

## 接口说明

### 提交识别结果

```http
POST /api/recognitions
```

请求示例：

```json
{
  "name": "张三",
  "score": 0.72,
  "status": "recognized",
  "camera_id": 0,
  "timestamp": "2026-06-05 14:30:22"
}
```

### 查看识别记录

```http
GET /api/recognitions?limit=50
```

### 查看最近一次识别结果

```http
GET /api/recognitions/latest
```

## 识别程序发送结果

先启动后端，然后运行：

```powershell
cd mine
python face_recog.py run --cam 0 --api http://127.0.0.1:8000/api/recognitions
```

默认同一个识别标签每 5 秒最多发送一次，避免摄像头每帧重复写入数据库。
