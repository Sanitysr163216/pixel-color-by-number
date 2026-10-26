"""
界面冒烟测试：真的打开游戏窗口，自动点一遍主要的页面，每一步都截图。
任何一步出错，程序会以错误码结束（GitHub Actions 会显示失败）。

用法（在项目文件夹里）：

    python tests/ui_smoke.py 截图文件夹

不会动到你自己的作品和设置：测试用的是截图文件夹里的 data 文件夹。
（文件名不是 test_ 开头，所以 pytest 不会自动运行它。）
"""

import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "smoke-output").resolve()
DATA = OUT / "data"
DATA.mkdir(parents=True, exist_ok=True)
with open(DATA / "settings.json", "w", encoding="utf-8") as file:
    json.dump({"music": False, "sound": False}, file)

import main  # noqa: E402,F401  （设置窗口大小等，和正常启动一样）
from kivy.clock import Clock  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.tests.common import UnitTestTouch  # noqa: E402
from kivy.uix.modalview import ModalView  # noqa: E402
from PIL import Image  # noqa: E402

from colornumber.ui import window_fix  # noqa: E402
from colornumber.ui.app import ColorNumberApp  # noqa: E402


class SmokeApp(ColorNumberApp):
    @property
    def user_data_dir(self):
        return str(DATA)


app = SmokeApp()
failures = []


def shot(name):
    app.screens.export_to_png(str(OUT / f"{name}.png"))
    for widget in Window.children:
        if isinstance(widget, ModalView):
            widget.children[0].export_to_png(str(OUT / f"{name}_dialog.png"))
    print("SHOT", name, flush=True)


def close_dialogs():
    for widget in list(Window.children):
        if isinstance(widget, ModalView):
            widget.dismiss()


def screen(name):
    return app.screens.get_screen(name)


def paint_some_cells():
    game_screen = screen("game")
    canvas, game = game_screen.canvas_widget, game_screen.game
    canvas.fit()
    cells = game.cells_by_number[canvas.selected][:20]
    for idx in cells:
        row, col = divmod(idx, game.width)
        x, y = canvas._cell_origin(row, col)
        touch = UnitTestTouch(x + canvas.scale / 2, y + canvas.scale / 2)
        touch.touch_down()
        touch.touch_up()
    painted = sum(1 for idx in cells if game.painted[idx])
    print("PAINTED", painted, "of", len(cells), flush=True)
    assert painted > 0, "painting did not work"


def open_test_photo():
    photo = OUT / "photo.png"
    image = Image.new("RGB", (300, 200), (90, 160, 230))
    for x in range(80, 220):
        for y in range(50, 150):
            image.putpixel((x, y), (240, 120, 60))
    image.save(photo)
    app.open_import(str(photo))
    assert app.screens.current == "import", "import screen did not open"


def check_window_on_screen():
    """Windows：窗口要完整地在屏幕里，画面要铺满整个窗口（屏幕缩放 125%、150% 时也一样）。"""
    from kivy.metrics import Metrics
    print("WINDOW size", Window.size, "system_size", Window.system_size, "density", Metrics.density, flush=True)
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes
    from PIL import ImageGrab
    user32 = ctypes.windll.user32
    hwnd = user32.GetActiveWindow() or user32.GetForegroundWindow()
    window, client, area = wintypes.RECT(), wintypes.RECT(), wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(window))
    user32.GetClientRect(hwnd, ctypes.byref(client))
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(area), 0)
    print("WINDOW rect", (window.left, window.top, window.right, window.bottom),
          "client", (client.right, client.bottom), "work area", (area.left, area.top, area.right, area.bottom),
          "dpi", user32.GetDpiForWindow(hwnd), flush=True)
    ImageGrab.grab().save(OUT / "00_desktop.png")
    margin = 12          # 窗口四周有几像素看不见的边框
    assert window.left >= area.left - margin and window.top >= area.top - margin, "window starts off screen"
    assert window.right <= area.right + margin and window.bottom <= area.bottom + margin, "window ends off screen"
    # 画面大小（像素）要和窗口里面的大小一样，不然画面会只占一部分或者被裁掉
    assert abs(Window.size[0] - client.right) <= 2 and abs(Window.size[1] - client.bottom) <= 2, \
        f"drawing size {Window.size} does not match the window {client.right}x{client.bottom}"


def check_online():
    online = screen("online")
    print("ONLINE", repr(online.status), len(online.ids.grid.children), flush=True)


# (等待秒数, 名字, 要做的事)
STEPS = [
    (1.0, "window", check_window_on_screen),
    (0.2, "home", lambda: shot("01_home")),
    (0.3, "library category", lambda: setattr(screen("home"), "category", "animals")),
    (0.5, "home animals", lambda: shot("02_home_animals")),
    (0.3, "open picture", lambda: app.open_library("cat")),
    (1.0, "game", lambda: shot("03_game")),
    (0.3, "paint", paint_some_cells),
    (0.5, "game painted", lambda: shot("04_game_painted")),
    (0.3, "shortcuts", lambda: screen("game").show_shortcuts()),
    (0.6, "shortcuts shot", lambda: shot("05_shortcuts")),
    (0.2, "close", close_dialogs),
    (0.3, "back home", lambda: screen("game").go_back()),
    (0.5, "import", open_test_photo),
    (3.0, "import shot", lambda: shot("06_import")),
    (0.3, "leave import", app.leave_import),
    (0.3, "online", app.show_online),
    (10.0, "online check", check_online),
    (0.2, "online shot", lambda: shot("07_online")),
    (0.3, "settings", app.show_settings),
    (0.5, "settings shot", lambda: shot("08_settings")),
    (0.3, "chinese", lambda: app.set_language("zh")),
    (0.6, "settings zh", lambda: shot("09_settings_zh")),
    (0.3, "english", lambda: app.set_language("en")),
    (0.3, "home again", app.show_home),
    (0.3, "fullscreen on", window_fix.toggle_fullscreen),
    (1.5, "fullscreen shot", lambda: shot("10_fullscreen")),
    (0.3, "fullscreen off", window_fix.toggle_fullscreen),
    (1.5, "window size", lambda: print("WINDOW", Window.size, Window.fullscreen, flush=True)),
]


def run_step(index):
    """做第 index 步，做完再等下一步的时间。（一步接一步，不怕第一帧很慢）"""
    if index == len(STEPS):
        Clock.schedule_once(lambda _dt: app.stop(), 1.0)
        return
    wait, name, action = STEPS[index]

    def step(_dt):
        try:
            action()
        except Exception:
            failures.append(name)
            print("FAILED", name, flush=True)
            traceback.print_exc()
        run_step(index + 1)

    Clock.schedule_once(step, wait)


Clock.schedule_once(lambda _dt: run_step(0), 1.5)
app.run()

if failures:
    print("SMOKE TEST FAILED:", ", ".join(failures), flush=True)
    sys.exit(1)
print("SMOKE TEST PASSED", flush=True)
