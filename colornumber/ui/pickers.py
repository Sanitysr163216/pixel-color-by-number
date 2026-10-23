"""
选择文件的窗口：尽量用系统自己的选择窗口，玩家最熟悉。

- macOS：用 osascript 运行一小段 AppleScript（choose file）
- Windows：用 PowerShell 打开 Windows 自带的"打开文件"窗口
- 其他系统，或者上面两种出错时：用 Kivy 自带的文件列表

系统的选择窗口会一直等玩家选好，所以放在后台线程里运行，界面不会卡住。
"""

import base64
import subprocess
import sys
import threading
from pathlib import Path

from kivy.clock import Clock
from kivy.metrics import dp

from colornumber.ui.common import Dialog, tr


def pick_files(title, kind, patterns, on_chosen, multiple=False):
    """
    让玩家选文件，选好后调用 on_chosen(路径列表)；玩家取消时什么都不做。
    kind 是 "image" 或 "audio"（macOS 用它决定能选哪些文件），
    patterns 是 ("*.jpg", "*.png", ...) 这样的文件类型。
    """
    if sys.platform == "darwin":
        run = lambda: _pick_with_macos(title, kind, multiple)
    elif sys.platform == "win32":
        run = lambda: _pick_with_windows(title, patterns, multiple)
    else:
        _pick_with_kivy(title, patterns, on_chosen, multiple)
        return

    def work():
        try:
            paths = run()
        except (OSError, subprocess.SubprocessError):   # 系统的窗口打不开：改用 Kivy 的文件列表
            Clock.schedule_once(lambda _dt: _pick_with_kivy(title, patterns, on_chosen, multiple))
            return
        if paths:
            Clock.schedule_once(lambda _dt: on_chosen(paths))

    threading.Thread(target=work, daemon=True).start()


def _pick_with_macos(title, kind, multiple):
    file_type = {"image": "public.image", "audio": "public.audio"}[kind]
    script = (f'set picked to choose file of type {{"{file_type}"}} with prompt "{title}"'
              + (" with multiple selections allowed" if multiple else "") + "\n"
              'if class of picked is not list then set picked to {picked}\n'
              'set output to ""\n'
              'repeat with chosen in picked\n'
              '  set output to output & POSIX path of chosen & linefeed\n'
              'end repeat\n'
              'return output')
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:            # 玩家点了"取消"
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _pick_with_windows(title, patterns, multiple):
    # PowerShell 的字符串里，单引号要写两次
    title = title.replace("'", "''")
    file_filter = ";".join(patterns)
    script = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = '{title}'
$dialog.Filter = '{file_filter}|{file_filter}'
$dialog.Multiselect = ${'true' if multiple else 'false'}
if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {{
    $dialog.FileNames -join "`n"
}}
"""
    # 用 -EncodedCommand 传脚本，不用担心引号和中文出问题
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-STA", "-EncodedCommand", encoded],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW,   # 不要弹出黑色的命令行窗口
    )
    output = result.stdout.decode("utf-8", errors="replace").lstrip("﻿")
    return [line.strip() for line in output.splitlines() if line.strip()]


def _pick_with_kivy(title, patterns, on_chosen, multiple):
    from kivy.uix.filechooser import FileChooserListView

    chooser = FileChooserListView(path=str(Path.home()), filters=list(patterns), multiselect=multiple,
                                  size_hint_y=None, height=dp(360))
    dialog = Dialog("", [
        (tr("cancel"), None, "normal"),
        (tr("ok"), lambda: chooser.selection and on_chosen(list(chooser.selection)), "primary"),
    ], title=title, content=chooser)
    dialog.width = dp(640)
    dialog.open()
