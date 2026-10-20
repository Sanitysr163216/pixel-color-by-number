"""
在线图库页面：搜索博物馆里公有领域的名画，选一张变成数字填色图。

联网很慢，所以搜索和下载都放在后台线程里做（ThreadPoolExecutor），
做完以后用 Clock.schedule_once 回到主线程更新界面（Kivy 只能在主线程里改界面）。
"""

import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.screenmanager import Screen

from colornumber.core import online
from colornumber.ui.common import Chip, Dialog, RoundButton, message, pil_to_texture, tr  # noqa: F401
from colornumber.ui.home_screen import Card

Builder.load_string("""
<OnlineScreen>:
    canvas.before:
        Color:
            rgba: 0.97, 0.96, 0.94, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: "18dp"
        spacing: "12dp"
        BoxLayout:
            size_hint_y: None
            height: "44dp"
            spacing: "10dp"
            RoundButton:
                text: app.tr("back", app.lang)
                size_hint_x: None
                width: "90dp"
                on_release: app.show_home()
            Label:
                text: app.tr("online_gallery", app.lang)
                color: 0.2, 0.2, 0.25, 1
                font_size: "22sp"
                bold: True
                text_size: self.size
                halign: "left"
                valign: "middle"
        BoxLayout:
            size_hint_y: None
            height: "40dp"
            spacing: "8dp"
            TextInput:
                id: query
                multiline: False
                hint_text: app.tr("online_search_hint", app.lang)
                font_size: "16sp"
                padding: "12dp", "10dp"
                write_tab: False
                on_text_validate: root.search(self.text)
            RoundButton:
                text: app.tr("search", app.lang)
                primary: True
                size_hint_x: None
                width: "100dp"
                on_release: root.search(query.text)
        BoxLayout:
            id: topics
            size_hint_y: None
            height: "36dp"
            spacing: "6dp"
        Label:
            text: root.status
            color: 0.5, 0.5, 0.55, 1
            font_size: "14sp"
            size_hint_y: None
            height: "20dp" if root.status else 0
            opacity: 1 if root.status else 0
            text_size: self.size
            halign: "left"
        ScrollView:
            id: scroll
            GridLayout:
                id: grid
                cols: max(1, int(self.width // dp(215)))
                size_hint_y: None
                height: self.minimum_height
                spacing: "14dp"
                padding: "2dp"
                row_default_height: "250dp"
                row_force_default: True
                col_force_default: True
                col_default_width: (self.width - dp(4) - (self.cols - 1) * dp(14)) / self.cols
        BoxLayout:
            size_hint_y: None
            height: "40dp"
            spacing: "10dp"
            Label:
                text: app.tr("online_credit", app.lang)
                color: 0.5, 0.5, 0.55, 1
                font_size: "12sp"
                text_size: self.size
                halign: "left"
                valign: "middle"
            RoundButton:
                text: app.tr("online_load_more", app.lang)
                size_hint_x: None
                width: "140dp"
                opacity: 1 if root.has_more and not root.busy else 0
                disabled: not root.has_more or root.busy
                on_release: root.load_more()
""")

# 同时最多下载 4 张缩略图，不要一下子发出几十个请求
_pool = ThreadPoolExecutor(max_workers=4)


def _in_background(work, done, failed):
    """在后台线程里运行 work()，成功后在主线程调用 done(结果)，出错时调用 failed(错误)。"""
    def run():
        try:
            result = work()
        except Exception as error:     # 联网失败、图片坏了……都交给 failed 处理
            Clock.schedule_once(lambda _dt, e=error: failed(e))
            return
        Clock.schedule_once(lambda _dt: done(result))
    _pool.submit(run)


