(() => {
  "use strict";

  const app = document.getElementById("app");

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  const compact = (s) => String(s || "").normalize("NFKC").toLowerCase().replace(/[\s　・･]/g, "");

  function isFollowTarget(p, watchlist) {
    const company = compact(p.company);
    const title = compact(p.title);
    return (watchlist.items || []).some((item) => {
      const companies = item.matchCompanies || [];
      const titles = item.matchTitles || [];
      return companies.some((name) => compact(name) === company) ||
        titles.some((name) => title.includes(compact(name)));
    });
  }

  function card(p, number, followed) {
    const title = p.url
      ? `<a href="${esc(p.url)}">${esc(p.title)}</a>`
      : esc(p.title);
    const parts = [];
    if (p.dates) parts.push(`<span class="date">${esc(p.dates)}</span>`);
    if (p.venue) parts.push(`<span>${esc(p.venue)}</span>`);
    const flags = [p.featured ? "注目作" : "", followed ? "フォロー対象" : ""].filter(Boolean);
    return `<div class="card${p.featured ? " proposal-featured" : ""}">
      <div class="proposal-heading"><div class="title proposal-title"><span class="proposal-number" aria-label="提案 ${number}">${String(number).padStart(2, "0")}</span>${title}</div>
      ${flags.length ? `<div class="proposal-flags">${flags.map((flag) => `<span>${esc(flag)}</span>`).join("")}</div>` : ""}</div>
      <div class="info">${parts.join("")}</div>
      <div class="reason">${esc(p.reason)}</div>
    </div>`;
  }

  function section(label, items, watchlist) {
    if (!items || !items.length) return "";
    return `<h2 class="section">${esc(label)} <span class="count">${items.length}件</span></h2>` +
      items.map((item, index) => card(item, index + 1, isFollowTarget(item, watchlist))).join("");
  }

  Promise.all([fetch("data/proposals.json"), fetch("data/watchlist.json")])
    .then(async ([proposals, watchlist]) => {
      if (!proposals.ok || !watchlist.ok) throw new Error(`HTTP ${proposals.status}/${watchlist.status}`);
      return [await proposals.json(), await watchlist.json()];
    })
    .then(([d, watchlist]) => {
      const items = d.items || [...(d.nextMonth || []), ...(d.special || [])];
      let html = `<div class="page-intro"><h1>今週の候補</h1><p>日程に関係なく、未登録の公演を一覧にしています。「注目作」は観劇記録との一致が特に強いもの、「フォロー対象」は継続して追っている団体・イベントです。</p></div>`;
      html += section("候補", items, watchlist);
      if (!items.length) {
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
