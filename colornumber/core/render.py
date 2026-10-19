"""
把填色进度画成图片（用 Pillow）：缩略图、导出 PNG、GIF 和 MP4 的每一帧都用它。
"""

from PIL import Image


def grey_of(color):
    """
    把颜色变成浅灰色，但保留明暗：原来深的颜色灰得深一点。
    没填的格子用它显示，远看就能看出图案的轮廓。
    """
    red, green, blue = color
    lightness = 0.299 * red + 0.587 * green + 0.114 * blue
    grey = int(175 + lightness * 0.28)
    return (grey, grey, grey)


def render_state(picture, painted, cell_pixels=1, unfilled="grey"):
    """
    画出一张图当前的样子。

    painted 是摊平的列表，0 表示没填。
    unfilled 决定没填的格子怎么画："grey" 是浅灰轮廓，"white" 是白色。
    """
    width, height = picture.width, picture.height
    answer = picture.flat_numbers()
    pixels = []
    for idx, number in enumerate(painted):
        if number:
            pixels.append(picture.color_of(number))
        elif unfilled == "grey":
            pixels.append(grey_of(picture.color_of(answer[idx])))
        else:
            pixels.append((255, 255, 255))
    image = Image.new("RGB", (width, height))
    image.putdata(pixels)
    if cell_pixels > 1:
        image = image.resize((width * cell_pixels, height * cell_pixels), Image.Resampling.NEAREST)
    return image


def cell_pixels_for(picture, long_side):
    """算出每格画多少像素，才能让长边大约等于 long_side。"""
    return max(1, long_side // max(picture.width, picture.height))
