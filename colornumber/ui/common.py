"""
界面里到处会用到的东西：颜色主题、中文字体、圆角按钮、弹窗、图片转换。
"""

import io
import os

from kivy.animation import Animation
from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.core.text import DEFAULT_FONT, LabelBase
from kivy.graphics import Color, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import BooleanProperty, ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.togglebutton import ToggleButton

# ---------------------------------------------------------------------------
# 颜色主题（RGBA，取值 0–1）
# ---------------------------------------------------------------------------

BACKGROUND = (0.97, 0.96, 0.94, 1)
SURFACE = (1, 1, 1, 1)
TEXT = (0.20, 0.20, 0.25, 1)
TEXT_LIGHT = (0.50, 0.50, 0.55, 1)
ACCENT = (0.30, 0.52, 0.95, 1)
ACCENT_LIGHT = (0.86, 0.91, 1.0, 1)
DANGER = (0.88, 0.30, 0.30, 1)
BUTTON = (0.92, 0.92, 0.94, 1)

# ---------------------------------------------------------------------------
# 中文字体：Kivy 自带的字体没有中文，这里找一个系统里的中文字体当默认字体
# ---------------------------------------------------------------------------

FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",           # macOS
    "/System/Library/Fonts/STHeiti Medium.ttc",             # macOS
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS
    "C:/Windows/Fonts/msyh.ttc",                            # Windows 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",                          # Windows 黑体
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux
]


def register_chinese_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            LabelBase.register(DEFAULT_FONT, fn_regular=path)
            return path
    return None


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

def tr(key, **values):
    """取当前语言的界面文字。"""
    return App.get_running_app().tr(key, **values)


def pil_to_texture(image, nearest=True):
    """
    把 Pillow 图片变成 Kivy 能显示的贴图。
    nearest=True（像素图）：放大时保持方块感；缩小时用多级纹理（mipmap）平滑，
    不然格子比屏幕像素还小时会跳格，出现锯齿和闪烁。
    """
    data = io.BytesIO()
    image.save(data, format="png")
    data.seek(0)
    texture = CoreImage(data, ext="png", mipmap=True).texture
    texture.min_filter = "linear_mipmap_linear"
    texture.mag_filter = "nearest" if nearest else "linear"
    return texture


def contrast_text_color(rgb):
    """在这个底色上，文字用黑色还是白色更清楚。rgb 取值 0–255。"""
    red, green, blue = rgb
    return (0.1, 0.1, 0.1, 1) if 0.299 * red + 0.587 * green + 0.114 * blue > 150 else (1, 1, 1, 1)


# ---------------------------------------------------------------------------
# 圆角按钮
# ---------------------------------------------------------------------------

Builder.load_string("""
<RoundButton>:
    background_normal: ""
    background_down: ""
    background_color: 0, 0, 0, 0
    color: (1, 1, 1, 1) if (self.primary or self.danger) else (0.2, 0.2, 0.25, 1)
    font_size: "15sp"
    size_hint_y: None
    height: "40dp"
    padding: "14dp", "6dp"
    canvas.before:
        Color:
            rgba: self.fill_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]

<Chip>:
    background_normal: ""
    background_down: ""
    background_color: 0, 0, 0, 0
    color: (1, 1, 1, 1) if self.state == "down" else (0.2, 0.2, 0.25, 1)
    font_size: "14sp"
    size_hint_y: None
    height: "36dp"
    canvas.before:
        Color:
            rgba: (0.30, 0.52, 0.95, 1) if self.state == "down" else (0.92, 0.92, 0.94, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(18)]

<LongPressButton>:
    canvas.after:
        # 按住时从左到右填满的进度条，满了就触发长按
        Color:
            rgba: 0.30, 0.52, 0.95, 0.35 if self.progress > 0 else 0
        RoundedRectangle:
            pos: self.pos
            size: self.width * self.progress, self.height
            radius: [dp(10)]

<TextLabel@Label>:
    color: 0.2, 0.2, 0.25, 1
    font_size: "15sp"
    text_size: self.width, None
    size_hint_y: None
    height: self.texture_size[1]
""")


class RoundButton(Button):
    """圆角按钮。primary=True 是蓝色的主按钮，danger=True 是红色的危险按钮。"""

    primary = BooleanProperty(False)
    danger = BooleanProperty(False)
    fill_color = ListProperty(BUTTON)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(primary=self._update_fill, danger=self._update_fill, state=self._update_fill)
        self._update_fill()

    def _update_fill(self, *_):
        if self.danger:
            base = DANGER
        elif self.primary:
            base = ACCENT
        else:
            base = BUTTON
        factor = 0.85 if self.state == "down" else 1.0
        self.fill_color = [base[0] * factor, base[1] * factor, base[2] * factor, 1]


