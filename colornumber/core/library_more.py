"""
图库的第二批图。

这些图不是一个字符一个字符写出来的，而是在一张"草稿纸"（Sketch）上
用代码涂椭圆、长方形、多边形，最后自动描边，得到和 library.py 一样的字符画。
"""

import math


class Sketch:
    """一张字符画的草稿纸。坐标：col 是第几列（x），row 是第几行（y），从 0 开始。"""

    def __init__(self, width, height, background="."):
        self.width = width
        self.height = height
        self.grid = [[background] * width for _ in range(height)]

    def paint(self, char, test, only=None):
        """把 test(row, col) 为真的格子涂成 char。给了 only 时，只涂原来是这些字符的格子。"""
        for row in range(self.height):
            for col in range(self.width):
                if (only is None or self.grid[row][col] in only) and test(row, col):
                    self.grid[row][col] = char

    def ellipse(self, char, cx, cy, rx, ry, angle=0, only=None):
        """椭圆，angle 是旋转的角度（度）。"""
        cos, sin = math.cos(math.radians(angle)), math.sin(math.radians(angle))

        def test(row, col):
            u = (col - cx) * cos + (row - cy) * sin
            v = -(col - cx) * sin + (row - cy) * cos
            return (u / rx) ** 2 + (v / ry) ** 2 <= 1
        self.paint(char, test, only)

    def rect(self, char, left, top, right, bottom, only=None):
        """长方形，四条边都包含在内。"""
        self.paint(char, lambda row, col: left <= col <= right and top <= row <= bottom, only)

    def polygon(self, char, points, only=None):
        """多边形，points 是 [(col, row), ...]，按格子中心判断在不在里面。"""
        def test(row, col):
            inside = False
            for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
                if (y1 > row) != (y2 > row) and col < x1 + (row - y1) * (x2 - x1) / (y2 - y1):
                    inside = not inside
            return inside
        self.paint(char, test, only)

    def dots(self, char, cells):
        """涂几个单独的格子，cells 是 [(row, col), ...]。"""
        for row, col in cells:
            if 0 <= row < self.height and 0 <= col < self.width:
                self.grid[row][col] = char

    def outline(self, char, chars):
        """给由 chars 组成的形状描边：形状里挨着外面的格子涂成 char（图片边缘不算外面）。"""
        def outside(row, col):
            inside_image = 0 <= row < self.height and 0 <= col < self.width
            return inside_image and self.grid[row][col] not in chars
        edge = [(row, col) for row in range(self.height) for col in range(self.width)
                if self.grid[row][col] in chars
                and any(outside(row + dr, col + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))]
        self.dots(char, edge)

    def rows(self):
        return ["".join(line) for line in self.grid]


