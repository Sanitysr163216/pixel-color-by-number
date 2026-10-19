"""
AI 辅助：用 Apple 的 Vision 框架分析照片。

Vision 是 macOS 和 iOS 自带的 AI 功能，在本机离线运行，不用下载模型，也不用花钱。
这里用到它的三个能力：
- 显著区域：一张图里人眼最先注意到的地方
- 人脸和五官：眼睛、瞳孔、眉毛、鼻子、嘴唇的位置
- 主体分割：把人、动物或物体从背景里分出来

分析结果交给 converter.convert()：
- importance（重要程度）：人脸、五官、显著区域分到更多颜色，也不会被当成杂色点清理掉
- subject（主体遮罩）：可以把主体以外的背景虚化，让颜色集中在主体上

只有 macOS 上装了 pyobjc 才能用；其他系统 available() 返回 False，游戏照常工作。
"""

import io
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

try:
    import objc
    import Quartz
    import Vision
    from Foundation import NSData
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

# 这些五官区域的格子最重要
FEATURES = ("leftEye", "rightEye", "leftPupil", "rightPupil", "outerLips",
            "leftEyebrow", "rightEyebrow", "nose")


@dataclass
class Analysis:
    importance: np.ndarray            # 和图片一样大，0–1
    subject: Optional[np.ndarray]     # 和图片一样大，0–1；没找到主体时是 None
    faces: int                        # 找到几张人脸


def available():
    return _AVAILABLE


def _buffer_to_array(buffer):
    """把 Vision 返回的 CVPixelBuffer（每像素一个 float32）变成 numpy 数组。"""
    Quartz.CVPixelBufferLockBaseAddress(buffer, 0)
    try:
        width = Quartz.CVPixelBufferGetWidth(buffer)
        height = Quartz.CVPixelBufferGetHeight(buffer)
        row_bytes = Quartz.CVPixelBufferGetBytesPerRow(buffer)
        base = Quartz.CVPixelBufferGetBaseAddress(buffer)
        raw = base.as_buffer(row_bytes * height)
        array = np.frombuffer(raw, dtype=np.float32).reshape(height, row_bytes // 4)[:, :width]
        return array.copy()
    finally:
        Quartz.CVPixelBufferUnlockBaseAddress(buffer, 0)


def _region_points(region, width, height):
    """五官区域的点，换成以左上角为原点的图片坐标（Vision 的原点在左下角）。"""
    count = region.pointCount()
    points = region.pointsInImageOfSize_(Quartz.CGSizeMake(width, height))
    return [(points[i].x, height - points[i].y) for i in range(count)]


def analyze(image):
    """分析一张 RGB 图片，返回 Analysis。不能用时返回 None。"""
    if not _AVAILABLE:
        return None
    width, height = image.size
    with objc.autorelease_pool():
        encoded = io.BytesIO()
        image.save(encoded, "JPEG", quality=92)
        data = encoded.getvalue()
        handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(
            NSData.dataWithBytes_length_(data, len(data)), None)
        saliency = Vision.VNGenerateAttentionBasedSaliencyImageRequest.alloc().init()
        faces = Vision.VNDetectFaceLandmarksRequest.alloc().init()
        requests = [saliency, faces]
        foreground = None
        if hasattr(Vision, "VNGenerateForegroundInstanceMaskRequest"):   # macOS 14 以上才有
            foreground = Vision.VNGenerateForegroundInstanceMaskRequest.alloc().init()
            requests.append(foreground)
        ok, _error = handler.performRequests_error_(requests, None)
        if not ok:
            return None

        importance = np.zeros((height, width), dtype=np.float32)

        # 显著区域：68 × 68 的热度图，放大到图片大小
        results = saliency.results()
        if results:
            heat = _buffer_to_array(results[0].pixelBuffer())
            heat /= max(1e-6, float(heat.max()))
            heat_image = Image.fromarray(heat).resize((width, height), Image.Resampling.BILINEAR)
            importance = np.maximum(importance, 0.5 * np.asarray(heat_image))

        # 人脸：整张脸中等重要，五官最重要
        face_results = faces.results() or []
        face_layer = Image.new("L", (width, height), 0)
        feature_layer = Image.new("L", (width, height), 0)
        face_draw = ImageDraw.Draw(face_layer)
        feature_draw = ImageDraw.Draw(feature_layer)
        for face in face_results:
            box = face.boundingBox()
            left = box.origin.x * width
            right = (box.origin.x + box.size.width) * width
            top = (1 - box.origin.y - box.size.height) * height
            bottom = (1 - box.origin.y) * height
            face_draw.ellipse((left, top - 0.1 * (bottom - top), right, bottom), fill=255)
            landmarks = face.landmarks()
            if landmarks is None:
                continue
            line = max(2, int(0.025 * (right - left)))
            for name in FEATURES:
                region = getattr(landmarks, name)()
                if region is None:
                    continue
                points = _region_points(region, width, height)
                if len(points) >= 3:
                    feature_draw.polygon(points, fill=255, outline=255, width=line)
                elif points:
                    x, y = points[0]
                    feature_draw.ellipse((x - line, y - line, x + line, y + line), fill=255)
        if face_results:
            radius = max(2, width // 150)
            feature_layer = feature_layer.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(radius))
            face_layer = face_layer.filter(ImageFilter.GaussianBlur(radius * 3))
            importance = np.maximum(importance, 0.6 * np.asarray(face_layer, dtype=np.float32) / 255)
            importance = np.maximum(importance, np.asarray(feature_layer, dtype=np.float32) / 255)

        # 主体：放大到图片大小的遮罩
        subject = None
        if foreground is not None and foreground.results():
            observation = foreground.results()[0]
            mask, _error = observation.generateScaledMaskForImageForInstances_fromRequestHandler_error_(
                observation.allInstances(), handler, None)
            if mask is not None:
                subject = np.clip(_buffer_to_array(mask), 0, 1)
                if subject.shape != (height, width):
                    subject = np.asarray(Image.fromarray(subject).resize((width, height)), dtype=np.float32)
                if subject.mean() < 0.01 or subject.mean() > 0.97:
                    subject = None          # 几乎没有主体，或者整张图都是主体，就当作没找到

        return Analysis(importance=np.clip(importance, 0, 1), subject=subject, faces=len(face_results))
