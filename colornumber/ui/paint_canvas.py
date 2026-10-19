"""
填色画布：显示格子，处理缩放、拖动和填色。

为了让 512 × 512（26 万格）的大图也能流畅显示，画布不是一格一格地画，
而是把整张图做成两张"贴图"（每格一个像素），再放大显示：

- 底图（base）：填了的格子显示颜色，没填的格子显示浅灰色轮廓
- 白色遮罩（mask）：没填的格子是白色，填了的格子透明

缩小时遮罩完全透明，看到的是灰色轮廓；放大时遮罩慢慢变成不透明，
没填的格子就渐渐变成白色，数字也渐渐出现。改变遮罩的透明度几乎不花时间。

数字和网格线（"数字层"）只画屏幕附近的格子。移动或缩放时，数字层先整体
平移、缩放跟着走，停下来以后才重新生成，这样拖动和捏合都很流畅。
"""

import math

import numpy as np
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import (Color, InstructionGroup, Line, PopMatrix, PushMatrix, Rectangle,
                           Scale, Translate)
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
OVERLAY_MARGIN = 0.35   # 数字层在屏幕外多画一圈（屏幕大小的 35%），移动时不用马上重画

HIGHLIGHT_BASE = (150, 160, 185)    # 当前编号没填的格子：远看的颜色
HIGHLIGHT_MASK = (198, 214, 245)    # 当前编号没填的格子：近看的颜色
CANVAS_BACKGROUND = (0.90, 0.90, 0.91, 1)
NUMBER_COLOR = (0.35, 0.35, 0.42)
WRONG_COLOR = (0.85, 0.15, 0.2)


def _clamp(value, low, high):
    return max(low, min(high, value))


