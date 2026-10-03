(() => {
'use strict';
const D = window.KP_DATA || [];
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const app = $('#app');
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const LV = {junior:'Junior', mid:'Mid', senior:'Senior'};
const chip = l => `<span class="chip ${esc(l)}">${esc(LV[l] || l)}</span>`;

/* ---------- data indexes ---------- */
const byNum = {}; const topics = [];
D.forEach(c => { byNum[c.number] = c; c.topics.forEach((t, i) => { t._ch = c; t._i = i; topics.push(t); }); });
const tById = Object.fromEntries(topics.map(t => [t.id, t]));
const parts = [];
D.forEach(c => { let p = parts.find(x => x.name === c.part); if (!p) parts.push(p = {name: c.part, chapters: []}); p.chapters.push(c); });

/* ---------- state (localStorage) ---------- */
const KEY = 'kubeprep.v1';
let S = {studied: {}, star: {}, srs: {}, mock: []};
try {
  const j = JSON.parse(localStorage.getItem(KEY) || '{}'), isO = v => v && typeof v === 'object' && !Array.isArray(v);
  ['studied', 'star', 'srs'].forEach(k => { if (isO(j[k])) S[k] = j[k]; });
  Object.keys(S.srs).forEach(k => { if (!isO(S.srs[k])) delete S.srs[k]; });
  if (Array.isArray(j.mock)) S.mock = j.mock.filter(isO);
} catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} drawRing(); };
const doneIn = c => c.topics.filter(t => S.studied[t.id]).length;

function drawRing() {
  const n = topics.length, d = Object.keys(S.studied).filter(k => tById[k]).length, p = n ? d / n : 0, C = 2 * Math.PI * 16;
  $('#ring').innerHTML = `<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="16" fill="none" stroke="rgba(45,49,66,.12)" stroke-width="4"/><circle cx="20" cy="20" r="16" fill="none" stroke="#326ce5" stroke-width="4" stroke-linecap="round" stroke-dasharray="${(C * p).toFixed(1)} ${C.toFixed(1)}"/></svg><b>${Math.round(p * 100)}%</b>`;
  $('#ring').title = `${d} of ${n} topics studied`;
}

