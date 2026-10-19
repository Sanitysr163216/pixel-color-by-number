"""
把一张照片转换成填色图（Picture）。

转换步骤：
1. load_image       读取照片（支持 iPhone 的 HEIC），修正旋转方向，透明部分变成白色
2. adjust_image     调整亮度、对比度、饱和度；可以把背景虚化（需要先识别出主体）
3. 算出每个格子的颜色：先把图缩小到"格子数 × 几倍"，再按格子求平均颜色，
   然后做一次"锐化"，让边缘两侧的格子颜色分得更开（这样人脸、眼睛不会糊）
4. 选调色板：在 Lab 颜色空间里用 k-means 聚类。Lab 空间里两个颜色的距离
   接近人眼感觉到的差别，所以选出的颜色彼此更好区分。
   - 平坦的大片区域（比如天空）权重低，细节多的地方（边缘、人脸）权重高
   - 先用七成名额覆盖整张图，剩下三成专门留给"还没被表示好"的颜色
     （眼白、嘴唇、高光这类面积小但很显眼的颜色）
   - 几乎一样的颜色（差别小于 MERGE_DELTA_E）合并成一种
5. 每个格子选最接近的颜色；清理杂色点：四周都不同色的孤立格子，
   如果和邻居颜色差别不大才合并，差别大的（比如眼睛里的高光）保留
6. 重新编号：用得最多的颜色是 1 号

另外提供 recommend_color_count()：为当前图片推荐一个颜色数。

经典模式（classic=True）用的是第一版的做法：每格取平均颜色，再用 Pillow 的
"中位切分"减少颜色，不锐化。边缘没那么清楚，但颜色过渡更平滑。

颜色的距离单位是 ΔE（Delta E）：大约 2 是人眼刚好能分辨的差别，
10 以下在调色板里就容易看混。
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

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
DEFAULT_DETAIL = 0.5
GRID_SIZE_MIN = 16
COLOR_COUNT_MIN = 4

FINE_PIXELS = 1_200_000     # 计算格子颜色时，先把图缩到大约这么多像素
MERGE_DELTA_E = 4.0         # 差别小于这个的两种颜色会合并
SIMILAR_DELTA_E = 10.0      # 差别小于这个的两种颜色算"很接近"


# ---------------------------------------------------------------------------
# 读取和调整
# ---------------------------------------------------------------------------

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


def blur_background(image, subject):
    """把主体以外的部分虚化。subject 是和图片一样大的数组，1 是主体，0 是背景。"""
    radius = max(2, 0.012 * max(image.size))
    blurred = image.filter(ImageFilter.GaussianBlur(radius))
    mask = Image.fromarray(np.clip(subject * 255, 0, 255).astype(np.uint8))
    mask = mask.filter(ImageFilter.GaussianBlur(radius / 3))     # 边界柔和一点
    return Image.composite(image, blurred, mask)


def grid_dimensions(width, height, grid_size):
    """长边是 grid_size 格，短边按比例计算。"""
    if width >= height:
        return grid_size, max(1, round(height * grid_size / width))
    return max(1, round(width * grid_size / height)), grid_size


# ---------------------------------------------------------------------------
# 颜色空间：sRGB ↔ Lab
# ---------------------------------------------------------------------------

_RGB_TO_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375],
                        [0.2126729, 0.7151522, 0.0721750],
                        [0.0193339, 0.1191920, 0.9503041]])
_WHITE = np.array([0.95047, 1.0, 1.08883])


def _to_linear(srgb):
    """屏幕上的颜色值（0–1）转成"线性光"，求平均要在线性光里做才准确。"""
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)


def _to_srgb(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


def _linear_to_lab(linear):
    xyz = linear @ _RGB_TO_XYZ.T / _WHITE
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16,
                     500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], -1)


def _lab_to_linear(lab):
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], -1)
    xyz = np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27)) * _WHITE
    return xyz @ np.linalg.inv(_RGB_TO_XYZ).T


def rgb_to_lab(colors):
    """RGB（0–255）转 Lab。colors 可以是一个颜色，也可以是一组颜色。"""
    return _linear_to_lab(_to_linear(np.asarray(colors, dtype=np.float64) / 255))


def lab_to_rgb(lab):
    """Lab 转 RGB（0–255 的整数）。"""
    return np.round(_to_srgb(_lab_to_linear(np.asarray(lab))) * 255).astype(np.uint8)


def _blur3(array):
    """3×3 的柔和模糊（权重 1-2-1），边缘用最近的值补齐。"""
    pad = [(1, 1), (1, 1)] + [(0, 0)] * (array.ndim - 2)
    p = np.pad(array, pad, mode="edge")
    rows = (p[:, :-2] + 2 * p[:, 1:-1] + p[:, 2:]) / 4
    return (rows[:-2] + 2 * rows[1:-1] + rows[2:]) / 4


def _normalize(values):
    """除以第 90 百分位数，让大部分值落在 0–1，限制在 0–2。"""
    return np.clip(values / max(1e-6, np.percentile(values, 90)), 0, 2)


# ---------------------------------------------------------------------------
# 第 3 步：每个格子的颜色和权重
# ---------------------------------------------------------------------------

def _cells(image, grid_size, detail, importance=None, subject=None):
    """
    返回 (宽, 高, 每格 Lab 颜色, 每格权重, 每格重要程度)。
    importance 和 subject 是和 image 一样大的数组（0–1），来自 AI 识别，可以没有。
    """
    width, height = grid_dimensions(*image.size, grid_size)
    factor = int(np.clip(np.sqrt(FINE_PIXELS / (width * height)), 2, 8))
    fine = image.resize((width * factor, height * factor), Image.Resampling.LANCZOS)
    linear = _to_linear(np.asarray(fine, dtype=np.float64) / 255)

    # 按格子求平均颜色（在线性光里平均），再转成 Lab
    cell_lab = _linear_to_lab(linear.reshape(height, factor, width, factor, 3).mean((1, 3)))

    # 每格里亮度变化有多剧烈（边缘、纹理多的地方大）
    lightness = _linear_to_lab(linear)[..., 0]
    gx = np.zeros_like(lightness)
    gy = np.zeros_like(lightness)
    gx[:, 1:-1] = lightness[:, 2:] - lightness[:, :-2]
    gy[1:-1] = lightness[2:] - lightness[:-2]
    edges = _normalize(np.hypot(gx, gy).reshape(height, factor, width, factor).mean((1, 3)))

    # AI 识别出的重要区域（人脸、五官），按格子大小缩放
    cell_importance = np.zeros((height, width))
    if importance is not None:
        cell_importance = _resize_map(importance, width, height)

    # 锐化：格子颜色减去周围的平均颜色，再按比例加回去，边缘两侧就分得更开。
    # 重要区域锐化得更多，眼睛、嘴巴的线条更清楚
    strength = (1.2 * detail * (1 + 0.8 * cell_importance))[..., None] * np.array([1, 0.5, 0.5])
    cells = cell_lab + strength * (cell_lab - _blur3(cell_lab))
    cells[..., 0] = np.clip(cells[..., 0], 0, 100)

    # 权重：平坦区域低，边缘、和周围不同的格子、鲜艳的颜色高
    contrast = _normalize(np.sqrt(((cells - _blur3(cells)) ** 2).sum(-1)))
    chroma = np.hypot(cells[..., 1], cells[..., 2])
    weights = 0.3 + (0.5 + 2 * detail) * (edges + contrast) / 4 + 0.4 * np.clip(chroma / 60, 0, 1)
    weights *= 1 + 4 * cell_importance          # 重要区域分到更多颜色
    if subject is not None:
        weights *= 0.35 + 0.65 * _resize_map(subject, width, height)
    return width, height, cells, weights, cell_importance


def _resize_map(values, width, height):
    """把 0–1 的数组缩放到格子大小（按面积平均）。"""
    image = Image.fromarray(np.asarray(values, dtype=np.float32))
    return np.asarray(image.resize((width, height), Image.Resampling.BOX), dtype=np.float64)


# ---------------------------------------------------------------------------
# 第 4 步：选调色板（加权 k-means）
# ---------------------------------------------------------------------------

def _nearest(points, centers):
    """每个点离哪个中心最近。用 |p|² - 2p·c + |c|² 一次算出所有距离。"""
    distance = (points ** 2).sum(1)[:, None] - 2 * points @ centers.T + (centers ** 2).sum(1)[None]
    return distance.argmin(1)


def _kmeans(points, weights, count, iterations=12, seed=0, sample=30000):
    """
    加权 k-means：把点分成 count 组，每组的中心就是一种颜色。
    点太多时按权重随机抽样，速度快很多，结果几乎一样。
    """
    rng = np.random.default_rng(seed)
    if len(points) > sample:
        chosen = rng.choice(len(points), sample, replace=True, p=weights / weights.sum())
        points, weights = points[chosen], np.ones(sample)
    # k-means++ 选初始中心：离已有中心越远的点越容易被选中
    centers = [points[rng.choice(len(points), p=weights / weights.sum())]]
    nearest = ((points - centers[0]) ** 2).sum(1)
    for _ in range(1, count):
        chance = nearest * weights
        if chance.sum() <= 0:
            break
        center = points[rng.choice(len(points), p=chance / chance.sum())]
        centers.append(center)
        nearest = np.minimum(nearest, ((points - center) ** 2).sum(1))
    centers = np.array(centers)
    for _ in range(iterations):
        labels = _nearest(points, centers)
        total = np.bincount(labels, weights, minlength=len(centers))
        sums = np.stack([np.bincount(labels, weights * points[:, i], minlength=len(centers))
                         for i in range(3)], 1)
        used = total > 0
        centers[used] = sums[used] / total[used, None]
    return centers


def _refine(points, weights, centers, iterations=4):
    """再做几轮"每个中心移到它那组点的平均位置"。"""
    for _ in range(iterations):
        labels = _nearest(points, centers)
        for index in range(len(centers)):
            group = labels == index
            if group.any():
                centers[index] = np.average(points[group], axis=0, weights=weights[group])
    return centers


def _palette(points, weights, count):
    """两阶段选色，再合并几乎一样的颜色。返回 Lab 颜色数组。"""
    main_count = max(2, round(count * 0.7))
    centers = _kmeans(points, weights, main_count)
    error = np.sqrt(((points - centers[_nearest(points, centers)]) ** 2).sum(1))
    poorly_shown = error > 10
    extra_count = count - main_count
    if extra_count > 0 and poorly_shown.sum() >= extra_count:
        extra = _kmeans(points[poorly_shown], (weights * error)[poorly_shown], extra_count, seed=1)
        centers = _refine(points, weights, np.vstack([centers, extra]))
    while len(centers) > 2:
        distance = np.sqrt(((centers[:, None] - centers[None]) ** 2).sum(-1))
        distance += np.eye(len(centers)) * 1e9
        i, j = np.unravel_index(distance.argmin(), distance.shape)
        if distance[i, j] >= MERGE_DELTA_E:
            break
        labels = _nearest(points, centers)
        weight_i, weight_j = weights[labels == i].sum(), weights[labels == j].sum()
        centers[i] = (centers[i] * weight_i + centers[j] * weight_j) / max(1e-9, weight_i + weight_j)
        centers = np.delete(centers, j, 0)
    return centers


# ---------------------------------------------------------------------------
# 第 5 步：清理杂色点
# ---------------------------------------------------------------------------

def _clean(labels, centers, threshold, passes=2):
    """
    孤立的格子（上下左右都和它不同色）改成邻居里最多的颜色，
    但只在两种颜色差别小于 threshold 时才改。threshold 可以是数字，也可以是每格一个值。
    """
    distance = np.sqrt(((centers[:, None] - centers[None]) ** 2).sum(-1))
    for _ in range(passes):
        padded = np.pad(labels, 1, constant_values=-1)
        neighbors = np.stack([padded[:-2, 1:-1], padded[2:, 1:-1],
                              padded[1:-1, :-2], padded[1:-1, 2:]], -1)
        isolated = (neighbors != labels[..., None]).all(-1)
        # 每个邻居的颜色在四个邻居里出现几次，取出现最多的
        votes = np.stack([((neighbors == neighbors[..., i:i + 1]) & (neighbors >= 0)).sum(-1)
                          for i in range(4)], -1)
        votes[neighbors < 0] = -1
        replacement = np.take_along_axis(neighbors, votes.argmax(-1)[..., None], -1)[..., 0]
        close = distance[labels, np.maximum(replacement, 0)] < threshold
        labels = np.where(isolated & close & (replacement >= 0), replacement, labels)
    return labels


# ---------------------------------------------------------------------------
# 对外的函数
# ---------------------------------------------------------------------------

def _prepare(image, brightness, contrast, saturation, crop, importance, subject, simplify_background):
    """裁剪、调整，并把 AI 识别结果裁成同样大小。"""
    if crop is not None:
        left, top, right, bottom = crop
        image = image.crop(crop)
        if importance is not None:
            importance = importance[top:bottom, left:right]
        if subject is not None:
            subject = subject[top:bottom, left:right]
    image = adjust_image(image, brightness, contrast, saturation)
    if simplify_background and subject is not None:
        image = blur_background(image, subject)
    else:
        subject = None
    return image, importance, subject


def _convert_classic(image, grid_size, color_count, clean):
    """
    经典模式（第一版的算法）：
    1. BOX 缩放：每个格子取原图对应区域的平均颜色
    2. 用 Pillow 的"中位切分"把颜色减少到 color_count 种（不抖动）
    3. 清理杂色点：四周都不同色的格子改成邻居里最多的颜色（不看颜色差别）
    """
    width, height = grid_dimensions(*image.size, grid_size)
    small = image.resize((width, height), Image.Resampling.BOX)
    reduced = small.quantize(colors=color_count, method=Image.Quantize.MEDIANCUT,
                             kmeans=3, dither=Image.Dither.NONE)
    labels = np.asarray(reduced, dtype=np.int64)
    palette = np.array(reduced.getpalette(), dtype=np.uint8).reshape(-1, 3)
    if clean:
        labels = _clean(labels, rgb_to_lab(palette), threshold=np.inf, passes=1)
    return _renumber(labels, palette)


def convert(image, grid_size=DEFAULT_GRID_SIZE, color_count=DEFAULT_COLOR_COUNT,
            brightness=1.0, contrast=1.0, saturation=1.0, clean=True, crop=None,
            detail=DEFAULT_DETAIL, importance=None, subject=None, simplify_background=False,
            classic=False):
    """
    把一张已读取的图片转换成 Picture。

    crop        裁剪框 (左, 上, 右, 下)，单位是原图的像素；None 表示不裁剪
    detail      细节程度 0–1：越大边缘越锐利、细节越多，杂色点也越多
    importance  AI 识别出的重要区域（人脸、眼睛等），和原图一样大的 0–1 数组
    subject     AI 识别出的主体，和原图一样大的 0–1 数组
    simplify_background  为 True 时把主体以外的背景虚化，颜色多分给主体
    classic     为 True 时用经典模式（第一版的算法，颜色过渡更平滑；不用 detail 和 importance）
    """
    image, importance, subject = _prepare(image, brightness, contrast, saturation, crop,
                                          importance, subject, simplify_background)
    if classic:
        return _convert_classic(image, grid_size, color_count, clean)
    width, height, cells, weights, cell_importance = _cells(image, grid_size, detail, importance, subject)
    points = cells.reshape(-1, 3)
    centers = _palette(points, weights.reshape(-1), color_count)
    labels = _nearest(points, centers).reshape(height, width)
    if clean:
        # 重要区域（人脸）里更不容易被当成杂色点
        labels = _clean(labels, centers, (25 - 15 * detail) * (1 - 0.6 * cell_importance))
    return _renumber(labels, lab_to_rgb(centers))


def _renumber(labels, palette):
    """去掉没用到的颜色，用得最多的颜色编为 1 号。"""
    usage = np.bincount(labels.ravel(), minlength=len(palette))
    order = [index for index in np.argsort(-usage, kind="stable") if usage[index] > 0]
    new_number = np.zeros(len(palette), dtype=np.int64)
    for position, index in enumerate(order):
        new_number[index] = position + 1
    numbers = new_number[labels].tolist()
    return Picture(palette=[tuple(int(v) for v in palette[index]) for index in order], numbers=numbers)


def convert_file(path, **options):
    """读取图片文件并转换成 Picture。options 和 convert() 的参数相同。"""
    return convert(load_image(path), **options)


def similar_color_pairs(palette, threshold=SIMILAR_DELTA_E):
    """调色板里有几对颜色差别小于 threshold（很难分辨）。"""
    lab = rgb_to_lab(palette)
    distance = np.sqrt(((lab[:, None] - lab[None]) ** 2).sum(-1))
    return int(((distance < threshold).sum() - len(palette)) // 2)


def recommend_color_count(image, grid_size=DEFAULT_GRID_SIZE, max_colors=36,
                          brightness=1.0, contrast=1.0, saturation=1.0, crop=None,
                          detail=DEFAULT_DETAIL, importance=None, subject=None,
                          simplify_background=False):
    """
    推荐颜色数：既要足够还原这张图，又尽量不出现很接近的颜色。

    对每个候选颜色数 k 算两样东西：
    - 平均误差：格子颜色和它所用颜色之间的平均 ΔE
    - 很接近的颜色有几对（ΔE < 10）
    "够用"的颜色数：误差降到 4.5 以下，或者再多 4 种颜色误差也只少 0.6 以内；
    "上限"：很接近的颜色超过 max(2, k/8) 对之前的最大 k。取两者中较小的。
    """
    image, importance, subject = _prepare(image, brightness, contrast, saturation, crop,
                                          importance, subject, simplify_background)
    _w, _h, cells, weights, _i = _cells(image, grid_size, detail, importance, subject)
    points, weights = cells.reshape(-1, 3), weights.reshape(-1)
    rng = np.random.default_rng(0)
    if len(points) > 6000:
        chosen = rng.choice(len(points), 6000, replace=False)
        points, weights = points[chosen], weights[chosen]

    max_colors = max(COLOR_COUNT_MIN, max_colors)
    candidates = list(range(COLOR_COUNT_MIN, max_colors + 1, 2))
    errors, crowded = {}, {}
    for k in candidates + [k + 4 for k in candidates[-2:]]:
        if k in errors:
            continue
        centers = _kmeans(points, weights, k, iterations=8, sample=10 ** 9)
        error = np.sqrt(((points - centers[_nearest(points, centers)]) ** 2).sum(1))
        errors[k] = np.average(error, weights=weights)
        distance = np.sqrt(((centers[:, None] - centers[None]) ** 2).sum(-1))
        crowded[k] = ((distance < SIMILAR_DELTA_E).sum() - len(centers)) // 2

    enough = candidates[-1]
    for k in candidates:
        if errors[k] <= 4.5 or (k + 4 in errors and errors[k] - errors[k + 4] < 0.6):
            enough = k
            break
    limit = COLOR_COUNT_MIN
    for k in candidates:
        if crowded[k] > max(2, k / 8):
            break
        limit = k
    return int(min(enough, limit, max_colors))