class LongPressButton(RoundButton):
    """
    可以长按的圆角按钮：短按触发 on_release，按住 long_press_time 秒触发 on_long_press
    （长按后松开不会再触发 on_release）。
    """

    __events__ = ("on_long_press",)
    long_press_time = NumericProperty(0.6)
    progress = NumericProperty(0)        # 按住的进度 0–1，用来画进度条

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._timer = None
        self._fired = False

    def on_touch_down(self, touch):
        handled = super().on_touch_down(touch)
        if handled and self.collide_point(*touch.pos) and not getattr(touch, "is_mouse_scrolling", False):
            self._fired = False
            self._timer = Clock.schedule_once(lambda _dt: self._fire(), self.long_press_time)
            Animation.cancel_all(self, "progress")
            self.progress = 0
            Animation(progress=1, duration=self.long_press_time).start(self)
        return handled

    def _fire(self):
        Animation.cancel_all(self, "progress")
        self.progress = 0
        if self.state == "down":
            self._fired = True
            self.dispatch("on_long_press")

    def on_touch_up(self, touch):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        Animation.cancel_all(self, "progress")
        self.progress = 0
        if touch.grab_current is self and self._fired:
            touch.ungrab(self)
            self.state = "normal"
            self._fired = False
            return True
        return super().on_touch_up(touch)

    def on_long_press(self):
        pass


class Chip(ToggleButton):
    """圆形的选项按钮，同一组（group）里只能选中一个。"""

    def on_touch_down(self, touch):
        # 已选中的不允许再点一下取消，保证一组里总有一个被选中
        if self.state == "down" and self.collide_point(*touch.pos) and self.group:
            return True
        return super().on_touch_down(touch)


# ---------------------------------------------------------------------------
# 弹窗
# ---------------------------------------------------------------------------

class Dialog(ModalView):
    """
    白色圆角的弹窗：上面一段文字，下面是按钮。

    buttons 是 [(文字, 回调, 样式), ...]，样式是 "normal"、"primary" 或 "danger"。
    点按钮后弹窗会关闭；加第四项 False 表示点了不关闭。
    按钮不超过 2 个时排成一行，更多时竖着排。
    content 是放在文字和按钮之间的任意控件（比如输入框）。
    """

    def __init__(self, text, buttons, title=None, content=None, **kwargs):
        super().__init__(size_hint=(None, None), width=dp(420), auto_dismiss=False,
                         background_color=(0, 0, 0, 0.35), background="", **kwargs)
        box = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(12),
                        size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        with box.canvas.before:
            Color(*SURFACE)
            self._bg = RoundedRectangle(radius=[dp(16)])
        box.bind(pos=self._update_bg, size=self._update_bg)

        if title:
            box.add_widget(Label(text=title, bold=True, font_size="20sp", color=TEXT,
                                 size_hint_y=None, height=dp(32)))
        if text:
            message_label = Label(text=text, color=TEXT, font_size="15sp", halign="center",
                                  size_hint_y=None)
            message_label.bind(
                width=lambda widget, width: setattr(widget, "text_size", (width, None)),
                texture_size=lambda widget, size: setattr(widget, "height", size[1]))
            box.add_widget(message_label)
        if content is not None:
            box.add_widget(content)

        if buttons:
            if len(buttons) <= 2:
                container = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))
            else:
                container = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
                container.bind(minimum_height=container.setter("height"))
            for spec in buttons:
                label, callback, style = spec[:3]
                close = spec[3] if len(spec) > 3 else True
                button = RoundButton(text=label, primary=(style == "primary"),
                                     danger=(style == "danger"))
                button.bind(on_release=self._make_handler(callback, close))
                container.add_widget(button)
            box.add_widget(container)
        self.add_widget(box)
        box.bind(height=lambda *_: setattr(self, "height", box.height))

    def _update_bg(self, widget, _value):
        self._bg.pos = widget.pos
        self._bg.size = widget.size

    def _make_handler(self, callback, close):
        def handler(_button):
            if close:
                self.dismiss()
            if callback:
                callback()
        return handler


def confirm(text, on_yes, yes_label=None, danger=False, title=None, on_no=None):
    """弹出"确定/取消"对话框，点确定时调用 on_yes，点取消时调用 on_no。"""
    Dialog(text, [
        (tr("cancel"), on_no, "normal"),
        (yes_label or tr("ok"), on_yes, "danger" if danger else "primary"),
    ], title=title).open()


def message(text, title=None, extra_buttons=()):
    """只有一个"确定"按钮的提示框。extra_buttons 是额外的 (文字, 回调, 样式)。"""
    dialog = Dialog(text, list(extra_buttons) + [(tr("ok"), None, "primary")], title=title)
    dialog.open()
    return dialog
