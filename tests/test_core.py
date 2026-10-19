"""
游戏逻辑的自动测试。运行方法：在项目文件夹里执行

    pytest
"""

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


def test_sounds(tmp_path):
    paths = audio.ensure_sounds(tmp_path)
    assert set(paths) == {"pop", "color_done", "complete", "music"}
