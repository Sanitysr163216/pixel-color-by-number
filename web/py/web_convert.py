"""
网页版：在浏览器里（Pyodide）调用 colornumber/core/converter.py 的小接口。

JavaScript 先把照片写进 Pyodide 的虚拟文件系统，再调用这里的函数；
参数和结果都用 JSON 文字传来传去。转换的算法和桌面版完全一样。
"""

import json

from PIL import Image

from colornumber.core import converter

WORK_LONG_SIDE = 1600       # 先把照片缩到这么大，手机上转换更快（最多 128 格，足够了）
_image = None


def load(path):
    """读取照片（会按照片里记录的方向转正），返回宽和高。"""
    global _image
    image = converter.load_image(path)
    image.thumbnail((WORK_LONG_SIDE, WORK_LONG_SIDE), Image.Resampling.LANCZOS)
    _image = image
    return json.dumps({"width": image.width, "height": image.height})


def convert(options_json):
    """按选项转换成填色图，返回调色板、编号、还原度和"很接近的颜色"有几对。"""
    options = json.loads(options_json)
    picture = converter.convert(_image, **options)
    crop = options.get("crop")
    original = _image.crop(crop) if crop else _image
    return json.dumps({
        "width": picture.width,
        "height": picture.height,
        "palette": [list(color) for color in picture.palette],
        "numbers": picture.flat_numbers(),
        "fidelity": converter.fidelity(original, picture),
        "similar": converter.similar_color_pairs(picture.palette),
    })


def recommend(options_json):
    """推荐的颜色数。"""
    options = json.loads(options_json)
    return converter.recommend_color_count(_image, **options)
