"""
填色画布：显示格子，处理缩放、拖动和填色。

为了让 512 × 512（26 万格）的大图也能流畅显示，画布不是一格一格地画，
而是把整张图做成两张"贴图"（每格一个像素），再放大显示：

- 底图（base）：填了的格子显示颜色，没填的格子显示浅灰色轮廓
- 白色遮罩（mask）：没填的格子是白色，填了的格子透明

缩小时遮罩完全透明，看到的是灰色轮廓；放大时遮罩慢慢变成不透明，
没填的格子就渐渐变成白色，数字也渐渐出现。改变遮罩的透明度几乎不花时间。

数字和网格线只画屏幕上看得到的那部分格子。
"""

import math

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, InstructionGroup, Line, Rectangle
from kivy.graphics.texture import Texture
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.stencilview import StencilView

from colornumber.core.game import cells_on_line
from colornumber.core.render import grey_of

FADE_START = 7.0        # 每格小于 7 像素：纯灰色轮廓
FADE_END = 18.0         # 每格大于 18 像素：白底
NUMBER_START = 13.0     # 每格大于 13 像素开始出现数字
NUMBER_FULL = 22.0      # 每格大于 22 像素数字完全显示
MAX_SCALE = 90.0        # 最多放大到每格 90 像素
MAX_NUMBER_CELLS = 9000  # 屏幕上格子太多时不画数字（太小也看不清）

HIGHLIGHT_BASE = (150, 160, 185)    # 当前编号没填的格子：远看的颜色
HIGHLIGHT_MASK = (198, 214, 245)    # 当前编号没填的格子：近看的颜色
CANVAS_BACKGROUND = (0.90, 0.90, 0.91, 1)


def _clamp(value, low, high):
    return max(low, min(high, value))


