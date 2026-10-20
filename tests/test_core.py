"""
游戏逻辑的自动测试。运行方法：在项目文件夹里执行

    pytest
"""

from pathlib import Path

import numpy as np
from PIL import Image

from colornumber.core import audio, converter, export, library
from colornumber.core.game import ALLOW_WRONG, BLOCK_WRONG, Game, cells_on_line
from colornumber.core.picture import Picture
from colornumber.core.settings import Settings
from colornumber.core.storage import ProjectStore

RED, BLUE, GREEN = (255, 0, 0), (0, 0, 255), (0, 255, 0)


def small_picture():
    #  1 1 2
    #  2 1 2
    #  3 3 1
    return Picture(palette=[RED, BLUE, GREEN], numbers=[[1, 1, 2], [2, 1, 2], [3, 3, 1]])


def test_picture_round_trip():
    picture = small_picture()
    again = Picture.from_dict(picture.to_dict())
    assert again == picture
    assert (picture.width, picture.height, picture.color_count) == (3, 3, 3)


def test_paint_blocks_wrong_color():
    game = Game(small_picture(), wrong_mode=BLOCK_WRONG)
    assert game.remaining_count(1) == 4
    assert not game.paint(0, 2)          # 0 号格应该是 1 号
    assert game.paint(0, 1)
    assert game.remaining_count(1) == 3
    assert not game.paint(0, 1)          # 已经填对，不重复


def test_paint_allows_wrong_color_and_fix():
    game = Game(small_picture(), wrong_mode=ALLOW_WRONG)
    assert game.paint(0, 2)
    assert game.is_wrong(0)
    assert game.remaining_count(1) == 4
    assert game.paint(0, 1)
    assert game.is_correct(0)
    assert game.remaining_count(1) == 3


def test_stroke_and_undo():
    game = Game(small_picture())
    game.begin_stroke()
    game.paint(0, 1)
    game.paint(1, 1)
    game.end_stroke()
    game.begin_stroke()
    game.paint(2, 2)
    game.end_stroke()
    assert len(game.history) == 2
    assert sorted(game.undo()) == [2]
    assert game.painted[2] == 0
    assert sorted(game.undo()) == [0, 1]
    assert game.painted == [0] * 9
    assert game.undo() == []
    assert game.remaining_count(1) == 4


def test_empty_stroke_is_not_recorded():
    game = Game(small_picture())
    game.begin_stroke()
    game.paint(0, 3)                     # 被阻止，没有改动
    game.end_stroke()
    assert game.history == []


def test_magic_wand_fills_connected_region_only():
    game = Game(small_picture())
    changed = game.magic_wand(0, 1)      # 1 号区域：(0,0) (0,1) (1,1) 相连，(2,2) 不相连
    assert sorted(changed) == [0, 1, 4]
    assert game.remaining_count(1) == 1
    assert game.magic_wand(2, 1) == []   # 点的格子不是 1 号


def test_bucket_and_completion():
    game = Game(small_picture())
    for number in (1, 2, 3):
        game.bucket(number)
    assert game.is_complete()
    assert game.progress() == 1.0
    game.undo()
    assert not game.is_complete()


def test_next_unfinished_and_hint():
    game = Game(small_picture())
    game.bucket(2)
    assert game.next_unfinished_number(1) == 3
    assert game.next_unfinished_number(3) == 1
    assert game.find_hint(1, 2, 2) == 8  # 离 (2,2) 最近的 1 号格就是它自己
    assert game.find_hint(2, 0, 0) in (0, 1, 4, 6, 7, 8)   # 2 号填完，退而找其他


def test_replay_frames():
    game = Game(small_picture())
    for number in (1, 2, 3):
        game.bucket(number)
    frames = game.replay_frames(5)
    assert frames[0] == [0] * 9
    assert frames[-1] == game.painted
    assert len(frames) == 5


def test_cells_on_line():
    assert cells_on_line(0, 0, 0, 3) == [(0, 0), (0, 1), (0, 2), (0, 3)]
    line = cells_on_line(0, 0, 3, 3)
    assert line[0] == (0, 0) and line[-1] == (3, 3)
    assert len(cells_on_line(2, 2, 2, 2)) == 1


