"""
修复 macOS 上全屏和放大窗口时卡死的问题。

conda-forge 的 SDL2 其实是"sdl2-compat"（底下用的是 SDL3），它和 Kivy 有两处配合不好：
1. 点绿色按钮进入 macOS 的"全屏空间"时，SDL3 会自己再切换一次全屏并等待切换完成，
   两边互相等待，程序卡死。所以在 main.py 里设置了 SDL_VIDEO_MAC_FULLSCREEN_SPACES=0，
   绿色按钮改为把窗口放大；真正的全屏由游戏自己提供（Ctrl+Cmd+F 或 F11）。
2. 窗口大小一变（放大、拖动边框），Kivy 都会重新设置一次全屏模式；窗口放大后
   sdl2-compat 会在这一步报错，Kivy 每一帧都重试，最后卡死。
   这里给 Kivy 的 SDL 窗口套一层"保护"：全屏模式没有变化就不重复设置，设置失败也不让错误一直循环。
"""

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import Metrics


class _SafeFullscreen:
    """把 Kivy 的 SDL 窗口对象包一层，只改 set_fullscreen_mode，其他功能原样转交。"""

    def __init__(self, inner):
        self._inner = inner
        self._mode = False            # 程序启动时是普通窗口

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def set_fullscreen_mode(self, mode):
        if mode == self._mode:
            return
        try:
            self._inner.set_fullscreen_mode(mode)
            self._mode = mode
        except SystemError:
            pass                      # sdl2-compat 偶尔会失败，失败就保持原来的模式


def install():
    """在窗口创建以后调用一次。"""
    win = getattr(Window, "_win", None)
    if win is not None and not isinstance(win, _SafeFullscreen):
        Window._win = _SafeFullscreen(win)


_windowed_size = None


def toggle_fullscreen():
    """进入或退出全屏（铺满整个屏幕）。退出时恢复进入全屏前的窗口大小。"""
    global _windowed_size
    if Window.fullscreen:
        Window.fullscreen = False
        if _windowed_size:
            size = _windowed_size
            Clock.schedule_once(lambda _dt: setattr(Window, "size", size), 0.3)
    else:
        # 读出来的 Window.size 是像素，设置时却按"点"算（Mac 视网膜屏 1 点 = 2 像素，
        # Windows 屏幕缩放 150% 时 1 点 = 1.5 像素），所以先换算
        _windowed_size = tuple(round(value / Metrics.density) for value in Window.size)
        Window.fullscreen = "auto"
