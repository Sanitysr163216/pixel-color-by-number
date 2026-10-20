"""
背景音乐的曲库：
- 内置合成音乐：core/audio.py 用代码生成
- 精选音乐：colornumber/assets/music 里的免费音乐（作者和许可证见 credits.json）
- 我的音乐：玩家自己导入的音乐，保存在数据文件夹的 music/ 里

游戏能直接播放 OGG、MP3、FLAC、WAV；其他格式（比如 iPhone 的 M4A）
导入时用 ffmpeg 转成 OGG。
"""

import json
import shutil
import subprocess
import uuid
from pathlib import Path

PLAYABLE = {".ogg", ".mp3", ".flac", ".wav"}
AUDIO_TYPES = ("*.mp3", "*.ogg", "*.flac", "*.wav", "*.m4a", "*.aac", "*.aiff", "*.aif", "*.opus", "*.wma")
FEATURED_FOLDER = Path(__file__).resolve().parent.parent / "assets" / "music"


def featured_tracks():
    """精选音乐：返回 [{"file": 路径, "title": 名字, "author": 作者, ...}]。"""
    credits = FEATURED_FOLDER / "credits.json"
    if not credits.exists():
        return []
    with open(credits, encoding="utf-8") as file:
        entries = json.load(file)
    tracks = []
    for entry in entries:
        path = FEATURED_FOLDER / entry["file"]
        if path.exists():
            tracks.append({**entry, "file": str(path)})
    return tracks


def _ffmpeg():
    """找到 ffmpeg：优先用 imageio-ffmpeg 自带的，没有就找系统里的。"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


class MusicLibrary:
    """玩家自己导入的音乐。"""

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._index = self.root / "music.json"

    def tracks(self):
        """返回 [{"id": ..., "name": ..., "file": 完整路径}]，按导入顺序。"""
        try:
            with open(self._index, encoding="utf-8") as file:
                entries = json.load(file)
        except (OSError, ValueError):
            return []
        return [{**entry, "file": str(self.root / entry["file"])}
                for entry in entries if (self.root / entry["file"]).exists()]

    def _save(self, entries):
        stored = [{**entry, "file": Path(entry["file"]).name} for entry in entries]
        with open(self._index, "w", encoding="utf-8") as file:
            json.dump(stored, file, ensure_ascii=False, indent=2)

    def add(self, path):
        """导入一首音乐，返回它的信息。格式不支持又转换失败时抛出 ValueError。"""
        source = Path(path)
        track_id = uuid.uuid4().hex[:10]
        suffix = source.suffix.lower()
        if suffix in PLAYABLE:
            target = self.root / f"{track_id}{suffix}"
            shutil.copyfile(source, target)
        else:
            ffmpeg = _ffmpeg()
            if ffmpeg is None:
                raise ValueError(f"unsupported format: {suffix}")
            target = self.root / f"{track_id}.ogg"
            result = subprocess.run(
                [ffmpeg, "-y", "-loglevel", "error", "-i", str(source), "-vn",
                 "-c:a", "libvorbis", "-q:a", "5", str(target)],
                capture_output=True, text=True)
            if result.returncode != 0 or not target.exists():
                target.unlink(missing_ok=True)
                raise ValueError(result.stderr.strip() or f"cannot convert {suffix}")
        entry = {"id": track_id, "name": source.stem, "file": str(target)}
        self._save(self.tracks() + [entry])
        return entry

    def remove(self, track_id):
        entries = self.tracks()
        for entry in entries:
            if entry["id"] == track_id:
                Path(entry["file"]).unlink(missing_ok=True)
        self._save([entry for entry in entries if entry["id"] != track_id])