class OnlineScreen(Screen):
    status = StringProperty("")         # 列表上方的提示：正在搜索、没有结果、连不上网
    has_more = BooleanProperty(False)   # 还有没有下一页
    busy = BooleanProperty(False)       # 正在搜索

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._query = None
        self._page = 1
        self._search_id = 0             # 每次新搜索加 1，用来丢掉旧搜索迟到的结果
        self._thumbnails = {}           # 下载过的缩略图：image_id → 贴图
        self._topic_chips = []
        Clock.schedule_once(lambda _dt: self._build_topics())
        App.get_running_app().bind(lang=self._update_topic_text)

    def _build_topics(self):
        for key, query in online.TOPICS:
            chip = Chip(group="online_topic")
            chip.bind(on_press=lambda _chip, q=query: self.search(q, from_topic=True))
            self.ids.topics.add_widget(chip)
            self._topic_chips.append((chip, key))
        self._update_topic_text()

    def _update_topic_text(self, *_):
        for chip, key in self._topic_chips:
            chip.text = tr(key)

    def on_pre_enter(self, *_):
        if self._query is None and self._topic_chips:   # 第一次打开：先显示第一个推荐主题
            self._topic_chips[0][0].state = "down"
            self.search(online.TOPICS[0][1], from_topic=True)

    # ------------------------------------------------------------------
    # 搜索
    # ------------------------------------------------------------------

    def search(self, query, from_topic=False):
        if not from_topic:
            for chip, _key in self._topic_chips:   # 自己输入的搜索词：取消推荐主题的选中
                chip.state = "normal"
        self._query = query
        self._page = 1
        self._search_id += 1
        self.ids.grid.clear_widgets()
        self.ids.scroll.scroll_y = 1
        self._load_page()

    def load_more(self):
        self._page += 1
        self._load_page()

    def _load_page(self):
        search_id, query, page = self._search_id, self._query, self._page
        self.busy = True
        self.has_more = False
        self.status = tr("online_loading")

        def done(result):
            if search_id != self._search_id:
                return
            artworks, has_more = result
            self.busy = False
            self.has_more = has_more
            self.status = "" if artworks or page > 1 else tr("online_no_results")
            for artwork in artworks:
                self._add_card(artwork, search_id)

        def failed(_error):
            if search_id != self._search_id:
                return
            self.busy = False
            self.has_more = page > 1        # 加载更多失败时还可以再点一次
            if page > 1:
                self._page -= 1
            self.status = tr("online_error")

        _in_background(lambda: online.search(query, page), done, failed)

    def _add_card(self, artwork, search_id):
        subtitle = ", ".join(part for part in (artwork["artist"], artwork["date"]) if part)
        texture = self._thumbnails.get(artwork["image_id"])
        card = Card(texture, artwork["title"], subtitle, on_open=lambda: self.choose(artwork))
        self.ids.grid.add_widget(card)
        if texture is None:
            self._load_thumbnail(card, artwork["image_id"], search_id)

    def _load_thumbnail(self, card, image_id, search_id):
        def done(image):
            texture = pil_to_texture(image, nearest=False)
            self._thumbnails[image_id] = texture
            if search_id == self._search_id:
                card.image.texture = texture

        def work():
            if search_id != self._search_id:   # 已经换了搜索，这张不用下载了
                return None
            return online.download_image(image_id, online.THUMBNAIL_WIDTH)

        _in_background(work, lambda image: image is not None and done(image), lambda _error: None)

    # ------------------------------------------------------------------
    # 选中一张画
    # ------------------------------------------------------------------

    def choose(self, artwork):
        lines = [artwork["title"]]
        details = ", ".join(part for part in (artwork["artist"], artwork["date"]) if part)
        if details:
            lines.append(details)
        lines.append(tr("online_public_domain"))
        Dialog("\n".join(lines), [
            (tr("cancel"), None, "normal"),
            (tr("online_use"), lambda: self._download(artwork), "primary"),
        ]).open()

    def _download(self, artwork):
        waiting = Dialog(tr("online_downloading"), [])
        waiting.open()

        def done(image):
            waiting.dismiss()
            if App.get_running_app().screens.current != self.name:
                return                       # 下载期间玩家已经离开了这一页
            self._open_in_import(image, artwork["title"])

        def failed(_error):
            waiting.dismiss()
            message(tr("online_error"))

        _in_background(lambda: online.download_image(artwork["image_id"]), done, failed)

    def _open_in_import(self, image, title):
        """把图片存成临时文件交给导入页面（导入页面读完就删掉）。"""
        app = App.get_running_app()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "artwork.png"
            image.save(path)
            app.open_import(str(path), name=title[:40].strip(), came_from=self.name)

