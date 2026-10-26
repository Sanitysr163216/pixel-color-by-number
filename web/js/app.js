// 网页版的入口：读取数据、切换页面、首页（图库和我的作品）、设置。

import { greyOf } from "./game.js";
import { loadStrings, setLanguage, tr, translatePage } from "./i18n.js";
import { ImportScreen } from "./importer.js";
import { exportPicture, PlayScreen } from "./play.js";
import * as sound from "./sound.js";
import {
  askToKeepData, deleteProject, findBySource, getProject, listProjects, loadSettings, newProject,
  saveProject, saveSettings,
} from "./store.js";
import { button, confirmDialog, dialog, drawThumbnail, el, icon, loadIcons } from "./ui.js";

const VERSION = "__VERSION__";        // build_web.py 会换成真正的版本号

class App {
  constructor() {
    this.settings = loadSettings();
    this.library = null;
    this.tab = "library";
    this.category = "all";
    this.filter = "all";
    this.showHidden = false;
  }

  async start() {
    await Promise.all([loadStrings(), loadIcons(), this.loadLibrary()]);
    setLanguage(this.settings.language);
    sound.setSoundEnabled(this.settings.sound);
    document.addEventListener("pointerdown", () => sound.unlockAudio(), { capture: true });

    this.play = new PlayScreen(document.querySelector("#play"), this);
    this.importer = new ImportScreen(document.querySelector("#import"), this);
    this.setupHome();
    this.setupSettings();
    this.applyIcons();
    translatePage();
    this.showHome();
    askToKeepData();
    this.registerServiceWorker();
  }

  async loadLibrary() {
    const response = await fetch("data/library.json");
    this.library = await response.json();
    for (const picture of this.library.pictures) picture.greys = picture.palette.map(greyOf);
  }

  // 页面里写 data-icon="名字" 的地方放上像素图标
  applyIcons() {
    for (const element of document.querySelectorAll("[data-icon]")) element.prepend(icon(element.dataset.icon));
  }

  registerServiceWorker() {
    if (!("serviceWorker" in navigator) || location.protocol === "file:") return;
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }

  showScreen(name) {
    for (const screen of document.querySelectorAll(".screen")) screen.hidden = screen.id !== name;
  }

  saveSettings() {
    saveSettings(this.settings);
  }

  projectName(project) {
    // 内置图的作品如果还是默认名字，就按当前语言显示（和桌面版一样）
    if (project.source.startsWith("library:")) {
      const key = `library_${project.source.slice(8)}`;
      if (project.name === tr(key) || project.defaultName) return tr(key);
    }
    return project.name;
  }

  // ---------------------------------------------------------------- 首页

  setupHome() {
    const home = document.querySelector("#home");
    home.querySelector("#home-import").addEventListener("click", () => this.importer.choosePhoto());
    home.querySelector("#home-settings").addEventListener("click", () => this.showSettings());
    for (const tab of home.querySelectorAll("[data-tab]")) {
      tab.addEventListener("click", () => {
        this.tab = tab.dataset.tab;
        this.refreshHome();
      });
    }
    home.querySelector("#home-show-hidden").addEventListener("click", () => {
      this.showHidden = !this.showHidden;
      this.refreshHome();
    });

    const categories = home.querySelector("#home-categories");
    for (const name of ["all", ...this.library.categories]) {
      categories.append(el("button", {
        class: "chip", type: "button", "data-category": name, "data-tr": `category_${name}`,
        onclick: () => {
          this.category = name;
          this.refreshHome();
        },
      }));
    }
    const filters = home.querySelector("#home-filters");
    for (const [name, key] of [["all", "filter_all"], ["in_progress", "filter_in_progress"], ["completed", "filter_completed"]]) {
      filters.append(el("button", {
        class: "chip", type: "button", "data-filter": name, "data-tr": key,
        onclick: () => {
          this.filter = name;
          this.refreshHome();
        },
      }));
    }
  }

  showHome() {
    this.showScreen("home");
    this.refreshHome();
  }

