"""
导入照片：裁剪、调整亮度/对比度/饱和度、选择格子数和颜色数，并实时预览。
"""

import subprocess
import sys
import threading
from pathlib import Path

from PIL import Image as PILImage

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from colornumber.core import converter
from colornumber.core.render import render_state
from colornumber.ui.common import Chip, Dialog, RoundButton, message, pil_to_texture, tr  # noqa: F401

WORK_LONG_SIDE = 2048     # 先把照片缩到这么大，转换更快（最多 512 格，足够了）
DISPLAY_LONG_SIDE = 1024  # 裁剪区显示用的图
IMAGE_TYPES = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.heif", "*.bmp", "*.gif", "*.webp", "*.tif", "*.tiff")

Builder.load_string("""
<SliderRow>:
    size_hint_y: None
    height: "40dp"
    spacing: "8dp"
    Label:
        text: root.title
        color: 0.2, 0.2, 0.25, 1
        font_size: "14sp"
        size_hint_x: None
        width: "120dp"
        text_size: self.size
        halign: "left"
        valign: "middle"
    Slider:
        min: root.minimum
        max: root.maximum
        step: root.step
        value: root.value
        on_value: root.value = self.value
        cursor_size: "20dp", "20dp"
    Label:
        text: root.value_text
        color: 0.3, 0.52, 0.95, 1
        font_size: "14sp"
        bold: True
        size_hint_x: None
        width: "48dp"

<ImportScreen>:
    canvas.before:
        Color:
            rgba: 0.97, 0.96, 0.94, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        padding: "16dp"
        spacing: "16dp"
        BoxLayout:
            orientation: "vertical"
            spacing: "8dp"
            size_hint_x: 0.55
            Label:
                text: app.tr("crop_hint", app.lang)
                color: 0.5, 0.5, 0.55, 1
                font_size: "13sp"
                size_hint_y: None
                height: "20dp"
            CropView:
                id: crop
                on_crop: root.schedule_preview()
            BoxLayout:
                size_hint_y: None
                height: "40dp"
                spacing: "8dp"
                RoundButton:
                    text: app.tr("reset_crop", app.lang)
                    on_release: crop.reset()
                RoundButton:
                    text: app.tr("choose_photo", app.lang)
                    on_release: app.open_import()
        BoxLayout:
            orientation: "vertical"
            spacing: "6dp"
            Image:
                id: preview
                fit_mode: "contain"
            Label:
                text: root.info
                color: 0.3, 0.3, 0.35, 1
                font_size: "13sp"
                size_hint_y: None
                height: "20dp"
            SliderRow:
                id: grid_size
                title: app.tr("grid_size", app.lang)
                minimum: 16
                maximum: app.settings_grid_limit
                step: 1
                value: 48
                on_value: root.schedule_preview()
            SliderRow:
                id: color_count
                title: app.tr("color_count", app.lang)
                minimum: 4
                maximum: app.settings_color_limit
                step: 1
                value: 16
                on_value: root.schedule_preview()
            SliderRow:
                id: brightness
                title: app.tr("brightness", app.lang)
                minimum: 0.5
                maximum: 1.5
                step: 0.05
                value: 1.0
                on_value: root.schedule_preview()
            SliderRow:
                id: contrast
                title: app.tr("contrast", app.lang)
                minimum: 0.5
                maximum: 1.5
                step: 0.05
                value: 1.0
                on_value: root.schedule_preview()
            SliderRow:
                id: saturation
                title: app.tr("saturation", app.lang)
                minimum: 0.0
                maximum: 2.0
                step: 0.05
                value: 1.0
                on_value: root.schedule_preview()
            BoxLayout:
                size_hint_y: None
                height: "40dp"
                spacing: "8dp"
                Chip:
                    id: clean
                    text: app.tr("clean_stray", app.lang)
                    state: "down"
                    on_state: root.schedule_preview()
                TextInput:
                    id: name
                    hint_text: app.tr("name", app.lang)
                    multiline: False
                    font_size: "15sp"
                    padding: "10dp", "10dp"
            BoxLayout:
                size_hint_y: None
                height: "44dp"
                spacing: "10dp"
                RoundButton:
                    text: app.tr("cancel", app.lang)
                    on_release: app.show_home()
                RoundButton:
                    text: app.tr("start_coloring", app.lang)
                    primary: True
                    on_release: root.start()
""")


