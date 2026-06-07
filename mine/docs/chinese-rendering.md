# 中文文字渲染说明

## 问题

OpenCV 的 `cv2.putText()` 只支持 ASCII 字符（英文、数字、符号），无法渲染中文，显示为乱码或方框。

## 解决方案

用 **Pillow**（Python 图片处理库）代替 OpenCV 绘制中文文字。

## 流程

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ OpenCV 画面  │ ──► │ Pillow 图片  │ ──► │ OpenCV 画面  │
│  BGR 格式    │     │  RGB 格式    │     │  BGR 格式    │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                    ┌───────▼───────┐
                    │ ImageDraw     │
                    │ .text()       │
                    │ 使用中文字体  │
                    └───────────────┘
```

1. 加载 Windows 自带字体 `C:/Windows/Fonts/msyh.ttc`（微软雅黑）
2. 把 OpenCV 的 BGR 帧转成 Pillow 的 RGB 格式
3. 用 Pillow 的 `ImageDraw.text()` 在图片上绘制中文
4. 转回 BGR 格式写回原图

## 优化

- **纯英文文字**（如 `"Unknown"`、`"F/25"`、`"FPS: 30.1"`）→ 走原 `cv2.putText`，不经过 Pillow
- **含中文的文字**（如人名标签）→ 走 Pillow 渲染

避免每帧全图转换的开销。

## 相关代码位置

- `face_recog.py` 中的 `_put_text()` 和 `_text_size()` 函数
- 字体路径在 `_get_cv_font()` 中配置
