"""
填色页面：上面是按钮，中间是画布，左边是工具，下面是颜色栏。
"""

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from colornumber.ui.common import ACCENT, Chip, Dialog, RoundButton, contrast_text_color, tr  # noqa: F401
from colornumber.ui.confetti import Confetti  # noqa: F401  （KV 里用到）
from colornumber.ui.exporting import export_game
from colornumber.ui.paint_canvas import PaintCanvas  # noqa: F401  （KV 里用到）

AUTOSAVE_DELAY = 1.5   # 停笔 1.5 秒后自动保存

Builder.load_string("""
<GameScreen>:
    canvas.before:
        Color:
            rgba: 0.97, 0.96, 0.94, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "8dp"

        # 顶部：返回、名字、进度、撤销、提示
        BoxLayout:
            size_hint_y: None
            height: "44dp"
            spacing: "8dp"
            RoundButton:
                text: app.tr("back", app.lang)
                size_hint_x: None
                width: "90dp"
                on_release: root.go_back()
            Label:
                text: root.title
                color: 0.2, 0.2, 0.25, 1
                font_size: "18sp"
                bold: True
                shorten: True
                text_size: self.size
                halign: "left"
                valign: "middle"
            Label:
                text: app.tr("progress", app.lang, percent=root.percent)
                color: 0.3, 0.52, 0.95, 1
                font_size: "18sp"
                bold: True
                size_hint_x: None
                width: "70dp"
            RoundButton:
                text: app.tr("undo", app.lang)
                size_hint_x: None
                width: "90dp"
                on_release: root.undo()
            RoundButton:
                text: app.tr("hint", app.lang)
                primary: True
                size_hint_x: None
                width: "90dp"
                on_release: root.hint()

        BoxLayout:
            spacing: "8dp"

            # 左边：工具
            BoxLayout:
                orientation: "vertical"
                size_hint_x: None
                width: "92dp"
                spacing: "8dp"
                Chip:
                    id: tool_brush
                    text: app.tr("tool_brush", app.lang)
                    group: "tool"
                    state: "down"
                    on_state: if self.state == "down": canvas_widget.tool = "brush"
                Chip:
                    id: tool_wand
                    text: app.tr("tool_wand", app.lang)
                    group: "tool"
                    on_state: if self.state == "down": canvas_widget.tool = "wand"
                Chip:
                    id: tool_move
                    text: app.tr("tool_move", app.lang)
                    group: "tool"
                    on_state: if self.state == "down": canvas_widget.tool = "move"
                Widget:
                    size_hint_y: None
                    height: "6dp"
                RoundButton:
                    text: app.tr("tool_bucket", app.lang)
                    on_release: root.bucket()
                RoundButton:
                    text: app.tr("fit_view", app.lang)
                    on_release: canvas_widget.fit()
                Widget:
                Label:
                    text: app.tr("controls_help", app.lang)
                    color: 0.5, 0.5, 0.55, 1
                    font_size: "11sp"
                    text_size: self.width, None
                    size_hint_y: None
                    height: self.texture_size[1]

            FloatLayout:
                PaintCanvas:
                    id: canvas_widget
                    pos: self.parent.pos
                    size: self.parent.size
                    on_cells_changed: root.on_cells_changed(*args[1:])
                    on_stroke_end: root.on_stroke_end()
                Confetti:
                    id: confetti
                    pos: self.parent.pos
                    size: self.parent.size

        # 下面：颜色栏
        ScrollView:
            size_hint_y: None
            height: "84dp"
            do_scroll_y: False
            bar_width: "4dp"
            BoxLayout:
                id: palette
                size_hint_x: None
                width: self.minimum_width
                spacing: "8dp"
                padding: "4dp"
""")