class SliderRow(BoxLayout):
    title = StringProperty("")
    minimum = NumericProperty(0)
    maximum = NumericProperty(1)
    step = NumericProperty(1)
    value = NumericProperty(0)
    value_text = StringProperty("")

    def on_value(self, *_):
        self.value_text = str(int(self.value)) if self.step >= 1 else f"{self.value:.2f}"

    def on_maximum(self, *_):
        if self.value > self.maximum:
            self.value = self.maximum


class CropView(Widget):
    """显示照片和一个可以拖动、调整大小的裁剪框。"""

    texture = ObjectProperty(None, allownone=True)
    image_size = ListProperty([1, 1])       # 照片的像素大小（WORK 图）
    crop = ListProperty([0, 0, 1, 1])       # 裁剪框：左、上、右、下（照片像素）

    HANDLE = 22  # 四角拖动区域的大小（dp）

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mode = None
        self.bind(pos=self._redraw, size=self._redraw, texture=self._redraw, crop=self._redraw)

    def set_image(self, texture, image_size):
        self.image_size = list(image_size)
        self.texture = texture
        self.reset()

    def reset(self):
        self.crop = [0, 0, self.image_size[0], self.image_size[1]]

    def _display_rect(self):
        """照片在控件里实际显示的位置和缩放比例。"""
        width, height = self.image_size
        scale = min(self.width / width, self.height / height)
        shown_w, shown_h = width * scale, height * scale
        return self.x + (self.width - shown_w) / 2, self.y + (self.height - shown_h) / 2, shown_w, shown_h, scale

    def _crop_screen_rect(self):
        x, y, _w, h, scale = self._display_rect()
        left, top, right, bottom = self.crop
        return x + left * scale, y + h - bottom * scale, (right - left) * scale, (bottom - top) * scale

    def _redraw(self, *_):
        self.canvas.clear()
        if self.texture is None:
            return
        x, y, w, h, _scale = self._display_rect()
        cx, cy, cw, ch = self._crop_screen_rect()
        handle = dp(10)
        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(texture=self.texture, pos=(x, y), size=(w, h))
            Color(0, 0, 0, 0.45)                 # 裁剪框外面变暗
            Rectangle(pos=(x, y), size=(w, cy - y))
            Rectangle(pos=(x, cy + ch), size=(w, y + h - cy - ch))
            Rectangle(pos=(x, cy), size=(cx - x, ch))
            Rectangle(pos=(cx + cw, cy), size=(x + w - cx - cw, ch))
            Color(1, 1, 1, 1)
            Line(rectangle=(cx, cy, cw, ch), width=1.5)
            for hx, hy in ((cx, cy), (cx + cw, cy), (cx, cy + ch), (cx + cw, cy + ch)):
                Rectangle(pos=(hx - handle / 2, hy - handle / 2), size=(handle, handle))

    def on_touch_down(self, touch):
        if self.texture is None or not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        cx, cy, cw, ch = self._crop_screen_rect()
        reach = dp(self.HANDLE)
        corners = {"bl": (cx, cy), "br": (cx + cw, cy), "tl": (cx, cy + ch), "tr": (cx + cw, cy + ch)}
        for name, (hx, hy) in corners.items():
            if abs(touch.x - hx) < reach and abs(touch.y - hy) < reach:
                self._mode = name
                break
        else:
            if cx <= touch.x <= cx + cw and cy <= touch.y <= cy + ch:
                self._mode = "move"
            else:
                return True
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self or self._mode is None:
            return False
        *_rest, scale = self._display_rect()
        dx, dy = touch.dx / scale, -touch.dy / scale   # 照片坐标的 y 轴向下
        width, height = self.image_size
        left, top, right, bottom = self.crop
        minimum = max(8, min(width, height) * 0.05)
        if self._mode == "move":
            dx = max(-left, min(width - right, dx))
            dy = max(-top, min(height - bottom, dy))
            left, right, top, bottom = left + dx, right + dx, top + dy, bottom + dy
        else:
            if "l" in self._mode:
                left = max(0, min(right - minimum, left + dx))
            if "r" in self._mode:
                right = min(width, max(left + minimum, right + dx))
            if "t" in self._mode:
                top = max(0, min(bottom - minimum, top + dy))
            if "b" in self._mode:
                bottom = min(height, max(top + minimum, bottom + dy))
        self.crop = [left, top, right, bottom]
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self._mode = None
            return True
        return False


