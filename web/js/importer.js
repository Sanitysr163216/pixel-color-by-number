// 导入照片页面：选一张照片，调格子数、颜色数和风格，预览转换结果，然后开始填色。
// 转换在后台线程里用 Pyodide 运行桌面版的 converter.py（见 convert-worker.js）。

import { tr } from "./i18n.js";
import { newProject, saveProject } from "./store.js";
import { toast } from "./ui.js";

const DEFAULTS = { gridSize: 48, colorCount: 16, style: "smooth" };

// 和后台线程说话：每个请求有一个编号，结果回来时按编号找到对应的 Promise
class Converter {
  constructor(onProgress) {
    this.worker = null;
    this.nextId = 1;
    this.pending = new Map();
    this.onProgress = onProgress;
  }

  call(action, data) {
    if (!this.worker) {
      this.worker = new Worker("js/convert-worker.js");
      this.worker.onmessage = (event) => {
        const { id, type, stage, result, error } = event.data;
        if (type === "progress") {
          this.onProgress(stage);
          return;
        }
        const request = this.pending.get(id);
        this.pending.delete(id);
        if (error) request.reject(new Error(error));
        else request.resolve(result);
      };
    }
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      this.pending.set(id, { resolve, reject });
      this.worker.postMessage({ id, action, data }, data instanceof ArrayBuffer ? [data] : []);
    });
  }
}

export class ImportScreen {
  // app: {showHome(), openProject(project), settings}
  constructor(root, app) {
    this.root = root;
    this.app = app;
    this.converter = new Converter((stage) => this.showStage(stage));
    this.options = { ...DEFAULTS };
    this.picture = null;
    this.photoId = 0;
    this.busy = false;
    this.again = false;

    this.input = root.querySelector("#photo-input");
    this.input.addEventListener("change", () => {
      const file = this.input.files[0];
      this.input.value = "";
      if (file) this.load(file);
    });
    root.querySelector("#import-back").addEventListener("click", () => app.showHome());
    root.querySelector("#import-choose").addEventListener("click", () => this.input.click());
    root.querySelector("#import-start").addEventListener("click", () => this.start());
    root.querySelector("#import-use-recommended").addEventListener("click", () => {
      if (this.recommended) this.setSlider("colors", this.recommended);
    });

    this.sliders = {};
    for (const [name, key] of [["grid", "gridSize"], ["colors", "colorCount"]]) {
      const slider = root.querySelector(`#import-${name}`);
      const value = root.querySelector(`#import-${name}-value`);
      slider.addEventListener("input", () => {
        value.textContent = slider.value;
      });
      slider.addEventListener("change", () => {
        this.options[key] = Number(slider.value);
        this.convert();
      });
      this.sliders[name] = { slider, value, key };
    }
    for (const chip of root.querySelectorAll("[data-style]")) {
      chip.addEventListener("click", () => {
        this.options.style = chip.dataset.style;
        this.updateStyleChips();
        this.convert();
      });
    }
    const compare = root.querySelector("#import-compare");
    const showOriginal = (on) => root.querySelector(".import-preview").classList.toggle("original", on);
    compare.addEventListener("pointerdown", () => showOriginal(true));
    for (const name of ["pointerup", "pointerleave", "pointercancel"]) {
      compare.addEventListener(name, () => showOriginal(false));
    }
  }

  // 首页点"导入照片"：直接打开手机的相册 / 文件选择
  choosePhoto() {
    this.input.click();
  }

  setSlider(name, value) {
    const { slider, value: label, key } = this.sliders[name];
    slider.value = value;
    label.textContent = value;
    this.options[key] = Number(value);
    this.convert();
  }

  updateStyleChips() {
    for (const chip of this.root.querySelectorAll("[data-style]")) {
      chip.classList.toggle("active", chip.dataset.style === this.options.style);
    }
  }

  showStage(stage) {
    const status = this.root.querySelector("#import-status");
    const messages = {
      python: "web_loading_converter",
      packages: "web_loading_converter",
      code: "web_loading_converter",
      ready: "web_converting",
    };
    if (messages[stage]) status.textContent = tr(messages[stage]);
  }

