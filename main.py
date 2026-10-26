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


def windows_work_area():
    """
    Windows：屏幕去掉任务栏后能用的范围 (左, 上, 宽, 高)，单位是"点"（和窗口大小的单位一样）。
    不是 Windows 时返回 None。

    注意：这里不能自己设置"DPI 感知"（SetProcessDpiAwareness）。Kivy 会让 SDL 自己处理
    屏幕缩放（125%、150%……），而这个设置只能设一次；抢先设置会让 SDL 的换算出错，
    窗口变得比屏幕还大，画面卡在左下角。
    """
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    area = wintypes.RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(area), 0)   # SPI_GETWORKAREA
    # 换算成"点"：屏幕缩放 150% 时，1 点 = 1.5 像素
    scale = user32.GetDpiForSystem() / 96 if hasattr(user32, "GetDpiForSystem") else 1
    return (area.left / scale, area.top / scale,
            (area.right - area.left) / scale, (area.bottom - area.top) / scale)


from kivy.config import Config  # noqa: E402

# 这些设置必须在创建窗口之前写好。大小的单位是"点"，屏幕缩放由 SDL 处理。
WINDOW = {"width": 1200, "height": 800, "minimum_width": 960, "minimum_height": 660}
TITLE_BAR = 32      # Windows 窗口标题栏大约的高度（点）
work_area = windows_work_area()
if work_area is not None:
    # 窗口不能比屏幕大，并且放在屏幕正中间（标题栏和底边都要看得见）
    left, top, width, height = work_area
    WINDOW["width"] = min(WINDOW["width"], int(width) - 16)
    WINDOW["height"] = min(WINDOW["height"], int(height) - TITLE_BAR - 16)
    WINDOW["minimum_width"] = min(WINDOW["minimum_width"], WINDOW["width"])
    WINDOW["minimum_height"] = min(WINDOW["minimum_height"], WINDOW["height"])
    Config.set("graphics", "position", "custom")
    Config.set("graphics", "left", str(int(left + (width - WINDOW["width"]) / 2)))
    Config.set("graphics", "top", str(int(top + TITLE_BAR + (height - TITLE_BAR - WINDOW["height"]) / 2)))
for key, value in WINDOW.items():
    Config.set("graphics", key, str(value))
Config.set("input", "mouse", "mouse,multitouch_on_demand")   # 右键不要出现红点
Config.set("kivy", "exit_on_escape", "0")                     # 按 Esc 不退出程序

from colornumber.ui.app import ColorNumberApp  # noqa: E402

if __name__ == "__main__":
    ColorNumberApp().run()
