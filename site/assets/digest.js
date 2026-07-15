(() => {
  "use strict";

  const app = document.getElementById("app");
  const MONTHS = ["", "1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  function statBlock(stats) {
    return `<div class="stats">` +
      stats
        .map((s) => `<div class="stat"><span class="v">${esc(s.value)}</span><span class="l">${esc(s.label)}</span></div>`)
        .join("") +
      `</div>`;
  }

  // 横棒グラフ（ラベル + 値 + バー）
  function barChart(rows) {
    const max = Math.max(1, ...rows.map((r) => r.value));
    return `<div class="bars">` +
      rows
        .map(
          (r) => `<div class="bar-row">
            <span class="bar-label">${esc(r.label)}</span>
            <span class="bar-track"><span class="bar-fill" style="width:${(r.value / max) * 100}%"></span></span>
            <span class="bar-val">${esc(r.value)}</span>
          </div>`
        )
        .join("") +
      `</div>`;
  }

  function rankList(items) {
    return `<ol class="ranklist">` +
      items
        .map((c) => `<li><span class="rk-name">${esc(c.name)}</span><span class="rk-count">${esc(c.count)}</span></li>`)
        .join("") +
      `</ol>`;
  }

  fetch("data/digest.json")
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then((d) => {
      let html = "";

      if (d.overview) {
        html += `<h2 class="section">概観</h2>`;
        if (d.overview.stats) html += statBlock(d.overview.stats);
        if (d.overview.text) html += `<p class="digest-text">${esc(d.overview.text)}</p>`;
      }

      if (d.byYear && d.byYear.length) {
        html += `<h2 class="section">年別の登録数</h2>`;
        html += barChart(d.byYear.map((y) => ({ label: `${y.year}年`, value: y.count })));
      }

      if (d.monthHistogram) {
        html += `<h2 class="section">開催月の分布 <span class="count">通算</span></h2>`;
        html += barChart(
          Object.keys(d.monthHistogram).map((m) => ({ label: MONTHS[Number(m)], value: d.monthHistogram[m] }))
        );
      }

      if (d.topCompanies && d.topCompanies.length) {
        html += `<h2 class="section">よく観る劇団・団体 <span class="count">通算トップ${d.topCompanies.length}</span></h2>`;
        html += rankList(d.topCompanies);
      }

      if (d.recentCompanies && d.recentCompanies.length) {
        html += `<h2 class="section">直近180日で登録が多い劇団</h2>`;
        html += rankList(d.recentCompanies);
      }

      if (d.topVenues && d.topVenues.length) {
        html += `<h2 class="section">よく行く会場 <span class="count">通算トップ${d.topVenues.length}</span></h2>`;
        html += rankList(d.topVenues);
      }

      if (d.notes) html += `<p class="digest-notes">${esc(d.notes)}</p>`;
      app.innerHTML = html;
      document.getElementById("meta").textContent = `生成日 ${d.generatedAt}`;
    })
    .catch((err) => {
      app.innerHTML = `<p class="empty">ダイジェストを読み込めませんでした（${esc(err.message)}）</p>`;
    });
})();