class ImportScreen(Screen):
    info = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.work_image = None
        self._generation = 0
        self._preview_trigger = Clock.create_trigger(self._start_preview, 0.2)

    def load_photo(self, path):
        """读取照片，准备裁剪和预览。成功返回 True。"""
        try:
            image = converter.load_image(path)
        except Exception as error:   # 打不开的文件：告诉玩家原因
            message(tr("load_failed", error=error))
            return False
        image.thumbnail((WORK_LONG_SIDE, WORK_LONG_SIDE), PILImage.Resampling.LANCZOS)
        self.work_image = image
        display = image.copy()
        display.thumbnail((DISPLAY_LONG_SIDE, DISPLAY_LONG_SIDE), PILImage.Resampling.LANCZOS)
        self.ids.crop.set_image(pil_to_texture(display, nearest=False), image.size)
        self.ids.name.text = Path(path).stem
        self.ids.preview.texture = None
        self.schedule_preview()
        return True

    def _options(self):
        ids = self.ids
        return {
            "grid_size": int(ids.grid_size.value),
            "color_count": int(ids.color_count.value),
            "brightness": ids.brightness.value,
            "contrast": ids.contrast.value,
            "saturation": ids.saturation.value,
            "clean": ids.clean.state == "down",
            "crop": tuple(round(value) for value in ids.crop.crop),
        }

    def schedule_preview(self, *_):
        if self.work_image is not None:
            self._preview_trigger()

    def _start_preview(self, *_):
        """在后台线程里转换，转换完再回到主线程显示。旧的结果会被丢掉。"""
        self._generation += 1
        generation = self._generation
        image, options = self.work_image, self._options()

        def work():
            picture = converter.convert(image, **options)
            cell = max(1, 600 // max(picture.width, picture.height))
            rendered = render_state(picture, picture.flat_numbers(), cell)
            Clock.schedule_once(lambda _dt: self._show_preview(generation, picture, rendered))

        threading.Thread(target=work, daemon=True).start()

    def _show_preview(self, generation, picture, rendered):
        if generation != self._generation:
            return
        self.ids.preview.texture = pil_to_texture(rendered)
        self.info = tr("preview_info", width=picture.width, height=picture.height,
                       colors=picture.color_count)

    def start(self):
        if self.work_image is None:
            return
        app = App.get_running_app()
        picture = converter.convert(self.work_image, **self._options())
        name = self.ids.name.text.strip() or tr("import_photo")
        meta = app.store.create(picture, name, "import")
        app.open_project(meta["id"])


# ---------------------------------------------------------------------------
# 选择照片：macOS 用系统自带的选择窗口，其他系统用 Kivy 的文件列表
# ---------------------------------------------------------------------------

def pick_photo(on_chosen):
    """让玩家选一张照片，选好后调用 on_chosen(路径)。"""
    if sys.platform == "darwin":
        _pick_with_macos(on_chosen)
    else:
        _pick_with_kivy(on_chosen)


def _pick_with_macos(on_chosen):
    script = f'POSIX path of (choose file of type {{"public.image"}} with prompt "{tr("pick_photo_title")}")'

    def work():
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        path = result.stdout.strip()
        if result.returncode == 0 and path:
            Clock.schedule_once(lambda _dt: on_chosen(path))

    threading.Thread(target=work, daemon=True).start()


def _pick_with_kivy(on_chosen):
    chooser = FileChooserListView(path=str(Path.home()), filters=list(IMAGE_TYPES))
    chooser.size_hint_y = None
    chooser.height = dp(360)
    dialog = Dialog("", [
        (tr("cancel"), None, "normal"),
        (tr("ok"), lambda: chooser.selection and on_chosen(chooser.selection[0]), "primary"),
    ], title=tr("pick_photo_title"))
    dialog.width = dp(640)
    dialog.children[0].add_widget(chooser, index=1)
    dialog.open()
