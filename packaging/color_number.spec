# PyInstaller 打包配置：把游戏打包成不需要安装 Python 的 macOS App。
# 用法：在项目文件夹里运行 packaging/build_macos.sh
# -*- mode: python ; coding: utf-8 -*-

import os
import shutil
import sys

from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, get_hooks

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
VERSION = os.environ.get("COLOR_NUMBER_VERSION", "1.0.0")

# 只带上用到的 Kivy 组件：SDL2 窗口、文字、图片和声音，不带视频和摄像头
deps = get_deps_minimal(video=None, camera=None, spelling=None)
# macOS 的系统库（/usr/lib、/System）不需要也不能打包进去，每台 Mac 都自带
deps["binaries"] = [entry for entry in deps.get("binaries", [])
                    if not entry[0].startswith(("/usr/lib", "/System")) and os.path.exists(entry[0])]
# conda-forge 的 SDL2 其实是"sdl2-compat"：运行时才去加载真正的 SDL3，
# 而且找的是和它放在一起的 "libSDL3.dylib" 这个名字。PyInstaller 看不到这种
# 运行时加载，所以手动复制一份放进去，不然 App 启动时会卡死。
sdl3 = os.path.join(sys.prefix, "lib", "libSDL3.0.dylib")
if os.path.exists(sdl3):
    os.makedirs(workpath, exist_ok=True)
    sdl3_copy = os.path.join(workpath, "libSDL3.dylib")
    shutil.copyfile(sdl3, sdl3_copy)
    deps["binaries"].append((sdl3_copy, "."))
deps["hiddenimports"] += [
    "colornumber.ui.game_screen", "colornumber.ui.home_screen",
    "colornumber.ui.import_screen", "colornumber.ui.settings_screen",
    "colornumber.ui.online_screen",
    "certifi",                                            # 在线名画联网用的证书
    "colornumber.ui.mac_gestures",
    "objc", "AppKit", "Foundation", "Quartz", "Vision",   # 触控板手势和 AI 识别
    "pillow_heif",                                        # 读取 iPhone 的 HEIC 照片
]

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    datas=[(os.path.join(ROOT, "colornumber", "assets"), os.path.join("colornumber", "assets"))],
    **deps,
    **get_hooks(),
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Color Number",
    console=False,
)

coll = COLLECT(exe, a.binaries, a.datas, name="Color Number")

app = BUNDLE(
    coll,
    name="Color Number.app",
    icon=os.path.join(ROOT, "Color Number.app", "Contents", "Resources", "AppIcon.icns"),
    bundle_identifier="io.github.sanitysr163216.colornumber",
    version=VERSION,
    info_plist={
        "CFBundleDisplayName": "Color Number",
        "CFBundleShortVersionString": VERSION,
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "12.0",
    },
)
