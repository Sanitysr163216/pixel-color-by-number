"""
设置页面：语言、填错模式、格子和颜色上限、声音。
"""

from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from colornumber.core.game import ALLOW_WRONG, BLOCK_WRONG
from colornumber.core.settings import COLOR_LIMIT_CHOICES, GRID_LIMIT_CHOICES
from colornumber.ui.common import BACKGROUND, TEXT, Chip, RoundButton, confirm, tr


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*BACKGROUND)
            self._bg = Rectangle()
        self.bind(pos=self._update_bg, size=self._update_bg)
        App.get_running_app().bind(lang=lambda *_: self.build())
        self.build()

    def _update_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def build(self):
        """（重新）建立整个页面。换语言时也调用它。"""
        app = App.get_running_app()
        settings = app.settings
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(14))

        header = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        back = RoundButton(text=tr("back"), size_hint_x=None, width=dp(90))
        back.bind(on_release=lambda _b: app.show_home())
        header.add_widget(back)
        title = Label(text=tr("settings"), color=TEXT, font_size="22sp", bold=True,
                      halign="left", valign="middle")
        title.bind(size=lambda widget, value: setattr(widget, "text_size", value))
        header.add_widget(title)
        root.add_widget(header)

        rows = BoxLayout(orientation="vertical", spacing=dp(18), size_hint_y=None)
        rows.bind(minimum_height=rows.setter("height"))

        rows.add_widget(self._choice_row(
            "language", [("zh", "中文"), ("en", "English")], settings.language,
            lambda value, _revert: app.set_language(value)))
        rows.add_widget(self._choice_row(
            "wrong_mode", [(BLOCK_WRONG, tr("wrong_block")), (ALLOW_WRONG, tr("wrong_allow"))],
            settings.wrong_mode, lambda value, _revert: app.update_setting("wrong_mode", value)))
        rows.add_widget(self._choice_row(
            "grid_limit", [(value, str(value)) for value in GRID_LIMIT_CHOICES],
            settings.grid_limit, self._choose_grid_limit))
        rows.add_widget(self._choice_row(
            "color_limit", [(value, str(value)) for value in COLOR_LIMIT_CHOICES],
            settings.color_limit, self._choose_color_limit))
        rows.add_widget(self._choice_row(
            "sound", [(True, tr("on")), (False, tr("off"))], settings.sound,
            lambda value, _revert: app.update_setting("sound", value)))
        rows.add_widget(self._choice_row(
            "music", [(True, tr("on")), (False, tr("off"))], settings.music,
            lambda value, _revert: app.update_setting("music", value)))

        scroll = ScrollView()
        scroll.add_widget(rows)
        root.add_widget(scroll)
        self.add_widget(root)

    def _choice_row(self, title_key, options, current, on_choose):
        """
        一行设置：左边标题，右边几个选项按钮。
        on_choose(value, revert) 在玩家选了新选项时调用；调用 revert() 可以退回原来的选项。
        """
        row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        row.add_widget(Label(text=tr(title_key), color=TEXT, font_size="16sp", size_hint_x=None,
                             width=dp(220), halign="left", valign="middle", text_size=(dp(220), None)))
        group = f"settings_{title_key}"
        chips = {}
        state = {"current": current, "syncing": False}

        def revert():
            state["syncing"] = True
            chips[state["current"]].state = "down"
            state["syncing"] = False

        def on_state(chip, value):
            if value != "down" or state["syncing"]:
                return
            if chip.value == state["current"]:
                return
            previous = state["current"]
            state["current"] = chip.value

            def undo_choice():
                state["current"] = previous
                revert()

            on_choose(chip.value, undo_choice)

        for value, label in options:
            chip = Chip(text=label, group=group, size_hint_x=None, width=dp(150 if len(label) > 4 else 90))
            chip.value = value
            chip.state = "down" if value == current else "normal"
            chip.bind(state=on_state)
            chips[value] = chip
            row.add_widget(chip)
        row.add_widget(Label())
        return row

    def _choose_grid_limit(self, value, revert):
        app = App.get_running_app()
        if value <= 128:
            app.update_setting("grid_limit", value)
            return
        cells = value * value
        confirm(tr("grid_warning", value=value, cells_wan=round(cells / 10000, 1),
                   cells_k=round(cells / 1000)),
                lambda: app.update_setting("grid_limit", value), title=tr("warning"), on_no=revert)

    def _choose_color_limit(self, value, revert):
        app = App.get_running_app()
        if value <= 36:
            app.update_setting("color_limit", value)
            return
        confirm(tr("color_warning"), lambda: app.update_setting("color_limit", value),
                title=tr("warning"), on_no=revert)
