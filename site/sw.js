/* 松田観劇カレンダー Service Worker
 * - アプリシェル（HTML/CSS/JS/アイコン）: precache + network-first（オンライン時は最新、オフライン時はキャッシュ）
 * - データ（data/*.json）: stale-while-revalidate（即表示しつつ裏で更新）
 * パスはすべて sw.js からの相対で解決するため、ルート配信でも /kangeki-hub/ 配信でも動く。
 */
const VERSION = "v1";
const SHELL_CACHE = `shell-${VERSION}`;
const DATA_CACHE = `data-${VERSION}`;

// sw.js のあるディレクトリ（scope）を基準に絶対URL化する
const base = new URL("./", self.location).href;
const url = (p) => new URL(p, base).href;

const SHELL = [
  "./",
  "index.html",
  "digest.html",
  "proposals.html",
  "assets/style.css",
  "assets/app.js",
  "assets/digest.js",
  "assets/proposals.js",
  "assets/register-sw.js",
  "manifest.json",
  "assets/icons/icon-192.png",
  "assets/icons/icon-512.png",
  "assets/icons/icon-maskable-512.png",
].map(url);

// データも初回インストール時に取得しておく（ベストエフォート。1つ欠けてもインストールは失敗させない）
const DATA_FILES = [
  "data/events.json",
  "data/digest.json",
  "data/proposals.json",
  "data/companies.json",
].map(url);

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const shell = await caches.open(SHELL_CACHE);
      await shell.addAll(SHELL); // 必須。失敗したらインストール失敗
      const data = await caches.open(DATA_CACHE);
      await Promise.all(
        DATA_FILES.map((u) =>
          fetch(u).then((res) => (res.ok ? data.put(u, res) : null)).catch(() => null)
        )
      );
      await self.skipWaiting();
    })()
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k !== SHELL_CACHE && k !== DATA_CACHE)
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

function isData(reqUrl) {
  return reqUrl.pathname.includes("/data/") && reqUrl.pathname.endsWith(".json");
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const reqUrl = new URL(req.url);
  if (reqUrl.origin !== self.location.origin) return; // 外部（Google Maps等）は素通し

  if (isData(reqUrl)) {
    // stale-while-revalidate: キャッシュを即返しつつ裏で更新
    event.respondWith(
      caches.open(DATA_CACHE).then(async (cache) => {
        const cached = await cache.match(req);
        const network = fetch(req)
          .then((res) => {
            if (res && res.ok) cache.put(req, res.clone());
            return res;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  // アプリシェル/ナビゲーション: network-first、失敗時はキャッシュ
  event.respondWith(
    fetch(req)
      .then((res) => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(SHELL_CACHE).then((c) => c.put(req, copy));
        }
        return res;
      })
      .catch(async () => {
        const cached = await caches.match(req);
        if (cached) return cached;
        if (req.mode === "navigate") return caches.match(url("index.html"));
        return Response.error();
      })
  );
});
