"""
导入照片：裁剪、调整亮度/对比度/饱和度、选择格子数和颜色数，并实时预览。
会推荐一个颜色数，提醒很接近的颜色；在 macOS 上还可以用 AI 识别人脸和主体。
"""

import math
import threading
from pathlib import Path

from PIL import Image as PILImage

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.stencilview import StencilView
from kivy.uix.widget import Widget

from colornumber.core import converter, vision
from colornumber.core.render import render_state
from colornumber.ui.common import Chip, Dialog, RoundButton, message, pil_to_texture, tr  # noqa: F401
from colornumber.ui.pickers import pick_files

WORK_LONG_SIDE = 2048     # 先把照片缩到这么大，转换更快（最多 512 格，足够了）
DISPLAY_LONG_SIDE = 1024  # 裁剪区显示用的图
IMAGE_TYPES = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.heif", "*.bmp", "*.gif", "*.webp", "*.tif", "*.tiff")

Builder.load_string("""
<SliderRow>:
    size_hint_y: None
    height: "36dp"
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
    TextInput:
        # 可以直接输入数字：按回车或点别处生效，超出范围会自动限制
        id: number
        text: root.value_text
        multiline: False
        input_filter: "float"
        font_size: "14sp"
        halign: "center"
        padding: "4dp", "8dp"
        size_hint: None, None
        size: "58dp", "32dp"
        pos_hint: {"center_y": 0.5}
        foreground_color: 0.3, 0.52, 0.95, 1
        on_text_validate: root.apply_text(self.text)
        on_focus: if not self.focus: root.apply_text(self.text)

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

        # 左边：裁剪和画面调整
        BoxLayout:
            orientation: "vertical"
            spacing: "6dp"
            size_hint_x: 0.5
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
                    text: app.tr("reset_defaults", app.lang)
                    on_release: root.reset_defaults()
                RoundButton:
                    text: app.tr("choose_photo", app.lang)
                    on_release: app.open_import()
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

        # 右边：预览和转换设置
        BoxLayout:
            orientation: "vertical"
            spacing: "6dp"
            FloatLayout:
                CompareView:
                    id: preview
                    compare: compare.state == "down"
                    pos: self.parent.pos
                    size: self.parent.size
                BoxLayout:
                    size_hint: None, None
                    size: "150dp", "30dp"
                    spacing: "4dp"
                    pos: self.parent.right - self.width - dp(6), self.parent.top - self.height - dp(6)
                    RoundButton:
                        text: "+"
                        font_size: "18sp"
                        height: "30dp"
                        on_release: preview.zoom_step(1)
                    RoundButton:
                        text: "-"
                        font_size: "18sp"
                        height: "30dp"
                        on_release: preview.zoom_step(-1)
                    RoundButton:
                        text: app.tr("fit_view", app.lang)
                        font_size: "13sp"
                        height: "30dp"
                        on_release: preview.reset_view()
            Label:
                text: root.info
                markup: True
                color: 0.3, 0.3, 0.35, 1
                font_size: "13sp"
                size_hint_y: None
                height: "20dp"
            BoxLayout:
                size_hint_y: None
                height: "34dp"
                spacing: "6dp"
                Chip:
                    id: style_smooth
                    text: app.tr("style_smooth", app.lang)
                    group: "convert_style"
                    height: "34dp"
                    on_state: if self.state == "down": root.set_style("smooth")
                Chip:
                    id: style_clear
                    text: app.tr("style_clear", app.lang)
                    group: "convert_style"
                    height: "34dp"
                    on_state: if self.state == "down": root.set_style("clear")
                Chip:
                    id: style_classic
                    text: app.tr("style_classic", app.lang)
                    group: "convert_style"
                    height: "34dp"
                    on_state: if self.state == "down": root.set_style("classic")
                Widget:
                    size_hint_x: 0.15
                Chip:
                    id: compare
                    text: app.tr("compare_original", app.lang)
                    height: "34dp"
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
            BoxLayout:
                size_hint_y: None
                height: "32dp"
                spacing: "8dp"
                Label:
                    text: root.recommendation
                    color: 0.3, 0.52, 0.95, 1
                    font_size: "13sp"
                    text_size: self.size
                    halign: "left"
                    valign: "middle"
                RoundButton:
                    text: app.tr("use_recommended", app.lang)
                    size_hint: None, None
                    size: "120dp", "30dp"
                    font_size: "13sp"
                    disabled: root.recommended == 0
                    on_release: root.use_recommendation()
            SliderRow:
                id: strength
                disabled: root.style == "classic"
                opacity: 0.4 if root.style == "classic" else 1
                title: app.tr("detail" if root.style == "clear" else "smoothness", app.lang)
                minimum: 0
                maximum: 100
                step: 5
                value: 50
                on_value: root.schedule_preview()
            BoxLayout:
                size_hint_y: None
                height: "36dp"
                spacing: "8dp"
                Chip:
                    id: clean
                    text: app.tr("clean_stray", app.lang)
                    state: "down"
                    on_state: root.schedule_preview()
                Chip:
                    id: ai
                    text: app.tr("ai_assist", app.lang)
                    disabled: not root.ai_available
                    opacity: 1 if root.ai_available else 0.4
                    on_state: root.on_ai_toggle()
                Chip:
                    id: blur_background
                    text: app.tr("blur_background", app.lang)
                    disabled: not root.subject_found or ai.state != "down"
                    opacity: 1 if (root.subject_found and ai.state == "down") else 0.4
                    on_state: root.schedule_preview()
            Label:
                text: root.ai_status
                color: 0.45, 0.45, 0.5, 1
                font_size: "12sp"
                size_hint_y: None
                height: "18dp"
                text_size: self.size
                halign: "left"
                valign: "middle"
            BoxLayout:
                size_hint_y: None
                height: "40dp"
                spacing: "8dp"
                TextInput:
                    id: name
                    hint_text: app.tr("name", app.lang)
                    multiline: False
                    font_size: "15sp"
                    padding: "10dp", "10dp"
                RoundButton:
                    text: app.tr("cancel", app.lang)
                    size_hint_x: None
                    width: "90dp"
                    on_release: app.leave_import()
                RoundButton:
                    text: app.tr("start_coloring", app.lang)
                    primary: True
                    size_hint_x: None
                    width: "130dp"
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
        self.value_text = str(int(round(self.value))) if self.step >= 1 else f"{self.value:.2f}"
        if "number" in self.ids:
            self.ids.number.text = self.value_text     # 拖动滑块时，输入框的数字也跟着变

    def apply_text(self, text):
        """把输入框里的数字用上：按步长取整，并限制在允许范围内。"""
        try:
            number = float(text)
        except ValueError:
            number = self.value
        number = min(self.maximum, max(self.minimum, number))
        number = round(round(number / self.step) * self.step, 4)
        self.value = number
        self.on_value()

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


class CompareView(StencilView):
    """
    转换结果的预览，可以缩放和拖动。
    - 滚轮、触控板捏合、右上角的 + / - 按钮：缩放；双击：回到"适合"大小
    - 拖动、触控板双指滑动：移动画面
    - 打开"对比原图"后，左边显示原图、右边显示填色图；在分隔线附近拖动是移动分隔线

    填色图的贴图是每格 1 个像素，按整数倍放大显示并对齐到整像素，
    这样每个格子都是同样大小、颜色均匀的方块。
    """

    compare = BooleanProperty(False)
    split = NumericProperty(0.5)          # 分隔线的位置，0 是最左，1 是最右
    MAX_CELL = 60                         # 最多放大到每格 60 像素

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pixel_texture = None
        self.original_texture = None
        self._labels = {}
        self._exact_scale = None          # None 表示"适合"大小
        self._pan = [0.0, 0.0]            # 画面中心相对控件中心的偏移（像素）
        self._drag = None                 # "split" 或 "pan"
        self.bind(pos=self._redraw, size=self._redraw, compare=self._redraw, split=self._redraw)

    def set_textures(self, pixel_texture, original_texture):
        if self.pixel_texture is None or self.pixel_texture.size != pixel_texture.size:
            self.reset_view()             # 格子数变了，缩放回到"适合"
        self.pixel_texture = pixel_texture
        self.original_texture = original_texture
        self._redraw()

    def clear(self):
        self.pixel_texture = self.original_texture = None
        self.reset_view()

    # ------------------------------------------------------------------
    # 缩放和移动
    # ------------------------------------------------------------------

    def _fit_scale(self):
        width, height = self.pixel_texture.size
        scale = min(self.width / width, self.height / height)
        return math.floor(scale) if scale >= 1 else scale

    def _scale(self):
        """现在每格显示多少像素（2 像素以上取整，格子才会大小一样）。"""
        fit = self._fit_scale()
        if self._exact_scale is None or self._exact_scale <= fit:
            return fit
        return float(round(self._exact_scale)) if self._exact_scale >= 2 else self._exact_scale

    def _rect(self):
        width, height = self.pixel_texture.size
        scale = self._scale()
        shown_w, shown_h = round(width * scale), round(height * scale)
        # 画面不能被拖得完全看不见：最多拖到边缘还留在控件里
        limit_x = max(0, (shown_w - self.width) / 2)
        limit_y = max(0, (shown_h - self.height) / 2)
        self._pan = [min(limit_x, max(-limit_x, self._pan[0])), min(limit_y, max(-limit_y, self._pan[1]))]
        return (round(self.x + (self.width - shown_w) / 2 + self._pan[0]),
                round(self.y + (self.height - shown_h) / 2 + self._pan[1]), shown_w, shown_h)

    def reset_view(self):
        self._exact_scale = None
        self._pan = [0.0, 0.0]
        self._redraw()

    def zoom_at(self, x, y, factor):
        """以 (x, y) 为中心缩放。"""
        if self.pixel_texture is None:
            return
        self._rect()                      # 先把拖动范围修正好
        old_scale = self._scale()
        exact = self._exact_scale if self._exact_scale is not None else old_scale
        self._exact_scale = min(self.MAX_CELL, max(self._fit_scale(), exact * factor))
        new_scale = self._scale()
        if new_scale == old_scale:
            self._redraw()
            return
        # 让光标下的那一点缩放后还在光标下：
        # 新的图片中心 = 光标 + (原来的图片中心 - 光标) × 放大倍数
        ratio = new_scale / old_scale
        old_cx, old_cy = self.center_x + self._pan[0], self.center_y + self._pan[1]
        self._pan = [x + (old_cx - x) * ratio - self.center_x, y + (old_cy - y) * ratio - self.center_y]
        self._redraw()

    def zoom_step(self, direction):
        """+ / - 按钮：每次放大或缩小一档。"""
        self.zoom_at(self.center_x, self.center_y, 1.5 if direction > 0 else 1 / 1.5)

    def pan_by(self, dx, dy):
        self._pan[0] += dx
        self._pan[1] += dy
        self._redraw()

    def wants_gesture(self):
        """鼠标在预览图上时，接收触控板手势。"""
        return self.pixel_texture is not None and self.collide_point(*Window.mouse_pos)

    def gesture_zoom(self, factor):
        self.zoom_at(*Window.mouse_pos, factor)

    def gesture_pan(self, dx, dy):
        self.pan_by(dx, dy)

    # ------------------------------------------------------------------
    # 画出来
    # ------------------------------------------------------------------

    def _label(self, key):
        """"原图""填色图"这样的小标签的贴图。"""
        text = tr(key)
        if self._labels.get(key, (None,))[0] != text:
            label = CoreLabel(text=text, font_size=dp(12), color=(1, 1, 1, 1))
            label.refresh()
            self._labels[key] = (text, label.texture)
        return self._labels[key][1]

    def _split_x(self):
        x, _y, w, _h = self._rect()
        pw = self.pixel_texture.size[0]
        left = round(pw * self.split)               # 分隔线放在格子边界上，不把格子切成两半
        return left, x + round(w * left / pw)

    def _redraw(self, *_):
        self.canvas.clear()
        if self.pixel_texture is None:
            return
        x, y, w, h = self._rect()
        with self.canvas:
            Color(1, 1, 1, 1)
            if not self.compare or self.original_texture is None:
                Rectangle(texture=self.pixel_texture, pos=(x, y), size=(w, h))
                return
            ow, oh = self.original_texture.size
            pw, ph = self.pixel_texture.size
            left, split_x = self._split_x()
            if left > 0:
                Rectangle(texture=self.original_texture.get_region(0, 0, max(1, round(ow * left / pw)), oh),
                          pos=(x, y), size=(split_x - x, h))
            if left < pw:
                Rectangle(texture=self.pixel_texture.get_region(left, 0, pw - left, ph),
                          pos=(split_x, y), size=(x + w - split_x, h))
            # 分隔线和拖动把手（把手放在看得见的那一段中间）
            visible_bottom, visible_top = max(y, self.y), min(y + h, self.top)
            Color(1, 1, 1, 1)
            Line(points=[split_x, visible_bottom, split_x, visible_top], width=dp(1.5))
            Color(0.3, 0.52, 0.95, 1)
            middle = (visible_bottom + visible_top) / 2
            Ellipse(pos=(split_x - dp(11), middle - dp(11)), size=(dp(22), dp(22)))
            # 左上角"原图"、右上角"填色图"（贴着看得见的区域）
            for key, left_side in (("original_label", True), ("pixel_label", False)):
                texture = self._label(key)
                tw, th = texture.size
                lx = max(x, self.x) + dp(6) if left_side else min(x + w, self.right) - tw - dp(14)
                ly = visible_top - th - dp(10)
                Color(0, 0, 0, 0.45)
                RoundedRectangle(pos=(lx - dp(4), ly - dp(2)), size=(tw + dp(8), th + dp(4)), radius=[dp(4)])
                Color(1, 1, 1, 1)
                Rectangle(texture=texture, pos=(lx, ly), size=(tw, th))

    # ------------------------------------------------------------------
    # 鼠标和触摸
    # ------------------------------------------------------------------

    def on_touch_down(self, touch):
        if self.pixel_texture is None or not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if touch.is_mouse_scrolling:
            factor = 1.25 if touch.button in ("scrolldown", "scrollleft") else 1 / 1.25
            self.zoom_at(touch.x, touch.y, factor)
            return True
        if touch.is_double_tap:
            self.reset_view()
            return True
        _left, split_x = self._split_x()
        self._drag = "split" if self.compare and abs(touch.x - split_x) < dp(24) else "pan"
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        if self._drag == "split":
            x, _y, w, _h = self._rect()
            self.split = min(1.0, max(0.0, (touch.x - x) / w))
        else:
            self.pan_by(touch.dx, touch.dy)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self._drag = None
            return True
        return False


class ImportScreen(Screen):
    info = StringProperty("")
    style = StringProperty(converter.DEFAULT_STYLE)
    recommendation = StringProperty("")
    recommended = NumericProperty(0)
    ai_available = BooleanProperty(False)
    subject_found = BooleanProperty(False)
    ai_status = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.work_image = None
        self.analysis = None              # AI 分析结果（core/vision.py 的 Analysis）
        self._photo_id = 0                # 每换一张照片加 1，用来丢掉旧照片的结果
        self._busy = False                # 后台正在转换
        self._pending = False             # 转换期间又有新的改动，转换完要再来一次
        self._recommend_key = None        # 上次计算推荐颜色数时用的设置
        self._preview_trigger = Clock.create_trigger(self._start_preview, 0.15)
        self.ai_available = vision.available()

    def on_pre_enter(self, *_):
        settings = App.get_running_app().settings
        self.ids.ai.state = "down" if (settings.ai_assist and self.ai_available) else "normal"
        style = settings.convert_style if settings.convert_style in converter.STYLES else converter.DEFAULT_STYLE
        self.ids[f"style_{style}"].state = "down"
        self.set_style(style)

    # ------------------------------------------------------------------
    # 读取照片
    # ------------------------------------------------------------------

    def load_photo(self, path):
        """读取照片，准备裁剪和预览。成功返回 True。"""
        try:
            image = converter.load_image(path)
        except Exception as error:   # 打不开的文件：告诉玩家原因
            message(tr("load_failed", error=error))
            return False
        image.thumbnail((WORK_LONG_SIDE, WORK_LONG_SIDE), PILImage.Resampling.LANCZOS)
        self.work_image = image
        self._photo_id += 1
        self.analysis = None
        self.subject_found = False
        self._recommend_key = None
        self.recommended = 0
        self.recommendation = ""
        display = image.copy()
        display.thumbnail((DISPLAY_LONG_SIDE, DISPLAY_LONG_SIDE), PILImage.Resampling.LANCZOS)
        self.ids.crop.set_image(pil_to_texture(display, nearest=False), image.size)
        self.ids.name.text = Path(path).stem
        self.ids.preview.clear()
        self.ids.blur_background.state = "normal"
        self._start_analysis()
        self.schedule_preview()
        return True

    def _start_analysis(self):
        """在后台用 AI 分析照片（人脸、五官、主体）。"""
        if not self.ai_available:
            self.ai_status = ""
            return
        self.ai_status = tr("ai_analyzing")
        photo_id, image = self._photo_id, self.work_image

        def work():
            try:
                result = vision.analyze(image)
            except Exception:       # AI 出问题时不影响正常转换
                result = None
            Clock.schedule_once(lambda _dt: self._analysis_done(photo_id, result))

        threading.Thread(target=work, daemon=True).start()

    def _analysis_done(self, photo_id, result):
        if photo_id != self._photo_id:
            return
        self.analysis = result
        self.subject_found = result is not None and result.subject is not None
        self._update_ai_status()
        if self.ids.ai.state == "down":
            self._recommend_key = None
            self.schedule_preview()

    def _update_ai_status(self):
        result = self.analysis
        if result is None and not self.ai_status:
            return
        if self.style == "classic" and result is not None and result.faces:
            self.ai_status = tr("ai_classic_note", faces=result.faces)
        elif result is None:
            self.ai_status = tr("ai_failed")
        elif result.faces and self.subject_found:
            self.ai_status = tr("ai_found_faces_subject", faces=result.faces)
        elif result.faces:
            self.ai_status = tr("ai_found_faces", faces=result.faces)
        elif self.subject_found:
            self.ai_status = tr("ai_found_subject")
        else:
            self.ai_status = tr("ai_found_nothing")

    def set_style(self, style):
        """切换转换风格：平滑、清晰、经典。会记住选择。"""
        self.style = style
        for name in converter.STYLES:
            self.ids[f"style_{name}"].state = "down" if name == style else "normal"
        App.get_running_app().update_setting("convert_style", style)
        if self.analysis is not None:
            self._update_ai_status()
        self.schedule_preview()

    def reset_defaults(self):
        """一键恢复默认：不裁剪，所有滑块、风格和开关回到默认值。"""
        ids = self.ids
        ids.crop.reset()
        for slider, value in ((ids.brightness, 1.0), (ids.contrast, 1.0), (ids.saturation, 1.0),
                              (ids.grid_size, converter.DEFAULT_GRID_SIZE),
                              (ids.color_count, converter.DEFAULT_COLOR_COUNT), (ids.strength, 50)):
            slider.value = value
        ids.clean.state = "down"
        ids.blur_background.state = "normal"
        ids.compare.state = "normal"
        ids.ai.state = "down" if self.ai_available else "normal"
        self.set_style(converter.DEFAULT_STYLE)

    def on_ai_toggle(self):
        App.get_running_app().update_setting("ai_assist", self.ids.ai.state == "down")
        if self.ids.ai.state != "down":
            self.ids.blur_background.state = "normal"
        self.schedule_preview()

    # ------------------------------------------------------------------
    # 预览
    # ------------------------------------------------------------------

    def _options(self):
        ids = self.ids
        options = {
            "grid_size": int(ids.grid_size.value),
            "color_count": int(ids.color_count.value),
            "brightness": ids.brightness.value,
            "contrast": ids.contrast.value,
            "saturation": ids.saturation.value,
            "clean": ids.clean.state == "down",
            "crop": tuple(round(value) for value in ids.crop.crop),
            "style": self.style,
            "detail": ids.strength.value / 100,
            "smoothness": ids.strength.value / 100,
        }
        if self.analysis is not None and ids.ai.state == "down":
            options["importance"] = self.analysis.importance
            if ids.blur_background.state == "down" and self.analysis.subject is not None:
                options["subject"] = self.analysis.subject
                options["simplify_background"] = True
        return options

    def schedule_preview(self, *_):
        if self.work_image is not None:
            self._preview_trigger()

    def _start_preview(self, *_):
        """
        在后台线程里转换。同一时间只转换一次；转换期间又改了设置，
        就等这次做完再用最新的设置做一次。颜色数以外的设置变了，才重新计算推荐颜色数。
        """
        if self._busy:
            self._pending = True
            return
        self._busy = True
        image, options, photo_id = self.work_image, self._options(), self._photo_id
        recommend_options = {key: value for key, value in options.items()
                             if key not in ("color_count", "clean")}
        key = (photo_id,) + tuple(sorted((k, id(v) if hasattr(v, "shape") else v)
                                         for k, v in recommend_options.items()))
        need_recommendation = key != self._recommend_key
        color_limit = App.get_running_app().settings.color_limit

        def work():
            try:
                picture = converter.convert(image, **options)
                rendered = render_state(picture, picture.flat_numbers(), 1)   # 每格 1 个像素，显示时整数倍放大
                similar = converter.similar_color_pairs(picture.palette)
                original = image.crop(options["crop"])
                fidelity = converter.fidelity(original, picture)
                adjusted = (any(options[key] != 1.0 for key in ("brightness", "contrast", "saturation"))
                            or options.get("simplify_background", False))
                original.thumbnail((1024, 1024), PILImage.Resampling.LANCZOS)
                Clock.schedule_once(lambda _dt: self._show_preview(
                    photo_id, picture, rendered, similar, original, fidelity, adjusted))
                if need_recommendation:
                    count = converter.recommend_color_count(image, max_colors=color_limit, **recommend_options)
                    Clock.schedule_once(lambda _dt: self._show_recommendation(photo_id, key, count))
            finally:
                Clock.schedule_once(lambda _dt: self._preview_done())

        if need_recommendation:
            self.recommendation = tr("recommend_working")
        threading.Thread(target=work, daemon=True).start()

    def _preview_done(self):
        self._busy = False
        if self._pending:
            self._pending = False
            self._start_preview()

    def _show_preview(self, photo_id, picture, rendered, similar, original, fidelity, adjusted):
        if photo_id != self._photo_id:
            return
        self.ids.preview.set_textures(pil_to_texture(rendered), pil_to_texture(original, nearest=False))
        text = tr("preview_info", width=picture.width, height=picture.height, colors=picture.color_count)
        text += "  " + tr("fidelity", score=fidelity)
        if adjusted:
            text += tr("fidelity_adjusted")
        if similar:
            text += "  [color=e0841c]" + tr("similar_warning", pairs=similar) + "[/color]"
        self.info = text

    def _show_recommendation(self, photo_id, key, count):
        if photo_id != self._photo_id:
            return
        self._recommend_key = key
        self.recommended = count
        self.recommendation = tr("recommended_colors", count=count)

    def use_recommendation(self):
        if self.recommended:
            self.ids.color_count.value = self.recommended

    def start(self):
        """在后台生成填色图（大图要一两秒），期间显示"正在生成"，也防止重复点击。"""
        if self.work_image is None or getattr(self, "_starting", False):
            return
        self._starting = True
        app = App.get_running_app()
        image, options = self.work_image, self._options()
        name = self.ids.name.text.strip() or tr("import_photo")
        waiting = Dialog(tr("creating_picture"), [])
        waiting.open()

        def work():
            picture = converter.convert(image, **options)
            Clock.schedule_once(lambda _dt: done(picture))

        def done(picture):
            meta = app.store.create(picture, name, "import")
            waiting.dismiss()
            self._starting = False
            app.open_project(meta["id"])

        threading.Thread(target=work, daemon=True).start()


# ---------------------------------------------------------------------------
# 选择照片
# ---------------------------------------------------------------------------

def pick_photo(on_chosen):
    """让玩家选一张照片，选好后调用 on_chosen(路径)。"""
    pick_files(tr("pick_photo_title"), "image", IMAGE_TYPES, lambda paths: on_chosen(paths[0]))
