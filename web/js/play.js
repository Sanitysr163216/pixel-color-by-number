// 填色页面：上面是返回、进度、撤销、重画、提示；中间是画布；下面是工具和颜色栏。
// （桌面版对应的是 ui/game_screen.py）

import { Board } from "./board.js";
import { Game } from "./game.js";
import { tr } from "./i18n.js";
import * as sound from "./sound.js";
import { saveProject } from "./store.js";
import { button, confirmDialog, dialog, el, longPress, toast } from "./ui.js";

const SAVE_DELAY = 1000;        // 停笔 1 秒后自动保存

export class PlayScreen {
  // app: {settings, showHome(), projectName(project)}
  constructor(root, app) {
    this.root = root;
    this.app = app;
    this.project = null;
    this.game = null;
    this.swatches = new Map();
    this.saveTimer = null;
    this.wasComplete = false;

    this.board = new Board(root.querySelector("#board"), {
      cellsChanged: (changed) => this.cellsChanged(changed),
      strokeEnded: () => this.strokeEnded(),
    });
    this.buildToolbar();
    root.querySelector("#play-back").addEventListener("click", () => this.goBack());
    root.querySelector("#play-undo").addEventListener("click", () => this.undo());
    root.querySelector("#play-redo").addEventListener("click", () => this.redo());
    root.querySelector("#play-hint").addEventListener("click", () => (this.game?.isComplete() ? this.showCompletion() : this.hint()));

    // 切到别的 App 或关掉页面前，马上保存
    document.addEventListener("visibilitychange", () => document.hidden && this.saveNow());
    window.addEventListener("pagehide", () => this.saveNow());
  }

  buildToolbar() {
    const bar = this.root.querySelector("#tools");
    this.toolButtons = {};
    for (const [tool, iconName, label] of [["brush", "brush", "tool_brush"], ["wand", "wand", "tool_wand"],
      ["move", "move", "tool_move"]]) {
      const item = button("", { iconName, kind: "tool", onClick: () => this.setTool(tool), title: tr(label) });
      item.append(el("span", { class: "tool-label", "data-tr": label, text: tr(label) }));
      this.toolButtons[tool] = item;
      bar.append(item);
    }
    const bucket = button("", { iconName: "bucket", kind: "tool long-press", title: tr("tool_bucket") });
    bucket.append(el("span", { class: "tool-label", "data-tr": "tool_bucket", text: tr("tool_bucket") }));
    longPress(bucket, { onTap: () => this.bucket(), onLong: () => this.askFillAll() });
    bar.append(bucket);
    const fit = button("", { iconName: "fit", kind: "tool", onClick: () => this.board.fit(), title: tr("fit_view") });
    fit.append(el("span", { class: "tool-label", "data-tr": "fit_view", text: tr("fit_view") }));
    bar.append(fit);
  }

  // ---------------------------------------------------------------- 打开和保存

  open(project) {
    this.project = project;
    this.game = new Game(project.picture, project.progress, this.app.settings.wrongMode);
    this.wasComplete = this.game.isComplete();
    this.root.querySelector("#play-title").textContent = this.app.projectName(project);
    this.board.load(this.game);
    this.setTool("brush");
    this.buildPalette();
    this.select(this.game.nextUnfinishedNumber(this.game.colorCount) || 1);
    this.updateProgress();
  }

  scheduleSave() {
    clearTimeout(this.saveTimer);
    this.saveTimer = setTimeout(() => this.saveNow(), SAVE_DELAY);
  }

  saveNow() {
    clearTimeout(this.saveTimer);
    if (!this.project || !this.game) return Promise.resolve();
    this.project.progress = this.game.toJSON();
    this.project.ratio = this.game.progress();
    this.project.completed = this.game.isComplete();
    return saveProject(this.project);
  }

  async goBack() {
    if (this.board.locked) return;
    await this.saveNow();
    this.project = null;
    this.game = null;
    this.app.showHome();
  }

  setTool(tool) {
    this.board.tool = tool;
    for (const [name, item] of Object.entries(this.toolButtons)) item.classList.toggle("active", name === tool);
  }

  // ---------------------------------------------------------------- 颜色栏

  buildPalette() {
    const palette = this.root.querySelector("#palette");
    palette.replaceChildren();
    this.swatches.clear();
    this.game.picture.palette.forEach((color, index) => {
      const number = index + 1;
      const [r, g, b] = color;
      const light = 0.299 * r + 0.587 * g + 0.114 * b > 150;
      const swatch = el("button", { class: "swatch", type: "button", onclick: () => this.select(number) }, [
        el("span", { class: "swatch-color", style: `background: rgb(${r}, ${g}, ${b}); color: ${light ? "#222" : "#fff"}` },
          [el("span", { class: "swatch-number", text: String(number) })]),
        el("span", { class: "swatch-bar" }, [el("span", { class: "swatch-fill" })]),
      ]);
      palette.append(swatch);
      this.swatches.set(number, swatch);
      this.updateSwatch(number);
    });
  }

  updateSwatch(number) {
    const swatch = this.swatches.get(number);
    const total = this.game.cellsByNumber[number].length;
    const remaining = this.game.remainingCount(number);
    swatch.classList.toggle("done", remaining === 0);
    swatch.querySelector(".swatch-fill").style.width = `${(100 * (total - remaining)) / Math.max(1, total)}%`;
  }

  select(number) {
    this.board.selected = number;
    for (const [n, swatch] of this.swatches) swatch.classList.toggle("selected", n === number);
    this.swatches.get(number)?.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
    this.board.requestDraw();
  }

