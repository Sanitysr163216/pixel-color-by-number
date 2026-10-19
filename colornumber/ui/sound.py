"""
播放音效和背景音乐。声音文件由 core/audio.py 合成。
"""

import time

from kivy.core.audio import SoundLoader

POP_MIN_INTERVAL = 0.05   # 拖动时"啵"声最快每 0.05 秒一次，避免太吵


class SoundManager:
    def __init__(self, settings):
        self.settings = settings
        self._sounds = {}
        self._last_pop = 0.0

    def load(self, paths):
        """加载声音文件。paths 是 {名字: 文件路径}，由 core/audio.py 的 ensure_sounds 生成。"""
        for name, path in paths.items():
            sound = SoundLoader.load(path)
            if sound is not None:
                self._sounds[name] = sound
        music = self._sounds.get("music")
        if music is not None:
            music.loop = True
            music.volume = 0.35
        if "pop" in self._sounds:
            self._sounds["pop"].volume = 0.5
        self.update_music()

    def play(self, name):
        if not self.settings.sound or name not in self._sounds:
            return
        if name == "pop":
            now = time.monotonic()
            if now - self._last_pop < POP_MIN_INTERVAL:
                return
            self._last_pop = now
        sound = self._sounds[name]
        sound.stop()
        sound.play()

    def update_music(self):
        """按设置开关背景音乐。"""
        music = self._sounds.get("music")
        if music is None:
            return
        if self.settings.music and music.state != "play":
            music.play()
        elif not self.settings.music and music.state == "play":
            music.stop()
