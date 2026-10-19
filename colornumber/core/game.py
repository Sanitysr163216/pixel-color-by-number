"""
填色游戏的进行状态：哪些格子填了什么颜色、撤销记录、各种填色工具。

几个名词：
- idx（下标）：格子在"摊平"后的长列表里的位置，idx = row * width + col
- answer：每格的正确编号（来自 Picture）
- painted：每格目前填的编号，0 表示还没填
- 一笔（stroke）：一次拖动、一次魔棒或一次油漆桶，撤销时整笔一起撤销

一笔在 history 里存成一个长列表 [idx, 旧值, 新值, idx, 旧值, 新值, ...]，
所以 history 既能用来撤销，也能用来回放整个填色过程。
"""

BLOCK_WRONG = "block"   # 填错模式：颜色不对就不让填
ALLOW_WRONG = "allow"   # 填错模式：可以填上，但标为错误


class Game:
    """一张图的填色进度。"""

    def __init__(self, picture, painted=None, history=None, wrong_mode=BLOCK_WRONG):
        self.picture = picture
        self.width = picture.width
        self.height = picture.height
        self.answer = picture.flat_numbers()
        self.painted = list(painted) if painted else [0] * len(self.answer)
        self.history = [list(stroke) for stroke in history] if history else []
        self.wrong_mode = wrong_mode
        self._stroke = None

        # 每个编号对应哪些格子，以及还剩多少格没填对
        self.cells_by_number = {n: [] for n in range(1, picture.color_count + 1)}
        for idx, number in enumerate(self.answer):
            self.cells_by_number[number].append(idx)
        self.remaining = {n: 0 for n in self.cells_by_number}
        for idx, number in enumerate(self.answer):
            if self.painted[idx] != number:
                self.remaining[number] += 1

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    def is_correct(self, idx):
        """这格是否已经填对。"""
        return self.painted[idx] == self.answer[idx]

    def is_wrong(self, idx):
        """这格是否填了错误的颜色。"""
        return self.painted[idx] != 0 and self.painted[idx] != self.answer[idx]

    def remaining_count(self, number):
        """某个编号还剩多少格没填对。"""
        return self.remaining[number]

    def total_remaining(self):
        return sum(self.remaining.values())

    def progress(self):
        """整张图的完成度，0.0 到 1.0。"""
        total = len(self.answer)
        return (total - self.total_remaining()) / total

    def is_complete(self):
        return self.total_remaining() == 0

    def next_unfinished_number(self, after):
        """从 after 的下一个编号开始找，返回第一个还没填完的编号；全部填完返回 None。"""
        count = self.picture.color_count
        for step in range(1, count + 1):
            number = (after - 1 + step) % count + 1
            if self.remaining[number] > 0:
                return number
        return None

    def find_hint(self, number, near_row, near_col):
        """
        找一个还没填对的格子给"提示"用：优先找 number 编号的格子，
        并选离 (near_row, near_col) 最近的那个。全部填完返回 None。
        """
        if number in self.remaining and self.remaining[number] > 0:
            candidates = self.cells_by_number[number]
        else:
            candidates = range(len(self.answer))
        best = None
        best_distance = None
        for idx in candidates:
            if self.is_correct(idx):
                continue
            row, col = divmod(idx, self.width)
            distance = (row - near_row) ** 2 + (col - near_col) ** 2
            if best is None or distance < best_distance:
                best = idx
                best_distance = distance
        return best

    # ------------------------------------------------------------------
    # 填色
    # ------------------------------------------------------------------

    def begin_stroke(self):
        """开始新的一笔（比如鼠标按下时）。"""
        self._stroke = []

    def end_stroke(self):
        """结束这一笔（比如鼠标松开时）。有改动才记进撤销记录。"""
        if self._stroke:
            self.history.append(self._stroke)
        self._stroke = None

    def _set(self, idx, value):
        """修改一格，同时更新剩余数量和这一笔的记录。"""
        old = self.painted[idx]
        if old == value:
            return False
        answer = self.answer[idx]
        if old == answer:
            self.remaining[answer] += 1
        if value == answer:
            self.remaining[answer] -= 1
        self.painted[idx] = value
        if self._stroke is not None:
            self._stroke.extend((idx, old, value))
        return True

    def paint(self, idx, number):
        """
        用 number 号颜色填 idx 这一格。返回是否真的改变了。
        已经填对的格子不会被覆盖；颜色不对时按填错模式处理。
        """
        if self.is_correct(idx):
            return False
        if number != self.answer[idx] and self.wrong_mode == BLOCK_WRONG:
            return False
        return self._set(idx, number)

    def magic_wand(self, idx, number):
        """
        魔棒：从 idx 出发，填满和它相连的、编号都是 number 的格子。
        点的格子编号不是 number 时什么都不做。返回改变了的格子列表。
        """
        if self.answer[idx] != number:
            return []
        self.begin_stroke()
        changed = []
        seen = {idx}
        stack = [idx]
        while stack:
            current = stack.pop()
            if self._set(current, number):
                changed.append(current)
            row, col = divmod(current, self.width)
            for r, c in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if 0 <= r < self.height and 0 <= c < self.width:
                    neighbor = r * self.width + c
                    if neighbor not in seen and self.answer[neighbor] == number:
                        seen.add(neighbor)
                        stack.append(neighbor)
        self.end_stroke()
        return changed

    def bucket(self, number):
        """油漆桶：填满整张图里所有编号是 number 的格子。返回改变了的格子列表。"""
        self.begin_stroke()
        changed = [idx for idx in self.cells_by_number[number] if self._set(idx, number)]
        self.end_stroke()
        return changed

    def undo(self):
        """撤销最后一笔。返回改变了的格子列表；没有可撤销的返回空列表。"""
        if not self.history:
            return []
        stroke = self.history.pop()
        changed = []
        saved, self._stroke = self._stroke, None   # 撤销本身不记进撤销记录
        # 倒着恢复，这样同一格在一笔里被改了多次也能正确还原
        for i in range(len(stroke) - 3, -1, -3):
            idx, old = stroke[i], stroke[i + 1]
            self._set(idx, old)
            changed.append(idx)
        self._stroke = saved
        return changed

    def restart(self):
        """清空进度，从头开始。"""
        self.__init__(self.picture, wrong_mode=self.wrong_mode)

    # ------------------------------------------------------------------
    # 回放（完成动画、导出 GIF/MP4 用）
    # ------------------------------------------------------------------

    def replay_frames(self, frame_count):
        """
        按填色顺序回放，平均取 frame_count 帧。
        每一帧是一个 painted 列表的副本，第一帧是空白，最后一帧是当前状态。
        """
        changes = [stroke[i:i + 3] for stroke in self.history for i in range(0, len(stroke), 3)]
        painted = [0] * len(self.answer)
        frames = [painted[:]]
        if not changes:
            return [self.painted[:]]
        frame_count = max(2, frame_count)
        applied = 0
        for frame in range(1, frame_count):
            target = round(len(changes) * frame / (frame_count - 1))
            while applied < target:
                idx, _old, new = changes[applied]
                painted[idx] = new
                applied += 1
            frames.append(painted[:])
        return frames

    # ------------------------------------------------------------------
    # 存档
    # ------------------------------------------------------------------

    def to_dict(self):
        return {"painted": self.painted, "history": self.history}

    @classmethod
    def from_dict(cls, picture, data, wrong_mode=BLOCK_WRONG):
        return cls(picture, data.get("painted"), data.get("history"), wrong_mode)


def cells_on_line(row0, col0, row1, col1):
    """
    返回从 (row0, col0) 到 (row1, col1) 直线经过的所有格子。
    拖动很快时两次鼠标位置之间会跳过格子，用它把中间补上。
    """
    cells = []
    d_row = abs(row1 - row0)
    d_col = abs(col1 - col0)
    step_row = 1 if row1 >= row0 else -1
    step_col = 1 if col1 >= col0 else -1
    error = d_col - d_row
    row, col = row0, col0
    while True:
        cells.append((row, col))
        if row == row1 and col == col1:
            return cells
        double = 2 * error
        if double > -d_row:
            error -= d_row
            col += step_col
        if double < d_col:
            error += d_col
            row += step_row
