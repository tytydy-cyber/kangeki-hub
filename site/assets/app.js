(() => {
  "use strict";

  const app = document.getElementById("app");
  const searchInput = document.getElementById("search");
  const tabs = document.querySelectorAll(".tab");
  const DOW = ["日", "月", "火", "水", "木", "金", "土"];

  let events = [];
  let companies = {}; // 劇団名 -> {summary, url, updatedAt}
  let view = "now"; // now | archive | companies
  let query = "";
  let selectedCompany = null;
  let dateFrom = "";
  let dateTo = "";

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

  function fmtMonth(ym) {
    const [y, m] = ym.split("-").map(Number);
    return `${y}年${m}月`;
  }

  function daysFromToday(iso) {
    return Math.round((Date.parse(iso) - Date.parse(todayStr)) / 86400000);
  }

  function mapsUrl(ev) {
    const q = ev.location || ev.venue;
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`;
  }

  function card(ev, badge, opts) {
    const showChip = !(opts && opts.noChip);
    const title = ev.url
      ? `<a href="${esc(ev.url)}" target="_blank" rel="noopener">${esc(ev.title)}</a>`
      : esc(ev.title);
    const parts = [fmtRange(ev)];
    if (ev.venue) {
      parts.push(
        `<a class="maploc" href="${esc(mapsUrl(ev))}" target="_blank" rel="noopener">📍${esc(ev.venue)}</a>`
      );
    }
    const chip =
      showChip && ev.company
        ? `<button class="chip" data-company="${esc(ev.company)}">${esc(ev.company)}</button>`
        : "";
    return `<div class="card">
      <div class="title">${title}${badge ? `<span class="badge">${esc(badge)}</span>` : ""}</div>
      <div class="info">${parts.join(" ・ ")}${chip}</div>
    </div>`;
  }

  function section(label, items, cards) {
    return `<h2 class="section">${label} <span class="count">${items.length}件</span></h2>` +
      (items.length ? cards : `<p class="empty">該当なし</p>`);
  }

  function groupByMonth(list, keyFn) {
    const map = new Map();
    for (const e of list) {
      const k = keyFn(e);
      if (!map.has(k)) map.set(k, []);
      map.get(k).push(e);
    }
    return map;
  }

  function matches(ev) {
    if (!query) return true;
    return [ev.title, ev.company, ev.work, ev.venue, ev.note]
      .filter(Boolean)
      .some((f) => f.toLowerCase().includes(query));
  }

  function upcomingBadge(ev) {
    const until = daysFromToday(ev.start);
    return until <= 14 ? `あと${until}日で開幕` : "";
  }

  function ongoingBadge(ev) {
    const left = daysFromToday(ev.end);
    return left === 0 ? "本日千秋楽" : `千秋楽まで${left}日`;
  }

  function renderNow(list) {
    const ongoing = list
      .filter((e) => e.start <= todayStr && todayStr <= e.end)
      .sort((a, b) => a.end.localeCompare(b.end));
    const upcoming = list.filter((e) => e.start > todayStr);

    const ongoingCards = ongoing.map((e) => card(e, ongoingBadge(e))).join("");

    let upcomingHtml = "";
    for (const [ym, items] of groupByMonth(upcoming, (e) => e.start.slice(0, 7))) {
      upcomingHtml += `<h3 class="month">${fmtMonth(ym)}</h3>`;
      upcomingHtml += items.map((e) => card(e, upcomingBadge(e))).join("");
    }

    return section("開催中", ongoing, ongoingCards) + section("今後", upcoming, upcomingHtml);
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
      let inner = "";
      for (const [ym, monthItems] of groupByMonth(items, (e) => e.start.slice(0, 7))) {
        inner += `<h3 class="month">${Number(ym.slice(5))}月</h3>`;
        inner += monthItems.map((e) => card(e, "")).join("");
      }
      html += section(`${y}年`, items, inner);
    }
    return html;
  }

  function companyStats(list) {
    // 件数は公演単位（production）で数える。日程分割された同一公演は1、再演は別公演として2。
    const map = new Map();
    for (const e of list) {
      if (!e.company) continue;
      if (!map.has(e.company)) map.set(e.company, { productions: new Set(), latest: "" });
      const s = map.get(e.company);
      s.productions.add(e.production);
      if (e.start > s.latest) s.latest = e.start;
    }
    return [...map.entries()]
      .map(([name, s]) => [name, { count: s.productions.size, latest: s.latest }])
      .sort((a, b) => b[1].count - a[1].count || b[1].latest.localeCompare(a[1].latest));
  }

  // 同一公演（production）の日程分割を1件にまとめる。開始=最早、千秋楽=最遅、会場は代表1つ。
  function collapseProductions(evs) {
    const map = new Map();
    for (const e of evs) {
      const p = map.get(e.production);
      if (!p) {
        map.set(e.production, { ...e, _venues: new Set(e.venue ? [e.venue] : []) });
      } else {
        if (e.start < p.start) {
          p.start = e.start;
          p.location = e.location; // マップリンクは先頭公演の住所に合わせる
        }
        if (e.end > p.end) p.end = e.end;
        if (e.venue) p._venues.add(e.venue);
        if (!p.url && e.url) p.url = e.url;
      }
    }
    return [...map.values()].map((p) => ({
      ...p,
      venue: p._venues.size > 1 ? `${[...p._venues][0]} ほか` : [...p._venues][0] || null,
    }));
  }

  function overviewBlock(name) {
    const info = companies[name];
    if (!info || !info.summary) return "";
    const src = info.url
      ? `<a class="ov-src" href="${esc(info.url)}" target="_blank" rel="noopener">出典</a>`
      : "";
    const updated = info.updatedAt ? `<span class="ov-date">${esc(info.updatedAt)} 時点</span>` : "";
    return `<div class="overview">
      <p>${esc(info.summary)}</p>
      <div class="ov-meta">${src}${updated}</div>
    </div>`;
  }

  function renderCompanies(list) {
    if (selectedCompany) {
      // 詳細も公演単位（日程分割をまとめる）で一覧表示し、劇団一覧の「N公演」と件数を一致させる
      const own = collapseProductions(list.filter((e) => e.company === selectedCompany));
      const current = own
        .filter((e) => todayStr <= e.end)
        .sort((a, b) => a.start.localeCompare(b.start));
      const past = own.filter((e) => e.end < todayStr).sort((a, b) => b.start.localeCompare(a.start));
      const currentCards = current
        .map((e) =>
          card(e, e.start <= todayStr ? ongoingBadge(e) : upcomingBadge(e), { noChip: true })
        )
        .join("");
      const pastCards = past.map((e) => card(e, "", { noChip: true })).join("");
      return `<div class="company-head">
          <button id="back-companies">← 劇団一覧</button>
          <h2>${esc(selectedCompany)}</h2>
        </div>` +
        overviewBlock(selectedCompany) +
        section("開催中・今後", current, currentCards) +
        section("過去", past, pastCards);
    }

    const stats = companyStats(list).filter(
      ([name]) => !query || name.toLowerCase().includes(query)
    );
    if (!stats.length) return `<p class="empty">該当なし</p>`;
    return `<h2 class="section">劇団・団体 <span class="count">${stats.length}組</span></h2>` +
      stats
        .map(
          ([name, s]) => `<button class="company-row" data-company="${esc(name)}">
            <span class="name">${esc(name)}</span>
            <span class="meta">${s.count}公演 ・ 直近 ${esc(s.latest.slice(0, 7).replace("-", "/"))}</span>
          </button>`
        )
        .join("");
  }

  function dateRange() {
    if (!dateFrom && !dateTo) return null;
    // 片方だけ指定された場合は単日として扱う
    const from = dateFrom || dateTo;
    const to = dateTo || dateFrom;
    return from <= to ? [from, to] : [to, from];
  }

  function renderDateResults(list, from, to) {
    const hits = list
      .filter((e) => e.start <= to && from <= e.end)
      .sort((a, b) => a.start.localeCompare(b.start) || a.end.localeCompare(b.end));
    const label =
      from === to
        ? `${fmtDate(from, Number(from.slice(0, 4)) !== todayYear)} の公演`
        : `${fmtDate(from, Number(from.slice(0, 4)) !== todayYear)} 〜 ${fmtDate(to, Number(to.slice(0, 4)) !== todayYear)} の公演`;
    const cards = hits
      .map((e) => {
        let badge = "";
        if (e.end < todayStr) badge = "終了";
        else if (e.start <= todayStr) badge = ongoingBadge(e);
        else badge = upcomingBadge(e);
        return card(e, badge);
      })
      .join("");
    return section(label, hits, cards);
  }

  function render() {
    const range = dateRange();
    if (range) {
      // 日程逆引きモード: タブより優先して期間と重なる公演を表示
      app.innerHTML = renderDateResults(events.filter(matches), range[0], range[1]);
      return;
    }
    if (view === "companies" && selectedCompany) {
      // 劇団詳細では検索ではなく劇団で絞る
      app.innerHTML = renderCompanies(events);
      return;
    }
    const list = events.filter(matches);
    app.innerHTML =
      view === "now" ? renderNow(list) : view === "archive" ? renderArchive(list) : renderCompanies(list);
  }

  function setView(v) {
    view = v;
    tabs.forEach((t) => t.classList.toggle("active", t.dataset.view === v));
    render();
  }

  tabs.forEach((tab) =>
    tab.addEventListener("click", () => {
      if (tab.dataset.view === "companies") selectedCompany = null;
      setView(tab.dataset.view);
    })
  );

  app.addEventListener("click", (e) => {
    const chip = e.target.closest("[data-company]");
    if (chip) {
      selectedCompany = chip.dataset.company;
      clearDates(); // 逆引きモードを抜けて劇団ページへ
      setView("companies");
      window.scrollTo(0, 0);
      return;
    }
    if (e.target.closest("#back-companies")) {
      selectedCompany = null;
      render();
    }
  });

  const dateFromInput = document.getElementById("date-from");
  const dateToInput = document.getElementById("date-to");
  const dateClear = document.getElementById("date-clear");

  function clearDates() {
    dateFrom = dateTo = "";
    dateFromInput.value = dateToInput.value = "";
    dateClear.hidden = true;
    syncMonthButtons();
  }

  function onDateChange() {
    dateFrom = dateFromInput.value;
    dateTo = dateToInput.value;
    dateClear.hidden = !dateFrom && !dateTo;
    syncMonthButtons();
    render();
  }

  // 1〜12月のワンボタン。当年の該当月をまるごと日程検索する
  const monthBtnsEl = document.getElementById("month-btns");
  const monthYear = Number(todayStr.slice(0, 4));
  document.getElementById("months-year").textContent = `${monthYear}年`;

  function monthRange(m) {
    const last = new Date(Date.UTC(monthYear, m, 0)).getUTCDate();
    const mm = String(m).padStart(2, "0");
    return [`${monthYear}-${mm}-01`, `${monthYear}-${mm}-${String(last).padStart(2, "0")}`];
  }

  function syncMonthButtons() {
    for (const b of monthBtnsEl.children) {
      const [from, to] = monthRange(Number(b.dataset.month));
      b.classList.toggle("active", dateFrom === from && dateTo === to);
    }
  }

  monthBtnsEl.innerHTML = Array.from(
    { length: 12 },
    (_, i) => `<button class="month-btn" data-month="${i + 1}">${i + 1}月</button>`
  ).join("");

  monthBtnsEl.addEventListener("click", (e) => {
    const b = e.target.closest(".month-btn");
    if (!b) return;
    const [from, to] = monthRange(Number(b.dataset.month));
    // 同じ月をもう一度押したら解除
    if (dateFrom === from && dateTo === to) {
      clearDates();
      render();
      return;
    }
    dateFromInput.value = from;
    dateToInput.value = to;
    onDateChange();
  });

  dateFromInput.addEventListener("change", onDateChange);
  dateToInput.addEventListener("change", onDateChange);
  dateClear.addEventListener("click", () => {
    clearDates();
    render();
  });

  searchInput.addEventListener("input", () => {
    query = searchInput.value.trim().toLowerCase();
    render();
  });

  // 劇団概要（任意・欠けていても動作する）。先に取得しておき、劇団詳細で使う
  fetch("data/companies.json")
    .then((r) => (r.ok ? r.json() : {}))
    .then((data) => {
      companies = data && data.companies ? data.companies : {};
    })
    .catch(() => {
      companies = {};
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
