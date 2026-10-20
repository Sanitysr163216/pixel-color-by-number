"""
作品的存档：每张图一个文件夹，里面有

    meta.json       名字、来源、创建和修改时间、是否完成
    picture.json    填色图本身（调色板和编号）
    progress.json   填色进度和撤销记录
    thumb.png       缩略图，作品集里显示

所有作品都放在 root 文件夹下面。root 由界面传进来，
这样电脑版和以后的 iPhone 版可以各自决定存在哪里。
"""

import json
import shutil
import time
import uuid
from pathlib import Path

from colornumber.core.game import Game
from colornumber.core.picture import Picture
from colornumber.core.render import render_state

THUMB_LONG_SIDE = 240


def _write_json(path, data):
    # 先写到临时文件再改名，避免写到一半程序关闭导致存档损坏
    temp = path.with_suffix(".tmp")
    with open(temp, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, separators=(",", ":"))
    temp.replace(path)


def _read_json(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


class ProjectStore:
    """管理所有作品的存档。"""

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _folder(self, project_id):
        return self.root / project_id

    def create(self, picture, name, source):
        """
        新建一个作品，返回它的 meta 字典。
        source 记录图从哪里来：内置图库是 "library:<名字>"，导入的照片是 "import"。
        """
        project_id = uuid.uuid4().hex[:12]
        folder = self._folder(project_id)
        folder.mkdir()
        now = time.time()
        meta = {"id": project_id, "name": name, "source": source,
                "created": now, "updated": now, "completed": False, "progress": 0.0}
        _write_json(folder / "picture.json", picture.to_dict())
        game = Game(picture)
        self.save(meta, game)
        return meta

    def save(self, meta, game):
        """保存进度、更新 meta 和缩略图。作品已经被删除时什么都不做。"""
        folder = self._folder(meta["id"])
        if not folder.exists():
            return
        meta["updated"] = time.time()
        meta["completed"] = game.is_complete()
        meta["progress"] = game.progress()
        _write_json(folder / "progress.json", game.to_dict())
        _write_json(folder / "meta.json", meta)
        self._save_thumbnail(folder, game)

    def _save_thumbnail(self, folder, game):
        picture = game.picture
        cell = max(1, THUMB_LONG_SIDE // max(picture.width, picture.height))
        render_state(picture, game.painted, cell).save(folder / "thumb.png")

    def thumbnail_path(self, project_id):
        return str(self._folder(project_id) / "thumb.png")

    def list(self):
        """返回所有作品的 meta，最近修改的在前面。"""
        metas = []
        for folder in self.root.iterdir():
            meta_path = folder / "meta.json"
            if meta_path.exists():
                try:
                    metas.append(_read_json(meta_path))
                except ValueError:
                    continue   # 损坏的存档跳过
        metas.sort(key=lambda meta: meta["updated"], reverse=True)
        return metas

    def find_by_source(self, source):
        """找到来自某个来源的作品（用来判断内置图是否已经开始填）。"""
        for meta in self.list():
            if meta["source"] == source:
                return meta
        return None

    def load(self, project_id, wrong_mode):
        """读取作品，返回 (meta, game)。"""
        folder = self._folder(project_id)
        meta = _read_json(folder / "meta.json")
        picture = Picture.from_dict(_read_json(folder / "picture.json"))
        game = Game.from_dict(picture, _read_json(folder / "progress.json"), wrong_mode)
        return meta, game

    def restart(self, project_id, wrong_mode):
        """清空进度，从头开始。"""
        meta, game = self.load(project_id, wrong_mode)
        game.restart()
        self.save(meta, game)

    def rename(self, project_id, name):
        folder = self._folder(project_id)
        meta = _read_json(folder / "meta.json")
        meta["name"] = name
        _write_json(folder / "meta.json", meta)

    def delete(self, project_id):
        shutil.rmtree(self._folder(project_id), ignore_errors=True)