  updateProgress() {
    this.root.querySelector("#play-percent").textContent = tr("progress", { percent: Math.floor(this.game.progress() * 100) });
    this.root.querySelector("#play-undo").disabled = !this.game.history.length;
    this.root.querySelector("#play-redo").disabled = !this.game.redoStack.length;
    const done = this.game.isComplete();
    const hint = this.root.querySelector("#play-hint");
    hint.querySelector("span:last-child").textContent = tr(done ? "finished_menu" : "hint");
  }

  // ---------------------------------------------------------------- 画布传来的事件

  cellsChanged(changed) {
    if (changed.some((idx) => this.game.isCorrect(idx))) sound.pop();
    else if (changed.some((idx) => this.game.isWrong(idx))) sound.wrong();
    const numbers = new Set(changed.map((idx) => this.game.answer[idx]));
    for (const number of numbers) this.updateSwatch(number);
    this.updateProgress();
  }

  strokeEnded() {
    this.scheduleSave();
    sound.startStroke();
    this.updateProgress();
    if (this.game.isComplete()) {
      if (!this.wasComplete) {
        this.wasComplete = true;
        this.celebrate();
      }
      return;
    }
    this.wasComplete = false;
    const selected = this.board.selected;
    if (this.game.remainingCount(selected) === 0) {
      sound.colorDone();
      const following = this.game.nextUnfinishedNumber(selected);
      if (following !== null) this.select(following);
    }
  }

  // ---------------------------------------------------------------- 按钮

  apply(changed) {
    if (!changed.length) return;
    this.board.refreshCells(changed);
    for (let n = 1; n <= this.game.colorCount; n++) this.updateSwatch(n);
    this.updateProgress();
    this.scheduleSave();
  }

  undo() {
    if (!this.board.locked) this.apply(this.game.undo());
  }

  redo() {
    if (!this.board.locked) this.apply(this.game.redo());
  }

  bucket() {
    if (this.board.locked) return;
    const changed = this.game.bucket(this.board.selected);
    if (changed.length) {
      this.board.refreshCells(changed);
      this.cellsChanged(changed);
      this.strokeEnded();
    }
  }

  // 长按油漆桶：确认后按颜色一种一种快速填满，整个过程算一笔
  askFillAll() {
    if (this.board.locked || this.game.isComplete()) return;
    confirmDialog(tr("confirm_fill_all", { cells: this.game.totalRemaining() }), tr("fill_all"), () => this.fillAll());
  }

  fillAll() {
    const numbers = [];
    for (let n = 1; n <= this.game.colorCount; n++) if (this.game.remainingCount(n) > 0) numbers.push(n);
    if (!numbers.length) return;
    this.board.locked = true;
    this.game.beginStroke();
    const step = () => {
      const number = numbers.shift();
      this.select(number);
      const changed = this.game.fillNumber(number);
      this.board.refreshCells(changed);
      this.cellsChanged(changed);
      if (numbers.length) {
        setTimeout(step, Math.min(150, 2500 / (numbers.length + 1)));
        return;
      }
      this.game.endStroke();
      this.board.locked = false;
      this.strokeEnded();
    };
    step();
  }

  hint() {
    if (this.board.locked || this.game.isComplete()) return;
    const [row, col] = this.board.visibleCenter();
    const idx = this.game.findHint(this.board.selected, row, col);
    if (idx === null) return;
    const number = this.game.answer[idx];
    if (number !== this.board.selected) this.select(number);
    this.board.showHint(idx);
  }

  // ---------------------------------------------------------------- 完成

  celebrate() {
    this.saveNow();
    sound.complete();
    this.board.fit();
    this.board.playReplay(this.game.replayFrames(90), 2800, () => setTimeout(() => this.showCompletion(), 300));
  }

  showCompletion() {
    if (!this.game) return;
    dialog({
      title: tr("picture_complete"),
      buttons: [
        { label: tr("export_png"), kind: "primary", action: () => exportPicture(this.game.picture, this.game.painted, this.app.projectName(this.project)), keepOpen: true },
        { label: tr("replay"), action: () => this.board.playReplay(this.game.replayFrames(90), 2800, () => this.showCompletion()) },
        { label: tr("back_to_gallery"), action: () => this.goBack() },
        { label: tr("keep_looking") },
      ],
    });
  }
}

// 导出 PNG：手机上弹出"分享"（可以存到相册），电脑上直接下载
export async function exportPicture(picture, painted, name) {
  const cell = Math.max(1, Math.floor(1024 / Math.max(picture.width, picture.height)));
  const canvas = document.createElement("canvas");
  canvas.width = picture.width * cell;
  canvas.height = picture.height * cell;
  const context = canvas.getContext("2d");
  context.fillStyle = "#fff";
  context.fillRect(0, 0, canvas.width, canvas.height);
  picture.numbers.forEach((_answer, idx) => {
    const value = painted[idx];
    if (!value) return;
    const [r, g, b] = picture.palette[value - 1];
    context.fillStyle = `rgb(${r}, ${g}, ${b})`;
    context.fillRect((idx % picture.width) * cell, Math.floor(idx / picture.width) * cell, cell, cell);
  });
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  const fileName = `${name.replace(/[\\/:*?"<>|]+/g, "_") || "picture"}.png`;
  const file = new File([blob], fileName, { type: "image/png" });
  if (navigator.canShare && navigator.canShare({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: name });
      return;
    } catch (error) {
      if (error.name === "AbortError") return;      // 玩家自己关掉了分享
    }
  }
  const link = el("a", { href: URL.createObjectURL(blob), download: fileName });
  document.body.append(link);
  link.click();
  link.remove();
  toast(tr("web_saved_to_downloads"));
}
