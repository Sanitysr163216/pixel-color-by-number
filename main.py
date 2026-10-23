"""
Color Number 数字填色 —— 程序入口。

运行方法：

    conda activate color-number
    python main.py
"""

import os
import sys

# 播放声音用 SDL2：Kivy 默认的 GStreamer 在 conda 环境里缺少 WAV 解码插件，会没有声音
os.environ.setdefault("KIVY_AUDIO", "sdl2")
# 不使用 macOS 的"全屏空间"：它和 SDL3 互相等待会卡死（见 colornumber/ui/window_fix.py）
os.environ.setdefault("SDL_VIDEO_MAC_FULLSCREEN_SPACES", "0")
# 打包成没有命令行窗口的程序时（Windows），sys.stdout 和 sys.stderr 是 None，
# 往里面写日志会出错，所以让它们指向一个"什么都不保存"的文件
if sys.stderr is None:
    sys.stdout = sys.stderr = open(os.devnull, "w", encoding="utf-8")


def windows_screen():
    """
    Windows：让程序自己处理屏幕缩放（125%、150%……），文字和图片才清楚，不会被系统拉伸得模糊。
    返回 (缩放倍数, 屏幕可用的宽, 高)，单位是像素；不是 Windows 时返回 None。
    """
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)     # 每个显示器分别按它的缩放显示
    except (AttributeError, OSError):
        ctypes.windll.user32.SetProcessDPIAware()          # 旧版 Windows
    scale = ctypes.windll.user32.GetDpiForSystem() / 96 if hasattr(ctypes.windll.user32, "GetDpiForSystem") else 1
    area = wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(area), 0)   # 去掉任务栏后的屏幕范围
    return scale, area.right - area.left, area.bottom - area.top


from kivy.config import Config  # noqa: E402

# 这些设置必须在创建窗口之前写好。大小按 macOS 的"点"写；
# Windows 上按屏幕缩放换算成像素，并且不超过屏幕（留出标题栏的位置）
WINDOW = {"width": 1200, "height": 800, "minimum_width": 960, "minimum_height": 660}
screen = windows_screen()
if screen is not None:
    scale, screen_width, screen_height = screen
    WINDOW = {key: round(value * scale) for key, value in WINDOW.items()}
    WINDOW["width"] = min(WINDOW["width"], screen_width)
    WINDOW["height"] = min(WINDOW["height"], screen_height - round(40 * scale))
    WINDOW["minimum_width"] = min(WINDOW["minimum_width"], WINDOW["width"])
    WINDOW["minimum_height"] = min(WINDOW["minimum_height"], WINDOW["height"])
for key, value in WINDOW.items():
    Config.set("graphics", key, str(value))
Config.set("input", "mouse", "mouse,multitouch_on_demand")   # 右键不要出现红点
Config.set("kivy", "exit_on_escape", "0")                     # 按 Esc 不退出程序

from colornumber.ui.app import ColorNumberApp  # noqa: E402

if __name__ == "__main__":
    ColorNumberApp().run()
