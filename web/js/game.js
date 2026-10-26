// 填色游戏的进行状态：colornumber/core/game.py 的 JavaScript 版本（逻辑一样，存档格式也一样）。
//
// 几个名词：
// - idx（下标）：格子在"摊平"后的长列表里的位置，idx = row * width + col
// - answer：每格的正确编号；painted：每格目前填的编号，0 表示还没填
// - 一笔（stroke）：一次拖动、一次魔棒或一次油漆桶，撤销时整笔一起撤销。
//   一笔存成 [idx, 旧值, 新值, idx, 旧值, 新值, ...]

export const BLOCK_WRONG = "block";   // 颜色不对就不让填
export const ALLOW_WRONG = "allow";   // 可以填上，但标为错误

export class Game {
  // picture: {width, height, palette: [[r, g, b], ...], numbers: [摊平的编号]}
  constructor(picture, saved = {}, wrongMode = BLOCK_WRONG) {
    this.picture = picture;
    this.width = picture.width;
    this.height = picture.height;
    this.answer = picture.numbers;
    this.colorCount = picture.palette.length;
    this.painted = saved.painted ? saved.painted.slice() : new Array(this.answer.length).fill(0);
    this.history = (saved.history || []).map((stroke) => stroke.slice());
    this.redoStack = (saved.redo || []).map((stroke) => stroke.slice());
    this.wrongMode = wrongMode;
    this.stroke = null;

    // 每个编号对应哪些格子，以及还剩多少格没填对
    this.cellsByNumber = {};
    this.remaining = {};
    for (let n = 1; n <= this.colorCount; n++) {
      this.cellsByNumber[n] = [];
      this.remaining[n] = 0;
    }
    this.answer.forEach((number, idx) => {
      this.cellsByNumber[number].push(idx);
      if (this.painted[idx] !== number) this.remaining[number] += 1;
    });
  }

  // ---------------------------------------------------------------- 查询

  isCorrect(idx) { return this.painted[idx] === this.answer[idx]; }

  isWrong(idx) { return this.painted[idx] !== 0 && this.painted[idx] !== this.answer[idx]; }

  remainingCount(number) { return this.remaining[number]; }

  totalRemaining() {
    let total = 0;
    for (const n in this.remaining) total += this.remaining[n];
    return total;
  }

  progress() { return (this.answer.length - this.totalRemaining()) / this.answer.length; }

  isComplete() { return this.totalRemaining() === 0; }

  // 从 after 的下一个编号开始找，返回第一个还没填完的编号；全部填完返回 null
  nextUnfinishedNumber(after) {
    for (let step = 1; step <= this.colorCount; step++) {
      const number = ((after - 1 + step) % this.colorCount) + 1;
      if (this.remaining[number] > 0) return number;
    }
    return null;
  }

  // 提示：优先找 number 编号里离 (nearRow, nearCol) 最近的没填对的格子
  findHint(number, nearRow, nearCol) {
    const candidates = this.remaining[number] > 0
      ? this.cellsByNumber[number]
      : this.answer.map((_n, idx) => idx);
    let best = null;
    let bestDistance = Infinity;
    for (const idx of candidates) {
      if (this.isCorrect(idx)) continue;
      const row = Math.floor(idx / this.width);
      const col = idx % this.width;
      const distance = (row - nearRow) ** 2 + (col - nearCol) ** 2;
      if (distance < bestDistance) {
        best = idx;
        bestDistance = distance;
      }
    }
    return best;
  }

  // ---------------------------------------------------------------- 填色

  beginStroke() { this.stroke = []; }

  endStroke() {
    if (this.stroke && this.stroke.length) {
      this.history.push(this.stroke);
      this.redoStack = [];      // 画了新的一笔，之前撤销的就不能重画了
    }
    this.stroke = null;
  }

  // 修改一格，同时更新剩余数量和这一笔的记录
  set(idx, value) {
    const old = this.painted[idx];
    if (old === value) return false;
    const answer = this.answer[idx];
    if (old === answer) this.remaining[answer] += 1;
    if (value === answer) this.remaining[answer] -= 1;
    this.painted[idx] = value;
    if (this.stroke) this.stroke.push(idx, old, value);
    return true;
  }

