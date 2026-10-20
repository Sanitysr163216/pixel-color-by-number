"""
内置图库。

小图用"字符画"来画：每个字符代表一种颜色，每一行字符就是一行格子。
COLORS 字典规定了每个字符是什么颜色。风景图用代码按规则生成。
"""

import math

from colornumber.core.picture import Picture

# ---------------------------------------------------------------------------
# 字符画
# ---------------------------------------------------------------------------

def _mushroom_art():
    """
    一大一小两朵牛肝菌：用半个椭圆画菌盖、长方形画菌柄，再自动描深色边。
    （刻意没有画红帽白点和脸，和游戏里常见的卡通蘑菇区分开。）
    """
    width, height = 22, 18

    def big_cap(row, col):
        return row <= 7 and ((col - 9.5) / 7.6) ** 2 + ((row - 7.5) / 6.4) ** 2 <= 1

    def big_stem_right(row):
        return 12 + (1 if row >= 13 else 0)          # 菌柄下面稍微粗一点

    def big_stem(row, col):
        return 8 <= row <= 15 and 7 - (1 if row >= 13 else 0) <= col <= big_stem_right(row)

    def small_cap(row, col):
        return 9 <= row <= 12 and ((col - 17.5) / 3.9) ** 2 + ((row - 12.5) / 3.4) ** 2 <= 1

    def small_stem(row, col):
        return 13 <= row <= 15 and 16 <= col <= 19

    def inside(row, col):
        return any(shape(row, col) for shape in (big_cap, big_stem, small_cap, small_stem))

    rows = []
    for row in range(height):
        line = ""
        for col in range(width):
            if row >= 16:
                char = "G" if (col + row) % 3 == 0 else "g"
            elif inside(row, col):
                edge = any(not inside(row + dr, col + dc) and row + dr < 16
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
                if edge:
                    char = "k"
                elif big_cap(row, col):
                    if row == 7:
                        char = "u"                                   # 菌盖下面一圈
                    elif (col - 6) ** 2 + (row - 3.5) ** 2 < 6:
                        char = "h"                                   # 高光
                    else:
                        char = "b"
                elif small_cap(row, col):
                    char = "U" if row == 12 else ("O" if (col - 16.5) ** 2 + (row - 10.8) ** 2 < 2 else "o")
                elif big_stem(row, col):
                    char = "S" if col == big_stem_right(row) - 1 else "s"   # 右边一列阴影
                else:
                    char = "S" if col == 18 else "s"
            elif (row, col) in ((15, 2), (15, 3), (14, 2), (15, 21), (14, 21)):
                char = "g"                                           # 几根小草
            else:
                char = "."
            line += char
        rows.append(line)
    return rows


MUSHROOM = {
    "colors": {
        ".": (222, 238, 226), "k": (70, 45, 35), "b": (150, 95, 60), "h": (190, 132, 86),
        "u": (236, 214, 170), "o": (232, 140, 62), "O": (247, 185, 110), "U": (240, 205, 150),
        "s": (244, 230, 200), "S": (214, 194, 158), "g": (112, 176, 96), "G": (82, 140, 76),
    },
    "art": _mushroom_art(),
}

CAT = {
    "colors": {
        ".": (205, 228, 245), "k": (55, 50, 60), "o": (240, 155, 65),
        "O": (205, 115, 45), "l": (255, 238, 215), "p": (240, 150, 170),
        "g": (110, 190, 100), "w": (255, 255, 255),
    },
    "art": [
        "..................",
        "..k............k..",
        ".kOk..........kOk.",
        ".kpOk........kOpk.",
        ".kppOkkkkkkkkOppk.",
        ".kooooOooooOooook.",
        "kooooooOooOooooook",
        "kooooooooooooooook",
        "koooggooooooggoook",
        "koookgoooooookgook",
        "kooooolllllloooook",
        "koooolllpplllooook",
        "koooolllkklllooook",
        "kooooolkllkloooook",
        ".kooooolllloooook.",
        "..kkooooooooookk..",
        "....kkkkkkkkkk....",
        "..................",
    ],
}

STRAWBERRY = {
    "colors": {
        ".": (255, 245, 235), "k": (90, 30, 40), "r": (225, 45, 60),
        "R": (180, 25, 45), "y": (255, 220, 120), "g": (80, 170, 80),
        "G": (45, 120, 60), "h": (255, 140, 150),
    },
    "art": [
        "................",
        "......G..G......",
        "....GgGggGgG....",
        "...kgGgggGgGk...",
        "..krrkGgGGkrrk..",
        ".krhrrrkkkrryrk.",
        ".krhyrrrrrrrrrk.",
        ".krrrrryrrryrrk.",
        ".kryrrrrrrrrrRk.",
        "..krrryrrryrRk..",
        "..krrrrrrrrrRk..",
        "...kryrrryrRk...",
        "...krrrrrrRRk...",
        "....krryrRRk....",
        ".....kRRRRk.....",
        "......kkkk......",
    ],
}

ICE_CREAM = {
    "colors": {
        ".": (225, 240, 250), "k": (80, 55, 50), "p": (250, 170, 195),
        "P": (225, 120, 160), "m": (180, 235, 200), "M": (120, 200, 160),
        "c": (230, 180, 110), "C": (190, 135, 70), "r": (220, 40, 60),
        "w": (255, 255, 255),
    },
    "art": [
        "................",
        ".......kk.......",
        "......krrk......",
        "......krrk......",
        "....kkkkkkkk....",
        "...kppwpppppk...",
        "..kpwppppppPPk..",
        "..kppppppppPPk..",
        "..kkPPkkPPkkkk..",
        "..kmmMmmmmmMMk..",
        "..kmwmmmmmmMMk..",
        "..kkMMkkMMkkkk..",
        "...kcCcCcCcCk...",
        "...kCcCcCcCck...",
        "....kcCcCcCk....",
        "....kCcCcCck....",
        ".....kcCcCk.....",
        ".....kCcCck.....",
        "......kcCk......",
        ".......kk.......",
    ],
}

HOUSE = {
    "colors": {
        ".": (190, 225, 250), "k": (60, 50, 50), "r": (200, 70, 60),
        "R": (150, 45, 45), "w": (250, 235, 205), "W": (220, 195, 160),
        "b": (110, 75, 55), "y": (255, 225, 110), "g": (110, 185, 90),
        "G": (75, 145, 70), "c": (150, 150, 160), "s": (255, 255, 255),
    },
    "art": [
        "....................",
        "..ss...........kk...",
        ".ssss..........kck..",
        "..ss.....kk....kck..",
        "........krrk...kck..",
        ".......krrrrk..kck..",
        "......krrrrrrk.kck..",
        ".....krrrrrrrrkkck..",
        "....krrrrrrrrrrkkk..",
        "...krrrrrrrrrrrrk...",
        "..kRRRRRRRRRRRRRRk..",
        "...kwwwwwwwwwwwwk...",
        "...kwkkkwwwwkkkwk...",
        "...kwkykwwwwkykwk...",
        "...kwkkkwkkkkkkwk...",
        "...kwwwwwkbbkwwwk...",
        "...kWWWWWkbbkWWWk...",
        "gGgkWWWWWkbykWWWkgGg",
        "GgGkkkkkkkbbkkkkkGgG",
        "gGgGgGgGgGgGgGgGgGgG",
    ],
}

CACTUS = {
    "colors": {
        ".": (255, 236, 200), "k": (50, 70, 50), "g": (95, 175, 95),
        "G": (60, 135, 70), "l": (160, 215, 140), "p": (245, 120, 160),
        "t": (205, 105, 70), "T": (160, 75, 50), "y": (250, 215, 120),
    },
    "art": [
        "................",
        "......kpk.......",
        ".....kpppk......",
        ".....kgggk......",
        "....kglgGGk.....",
        "....kglgGGk.kk..",
        ".kk.kglgGGkkgGk.",
        "kgGkkglgGGkglGk.",
        "kglGkglgGGkglGk.",
        "kglGkglgGGgglGk.",
        "kglGgglgGGGGGk..",
        ".kGGGglgGGkkk...",
        "..kkkglgGGk.....",
        "....kglgGGk.....",
        "..kkkkkkkkkkkk..",
        "..kttttttttttk..",
        "...kTyTyTyTyk...",
        "...ktttttttk....",
        "....kTTTTTk.....",
        "....kkkkkkk.....",
    ],
}

def _fish_art():
    """小丑鱼：用椭圆和三角形算出鱼的形状，再自动描黑边。"""
    width, height = 24, 18
    cx, cy = 13.5, 8.0

    def in_fish(row, col):
        body = ((col - cx) / 7.5) ** 2 + ((row - cy) / 4.6) ** 2 <= 1
        tail = 2 <= col <= 6 and abs(row - cy) <= (7 - col) * 0.9 + 0.5
        fin = 10 <= col <= 14 and cy - 6 <= row <= cy - 4 and col - 10 >= (cy - 4 - row) * 1.5
        return body or tail or fin

    rows = []
    for row in range(height):
        line = ""
        for col in range(width):
            if row >= height - 2:
                char = "y" if (row, col) in ((16, 5), (17, 18), (16, 21)) else "s"
            elif in_fish(row, col):
                edge = any(not in_fish(row + dr, col + dc)
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
                if edge:
                    char = "k"
                elif abs(col - 10) < 0.6 or abs(col - 16) < 0.6:
                    char = "w"
                elif (row, col) == (int(cy) - 1, 18):
                    char = "b"
                else:
                    char = "o"
            elif (col in (3, 4) and row >= 12) or (col in (20,) and row >= 13):
                char = "g"
            elif (row, col) in ((2, 20), (3, 21), (1, 19), (4, 4)):
                char = "~"
            else:
                char = "."
            line += char
        rows.append(line)
    return rows


FISH = {
    "colors": {
        ".": (120, 190, 235), "~": (200, 235, 250), "k": (40, 40, 50),
        "o": (250, 140, 40), "w": (255, 255, 255), "b": (25, 25, 35),
        "y": (255, 215, 90), "s": (235, 225, 190), "g": (80, 165, 120),
    },
    "art": _fish_art(),
}


def _from_art(art):
    """把字符画变成 Picture：用到的颜色按出现次数从多到少编号。"""
    rows = art["art"]
    width = max(len(row) for row in rows)
    rows = [row.ljust(width, ".") for row in rows]   # 不够长的行用背景补齐
    usage = {}
    for row in rows:
        for char in row:
            if char == " ":
                continue
            usage[char] = usage.get(char, 0) + 1
    ordered = sorted(usage, key=lambda char: usage[char], reverse=True)
    number_of = {char: i + 1 for i, char in enumerate(ordered)}
    number_of[" "] = number_of["."]
    numbers = [[number_of[char] for char in row] for row in rows]
    palette = [art["colors"][char] for char in ordered]
    return Picture(palette=palette, numbers=numbers)


# ---------------------------------------------------------------------------
# 用代码生成的风景
# ---------------------------------------------------------------------------

def _sunset():
    """日落时的山和湖：天空渐变、太阳、三层山、湖面倒影。"""
    width, height = 48, 32
    sky = [(255, 214, 140), (252, 180, 120), (240, 140, 115), (200, 110, 130), (130, 90, 140)]
    sun = (255, 240, 190)
    mountains = [(110, 80, 120), (80, 60, 100), (50, 40, 70)]
    water = [(120, 90, 130), (90, 70, 110)]
    shine = (255, 200, 150)

    palette = sky + [sun] + mountains + water + [shine]
    number = {color: i + 1 for i, color in enumerate(palette)}
    horizon = 22
    numbers = []
    for row in range(height):
        line = []
        for col in range(width):
            if row < horizon:
                color = sky[min(len(sky) - 1, (horizon - 1 - row) * len(sky) // horizon)]
                if (col - 30) ** 2 + (row - 11) ** 2 <= 26:
                    color = sun
                # 三层山，越近越深、越低
                for layer, base in enumerate((14, 17, 19)):
                    ridge = base + 3 * math.sin(col / (5 - layer) + layer * 2) + layer
                    if row >= ridge:
                        color = mountains[layer]
            else:
                color = water[(row + col // 6) % 2]
                if abs(col - 30) <= max(0, 4 - (row - horizon) // 2) and row % 2 == 0:
                    color = shine
            line.append(number[color])
        numbers.append(line)

    # 去掉没用到的颜色，并按使用次数重新编号
    usage = {}
    for line in numbers:
        for n in line:
            usage[n] = usage.get(n, 0) + 1
    ordered = sorted(usage, key=lambda n: usage[n], reverse=True)
    renumber = {old: i + 1 for i, old in enumerate(ordered)}
    return Picture(
        palette=[palette[old - 1] for old in ordered],
        numbers=[[renumber[n] for n in line] for line in numbers],
    )


# ---------------------------------------------------------------------------
# 图库目录
# ---------------------------------------------------------------------------

# 键是图的编号，名字的翻译在 i18n.py 里（"library_<键>"）
LIBRARY = {
    "mushroom": lambda: _from_art(MUSHROOM),
    "cat": lambda: _from_art(CAT),
    "strawberry": lambda: _from_art(STRAWBERRY),
    "ice_cream": lambda: _from_art(ICE_CREAM),
    "house": lambda: _from_art(HOUSE),
    "cactus": lambda: _from_art(CACTUS),
    "fish": lambda: _from_art(FISH),
    "sunset": _sunset,
}


def load(key):
    """按键名取出一张内置图。"""
    return LIBRARY[key]()
