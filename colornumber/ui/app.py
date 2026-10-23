"""
程序的主体：管理各个页面、设置、存档和声音。
"""

import threading
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.screenmanager import FadeTransition, ScreenManager

from colornumber import __version__
from colornumber.core import library
from colornumber.core import audio
from colornumber.core.music import MusicLibrary, featured_tracks
from colornumber.core.i18n import project_name
from colornumber.core.i18n import tr as translate
from colornumber.core.settings import Settings
from colornumber.core.storage import ProjectStore
from colornumber.ui import window_fix
from colornumber.ui.common import BACKGROUND, register_chinese_font
from colornumber.ui.sound import SoundManager


class ColorNumberApp(App):
    version = __version__                # 版本号，界面上显示用
    title = "Color Number"
    # 窗口标题栏和任务栏上的小图标（不设置的话 Windows 上会显示 Kivy 的图标）
    icon = str(Path(__file__).resolve().parent.parent / "assets" / "icon.png")
    lang = StringProperty("en")                  # 当前语言，界面文字会跟着它变
    settings_grid_limit = NumericProperty(128)   # 导入时格子数滑块的上限
    settings_color_limit = NumericProperty(36)   # 导入时颜色数滑块的上限

    def tr(self, key, _lang=None, **values):
        """
        取界面文字。KV 里写 app.tr("back", app.lang)：
        第二个参数没有用到，但写上 app.lang 后，换语言时文字会自动刷新。
        """
        return translate(key, self.lang, **values)

    def build(self):
        register_chinese_font()
        Window.clearcolor = BACKGROUND
        data = Path(self.user_data_dir)
        self.settings_path = data / "settings.json"
        self.settings = Settings.load(self.settings_path)
        self.lang = self.settings.language
        self.settings_grid_limit = self.settings.grid_limit
        self.settings_color_limit = self.settings.color_limit
        self.store = ProjectStore(data / "projects")
        self.sounds = SoundManager(self.settings)
        self.music_library = MusicLibrary(data / "music")
        for track in featured_tracks():
            self.sounds.add_track(f"featured:{Path(track['file']).name}", track["file"], "featured",
                                  title=track["title"])
        for track in self.music_library.tracks():
            self.sounds.add_track(f"mine:{track['id']}", track["file"], "mine", title=track["name"])
        self._prepare_sounds(data)

        # 这些页面要用到 app.tr 等属性，所以在这里才 import
        from colornumber.ui.game_screen import GameScreen
        from colornumber.ui.home_screen import HomeScreen
        from colornumber.ui.import_screen import ImportScreen
        from colornumber.ui.settings_screen import SettingsScreen
        from colornumber.ui.online_screen import OnlineScreen

        self.screens = ScreenManager(transition=FadeTransition(duration=0.15))
        self.screens.add_widget(HomeScreen(name="home"))
        self.screens.add_widget(GameScreen(name="game"))
        self.screens.add_widget(ImportScreen(name="import"))
        self.screens.add_widget(SettingsScreen(name="settings"))
        self.screens.add_widget(OnlineScreen(name="online"))
        Window.bind(on_drop_file=self._on_drop_file)
        return self.screens

    def _prepare_sounds(self, folder):
        """
        第一次运行时合成声音要十几秒，放到后台做：先做音效，再一首一首做音乐，
        每做好一样就交给 SoundManager，不用等全部做完。
        """
        def work():
            audio.remove_old_sounds(folder)
            effects = audio.ensure_effects(folder)
            Clock.schedule_once(lambda _dt: self.sounds.load_effects(effects))
            for track in audio.MUSIC_TRACKS:
                path = audio.ensure_music(folder, track)
                Clock.schedule_once(lambda _dt, n=track.name, p=path: self.sounds.add_track(
                    f"synth:{n}", p, "synth", title_key=f"music_{n}"))
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------------
    # 切换页面
    # ------------------------------------------------------------------

    def show_home(self, works=False):
        self.screens.current = "home"
        if works:
            self.screens.get_screen("home").show_works()

    def show_online(self):
        self.screens.current = "online"

    def show_settings(self):
        self.screens.current = "settings"

    def open_project(self, project_id):
        meta, game = self.store.load(project_id, self.settings.wrong_mode)
        self.screens.get_screen("game").open_project(meta, game)
        self.screens.current = "game"

    def open_library(self, key):
        """打开内置图：已经开始填过就接着填，否则新建一个作品。"""
        source = f"library:{key}"
        meta = self.store.find_by_source(source)
        if meta is None:
            meta = self.store.create(library.load(key), self.tr(f"library_{key}"), source)
        self.open_project(meta["id"])

    def open_import(self, path=None, name=None, came_from="home"):
        """
        打开导入页面。name 是作品的默认名字（不给就用文件名），
        came_from 是在导入页面点"返回"时回到哪一页。
        """
        from colornumber.ui.import_screen import pick_photo

        if path is None:
            pick_photo(self.open_import)
            return
        screen = self.screens.get_screen("import")
        if screen.load_photo(path):
            if name:
                screen.ids.name.text = name
            self._import_came_from = came_from
            self.screens.current = "import"

    def leave_import(self):
        """导入页面的"返回"：回到打开它的那一页。"""
        self.screens.current = getattr(self, "_import_came_from", "home")

    def _on_drop_file(self, _window, path, *_):
        if self.screens.current in ("home", "import"):
            if isinstance(path, bytes):
                path = path.decode("utf-8")
            self.open_import(path)

    # ------------------------------------------------------------------
    # 设置
    # ------------------------------------------------------------------

    def update_setting(self, name, value):
        setattr(self.settings, name, value)
        self.settings.save(self.settings_path)
        self.settings_grid_limit = self.settings.grid_limit
        self.settings_color_limit = self.settings.color_limit
        if name == "music":
            self.sounds.update_music()
            if self.sounds.on_track_change:
                self.sounds.on_track_change(self.sounds.current_track if value else None)
        if name in ("music_volume", "sound_volume"):
            self.sounds.update_volumes()
        if name == "music_source":
            self.sounds.source_changed()

    def is_hidden(self, key):
        """这张图有没有被隐藏。key 是 "library:<键>" 或 "project:<编号>"。"""
        return key in self.settings.hidden

    def set_hidden(self, key, hidden):
        """隐藏或取消隐藏一张图（只是不显示，不会删除）。"""
        keys = [item for item in self.settings.hidden if item != key]
        if hidden:
            keys.append(key)
        self.update_setting("hidden", keys)

    def project_name(self, meta):
        """作品显示的名字（内置图的默认名字会跟着语言变）。"""
        return project_name(meta, self.lang)

    def track_title(self, key):
        """曲子显示的名字。"""
        info = self.sounds.track_info(key) if key else None
        if info is None:
            return ""
        return self.tr(info["title_key"]) if info["title_key"] else info["title"]

    def set_language(self, language):
        self.update_setting("language", language)
        self.lang = language

    # ------------------------------------------------------------------
    # 程序关闭或切到后台时保存
    # ------------------------------------------------------------------

    def _on_global_key(self, _window, key, _scancode, codepoint, modifiers):
        """全局快捷键：Ctrl+Cmd+F 或 F11 进入、退出全屏。"""
        if key == 292 or (codepoint == "f" and "ctrl" in modifiers and "meta" in modifiers):
            window_fix.toggle_fullscreen()
            return True
        return False

    def on_start(self):
        window_fix.install()
        Window.bind(on_key_down=self._on_global_key)
        # Mac 触控板：捏合缩放、双指滑动移动画布（只在填色页面、鼠标在画布上时）
        from colornumber.ui import mac_gestures

        def gesture_target():
            if self.screens.current == "game":
                canvas = self.screens.get_screen("game").canvas_widget
                return canvas if canvas.wants_gesture() else None
            if self.screens.current == "import":
                preview = self.screens.get_screen("import").ids.preview
                return preview if preview.wants_gesture() else None
            return None

        mac_gestures.install(gesture_target)

    def on_stop(self):
        if self.screens.current == "game":
            self.screens.get_screen("game").save()

    def on_pause(self):
        if self.screens.current == "game":
            self.screens.get_screen("game").save()
        return True
