// 存档：作品存在浏览器的 IndexedDB 里（空间比 localStorage 大很多），设置存在 localStorage 里。
//
// 一个作品（project）是这样的对象：
// {id, name, source, created, updated, picture: {width, height, palette, numbers},
//  progress: {painted, history, redo}, completed, ratio}
// source 是 "library:<图的键>" 或 "import"。

const DB_NAME = "colornumber";
const STORE = "projects";
let database = null;

function open() {
  if (database) return Promise.resolve(database);
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: "id" });
    request.onsuccess = () => {
      database = request.result;
      resolve(database);
    };
    request.onerror = () => reject(request.error);
  });
}

// 在一个"事务"里对作品表做一件事，返回结果
async function run(mode, action) {
  const db = await open();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE, mode);
    const request = action(transaction.objectStore(STORE));
    transaction.oncomplete = () => resolve(request ? request.result : undefined);
    transaction.onerror = () => reject(transaction.error);
  });
}

export async function listProjects() {
  const projects = await run("readonly", (store) => store.getAll());
  return projects.sort((a, b) => b.updated - a.updated);      // 最近玩的在前面
}

export function getProject(id) {
  return run("readonly", (store) => store.get(id));
}

export function saveProject(project) {
  project.updated = Date.now();
  return run("readwrite", (store) => store.put(project));
}

export function deleteProject(id) {
  return run("readwrite", (store) => store.delete(id));
}

export async function findBySource(source) {
  const projects = await listProjects();
  return projects.find((project) => project.source === source) || null;
}

export function newProject(picture, name, source) {
  const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  return {
    id, name, source, picture,
    created: Date.now(), updated: Date.now(),
    progress: { painted: new Array(picture.numbers.length).fill(0), history: [], redo: [] },
    completed: false, ratio: 0,
  };
}

// 请浏览器不要在空间紧张时自动清掉存档（加到主屏幕的网页 App 一般会被允许）
export function askToKeepData() {
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
}

// ---------------------------------------------------------------- 设置

const SETTINGS_KEY = "colornumber-settings";

export function loadSettings() {
  const defaults = {
    language: (navigator.language || "en").toLowerCase().startsWith("zh") ? "zh" : "en",
    wrongMode: "block",
    sound: true,
    hidden: [],
  };
  try {
    return { ...defaults, ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}") };
  } catch {
    return defaults;
  }
}

export function saveSettings(settings) {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    // 隐私模式下可能存不了：这次照常玩，只是下次打开会恢复默认设置
  }
}
