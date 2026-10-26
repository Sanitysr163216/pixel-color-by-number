// 填色画布：显示格子、缩放和移动、触摸填色。（桌面版对应的是 ui/paint_canvas.py）
//
// 坐标：(ox, oy) 是整张图左上角在画布上的位置，scale 是每格多少"CSS 像素"。
// 手机屏幕一个 CSS 像素里有 2～3 个真正的像素（devicePixelRatio），
// 每格的大小和位置都对齐到真正的像素，格子才会清清楚楚、大小一样。
//
// 操作：一根手指填色（移动工具时是拖动画面），两根手指缩放和移动；电脑上滚轮缩放、右键拖动。

import { cellsOnLine, greyOf } from "./game.js";

const FADE_START = 11;      // 每格大于这么多 CSS 像素时，开始从灰色轮廓变成白格子和数字
const FADE_END = 18;
const MAX_SCALE = 72;
const HIGHLIGHT = "rgba(77, 133, 242, 0.30)";   // 当前编号的格子

export class Board {
  // callbacks: {cellsChanged(changed), strokeEnded()}
  constructor(canvas, callbacks) {
    this.canvas = canvas;
    this.context = canvas.getContext("2d");
    this.callbacks = callbacks;
    this.game = null;
    this.selected = 1;
    this.tool = "brush";            // "brush"、"wand" 或 "move"
    this.locked = false;            // 播放完成动画时不能操作
    this.scale = 1;
    this.exactScale = 1;            // 缩放时用的精确值，显示时再对齐到像素
    this.ox = 0;
    this.oy = 0;
    this.pointers = new Map();
    this.mode = null;               // "paint"、"pan" 或 "pinch"
    this.hint = null;               // {idx, until}：提示时闪烁的格子
    this.drawQueued = false;
    this.glyphs = new Map();        // 数字的小图片，画数字时直接贴上去，比每次写字快很多

    this.layer = document.createElement("canvas");   // 每格 1 个像素：填了的颜色，没填的是灰色
    this.mask = document.createElement("canvas");    // 没填的格子是白色，其他透明
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(canvas.parentElement);

    canvas.addEventListener("pointerdown", (event) => this.pointerDown(event));
    canvas.addEventListener("pointermove", (event) => this.pointerMove(event));
    canvas.addEventListener("pointerup", (event) => this.pointerUp(event));
    canvas.addEventListener("pointercancel", (event) => this.pointerUp(event, true));
    canvas.addEventListener("wheel", (event) => this.wheel(event), { passive: false });
    canvas.addEventListener("contextmenu", (event) => event.preventDefault());
  }

  load(game) {
    this.game = game;
    this.layer.width = this.mask.width = game.width;
    this.layer.height = this.mask.height = game.height;
    this.layerData = this.layer.getContext("2d").createImageData(game.width, game.height);
    this.maskData = this.mask.getContext("2d").createImageData(game.width, game.height);
    this.greys = game.picture.palette.map(greyOf);
    this.repaintAll(game.painted);
    this.resize();
    this.fit();
  }

  // ---------------------------------------------------------------- 格子的颜色

  setPixel(idx, value) {
    const answer = this.game.answer[idx];
    const color = value ? this.game.picture.palette[value - 1] : this.greys[answer - 1];
    const i = idx * 4;
    this.layerData.data.set([color[0], color[1], color[2], 255], i);
    this.maskData.data.set([255, 255, 255, value ? 0 : 255], i);
  }

  flushLayers() {
    this.layer.getContext("2d").putImageData(this.layerData, 0, 0);
    this.mask.getContext("2d").putImageData(this.maskData, 0, 0);
    this.requestDraw();
  }

  repaintAll(painted) {
    painted.forEach((value, idx) => this.setPixel(idx, value));
    this.flushLayers();
  }

  refreshCells(changed) {
    for (const idx of changed) this.setPixel(idx, this.game.painted[idx]);
    this.flushLayers();
  }

  // ---------------------------------------------------------------- 视图

  resize() {
    const parent = this.canvas.parentElement;
    const ratio = window.devicePixelRatio || 1;
    const width = parent.clientWidth;
    const height = parent.clientHeight;
    if (!width || !height) return;
    const centerX = this.viewWidth ? (this.viewWidth / 2 - this.ox) / this.scale : null;
    const centerY = this.viewHeight ? (this.viewHeight / 2 - this.oy) / this.scale : null;
    this.ratio = ratio;
    this.viewWidth = width;
    this.viewHeight = height;
    this.canvas.width = Math.round(width * ratio);
    this.canvas.height = Math.round(height * ratio);
    this.canvas.style.width = `${width}px`;
    this.canvas.style.height = `${height}px`;
    if (this.game && centerX !== null) {
      // 窗口大小变了（比如手机转了方向）：保持原来在中间的格子还在中间
      this.ox = width / 2 - centerX * this.scale;
      this.oy = height / 2 - centerY * this.scale;
      this.clamp();
    }
    this.glyphs.clear();
    this.requestDraw();
  }

