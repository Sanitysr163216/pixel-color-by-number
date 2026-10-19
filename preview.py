"""
预览照片转换的效果（还没有游戏界面时用来看效果）。

用法（在终端里，先 conda activate color-number）：

    python preview.py 照片.jpg
    python preview.py 照片.jpg --size 64 --colors 20

会在 output 文件夹里生成两张图：
- *_colored.png   转换后的像素图（填完后的样子）
- *_numbers.png   带编号的白色格子（开始填色前的样子）
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from colornumber.core import converter

CELL_PIXELS = 24   # 预览图里每个格子画多大


def render_colored(picture):
    """把每个格子画成它的颜色。"""
    image = Image.new("RGB", (picture.width, picture.height))
    for row in range(picture.height):
        for col in range(picture.width):
            image.putpixel((col, row), picture.color_of(picture.numbers[row][col]))
    return image.resize(
        (picture.width * CELL_PIXELS, picture.height * CELL_PIXELS),
        Image.Resampling.NEAREST,
    )


def render_numbers(picture):
    """画出白色格子、灰色网格线和每格的编号。"""
    size = (picture.width * CELL_PIXELS, picture.height * CELL_PIXELS)
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=CELL_PIXELS // 2)
    for row in range(picture.height):
        for col in range(picture.width):
            left = col * CELL_PIXELS
            top = row * CELL_PIXELS
            draw.rectangle(
                (left, top, left + CELL_PIXELS, top + CELL_PIXELS),
                outline=(210, 210, 210),
            )
            draw.text(
                (left + CELL_PIXELS / 2, top + CELL_PIXELS / 2),
                str(picture.numbers[row][col]),
                fill=(90, 90, 90),
                font=font,
                anchor="mm",
            )
    return image


def print_palette(picture):
    """打印每种颜色有多少格。"""
    print(f"格子：{picture.width} × {picture.height}，颜色：{picture.color_count} 种")
    flat = picture.flat_numbers()
    for number in range(1, picture.color_count + 1):
        print(f"  {number:>2} 号  RGB{picture.color_of(number)}  {flat.count(number)} 格")


def main():
    parser = argparse.ArgumentParser(description="预览照片转换成填色图的效果")
    parser.add_argument("photo", help="照片文件路径")
    parser.add_argument("--size", type=int, default=converter.DEFAULT_GRID_SIZE,
                        help="长边的格子数")
    parser.add_argument("--colors", type=int, default=converter.DEFAULT_COLOR_COUNT,
                        help="颜色数量")
    parser.add_argument("--no-clean", action="store_true", help="不清理杂色点")
    args = parser.parse_args()

    picture = converter.convert_file(
        args.photo, grid_size=args.size, color_count=args.colors, clean=not args.no_clean
    )
    print_palette(picture)

    output = Path("output")
    output.mkdir(exist_ok=True)
    stem = Path(args.photo).stem
    render_colored(picture).save(output / f"{stem}_colored.png")
    render_numbers(picture).save(output / f"{stem}_numbers.png")
    print(f"预览图已保存到 {output}/ 文件夹")


if __name__ == "__main__":
    main()
