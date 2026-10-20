"""
按钮上的小图标，用"字符画"画出来：# 是有颜色的点，. 是透明的点。

图标是白色的，显示时用 Kivy 的 Color 染成需要的颜色（和按钮文字同色）。
放大时用"最近邻"方式，并且只放大整数倍，所以图标的像素边缘总是清清楚楚的。
"""

from kivy.metrics import dp
from PIL import Image

from colornumber.ui.common import pil_to_texture

ICONS = {
    "brush": [
        "........###.",
        ".......#####",
        "......#.####",
        ".....###.##.",
        "....#####...",
        "...#####....",
        "..#####.....",
        ".#####......",
        ".####.......",
        "#.##........",
        "##..........",
        "............",
    ],
    "wand": [
        "........#...",
        "........#...",
        "......#####.",
        ".......###..",
        "......##.##.",
        ".....#......",
        "....##......",
        "...##.......",
        "..##........",
        ".##.........",
        "##..........",
        "#...........",
    ],
    "move": [
        ".....##.....",
        "....####....",
        "...######...",
        "..#..##..#..",
        ".##..##..##.",
        "############",
        "############",
        ".##..##..##.",
        "..#..##..#..",
        "...######...",
        "....####....",
        ".....##.....",
    ],
    "bucket": [
        "...####.....",
        "..#....#....",
        "..#....#....",
        ".##########.",
        ".##########.",
        ".#########..",
        "..########.#",
        "..#######..#",
        "...######.##",
        "...#####..##",
        "....####....",
        "............",
    ],
    "zoom_in": [
        "..#####.....",
        ".##...##....",
        "##..#..##...",
        "#...#...#...",
        "#.#####.#...",
        "#...#...#...",
        "##..#..##...",
        ".##...###...",
        "..#####.##..",
        "........###.",
        ".........###",
        "..........##",
    ],
    "zoom_out": [
        "..#####.....",
        ".##...##....",
        "##.....##...",
        "#.......#...",
        "#.#####.#...",
        "#.......#...",
        "##.....##...",
        ".##...###...",
        "..#####.##..",
        "........###.",
        ".........###",
        "..........##",
    ],
    "fit": [
        "####....####",
        "####....####",
        "##........##",
        "##........##",
        "............",
        "............",
        "............",
        "............",
        "##........##",
        "##........##",
        "####....####",
        "####....####",
    ],
    "undo": [
        "...#........",
        "..##........",
        ".#######....",
        "#########...",
        ".##.....##..",
        "..#......##.",
        "..........##",
        "..........##",
        ".........##.",
        "......####..",
        "...#####....",
        "............",
    ],
    "help": [
        "...######...",
        "..########..",
        ".###....###.",
        ".##......##.",
        "........###.",
        ".......###..",
        ".....###....",
        ".....##.....",
        ".....##.....",
        "............",
        ".....##.....",
        ".....##.....",
    ],
    # 笔刷大小：1×1、3×3、5×5 个格子（每个格子画成 2×2 个点）
    "size_1": ["." * 12] * 5 + ["....." + "##" + "....."] * 2 + ["." * 12] * 5,
    "size_3": ["." * 12] * 3 + ["..." + "######" + "..."] * 6 + ["." * 12] * 3,
    "size_5": ["." * 12] + ["." + "##########" + "."] * 10 + ["." * 12],
}

# 重做的箭头就是撤销的箭头左右翻过来
ICONS["redo"] = [row[::-1] for row in ICONS["undo"]]

ART_SIZE = 12
_textures = {}


def icon_texture(name):
    """取出图标的贴图（第一次用到时才画，之后重复使用）。"""
    if name not in _textures:
        rows = ICONS[name]
        image = Image.new("RGBA", (ART_SIZE, ART_SIZE), (255, 255, 255, 0))
        for y, row in enumerate(rows):
            for x, char in enumerate(row):
                if char == "#":
                    image.putpixel((x, y), (255, 255, 255, 255))
        _textures[name] = pil_to_texture(image)
    return _textures[name]


def icon_size():
    """图标显示的边长（屏幕像素）：约 20dp，取字符画的整数倍。"""
    return ART_SIZE * max(1, round(dp(20) / ART_SIZE))


# ---------------------------------------------------------------------------
# 带图标的按钮：图标在左、文字在右；没有文字时图标居中
# ---------------------------------------------------------------------------

from kivy.lang import Builder  # noqa: E402
from kivy.properties import NumericProperty, ObjectProperty, StringProperty  # noqa: E402

from colornumber.ui.common import Chip, LongPressButton, RoundButton  # noqa: E402


class IconMixin:
    icon = StringProperty("")                          # 图标的名字，见上面的 ICONS
    icon_tex = ObjectProperty(None, allownone=True)    # 图标的贴图，换图标时自动更新
    icon_px = NumericProperty(0)

    def __init__(self, **kwargs):
        self.icon_px = icon_size()
        super().__init__(**kwargs)

    def on_icon(self, _widget, name):
        self.icon_tex = icon_texture(name) if name else None


class IconChip(IconMixin, Chip):
    """可以选中的带图标按钮（工具、笔刷大小）。"""


class IconButton(IconMixin, RoundButton):
    """普通的带图标按钮。"""


class IconLongPressButton(IconMixin, LongPressButton):
    """可以长按的带图标按钮（油漆桶）。"""


Builder.load_string("""
<IconChip,IconButton,IconLongPressButton>:
    text_size: self.size
    halign: "left" if self.text else "center"
    valign: "middle"
    shorten: True
    padding: (dp(10) + self.icon_px + dp(8), 0, dp(4), 0) if self.text else (0, 0, 0, 0)
    canvas.after:
        Color:
            rgba: self.color if self.icon else (0, 0, 0, 0)
        Rectangle:
            texture: self.icon_tex
            size: self.icon_px, self.icon_px
            pos: (round(self.x + dp(10)) if self.text else round(self.center_x - self.icon_px / 2)), round(self.center_y - self.icon_px / 2)
""")
