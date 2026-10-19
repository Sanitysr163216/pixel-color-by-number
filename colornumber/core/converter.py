"""
把一张照片转换成填色图（Picture）。

转换分五步：
1. load_image       读取照片，修正手机照片的旋转方向，透明部分变成白色
2. adjust_image     调整亮度、对比度、饱和度
3. pixelate         缩小成格子：长边变成 grid_size 格，每格取这一块区域的平均颜色
4. reduce_colors    把颜色减少到 color_count 种
5. remove_stray_cells  清理杂色点：四周没有同色邻居的孤立格子，改成邻居里最多的颜色

最后把用到的颜色重新编号：用得最多的颜色是 1 号，其次是 2 号，依此类推。
"""

from PIL import Image, ImageEnhance, ImageOps

from colornumber.core.picture import Picture

# iPhone 照片是 HEIC 格式，Pillow 需要 pillow-heif 才能读取；没装就只支持普通格式
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# 默认值和可调范围（上限可以在设置里解锁得更大，见 settings.py）
DEFAULT_GRID_SIZE = 48
DEFAULT_COLOR_COUNT = 16
GRID_SIZE_MIN = 16
COLOR_COUNT_MIN = 4


def load_image(path):
    """读取图片文件，返回 RGB 模式的图片。"""
    image = Image.open(path)
    # 手机照片常把"旋转方向"单独记在 EXIF 信息里，这里把图真正转正
    image = ImageOps.exif_transpose(image)
    # 带透明部分的图（比如 PNG）：先铺一层白底，避免透明处变成黑色
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        background = Image.new("RGBA", image.size, "white")
        background.alpha_composite(image)
        image = background
    return image.convert("RGB")


def adjust_image(image, brightness=1.0, contrast=1.0, saturation=1.0):
    """调整亮度、对比度、饱和度。1.0 表示不变，大于 1 增强，小于 1 减弱。"""
    if brightness != 1.0:
        image = ImageEnhance.Brightness(image).enhance(brightness)
    if contrast != 1.0:
        image = ImageEnhance.Contrast(image).enhance(contrast)
    if saturation != 1.0:
        image = ImageEnhance.Color(image).enhance(saturation)
    return image


def pixelate(image, grid_size):
    """把图片缩小成格子，长边变成 grid_size 格，短边按比例计算。"""
    width, height = image.size
    if width >= height:
        new_width = grid_size
        new_height = max(1, round(height * grid_size / width))
    else:
        new_height = grid_size
        new_width = max(1, round(width * grid_size / height))
    # BOX 缩放：每个格子取原图对应区域所有像素的平均颜色
    return image.resize((new_width, new_height), Image.Resampling.BOX)


def reduce_colors(small_image, color_count):
    """
    把颜色减少到最多 color_count 种。

    返回 (numbers, palette)：
    - numbers 是列表套列表，每格存的是颜色的下标（从 0 开始，还没重新编号）
    - palette 是颜色列表
    """
    reduced = small_image.quantize(
        colors=color_count,
        method=Image.Quantize.MEDIANCUT,
        kmeans=3,                    # 再微调几轮，让颜色更贴近原图
        dither=Image.Dither.NONE,    # 不要抖动：抖动会产生大量杂色点
    )
    width, height = reduced.size
    flat = list(reduced.get_flattened_data())   # 所有格子排成一行
    numbers = [flat[row * width:(row + 1) * width] for row in range(height)]

    raw = reduced.getpalette()       # [r, g, b, r, g, b, ...]
    palette = [tuple(raw[i * 3:i * 3 + 3]) for i in range(len(raw) // 3)]
    return numbers, palette


def _neighbors(numbers, row, col):
    """返回某格上下左右四个邻居的值（在边缘的格子邻居更少）。"""
    height = len(numbers)
    width = len(numbers[0])
    result = []
    for d_row, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        r = row + d_row
        c = col + d_col
        if 0 <= r < height and 0 <= c < width:
            result.append(numbers[r][c])
    return result


def remove_stray_cells(numbers):
    """
    清理杂色点：如果一个格子的上下左右都没有和它同色的邻居，
    就把它改成邻居里出现次数最多的颜色。返回新的格子，不修改原来的。
    """
    cleaned = [row[:] for row in numbers]
    for row in range(len(numbers)):
        for col in range(len(numbers[0])):
            neighbors = _neighbors(numbers, row, col)
            if neighbors and numbers[row][col] not in neighbors:
                cleaned[row][col] = max(neighbors, key=neighbors.count)
    return cleaned


def _renumber(numbers, palette):
    """
    重新编号：去掉没用到的颜色，用得最多的颜色编为 1 号。
    返回 Picture。
    """
    usage = {}
    for row in numbers:
        for index in row:
            usage[index] = usage.get(index, 0) + 1

    # 按使用次数从多到少排序
    ordered = sorted(usage, key=lambda index: usage[index], reverse=True)
    new_number = {old: position + 1 for position, old in enumerate(ordered)}

    new_palette = [palette[old] for old in ordered]
    new_numbers = [[new_number[index] for index in row] for row in numbers]
    return Picture(palette=new_palette, numbers=new_numbers)


def convert(image, grid_size=DEFAULT_GRID_SIZE, color_count=DEFAULT_COLOR_COUNT,
            brightness=1.0, contrast=1.0, saturation=1.0, clean=True, crop=None):
    """
    把一张已读取的图片转换成 Picture。
    crop 是裁剪框 (左, 上, 右, 下)，单位是原图的像素；None 表示不裁剪。
    """
    if crop is not None:
        image = image.crop(crop)
    image = adjust_image(image, brightness, contrast, saturation)
    small = pixelate(image, grid_size)
    numbers, palette = reduce_colors(small, color_count)
    if clean:
        numbers = remove_stray_cells(numbers)
    return _renumber(numbers, palette)


def convert_file(path, **options):
    """读取图片文件并转换成 Picture。options 和 convert() 的参数相同。"""
    return convert(load_image(path), **options)
