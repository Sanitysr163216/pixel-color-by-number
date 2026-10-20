"""
播放音效和背景音乐。

背景音乐是一个随机顺序的歌单：一首放完自动放下一首。曲子有三个来源：
- "featured"：精选音乐（assets/music，网上挑选的免费音乐）
- "synth"：内置的合成音乐（core/audio.py）
- "mine"：玩家自己导入的音乐（core/music.py）
设置里的"曲库"决定从哪些来源里选。

填色的"啵"声有 8 个音高，拖动时依次往上走，像在弹琴。
"""

import random
import time

from kivy.core.audio import SoundLoader

POP_MIN_INTERVAL = 0.045   # 拖动时"啵"声最快 0.045 秒一次，避免太吵


class SoundManager:
    def __init__(self, settings):
        self.settings = settings
        self._effects = {}
        self._pops = []
        self._pop_index = 0
        self._last_pop = 0.0
        self._tracks = {}              # 曲子的键 → {"path", "source", "title", "title_key"}
        self._order = []
        self._music = None             # 正在播放的 Sound
        self.current_track = None      # 正在播放的曲子的键
        self._switching = False        # 我们自己停止音乐时，不要自动跳下一首
        self.on_track_change = None    # 换歌时通知界面

    # ------------------------------------------------------------------
    # 音效
    # ------------------------------------------------------------------

    def load_effects(self, paths):
        """paths 来自 core/audio.py 的 ensure_effects。"""
        self._pops = [sound for sound in (SoundLoader.load(p) for p in paths["pop"]) if sound]
        for name in ("wrong", "color_done", "complete"):
            sound = SoundLoader.load(paths[name])
            if sound is not None:
                self._effects[name] = sound
        self.update_volumes()

    def start_stroke(self):
        """新的一笔开始：从低音区随机选一个起点。"""
        self._pop_index = random.randint(0, 3)

    def pop(self):
        """填对一格的声音。"""
        if not self.settings.sound or not self._pops:
            return
        now = time.monotonic()
        if now - self._last_pop < POP_MIN_INTERVAL:
            return
        self._last_pop = now
        sound = self._pops[self._pop_index % len(self._pops)]
        self._pop_index += 1
        sound.stop()
        sound.play()

    def play(self, name):
        """播放 "wrong"、"color_done"、"complete" 这几个音效。"""
        if not self.settings.sound or name not in self._effects:
            return
        sound = self._effects[name]
        sound.stop()
        sound.play()

    # ------------------------------------------------------------------
    # 曲库
    # ------------------------------------------------------------------

    def add_track(self, key, path, source, title=None, title_key=None):
        """加入一首曲子。如果现在没有音乐在放，就从它开始放。"""
        self._tracks[key] = {"path": path, "source": source, "title": title, "title_key": title_key}
        if self._music is None:
            self.update_music()

    def remove_track(self, key):
        self._tracks.pop(key, None)
        self._order = [name for name in self._order if name != key]
        if self.current_track == key:
            self._stop_music()
            self.current_track = None
            self.update_music()

    def track_info(self, key):
        return self._tracks.get(key)

    def _eligible(self):
        """按设置里的"曲库"筛选可以播放的曲子。"""
        source = getattr(self.settings, "music_source", "all")
        return [key for key, info in self._tracks.items() if source == "all" or info["source"] == source]

    def source_changed(self):
        """换了曲库：正在放的曲子不在新的曲库里，就换一首。"""
        self._order = []
        if self.current_track not in self._eligible():
            self._stop_music()
            self.current_track = None
            if self.on_track_change:
                self.on_track_change(None)
            self.update_music()

    # ------------------------------------------------------------------
    # 播放
    # ------------------------------------------------------------------

    def _next_name(self):
        eligible = self._eligible()
        if not eligible:
            return None
        self._order = [key for key in self._order if key in eligible]
        if not self._order:
            self._order = eligible[:]
            random.shuffle(self._order)
            if len(self._order) > 1 and self._order[0] == self.current_track:
                self._order.append(self._order.pop(0))   # 避免同一首连放两次
        return self._order.pop(0)

    def _stop_music(self):
        if self._music is not None:
            self._switching = True
            self._music.stop()
            self._music.unload()
            self._switching = False
            self._music = None

    def _play_next(self):
        self._stop_music()
        key = self._next_name()
        if key is None:
            return
        sound = SoundLoader.load(self._tracks[key]["path"])
        if sound is None:
            self._tracks.pop(key, None)                 # 打不开的文件从歌单里去掉
            return
        sound.volume = self.settings.music_volume
        sound.bind(on_stop=self._on_music_stop)
        self._music = sound
        self.current_track = key
        sound.play()
        if self.on_track_change:
            self.on_track_change(key)

    def _on_music_stop(self, _sound):
        # 放完了（不是我们自己停的）就接着放下一首
        if not self._switching and self.settings.music:
            self._play_next()

    def next_track(self):
        """换下一首。"""
        if self.settings.music:
            self._play_next()

    def update_music(self):
        """按设置开关背景音乐。"""
        if self.settings.music:
            if self._music is None:
                self._play_next()
        else:
            self._stop_music()

    def update_volumes(self):
        for sound in list(self._effects.values()) + self._pops:
            sound.volume = self.settings.sound_volume
        if self._music is not None:
            self._music.volume = self.settings.music_volume
