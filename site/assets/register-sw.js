// Service Worker を登録してオフライン対応を有効にする。
// register() のURLはドキュメントのベースURL基準で解決されるため、
// ルート配信でも /kangeki-hub/ 配信でも sw.js が正しいscopeで登録される。
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch((err) => {
      console.warn("SW registration failed:", err);
    });
  });
}
