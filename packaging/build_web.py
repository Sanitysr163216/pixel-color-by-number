"""
生成网页版（PWA，手机和电脑的浏览器都能玩）。

网页版的界面写在 web/ 文件夹里（HTML、CSS、JavaScript）。这个脚本把它们复制到 site/，
再从 Python 代码里导出网页版要用的东西，保证桌面版和网页版用的是同一份：

- data/library.json   图库里的图（来自 core/library.py）
- data/strings.json   中英文界面文字（来自 core/i18n.py）
- data/icons.json     按钮小图标，转成 SVG（来自 core/icon_art.py）
- data/artworks.json  内置名画的署名资料，图片在 art/，缩略图在 art/thumbs/（来自 core/artworks.py）
- py/colornumber/...  照片转换的 Python 代码（core/converter.py），在浏览器里用 Pyodide 运行
- pyodide/            Pyodide（浏览器里的 Python）和 numpy、Pillow：放在自己的网站上，
                      不用再从 jsDelivr 下载（jsDelivr 在中国大陆经常连不上）
- icons/*.png         App 图标
- sw.js               离线缓存要用的文件列表和版本号

用法（在项目文件夹里）：

    python packaging/build_web.py
    python -m http.server --directory site 8000      # 然后用浏览器打开 http://localhost:8000
"""

import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from colornumber import __version__  # noqa: E402
from colornumber.core import artworks, library  # noqa: E402
from colornumber.core.i18n import STRINGS  # noqa: E402
from colornumber.core.icon_art import ICONS  # noqa: E402

WEB = ROOT / "web"
SITE = ROOT / "site"
ICON_SOURCE = ROOT / "Color Number.app" / "Contents" / "Resources" / "AppIcon.icns"
PYODIDE_VERSION = "0.27.7"
PYODIDE_CDN = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"
PYODIDE_FILES = ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]
PYODIDE_PACKAGES = ["numpy", "pillow"]
PYODIDE_CACHE = ROOT / "build" / f"pyodide-{PYODIDE_VERSION}"    # 下载过一次就存在这里，下次不用再下载

# 浏览器里运行的 Python 文件：照片转换只需要这几个（不需要 Kivy）
PYTHON_FILES = [
    "colornumber/__init__.py",
    "colornumber/core/__init__.py",
    "colornumber/core/picture.py",
    "colornumber/core/converter.py",
]


def export_library():
    category_of = {key: name for name, keys in library.CATEGORIES.items() for key in keys}
    pictures = []
    for key in library.LIBRARY:
        picture = library.load(key)
        pictures.append({
            "key": key,
            "category": category_of[key],
            "width": picture.width,
            "height": picture.height,
            "palette": [list(color) for color in picture.palette],
            "numbers": picture.flat_numbers(),
        })
    return {"categories": list(library.CATEGORIES), "pictures": pictures}


def icon_svg(rows):
    """把一个字符画图标变成 SVG：每一行里连续的 # 合成一个长方形。颜色跟着文字颜色（currentColor）。"""
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            if row[x] == "#":
                start = x
                while x < len(row) and row[x] == "#":
                    x += 1
                rects.append(f'<rect x="{start}" y="{y}" width="{x - start}" height="1"/>')
            else:
                x += 1
    return ('<svg viewBox="0 0 12 12" fill="currentColor" shape-rendering="crispEdges" aria-hidden="true">'
            + "".join(rects) + "</svg>")


def export_artworks(folder):
    """复制内置名画，并做小缩略图（首页的卡片用，打开得快）。返回署名资料。"""
    thumbs = folder / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    entries = artworks.load()
    for entry in entries:
        source = artworks.image_path(entry)
        shutil.copyfile(source, folder / entry["file"])
        with Image.open(source) as image:
            image = image.convert("RGB")
            image.thumbnail((320, 320), Image.Resampling.LANCZOS)
            image.save(thumbs / entry["file"], quality=80, optimize=True)
    return entries


