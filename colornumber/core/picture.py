"""
一张填色图的数据。

一张图由两样东西组成：
- palette（调色板）：一个列表，存放这张图用到的所有颜色。
- numbers（编号格子）：一个"列表套列表"，记录每个格子的编号。

编号从 1 开始，和玩家在屏幕上看到的一样。
编号 n 对应的颜色是 palette[n - 1]（因为列表的下标从 0 开始）。

例子：一张 3 格宽、2 格高的图

    palette = [(255, 0, 0), (0, 0, 255)]    # 1 号是红色，2 号是蓝色
    numbers = [
        [1, 1, 2],     # 第 0 行
        [2, 1, 2],     # 第 1 行
    ]

    numbers[0][2]  →  2，表示第 0 行第 2 列的格子是 2 号（蓝色）

游戏运行时，为了速度，常把格子"摊平"成一个长列表（flat），
第 row 行第 col 列的格子在长列表里的位置是 row * width + col。
"""

from dataclasses import dataclass


@dataclass
class Picture:
    """一张填色图：调色板加编号格子。"""

    palette: list   # 每个元素是一个 (红, 绿, 蓝) 元组，取值 0–255
    numbers: list   # numbers[行][列] 是该格的编号，从 1 开始

    @property
    def width(self):
        """宽度：每一行有多少格。"""
        return len(self.numbers[0])

    @property
    def height(self):
        """高度：一共有多少行。"""
        return len(self.numbers)

    @property
    def color_count(self):
        """这张图一共用了多少种颜色。"""
        return len(self.palette)

    def color_of(self, number):
        """返回某个编号对应的颜色。"""
        return self.palette[number - 1]

    def flat_numbers(self):
        """把所有格子的编号摊平成一个长列表。"""
        return [number for row in self.numbers for number in row]

    def to_dict(self):
        """转成可以存进 JSON 文件的字典。"""
        return {
            "width": self.width,
            "palette": [list(color) for color in self.palette],
            "numbers": self.flat_numbers(),
        }

    @classmethod
    def from_dict(cls, data):
        """从 to_dict() 生成的字典还原。"""
        width = data["width"]
        flat = data["numbers"]
        numbers = [flat[i:i + width] for i in range(0, len(flat), width)]
        palette = [tuple(color) for color in data["palette"]]
        return cls(palette=palette, numbers=numbers)
