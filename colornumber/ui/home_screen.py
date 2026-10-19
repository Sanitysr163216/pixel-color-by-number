"""
首页：图库和我的作品。
"""

from PIL import Image as PILImage

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput

from colornumber.core import library
from colornumber.core.render import render_state
from colornumber.ui.common import (TEXT, TEXT_LIGHT, Chip, Dialog, RoundButton,  # noqa: F401
                                   confirm, pil_to_texture, tr)
from colornumber.ui.exporting import export_game

CARD_WIDTH = 200

Builder.load_string("""
<HomeScreen>:
    canvas.before:
        Color:
            rgba: 0.97, 0.96, 0.94, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: "18dp"
        spacing: "12dp"
        BoxLayout:
            size_hint_y: None
            height: "48dp"
            spacing: "10dp"
            Label:
                text: app.tr("app_title", app.lang)
                color: 0.2, 0.2, 0.25, 1
                font_size: "24sp"
                bold: True
                text_size: self.size
                halign: "left"
                valign: "middle"
            RoundButton:
                text: app.tr("import_photo", app.lang)
                primary: True
                size_hint_x: None
                width: "130dp"
                on_release: app.open_import()
            RoundButton:
                text: app.tr("settings", app.lang)
                size_hint_x: None
                width: "100dp"
                on_release: app.show_settings()
        BoxLayout:
            size_hint_y: None
            height: "36dp"
            spacing: "8dp"
            Chip:
                id: tab_library
                text: app.tr("library", app.lang)
                group: "home_tab"
                state: "down"
                size_hint_x: None
                width: "110dp"
                on_state: if self.state == "down": root.tab = "library"
            Chip:
                id: tab_works
                text: app.tr("my_works", app.lang)
                group: "home_tab"
                size_hint_x: None
                width: "110dp"
                on_state: if self.state == "down": root.tab = "works"
            Widget:
            BoxLayout:
                size_hint_x: None
                width: "330dp"
                spacing: "6dp"
                opacity: 1 if root.tab == "works" else 0
                disabled: root.tab != "works"
                Chip:
                    text: app.tr("filter_all", app.lang)
                    group: "home_filter"
                    state: "down"
                    on_state: if self.state == "down": root.filter = "all"
                Chip:
                    text: app.tr("filter_in_progress", app.lang)
                    group: "home_filter"
                    on_state: if self.state == "down": root.filter = "in_progress"
                Chip:
                    text: app.tr("filter_completed", app.lang)
                    group: "home_filter"
                    on_state: if self.state == "down": root.filter = "completed"
        ScrollView:
            GridLayout:
                id: grid
                cols: max(1, int(self.width // dp(215)))
                size_hint_y: None
                height: self.minimum_height
                spacing: "14dp"
                padding: "2dp"
                row_default_height: "250dp"
                row_force_default: True
                col_force_default: True
                col_default_width: (self.width - dp(4) - (self.cols - 1) * dp(14)) / self.cols
        Label:
            text: app.tr("drop_hint", app.lang)
            color: 0.5, 0.5, 0.55, 1
            font_size: "12sp"
            size_hint_y: None
            height: "18dp"
""")


