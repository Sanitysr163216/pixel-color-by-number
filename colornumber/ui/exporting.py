"""
导出作品（PNG / GIF / MP4）：在后台线程里导出，避免界面卡住。
"""

import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from kivy.clock import Clock

from colornumber.core import export
from colornumber.ui.common import Dialog, message, tr

EXPORT_FOLDER = Path.home() / "Pictures" / "Color Number"

EXPORTERS = {
    "png": export.export_png,
    "gif": export.export_gif,
    "mp4": export.export_mp4,
}


def _safe_name(name):
    """去掉文件名里不能用的字符。"""
    return re.sub(r'[\\/:*?"<>|]+', "_", name).strip() or "picture"


def show_in_finder(path):
    if sys.platform == "darwin":
        subprocess.run(["open", "-R", str(path)], check=False)
    elif sys.platform.startswith("win"):
        subprocess.run(["explorer", "/select,", str(path)], check=False)


def export_kinds():
    """能导出的格式。没有 ffmpeg 时不显示 MP4。"""
    return ("png", "gif", "mp4") if export.mp4_available() else ("png", "gif")


def export_game(game, name, kind):
    """导出 game，kind 是 "png"、"gif" 或 "mp4"。"""
    EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = EXPORT_FOLDER / f"{_safe_name(name)}_{stamp}.{kind}"
    waiting = Dialog(tr("exporting"), [])
    waiting.open()

    def work():
        try:
            EXPORTERS[kind](game, path)
            error = None
        except Exception as exc:   # 导出失败时把原因显示给玩家
            error = exc
        Clock.schedule_once(lambda _dt: finish(error))

    def finish(error):
        waiting.dismiss()
        if error is not None:
            message(tr("export_failed", error=error))
            return
        extra = []
        if sys.platform in ("darwin", "win32"):
            extra.append((tr("show_in_finder"), lambda: show_in_finder(path), "normal"))
        message(tr("exported_to", path=path), extra_buttons=extra)

    threading.Thread(target=work, daemon=True).start()
