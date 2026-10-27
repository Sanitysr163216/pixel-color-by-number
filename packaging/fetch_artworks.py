"""
下载内置名画包：从两个开放资料库挑选的中外名画，存进 colornumber/assets/artworks/。

游戏里的"名画"页面直接用这些图，不需要联网（在中国大陆也能用）。
这个脚本只在挑选、更新名画时运行一次；下载好的图片和 credits.json 会提交到仓库里。

来源和授权：
- 大都会艺术博物馆（The Metropolitan Museum of Art）开放资料：CC0（公有领域）
  https://www.metmuseum.org/hubs/open-access
- 国立故宫博物院（台北）开放资料：CC BY 4.0，需按院方规定的格式署名
  https://digitalarchive.npm.gov.tw/opendata
  图片通过院方公开的 IIIF 接口取得。

用法（在项目文件夹里）：

    python packaging/fetch_artworks.py
"""

import json
import subprocess
import sys
import time
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "colornumber" / "assets" / "artworks"
LONG_SIDE = 1000            # 存下来的图最长边多少像素（做像素画足够了）
MET_API = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
NPM_MANIFEST = "https://digitalarchive.npm.gov.tw/Integrate/GetJson?cid={cid}&dept=P"
NPM_PAGE = "https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/{cid}?dep=P&mode=full"
NPM_CREDIT = "{name}。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw"

# 大都会艺术博物馆：(编号, 分类, 中文名, 中文作者, 中文年代)
MET = [
    (436535, "west", "麦田与柏树", "文森特·梵高", "1889年"),
    (436524, "west", "向日葵", "文森特·梵高", "1887年"),
    (436528, "west", "鸢尾花", "文森特·梵高", "1890年"),
    (436532, "west", "戴草帽的自画像", "文森特·梵高", "1887年"),
    (436530, "west", "夹竹桃", "文森特·梵高", "1888年"),
    (437980, "west", "柏树", "文森特·梵高", "1889年"),
    (437881, "west", "持水壶的年轻女子", "约翰内斯·维米尔", "约1662年"),
    (435809, "west", "收割者", "老彼得·勃鲁盖尔", "1565年"),
    (438817, "west", "舞蹈课", "埃德加·德加", "1874年"),
    (436819, "west", "玛达·普里马维西", "古斯塔夫·克里姆特", "1912–1913年"),
    (438822, "west", "狮子的晚餐", "亨利·卢梭", "约1907年"),
    (45434, "east", "神奈川冲浪里", "葛饰北斋", "约1830–1832年"),
    (39901, "east", "照夜白图", "韩幹", "唐，约750年"),
    (40081, "east", "王羲之观鹅图", "钱选", "元，约1295年"),
    (39936, "east", "竹禽图", "宋徽宗", "北宋，12世纪初"),
    (44638, "east", "月下赏梅图", "马远", "南宋，13世纪初"),
    (40133, "east", "兰花图", "马麟", "南宋，13世纪"),
]

# 国立故宫博物院（台北）：编号、名字、作者、年代，以及裁剪框（左、上、右、下，占原图的比例；
# 有的照片带着色卡、尺子或空白的对页，裁掉）
NPM = [
    {"cid": 48, "zh": "双喜图", "en": "Magpies and Hare", "artist_zh": "崔白", "artist_en": "Cui Bo",
     "date": "1061", "date_zh": "北宋，1061年"},
    {"cid": 4954, "zh": "仙萼长春·牡丹", "en": "Peonies, from Immortal Blossoms in an Everlasting Spring",
     "artist_zh": "郎世宁", "artist_en": "Giuseppe Castiglione (Lang Shining)", "date": "Qing dynasty",
     "date_zh": "清", "crop": (0.50, 0.10, 0.91, 0.88)},
    {"cid": 4958, "zh": "仙萼长春·虞美人蝴蝶花", "en": "Poppies and Irises, from Immortal Blossoms in an Everlasting Spring",
     "artist_zh": "郎世宁", "artist_en": "Giuseppe Castiglione (Lang Shining)", "date": "Qing dynasty",
     "date_zh": "清", "crop": (0.02, 0.09, 0.88, 0.88)},
    {"cid": 3581, "zh": "聚瑞图", "en": "Assembled Auspiciousness", "artist_zh": "郎世宁",
     "artist_en": "Giuseppe Castiglione (Lang Shining)", "date": "1723", "date_zh": "清，1723年"},
    {"cid": 1227, "zh": "岁朝图", "en": "Picture for the New Year", "artist_zh": "赵昌", "artist_en": "Zhao Chang",
     "date": "Song dynasty", "date_zh": "宋"},
    {"cid": 5, "zh": "宫乐图", "en": "Palace Concert", "artist_zh": "唐人（佚名）", "artist_en": "Anonymous (Tang dynasty)",
     "date": "Tang dynasty", "date_zh": "唐", "crop": (0.055, 0.05, 0.935, 0.885)},
    {"cid": 34, "zh": "秋庭戏婴图", "en": "Children at Play in an Autumn Garden", "artist_zh": "苏汉臣",
     "artist_en": "Su Hanchen", "date": "Song dynasty", "date_zh": "宋"},
    {"cid": 1195, "zh": "谿山行旅图", "en": "Travelers Among Mountains and Streams", "artist_zh": "范宽",
     "artist_en": "Fan Kuan", "date": "Song dynasty", "date_zh": "北宋"},
    {"cid": 47, "zh": "早春图", "en": "Early Spring", "artist_zh": "郭熙", "artist_en": "Guo Xi",
     "date": "1072", "date_zh": "北宋，1072年"},
    {"cid": 13636, "zh": "十骏犬·雪爪卢", "en": "Xuezhualu, from Ten Fine Hounds", "artist_zh": "郎世宁",
     "artist_en": "Giuseppe Castiglione (Lang Shining)", "date": "Qing dynasty", "date_zh": "清"},
]


