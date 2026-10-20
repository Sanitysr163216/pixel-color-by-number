"""
在线图库：搜索芝加哥艺术博物馆（Art Institute of Chicago）公开的名画。

只搜索"公有领域"（public domain，CC0）的作品：版权已经过期，谁都可以自由使用，
所以可以放心地把它们变成数字填色图。博物馆的接口不需要注册或密钥。
接口说明：https://api.artic.edu/docs/

这里只负责联网和读取数据，不涉及界面；联网比较慢，界面那边会放到后台线程里调用。
"""

import json
import ssl
import urllib.error
import urllib.request
from io import BytesIO

from PIL import Image

SEARCH_URL = "https://api.artic.edu/api/v1/artworks/search"
IMAGE_URL = "https://www.artic.edu/iiif/2/{image_id}/full/{width},/0/default.jpg"
# 博物馆希望调用接口的程序说明自己是谁、怎么联系
USER_AGENT = "ColorNumber (https://github.com/Sanitysr163216/pixel-color-by-number)"
TIMEOUT = 20                 # 秒
PAGE_SIZE = 24               # 每次取多少张
ARTWORK_TYPES = [1, 18]      # 只要绘画（1 = Painting）和版画（18 = Print），不要首饰、陶器之类
THUMBNAIL_WIDTH = 200
IMAGE_WIDTH = 843            # 博物馆公开提供的标准尺寸，做像素画足够了

# 推荐的搜索词：(界面文字的键, 用英文搜索的词)
TOPICS = [
    ("topic_flowers", "flowers"),
    ("topic_cats", "cat"),
    ("topic_birds", "bird"),
    ("topic_landscape", "landscape"),
    ("topic_sea", "sea boat"),
    ("topic_japan", "japanese woodblock"),
]


class OnlineError(Exception):
    """连不上网、博物馆的服务器出错等。"""


def _ssl_context():
    # 打包好的 App 里不一定找得到系统的证书，优先用 certifi 带的证书
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _fetch(url, body=None):
    """发出请求，返回收到的数据（bytes）。body 是要发送的 JSON 数据。"""
    headers = {"User-Agent": USER_AGENT, "AIC-User-Agent": USER_AGENT}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT, context=_ssl_context()) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise OnlineError(f"HTTP {error.code}") from error
    except (urllib.error.URLError, OSError) as error:   # 没有网络、超时……
        raise OnlineError(str(getattr(error, "reason", error))) from error


def search(query, page=1):
    """
    搜索作品。返回 (作品列表, 还有没有下一页)。
    每个作品是字典：id、title（名字）、artist（作者）、date（年代）、image_id（取图片用）。
    """
    body = {
        "query": {"bool": {"filter": [
            {"term": {"is_public_domain": True}},
            {"exists": {"field": "image_id"}},
            {"terms": {"artwork_type_id": ARTWORK_TYPES}},
        ]}},
        "fields": ["id", "title", "artist_title", "date_display", "image_id"],
        "limit": PAGE_SIZE,
        "page": page,
    }
    if query.strip():
        body["q"] = query.strip()
    try:
        result = json.loads(_fetch(SEARCH_URL, body))
        items = result["data"]
        total_pages = result["pagination"]["total_pages"]
    except (ValueError, KeyError, TypeError) as error:
        raise OnlineError("unexpected answer") from error
    artworks = [{
        "id": item["id"],
        "title": item.get("title") or "",
        "artist": item.get("artist_title") or "",
        "date": item.get("date_display") or "",
        "image_id": item["image_id"],
    } for item in items if item.get("image_id")]
    return artworks, page < total_pages


def download_image(image_id, width=IMAGE_WIDTH):
    """下载作品的图片，返回 Pillow 图片（RGB）。"""
    data = _fetch(IMAGE_URL.format(image_id=image_id, width=width))
    try:
        with Image.open(BytesIO(data)) as image:
            return image.convert("RGB")
    except OSError as error:
        raise OnlineError("not an image") from error
