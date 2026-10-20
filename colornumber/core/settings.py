"""
游戏设置：保存在一个 JSON 文件里，下次打开程序时读回来。
"""

import json
from dataclasses import asdict, dataclass, fields

from colornumber.core.game import BLOCK_WRONG

GRID_LIMIT_CHOICES = (128, 256, 512)    # 格子长边上限：128 是默认，后两档要解锁
COLOR_LIMIT_CHOICES = (36, 48, 64)      # 颜色上限：36 是默认，后两档要解锁


@dataclass
class Settings:
    language: str = "zh"              # "zh" 中文，"en" 英文
    wrong_mode: str = BLOCK_WRONG     # 填错模式，见 game.py
    grid_limit: int = 128             # 导入照片时格子长边最多多少
    color_limit: int = 36             # 导入照片时颜色最多多少种
    sound: bool = True                # 音效
    music: bool = True                # 背景音乐
    sound_volume: float = 0.8         # 音效音量 0–1
    music_volume: float = 0.5         # 背景音乐音量 0–1
    music_source: str = "all"         # 曲库："all" 全部、"featured" 精选、"synth" 合成、"mine" 我的音乐
    convert_style: str = "smooth"     # 导入照片的风格："smooth" 平滑、"clear" 清晰、"classic" 经典
    ai_assist: bool = True            # 导入照片时用 AI 识别人脸和主体（只在 macOS 上有）

    def save(self, path):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(asdict(self), file, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        """读取设置；文件不存在或损坏时用默认设置。"""
        try:
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, ValueError):
            return cls()
        known = {field.name for field in fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in known})