/* ---------- small renderers ---------- */
const table = t => !t ? '' : `<div class="tablewrap"><table>${t.caption ? `<caption>${esc(t.caption)}</caption>` : ''}<thead><tr>${t.headers.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${t.rows.map(r => `<tr>${r.map(c => `<td>${c && c.html ? c.html : inline(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
// `code` spans only; everything else escaped
const inline = s => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>');
const para = s => `<p>${inline(s)}</p>`;
const bar = (n, d) => `<div class="bar ${n === d && d ? 'done' : ''}"><i style="width:${d ? Math.round(100 * n / d) : 0}%"></i></div>`;
const levelsOf = c => ['junior', 'mid', 'senior'].filter(l => c.topics.some(t => t.level === l));
const nDia = c => c.topics.filter(t => t.diagram).length;

function topicCard(t, n) {
  const dia = t.diagram ? `<figure class="fig"><div class="scroll" data-zoom="${esc(t.id)}" title="Click to enlarge">${t.diagram.svg}</div><figcaption><span>${esc(t.diagram.title || 'Diagram')}</span><button class="btn sm" data-zoom="${esc(t.id)}">Open full size</button></figcaption></figure>` : '';
  const cmds = (t.commands || []).length ? `<h3>Commands</h3><pre>${t.commands.map(c => `<div class="cmd"><code>${esc(c.cmd)}</code><span class="n">${esc(c.note || '')}</span><button data-copy="${esc(c.cmd)}">Copy</button></div>`).join('')}</pre>` : '';
  return `<article class="topic ${S.studied[t.id] ? 'studied' : ''}" id="${esc(t.id)}" data-level="${esc(t.level)}">
    <div class="qh"><div><div class="qn">Q${n}</div><h2>${inline(t.question)}</h2></div>${chip(t.level)}</div>
    <div class="say"><span class="tag">Say this first</span><p>${inline(t.say_first)}</p></div>
    <h3>Explain it simply</h3>${(t.explain || []).map(para).join('')}
    ${dia}
    ${(t.key_points || []).length ? `<h3>Key points</h3><ul class="checks">${t.key_points.map(k => `<li>${inline(k)}</li>`).join('')}</ul>` : ''}
    ${table(t.table)}${cmds}
    ${(t.follow_ups || []).length ? `<h3>Likely follow-ups</h3><div class="fu">${t.follow_ups.map(f => `<span>${esc(f)}</span>`).join('')}</div>` : ''}
    ${(t.pitfalls || []).length ? `<div class="pit"><span class="tag">Common pitfalls</span><ul>${t.pitfalls.map(p => `<li>${inline(p)}</li>`).join('')}</ul></div>` : ''}
    <div class="tfoot"><button class="btn sm ${S.studied[t.id] ? 'on' : ''}" data-study="${esc(t.id)}">${S.studied[t.id] ? '✓ Studied' : 'Mark as studied'}</button><button class="btn sm ${S.star[t.id] ? 'on' : ''}" data-star="${esc(t.id)}">${S.star[t.id] ? '★ In starred deck' : '☆ Add to flashcards'}</button></div>
  </article>`;
}

/* ---------- views ---------- */
function home() {
  const nT = topics.length, nD = topics.filter(t => t.diagram).length, nTab = topics.filter(t => t.table).length;
  const hero = topics.find(t => t.diagram && /architecture/.test(t.diagram.file || ''));
  app.innerHTML = `
  <section class="hero"><div class="wrap">
    <div><span class="tag b">Visual-first interview prep</span>
    <h1>Crack the Kubernetes interview, <em>one diagram at a time</em></h1>
    <p class="lead">Chapter-wise questions with the answer to open with, a plain-English explanation, a diagram, a comparison table and the commands to back it up.</p>
    <div class="cta"><a class="btn pri" href="#/chapter/1">Start learning</a><a class="btn" href="#/mock">Take a mock interview</a></div>
    <div class="stats"><span><b>${D.length}</b>chapters</span><span><b>${nT}</b>questions</span><span><b>${nD}</b>diagrams</span><span><b>${nTab}</b>tables</span></div></div>
    ${hero ? `<div class="herofig">${hero.diagram.svg}<div class="tag cap">${esc(hero.diagram.title || '')}</div></div>` : ''}
  </div></section>
  <section class="sec"><div class="wrap"><span class="tag b">Curriculum</span><h2>${D.length} chapters, from containers to incident response</h2>
    <p class="sub">Pick a chapter, read the cards, mark what you have studied. Progress is saved in this browser only.</p>
    ${parts.map(p => { const tt = p.chapters.reduce((a, c) => a + c.topics.length, 0), dd = p.chapters.reduce((a, c) => a + doneIn(c), 0); return `<div class="part"><header><h3>${esc(p.name)}</h3><span class="meta">${p.chapters.length} chapters · ${tt} questions · ${dd}/${tt} studied</span></header><div class="cards">${p.chapters.map(c => `<a class="ccard" href="#/chapter/${c.number}"><div class="row"><span>CH ${String(c.number).padStart(2, '0')}</span><span>${c.topics.length} questions · ${nDia(c)} diagrams</span></div><h4>${esc(c.title)}</h4><p>${esc(c.tagline || c.overview)}</p>${bar(doneIn(c), c.topics.length)}<div class="chips">${levelsOf(c).map(chip).join('')}</div></a>`).join('')}</div></div>`; }).join('')}
  </div></section>
  <section class="sec" style="padding-top:0"><div class="wrap"><span class="tag b">Quick compare</span><h2>Deployment vs StatefulSet vs DaemonSet</h2><p class="sub">A favourite opener. Know the one-line difference and the trap in each.</p>
  ${table({headers: ['', 'Deployment', 'StatefulSet', 'DaemonSet'], rows: [
    ['Use it for', 'Stateless apps and APIs', 'Databases, queues, anything needing stable identity', 'One agent per node (logs, CNI, monitoring)'],
    ['Pod names', 'Random suffix (`web-7d9f-x2k`)', 'Stable ordinals (`db-0`, `db-1`)', 'Random suffix, one per node'],
    ['Storage', 'Shared or ephemeral volumes', 'Own PVC per Pod via `volumeClaimTemplates`', 'Usually hostPath or none'],
    ['Scaling', 'Parallel, unordered', 'Ordered start, reverse-ordered stop', 'Follows the node count'],
    ['Network identity', 'Service load-balances across Pods', 'Headless Service gives each Pod a DNS name', 'Node-level, often `hostPort` or `hostNetwork`'],
    ['Rollout', 'RollingUpdate with `maxSurge` / `maxUnavailable`', 'RollingUpdate in reverse order, `partition` for canaries', 'RollingUpdate or `OnDelete`'],
    ['Classic trap', 'Treating it as safe for stateful data', 'Deleting the StatefulSet does not delete its PVCs', 'Forgetting tolerations, so control-plane nodes get no Pod']
  ]})}
  </div></section>`;
}

function chapter(num, focus) {
  const c = byNum[num]; if (!c) return notFound();
  const prev = byNum[num - 1], next = byNum[num + 1];
  app.innerHTML = `<div class="wrap"><div class="chlayout">
    <aside class="side"><h4>${esc(c.title)}</h4><div class="meta" id="pmeta" style="font:500 12px var(--f-mono);color:var(--muted)"></div><div id="pbar"></div>
      <div class="filters" id="filters"><button class="fbtn on" data-f="all">All</button>${levelsOf(c).map(l => `<button class="fbtn" data-f="${l}">${LV[l]}</button>`).join('')}</div>
      <ol id="toc">${c.topics.map((t, i) => `<li data-level="${t.level}"><a href="#/chapter/${num}/${esc(t.id)}" data-id="${esc(t.id)}"><span class="dot ${S.studied[t.id] ? 'ok' : ''}">${S.studied[t.id] ? '✓' : ''}</span><span>${inline(t.question)}</span></a></li>`).join('')}</ol></aside>
    <div><div class="crumb">${esc(c.part)} / Chapter ${num}</div>
      <div class="chhead"><h1>${esc(c.title)}</h1><p>${esc(c.overview)}</p></div>
      <div id="topics">${c.topics.map((t, i) => topicCard(t, i + 1)).join('')}</div>
      <div class="pager">${prev ? `<a class="btn" href="#/chapter/${prev.number}">← ${esc(prev.title)}</a>` : '<span></span>'}${next ? `<a class="btn pri" href="#/chapter/${next.number}">${esc(next.title)} →</a>` : `<a class="btn pri" href="#/mock">Try a mock interview →</a>`}</div>
    </div></div></div>`;
  const upd = () => { $('#pmeta').textContent = `${doneIn(c)} / ${c.topics.length} studied`; $('#pbar').innerHTML = bar(doneIn(c), c.topics.length); };
  upd();
  $('#filters').onclick = e => { const b = e.target.closest('[data-f]'); if (!b) return; $$('#filters .fbtn').forEach(x => x.classList.toggle('on', x === b)); const f = b.dataset.f; $$('.topic').forEach(x => x.hidden = f !== 'all' && x.dataset.level !== f); $$('#toc li').forEach(x => x.hidden = f !== 'all' && x.dataset.level !== f); };
  app.onclick = e => {
    const s = e.target.closest('[data-study]');
    if (s) { const id = s.dataset.study; S.studied[id] ? delete S.studied[id] : S.studied[id] = Date.now(); save(); const a = $('#' + CSS.escape(id)); a.classList.toggle('studied', !!S.studied[id]); s.classList.toggle('on', !!S.studied[id]); s.textContent = S.studied[id] ? '✓ Studied' : 'Mark as studied'; const dot = $(`#toc a[data-id="${CSS.escape(id)}"] .dot`); dot.classList.toggle('ok', !!S.studied[id]); dot.textContent = S.studied[id] ? '✓' : ''; upd(); return; }
    const st = e.target.closest('[data-star]');
    if (st) { const id = st.dataset.star; S.star[id] ? delete S.star[id] : S.star[id] = 1; save(); st.classList.toggle('on', !!S.star[id]); st.textContent = S.star[id] ? '★ In starred deck' : '☆ Add to flashcards'; return; }
    globalClicks(e);
  };
  if (focus && tById[focus]) setTimeout(() => $('#' + CSS.escape(focus))?.scrollIntoView(), 30); else window.scrollTo(0, 0);
  const links = $$('#toc a');
  const io = new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) links.forEach(l => l.classList.toggle('cur', l.dataset.id === en.target.id)); }), {rootMargin: '-90px 0px -70% 0px'});
  $$('.topic').forEach(x => io.observe(x));
}

