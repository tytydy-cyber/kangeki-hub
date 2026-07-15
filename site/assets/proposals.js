(() => {
  "use strict";

  const app = document.getElementById("app");

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  function card(p) {
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

  function section(label, note, items) {
    if (!items || !items.length) return "";
    return `<h2 class="section">${esc(label)}${note ? ` <span class="count">${esc(note)}</span>` : ""}</h2>` +
      items.map(card).join("");
  }

  fetch("data/proposals.json")
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then((d) => {
      let html = "";
      const winLabel = d.window ? d.window.label : "";
      html += section("直近1ヶ月の未登録公演", winLabel, d.nextMonth);
      html += section("特筆（期間を問わず）", "", d.special);
      if (!d.nextMonth?.length && !d.special?.length) {
        html += `<p class="empty">現在の提案はありません</p>`;
      }
      if (d.notes) html += `<p class="digest-notes">${esc(d.notes)}</p>`;
      app.innerHTML = html;
      document.getElementById("meta").textContent = `生成日 ${d.generatedAt}`;
    })
    .catch((err) => {
      app.innerHTML = `<p class="empty">提案を読み込めませんでした（${esc(err.message)}）</p>`;
    });
})();
