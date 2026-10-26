// 离线缓存（Service Worker）：第一次打开时把整个游戏存到手机里，以后没有网络也能玩。
// 版本号变了（发布了新版本）就重新缓存，并删掉旧版本的缓存。

const VERSION = "__VERSION__";
const APP_CACHE = `colornumber-${VERSION}`;
const PYODIDE_CACHE = "pyodide-0.27.7";       // 照片转换用的 Python，第一次导入照片时才下载
const FILES = "__FILES__";                     // build_web.py 会换成所有文件的列表

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(APP_CACHE).then((cache) => cache.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(names
        .filter((name) => name !== APP_CACHE && name !== PYODIDE_CACHE)
        .map((name) => caches.delete(name))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  // Pyodide：先看缓存，没有再下载并存起来
  if (url.hostname === "cdn.jsdelivr.net" && url.pathname.startsWith("/pyodide/")) {
    event.respondWith(caches.open(PYODIDE_CACHE).then(async (cache) => {
      const cached = await cache.match(request);
      if (cached) return cached;
      const response = await fetch(request);
      if (response.ok) cache.put(request, response.clone());
      return response;
    }));
    return;
  }
  if (url.origin !== location.origin) return;
  // 游戏本身的文件：有网时取最新的（顺便更新缓存），没网时用缓存里的，所以离线也能玩。
  // cache: "no-cache" 让浏览器每次都问一下服务器文件有没有变（没变时服务器只回一句"没变"，很快），
  // 这样发布新版本后马上就能用上，不会还在用浏览器自己存的旧文件
  event.respondWith(fetch(request, { cache: "no-cache" }).then((response) => {
    if (response.ok) {
      const copy = response.clone();
      caches.open(APP_CACHE).then((cache) => cache.put(request, copy));
    }
    return response;
  }).catch(() => caches.match(request, { ignoreSearch: true })));
});