def test_converter_limits_colors_and_size():
    image = Image.new("RGB", (200, 100))
    for x in range(200):
        for y in range(100):
            image.putpixel((x, y), (x, y * 2, 128))
    picture = converter.convert(image, grid_size=32, color_count=8)
    assert picture.width == 32 and picture.height == 16
    assert picture.color_count <= 8
    used = set(picture.flat_numbers())
    assert used == set(range(1, picture.color_count + 1))


def test_classic_mode():
    image = Image.new("RGB", (200, 100))
    image.putdata([(x, y * 2, 128) for y in range(100) for x in range(200)])
    picture = converter.convert(image, grid_size=32, color_count=8, style="classic")
    assert (picture.width, picture.height) == (32, 16)
    assert picture.color_count <= 8
    assert set(picture.flat_numbers()) == set(range(1, picture.color_count + 1))


def test_fidelity():
    image = Image.new("RGB", (64, 64))
    image.putdata([(x * 4, y * 4, 128) for y in range(64) for x in range(64)])
    many = converter.fidelity(image, converter.convert(image, grid_size=16, color_count=32))
    few = converter.fidelity(image, converter.convert(image, grid_size=16, color_count=4))
    changed = converter.fidelity(image, converter.convert(image, grid_size=16, color_count=32, saturation=0.0))
    assert 0 <= few < many <= 100
    assert changed < many                       # 调整越多，还原度越低


def test_converter_crop():
    image = Image.new("RGB", (100, 100), "white")
    picture = converter.convert(image, grid_size=20, color_count=4, crop=(0, 0, 100, 50))
    assert (picture.width, picture.height) == (20, 10)


def test_library_pictures_are_valid():
    for key in library.LIBRARY:
        picture = library.load(key)
        widths = {len(row) for row in picture.numbers}
        assert len(widths) == 1, key
        assert set(picture.flat_numbers()) == set(range(1, picture.color_count + 1)), key


def test_storage_round_trip(tmp_path):
    store = ProjectStore(tmp_path)
    meta = store.create(small_picture(), "测试", "import")
    _, game = store.load(meta["id"], BLOCK_WRONG)
    game.bucket(1)
    store.save(meta, game)
    _, again = store.load(meta["id"], BLOCK_WRONG)
    assert again.painted == game.painted
    assert again.history == game.history
    assert store.list()[0]["progress"] > 0
    store.restart(meta["id"], BLOCK_WRONG)
    _, fresh = store.load(meta["id"], BLOCK_WRONG)
    assert fresh.painted == [0] * 9 and fresh.history == []
    store.delete(meta["id"])
    assert store.list() == []


def test_settings_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    assert Settings.load(path) == Settings()
    Settings(language="en", grid_limit=512).save(path)
    loaded = Settings.load(path)
    assert loaded.language == "en" and loaded.grid_limit == 512


def test_exports(tmp_path):
    game = Game(library.load("mushroom"))
    for number in range(1, game.picture.color_count + 1):
        game.bucket(number)
    export.export_png(game, tmp_path / "a.png")
    export.export_gif(game, tmp_path / "a.gif")
    export.export_mp4(game, tmp_path / "a.mp4")
    for name in ("a.png", "a.gif", "a.mp4"):
        assert (tmp_path / name).stat().st_size > 1000


def test_sound_effects(tmp_path):
    paths = audio.ensure_effects(tmp_path)
    assert len(paths["pop"]) == len(audio.POP_NOTES)
    for name in ("wrong", "color_done", "complete"):
        assert Path(paths[name]).stat().st_size > 1000


def test_music_track(tmp_path):
    track = audio.MUSIC_TRACKS[0]
    path = audio.ensure_music(tmp_path, track)
    import wave
    with wave.open(path) as file:
        seconds = file.getnframes() / file.getframerate()
    assert 40 < seconds < 150


