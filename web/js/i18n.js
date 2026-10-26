// 中英文界面文字。文字本身来自 colornumber/core/i18n.py（build_web.py 导出成 data/strings.json），
// 桌面版和网页版用的是同一份翻译。

let strings = {};
let language = "en";

export async function loadStrings() {
  const response = await fetch("data/strings.json");
  strings = await response.json();
}

export function setLanguage(value) {
  language = value;
  document.documentElement.lang = value === "zh" ? "zh-Hans" : "en";
}

export function getLanguage() {
  return language;
}

// 取出 key 对应的文字，把 {名字} 换成 values 里的值；找不到翻译时退回中文，再找不到就显示 key
export function tr(key, values = {}) {
  const entry = strings[key];
  if (!entry) return key;
  const text = entry[language] || entry.zh;
  return text.replace(/\{(\w+)\}/g, (whole, name) => (name in values ? values[name] : whole));
}

// 页面里写 data-tr="键" 的元素，换语言时自动换文字
export function translatePage(root = document) {
  for (const element of root.querySelectorAll("[data-tr]")) {
    element.textContent = tr(element.dataset.tr);
  }
  for (const element of root.querySelectorAll("[data-tr-placeholder]")) {
    element.placeholder = tr(element.dataset.trPlaceholder);
  }
}