def _scatter(row, col, seed, chance):
    """看起来随机、但每次都一样的点（撒星星、糖粒用）。chance 是百分比 0–100。"""
    value = (row * 374761393 + col * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    value = ((value ^ (value >> 13)) * 1274126177) & 0xFFFFFFFF
    return (value ^ (value >> 16)) % 100 < chance


# ---------------------------------------------------------------------------
# 动物
# ---------------------------------------------------------------------------

def _penguin():
    s = Sketch(24, 26)
    s.paint("w", lambda r, c: r < 20 and _scatter(r, c, 1, 3))            # 雪花
    s.rect("w", 0, 22, 23, 25)                                              # 雪地
    s.paint("W", lambda r, c: r >= 23 and (c + 2 * r) % 7 < 2)
    s.ellipse("k", 4.5, 14, 1.8, 5, angle=15)                               # 翅膀
    s.ellipse("k", 19.5, 14, 1.8, 5, angle=-15)
    s.ellipse("k", 12, 13, 7.5, 10)                                         # 身体
    s.ellipse("w", 12, 16, 5, 7, only="k")                                  # 肚子
    s.ellipse("w", 9.6, 8.8, 2.3, 2.1, only="k")                            # 脸
    s.ellipse("w", 14.4, 8.8, 2.3, 2.1, only="k")
    s.dots("k", [(8, 10), (8, 14)])                                         # 眼睛
    s.polygon("o", [(10.5, 9.6), (13.5, 9.6), (12, 12)])                    # 嘴
    s.dots("p", [(10, 8), (10, 16)])                                        # 脸红
    s.rect("r", 0, 13, 23, 14, only="kw")                                   # 围巾
    s.rect("r", 15, 15, 16, 18)
    s.paint("R", lambda r, c: (c + r) % 3 == 0, only="r")
    s.ellipse("o", 9, 22.6, 2.4, 1.1)                                       # 脚
    s.ellipse("o", 15, 22.6, 2.4, 1.1)
    return s.rows()


PENGUIN = {
    "colors": {
        ".": (200, 228, 248), "w": (255, 255, 255), "W": (214, 230, 244),
        "k": (40, 45, 62), "o": (250, 168, 55), "p": (250, 170, 185), "r": (225, 60, 72),
        "R": (178, 40, 56),
    },
    "art": _penguin(),
}


def _fox():
    s = Sketch(24, 22)
    s.paint("f", lambda r, c: _scatter(r, c, 4, 4))                         # 背景的小花
    s.polygon("o", [(2.5, 10), (4.5, 0.5), (11, 6)])                        # 耳朵
    s.polygon("o", [(21.5, 10), (19.5, 0.5), (13, 6)])
    s.polygon("d", [(4.6, 7), (5, 3), (8.4, 6.2)], only="o")
    s.polygon("d", [(19.4, 7), (19, 3), (15.6, 6.2)], only="o")
    s.ellipse("o", 12, 12.5, 9, 7)                                          # 头
    s.ellipse("O", 12, 7, 3, 2.2, only="o")                                 # 额头的深色
    s.ellipse("w", 6.5, 16, 4.6, 3.6, only="oO")                            # 白色脸颊
    s.ellipse("w", 17.5, 16, 4.6, 3.6, only="oO")
    s.ellipse("w", 12, 18, 3.4, 2.2, only="oO")
    s.outline("K", "oOdw")
    s.rect("k", 7, 11, 8, 12)                                               # 眼睛
    s.rect("k", 16, 11, 17, 12)
    s.dots("w", [(11, 7), (11, 16)])
    s.ellipse("k", 12, 15.6, 1.5, 1.1)                                      # 鼻子
    return s.rows()


FOX = {
    "colors": {
        ".": (196, 228, 186), "f": (255, 236, 140), "o": (238, 128, 48), "O": (212, 98, 40),
        "d": (120, 62, 42), "w": (255, 248, 236), "k": (45, 35, 35), "K": (112, 56, 36),
    },
    "art": _fox(),
}


def _ladybug():
    s = Sketch(22, 22)
    s.ellipse("g", 11, 11, 11.5, 6.5, angle=-35)                            # 叶子
    s.ellipse("G", 11, 11, 11, 0.6, angle=-35, only="g")                    # 叶脉
    s.outline("L", "gG")
    s.ellipse("k", 11, 6, 3.6, 2.6)                                         # 头
    s.ellipse("r", 11, 12.5, 6, 6.5)                                        # 身体
    s.outline("k", "r")
    s.ellipse("h", 8.6, 9.2, 1.4, 1.1, only="r")                            # 高光
    s.rect("k", 11, 7, 11, 19, only="r")                                    # 中线
    for cx, cy in ((8.2, 11.8), (13.8, 11.8), (7.4, 15.4), (14.6, 15.4), (9.2, 17.6), (12.8, 17.6)):
        s.ellipse("k", cx, cy, 1.25, 1.2, only="r")                         # 斑点
    s.dots("w", [(5, 9), (5, 13)])                                          # 眼睛
    s.dots("k", [(3, 9), (2, 8), (3, 13), (2, 14)])                         # 触角
    return s.rows()


LADYBUG = {
    "colors": {
        ".": (236, 246, 250), "g": (120, 196, 100), "G": (86, 156, 74), "L": (60, 120, 60),
        "k": (35, 32, 40), "r": (228, 52, 52), "h": (255, 140, 130), "w": (255, 255, 255),
    },
    "art": _ladybug(),
}


def _whale():
    s = Sketch(32, 20)
    s.rect("s", 0, 8, 31, 19)                                               # 海
    s.rect("S", 0, 14, 31, 19)
    s.paint("~", lambda r, c: r == 8 and c % 5 in (1, 2))                   # 海浪
    s.paint("~", lambda r, c: r == 12 and (c + 3) % 7 == 0, only="s")
    s.polygon("b", [(22, 10), (29, 4), (31, 6.5), (27.5, 10), (31, 13.5), (29, 16), (22, 12.5)])
    s.ellipse("b", 13.5, 11, 10.5, 5.6)                                     # 身体
    s.ellipse("B", 12.5, 14.6, 8.5, 2.6, only="b")                          # 肚子
    s.outline("K", "bB")
    s.dots("k", [(10, 7)])                                                  # 眼睛
    s.dots("p", [(11, 9)])                                                  # 脸红
    s.dots("w", [(4, 8), (3, 8), (2, 8), (1, 6), (1, 10), (2, 7), (2, 9), (0, 5), (0, 11)])   # 喷水
    return s.rows()


WHALE = {
    "colors": {
        ".": (214, 236, 250), "s": (92, 170, 220), "S": (66, 138, 196), "~": (180, 222, 246),
        "b": (70, 100, 170), "B": (170, 196, 230), "K": (36, 52, 104), "k": (20, 24, 40),
        "p": (240, 150, 180), "w": (255, 255, 255),
    },
    "art": _whale(),
}


# ---------------------------------------------------------------------------
# 食物
# ---------------------------------------------------------------------------

def _watermelon():
    s = Sketch(26, 16)

    def ring(low, high):
        return lambda r, c: r >= 2 and low <= math.hypot((c - 12.5) / 12, (r - 2) / 12.5) <= high
    s.paint("G", ring(0, 1))                                                # 外皮
    s.paint("g", ring(0, 0.9))                                              # 浅色的皮
    s.paint("r", ring(0, 0.8))                                              # 果肉
    s.paint("h", lambda r, c: r == 2, only="r")                             # 切面的亮边
    for row, col in ((4, 7), (4, 18), (6, 10), (6, 15), (8, 12), (5, 4), (5, 21), (9, 8), (9, 17)):
        s.dots("k", [(row, col)])                                           # 籽
    s.outline("D", "Gg")
    return s.rows()


WATERMELON = {
    "colors": {
        ".": (255, 246, 214), "G": (54, 136, 66), "g": (176, 222, 140), "r": (238, 72, 84),
        "h": (255, 128, 136), "k": (40, 30, 30), "D": (32, 92, 46),
    },
    "art": _watermelon(),
}


def _donut():
    s = Sketch(22, 22)
    s.ellipse("d", 11, 11, 9.6, 9.6)                                        # 面团
    s.ellipse("D", 12.5, 12.5, 9.5, 9.5, only="d")                          # 右下角的阴影
    s.ellipse("d", 9.8, 9.8, 8.6, 8.6, only="D")

    def icing(r, c):
        angle = math.atan2(r - 11, c - 11)
        return math.hypot(c - 11, r - 11) <= 7.6 + 0.9 * math.sin(7 * angle)
    s.paint("p", icing)                                                     # 糖霜
    s.ellipse(".", 11, 11, 2.9, 2.9)                                        # 中间的洞
    s.ellipse("D", 11, 11, 3.6, 3.6, only="p")
    for index, char in enumerate("ybwg"):
        s.paint(char, lambda r, c, i=index: _scatter(r, c, 10 + i, 4), only="p")   # 糖粒
    s.outline("k", "dDpybwg")
    return s.rows()


DONUT = {
    "colors": {
        ".": (255, 236, 242), "d": (226, 172, 104), "D": (190, 132, 72), "p": (244, 128, 172),
        "y": (255, 222, 90), "b": (96, 168, 236), "w": (255, 255, 255), "g": (120, 204, 120),
        "k": (110, 66, 46),
    },
    "art": _donut(),
}


def _cupcake():
    s = Sketch(20, 24)
    s.polygon("c", [(2.5, 13.5), (16.5, 13.5), (14.6, 22.5), (4.4, 22.5)])  # 纸杯
    s.paint("C", lambda r, c: c % 3 == 0, only="c")
    for cx, cy, rx, ry in ((9.5, 12.8, 7.6, 2.6), (9.5, 10.2, 6.2, 2.3), (9.5, 7.8, 4.6, 2),
                           (9.5, 5.9, 2.8, 1.6)):
        s.ellipse("F", cx, cy + 0.6, rx, ry)                                # 奶油的影子
        s.ellipse("f", cx, cy, rx, ry - 0.3)                                # 一层奶油
    s.paint("y", lambda r, c: _scatter(r, c, 3, 5), only="f")               # 糖粒
    s.paint("b", lambda r, c: _scatter(r, c, 7, 4), only="f")
    s.ellipse("r", 9.5, 3, 1.7, 1.6)                                        # 樱桃
    s.dots("w", [(2, 9)])
    s.outline("k", "cCfFybrw")
    s.dots("k", [(1, 10), (0, 11)])                                         # 樱桃梗
    return s.rows()


CUPCAKE = {
    "colors": {
        ".": (214, 236, 246), "c": (126, 196, 220), "C": (90, 160, 196), "f": (255, 214, 226),
        "F": (240, 168, 192), "y": (255, 214, 80), "b": (150, 110, 220), "r": (218, 40, 60),
        "w": (255, 255, 255), "k": (90, 60, 70),
    },
    "art": _cupcake(),
}


def _avocado():
    s = Sketch(20, 26)
    s.ellipse("G", 10, 16, 7.6, 8.6)                                        # 外皮
    s.ellipse("G", 10, 8, 5.2, 6.2)
    s.ellipse("y", 10, 16, 6.2, 7.2, only="G")                              # 果肉
    s.ellipse("y", 10, 8, 3.9, 4.9, only="G")
    s.ellipse("Y", 10, 16.5, 4.6, 5.2, only="y")                            # 中间浅一点
    s.ellipse("b", 10, 17, 3.2, 3.5)                                        # 果核
    s.ellipse("B", 10.8, 17.8, 2.4, 2.6, only="b")
    s.dots("h", [(15, 9), (16, 8)])                                         # 果核的高光
    s.outline("k", "GyYbBh")
    s.ellipse("l", 13.5, 1.6, 2.6, 1, angle=-25)                            # 小叶子
    return s.rows()


AVOCADO = {
    "colors": {
        ".": (255, 230, 210), "G": (62, 110, 52), "y": (196, 226, 120), "Y": (232, 242, 168),
        "b": (150, 92, 54), "B": (118, 68, 40), "h": (210, 150, 104), "k": (40, 60, 34),
        "l": (110, 180, 80),
    },
    "art": _avocado(),
}


def _coffee():
    s = Sketch(24, 22)
    s.rect("t", 0, 19, 23, 21)                                              # 桌子
    s.paint("T", lambda r, c: r == 20 and c % 6 < 3, only="t")
    s.ellipse("s", 10.5, 19, 9.5, 1.6)                                      # 碟子
    s.ellipse("m", 18, 12.5, 3.6, 3.6)                                      # 把手
    s.ellipse(".", 18, 12.5, 1.8, 1.8, only="m")
    s.rect("m", 4, 7, 16, 16)                                               # 杯子
    s.ellipse("m", 10, 16, 6.5, 2.4)
    s.paint("M", lambda r, c: c >= 15, only="m")                            # 右边的阴影
    s.ellipse("c", 10, 7, 5.8, 1.2)                                         # 咖啡
    heart = lambda r, c: ((((c - 10) / 3) ** 2 + ((13.2 - r) / 3) ** 2 - 1) ** 3
                          - ((c - 10) / 3) ** 2 * ((13.2 - r) / 3) ** 3 <= 0)
    s.paint("p", heart, only="mM")                                          # 爱心
    s.outline("k", "mMsc")
    for col in (7, 12):                                                     # 热气
        s.dots("w", [(1, col), (2, col + 1), (3, col), (4, col - 1), (5, col)])
    return s.rows()


COFFEE = {
    "colors": {
        ".": (246, 234, 216), "t": (190, 140, 96), "T": (166, 118, 78), "s": (236, 240, 244),
        "m": (120, 186, 196), "M": (90, 152, 166), "c": (110, 66, 40), "p": (244, 120, 140),
        "k": (60, 50, 56), "w": (255, 255, 255),
    },
    "art": _coffee(),
}


# ---------------------------------------------------------------------------
# 自然
# ---------------------------------------------------------------------------

def _sunflower():
    s = Sketch(26, 32)
    s.ellipse("w", 4, 4, 3.5, 1.6)                                          # 云
    s.ellipse("w", 6.5, 3, 2.5, 1.6)
    s.ellipse("w", 21, 6, 3, 1.4)
    s.rect("g", 0, 28, 25, 31)                                              # 草地
    s.paint("G", lambda r, c: (c + r) % 4 == 0, only="g")
    s.rect("s", 12, 17, 13, 29)                                             # 茎
    s.ellipse("l", 8.5, 23, 4.2, 1.8, angle=30)                             # 叶子
    s.ellipse("l", 17, 21, 4.2, 1.8, angle=-30)
    s.outline("L", "sl")
    for index in range(12):                                                 # 12 片花瓣
        angle = index * 30
        cx = 12.5 + 7 * math.cos(math.radians(angle))
        cy = 10 + 7 * math.sin(math.radians(angle))
        s.ellipse("y" if index % 2 else "Y", cx, cy, 3.4, 1.7, angle=angle)
    s.outline("O", "yY")
    s.ellipse("b", 12.5, 10, 4.6, 4.6)                                      # 花心
    s.paint("B", lambda r, c: (r + c) % 2 == 0 and math.hypot(c - 12.5, r - 10) < 3.4, only="b")
    return s.rows()


SUNFLOWER = {
    "colors": {
        ".": (170, 214, 246), "w": (255, 255, 255), "g": (110, 184, 84), "G": (84, 150, 70),
        "s": (80, 150, 64), "l": (104, 180, 76), "L": (52, 110, 48), "y": (255, 212, 56),
        "Y": (250, 186, 40), "O": (200, 120, 30), "b": (110, 70, 40), "B": (76, 46, 28),
    },
    "art": _sunflower(),
}


def _rainbow():
    s = Sketch(40, 24)
    s.ellipse("y", 4, 3.5, 2.6, 2.6)                                        # 太阳
    bands = "roygbp"
    for index, char in enumerate(bands):                                    # 一圈一圈的彩虹
        outer = 18.5 - index * 1.5
        s.paint(char, lambda r, c, o=outer: r <= 21 and math.hypot(c - 20, (r - 22) * 1.05) <= o)
    s.paint(".", lambda r, c: r <= 21 and math.hypot(c - 20, (r - 22) * 1.05) <= 9.5)
    for cx in (6, 34):                                                      # 两边的云
        s.ellipse("W", cx, 20.5, 6.5, 2.6)
        s.ellipse("W", cx - 2.4, 18.5, 3, 2.4)
        s.ellipse("W", cx + 2, 17.8, 3.4, 2.8)
        s.ellipse("w", cx, 20, 6, 2)
        s.ellipse("w", cx - 2.4, 18.2, 2.5, 2)
        s.ellipse("w", cx + 2, 17.5, 3, 2.4)
    s.rect("G", 0, 22, 39, 23)                                              # 草
    s.paint("g", lambda r, c: r == 22 and c % 3 != 0, only="G")
    return s.rows()


RAINBOW = {
    "colors": {
        ".": (190, 226, 250), "y": (255, 220, 90), "r": (236, 72, 72), "o": (248, 152, 56),
        "g": (120, 200, 96), "b": (80, 150, 230), "p": (150, 100, 210), "w": (255, 255, 255),
        "W": (210, 222, 236), "G": (86, 160, 76),
    },
    "art": _rainbow(),
}


def _night():
    width, height = 48, 32
    s = Sketch(width, height)
    sky = "1234"
    for index, char in enumerate(sky):                                      # 天空：越往下越亮
        s.paint(char, lambda r, c, i=index: r >= i * 5)
    s.paint("*", lambda r, c: r < 17 and _scatter(r, c, 2, 3))              # 星星
    s.paint("m", lambda r, c: math.hypot(c - 37, r - 7) <= 4.2
            and math.hypot(c - 39, r - 5.6) > 3.8)                         # 弯弯的月亮
    s.paint("M", lambda r, c: r >= 15 + 3 * math.sin(c / 6) + 2 * math.sin(c / 2.6))   # 远山
    s.paint("N", lambda r, c: r >= 19 + 2 * math.sin(c / 5 + 2))                       # 近山
    for col, top in ((6, 14), (11, 16), (15, 13), (33, 15), (40, 13), (44, 16)):       # 松树
        s.polygon("t", [(col - 2.6, top + 8), (col + 2.6, top + 8), (col, top)])
    s.rect("L", 0, 24, width - 1, height - 1)                               # 湖
    s.paint("l", lambda r, c: r % 2 == 0 and abs(c - 37) <= max(0, 4 - (r - 24) // 2), only="L")
    s.paint("l", lambda r, c: r % 3 == 1 and (c * 7 + r) % 11 == 0, only="L")
    return s.rows()


NIGHT = {
    "colors": {
        "1": (24, 30, 72), "2": (36, 44, 98), "3": (58, 62, 124), "4": (92, 80, 146),
        "*": (255, 236, 160), "m": (255, 240, 190), "M": (54, 50, 100),
        "N": (34, 36, 70), "t": (20, 44, 50), "L": (30, 46, 92), "l": (150, 160, 210),
    },
    "art": _night(),
}


def _blossom():
    s = Sketch(36, 28)
    s.rect("g", 0, 23, 35, 27)                                              # 草地
    s.paint("G", lambda r, c: (2 * c + r) % 5 == 0, only="g")
    for cx, cy, rx, ry in ((18, 9, 9, 6), (10, 11.5, 6.2, 4.6), (26, 11.5, 6.2, 4.6),
                           (18, 4.8, 6.2, 4), (12, 6.5, 4.6, 3.4), (24, 6.5, 4.6, 3.4)):
        s.ellipse("p", cx, cy, rx, ry)                                      # 树冠
    s.paint("P", lambda r, c: _scatter(r, c, 5, 14) or r >= 13, only="p")   # 深一点的花
    s.paint("w", lambda r, c: _scatter(r, c, 9, 9), only="p")               # 浅色的花
    s.polygon("b", [(15.5, 23.5), (20.5, 23.5), (19.2, 13), (16.8, 13)])    # 树干
    s.polygon("b", [(16.5, 16), (18, 15), (11, 10), (10, 11)])              # 树枝
    s.polygon("b", [(19.5, 16), (18, 15), (25, 9.5), (26, 10.5)])
    s.paint("B", lambda r, c: c >= 19, only="b")
    s.paint("p", lambda r, c: r >= 15 and _scatter(r, c, 6, 3), only=".gG")   # 飘落的花瓣
    return s.rows()


BLOSSOM = {
    "colors": {
        ".": (206, 232, 250), "g": (150, 206, 116), "G": (118, 176, 92), "p": (248, 178, 200),
        "P": (236, 128, 164), "w": (255, 232, 240), "b": (126, 86, 70), "B": (96, 62, 52),
    },
    "art": _blossom(),
}


# ---------------------------------------------------------------------------
# 物品和地方
# ---------------------------------------------------------------------------

def _balloon():
    s = Sketch(28, 34)
    s.ellipse("w", 4, 26, 4, 1.6)                                           # 云
    s.ellipse("w", 6, 25, 2.6, 1.6)
    s.ellipse("w", 23, 5, 3.6, 1.5)
    s.ellipse("w", 24.5, 4, 2.2, 1.4)
    s.ellipse("e", 14, 11, 9.6, 9.6)                                        # 气球（先用 e 占位）
    s.polygon("e", [(5.2, 14), (22.8, 14), (17.2, 23.2), (10.8, 23.2)])

    def stripe(r, c):
        half = 9.6 if r < 14 else max(3.2, 9.6 - (r - 14) * 0.75)
        return int((c - 14 + half) / (2 * half) * 5)
    for index, char in enumerate("rybyr"):
        s.paint(char, lambda r, c, i=index: stripe(r, c) == i, only="e")
    s.paint("h", lambda r, c: math.hypot(c - 10, r - 6) < 2.2, only="y")    # 高光
    s.outline("k", "rybh")
    for start, end in (((11, 23), (12, 27)), ((17, 23), (16, 27))):         # 绳子
        (c1, r1), (c2, r2) = start, end
        s.dots("k", [(r, round(c1 + (c2 - c1) * (r - r1) / (r2 - r1))) for r in range(r1, r2)])
    s.rect("c", 11, 27, 17, 30)                                             # 篮子
    s.paint("C", lambda r, c: (r + c) % 2 == 0, only="c")
    s.outline("k", "cC")
    return s.rows()


BALLOON = {
    "colors": {
        ".": (186, 222, 248), "w": (255, 255, 255), "r": (232, 70, 70), "y": (255, 214, 80),
        "b": (80, 150, 226), "h": (255, 246, 196), "k": (70, 52, 50), "c": (200, 146, 90),
        "C": (164, 112, 66),
    },
    "art": _balloon(),
}


def _rocket():
    s = Sketch(24, 32)
    s.paint("*", lambda r, c: _scatter(r, c, 8, 3))                         # 星星
    s.ellipse("p", 3.5, 5, 2.4, 2.4)                                        # 小星球
    s.ellipse("P", 3.5, 5, 4, 0.7, angle=-20)
    s.rect("w", 8, 8, 15, 22)                                               # 机身
    s.polygon("r", [(7.6, 8.4), (15.4, 8.4), (11.5, 0.5)])                  # 头
    s.paint("W", lambda r, c: c >= 14, only="w")                            # 阴影
    s.polygon("r", [(8, 16.5), (8, 23.5), (4, 25.5), (4, 20.5)])            # 尾翼
    s.polygon("r", [(15, 16.5), (15, 23.5), (19, 25.5), (19, 20.5)])
    s.rect("r", 11, 18, 12, 23)
    s.ellipse("g", 11.5, 12.5, 3, 3)                                        # 窗户
    s.ellipse("b", 11.5, 12.5, 2, 2)
    s.dots("B", [(11, 11)])
    s.outline("k", "wWrgbB")
    s.polygon("o", [(8.6, 23.5), (14.4, 23.5), (11.5, 31)])                 # 火焰
    s.polygon("y", [(9.8, 23.5), (13.2, 23.5), (11.5, 27.5)])
    return s.rows()


ROCKET = {
    "colors": {
        ".": (32, 38, 78), "*": (255, 236, 150), "p": (170, 130, 230), "P": (230, 190, 120),
        "w": (240, 242, 248), "W": (196, 202, 218), "r": (226, 62, 70), "g": (150, 158, 176),
        "b": (110, 196, 240), "B": (220, 244, 255), "k": (18, 20, 40), "o": (250, 140, 40),
        "y": (255, 226, 100),
    },
    "art": _rocket(),
}


def _lighthouse():
    s = Sketch(32, 40)
    s.polygon("Y", [(15.5, 8.5), (0, 3), (0, 12)])                          # 灯光
    s.polygon("Y", [(15.5, 8.5), (31, 3), (31, 12)])
    s.ellipse("w", 5, 18, 4, 1.5)                                           # 云
    s.ellipse("w", 26, 20, 3.6, 1.4)
    s.rect("s", 0, 31, 31, 39)                                              # 海
    s.paint("S", lambda r, c: (c + 3 * r) % 8 < 2, only="s")
    s.ellipse("g", 15.5, 34, 11, 4.5)                                       # 礁石
    s.ellipse("G", 18, 35.5, 8, 3, only="g")
    s.polygon("t", [(11.6, 12), (19.4, 12), (21.5, 32.5), (9.5, 32.5)])     # 塔
    s.paint("R", lambda r, c: (r - 12) // 4 % 2 == 0, only="t")
    s.paint("w", lambda r, c: True, only="t")
    s.paint("r", lambda r, c: True, only="R")
    s.paint("q", lambda r, c: c >= 18, only="w")                            # 塔右边的阴影
    s.paint("Q", lambda r, c: c >= 18, only="r")
    s.rect("b", 15, 28, 16, 31)                                             # 门
    s.rect("b", 15, 19, 16, 20)                                             # 窗
    s.rect("k", 11, 11, 20, 11)                                             # 走廊
    s.rect("y", 13, 7, 18, 10)                                              # 灯室
    s.rect("k", 13, 7, 13, 10)
    s.rect("k", 18, 7, 18, 10)
    s.polygon("r", [(12, 7.4), (19, 7.4), (15.5, 3)])                       # 屋顶
    s.outline("k", "wqrQbyR")
    s.dots("k", [(2, 15), (2, 16)])                                         # 屋顶上的小尖
    s.dots("k", [(24, 5), (23, 6), (24, 7), (27, 9), (26, 10), (27, 11)])   # 海鸥
    return s.rows()


LIGHTHOUSE = {
    "colors": {
        ".": (160, 206, 240), "Y": (250, 238, 180), "w": (255, 255, 255), "s": (60, 140, 200),
        "S": (110, 180, 228), "g": (130, 130, 140), "G": (96, 96, 108),
        "r": (220, 60, 60), "q": (216, 220, 230), "Q": (176, 44, 48),
        "b": (90, 60, 50), "k": (44, 40, 50), "y": (255, 222, 80),
    },
    "art": _lighthouse(),
}
