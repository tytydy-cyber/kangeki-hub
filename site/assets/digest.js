(() => {
  "use strict";

  const app = document.getElementById("app");
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

  function rankList(items, value) {
    return `<ol class="ranklist">` +
      items
        .map((c) => `<li><span class="rk-name">${esc(c.name)}</span><span class="rk-count">${esc(value ? value(c) : c.count)}</span></li>`)
        .join("") +
      `</ol>`;
  }

  fetch("data/digest.json")
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then((d) => {
      let html = `<div class="page-intro"><h1>関心の変化</h1><p>累積ランキングではなく、最近何を登録し始め、何を追い続けているかを見ます。</p></div>`;

      if (d.overview) {
        html += `<h2 class="section">概観</h2>`;
        if (d.overview.stats) html += statBlock(d.overview.stats);
        if (d.overview.text) html += `<p class="digest-text">${esc(d.overview.text)}</p>`;
      }

      if (d.comparison) {
        html += `<h2 class="section">90日間の変化</h2>`;
        html += barChart([
          { label: "直近", value: d.comparison.current },
          { label: "その前", value: d.comparison.previous },
        ]);
        html += `<p class="digest-notes">直近 ${esc(d.comparison.currentLabel)} ／ その前 ${esc(d.comparison.previousLabel)}</p>`;
      }

      if (d.registrationPace?.length) {
        html += `<h2 class="section">登録ペース <span class="count">直近1年</span></h2>`;
        html += barChart(d.registrationPace.map((m) => ({ label: m.month.slice(2).replace("-", "/"), value: m.count })));
      }

      if (d.momentum?.length) {
        html += `<h2 class="section">関心が強まった団体 <span class="count">前の90日比</span></h2>`;
        html += rankList(d.momentum, (c) => `${c.current}公演（${c.delta > 0 ? "+" : ""}${c.delta}）`);
      }

      if (d.discoveries?.length) {
        html += `<h2 class="section">初めて登録した団体 <span class="count">直近90日</span></h2>`;
        html += rankList(d.discoveries, (c) => `${c.count}公演`);
      }

      if (d.recentTop?.length) {
        html += `<h2 class="section">継続して追っている団体 <span class="count">直近1年</span></h2>`;
        html += rankList(d.recentTop, (c) => `${c.count}公演`);
      }

      if (d.notes) html += `<p class="digest-notes">${esc(d.notes)}</p>`;
      app.innerHTML = html;
      document.getElementById("meta").textContent = `${d.cadence || "更新"} ・ 最終生成 ${d.generatedAt}`;
    })
    .catch((err) => {
      app.innerHTML = `<p class="empty">ダイジェストを読み込めませんでした（${esc(err.message)}）</p>`;
    });
})();
