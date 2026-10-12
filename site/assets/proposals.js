(() => {
  "use strict";

  const app = document.getElementById("app");

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  function card(p, number) {
    const title = p.url
      ? `<a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.title)}</a>`
      : esc(p.title);
    const parts = [];
    if (p.dates) parts.push(`<span class="date">${esc(p.dates)}</span>`);
    if (p.venue) parts.push(`<span>${esc(p.venue)}</span>`);
    return `<div class="card">
      <div class="title proposal-title"><span class="proposal-number" aria-label="提案 ${number}">${String(number).padStart(2, "0")}</span>${title}</div>
      <div class="info">${parts.join("")}</div>
      <div class="reason">${esc(p.reason)}</div>
    </div>`;
  }

  function section(label, note, items, startAt) {
    if (!items || !items.length) return "";
    return `<h2 class="section">${esc(label)}${note ? ` <span class="count">${esc(note)}</span>` : ""}</h2>` +
      items.map((item, index) => card(item, startAt + index)).join("");
  }

  fetch("data/proposals.json")
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then((d) => {
      let html = `<div class="page-intro"><span class="eyebrow">WEEKLY PICKS</span><h1>今週の候補</h1><p>カレンダー未登録の公演だけを、公開情報で確認して掲載しています。</p></div>`;
      const winLabel = d.window ? d.window.label : "";
      html += section("これから約6週間", winLabel, d.nextMonth, 1);
      html += section("特筆（期間を問わず）", "", d.special, (d.nextMonth?.length || 0) + 1);
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