  fitScale() {
    return Math.min(this.viewWidth / this.game.width, this.viewHeight / this.game.height) * 0.94;
  }

  // 显示用的缩放：2 以上时对齐到真正的像素，每格大小完全一样
  snap(scale) {
    if (scale < 2) return scale;
    return Math.max(1, Math.round(scale * this.ratio)) / this.ratio;
  }

  fit() {
    if (!this.game || !this.viewWidth) return;
    this.exactScale = this.fitScale();
    this.scale = this.snap(this.exactScale);
    this.ox = (this.viewWidth - this.game.width * this.scale) / 2;
    this.oy = (this.viewHeight - this.game.height * this.scale) / 2;
    this.clamp();
    this.requestDraw();
  }

  // 以 (x, y) 为中心缩放：那个点下面的格子保持不动
  zoomAt(x, y, factor) {
    if (!this.game) return;
    const minimum = this.fitScale() * 0.6;
    const exact = Math.min(MAX_SCALE, Math.max(minimum, this.exactScale * factor));
    const scale = this.snap(exact);
    const ratio = scale / this.scale;
    this.ox = x - (x - this.ox) * ratio;
    this.oy = y - (y - this.oy) * ratio;
    this.exactScale = exact;
    this.scale = scale;
    this.clamp();
    this.requestDraw();
  }

  panBy(dx, dy) {
    this.ox += dx;
    this.oy += dy;
    this.clamp();
    this.requestDraw();
  }

  // 不能把图完全拖出画面：图总要盖住画面的中心
  clamp() {
    const width = this.game.width * this.scale;
    const height = this.game.height * this.scale;
    this.ox = Math.min(this.viewWidth / 2, Math.max(this.viewWidth / 2 - width, this.ox));
    this.oy = Math.min(this.viewHeight / 2, Math.max(this.viewHeight / 2 - height, this.oy));
    const ratio = this.ratio || 1;
    this.ox = Math.round(this.ox * ratio) / ratio;
    this.oy = Math.round(this.oy * ratio) / ratio;
  }

  cellAt(x, y) {
    const col = Math.floor((x - this.ox) / this.scale);
    const row = Math.floor((y - this.oy) / this.scale);
    if (col < 0 || row < 0 || col >= this.game.width || row >= this.game.height) return null;
    return [row, col];
  }

  // 画面中间是哪一格（提示时找离它最近的格子）
  visibleCenter() {
    return [(this.viewHeight / 2 - this.oy) / this.scale, (this.viewWidth / 2 - this.ox) / this.scale];
  }

  // 提示：把格子移到画面中间、放大到看得清，然后闪几下
  showHint(idx) {
    const row = Math.floor(idx / this.game.width);
    const col = idx % this.game.width;
    const target = Math.max(this.exactScale, 26);
    this.exactScale = target;
    this.scale = this.snap(target);
    this.ox = this.viewWidth / 2 - (col + 0.5) * this.scale;
    this.oy = this.viewHeight / 2 - (row + 0.5) * this.scale;
    this.clamp();
    this.hint = { idx, until: performance.now() + 1800 };
    this.requestDraw();
  }

  // ---------------------------------------------------------------- 画出来

  requestDraw() {
    if (this.drawQueued) return;
    this.drawQueued = true;
    requestAnimationFrame(() => {
      this.drawQueued = false;
      this.draw();
    });
  }

  draw() {
    const context = this.context;
    const { ratio, viewWidth, viewHeight } = this;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, viewWidth, viewHeight);
    if (!this.game) return;
    const { scale, ox, oy } = this;
    const width = this.game.width;
    const height = this.game.height;
    context.imageSmoothingEnabled = false;
    context.drawImage(this.layer, ox, oy, width * scale, height * scale);

