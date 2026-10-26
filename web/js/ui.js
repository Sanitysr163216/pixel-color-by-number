// 界面上到处用到的小工具：创建元素、图标、按钮、弹窗、长按。

import { tr } from "./i18n.js";

let icons = {};

export async function loadIcons() {
  const response = await fetch("data/icons.json");
  icons = await response.json();
}

// 像素小图标（来自 colornumber/core/icon_art.py），颜色跟着文字颜色
export function icon(name) {
  const span = document.createElement("span");
  span.className = "icon";
  span.innerHTML = icons[name] || "";
  return span;
}

// el("button", {class: "chip", onclick: ...}, ["文字", 子元素...])
export function el(tag, props = {}, children = []) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "class") element.className = value;
    else if (key.startsWith("on")) element.addEventListener(key.slice(2), value);
    else if (key === "text") element.textContent = value;
    else element.setAttribute(key, value);
  }
  for (const child of [].concat(children)) {
    if (child !== null && child !== undefined) element.append(child);
  }
  return element;
}

export function button(label, { iconName, kind = "", onClick, title } = {}) {
  const element = el("button", { class: `button ${kind}`.trim(), type: "button" });
  if (iconName) element.append(icon(iconName));
  if (label) element.append(el("span", { text: label }));
  if (title) element.setAttribute("aria-label", title);
  if (onClick) element.addEventListener("click", onClick);
  return element;
}

// 弹窗：buttons 是 [{label, kind: "primary" | "danger" | "", action, keepOpen}]
export function dialog({ title, text, content, buttons = [] }) {
  const box = el("div", { class: "dialog", role: "dialog", "aria-modal": "true" });
  if (title) box.append(el("h2", { text: title }));
  if (text) box.append(el("p", { text }));
  if (content) box.append(content);
  const row = el("div", { class: buttons.length > 2 ? "dialog-buttons column" : "dialog-buttons" });
  const overlay = el("div", { class: "overlay" }, [box]);
  const close = () => overlay.remove();
  for (const spec of buttons) {
    row.append(button(spec.label, {
      kind: spec.kind || "",
      onClick: () => {
        if (!spec.keepOpen) close();
        if (spec.action) spec.action();
      },
    }));
  }
  if (buttons.length) box.append(row);
  document.body.append(overlay);
  return { close, box };
}

export function confirmDialog(text, yesLabel, onYes, { danger = false, title } = {}) {
  dialog({
    title, text,
    buttons: [
      { label: tr("cancel") },
      { label: yesLabel || tr("ok"), kind: danger ? "danger" : "primary", action: onYes },
    ],
  });
}

// 一行短短的提示，几秒后自己消失
export function toast(text) {
  const element = el("div", { class: "toast", text });
  document.body.append(element);
  setTimeout(() => element.classList.add("show"), 10);
  setTimeout(() => element.remove(), 2600);
}

// 长按：按住 time 毫秒触发 onLong（按钮上有一条进度条），短按触发 onTap
export function longPress(element, { onTap, onLong, time = 600 }) {
  let timer = null;
  let fired = false;
  const cancel = () => {
    clearTimeout(timer);
    timer = null;
    element.classList.remove("pressing");
  };
  element.addEventListener("pointerdown", () => {
    fired = false;
    element.classList.add("pressing");
    element.style.setProperty("--press-time", `${time}ms`);
    timer = setTimeout(() => {
      fired = true;
      cancel();
      onLong();
    }, time);
  });
  element.addEventListener("pointerup", () => {
    const wasPressing = timer !== null;
    cancel();
    if (wasPressing && !fired && onTap) onTap();
  });
  element.addEventListener("pointerleave", cancel);
  element.addEventListener("pointercancel", cancel);
  element.addEventListener("contextmenu", (event) => event.preventDefault());
}

// 在一个 canvas 上画缩略图：填了的格子是颜色，没填的是浅灰色
export function drawThumbnail(canvas, picture, painted, greys) {
  const { width, height } = picture;
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  const image = context.createImageData(width, height);
  picture.numbers.forEach((answer, idx) => {
    const value = painted ? painted[idx] : 0;
    const color = value ? picture.palette[value - 1] : greys[answer - 1];
    image.data.set([color[0], color[1], color[2], 255], idx * 4);
  });
  context.putImageData(image, 0, 0);
}