/* flashcards: tiny spaced-repetition (Leitner boxes) */
const STEP = [600e3, 864e5, 3 * 864e5, 7 * 864e5, 14 * 864e5, 30 * 864e5];
const human = ms => ms < 36e5 ? Math.round(ms / 6e4) + 'm' : ms < 2 * 864e5 ? Math.round(ms / 36e5) + 'h' : Math.round(ms / 864e5) + 'd';
const after = (t, r) => { const b = (S.srs[t.id]?.box) ?? -1; const nb = r === 0 ? 0 : r === 1 ? Math.max(b, 0) : r === 2 ? Math.min(Math.max(b + 1, 1), 5) : Math.min(Math.max(b + 2, 2), 5); return {box: nb, gap: r === 1 ? (b < 0 ? 36e5 : STEP[b]) : STEP[nb]}; };
let FC = {chs: new Set(D.map(c => c.number)), lv: new Set(['junior', 'mid', 'senior']), starOnly: false, shuffle: true, queue: [], i: 0, show: false, stat: {again: 0, hard: 0, good: 0, easy: 0}};
function fcBuild() {
  const now = Date.now();
  let q = topics.filter(t => FC.chs.has(t._ch.number) && FC.lv.has(t.level) && (!FC.starOnly || S.star[t.id]));
  const due = q.filter(t => !S.srs[t.id] || S.srs[t.id].due <= now);
  q = due.length ? due : q;
  if (FC.shuffle) q = q.map(t => [Math.random(), t]).sort((a, b) => a[0] - b[0]).map(x => x[1]);
  FC.queue = q; FC.i = 0; FC.show = false;
}
function flashcards() {
  if (!FC.queue.length) fcBuild();
  const nowDue = topics.filter(t => !S.srs[t.id] || S.srs[t.id].due <= Date.now()).length;
  const learned = Object.values(S.srs).filter(x => x.box >= 2).length;
  app.innerHTML = `<div class="wrap"><div class="study">
    <aside class="panel"><h4>Deck</h4>
      <label><input type="checkbox" id="fcStar" ${FC.starOnly ? 'checked' : ''}> Starred only (${Object.keys(S.star).length})</label>
      <label><input type="checkbox" id="fcShuf" ${FC.shuffle ? 'checked' : ''}> Shuffle</label>
      <div class="filters">${['junior', 'mid', 'senior'].map(l => `<button class="fbtn ${FC.lv.has(l) ? 'on' : ''}" data-lv="${l}">${LV[l]}</button>`).join('')}</div>
      <div class="lst">${D.map(c => `<label><input type="checkbox" data-ch="${c.number}" ${FC.chs.has(c.number) ? 'checked' : ''}> <span>${c.number}. ${esc(c.title)}</span></label>`).join('')}</div>
      <button class="btn sm" id="fcRebuild">Rebuild deck</button></aside>
    <section id="card"></section>
    <aside class="panel"><h4>Progress</h4><div class="big">${nowDue}</div><div class="tag">cards due or new</div><div class="big" style="margin-top:14px">${learned}</div><div class="tag">cards in box 3+</div>
      <h4 style="margin-top:18px">This session</h4><div class="tablewrap"><table><tbody>${['again', 'hard', 'good', 'easy'].map(k => `<tr><td>${k}</td><td>${FC.stat[k]}</td></tr>`).join('')}</tbody></table></div></aside>
  </div></div>`;
  const draw = () => {
    const t = FC.queue[FC.i], el = $('#card');
    if (!t) { el.innerHTML = `<div class="flash"><div class="empty"><h2>Deck finished</h2><p>${FC.queue.length} cards reviewed. Cards come back on their own schedule.</p><button class="btn pri" id="again">Review the deck again</button></div></div>`; $('#again').onclick = () => { fcBuild(); flashcards(); }; return; }
    const hint = r => human(after(t, r).gap);
    el.innerHTML = `<div class="flash"><div class="fh"><span class="tag">Card ${FC.i + 1} of ${FC.queue.length}</span><span class="chip mid" style="background:var(--blue-tint);color:var(--blue-ink)">Ch ${t._ch.number}</span>${chip(t.level)}<button class="btn sm" style="margin-left:auto" data-star="${esc(t.id)}">${S.star[t.id] ? '★' : '☆'}</button></div>
      <div class="q">${inline(t.question)}</div>
      ${FC.show ? `<div class="ans"><div class="say"><span class="tag">Say this first</span><p>${inline(t.say_first)}</p></div><ul class="checks">${(t.key_points || []).slice(0, 4).map(k => `<li>${inline(k)}</li>`).join('')}</ul>${t.diagram ? t.diagram.svg : ''}<p style="margin-top:12px"><a href="#/chapter/${t._ch.number}/${esc(t.id)}">Read the full explanation →</a></p></div>
      <div class="rate"><button class="a" data-r="0">Again<small>${hint(0)}</small></button><button class="h" data-r="1">Hard<small>${hint(1)}</small></button><button class="g" data-r="2">Good<small>${hint(2)}</small></button><button class="e" data-r="3">Easy<small>${hint(3)}</small></button></div>` : `<div style="margin-top:auto;padding-top:30px"><button class="btn pri" id="reveal">Reveal answer</button></div>`}
      <div class="kbds"><kbd>Space</kbd> reveal · <kbd>1</kbd> again · <kbd>2</kbd> hard · <kbd>3</kbd> good · <kbd>4</kbd> easy</div></div>`;
  };
  const rate = r => { const t = FC.queue[FC.i]; if (!t || !FC.show) return; const a = after(t, r); S.srs[t.id] = {box: a.box, due: Date.now() + a.gap}; FC.stat[['again', 'hard', 'good', 'easy'][r]]++; save(); FC.i++; FC.show = false; flashcards(); };
  draw();
  app.onclick = e => {
    if (e.target.id === 'reveal') { FC.show = true; draw(); return; }
    const r = e.target.closest('[data-r]'); if (r) { rate(+r.dataset.r); return; }
    const st = e.target.closest('[data-star]'); if (st) { const id = st.dataset.star; S.star[id] ? delete S.star[id] : S.star[id] = 1; save(); st.textContent = S.star[id] ? '★' : '☆'; return; }
    const lv = e.target.closest('[data-lv]'); if (lv) { const l = lv.dataset.lv; FC.lv.has(l) ? FC.lv.delete(l) : FC.lv.add(l); lv.classList.toggle('on'); return; }
    if (e.target.dataset.ch) { const n = +e.target.dataset.ch; e.target.checked ? FC.chs.add(n) : FC.chs.delete(n); return; }
    if (e.target.id === 'fcStar') { FC.starOnly = e.target.checked; return; }
    if (e.target.id === 'fcShuf') { FC.shuffle = e.target.checked; return; }
    if (e.target.id === 'fcRebuild') { fcBuild(); flashcards(); return; }
    globalClicks(e);
  };
  keyHandler = ev => { if (ev.key === ' ') { ev.preventDefault(); if (!FC.show) { FC.show = true; draw(); } } else if ('1234'.includes(ev.key) && ev.key) rate(+ev.key - 1); };
}