    // 放大以后：灰色慢慢变成白色，出现格子线和数字
    const fade = Math.min(1, Math.max(0, (scale - FADE_START) / (FADE_END - FADE_START)));
    if (fade > 0) {
      context.globalAlpha = fade;
      context.drawImage(this.mask, ox, oy, width * scale, height * scale);
      this.drawDetails(context, fade);
      context.globalAlpha = 1;
    }
    this.drawHint(context);
  }

  // 看得见的格子才画格子线、高亮和数字
  drawDetails(context, fade) {
    const { scale, ox, oy, game } = this;
    const col0 = Math.max(0, Math.floor(-ox / scale));
    const row0 = Math.max(0, Math.floor(-oy / scale));
    const col1 = Math.min(game.width, Math.ceil((this.viewWidth - ox) / scale));
    const row1 = Math.min(game.height, Math.ceil((this.viewHeight - oy) / scale));

    context.fillStyle = HIGHLIGHT;
    for (const idx of game.cellsByNumber[this.selected] || []) {
      const row = Math.floor(idx / game.width);
      const col = idx % game.width;
      if (row < row0 || row >= row1 || col < col0 || col >= col1 || game.painted[idx]) continue;
      context.fillRect(ox + col * scale, oy + row * scale, scale, scale);
    }

    // 格子线：1 个真正的像素宽
    const line = 1 / this.ratio;
    context.fillStyle = "rgba(60, 60, 70, 0.22)";
    for (let col = col0; col <= col1; col++) {
      context.fillRect(ox + col * scale, oy + row0 * scale, line, (row1 - row0) * scale);
    }
    for (let row = row0; row <= row1; row++) {
      context.fillRect(ox + col0 * scale, oy + row * scale, (col1 - col0) * scale, line);
    }

    const size = Math.round(scale * 0.5 * this.ratio);
    for (let row = row0; row < row1; row++) {
      for (let col = col0; col < col1; col++) {
        const idx = row * game.width + col;
        const value = game.painted[idx];
        const x = ox + col * scale;
        const y = oy + row * scale;
        if (!value) {
          const glyph = this.glyph(game.answer[idx], size);
          context.drawImage(glyph, Math.round((x + (scale - glyph.width / this.ratio) / 2) * this.ratio) / this.ratio,
            Math.round((y + (scale - glyph.height / this.ratio) / 2) * this.ratio) / this.ratio,
            glyph.width / this.ratio, glyph.height / this.ratio);
        } else if (value !== game.answer[idx]) {
          // 填错的格子（"可以填错"模式）：画一条斜线，再显示正确的数字
          context.strokeStyle = `rgba(200, 40, 40, ${fade})`;
          context.lineWidth = Math.max(1, scale / 10);
          context.beginPath();
          context.moveTo(x + scale * 0.2, y + scale * 0.8);
          context.lineTo(x + scale * 0.8, y + scale * 0.2);
          context.stroke();
        }
      }
    }
  }

  // 一个数字的小图片（按真正的像素大小画好，存起来反复用）
  glyph(number, size) {
    const key = `${number}:${size}`;
    let glyph = this.glyphs.get(key);
    if (!glyph) {
      glyph = document.createElement("canvas");
      const text = String(number);
      const context = glyph.getContext("2d");
      context.font = `500 ${size}px -apple-system, "Segoe UI", Roboto, sans-serif`;
      glyph.width = Math.ceil(context.measureText(text).width) + 2;
      glyph.height = Math.ceil(size * 1.2);
      context.font = `500 ${size}px -apple-system, "Segoe UI", Roboto, sans-serif`;
      context.fillStyle = "#4a4a55";
      context.textBaseline = "middle";
      context.fillText(text, 1, glyph.height / 2 + size * 0.05);
      this.glyphs.set(key, glyph);
    }
    return glyph;
  }

  drawHint(context) {
    if (!this.hint) return;
    const now = performance.now();
    if (now > this.hint.until) {
      this.hint = null;
      return;
    }
    const { idx } = this.hint;
    const row = Math.floor(idx / this.game.width);
    const col = idx % this.game.width;
    const pulse = 0.5 + 0.5 * Math.sin(now / 120);
    context.strokeStyle = `rgba(242, 120, 40, ${0.4 + 0.6 * pulse})`;
    context.lineWidth = Math.max(2, this.scale / 6);
    context.strokeRect(this.ox + col * this.scale, this.oy + row * this.scale, this.scale, this.scale);
    this.requestDraw();
  }

  // ---------------------------------------------------------------- 触摸和鼠标

  point(event) {
    const rect = this.canvas.getBoundingClientRect();
    return [event.clientX - rect.left, event.clientY - rect.top];
  }

  pointerDown(event) {
    if (!this.game || this.locked) return;
    event.preventDefault();
    try {
      this.canvas.setPointerCapture(event.pointerId);   // 手指滑出画布也继续收到移动
    } catch {
      // 有的浏览器不支持某些指针，没关系
    }
    this.pointers.set(event.pointerId, this.point(event));
    if (this.pointers.size === 2) {
      // 第二根手指放上来：改成缩放。第一根手指刚画的那一笔撤掉
      this.cancelStroke();
      this.startPinch();
      return;
    }
    if (this.pointers.size > 2) return;
    const [x, y] = this.point(event);
    this.start = [x, y];
    this.moved = false;
    if (this.tool === "move" || event.button === 1 || event.button === 2) {
      this.mode = "pan";
    } else if (this.tool === "wand") {
      this.mode = "wand";
    } else {
      this.mode = "paint";
      this.game.beginStroke();
      this.strokeChanged = false;
      this.lastCell = null;
      this.paintTo(x, y);
    }
    this.last = [x, y];
  }

  pointerMove(event) {
    if (!this.pointers.has(event.pointerId)) return;
    const [x, y] = this.point(event);
    this.pointers.set(event.pointerId, [x, y]);
    if (this.mode === "pinch") {
      this.updatePinch();
      return;
    }
    if (Math.hypot(x - this.start[0], y - this.start[1]) > 8) this.moved = true;
    if (this.mode === "pan") {
      this.panBy(x - this.last[0], y - this.last[1]);
    } else if (this.mode === "paint") {
      this.paintTo(x, y);
    }
    this.last = [x, y];
  }

  pointerUp(event, cancelled = false) {
    if (!this.pointers.has(event.pointerId)) return;
    this.pointers.delete(event.pointerId);
    if (this.mode === "pinch") {
      if (this.pointers.size === 0) this.mode = null;    // 剩一根手指时不接着画，免得误填
      return;
    }
    if (this.mode === "paint") {
      this.finishStroke();
    } else if (this.mode === "wand" && !this.moved && !cancelled) {
      const cell = this.cellAt(...this.point(event));
      if (cell) {
        const changed = this.game.magicWand(cell[0] * this.game.width + cell[1], this.selected);
        if (changed.length) {
          this.refreshCells(changed);
          this.callbacks.cellsChanged(changed);
          this.callbacks.strokeEnded();
        }
      }
    }
    this.mode = null;
  }

  paintTo(x, y) {
    const cell = this.cellAt(x, y);
    if (!cell) {
      this.lastCell = null;
      return;
    }
    const cells = this.lastCell ? cellsOnLine(...this.lastCell, ...cell) : [cell];
    this.lastCell = cell;
    const changed = [];
    for (const [row, col] of cells) {
      const idx = row * this.game.width + col;
      if (this.game.paint(idx, this.selected)) changed.push(idx);
    }
    if (changed.length) {
      this.strokeChanged = true;
      this.refreshCells(changed);
      this.callbacks.cellsChanged(changed);
    }
  }

  finishStroke() {
    this.game.endStroke();
    if (this.strokeChanged) this.callbacks.strokeEnded();
    this.strokeChanged = false;
  }

  cancelStroke() {
    if (this.mode !== "paint") return;
    this.game.endStroke();
    if (this.strokeChanged) {
      const changed = this.game.undo();
      this.game.redoStack.pop();          // 这一笔不应该能"重画"回来
      this.refreshCells(changed);
      this.callbacks.cellsChanged(changed);
    }
    this.strokeChanged = false;
  }

  startPinch() {
    this.mode = "pinch";
    const [a, b] = [...this.pointers.values()];
    this.pinch = { center: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], distance: Math.hypot(a[0] - b[0], a[1] - b[1]) };
  }

  updatePinch() {
    if (this.pointers.size < 2) return;
    const [a, b] = [...this.pointers.values()];
    const center = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    const distance = Math.hypot(a[0] - b[0], a[1] - b[1]);
    this.panBy(center[0] - this.pinch.center[0], center[1] - this.pinch.center[1]);
    if (this.pinch.distance > 10) this.zoomAt(center[0], center[1], distance / this.pinch.distance);
    this.pinch = { center, distance };
  }

  wheel(event) {
    if (!this.game) return;
    event.preventDefault();
    const [x, y] = this.point(event);
    // 电脑触控板的捏合手势在浏览器里是"按着 Ctrl 的滚轮"，变化小，所以放大得多一些
    const speed = event.ctrlKey ? 0.01 : 0.0015;
    this.zoomAt(x, y, Math.exp(-event.deltaY * speed));
  }

  // 完成后的回放：按填色顺序很快地重画一遍
  playReplay(frames, duration, onDone) {
    this.locked = true;
    const startTime = performance.now();
    const step = (now) => {
      const index = Math.min(frames.length - 1, Math.floor(((now - startTime) / duration) * frames.length));
      this.repaintAll(frames[index]);
      if (index < frames.length - 1) {
        requestAnimationFrame(step);
      } else {
        this.locked = false;
        this.repaintAll(this.game.painted);
        onDone();
      }
    };
    requestAnimationFrame(step);
  }
}
