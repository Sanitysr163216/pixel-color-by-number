"""
Color Number 数字填色 —— 程序入口。

运行方法：

    conda activate color-number
    python main.py
"""

import os

# 播放声音用 SDL2：Kivy 默认的 GStreamer 在 conda 环境里缺少 WAV 解码插件，会没有声音
os.environ.setdefault("KIVY_AUDIO", "sdl2")
# 不使用 macOS 的"全屏空间"：它和 SDL3 互相等待会卡死（见 colornumber/ui/window_fix.py）
os.environ.setdefault("SDL_VIDEO_MAC_FULLSCREEN_SPACES", "0")

from kivy.config import Config  # noqa: E402

# 这些设置必须在创建窗口之前写好
Config.set("graphics", "width", "1200")
Config.set("graphics", "height", "800")
Config.set("graphics", "minimum_width", "960")
Config.set("graphics", "minimum_height", "660")
Config.set("input", "mouse", "mouse,multitouch_on_demand")   # 右键不要出现红点
Config.set("kivy", "exit_on_escape", "0")                     # 按 Esc 不退出程序

from colornumber.ui.app import ColorNumberApp  # noqa: E402

if __name__ == "__main__":
    ColorNumberApp().run()