/* mock interview */
let M = null, mockTimer = null;
function mock() {
  clearInterval(mockTimer);
  if (!M || M.phase === 'setup') {
    M = {phase: 'setup', n: 10, chs: new Set(D.map(c => c.number)), lv: new Set(['junior', 'mid', 'senior'])};
    app.innerHTML = `<div class="wrap sec"><span class="tag b">Mock interview</span><h2>Timed, randomised, honest</h2><p class="sub">You get a question, 3 minutes each. Answer out loud, reveal the model answer, then rate yourself. The scorecard shows what to revisit.</p>
    <div class="panel" style="max-width:640px"><h4>Questions</h4><div class="filters">${[5, 10, 15, 20].map(n => `<button class="fbtn ${n === M.n ? 'on' : ''}" data-n="${n}">${n}</button>`).join('')}</div>
    <h4 style="margin-top:16px">Level</h4><div class="filters">${['junior', 'mid', 'senior'].map(l => `<button class="fbtn on" data-lv="${l}">${LV[l]}</button>`).join('')}</div>
    <h4 style="margin-top:16px">Chapters</h4><div class="lst">${D.map(c => `<label><input type="checkbox" data-ch="${c.number}" checked> <span>${c.number}. ${esc(c.title)}</span></label>`).join('')}</div>
    <button class="btn pri" id="go">Start interview</button></div>
    ${S.mock.length ? `<h3 style="margin-top:28px">Past sessions</h3>${table({headers: ['Date', 'Questions', 'Score'], rows: S.mock.slice(-6).reverse().map(m => [new Date(m.at).toLocaleDateString(), String(m.n), m.score + '%'])})}` : ''}</div>`;
    app.onclick = e => {
      const n = e.target.closest('[data-n]'); if (n) { M.n = +n.dataset.n; $$('[data-n]').forEach(x => x.classList.toggle('on', x === n)); return; }
      const lv = e.target.closest('[data-lv]'); if (lv) { const l = lv.dataset.lv; M.lv.has(l) ? M.lv.delete(l) : M.lv.add(l); lv.classList.toggle('on'); return; }
      if (e.target.dataset.ch) { const k = +e.target.dataset.ch; e.target.checked ? M.chs.add(k) : M.chs.delete(k); return; }
      if (e.target.id === 'go') { const pool = topics.filter(t => M.chs.has(t._ch.number) && M.lv.has(t.level)); if (!pool.length) return alert('Pick at least one chapter and level.'); M.qs = pool.map(t => [Math.random(), t]).sort((a, b) => a[0] - b[0]).slice(0, M.n).map(x => x[1]); M.i = 0; M.res = []; M.phase = 'run'; M.left = 180; M.show = false; mockRun(); return; }
      globalClicks(e);
    };
    return;
  }
}
function mockRun() {
  clearInterval(mockTimer);
  const t = M.qs[M.i];
  if (!t) return mockEnd();
  const draw = () => {
    const m = String(Math.floor(M.left / 60)).padStart(2, '0'), s = String(M.left % 60).padStart(2, '0');
    app.innerHTML = `<div class="wrap"><div class="sec"><div class="flash"><div class="fh"><span class="tag">Question ${M.i + 1} of ${M.qs.length}</span>${chip(t.level)}<span class="timer ${M.left < 30 ? 'low' : ''}" style="margin-left:auto">${m}:${s}</span></div>
      <div class="q">${inline(t.question)}</div>
      ${M.show ? `<div class="ans"><div class="say"><span class="tag">Model opening</span><p>${inline(t.say_first)}</p></div><ul class="checks">${(t.key_points || []).map(k => `<li>${inline(k)}</li>`).join('')}</ul></div>
        <div class="rate" style="grid-template-columns:repeat(3,1fr)"><button class="a" data-m="0">Missed</button><button class="h" data-m="1">Partly</button><button class="e" data-m="2">Nailed it</button></div>`
      : `<div style="margin-top:auto;padding-top:30px;display:flex;gap:10px"><button class="btn pri" id="mreveal">Reveal model answer</button><button class="btn" id="mquit">End session</button></div>`}
      </div></div></div>`;
  };
  draw();
  mockTimer = setInterval(() => { if (!M.show && M.left > 0) { M.left--; const tm = $('.timer'); if (tm) { tm.textContent = `${String(Math.floor(M.left / 60)).padStart(2, '0')}:${String(M.left % 60).padStart(2, '0')}`; tm.classList.toggle('low', M.left < 30); } if (M.left === 0) { M.show = true; draw(); } } }, 1000);
  app.onclick = e => {
    if (e.target.id === 'mreveal') { M.show = true; draw(); return; }
    if (e.target.id === 'mquit') { return mockEnd(); }
    const r = e.target.closest('[data-m]'); if (r) { M.res.push({t, s: +r.dataset.m}); M.i++; M.left = 180; M.show = false; mockRun(); return; }
    globalClicks(e);
  };
}
function mockEnd() {
  clearInterval(mockTimer);
  const r = M.res, max = r.length * 2, got = r.reduce((a, x) => a + x.s, 0), pct = max ? Math.round(100 * got / max) : 0;
  if (r.length) { S.mock.push({at: Date.now(), n: r.length, score: pct}); save(); }
  const weak = r.filter(x => x.s < 2);
  const per = {}; r.forEach(x => { const k = x.t._ch.number; (per[k] ||= [0, 0]); per[k][0] += x.s; per[k][1] += 2; });
  app.innerHTML = `<div class="wrap sec"><span class="tag b">Scorecard</span><h2>${pct}% — ${pct >= 80 ? 'interview-ready on these topics' : pct >= 50 ? 'solid base, tighten the gaps' : 'keep studying, then retry'}</h2>
    ${r.length ? `<h3 style="margin-top:20px">By chapter</h3>${table({headers: ['Chapter', 'Score'], rows: Object.entries(per).map(([k, v]) => [`${k}. ${byNum[k].title}`, Math.round(100 * v[0] / v[1]) + '%'])})}
    ${weak.length ? `<h3>Revisit these</h3>${table({headers: ['Question', 'Result', 'Read'], rows: weak.map(x => [x.t.question, x.s === 0 ? 'Missed' : 'Partly', {html: `<a href="#/chapter/${x.t._ch.number}/${esc(x.t.id)}">Open</a>`}])})}` : '<p>No weak spots this round.</p>'}` : '<p>No questions answered.</p>'}
    <p style="margin-top:20px"><button class="btn pri" id="retry">New interview</button></p></div>`;
  app.onclick = e => { if (e.target.id === 'retry') { M = null; mock(); } else globalClicks(e); };
}