  // 用 number 号颜色填 idx 这一格；已经填对的不会被覆盖
  paint(idx, number) {
    if (this.isCorrect(idx)) return false;
    if (number !== this.answer[idx] && this.wrongMode === BLOCK_WRONG) return false;
    return this.set(idx, number);
  }

  // 魔棒：填满和 idx 相连、编号都是 number 的格子
  magicWand(idx, number) {
    if (this.answer[idx] !== number) return [];
    this.beginStroke();
    const changed = [];
    const seen = new Set([idx]);
    const stack = [idx];
    while (stack.length) {
      const current = stack.pop();
      if (this.set(current, number)) changed.push(current);
      const row = Math.floor(current / this.width);
      const col = current % this.width;
      for (const [r, c] of [[row - 1, col], [row + 1, col], [row, col - 1], [row, col + 1]]) {
        if (r < 0 || r >= this.height || c < 0 || c >= this.width) continue;
        const neighbor = r * this.width + c;
        if (!seen.has(neighbor) && this.answer[neighbor] === number) {
          seen.add(neighbor);
          stack.push(neighbor);
        }
      }
    }
    this.endStroke();
    return changed;
  }

  // 把编号是 number 的格子全部填对，记进当前这一笔
  fillNumber(number) {
    return this.cellsByNumber[number].filter((idx) => this.set(idx, number));
  }

  // 油漆桶：填满整张图里编号是 number 的格子
  bucket(number) {
    this.beginStroke();
    const changed = this.fillNumber(number);
    this.endStroke();
    return changed;
  }

  undo() {
    if (!this.history.length) return [];
    const stroke = this.history.pop();
    this.redoStack.push(stroke);
    const saved = this.stroke;
    this.stroke = null;                 // 撤销本身不记进撤销记录
    const changed = [];
    for (let i = stroke.length - 3; i >= 0; i -= 3) {   // 倒着恢复
      this.set(stroke[i], stroke[i + 1]);
      changed.push(stroke[i]);
    }
    this.stroke = saved;
    return changed;
  }

  redo() {
    if (!this.redoStack.length) return [];
    const stroke = this.redoStack.pop();
    const saved = this.stroke;
    this.stroke = null;
    const changed = [];
    for (let i = 0; i < stroke.length; i += 3) {
      this.set(stroke[i], stroke[i + 2]);
      changed.push(stroke[i]);
    }
    this.stroke = saved;
    this.history.push(stroke);
    return changed;
  }

  // 按填色顺序回放：平均取 frameCount 帧，每帧是一份 painted
  replayFrames(frameCount) {
    const changes = [];
    for (const stroke of this.history) {
      for (let i = 0; i < stroke.length; i += 3) changes.push(stroke.slice(i, i + 3));
    }
    if (!changes.length) return [this.painted.slice()];
    const painted = new Array(this.answer.length).fill(0);
    const frames = [painted.slice()];
    frameCount = Math.max(2, frameCount);
    let applied = 0;
    for (let frame = 1; frame < frameCount; frame++) {
      const target = Math.round((changes.length * frame) / (frameCount - 1));
      while (applied < target) {
        const [idx, , value] = changes[applied];
        painted[idx] = value;
        applied += 1;
      }
      frames.push(painted.slice());
    }
    return frames;
  }

  toJSON() {
    return { painted: this.painted, history: this.history, redo: this.redoStack };
  }
}

// 从 (row0, col0) 到 (row1, col1) 直线经过的所有格子（拖得快时把中间补上）
export function cellsOnLine(row0, col0, row1, col1) {
  const cells = [];
  const dRow = Math.abs(row1 - row0);
  const dCol = Math.abs(col1 - col0);
  const stepRow = row1 >= row0 ? 1 : -1;
  const stepCol = col1 >= col0 ? 1 : -1;
  let error = dCol - dRow;
  let row = row0;
  let col = col0;
  for (;;) {
    cells.push([row, col]);
    if (row === row1 && col === col1) return cells;
    const double = 2 * error;
    if (double > -dRow) { error -= dRow; col += stepCol; }
    if (double < dCol) { error += dCol; row += stepRow; }
  }
}

// 没填的格子显示成浅灰色，但保留明暗（和 core/render.py 的 grey_of 一样）
export function greyOf([red, green, blue]) {
  const lightness = 0.299 * red + 0.587 * green + 0.114 * blue;
  const grey = Math.floor(175 + lightness * 0.28);
  return [grey, grey, grey];
}
