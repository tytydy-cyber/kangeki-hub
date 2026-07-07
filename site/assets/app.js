(() => {
  "use strict";

  const app = document.getElementById("app");
  const searchInput = document.getElementById("search");
  const tabs = document.querySelectorAll(".tab");
  const DOW = ["日", "月", "火", "水", "木", "金", "土"];

  let events = [];
  let view = "now";
  let query = "";

  // JSTの今日（閲覧環境のタイムゾーンに依存しない）
  const todayStr = new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10);
  const todayYear = Number(todayStr.slice(0, 4));

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  function fmtDate(iso, withYear) {
    const [y, m, d] = iso.split("-").map(Number);
    const dow = DOW[new Date(Date.UTC(y, m - 1, d)).getUTCDay()];
    return `${withYear ? y + "/" : ""}${m}/${d}(${dow})`;
  }

  function fmtRange(ev) {
    const withYear = Number(ev.start.slice(0, 4)) !== todayYear;
    if (ev.start === ev.end) return fmtDate(ev.start, withYear);
    return `${fmtDate(ev.start, withYear)} 〜 ${fmtDate(ev.end, withYear)}`;
  }

  function daysFromToday(iso) {
    return Math.round((Date.parse(iso) - Date.parse(todayStr)) / 86400000);
  }

  function card(ev, badge) {
    const title = ev.url
      ? `<a href="${esc(ev.url)}" target="_blank" rel="noopener">${esc(ev.title)}</a>`
      : esc(ev.title);
    const parts = [fmtRange(ev)];
    if (ev.venue) parts.push(esc(ev.venue));
    return `<div class="card">
      <div class="title">${title}${badge ? `<span class="badge">${esc(badge)}</span>` : ""}</div>
      <div class="info">${parts.join(" ・ ")}</div>
    </div>`;
  }

  function section(label, items, cards) {
    return `<h2 class="section">${label} <span class="count">${items.length}件</span></h2>` +
      (items.length ? cards : `<p class="empty">該当なし</p>`);
  }

  function matches(ev) {
    if (!query) return true;
    return [ev.title, ev.company, ev.work, ev.venue, ev.note]
      .filter(Boolean)
      .some((f) => f.toLowerCase().includes(query));
  }

  function renderNow(list) {
    const ongoing = list
      .filter((e) => e.start <= todayStr && todayStr <= e.end)
      .sort((a, b) => a.end.localeCompare(b.end));
    const upcoming = list.filter((e) => e.start > todayStr);

    const ongoingCards = ongoing
      .map((e) => {
        const left = daysFromToday(e.end);
        return card(e, left === 0 ? "本日千秋楽" : `千秋楽まで${left}日`);
      })
      .join("");
    const upcomingCards = upcoming
      .map((e) => {
        const until = daysFromToday(e.start);
        return card(e, until <= 14 ? `あと${until}日で開幕` : "");
      })
      .join("");

    return section("開催中", ongoing, ongoingCards) + section("今後", upcoming, upcomingCards);
  }

  function renderArchive(list) {
    const past = list.filter((e) => e.end < todayStr).reverse();
    if (!past.length) return `<p class="empty">該当なし</p>`;
    const byYear = new Map();
    for (const e of past) {
      const y = e.start.slice(0, 4);
      if (!byYear.has(y)) byYear.set(y, []);
      byYear.get(y).push(e);
    }
    let html = "";
    for (const [y, items] of byYear) {
      html += section(`${y}年`, items, items.map((e) => card(e, "")).join(""));
    }
    return html;
  }

  function render() {
    const list = events.filter(matches);
    app.innerHTML = view === "now" ? renderNow(list) : renderArchive(list);
  }

  tabs.forEach((tab) =>
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.toggle("active", t === tab));
      view = tab.dataset.view;
      render();
    })
  );

  searchInput.addEventListener("input", () => {
    query = searchInput.value.trim().toLowerCase();
    render();
  });

  fetch("data/events.json")
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then((data) => {
      events = data.events;
      document.getElementById("meta").textContent =
        `全${data.count}件 ・ 最終更新 ${data.generatedAt.slice(0, 16).replace("T", " ")}`;
      render();
    })
    .catch((err) => {
      app.innerHTML = `<p class="empty">データを読み込めませんでした（${esc(err.message)}）</p>`;
    });
})();