def fetch(url, attempts=3):
    """下载一个网址的内容（用 curl：台北故宫网站的证书 Python 3.13 不接受）。偶尔失败就再试几次。"""
    for attempt in range(attempts):
        result = subprocess.run(["curl", "-sfL", "-m", "120", "-A", "ColorNumber (github.com/Sanitysr163216)", url],
                                capture_output=True)
        if result.returncode == 0:
            return result.stdout
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"download failed: {url}")


def trim_dark_border(image):
    """去掉照片四周的黑边（有的画是连着黑色画框边一起拍的）。"""
    grey = image.convert("L")
    width, height = grey.size

    def dark_row(y):
        return sum(grey.getpixel((x, y)) for x in range(0, width, 4)) / len(range(0, width, 4)) < 30

    def dark_col(x):
        return sum(grey.getpixel((x, y)) for y in range(0, height, 4)) / len(range(0, height, 4)) < 30

    top, bottom, left, right = 0, height - 1, 0, width - 1
    while top < height // 4 and dark_row(top):
        top += 1
    while bottom > height * 3 // 4 and dark_row(bottom):
        bottom -= 1
    while left < width // 4 and dark_col(left):
        left += 1
    while right > width * 3 // 4 and dark_col(right):
        right -= 1
    return image.crop((left, top, right + 1, bottom + 1))


def save(image, name):
    image.thumbnail((LONG_SIDE, LONG_SIDE), Image.Resampling.LANCZOS)
    image.save(OUT / name, quality=86, optimize=True, progressive=True)
    return image.size


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for object_id, category, title_zh, artist_zh, date_zh in MET:
        data = json.loads(fetch(MET_API + str(object_id)))
        if not data.get("isPublicDomain"):
            sys.exit(f"{object_id} is not in the public domain")
        image = trim_dark_border(Image.open(BytesIO(fetch(data["primaryImageSmall"]))).convert("RGB"))
        name = f"met-{object_id}.jpg"
        size = save(image, name)
        entries.append({
            "file": name, "category": category, "museum": "met", "license": "CC0",
            "title": {"zh": title_zh, "en": data["title"].split(" (")[0].split(", from the series")[0]},
            "artist": {"zh": artist_zh, "en": data["artistDisplayName"]},
            "date": {"zh": date_zh, "en": data["objectDate"]},
            "credit": f"{data['title']}, {data['artistDisplayName']}, {data['objectDate']}. "
                      f"The Metropolitan Museum of Art, {data['creditLine']}. Public domain (CC0).",
            "source": data["objectURL"], "size": list(size),
        })
        print("Met", object_id, size, title_zh, flush=True)

    for item in NPM:
        cid = item["cid"]
        manifest = json.loads(fetch(NPM_MANIFEST.format(cid=cid)))
        canvas = manifest["sequences"][0]["canvases"][0]          # 第一张是整幅画，后面是局部
        service = canvas["images"][0]["resource"]["service"]["@id"]
        request = "1000," if int(canvas["width"]) >= int(canvas["height"]) else ",1000"
        image = Image.open(BytesIO(fetch(f"{service}/full/{request}/0/default.jpg"))).convert("RGB")
        if "crop" in item:
            left, top, right, bottom = item["crop"]
            image = image.crop((round(left * image.width), round(top * image.height),
                                round(right * image.width), round(bottom * image.height)))
        name = f"npm-{cid}.jpg"
        size = save(image, name)
        official_name = manifest["label"].replace("NPM 故宮 - ", "").replace("　", " ")
        entries.append({
            "file": name, "category": "east", "museum": "npm", "license": "CC BY 4.0",
            "title": {"zh": item["zh"], "en": item["en"]},
            "artist": {"zh": item["artist_zh"], "en": item["artist_en"]},
            "date": {"zh": item["date_zh"], "en": item["date"]},
            # 院方规定的署名格式（文字照抄，不改成简体）
            "credit": NPM_CREDIT.format(name=official_name),
            "source": NPM_PAGE.format(cid=cid), "size": list(size),
            "changes": "cropped" if "crop" in item else "",
        })
        print("NPM", cid, size, item["zh"], flush=True)

    with open(OUT / "credits.json", "w", encoding="utf-8") as file:
        json.dump(entries, file, ensure_ascii=False, indent=1)
    print(f"Saved {len(entries)} artworks to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