  async load(file) {
    this.app.showScreen("import");
    this.photoId += 1;
    const photoId = this.photoId;
    this.picture = null;
    this.recommended = 0;
    this.root.querySelector("#import-recommend").hidden = true;
    this.root.querySelector("#import-start").disabled = true;
    this.root.querySelector("#import-name").value = file.name.replace(/\.[^.]+$/, "");
    const original = this.root.querySelector("#import-original");
    if (original.src) URL.revokeObjectURL(original.src);
    original.src = URL.createObjectURL(file);
    this.clearPreview();
    this.root.querySelector("#import-status").textContent = tr("web_converting");
    try {
      const size = await this.converter.call("load", await file.arrayBuffer());
      if (photoId !== this.photoId) return;
      this.photoSize = size;
      await this.convert();
      this.recommend(photoId);
    } catch (error) {
      this.root.querySelector("#import-status").textContent = tr("web_convert_failed");
      toast(String(error.message || error));
    }
  }

  // 转换：正在转换时又改了选项，等这次做完再按最新的选项做一次
  async convert() {
    if (!this.photoSize) return;
    if (this.busy) {
      this.again = true;
      return;
    }
    this.busy = true;
    this.root.querySelector("#import-status").textContent = tr("web_converting");
    try {
      do {
        this.again = false;
        const photoId = this.photoId;
        const picture = await this.converter.call("convert", {
          grid_size: this.options.gridSize,
          color_count: this.options.colorCount,
          style: this.options.style,
        });
        if (photoId === this.photoId && !this.again) this.showPicture(picture);
      } while (this.again);
    } catch (error) {
      this.root.querySelector("#import-status").textContent = tr("web_convert_failed");
      toast(String(error.message || error));
    } finally {
      this.busy = false;
    }
  }

  async recommend(photoId) {
    try {
      const count = await this.converter.call("recommend", {
        grid_size: this.options.gridSize,
        style: this.options.style,
        max_colors: 36,
      });
      if (photoId !== this.photoId) return;
      this.recommended = count;
      const row = this.root.querySelector("#import-recommend");
      row.querySelector("span").textContent = tr("recommended_colors", { count });
      row.hidden = false;
    } catch {
      // 推荐失败不影响转换
    }
  }

  clearPreview() {
    const canvas = this.root.querySelector("#import-preview");
    canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
  }

  // 预览：每格画成一样大的方块
  showPicture(picture) {
    this.picture = picture;
    const canvas = this.root.querySelector("#import-preview");
    const box = canvas.parentElement;
    const ratio = window.devicePixelRatio || 1;
    const cell = Math.max(1, Math.floor(Math.min(box.clientWidth / picture.width, box.clientHeight / picture.height) * ratio));
    canvas.width = picture.width * cell;
    canvas.height = picture.height * cell;
    canvas.style.width = `${canvas.width / ratio}px`;
    canvas.style.height = `${canvas.height / ratio}px`;
    const context = canvas.getContext("2d");
    picture.numbers.forEach((number, idx) => {
      const [r, g, b] = picture.palette[number - 1];
      context.fillStyle = `rgb(${r}, ${g}, ${b})`;
      context.fillRect((idx % picture.width) * cell, Math.floor(idx / picture.width) * cell, cell, cell);
    });
    let text = tr("preview_info", { width: picture.width, height: picture.height, colors: picture.palette.length });
    text += ` ${tr("fidelity", { score: picture.fidelity })}`;
    if (picture.similar) text += ` ${tr("similar_warning", { pairs: picture.similar })}`;
    this.root.querySelector("#import-status").textContent = text;
    this.root.querySelector("#import-start").disabled = false;
  }

  async start() {
    if (!this.picture) return;
    const name = this.root.querySelector("#import-name").value.trim() || tr("import_photo");
    const { width, height, palette, numbers } = this.picture;
    const project = newProject({ width, height, palette, numbers }, name, "import");
    await saveProject(project);
    this.app.openProject(project);
  }
}