  async refreshHome() {
    const home = document.querySelector("#home");
    for (const tab of home.querySelectorAll("[data-tab]")) tab.classList.toggle("active", tab.dataset.tab === this.tab);
    for (const chip of home.querySelectorAll("[data-category]")) chip.classList.toggle("active", chip.dataset.category === this.category);
    for (const chip of home.querySelectorAll("[data-filter]")) chip.classList.toggle("active", chip.dataset.filter === this.filter);
    home.querySelector("#home-categories").hidden = this.tab !== "library";
    home.querySelector("#home-filters").hidden = this.tab !== "works";

    const projects = await listProjects();
    const grid = home.querySelector("#home-grid");
    grid.replaceChildren();
    let hiddenCount = 0;
    if (this.tab === "library") {
      for (const picture of this.library.pictures) {
        if (this.category !== "all" && picture.category !== this.category) continue;
        const key = `library:${picture.key}`;
        const hidden = this.settings.hidden.includes(key);
        if (hidden) hiddenCount += 1;
        if (hidden && !this.showHidden) continue;
        const project = projects.find((item) => item.source === key);
        grid.append(this.card({
          picture, painted: project?.progress.painted, name: tr(`library_${picture.key}`),
          status: statusText(project), hidden,
          onOpen: () => this.openLibrary(picture),
          onMenu: () => this.libraryMenu(picture, key),
        }));
      }
    } else {
      let shown = projects;
      if (this.filter === "in_progress") shown = shown.filter((project) => !project.completed);
      if (this.filter === "completed") shown = shown.filter((project) => project.completed);
      hiddenCount = shown.filter((project) => this.settings.hidden.includes(`project:${project.id}`)).length;
      if (!this.showHidden) shown = shown.filter((project) => !this.settings.hidden.includes(`project:${project.id}`));
      if (!shown.length) grid.append(el("p", { class: "empty", text: tr("no_works") }));
      for (const project of shown) {
        const picture = project.picture;
        picture.greys = picture.greys || picture.palette.map(greyOf);
        grid.append(this.card({
          picture, painted: project.progress.painted, name: this.projectName(project),
          status: statusText(project), hidden: this.settings.hidden.includes(`project:${project.id}`),
          onOpen: () => this.openProject(project),
          onMenu: () => this.projectMenu(project),
        }));
      }
    }
    const toggle = home.querySelector("#home-show-hidden");
    toggle.hidden = !hiddenCount && !this.showHidden;
    toggle.classList.toggle("active", this.showHidden);
    toggle.textContent = tr("show_hidden", { count: hiddenCount });
  }

  card({ picture, painted, name, status, hidden, onOpen, onMenu }) {
    const thumbnail = el("canvas", { class: "thumbnail" });
    drawThumbnail(thumbnail, picture, painted, picture.greys);
    const more = el("button", { class: "more", type: "button", "aria-label": "…", text: "…" });
    more.addEventListener("click", (event) => {
      event.stopPropagation();
      onMenu();
    });
    const card = el("div", { class: hidden ? "card hidden-card" : "card", role: "button", tabindex: "0" }, [
      el("div", { class: "thumbnail-box" }, [thumbnail]),
      el("div", { class: "card-row" }, [
        el("div", { class: "card-text" }, [el("strong", { text: name }), el("small", { text: status })]),
        more,
      ]),
    ]);
    card.addEventListener("click", onOpen);
    return card;
  }

  async openLibrary(picture) {
    const source = `library:${picture.key}`;
    let project = await findBySource(source);
    if (!project) {
      const { width, height, palette, numbers } = picture;
      project = newProject({ width, height, palette, numbers }, tr(`library_${picture.key}`), source);
      project.defaultName = true;
      await saveProject(project);
    }
    this.openProject(project);
  }

  async openProject(project) {
    const fresh = (await getProject(project.id)) || project;
    this.showScreen("play");
    this.play.open(fresh);
  }

  setHidden(key, hidden) {
    this.settings.hidden = this.settings.hidden.filter((item) => item !== key);
    if (hidden) this.settings.hidden.push(key);
    this.saveSettings();
    this.refreshHome();
  }

  hideButton(key) {
    const hidden = this.settings.hidden.includes(key);
    return { label: tr(hidden ? "unhide" : "hide"), action: () => this.setHidden(key, !hidden) };
  }

  libraryMenu(picture, key) {
    dialog({
      title: tr(`library_${picture.key}`),
      buttons: [
        { label: tr("open_picture"), kind: "primary", action: () => this.openLibrary(picture) },
        this.hideButton(key),
        { label: tr("cancel") },
      ],
    });
  }

