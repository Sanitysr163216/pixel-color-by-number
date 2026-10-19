"""
导出作品：PNG 图片、GIF 动图、MP4 视频。

GIF 和 MP4 是"延时动画"：按填色顺序回放整个过程。
"""

from PIL import Image

from colornumber.core.render import cell_pixels_for, render_state

PNG_LONG_SIDE = 1024
VIDEO_LONG_SIDE = 720
ANIMATION_FRAMES = 90        # 回放过程取多少帧
ANIMATION_FPS = 30
HOLD_SECONDS = 1.5           # 结尾停留在完成图上的时间


def export_png(game, path):
    """把当前的样子导出成 PNG。"""
    cell = cell_pixels_for(game.picture, PNG_LONG_SIDE)
    render_state(game.picture, game.painted, cell).save(path)


def _animation_images(game, long_side):
    """生成延时动画的每一帧图片（Pillow Image）。"""
    cell = cell_pixels_for(game.picture, long_side)
    frames = [render_state(game.picture, painted, cell)
              for painted in game.replay_frames(ANIMATION_FRAMES)]
    frames += [frames[-1]] * int(HOLD_SECONDS * ANIMATION_FPS)
    return frames


def export_gif(game, path):
    """导出延时 GIF。"""
    frames = _animation_images(game, VIDEO_LONG_SIDE // 2)   # GIF 文件大，尺寸减半
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / ANIMATION_FPS),
        loop=0,
        optimize=True,
    )


def _even_size(image):
    """H.264 视频要求宽高都是偶数，不够就在右边和下面补一行白色。"""
    width, height = image.size
    if width % 2 == 0 and height % 2 == 0:
        return image
    padded = Image.new("RGB", (width + width % 2, height + height % 2), "white")
    padded.paste(image, (0, 0))
    return padded


def export_mp4(game, path):
    """导出延时 MP4。需要安装 imageio 和 imageio-ffmpeg。"""
    import imageio.v2 as imageio   # 只在导出视频时才需要，所以放在这里 import

    writer = imageio.get_writer(path, fps=ANIMATION_FPS, codec="libx264",
                                macro_block_size=1, quality=8)
    try:
        for frame in _animation_images(game, VIDEO_LONG_SIDE):
            writer.append_data(_as_array(_even_size(frame)))
    finally:
        writer.close()


def _as_array(image):
    import numpy   # imageio 自带 numpy
    return numpy.asarray(image)
