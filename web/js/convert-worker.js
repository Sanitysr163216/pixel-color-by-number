// 后台线程：加载 Pyodide（浏览器里的 Python）和 numpy、Pillow，运行桌面版的 converter.py。
// 放在后台线程里，转换时页面不会卡住。

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
const PYTHON_FILES = [
  "colornumber/__init__.py",
  "colornumber/core/__init__.py",
  "colornumber/core/picture.py",
  "colornumber/core/converter.py",
  "web_convert.py",
];

let ready = null;
let loaded = false;
let pyodide = null;

function progress(stage) {
  postMessage({ type: "progress", stage });
}

async function setup() {
  progress("python");
  importScripts(`${PYODIDE_URL}pyodide.js`);
  pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  progress("packages");
  await pyodide.loadPackage(["numpy", "pillow"]);
  progress("code");
  const home = "/home/pyodide/";
  for (const name of PYTHON_FILES) {
    const response = await fetch(`../py/${name}`);
    const text = await response.text();
    pyodide.FS.mkdirTree(home + name.split("/").slice(0, -1).join("/"));
    pyodide.FS.writeFile(home + name, text);
  }
  pyodide.runPython(`import sys\nif "${home}" not in sys.path: sys.path.insert(0, "${home}")\nimport web_convert`);
  loaded = true;
  progress("ready");
}

onmessage = async (event) => {
  const { id, action, data } = event.data;
  try {
    if (!ready) ready = setup();
    await ready;
    const module = pyodide.pyimport("web_convert");
    let result;
    if (action === "load") {
      pyodide.FS.writeFile("/tmp/photo", new Uint8Array(data));
      result = JSON.parse(module.load("/tmp/photo"));
    } else if (action === "convert") {
      result = JSON.parse(module.convert(JSON.stringify(data)));
    } else if (action === "recommend") {
      result = module.recommend(JSON.stringify(data));
    } else if (action === "warmup") {
      result = true;
    }
    postMessage({ id, result });
  } catch (error) {
    if (!loaded) ready = null;           // 加载失败（比如没网）时，下次重新试
    postMessage({ id, error: String(error && error.message ? error.message : error) });
  }
};