  projectMenu(project) {
    const name = this.projectName(project);
    const buttons = [{ label: tr("continue"), kind: "primary", action: () => this.openProject(project) }];
    if (project.completed) {
      buttons.push({ label: tr("export_png"), action: () => exportPicture(project.picture, project.progress.painted, name) });
    }
    buttons.push(
      { label: tr("rename"), action: () => this.rename(project) },
      { label: tr("restart"), action: () => confirmDialog(tr("confirm_restart", { name }), tr("restart"), () => this.restart(project)) },
      this.hideButton(`project:${project.id}`),
      {
        label: tr("delete"), kind: "danger",
        action: () => confirmDialog(tr("confirm_delete", { name }), tr("delete"), () => this.remove(project), { danger: true }),
      },
      { label: tr("cancel") },
    );
    dialog({ title: name, buttons });
  }

  rename(project) {
    const input = el("input", { class: "text-input", type: "text", value: this.projectName(project), maxlength: "60" });
    dialog({
      title: tr("rename"), content: input,
      buttons: [
        { label: tr("cancel") },
        {
          label: tr("ok"), kind: "primary",
          action: async () => {
            const name = input.value.trim();
            if (!name) return;
            project.name = name;
            project.defaultName = false;
            await saveProject(project);
            this.refreshHome();
          },
        },
      ],
    });
    setTimeout(() => input.focus(), 50);
  }

  async restart(project) {
    project.progress = { painted: new Array(project.picture.numbers.length).fill(0), history: [], redo: [] };
    project.completed = false;
    project.ratio = 0;
    await saveProject(project);
    this.refreshHome();
  }

  async remove(project) {
    await deleteProject(project.id);
    this.setHidden(`project:${project.id}`, false);
  }

  // ---------------------------------------------------------------- 设置

  setupSettings() {
    const page = document.querySelector("#settings");
    page.querySelector("#settings-back").addEventListener("click", () => this.showHome());
    const rows = page.querySelector("#settings-rows");
    const choice = (titleKey, options, current, onChoose) => {
      const chips = options.map(([value, labelKey]) => el("button", {
        class: value === current() ? "chip active" : "chip", type: "button", "data-tr": labelKey,
        onclick: () => {
          onChoose(value);
          for (const [index, chip] of chips.entries()) chip.classList.toggle("active", options[index][0] === current());
        },
      }));
      rows.append(el("div", { class: "setting" }, [el("h3", { "data-tr": titleKey }), el("div", { class: "chips" }, chips)]));
    };
    choice("language", [["zh", "web_language_zh"], ["en", "web_language_en"]], () => this.settings.language, (value) => {
      this.settings.language = value;
      this.saveSettings();
      setLanguage(value);
      translatePage();
      page.querySelector("#settings-version").textContent = tr("version", { version: VERSION });
      this.refreshHome();
    });
    choice("wrong_mode", [["block", "wrong_block"], ["allow", "wrong_allow"]], () => this.settings.wrongMode, (value) => {
      this.settings.wrongMode = value;
      this.saveSettings();
    });
    choice("sound", [[true, "on"], [false, "off"]], () => this.settings.sound, (value) => {
      this.settings.sound = value;
      this.saveSettings();
      sound.setSoundEnabled(value);
    });
    rows.append(el("div", { class: "setting" }, [
      el("h3", { "data-tr": "web_install_title" }),
      el("p", { class: "note", "data-tr": "web_install_ios" }),
      el("p", { class: "note", "data-tr": "web_install_android" }),
    ]));
    // Android 的 Chrome 可以直接弹出"安装"
    window.addEventListener("beforeinstallprompt", (event) => {
      event.preventDefault();
      const install = button(tr("web_install_button"), { kind: "primary", onClick: () => event.prompt() });
      rows.append(install);
    });
    page.querySelector("#settings-version").textContent = tr("version", { version: VERSION });
  }

  showSettings() {
    this.showScreen("settings");
  }
}

function statusText(project) {
  if (!project || !project.ratio) return tr("not_started");
  if (project.completed) return tr("completed");
  return tr("percent_done", { percent: Math.floor(project.ratio * 100) });
}

const app = new App();
window.colorNumber = app;          // 方便在浏览器的开发者工具里查看（调试用）
app.start().catch((error) => {
  document.body.textContent = `Color Number could not start: ${error.message || error}`;
});