/* cheat sheet: every command in the guide */
function cheatsheet() {
  const all = []; topics.forEach(t => (t.commands || []).forEach(c => all.push({c, t})));
  app.innerHTML = `<div class="wrap sec cs"><span class="tag b">Cheat sheet</span><h2>${all.length} commands from the guide</h2><p class="sub">Search by command or purpose. Each row links back to the question it belongs to.</p>
    <input id="csq" type="search" placeholder="Filter: rollout, logs, drain, ..." aria-label="Filter commands"><div id="csout"></div></div>`;
  const draw = q => { const f = all.filter(x => !q || (x.c.cmd + ' ' + (x.c.note || '') + ' ' + x.t.question).toLowerCase().includes(q)); $('#csout').innerHTML = f.length ? `<div class="tablewrap"><table><thead><tr><th>Command</th><th>What it does</th><th>Ch</th><th></th></tr></thead><tbody>${f.map(x => `<tr><td><code>${esc(x.c.cmd)}</code></td><td>${esc(x.c.note || '')}</td><td><a href="#/chapter/${x._ch ?? x.t._ch.number}/${esc(x.t.id)}">${x.t._ch.number}</a></td><td><button class="btn sm" data-copy="${esc(x.c.cmd)}">Copy</button></td></tr>`).join('')}</tbody></table></div>` : '<div class="empty">No commands match.</div>'; };
  draw(''); $('#csq').oninput = e => draw(e.target.value.trim().toLowerCase());
  app.onclick = globalClicks;
}

