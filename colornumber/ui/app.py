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

from colornumber.core import library
from colornumber.core.audio import ensure_sounds
from colornumber.core.i18n import tr as translate
from colornumber.core.settings import Settings
from colornumber.core.storage import ProjectStore
from colornumber.ui.common import BACKGROUND, register_chinese_font
from colornumber.ui.sound import SoundManager


class ColorNumberApp(App):
    title = "Color Number"
    lang = StringProperty("zh")                  # 当前语言，界面文字会跟着它变
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
        self._prepare_sounds(data / "sounds")

        # 这些页面要用到 app.tr 等属性，所以在这里才 import
        from colornumber.ui.game_screen import GameScreen
        from colornumber.ui.home_screen import HomeScreen
        from colornumber.ui.import_screen import ImportScreen
        from colornumber.ui.settings_screen import SettingsScreen

        self.screens = ScreenManager(transition=FadeTransition(duration=0.15))
        self.screens.add_widget(HomeScreen(name="home"))
        self.screens.add_widget(GameScreen(name="game"))
        self.screens.add_widget(ImportScreen(name="import"))
        self.screens.add_widget(SettingsScreen(name="settings"))
        Window.bind(on_drop_file=self._on_drop_file)
        return self.screens

    def _prepare_sounds(self, folder):
        """第一次运行时合成声音要几秒钟，放到后台做，做完再加载。"""
        def work():
            paths = ensure_sounds(folder)
            Clock.schedule_once(lambda _dt: self.sounds.load(paths))
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------------
    # 切换页面
    # ------------------------------------------------------------------

    def show_home(self, works=False):
        self.screens.current = "home"
        if works:
            self.screens.get_screen("home").show_works()

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

    def open_import(self, path=None):
        from colornumber.ui.import_screen import pick_photo

        if path is None:
            pick_photo(self.open_import)
            return
        if self.screens.get_screen("import").load_photo(path):
            self.screens.current = "import"

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

    def set_language(self, language):
        self.update_setting("language", language)
        self.lang = language

    # ------------------------------------------------------------------
    # 程序关闭或切到后台时保存
    # ------------------------------------------------------------------

    def on_stop(self):
        self.screens.get_screen("game").save()

    def on_pause(self):
        self.screens.get_screen("game").save()
        return True
