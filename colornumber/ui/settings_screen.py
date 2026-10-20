"""
设置页面：语言、填错模式、格子和颜色上限、声音。
"""

import subprocess
import sys
import threading
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider

from colornumber.core.game import ALLOW_WRONG, BLOCK_WRONG
from colornumber.core.music import AUDIO_TYPES
from colornumber.core.settings import COLOR_LIMIT_CHOICES, GRID_LIMIT_CHOICES
from colornumber.ui.common import BACKGROUND, TEXT, TEXT_LIGHT, Chip, Dialog, RoundButton, confirm, message, tr


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
        version = Label(text=tr("version", version=app.version), color=TEXT_LIGHT, font_size="14sp",
                        size_hint_x=None, width=dp(160), halign="right", valign="middle")
        version.bind(size=lambda widget, value: setattr(widget, "text_size", value))
        header.add_widget(version)
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
        rows.add_widget(self._slider_row("sound_volume", settings.sound_volume))
        rows.add_widget(self._choice_row(
            "music", [(True, tr("on")), (False, tr("off"))], settings.music,
            lambda value, _revert: app.update_setting("music", value)))
        rows.add_widget(self._slider_row("music_volume", settings.music_volume))
        rows.add_widget(self._choice_row(
            "music_source", [("all", tr("source_all")), ("featured", tr("source_featured")),
                             ("synth", tr("source_synth")), ("mine", tr("source_mine"))],
            settings.music_source, lambda value, _revert: app.update_setting("music_source", value)))
        rows.add_widget(self._now_playing_row())
        rows.add_widget(self._my_music_row())
        for track in app.music_library.tracks():
            rows.add_widget(self._my_track_row(track))

        scroll = ScrollView()
        scroll.add_widget(rows)
        root.add_widget(scroll)
        self.add_widget(root)

    def _title(self, key):
        return Label(text=tr(key), color=TEXT, font_size="16sp", size_hint_x=None,
                     width=dp(220), halign="left", valign="middle", text_size=(dp(220), None))

    def _slider_row(self, key, value):
        """音量滑块：拖动时马上生效。"""
        app = App.get_running_app()
        row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        row.add_widget(self._title(key))
        slider = Slider(min=0, max=1, value=value, size_hint_x=None, width=dp(320),
                        cursor_size=(dp(20), dp(20)))
        slider.bind(value=lambda _s, v: app.update_setting(key, round(v, 2)))
        row.add_widget(slider)
        row.add_widget(Label())
        return row

    def _now_playing_row(self):
        """显示正在播放的曲子，可以换下一首。"""
        app = App.get_running_app()
        row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        row.add_widget(Label(size_hint_x=None, width=dp(220)))
        label = Label(color=TEXT, font_size="15sp", halign="left", valign="middle")
        label.bind(size=lambda widget, value: setattr(widget, "text_size", value))

        def show(key=None):
            key = key or app.sounds.current_track
            title = app.track_title(key)
            if not app.settings.music:
                label.text = tr("music_is_off")
            elif title:
                label.text = tr("now_playing", track=title)
            elif app.settings.music_source == "mine" and not app.music_library.tracks():
                label.text = tr("no_my_music")
            else:
                label.text = tr("nothing_playing")

        app.sounds.on_track_change = show
        show()
        button = RoundButton(text=tr("next_track"), size_hint_x=None, width=dp(110))
        button.bind(on_release=lambda _b: app.sounds.next_track())
        row.add_widget(button)
        row.add_widget(label)
        return row

    def _my_music_row(self):
        """"我的音乐"：导入按钮和状态文字。"""
        row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        row.add_widget(self._title("my_music"))
        button = RoundButton(text=tr("import_music"), primary=True, size_hint_x=None, width=dp(150))
        button.bind(on_release=lambda _b: pick_audio(self._import_music))
        row.add_widget(button)
        count = len(App.get_running_app().music_library.tracks())
        self._music_status = Label(text=tr("my_music_count", count=count), color=TEXT, font_size="14sp",
                                   halign="left", valign="middle")
        self._music_status.bind(size=lambda widget, value: setattr(widget, "text_size", value))
        row.add_widget(self._music_status)
        return row

    def _my_track_row(self, track):
        row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        row.add_widget(Label(size_hint_x=None, width=dp(220)))
        name = Label(text=track["name"], color=TEXT, font_size="14sp", halign="left", valign="middle",
                     shorten=True, shorten_from="right")
        name.bind(size=lambda widget, value: setattr(widget, "text_size", value))
        row.add_widget(name)
        delete = RoundButton(text=tr("delete"), size_hint=(None, None), size=(dp(80), dp(32)), font_size="13sp")
        delete.bind(on_release=lambda _b: confirm(tr("confirm_delete_music", name=track["name"]),
                                                  lambda: self._delete_music(track), tr("delete"), danger=True))
        row.add_widget(delete)
        return row

    def _import_music(self, paths):
        """在后台导入（可能要转换格式），导入完刷新页面。"""
        app = App.get_running_app()
        self._music_status.text = tr("importing_music")

        def work():
            added, failed = [], []
            for path in paths:
                try:
                    added.append(app.music_library.add(path))
                except Exception:      # 打不开或转换失败的文件记下来告诉玩家
                    failed.append(Path(path).name)
            Clock.schedule_once(lambda _dt: done(added, failed))

        def done(added, failed):
            for track in added:
                app.sounds.add_track(f"mine:{track['id']}", track["file"], "mine", title=track["name"])
            self.build()
            if failed:
                message(tr("import_music_failed", files="\n".join(failed)))

        threading.Thread(target=work, daemon=True).start()

    def _delete_music(self, track):
        app = App.get_running_app()
        app.sounds.remove_track(f"mine:{track['id']}")
        app.music_library.remove(track["id"])
        self.build()

    def _choice_row(self, title_key, options, current, on_choose):
        """
        一行设置：左边标题，右边几个选项按钮。
        on_choose(value, revert) 在玩家选了新选项时调用；调用 revert() 可以退回原来的选项。
        """
        row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        row.add_widget(self._title(title_key))
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


# ---------------------------------------------------------------------------
# 选择音乐文件：macOS 用系统的选择窗口（可以一次选多首），其他系统用 Kivy 的文件列表
# ---------------------------------------------------------------------------

def pick_audio(on_chosen):
    """让玩家选一首或几首音乐，选好后调用 on_chosen(路径列表)。"""
    if sys.platform == "darwin":
        script = (f'set picked to choose file of type {{"public.audio"}} with prompt "{tr("pick_music_title")}" '
                  'with multiple selections allowed\n'
                  'set output to ""\n'
                  'repeat with chosen in picked\n'
                  '  set output to output & POSIX path of chosen & linefeed\n'
                  'end repeat\n'
                  'return output')

        def work():
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            paths = [line for line in result.stdout.splitlines() if line.strip()]
            if result.returncode == 0 and paths:
                Clock.schedule_once(lambda _dt: on_chosen(paths))

        threading.Thread(target=work, daemon=True).start()
        return

    from kivy.uix.filechooser import FileChooserListView
    chooser = FileChooserListView(path=str(Path.home()), filters=list(AUDIO_TYPES), multiselect=True,
                                  size_hint_y=None, height=dp(360))
    dialog = Dialog("", [
        (tr("cancel"), None, "normal"),
        (tr("ok"), lambda: chooser.selection and on_chosen(list(chooser.selection)), "primary"),
    ], title=tr("pick_music_title"), content=chooser)
    dialog.width = dp(640)
    dialog.open()
