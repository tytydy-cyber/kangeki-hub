(() => {
  "use strict";

  const app = document.getElementById("app");
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
  const today = new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10);

  function matchingEvents(item, events) {
    return events.filter((event) => {
      if (event.end < today) return false;
      return item.matchCompanies?.includes(event.company) ||
        item.matchTitles?.some((term) => event.title.includes(term) || event.note?.includes(term));
    });
  }

  function itemCard(item, events) {
    const matches = matchingEvents(item, events);
    const schedule = matches.length
      ? `<div class="follow-schedule"><strong>登録済み</strong>${matches.slice(0, 3).map((event) =>
          `<a href="${esc(event.url || "#")}" ${event.url ? 'target="_blank" rel="noopener"' : ""}>${esc(event.title)} <span>${esc(event.start)}</span></a>`
        ).join("")}</div>`
      : `<p class="follow-empty">カレンダーに今後の登録なし</p>`;
    const latest = item.latest || {};
    const confirmed = latest.status === "確認済み";
    const status = confirmed && latest.checkedAt
      ? `最終確認 ${esc(latest.checkedAt)}`
      : esc(latest.status || "未確認");
    const checkedAt = confirmed ? "" : `<span>${esc(latest.checkedAt || "未確認")}</span>`;
    return `<article class="follow-card">
      <div class="follow-head"><span class="eyebrow">${esc(item.type)}</span><span class="watch-status">${status}</span></div>
      <h2><a href="${esc(item.url)}" target="_blank" rel="noopener">${esc(item.name)}</a></h2>
      <p>${esc(item.reason)}</p>
      <div class="latest-note">${checkedAt}${esc(latest.summary || "まだ確認結果がありません。")}${latest.url ? ` <a href="${esc(latest.url)}" target="_blank" rel="noopener">確認元</a>` : ""}</div>
      ${schedule}
    </article>`;
  }

  Promise.all([
    fetch("data/watchlist.json").then((r) => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))),
    fetch("data/events.json").then((r) => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))),
  ]).then(([watchlist, eventData]) => {
    app.innerHTML = `<div class="page-intro"><h1>${watchlist.items.length}件をフォロー</h1><p>個別の団体やイベントを直接追います。予定が決まった対象は公演終了まで週次確認を休止します。</p></div>` +
      `<div class="follow-grid">${watchlist.items.map((item) => itemCard(item, eventData.events)).join("")}</div>`;
    document.getElementById("meta").textContent = `最終確認 ${watchlist.generatedAt}`;
  }).catch((err) => {
    app.innerHTML = `<p class="empty">フォロー情報を読み込めませんでした（${esc(err.message)}）</p>`;
  });
})();