def test_redo():
    game = Game(small_picture())
    game.bucket(1)
    painted = game.painted[:]
    game.undo()
    assert game.redo() and game.painted == painted
    assert game.redo() == []
    game.undo()
    game.paint(2, 2)          # 不在一笔里（没有 begin_stroke），不记录
    game.bucket(3)            # 新的一笔会清空重做
    assert game.redo() == []


def test_fill_all_in_one_stroke():
    game = Game(small_picture())
    game.paint(0, 1)
    game.begin_stroke()
    for number in (1, 2, 3):
        game.fill_number(number)
    game.end_stroke()
    assert game.is_complete()
    game.undo()                       # 一次撤销全部撤回（开始前不在笔画里填的那格不算）
    assert game.total_remaining() == 8


def test_lab_round_trip():
    colors = np.array([[255, 0, 0], [12, 200, 90], [255, 255, 255], [0, 0, 0]])
    assert np.abs(converter.lab_to_rgb(converter.rgb_to_lab(colors)).astype(int) - colors).max() <= 1


def test_similar_color_pairs():
    assert converter.similar_color_pairs([(255, 0, 0), (250, 5, 5), (0, 0, 255)]) == 1
    assert converter.similar_color_pairs([(255, 0, 0), (0, 0, 255)]) == 0


def test_clean_keeps_contrasting_detail():
    # 一大片皮肤色里有一个黑点（像瞳孔）和一个几乎同色的点（像噪点）
    image = Image.new("RGB", (160, 160), (235, 190, 160))
    for x in range(70, 80):
        for y in range(70, 80):
            image.putpixel((x, y), (20, 15, 15))
    for x in range(20, 30):
        for y in range(20, 30):
            image.putpixel((x, y), (222, 178, 150))
    picture = converter.convert(image, grid_size=16, color_count=4, style="clear")
    numbers = picture.numbers
    assert numbers[7][7] != numbers[0][0]          # 清晰风格：黑点保留
    assert numbers[2][2] == numbers[0][0]          # 低对比的点被清理


def test_smooth_style_rounds_off_spikes():
    # 一块方形色块，右边伸出一个单格的尖角
    image = Image.new("RGB", (160, 160), (240, 240, 240))
    for x in range(40, 120):
        for y in range(40, 120):
            image.putpixel((x, y), (40, 90, 200))
    for x in range(120, 130):
        for y in range(70, 80):
            image.putpixel((x, y), (40, 90, 200))
    smooth = converter.convert(image, grid_size=16, color_count=4, style="smooth")
    clear = converter.convert(image, grid_size=16, color_count=4, style="clear", clean=False)
    assert clear.numbers[7][12] != clear.numbers[0][0]       # 清晰风格保留尖角
    assert smooth.numbers[7][12] == smooth.numbers[0][0]     # 平滑风格把尖角抹平
    assert smooth.numbers[7][7] != smooth.numbers[0][0]      # 色块本身还在


def test_recommend_color_count_for_simple_art():
    picture = library.load("mushroom")
    image = Image.new("RGB", (picture.width, picture.height))
    image.putdata([picture.color_of(n) for n in picture.flat_numbers()])
    image = image.resize((picture.width * 20, picture.height * 20), Image.Resampling.NEAREST)
    count = converter.recommend_color_count(image, grid_size=32, max_colors=36)
    assert 6 <= count <= 10                        # 这张图本来就是 8 种颜色


def test_detail_and_importance_options():
    image = Image.new("RGB", (120, 80))
    image.putdata([(x * 2, y * 3, 100) for y in range(80) for x in range(120)])
    importance = np.zeros((80, 120))
    importance[20:60, 30:90] = 1
    subject = np.zeros((80, 120))
    subject[10:70, 20:100] = 1
    for detail in (0.0, 1.0):
        picture = converter.convert(image, grid_size=30, color_count=8, detail=detail,
                                    importance=importance, subject=subject, simplify_background=True,
                                    crop=(10, 0, 110, 80))
        assert (picture.width, picture.height) == (30, 24)