function diagrams() {
  const all = topics.filter(t => t.diagram);
  app.innerHTML = `<div class="wrap sec"><span class="tag b">Diagram gallery</span><h2>${all.length} diagrams</h2><p class="sub">Click any diagram to enlarge it; use the chapter link for the full explanation.</p><div class="gal">${all.map(t => `<div class="gcard" data-zoom="${esc(t.id)}" tabindex="0" role="button">${t.diagram.svg}<b>${esc(t.diagram.title || t.question)}</b><small>Ch ${t._ch.number} · <a href="#/chapter/${t._ch.number}/${esc(t.id)}">read</a></small></div>`).join('')}</div></div>`;
  app.onclick = globalClicks;
}
function notFound() { app.innerHTML = `<div class="wrap"><div class="empty"><h2>Not found</h2><p><a href="#/">Back to chapters</a></p></div></div>`; }

/* ---------- global behaviours ---------- */
let keyHandler = null;
function globalClicks(e) {
  const cp = e.target.closest('[data-copy]');
  if (cp) { navigator.clipboard?.writeText(cp.dataset.copy); const o = cp.textContent; cp.textContent = 'Copied'; setTimeout(() => cp.textContent = o, 1100); return; }
  const z = e.target.closest('[data-zoom]');
  if (z && !e.target.closest('a')) { const t = tById[z.dataset.zoom]; if (t?.diagram) { $('#zoomBox').innerHTML = `<div class="zh"><span>${esc(t.diagram.title || '')}</span><button class="btn sm" id="zclose">Close</button></div>${t.diagram.svg}`; $('#zoomOv').classList.add('open'); } }
}
$('#zoomOv').onclick = e => { if (e.target.id === 'zoomOv' || e.target.id === 'zclose') $('#zoomOv').classList.remove('open'); };
const sOv = $('#searchOv'), qIn = $('#q');
const openS = () => { sOv.classList.add('open'); qIn.value = ''; $('#res').innerHTML = ''; qIn.focus(); };
const closeS = () => sOv.classList.remove('open');
$('#openSearch').onclick = openS;
sOv.onclick = e => { if (e.target === sOv) closeS(); };
const hay = topics.map(t => ({t, s: [t.question, t.say_first, ...(t.key_points || []), ...(t.explain || []), ...(t.commands || []).map(c => c.cmd + ' ' + (c.note || '')), ...(t.follow_ups || [])].join(' \n ').toLowerCase()}));
qIn.oninput = () => {
  const q = qIn.value.trim().toLowerCase(); if (q.length < 2) { $('#res').innerHTML = ''; return; }
  const words = q.split(/\s+/);
  const hits = hay.map(h => ({t: h.t, sc: words.every(w => h.s.includes(w)) ? words.reduce((a, w) => a + (h.t.question.toLowerCase().includes(w) ? 5 : 1), 0) : 0})).filter(x => x.sc).sort((a, b) => b.sc - a.sc).slice(0, 25);
  const mk = s => { const re = new RegExp('(' + words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|') + ')', 'ig'); return s.split(re).map((p, i) => i % 2 ? '<mark>' + esc(p) + '</mark>' : esc(p)).join(''); };
  $('#res').innerHTML = hits.length ? hits.map(x => `<a href="#/chapter/${x.t._ch.number}/${esc(x.t.id)}"><small>Ch ${x.t._ch.number} · ${esc(x.t._ch.title)} · ${LV[x.t.level]}</small>${mk(x.t.question)}</a>`).join('') : '<div class="empty">No matches.</div>';
};
$('#res').onclick = e => { if (e.target.closest('a')) closeS(); };
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openS(); return; }
  if (e.key === 'Escape') { closeS(); $('#zoomOv').classList.remove('open'); return; }
  if (/INPUT|TEXTAREA/.test(document.activeElement.tagName) || sOv.classList.contains('open')) return;
  if (keyHandler) keyHandler(e);
});
$('#menu').onclick = () => $('#nav').classList.toggle('open');

/* ---------- router ---------- */
function route() {
  clearInterval(mockTimer); keyHandler = null; app.onclick = globalClicks;
  $('#nav').classList.remove('open');
  const h = location.hash.replace(/^#\/?/, '').split('/');
  const r = h[0] || 'home';
  $$('#nav a').forEach(a => a.classList.toggle('on', a.dataset.r === (r === 'chapter' ? 'home' : r)));
  ({
    home, chapter: () => chapter(+h[1], h[2]), flashcards, mock: () => { M = M && M.phase === 'run' ? null : M; mock(); }, cheatsheet, diagrams
  }[Object.hasOwn({home:1,chapter:1,flashcards:1,mock:1,cheatsheet:1,diagrams:1}, r) ? r : 'x'] || notFound)();
  if (r !== 'chapter') window.scrollTo(0, 0);
}
window.addEventListener('hashchange', route);
drawRing(); route();
})();
