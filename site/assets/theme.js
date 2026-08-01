// テーマ切替: 自動（端末設定）→ライト→ダーク→自動 の3状態をボタン1つで循環する。
// 選択はlocalStorageに保存し、次回訪問時も維持する。
(function () {
  "use strict";
  var KEY = "kangeki-theme";
  var root = document.documentElement;
  var btn;

  function updateButton(mode) {
    if (!btn) return;
    var icon = mode === "light" ? "☀️" : mode === "dark" ? "🌙" : "🌓";
    var label =
      mode === "light"
        ? "ライト表示中（タップでダークに切替）"
        : mode === "dark"
        ? "ダーク表示中（タップで自動に切替）"
        : "自動（端末設定に追従・タップでライトに切替）";
    btn.textContent = icon;
    btn.setAttribute("aria-label", label);
    btn.title = label;
  }

  function apply(mode) {
    if (mode === "light" || mode === "dark") root.dataset.theme = mode;
    else delete root.dataset.theme;
    updateButton(mode);
  }

  function next(mode) {
    if (mode === "light") return "dark";
    if (mode === "dark") return "auto";
    return "light";
  }

  function readSaved() {
    try {
      return localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    btn = document.getElementById("theme-toggle");
    if (!btn) return;
    updateButton(readSaved() || "auto");
    btn.addEventListener("click", function () {
      var mode = next(readSaved() || "auto");
      apply(mode);
      try {
        if (mode === "auto") localStorage.removeItem(KEY);
        else localStorage.setItem(KEY, mode);
      } catch (e) {
        /* localStorage無効でも表示切替自体は機能する */
      }
    });
  });
})();