def test_trackpad_event_handling():
    from colornumber.ui import mac_gestures
    if not mac_gestures.available():
        return
    import AppKit

    class FakeEvent:
        def __init__(self, kind, **values):
            self.kind, self.values = kind, values
        def type(self): return self.kind
        def magnification(self): return self.values.get("magnification", 0)
        def hasPreciseScrollingDeltas(self): return self.values.get("precise", False)
        def scrollingDeltaX(self): return self.values.get("dx", 0)
        def scrollingDeltaY(self): return self.values.get("dy", 0)
        def window(self): return None
        def modifierFlags(self): return self.values.get("flags", 0)
        def isDirectionInvertedFromDevice(self): return False

    class FakeCanvas:
        def __init__(self): self.calls = []
        def gesture_zoom(self, factor): self.calls.append(("zoom", factor))
        def gesture_pan(self, dx, dy): self.calls.append(("pan", dx, dy))

    canvas = FakeCanvas()
    pinch = FakeEvent(AppKit.NSEventTypeMagnify, magnification=0.1)
    assert mac_gestures.handle_event(pinch, lambda: canvas) is None
    swipe = FakeEvent(AppKit.NSEventTypeScrollWheel, precise=True, dx=3, dy=4)
    assert mac_gestures.handle_event(swipe, lambda: canvas) is None
    wheel = FakeEvent(AppKit.NSEventTypeScrollWheel, precise=False, dy=1)
    assert mac_gestures.handle_event(wheel, lambda: canvas) is wheel      # 鼠标滚轮交给 Kivy
    assert mac_gestures.handle_event(pinch, lambda: None) is pinch        # 不在画布上
    magic = FakeEvent(AppKit.NSEventTypeScrollWheel, precise=True, dy=10,
                      flags=AppKit.NSEventModifierFlagCommand)
    assert mac_gestures.handle_event(magic, lambda: canvas) is None      # Cmd + 滚动：缩放
    assert canvas.calls[:2] == [("zoom", 1.1), ("pan", 6.0, -8.0)]
    assert canvas.calls[2][0] == "zoom" and canvas.calls[2][1] > 1


def test_music_library(tmp_path):
    import subprocess
    from colornumber.core import music
    wav = tmp_path / "song.wav"
    audio.save_wav(audio.make_color_done(), wav, audio.EFFECT_RATE)
    library = music.MusicLibrary(tmp_path / "library")
    first = library.add(wav)
    assert first["name"] == "song" and Path(first["file"]).suffix == ".wav"
    ffmpeg = music._ffmpeg()
    if ffmpeg:
        m4a = tmp_path / "phone.m4a"
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "aac", str(m4a)], check=True)
        second = library.add(m4a)
        assert Path(second["file"]).suffix == ".ogg" and Path(second["file"]).stat().st_size > 1000
    assert [t["name"] for t in library.tracks()][0] == "song"
    library.remove(first["id"])
    assert all(t["id"] != first["id"] for t in library.tracks())
    assert not Path(first["file"]).exists()


def test_save_after_delete_is_ignored(tmp_path):
    store = ProjectStore(tmp_path)
    meta = store.create(small_picture(), "test", "import")
    _, game = store.load(meta["id"], BLOCK_WRONG)
    store.delete(meta["id"])
    store.save(meta, game)               # 不报错，也不会把作品"复活"
    assert store.list() == []


def test_project_name_follows_language():
    from colornumber.core.i18n import project_name
    meta = {"name": "橘猫", "source": "library:cat"}
    assert project_name(meta, "en") == "Ginger Cat"
    assert project_name({"name": "Ginger Cat", "source": "library:cat"}, "zh") == "橘猫"
    assert project_name({"name": "我家的猫", "source": "library:cat"}, "en") == "我家的猫"   # 改过的名字不变
    assert project_name({"name": "photo", "source": "import"}, "en") == "photo"


def test_smooth_style_keeps_small_contrasting_features():
    # 浅色皮肤上一个单格的深色点（像瞳孔）：平滑风格也要保留
    image = Image.new("RGB", (160, 160), (235, 190, 160))
    for x in range(70, 80):
        for y in range(70, 80):
            image.putpixel((x, y), (20, 15, 15))
    picture = converter.convert(image, grid_size=16, color_count=4, style="smooth")
    assert picture.numbers[7][7] != picture.numbers[0][0]
