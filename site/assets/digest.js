(() => {
  "use strict";

  const app = document.getElementById("app");

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  function proposalCard(p) {
    const title = p.url
      ? `<a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.title)}</a>`
      : esc(p.title);
    const parts = [];
    if (p.dates) parts.push(esc(p.dates));
    if (p.venue) parts.push(esc(p.venue));
    return `<div class="card">
      <div class="title">${title}</div>
      <div class="info">${parts.join(" ・ ")}</div>
      <div class="reason">${esc(p.reason)}</div>
    </div>`;
  }

  function watchCard(w) {
    const name = w.url
      ? `<a href="${esc(w.url)}" target="_blank" rel="noopener">${esc(w.name)}</a>`
      : esc(w.name);
    return `<div class="card">
      <div class="title">${name}</div>
      <div class="reason">${esc(w.note)}</div>
    </div>`;
  }

  fetch("data/digest.json")
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then((d) => {
      let html = "";
      if (d.summary) {
        html += `<h2 class="section">傾向サマリ</h2>`;
        if (d.summary.stats) {
          html += `<div class="stats">` +
            d.summary.stats
              .map((s) => `<div class="stat"><span class="v">${esc(s.value)}</span><span class="l">${esc(s.label)}</span></div>`)
              .join("") +
            `</div>`;
        }
        if (d.summary.text) html += `<p class="digest-text">${esc(d.summary.text)}</p>`;
      }
      if (d.proposals && d.proposals.length) {
        html += `<h2 class="section">今週の提案 <span class="count">${d.proposals.length}件</span></h2>`;
        html += d.proposals.map(proposalCard).join("");
      }
      if (d.watchlist && d.watchlist.length) {
        html += `<h2 class="section">ウォッチ中（発表待ち）</h2>`;
        html += d.watchlist.map(watchCard).join("");
      }
      if (d.notes) html += `<p class="digest-notes">${esc(d.notes)}</p>`;
      app.innerHTML = html;
      document.getElementById("meta").textContent = `生成日 ${d.generatedAt}`;
    })
    .catch((err) => {
      app.innerHTML = `<p class="empty">ダイジェストを読み込めませんでした（${esc(err.message)}）</p>`;
    });
})();
