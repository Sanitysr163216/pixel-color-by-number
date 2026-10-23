# PyInstaller 打包配置：把游戏打包成不需要安装 Python 的 Windows 程序。
# 用法：在 Windows 上运行 packaging/build_windows.ps1（只能在 Windows 上打包）
# -*- mode: python ; coding: utf-8 -*-

import os

from kivy_deps import angle, glew, sdl2
from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, get_hooks

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

# 只带上用到的 Kivy 组件：SDL2 窗口、文字、图片和声音，不带视频和摄像头
deps = get_deps_minimal(video=None, camera=None, spelling=None)
deps["hiddenimports"] += [
    "colornumber.ui.game_screen", "colornumber.ui.home_screen",
    "colornumber.ui.import_screen", "colornumber.ui.settings_screen",
    "colornumber.ui.online_screen",
    "certifi",                    # 在线名画联网用的证书
    "pillow_heif",                # 读取 iPhone 的 HEIC 照片
]

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    datas=[(os.path.join(ROOT, "colornumber", "assets"), os.path.join("colornumber", "assets"))],
    **deps,
    **get_hooks(),
    noarchive=False,
)


def _is_ffmpeg(entry):
    # imageio-ffmpeg 自带的 ffmpeg 是 GPL 许可证，不和游戏一起发布（和 macOS 版一样）。
    # 玩家自己装了 ffmpeg 时，导出 MP4 的按钮会自动出现。
    return "imageio_ffmpeg" in entry[0].replace("\\", "/") and "binaries" in entry[0].replace("\\", "/")


a.datas = [entry for entry in a.datas if not _is_ffmpeg(entry)]
a.binaries = [entry for entry in a.binaries if not _is_ffmpeg(entry)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Color Number",
    icon=os.path.join(ROOT, "packaging", "icon.ico"),
    console=False,                # 不要命令行窗口
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    # Kivy 在 Windows 上需要的 SDL2、GLEW、ANGLE 动态库
    *[Tree(path) for path in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)],
    name="Color Number",
)
