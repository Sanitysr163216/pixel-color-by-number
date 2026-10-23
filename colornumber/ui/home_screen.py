"""
首页：图库和我的作品。
"""

from PIL import Image as PILImage

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
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
from colornumber.ui.exporting import export_game, export_kinds

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
                text: app.tr("online_gallery", app.lang)
                size_hint_x: None
                width: "130dp"
                on_release: app.show_online()
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
            # 有隐藏的图时才出现：按下去显示隐藏的图（变淡），可以在菜单里取消隐藏
            Chip:
                id: show_hidden
                text: app.tr("show_hidden", app.lang, count=root.hidden_count)
                size_hint_x: None
                width: "150dp"
                opacity: 1 if (root.hidden_count or root.show_hidden) else 0
                disabled: not (root.hidden_count or root.show_hidden)
                on_state: root.show_hidden = self.state == "down"
            Widget:
            # 右边：图库显示分类，我的作品显示筛选（两组叠在同一个位置，只显示一组）
            FloatLayout:
                size_hint_x: None
                width: "440dp"
                BoxLayout:
                    pos: self.parent.pos
                    spacing: "6dp"
                    opacity: 1 if root.tab == "library" else 0
                    disabled: root.tab != "library"
                    Chip:
                        text: app.tr("category_all", app.lang)
                        group: "home_category"
                        state: "down"
                        on_state: if self.state == "down": root.category = "all"
                    Chip:
                        text: app.tr("category_animals", app.lang)
                        group: "home_category"
                        on_state: if self.state == "down": root.category = "animals"
                    Chip:
                        text: app.tr("category_food", app.lang)
                        group: "home_category"
                        on_state: if self.state == "down": root.category = "food"
                    Chip:
                        text: app.tr("category_nature", app.lang)
                        group: "home_category"
                        on_state: if self.state == "down": root.category = "nature"
                    Chip:
                        text: app.tr("category_things", app.lang)
                        group: "home_category"
                        on_state: if self.state == "down": root.category = "things"
                BoxLayout:
                    pos: self.parent.x + dp(110), self.parent.y
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
        BoxLayout:
            size_hint_y: None
            height: "18dp"
            Widget:
                size_hint_x: None
                width: "120dp"
            Label:
                text: app.tr("drop_hint", app.lang)
                color: 0.5, 0.5, 0.55, 1
                font_size: "12sp"
            Label:
                text: "v" + app.version
                color: 0.6, 0.6, 0.64, 1
                font_size: "12sp"
                size_hint_x: None
                width: "120dp"
                text_size: self.size
                halign: "right"
                valign: "middle"
""")


class Card(ButtonBehavior, BoxLayout):
    """作品卡片：缩略图、名字、进度。"""

    def __init__(self, texture, name, status, on_open, on_menu=None, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(6), **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = RoundedRectangle(radius=[dp(14)])
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.image = Image(texture=texture, fit_mode="contain")   # 在线图库：缩略图下载好后再换上
        self.add_widget(self.image)
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
    filter = StringProperty("all")          # 我的作品：全部 / 进行中 / 已完成
    category = StringProperty("all")        # 图库：全部 / 动物 / 美食 / 自然 / 物品
    show_hidden = BooleanProperty(False)    # 是否也显示隐藏起来的图
    hidden_count = NumericProperty(0)       # 当前页里隐藏了几张图

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._library_previews = {}
        self.bind(tab=self.refresh, filter=self.refresh, category=self.refresh, show_hidden=self.refresh)
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
        keys = library.keys_in(self.category)
        self.hidden_count = sum(1 for key in keys if app.is_hidden(f"library:{key}"))
        for key in keys:
            source = f"library:{key}"
            hidden = app.is_hidden(source)
            if hidden and not self.show_hidden:
                continue
            meta = app.store.find_by_source(source)
            if meta is not None:
                texture = _thumbnail_texture(app.store.thumbnail_path(meta["id"]))
            else:
                texture = self._library_preview(key)
            card = Card(texture, tr(f"library_{key}"), _status_text(meta),
                        on_open=lambda k=key: app.open_library(k),
                        on_menu=lambda k=key: self._show_library_menu(k))
            card.opacity = 0.5 if hidden else 1          # 隐藏的图显示出来时变淡
            grid.add_widget(card)

    def _show_library_menu(self, key):
        app = App.get_running_app()
        source = f"library:{key}"
        Dialog("", [
            (tr("open_picture"), lambda: app.open_library(key), "primary"),
            self._hide_button(source),
            (tr("cancel"), None, "normal"),
        ], title=tr(f"library_{key}")).open()

    def _hide_button(self, key):
        """菜单里的"隐藏 / 取消隐藏"按钮。"""
        app = App.get_running_app()
        if app.is_hidden(key):
            return (tr("unhide"), lambda: self._set_hidden(key, False), "normal")
        return (tr("hide"), lambda: self._set_hidden(key, True), "normal")

    def _set_hidden(self, key, hidden):
        App.get_running_app().set_hidden(key, hidden)
        self.refresh()

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
        self.hidden_count = sum(1 for meta in metas if app.is_hidden(f"project:{meta['id']}"))
        if not self.show_hidden:
            metas = [meta for meta in metas if not app.is_hidden(f"project:{meta['id']}")]
        if not metas:
            label = Label(text=tr("no_works"), color=TEXT_LIGHT, font_size="15sp")
            grid.add_widget(label)
            return
        for meta in metas:
            texture = _thumbnail_texture(app.store.thumbnail_path(meta["id"]))
            card = Card(texture, app.project_name(meta), _status_text(meta),
                        on_open=lambda m=meta: app.open_project(m["id"]),
                        on_menu=lambda m=meta: self._show_menu(m))
            card.opacity = 0.5 if app.is_hidden(f"project:{meta['id']}") else 1
            grid.add_widget(card)

    def _show_menu(self, meta):
        app = App.get_running_app()
        name = app.project_name(meta)
        buttons = [(tr("continue"), lambda: app.open_project(meta["id"]), "primary")]
        if meta["completed"]:
            for kind in export_kinds():
                buttons.append((tr(f"export_{kind}"),
                                lambda k=kind: self._export(meta, k), "normal", False))
        buttons += [
            (tr("rename"), lambda: self._rename(meta), "normal"),
            self._hide_button(f"project:{meta['id']}"),
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
        export_game(game, app.project_name(meta), kind)

    def _rename(self, meta):
        field = TextInput(text=App.get_running_app().project_name(meta), multiline=False, font_size="16sp",
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
        app = App.get_running_app()
        app.store.delete(meta["id"])
        app.set_hidden(f"project:{meta['id']}", False)   # 删掉的作品也不用再记着隐藏了
        self.refresh()
