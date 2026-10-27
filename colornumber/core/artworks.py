"""
内置名画包：colornumber/assets/artworks 里的名画图片和署名资料（credits.json）。

这些画不需要联网就能用（在中国大陆也能用），由 packaging/fetch_artworks.py 下载整理：
- 大都会艺术博物馆（The Metropolitan Museum of Art）：CC0，公有领域
- 国立故宫博物院（台北）：CC BY 4.0，必须按院方规定的格式署名（见每幅画的 credit）

credits.json 里每幅画是一个字典：
    file      图片文件名
    category  "east" 东方 或 "west" 西方
    museum    "met" 或 "npm"
    license   "CC0" 或 "CC BY 4.0"
    title     {"zh": 中文名, "en": 英文名}
    artist    {"zh": ..., "en": ...}
    date      {"zh": 中文年代, "en": 英文年代}
    credit    完整的署名文字（台北故宫的照抄院方格式）
    source    这幅画在博物馆网站上的网址
    changes   "cropped" 表示裁掉了照片边上的色卡或空白（可能没有这一项）
"""

import json
from pathlib import Path

FOLDER = Path(__file__).resolve().parent.parent / "assets" / "artworks"
CATEGORIES = ("east", "west")       # 显示顺序：东方在前


def load():
    """所有内置名画，东方在前、西方在后。没有名画包时返回空列表。"""
    path = FOLDER / "credits.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as file:
        entries = json.load(file)
    return sorted(entries, key=lambda entry: CATEGORIES.index(entry["category"]))


def image_path(entry):
    return FOLDER / entry["file"]


def text(entry, field, language):
    """取中文或英文的名字、作者、年代；没有这种语言时用英文。"""
    return entry[field].get(language) or entry[field]["en"]