class Card(ButtonBehavior, BoxLayout):
    """作品卡片：缩略图、名字、进度。"""

    def __init__(self, texture, name, status, on_open, on_menu=None, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(6), **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = RoundedRectangle(radius=[dp(14)])
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.add_widget(Image(texture=texture, fit_mode="contain"))
        row = BoxLayout(size_hint_y=None, height=dp(44))
        labels = BoxLayout(orientation="vertical")
        for text, color, size in ((name, TEXT, "15sp"), (status, TEXT_LIGHT, "12sp")):
            label = Label(text=text, color=color, font_size=size, halign="left", valign="middle",
                          shorten=True, shorten_from="right")
            label.bind(size=lambda widget, value: setattr(widget, "text_size", value))
            labels.add_widget(label)
        row.add_widget(labels)
        if on_menu is not None:
            menu = RoundButton(text="…", size_hint=(None, None), size=(dp(40), dp(34)))
            menu.bind(on_release=lambda _b: on_menu())
            row.add_widget(menu)
        self.add_widget(row)
        self.bind(on_release=lambda _card: on_open())

    def _update_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


def _status_text(meta):
    if meta is None or meta["progress"] == 0:
        return tr("not_started")
    if meta["completed"]:
        return tr("completed")
    return tr("percent_done", percent=int(meta["progress"] * 100))


def _thumbnail_texture(path):
    with PILImage.open(path) as image:
        return pil_to_texture(image.convert("RGB"))


class HomeScreen(Screen):
    tab = StringProperty("library")
    filter = StringProperty("all")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._library_previews = {}
        self.bind(tab=self.refresh, filter=self.refresh)
        App.get_running_app().bind(lang=self.refresh)

    def on_pre_enter(self, *_):
        self.refresh()

    def show_works(self):
        # 用代码切换时要自己把另一个按钮取消选中
        self.ids.tab_library.state = "normal"
        self.ids.tab_works.state = "down"

    def refresh(self, *_):
        grid = self.ids.grid
        grid.clear_widgets()
        if self.tab == "library":
            self._fill_library(grid)
        else:
            self._fill_works(grid)

    # ------------------------------------------------------------------
    # 图库
    # ------------------------------------------------------------------

    def _library_preview(self, key):
        """还没开始填的内置图：显示灰色轮廓。"""
        if key not in self._library_previews:
            picture = library.load(key)
            cell = max(1, 240 // max(picture.width, picture.height))
            image = render_state(picture, [0] * (picture.width * picture.height), cell)
            self._library_previews[key] = pil_to_texture(image)
        return self._library_previews[key]

    def _fill_library(self, grid):
        app = App.get_running_app()
        for key in library.LIBRARY:
            source = f"library:{key}"
            meta = app.store.find_by_source(source)
            if meta is not None:
                texture = _thumbnail_texture(app.store.thumbnail_path(meta["id"]))
            else:
                texture = self._library_preview(key)
            grid.add_widget(Card(texture, tr(f"library_{key}"), _status_text(meta),
                                 on_open=lambda k=key: app.open_library(k)))

    # ------------------------------------------------------------------
    # 我的作品
    # ------------------------------------------------------------------

    def _fill_works(self, grid):
        app = App.get_running_app()
        metas = app.store.list()
        if self.filter == "in_progress":
            metas = [meta for meta in metas if not meta["completed"]]
        elif self.filter == "completed":
            metas = [meta for meta in metas if meta["completed"]]
        if not metas:
            label = Label(text=tr("no_works"), color=TEXT_LIGHT, font_size="15sp")
            grid.add_widget(label)
            return
        for meta in metas:
            texture = _thumbnail_texture(app.store.thumbnail_path(meta["id"]))
            grid.add_widget(Card(texture, meta["name"], _status_text(meta),
                                 on_open=lambda m=meta: app.open_project(m["id"]),
                                 on_menu=lambda m=meta: self._show_menu(m)))

    def _show_menu(self, meta):
        app = App.get_running_app()
        name = meta["name"]
        buttons = [(tr("continue"), lambda: app.open_project(meta["id"]), "primary")]
        if meta["completed"]:
            for kind in ("png", "gif", "mp4"):
                buttons.append((tr(f"export_{kind}"),
                                lambda k=kind: self._export(meta, k), "normal", False))
        buttons += [
            (tr("rename"), lambda: self._rename(meta), "normal"),
            (tr("restart"), lambda: confirm(tr("confirm_restart", name=name),
                                            lambda: self._restart(meta), tr("restart")), "normal"),
            (tr("delete"), lambda: confirm(tr("confirm_delete", name=name),
                                           lambda: self._delete(meta), tr("delete"), danger=True),
             "danger"),
            (tr("cancel"), None, "normal"),
        ]
        Dialog("", buttons, title=name).open()

    def _export(self, meta, kind):
        app = App.get_running_app()
        _, game = app.store.load(meta["id"], app.settings.wrong_mode)
        export_game(game, meta["name"], kind)

    def _rename(self, meta):
        field = TextInput(text=meta["name"], multiline=False, font_size="16sp",
                          size_hint_y=None, height=dp(42), padding=(dp(10), dp(10)))

        def save():
            name = field.text.strip()
            if name:
                App.get_running_app().store.rename(meta["id"], name)
                self.refresh()

        field.bind(on_text_validate=lambda _f: (dialog.dismiss(), save()))
        dialog = Dialog("", [(tr("cancel"), None, "normal"), (tr("ok"), save, "primary")],
                        title=tr("rename"), content=field)
        dialog.open()
        Clock.schedule_once(lambda _dt: setattr(field, "focus", True), 0.2)

    def _restart(self, meta):
        app = App.get_running_app()
        app.store.restart(meta["id"], app.settings.wrong_mode)
        self.refresh()

    def _delete(self, meta):
        App.get_running_app().store.delete(meta["id"])
        self.refresh()