class ColorSwatch(ButtonBehavior, Widget):
    """颜色栏里的一个颜色：色块、编号、剩余进度，填完打勾。"""

    number = NumericProperty(1)
    rgb = ListProperty([255, 255, 255])
    total = NumericProperty(1)
    remaining = NumericProperty(1)
    selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(62), dp(74))
        self._label = Label(font_size="17sp", bold=True)
        self.add_widget(self._label)
        self.bind(pos=self._redraw, size=self._redraw, rgb=self._redraw, total=self._redraw,
                  remaining=self._redraw, selected=self._redraw, number=self._redraw)
        self._redraw()

    def _redraw(self, *_):
        self.canvas.before.clear()
        done = self.remaining == 0
        rgb = [value / 255 for value in self.rgb]
        box = dp(52)
        left = self.x + (self.width - box) / 2
        bottom = self.y + dp(14)
        with self.canvas.before:
            if self.selected:
                Color(*ACCENT)
                RoundedRectangle(pos=(left - dp(4), bottom - dp(4)), size=(box + dp(8), box + dp(8)),
                                 radius=[dp(14)])
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=(left - dp(1.5), bottom - dp(1.5)), size=(box + dp(3), box + dp(3)),
                                 radius=[dp(12)])
            Color(*rgb, 0.45 if done else 1)
            RoundedRectangle(pos=(left, bottom), size=(box, box), radius=[dp(10)])
            # 下面的进度条
            Color(0.85, 0.85, 0.88, 1)
            RoundedRectangle(pos=(left, self.y + dp(3)), size=(box, dp(5)), radius=[dp(2.5)])
            filled = 1 - self.remaining / max(1, self.total)
            Color(*ACCENT)
            RoundedRectangle(pos=(left, self.y + dp(3)), size=(box * filled, dp(5)), radius=[dp(2.5)])
            if done:
                Color(*contrast_text_color(self.rgb))
                cx, cy = left + box / 2, bottom + box / 2
                Line(points=[cx - dp(12), cy, cx - dp(3), cy - dp(9), cx + dp(13), cy + dp(10)],
                     width=dp(2.5), cap="round", joint="round")
        self._label.text = "" if done else str(self.number)
        self._label.color = contrast_text_color(self.rgb)
        self._label.center = (left + box / 2, bottom + box / 2)