class PaintCanvas(StencilView):
    """可以缩放和拖动的填色画布。"""

    selected = NumericProperty(1)        # 当前选中的颜色编号
    tool = StringProperty("brush")       # "brush" 画笔，"wand" 魔棒，"move" 移动
    scale = NumericProperty(1.0)         # 每格显示成多少像素
    offset = ListProperty([0.0, 0.0])    # 图的左下角相对画布左下角的位置
    space_pan = BooleanProperty(False)   # 按住空格时，左键拖动变成移动画布
    locked = BooleanProperty(False)      # 回放动画时不能操作

    __events__ = ("on_cells_changed", "on_stroke_end")

    _number_textures = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = None
        self.display = None          # 正在显示的 painted 列表（回放时是临时的）
        self._replaying = False
        self._touches = []
        self._stroke_active = False
        self._stroke_changed = False
        self._last_cell = None
        self._pinch = None
        self._highlighted = None
        self._hint_idx = None
        self._fit_scale = 1.0

        with self.canvas:
            Color(*CANVAS_BACKGROUND)
            self._background = Rectangle()
            Color(1, 1, 1, 1)
            self._base_rect = Rectangle()
            self._mask_color = Color(1, 1, 1, 0)
            self._mask_rect = Rectangle()
        self._overlay = InstructionGroup()
        self.canvas.add(self._overlay)
        with self.canvas:
            self._hint_color = Color(0.95, 0.25, 0.3, 0)
            self._hint_line = Line(width=2.5)

        self._overlay_trigger = Clock.create_trigger(self._rebuild_overlay, -1)
        self.bind(pos=self._update_view, size=self._on_size, scale=self._update_view,
                  offset=self._update_view, selected=self._on_selected)

    # ------------------------------------------------------------------
    # 载入一张图
    # ------------------------------------------------------------------

    def load_game(self, game):
        self.game = game
        self.display = game.painted
        self._replaying = False
        width, height = game.width, game.height
        self._colors = [None] + [bytes(color) + b"\xff" for color in game.picture.palette]
        self._greys = [None] + [bytes(grey_of(color)) + b"\xff" for color in game.picture.palette]
        self._base = bytearray(width * height * 4)
        self._mask = bytearray(width * height * 4)
        self._base_texture = self._make_texture(width, height)
        self._mask_texture = self._make_texture(width, height)
        self._base_rect.texture = self._base_texture
        self._mask_rect.texture = self._mask_texture
        self._highlighted = self.selected
        self._rebuild_all()
        self.fit()

    @staticmethod
    def _make_texture(width, height):
        texture = Texture.create(size=(width, height), colorfmt="rgba")
        texture.mag_filter = "nearest"
        texture.min_filter = "nearest"
        return texture

    # ------------------------------------------------------------------
    # 更新贴图
    # ------------------------------------------------------------------

    def _write_cell(self, idx):
        """根据这格的状态，算出它在两张贴图里的颜色。"""
        game = self.game
        row, col = divmod(idx, game.width)
        position = ((game.height - 1 - row) * game.width + col) * 4
        value = self.display[idx]
        answer = game.answer[idx]
        if value:
            base = self._colors[value]
            mask = b"\x00\x00\x00\x00"
        elif answer == self._highlighted and not self._replaying:
            base = bytes(HIGHLIGHT_BASE) + b"\xff"
            mask = bytes(HIGHLIGHT_MASK) + b"\xff"
        else:
            base = self._greys[answer]
            mask = b"\xff\xff\xff\xff"
        self._base[position:position + 4] = base
        self._mask[position:position + 4] = mask

    def _upload(self):
        self._base_texture.blit_buffer(bytes(self._base), colorfmt="rgba", bufferfmt="ubyte")
        self._mask_texture.blit_buffer(bytes(self._mask), colorfmt="rgba", bufferfmt="ubyte")
        self.canvas.ask_update()

    def _rebuild_all(self):
        for idx in range(len(self.game.answer)):
            self._write_cell(idx)
        self._upload()
        self._overlay_trigger()

    def refresh_cells(self, cells):
        """只更新改变了的格子。"""
        for idx in cells:
            self._write_cell(idx)
        self._upload()
        self._overlay_trigger()

    def _on_selected(self, *_):
        """换了颜色：取消旧编号的高亮，高亮新编号。"""
        if self.game is None:
            return
        old, self._highlighted = self._highlighted, self.selected
        cells = list(self.game.cells_by_number.get(old, []))
        cells += self.game.cells_by_number.get(self.selected, [])
        self.refresh_cells(cells)

    # ------------------------------------------------------------------
    # 视图：缩放和移动
    # ------------------------------------------------------------------

    def _on_size(self, *_):
        if self.game is not None and not self._touches:
            self.fit()
        self._update_view()

    def fit(self):
        """缩放到刚好看到整张图。"""
        if self.game is None or self.width < 10 or self.height < 10:
            return
        self._fit_scale = min(self.width / self.game.width, self.height / self.game.height) * 0.94
        self.scale = self._fit_scale
        self.offset = [(self.width - self.game.width * self.scale) / 2,
                       (self.height - self.game.height * self.scale) / 2]

    def _min_scale(self):
        return min(self._fit_scale * 0.5, 2.0)

    def zoom_at(self, x, y, factor):
        """以屏幕上的 (x, y) 为中心缩放。"""
        if self.game is None:
            return
        new_scale = _clamp(self.scale * factor, self._min_scale(), MAX_SCALE)
        self._set_view(new_scale, x, y, x, y, self.scale, self.offset)

    def _set_view(self, new_scale, anchor_x, anchor_y, target_x, target_y, old_scale, old_offset):
        """缩放后，让原来在 anchor 位置下的那一点移到 target 位置。"""
        grid_x = (anchor_x - self.x - old_offset[0]) / old_scale
        grid_y = (anchor_y - self.y - old_offset[1]) / old_scale
        self.scale = new_scale
        self._set_offset(target_x - self.x - grid_x * new_scale,
                         target_y - self.y - grid_y * new_scale)

    def _set_offset(self, offset_x, offset_y):
        """移动画布，但至少留一部分图在屏幕里，避免整张图被拖丢。"""
        margin = 60
        width = self.game.width * self.scale
        height = self.game.height * self.scale
        offset_x = _clamp(offset_x, margin - width, self.width - margin)
        offset_y = _clamp(offset_y, margin - height, self.height - margin)
        self.offset = [offset_x, offset_y]

    def pan(self, dx, dy):
        if self.game is not None:
            self._set_offset(self.offset[0] + dx, self.offset[1] + dy)

    def _fade(self):
        """0 到 1：0 表示远看（灰色轮廓），1 表示近看（白底）。"""
        return _clamp((self.scale - FADE_START) / (FADE_END - FADE_START), 0, 1)

    def _update_view(self, *_):
        self._background.pos = self.pos
        self._background.size = self.size
        if self.game is None:
            return
        origin = (self.x + self.offset[0], self.y + self.offset[1])
        size = (self.game.width * self.scale, self.game.height * self.scale)
        self._base_rect.pos = self._mask_rect.pos = origin
        self._base_rect.size = self._mask_rect.size = size
        self._mask_color.a = 0 if self._replaying else self._fade()
        self._update_hint_box()
        self._overlay_trigger()

    def cell_at(self, x, y):
        """屏幕坐标 (x, y) 落在哪一格，返回 (row, col)；不在图上返回 None。"""
        col = math.floor((x - self.x - self.offset[0]) / self.scale)
        flipped = math.floor((y - self.y - self.offset[1]) / self.scale)
        row = self.game.height - 1 - flipped
        if 0 <= row < self.game.height and 0 <= col < self.game.width:
            return row, col
        return None

    def _cell_origin(self, row, col):
        """某格左下角的屏幕坐标。"""
        return (self.x + self.offset[0] + col * self.scale,
                self.y + self.offset[1] + (self.game.height - 1 - row) * self.scale)

    # ------------------------------------------------------------------
    # 数字和网格线
    # ------------------------------------------------------------------

    @classmethod
    def _number_texture(cls, number):
        if number not in cls._number_textures:
            label = CoreLabel(text=str(number), font_size=44)
            label.refresh()
            cls._number_textures[number] = label.texture
        return cls._number_textures[number]

    def _visible_range(self):
        """屏幕上看得到的行和列范围。"""
        game = self.game
        col0 = max(0, math.floor(-self.offset[0] / self.scale))
        col1 = min(game.width - 1, math.floor((self.width - self.offset[0]) / self.scale))
        low = max(0, math.floor(-self.offset[1] / self.scale))
        high = min(game.height - 1, math.floor((self.height - self.offset[1]) / self.scale))
        row0 = game.height - 1 - high
        row1 = game.height - 1 - low
        return row0, row1, col0, col1

    def _rebuild_overlay(self, *_):
        overlay = self._overlay
        overlay.clear()
        if self.game is None or self._replaying:
            return
        fade = self._fade()
        number_alpha = _clamp((self.scale - NUMBER_START) / (NUMBER_FULL - NUMBER_START), 0, 1)
        row0, row1, col0, col1 = self._visible_range()
        if row0 > row1 or col0 > col1:
            return
        scale = self.scale

        # 网格线
        if fade > 0.05:
            overlay.add(Color(0.78, 0.78, 0.82, fade))
            left, bottom = self._cell_origin(row1, col0)
            right = left + (col1 - col0 + 1) * scale
            top = bottom + (row1 - row0 + 1) * scale
            for col in range(col0, col1 + 2):
                x = left + (col - col0) * scale
                overlay.add(Line(points=[x, bottom, x, top], width=1))
            for row in range(row1 - row0 + 2):
                y = bottom + row * scale
                overlay.add(Line(points=[left, y, right, y], width=1))

        # 数字：没填的格子用灰色数字，填错的格子用红色数字
        visible = (row1 - row0 + 1) * (col1 - col0 + 1)
        if number_alpha <= 0 or visible > MAX_NUMBER_CELLS:
            return
        game = self.game
        normal, wrong = [], []
        for row in range(row0, row1 + 1):
            base = row * game.width
            for col in range(col0, col1 + 1):
                idx = base + col
                value = self.display[idx]
                if value == 0:
                    normal.append((row, col, game.answer[idx]))
                elif value != game.answer[idx]:
                    wrong.append((row, col, game.answer[idx]))
        text_height = scale * 0.5
        for color, cells in (((0.35, 0.35, 0.42, number_alpha), normal),
                             ((0.85, 0.15, 0.2, number_alpha), wrong)):
            if not cells:
                continue
            overlay.add(Color(*color))
            for row, col, number in cells:
                texture = self._number_texture(number)
                text_width = text_height * texture.width / texture.height
                x, y = self._cell_origin(row, col)
                overlay.add(Rectangle(texture=texture,
                                      pos=(x + (scale - text_width) / 2, y + (scale - text_height) / 2),
                                      size=(text_width, text_height)))

    # ------------------------------------------------------------------
    # 提示：移动到一格并闪烁
    # ------------------------------------------------------------------

    def show_hint(self, idx):
        row, col = divmod(idx, self.game.width)
        scale = max(self.scale, 28.0)
        self.scale = min(scale, MAX_SCALE)
        center_x = (col + 0.5) * self.scale
        center_y = (self.game.height - 1 - row + 0.5) * self.scale
        self._set_offset(self.width / 2 - center_x, self.height / 2 - center_y)
        self._hint_idx = idx
        self._update_hint_box()
        Animation.cancel_all(self._hint_color)
        blink = Animation(a=1, duration=0.2) + Animation(a=0.15, duration=0.25)
        (blink + blink + blink + Animation(a=0, duration=0.3)).start(self._hint_color)

    def _update_hint_box(self):
        if self._hint_idx is None or self.game is None:
            return
        row, col = divmod(self._hint_idx, self.game.width)
        x, y = self._cell_origin(row, col)
        pad = 3
        self._hint_line.rectangle = (x - pad, y - pad, self.scale + 2 * pad, self.scale + 2 * pad)

    # ------------------------------------------------------------------
    # 填色
    # ------------------------------------------------------------------

    def _paint_cells(self, cells):
        changed = []
        width = self.game.width
        for row, col in cells:
            idx = row * width + col
            if self.game.paint(idx, self.selected):
                changed.append(idx)
        if changed:
            self._stroke_changed = True
            self.refresh_cells(changed)
            self.dispatch("on_cells_changed", changed)

    def _finish_stroke(self):
        if self._stroke_active:
            self.game.end_stroke()
            self._stroke_active = False
            if self._stroke_changed:
                self.dispatch("on_stroke_end")

    def _cancel_stroke(self):
        """第二根手指放上来时，把第一根手指刚画的那一笔撤掉，改成缩放。"""
        if self._stroke_active:
            self.game.end_stroke()
            self._stroke_active = False
            if self._stroke_changed:
                changed = self.game.undo()
                self.refresh_cells(changed)
                self.dispatch("on_cells_changed", changed)

    def apply_action(self, changed):
        """魔棒、油漆桶、撤销之后调用：刷新显示并通知外面。"""
        if changed:
            self.refresh_cells(changed)
            self.dispatch("on_cells_changed", changed)
            self.dispatch("on_stroke_end")

    def on_cells_changed(self, changed):
        pass

    def on_stroke_end(self):
        pass

    # ------------------------------------------------------------------
    # 鼠标和触摸
    # ------------------------------------------------------------------

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or self.game is None or self.locked:
            return False
        if touch.is_mouse_scrolling:
            if touch.button in ("scrolldown", "scrollleft"):
                self.zoom_at(touch.x, touch.y, 1.15)
            else:
                self.zoom_at(touch.x, touch.y, 1 / 1.15)
            return True

        touch.grab(self)
        self._touches.append(touch)
        if len(self._touches) == 2:
            self._cancel_stroke()
            self._start_pinch()
            return True
        if len(self._touches) > 2:
            return True

        button = getattr(touch, "button", "left")
        if button in ("right", "middle") or self.tool == "move" or self.space_pan:
            touch.ud["pan"] = True
            return True

        cell = self.cell_at(touch.x, touch.y)
        if self.tool == "wand":
            if cell:
                row, col = cell
                self.apply_action(self.game.magic_wand(row * self.game.width + col, self.selected))
            return True

        self.game.begin_stroke()
        self._stroke_active = True
        self._stroke_changed = False
        self._last_cell = cell
        if cell:
            self._paint_cells([cell])
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        if len(self._touches) >= 2:
            self._update_pinch()
            return True
        if touch.ud.get("pan"):
            self.pan(touch.dx, touch.dy)
            return True
        if self._stroke_active:
            cell = self.cell_at(touch.x, touch.y)
            if cell and self._last_cell:
                self._paint_cells(cells_on_line(*self._last_cell, *cell))
            elif cell:
                self._paint_cells([cell])
            if cell:
                self._last_cell = cell
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        if touch in self._touches:
            self._touches.remove(touch)
        if len(self._touches) < 2:
            self._pinch = None
        if not self._touches:
            self._finish_stroke()
        return True

    def _start_pinch(self):
        first, second = self._touches[:2]
        self._pinch = {
            "distance": max(1.0, math.dist(first.pos, second.pos)),
            "center": ((first.x + second.x) / 2, (first.y + second.y) / 2),
            "scale": self.scale,
            "offset": list(self.offset),
        }

    def _update_pinch(self):
        if self._pinch is None:
            return
        first, second = self._touches[:2]
        distance = max(1.0, math.dist(first.pos, second.pos))
        center = ((first.x + second.x) / 2, (first.y + second.y) / 2)
        start = self._pinch
        new_scale = _clamp(start["scale"] * distance / start["distance"], self._min_scale(), MAX_SCALE)
        self._set_view(new_scale, *start["center"], *center, start["scale"], start["offset"])

    # ------------------------------------------------------------------
    # 回放填色过程（完成动画）
    # ------------------------------------------------------------------

    def play_replay(self, duration, on_done=None):
        """从空白开始，按顺序把填色过程快速播放一遍。"""
        game = self.game
        changes = [stroke[i:i + 3] for stroke in game.history for i in range(0, len(stroke), 3)]
        if not changes:
            if on_done:
                on_done()
            return
        self.locked = True
        self._replaying = True
        self.display = [0] * len(game.answer)
        self.fit()
        self._rebuild_all()
        self._update_view()
        per_frame = max(1, math.ceil(len(changes) / (duration * 60)))
        state = {"next": 0}

        def step(_dt):
            start = state["next"]
            end = min(len(changes), start + per_frame)
            touched = []
            for idx, _old, new in changes[start:end]:
                self.display[idx] = new
                touched.append(idx)
            state["next"] = end
            self.refresh_cells(touched)
            if end >= len(changes):
                self._replaying = False
                self.display = game.painted
                self.locked = False
                self._rebuild_all()
                self._update_view()
                if on_done:
                    on_done()
                return False
            return True

        Clock.schedule_interval(step, 1 / 60)