class PaintCanvas(StencilView):
    """可以缩放和拖动的填色画布。"""

    selected = NumericProperty(1)        # 当前选中的颜色编号
    tool = StringProperty("brush")       # "brush" 画笔，"wand" 魔棒，"move" 移动
    brush = NumericProperty(1)           # 笔刷大小：1、3 或 5 格
    scale = NumericProperty(1.0)         # 每格显示成多少像素
    offset = ListProperty([0.0, 0.0])    # 图的左下角相对画布左下角的位置
    space_pan = BooleanProperty(False)   # 按住空格时，左键拖动变成移动画布
    locked = BooleanProperty(False)      # 回放动画时不能操作

    __events__ = ("on_cells_changed", "on_stroke_end", "on_pick")

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
        self._at_fit = True          # 现在是不是"显示全图"的状态（改窗口大小时用）
        self._last_size = None
        self._built = None           # 数字层是按什么视图生成的
        self._number_rects = {}      # 格子 → (数字的 Rectangle, "normal" 或 "wrong")

        with self.canvas:
            Color(*CANVAS_BACKGROUND)
            self._background = Rectangle()
            Color(1, 1, 1, 1)
            self._base_rect = Rectangle()
            self._mask_color = Color(1, 1, 1, 0)
            self._mask_rect = Rectangle()
            PushMatrix()
            self._overlay_scale = Scale(1, 1, 1)
            self._overlay_shift = Translate(0, 0)
        self._overlay = InstructionGroup()
        self.canvas.add(self._overlay)
        with self.canvas:
            PopMatrix()
            self._hint_color = Color(0.95, 0.25, 0.3, 0)
            self._hint_line = Line(width=2.5)

        self._rebuild_soon = Clock.create_trigger(self._rebuild_overlay, 0.12)
        self._rebuild_now = Clock.create_trigger(self._rebuild_overlay, -1)
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
        palette = np.array(game.picture.palette, dtype=np.uint8)
        alpha = np.full((len(palette), 1), 255, dtype=np.uint8)
        self._colors = np.vstack([[0, 0, 0, 0], np.hstack([palette, alpha])]).astype(np.uint8)
        greys = np.array([grey_of(color) for color in game.picture.palette], dtype=np.uint8)
        self._greys = np.vstack([[0, 0, 0, 0], np.hstack([greys, alpha])]).astype(np.uint8)
        self._answer = np.array(game.answer, dtype=np.int64)
        self._base = np.zeros((height, width, 4), dtype=np.uint8)
        self._mask = np.zeros((height, width, 4), dtype=np.uint8)
        self._base_texture = self._make_texture(width, height)
        self._mask_texture = self._make_texture(width, height)
        self._base_rect.texture = self._base_texture
        self._mask_rect.texture = self._mask_texture
        self._highlighted = self.selected
        self._hint_idx = None
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
        """根据这格的状态，算出它在两张贴图里的颜色。贴图的第 0 行在最下面。"""
        game = self.game
        row, col = divmod(idx, game.width)
        texture_row = game.height - 1 - row
        value = self.display[idx]
        answer = game.answer[idx]
        if value:
            self._base[texture_row, col] = self._colors[value]
            self._mask[texture_row, col] = (0, 0, 0, 0)
        elif answer == self._highlighted and not self._replaying:
            self._base[texture_row, col] = HIGHLIGHT_BASE + (255,)
            self._mask[texture_row, col] = HIGHLIGHT_MASK + (255,)
        else:
            self._base[texture_row, col] = self._greys[answer]
            self._mask[texture_row, col] = (255, 255, 255, 255)

    def _rebuild_all(self):
        """用 numpy 一次算出所有格子的颜色。"""
        game = self.game
        display = np.array(self.display, dtype=np.int64)
        unfilled = display == 0
        base = np.where(unfilled[:, None], self._greys[self._answer], self._colors[display])
        mask = np.where(unfilled[:, None], np.uint8(255), np.uint8(0)).repeat(4, 1)
        if not self._replaying:
            highlight = unfilled & (self._answer == self._highlighted)
            base[highlight] = HIGHLIGHT_BASE + (255,)
            mask[highlight] = HIGHLIGHT_MASK + (255,)
        shape = (game.height, game.width, 4)
        self._base = np.ascontiguousarray(base.reshape(shape)[::-1])
        self._mask = np.ascontiguousarray(mask.reshape(shape)[::-1])
        self._upload()
        self._built = None
        self._rebuild_now()

    def _upload(self):
        self._base_texture.blit_buffer(self._base.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
        self._mask_texture.blit_buffer(self._mask.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
        self.canvas.ask_update()

    def refresh_cells(self, cells):
        """只更新改变了的格子。"""
        for idx in cells:
            self._write_cell(idx)
        self._upload()
        self._patch_numbers(cells)

    def _on_selected(self, *_):
        """换了颜色：取消旧编号的高亮，高亮新编号。"""
        if self.game is None:
            return
        old, self._highlighted = self._highlighted, self.selected
        cells = list(self.game.cells_by_number.get(old, []))
        cells += self.game.cells_by_number.get(self.selected, [])
        for idx in cells:
            self._write_cell(idx)
        self._upload()

    # ------------------------------------------------------------------
    # 视图：缩放和移动
    # ------------------------------------------------------------------

    def _on_size(self, *_):
        if self.game is not None and not self._touches:
            if self._at_fit or self._last_size is None:
                self.fit()
            else:
                # 窗口变大或变小时，保持画面中心不变
                old_width, old_height = self._last_size
                self._set_offset(self.offset[0] + (self.width - old_width) / 2,
                                 self.offset[1] + (self.height - old_height) / 2)
        self._last_size = tuple(self.size)
        self._update_view()

    def fit(self):
        """缩放到刚好看到整张图。"""
        if self.game is None or self.width < 10 or self.height < 10:
            return
        self._fit_scale = min(self.width / self.game.width, self.height / self.game.height) * 0.94
        self.scale = self._fit_scale
        self.offset = [(self.width - self.game.width * self.scale) / 2,
                       (self.height - self.game.height * self.scale) / 2]
        self._at_fit = True

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
        self._at_fit = False

    def pan(self, dx, dy):
        if self.game is not None:
            self._set_offset(self.offset[0] + dx, self.offset[1] + dy)

    def gesture_zoom(self, factor):
        """触控板捏合：以鼠标位置为中心缩放。"""
        if self.game is not None and not self.locked:
            self.zoom_at(*Window.mouse_pos, factor)

    def gesture_pan(self, dx, dy):
        """触控板双指滑动：移动画布。"""
        if not self.locked:
            self.pan(dx, dy)

    def wants_gesture(self):
        """鼠标在画布上、而且可以操作时，才接收触控板手势。"""
        return self.game is not None and not self.locked and self.collide_point(*Window.mouse_pos)

    def _fade(self):
        """0 到 1：0 表示远看（灰色轮廓），1 表示近看（白底）。"""
        return _clamp((self.scale - FADE_START) / (FADE_END - FADE_START), 0, 1)

    def _number_alpha(self):
        return _clamp((self.scale - NUMBER_START) / (NUMBER_FULL - NUMBER_START), 0, 1)

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
        self._follow_view()

    def cell_at(self, x, y):
        """屏幕坐标 (x, y) 落在哪一格，返回 (row, col)；不在图上返回 None。"""
        col = math.floor((x - self.x - self.offset[0]) / self.scale)
        flipped = math.floor((y - self.y - self.offset[1]) / self.scale)
        row = self.game.height - 1 - flipped
        if 0 <= row < self.game.height and 0 <= col < self.game.width:
            return row, col
        return None

    def _cell_origin(self, row, col, offset=None, scale=None):
        """某格左下角的屏幕坐标（默认按现在的视图算）。"""
        offset = offset or self.offset
        scale = scale or self.scale
        return (self.x + offset[0] + col * scale,
                self.y + offset[1] + (self.game.height - 1 - row) * scale)

    def visible_range(self, scale=None, offset=None):
        """屏幕上看得到的行和列范围 (第一行, 最后一行, 第一列, 最后一列)。"""
        game = self.game
        scale = scale or self.scale
        offset = offset or self.offset
        col0 = max(0, math.floor(-offset[0] / scale))
        col1 = min(game.width - 1, math.floor((self.width - offset[0]) / scale))
        low = max(0, math.floor(-offset[1] / scale))
        high = min(game.height - 1, math.floor((self.height - offset[1]) / scale))
        return game.height - 1 - high, game.height - 1 - low, col0, col1

    # ------------------------------------------------------------------
    # 数字层：数字和网格线
    # ------------------------------------------------------------------

    @classmethod
    def _number_texture(cls, number):
        if number not in cls._number_textures:
            label = CoreLabel(text=str(number), font_size=44)
            label.refresh()
            cls._number_textures[number] = label.texture
        return cls._number_textures[number]

    def _follow_view(self):
        """
        视图变了：数字层先整体平移、缩放跟上（很快），需要时再安排重新生成。
        数字层是按 self._built 记下的视图生成的。
        """
        built = self._built
        if built is None or self._replaying:
            self._rebuild_now()
            return
        ratio = self.scale / built["scale"]
        anchor = (self.x + self.offset[0], self.y + self.offset[1])
        self._overlay_scale.origin = anchor
        self._overlay_scale.x = self._overlay_scale.y = ratio
        self._overlay_shift.x = self.offset[0] - built["offset"][0]
        self._overlay_shift.y = self.offset[1] - built["offset"][1]
        alpha = self._number_alpha()
        for color, rgb in ((built["number_color"], NUMBER_COLOR), (built["wrong_color"], WRONG_COLOR)):
            if color is not None:
                color.rgba = (*rgb, alpha)
        if built["grid_color"] is not None:
            built["grid_color"].a = self._fade()

        if ratio != 1:
            self._rebuild_soon.cancel()             # 缩放停下来 0.12 秒以后再按新大小重画
            self._rebuild_soon()
            return
        row0, row1, col0, col1 = self.visible_range()
        if not (built["rows"][0] <= row0 and row1 <= built["rows"][1]
                and built["cols"][0] <= col0 and col1 <= built["cols"][1]):
            self._rebuild_now()                     # 移出了画好的范围
        elif built["empty"] and (alpha > 0 or self._fade() > 0.05):
            self._rebuild_now()                     # 之前太小没画数字，现在需要了

    def _rebuild_overlay(self, *_):
        overlay = self._overlay
        overlay.clear()
        self._number_rects = {}
        self._overlay_scale.x = self._overlay_scale.y = 1
        self._overlay_shift.x = self._overlay_shift.y = 0
        self._built = None
        if self.game is None or self._replaying or self.width < 10:
            return
        scale = self.scale
        offset = list(self.offset)
        fade = self._fade()
        alpha = self._number_alpha()
        row0, row1, col0, col1 = self.visible_range()
        built = {"scale": scale, "offset": offset, "rows": (row0, row1), "cols": (col0, col1),
                 "grid_color": None, "number_color": None, "wrong_color": None, "empty": True}
        self._built = built
        if row0 > row1 or col0 > col1 or (fade <= 0.05 and alpha <= 0):
            return

        # 在屏幕外多画一圈，移动一点点不用重画
        rows_visible, cols_visible = row1 - row0 + 1, col1 - col0 + 1
        if rows_visible * cols_visible * (1 + 2 * OVERLAY_MARGIN) ** 2 <= MAX_NUMBER_CELLS * 1.6:
            extra_rows = int(rows_visible * OVERLAY_MARGIN) + 1
            extra_cols = int(cols_visible * OVERLAY_MARGIN) + 1
            row0, row1 = max(0, row0 - extra_rows), min(self.game.height - 1, row1 + extra_rows)
            col0, col1 = max(0, col0 - extra_cols), min(self.game.width - 1, col1 + extra_cols)
            built["rows"], built["cols"] = (row0, row1), (col0, col1)
        built["empty"] = False

        # 网格线
        if fade > 0.05:
            built["grid_color"] = Color(0.78, 0.78, 0.82, fade)
            overlay.add(built["grid_color"])
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
        if alpha <= 0 or (row1 - row0 + 1) * (col1 - col0 + 1) > MAX_NUMBER_CELLS * 1.6:
            return
        self._normal_group = InstructionGroup()
        self._wrong_group = InstructionGroup()
        built["number_color"] = Color(*NUMBER_COLOR, alpha)
        built["wrong_color"] = Color(*WRONG_COLOR, alpha)
        overlay.add(built["number_color"])
        overlay.add(self._normal_group)
        overlay.add(built["wrong_color"])
        overlay.add(self._wrong_group)
        game = self.game
        for row in range(row0, row1 + 1):
            base = row * game.width
            for col in range(col0, col1 + 1):
                idx = base + col
                value = self.display[idx]
                if value == 0:
                    self._add_number(idx, "normal")
                elif value != game.answer[idx]:
                    self._add_number(idx, "wrong")

    def _add_number(self, idx, kind):
        """在数字层里加一个数字（坐标按生成数字层时的视图算）。"""
        built = self._built
        scale = built["scale"]
        row, col = divmod(idx, self.game.width)
        texture = self._number_texture(self.game.answer[idx])
        text_height = scale * 0.5
        text_width = text_height * texture.width / texture.height
        x, y = self._cell_origin(row, col, built["offset"], scale)
        rect = Rectangle(texture=texture, size=(text_width, text_height),
                         pos=(x + (scale - text_width) / 2, y + (scale - text_height) / 2))
        (self._normal_group if kind == "normal" else self._wrong_group).add(rect)
        self._number_rects[idx] = (rect, kind)

    def _patch_numbers(self, cells):
        """
        格子变了以后只改动这些格子的数字，不用整个数字层重画。
        改动很多（比如油漆桶）时直接重画更快。
        """
        built = self._built
        if built is None or built["number_color"] is None:
            return                             # 现在没有显示数字，不用处理
        if len(cells) > 400:
            self._rebuild_now()
            return
        game = self.game
        (row0, row1), (col0, col1) = built["rows"], built["cols"]
        for idx in cells:
            row, col = divmod(idx, game.width)
            if not (row0 <= row <= row1 and col0 <= col <= col1):
                continue
            value = self.display[idx]
            wanted = None if value == game.answer[idx] else ("wrong" if value else "normal")
            current = self._number_rects.get(idx)
            if current is not None and current[1] == wanted:
                continue
            if current is not None:
                current[0].size = (0, 0)       # 藏起来，比从列表里删除快
                del self._number_rects[idx]
            if wanted is not None:
                self._add_number(idx, wanted)

    # ------------------------------------------------------------------
    # 提示：移动到一格并闪烁
    # ------------------------------------------------------------------

    def show_hint(self, idx):
        row, col = divmod(idx, self.game.width)
        self.scale = min(max(self.scale, 28.0), MAX_SCALE)
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

    def _brush_cells(self, cells):
        """把一串格子按笔刷大小扩展成方块（去掉重复的、超出边界的）。"""
        if self.brush <= 1:
            return cells
        radius = self.brush // 2
        result = []
        seen = set()
        for row, col in cells:
            for r in range(row - radius, row + radius + 1):
                for c in range(col - radius, col + radius + 1):
                    if (r, c) not in seen and 0 <= r < self.game.height and 0 <= c < self.game.width:
                        seen.add((r, c))
                        result.append((r, c))
        return result

    def _paint_cells(self, cells):
        changed = []
        width = self.game.width
        for row, col in self._brush_cells(cells):
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
                self.game.redo_stack.pop()      # 这一笔不应该能"重做"回来
                self.refresh_cells(changed)
                self.dispatch("on_cells_changed", changed)

    def apply_action(self, changed):
        """魔棒、油漆桶、撤销、重做之后调用：刷新显示并通知外面。"""
        if changed:
            self.refresh_cells(changed)
            self.dispatch("on_cells_changed", changed)
            self.dispatch("on_stroke_end")

    def on_cells_changed(self, changed):
        pass

    def on_stroke_end(self):
        pass

    def on_pick(self, number):
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
        if "alt" in Window.modifiers:
            # 按住 Option（Alt）点一下：吸管，选中这一格的颜色
            if cell:
                row, col = cell
                self.dispatch("on_pick", self.game.answer[row * self.game.width + col])
            touch.ud["picked"] = True
            return True
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
            for idx, _old, new in changes[start:end]:
                self.display[idx] = new
                self._write_cell(idx)
            self._upload()
            state["next"] = end
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