class GameScreen(Screen):
    title = ObjectProperty("")
    percent = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.meta = None
        self.game = None
        self._swatches = {}
        self._was_complete = False
        self._save_trigger = Clock.create_trigger(lambda _dt: self.save(), AUTOSAVE_DELAY)
        self.app = App.get_running_app()   # 程序关闭时 get_running_app() 会返回 None，所以先存下来

    @property
    def canvas_widget(self):
        return self.ids.canvas_widget

    # ------------------------------------------------------------------
    # 打开和保存
    # ------------------------------------------------------------------

    def open_project(self, meta, game):
        app = App.get_running_app()
        self.meta = meta
        self.game = game
        game.wrong_mode = app.settings.wrong_mode
        self.title = meta["name"]
        self._was_complete = game.is_complete()
        self.set_tool("brush")
        self._build_palette()
        first = game.next_unfinished_number(game.picture.color_count) or 1
        self.canvas_widget.selected = first
        self.canvas_widget.load_game(game)
        self._select(first)
        self._update_progress()
        if self._was_complete:
            Clock.schedule_once(lambda _dt: self.show_completion(), 0.3)

    def save(self):
        if self.meta is not None and self.game is not None:
            self.app.store.save(self.meta, self.game)

    def go_back(self):
        self._save_trigger.cancel()
        self.save()
        App.get_running_app().show_home()

    def set_tool(self, name):
        """用代码切换工具。（用代码改按钮状态时，同组的其他按钮要自己取消选中）"""
        for tool in ("brush", "wand", "move"):
            self.ids[f"tool_{tool}"].state = "down" if tool == name else "normal"

    # ------------------------------------------------------------------
    # 颜色栏
    # ------------------------------------------------------------------

    def _build_palette(self):
        palette = self.ids.palette
        palette.clear_widgets()
        self._swatches = {}
        game = self.game
        for number in range(1, game.picture.color_count + 1):
            swatch = ColorSwatch(number=number, rgb=list(game.picture.color_of(number)),
                                 total=len(game.cells_by_number[number]),
                                 remaining=game.remaining_count(number))
            swatch.bind(on_release=lambda widget: self._select(widget.number))
            palette.add_widget(swatch)
            self._swatches[number] = swatch

    def _select(self, number):
        self.canvas_widget.selected = number
        for n, swatch in self._swatches.items():
            swatch.selected = (n == number)
        swatch = self._swatches.get(number)
        scroll = self.ids.palette.parent
        if swatch is not None and self.ids.palette.width > scroll.width:
            scroll.scroll_to(swatch, padding=dp(40), animate=True)

    def _update_progress(self):
        self.percent = int(self.game.progress() * 100)

    # ------------------------------------------------------------------
    # 画布传来的事件
    # ------------------------------------------------------------------

    def on_cells_changed(self, changed):
        App.get_running_app().sounds.play("pop")
        numbers = {self.game.answer[idx] for idx in changed}
        for number in numbers:
            self._swatches[number].remaining = self.game.remaining_count(number)
        self._update_progress()

    def on_stroke_end(self):
        self._save_trigger()
        app = App.get_running_app()
        if self.game.is_complete():
            if not self._was_complete:
                self._was_complete = True
                self.celebrate()
            return
        self._was_complete = False
        selected = self.canvas_widget.selected
        if self.game.remaining_count(selected) == 0:
            app.sounds.play("color_done")
            following = self.game.next_unfinished_number(selected)
            if following is not None:
                self._select(following)

    # ------------------------------------------------------------------
    # 按钮
    # ------------------------------------------------------------------

    def undo(self):
        if self.canvas_widget.locked:
            return
        changed = self.game.undo()
        if changed:
            self.canvas_widget.apply_action(changed)
            # 撤销可能让一个已经填完的颜色又有了空格，或者把错误的颜色撤掉
            for number, swatch in self._swatches.items():
                swatch.remaining = self.game.remaining_count(number)

    def bucket(self):
        if self.canvas_widget.locked:
            return
        self.canvas_widget.apply_action(self.game.bucket(self.canvas_widget.selected))

    def hint(self):
        if self.canvas_widget.locked or self.game.is_complete():
            return
        canvas = self.canvas_widget
        row0, row1, col0, col1 = canvas._visible_range()
        idx = self.game.find_hint(canvas.selected, (row0 + row1) / 2, (col0 + col1) / 2)
        if idx is None:
            return
        number = self.game.answer[idx]
        if number != canvas.selected:
            self._select(number)
        canvas.show_hint(idx)

    # ------------------------------------------------------------------
    # 完成
    # ------------------------------------------------------------------

    def celebrate(self):
        app = App.get_running_app()
        self._save_trigger.cancel()
        self.save()
        app.sounds.play("complete")
        self.ids.confetti.burst()
        self.canvas_widget.play_replay(3.0, on_done=lambda: Clock.schedule_once(
            lambda _dt: self.show_completion(), 0.4))

    def replay(self):
        self.canvas_widget.play_replay(3.0, on_done=lambda: Clock.schedule_once(
            lambda _dt: self.show_completion(), 0.4))

    def show_completion(self):
        game, name = self.game, self.meta["name"]
        buttons = [(tr(f"export_{kind}"), lambda k=kind: export_game(game, name, k), "primary", False)
                   for kind in ("png", "gif", "mp4")]
        buttons += [
            (tr("replay"), self.replay, "normal"),
            (tr("back_to_gallery"), self.go_back, "normal"),
            (tr("keep_looking"), None, "normal"),
        ]
        Dialog("", buttons, title=tr("picture_complete")).open()

    # ------------------------------------------------------------------
    # 键盘
    # ------------------------------------------------------------------

    def on_enter(self, *_):
        Window.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)

    def on_leave(self, *_):
        Window.unbind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
        self.canvas_widget.space_pan = False

    def _on_key_down(self, _window, key, _scancode, codepoint, modifiers):
        canvas = self.canvas_widget
        command = "meta" in modifiers or "ctrl" in modifiers
        if command and codepoint == "z":
            self.undo()
        elif key == 32:                       # 空格
            canvas.space_pan = True
        elif codepoint == "b":
            self.set_tool("brush")
        elif codepoint == "w":
            self.set_tool("wand")
        elif codepoint == "m":
            self.set_tool("move")
        elif codepoint == "h":
            self.hint()
        elif codepoint == "0":
            canvas.fit()
        elif codepoint in ("=", "+"):
            canvas.zoom_at(canvas.center_x, canvas.center_y, 1.25)
        elif codepoint == "-":
            canvas.zoom_at(canvas.center_x, canvas.center_y, 1 / 1.25)
        elif key in (273, 274, 275, 276):     # 方向键
            step = dp(60)
            dx = {275: -step, 276: step}.get(key, 0)
            dy = {273: -step, 274: step}.get(key, 0)
            canvas.pan(dx, dy)
        else:
            return False
        return True

    def _on_key_up(self, _window, key, *_):
        if key == 32:
            self.canvas_widget.space_pan = False
        return False