def pyodide_file(name, sha256=None):
    """取一个 Pyodide 文件：先看 build/ 里有没有，没有就从 jsDelivr 下载。给了 sha256 就检查文件对不对。"""
    PYODIDE_CACHE.mkdir(parents=True, exist_ok=True)
    path = PYODIDE_CACHE / name
    if not path.exists():
        request = urllib.request.Request(PYODIDE_CDN + name, headers={"User-Agent": "ColorNumber build"})
        with urllib.request.urlopen(request, timeout=120) as response:
            path.write_bytes(response.read())
    data = path.read_bytes()
    if sha256 and hashlib.sha256(data).hexdigest() != sha256:
        path.unlink()
        raise RuntimeError(f"{name}: checksum does not match, please run the build again")
    return data


def copy_pyodide(folder):
    """把 Pyodide 和照片转换要用的软件包（numpy、Pillow）放进网站。"""
    folder.mkdir(parents=True, exist_ok=True)
    lock = json.loads(pyodide_file("pyodide-lock.json"))
    needed, queue = [], list(PYODIDE_PACKAGES)
    while queue:                                  # 连同它们依赖的软件包一起
        name = queue.pop()
        if name not in needed:
            needed.append(name)
            queue.extend(lock["packages"][name]["depends"])
    for name in PYODIDE_FILES:
        (folder / name).write_bytes(pyodide_file(name))
    for name in needed:
        package = lock["packages"][name]
        (folder / package["file_name"]).write_bytes(pyodide_file(package["file_name"], package["sha256"]))


def app_icons(folder):
    """从 Mac 的 App 图标生成网页要用的几种尺寸。"""
    folder.mkdir(parents=True, exist_ok=True)
    with Image.open(ICON_SOURCE) as icon:
        icon.size = (512, 512)
        icon.load(scale=2)                       # 1024×1024
        icon = icon.convert("RGBA")
    for size in (192, 512):
        icon.resize((size, size), Image.Resampling.LANCZOS).save(folder / f"icon-{size}.png", optimize=True)
    # iPhone 主屏幕的图标不能有透明的部分（会变成黑色），铺满图标自己的背景色，系统会自动切圆角
    background = icon.getpixel((512, 80))
    square = Image.new("RGBA", icon.size, background)
    square.alpha_composite(icon)
    square.convert("RGB").resize((180, 180), Image.Resampling.LANCZOS).save(folder / "apple-touch-icon.png")
    icon.resize((64, 64), Image.Resampling.LANCZOS).save(folder / "favicon.png", optimize=True)


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(WEB, SITE)

    data = SITE / "data"
    data.mkdir(exist_ok=True)
    (data / "library.json").write_text(json.dumps(export_library(), separators=(",", ":")), encoding="utf-8")
    (data / "strings.json").write_text(json.dumps(STRINGS, ensure_ascii=False, separators=(",", ":")),
                                       encoding="utf-8")
    icons = {name: icon_svg(rows) for name, rows in ICONS.items()}
    (data / "icons.json").write_text(json.dumps(icons, separators=(",", ":")), encoding="utf-8")

    for name in PYTHON_FILES:
        target = SITE / "py" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)

    app_icons(SITE / "icons")
    copy_pyodide(SITE / "pyodide")
    (data / "artworks.json").write_text(json.dumps(export_artworks(SITE / "art"), ensure_ascii=False,
                                                   separators=(",", ":")), encoding="utf-8")

    # 版本号写进页面和离线缓存；文件列表交给 sw.js，第一次打开时全部缓存下来，以后没网也能玩
    # 名画的大图和 Pyodide 不预先缓存（第一次用到时才下载，并且存下来），免得第一次打开就要下载十几 MB
    files = sorted(str(path.relative_to(SITE)).replace("\\", "/") for path in SITE.rglob("*")
                   if path.is_file() and path.name != "sw.js" and not path.name.startswith(".")
                   and path.parent not in (SITE / "art", SITE / "pyodide"))
    for name in ("index.html", "js/app.js"):
        path = SITE / name
        path.write_text(path.read_text(encoding="utf-8").replace("__VERSION__", __version__), encoding="utf-8")
    sw = SITE / "sw.js"
    sw.write_text(sw.read_text(encoding="utf-8")
                  .replace("__VERSION__", __version__)
                  .replace("__PYODIDE_VERSION__", PYODIDE_VERSION)
                  .replace('"__FILES__"', json.dumps(["./"] + files)), encoding="utf-8")
    print(f"Built site/ (version {__version__}, {len(files)} files)")


if __name__ == "__main__":
    main()
