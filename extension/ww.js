// Capture WaterlooWorks postings into Radar Monkey. Local only: it reads pages you
// already have open (you're logged in) and saves job records to the extension's
// storage, which syncs into your dashboard feed. It NEVER applies, shortlists, or
// clicks anything on WaterlooWorks — it only reads when you press Save or while the
// Auto toggle is on. Works on three kinds of page:
//   - a single posting (OVERVIEW)      -> one rich record
//   - a results / shortlist table      -> every row on the page at once
//   - the WORK TERM RATINGS tab        -> hiring history merged onto the last posting
(function () {
  if (window.__rmWW || window.top !== window) return;
  window.__rmWW = true;

  const clean = (s) => String(s || '').replace(/\u00a0/g, ' ').replace(/[ \t]+/g, ' ').replace(/\s*\n\s*/g, '\n').trim();
  const lower = (s) => clean(s).toLowerCase();
  const digits = (s) => (String(s || '').match(/\d{3,}/) || [''])[0];

  // ---- read a posting's label -> value pairs from any of WaterlooWorks' layouts ----
  function readFields() {
    const fields = [];
    const add = (label, value) => {
      label = clean(label).replace(/:\s*$/, ''); value = clean(value);
      if (label && value && label.length < 80 && value.length < 6000) fields.push([lower(label), value]);
    };
    // 2-column tables
    document.querySelectorAll('table tr').forEach(tr => {
      const cells = tr.querySelectorAll('th,td');
      if (cells.length === 2) add(cells[0].textContent, cells[1].textContent);
    });
    // definition lists
    document.querySelectorAll('dl').forEach(dl => {
      const dts = dl.querySelectorAll('dt'), dds = dl.querySelectorAll('dd');
      for (let i = 0; i < Math.min(dts.length, dds.length); i++) add(dts[i].textContent, dds[i].textContent);
    });
    // stacked "Label:" (bold) then value underneath — the OVERVIEW layout
    document.querySelectorAll('strong,b,label,.label,.tag__key,dt,h4,h5').forEach(el => {
      const txt = clean(el.textContent);
      if (!txt || !/:$/.test(txt) || txt.length > 80) return;
      let v = '';
      let n = el.nextElementSibling;
      if (n && !/^(strong|b|label)$/i.test(n.tagName)) v = n.textContent;
      if (!v && el.parentElement) {                       // value is sibling text in the same block
        const after = el.parentElement.textContent.split(txt).slice(1).join(txt);
        v = after;
      }
      add(txt, v);
    });
    return fields;
  }
  const pick = (fields, ...keys) => { for (const [l, v] of fields) if (keys.some(k => l === k || l.includes(k))) return v; return ''; };
  function gather(fields, ...keys) {
    const parts = [];
    for (const [l, v] of fields) if (keys.some(k => l.includes(k))) parts.push(clean(v));
    return [...new Set(parts)].join('\n\n');
  }

  function headerBits() {
    // The title/org and the job-id pill live above the OVERVIEW tabs.
    const h = document.querySelector('h1,h2,.heading__title,[class*="posting"] h1,[class*="posting"] h2');
    const title = h ? clean(h.textContent) : '';
    let id = '';
    const region = (h && h.closest('header,div')) || document.body;
    region.querySelectorAll('span,div,a,td').forEach(el => {
      if (id) return;
      const t = clean(el.textContent);
      if (/^\d{4,7}$/.test(t)) id = t;
    });
    return { title, id };
  }

  function jobId(fields, hdr) {
    const fromField = digits(pick(fields, 'job id', 'posting id', 'job posting id'));
    if (fromField) return 'ww:' + fromField;
    if (hdr && hdr.id) return 'ww:' + hdr.id;
    try { const q = new URL(location.href).searchParams; for (const k of ['ck_jobid', 'jobId', 'postingId', 'id']) { const v = q.get(k); if (v && /\d/.test(v)) return 'ww:' + digits(v) || 'ww:' + v; } } catch (e) {}
    return 'ww:h' + hash(lower((hdr && hdr.title) || pick(fields, 'job title', 'title')) + '|' + lower(pick(fields, 'organization', 'company', 'employer')));
  }
  function hash(seed) { let h = 0; for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) | 0; return (h >>> 0).toString(36); }

  const modelOf = (s) => { s = lower(s); return s.includes('remote') ? 'Remote' : s.includes('hybrid') ? 'Hybrid' : /in.?person|on.?site/.test(s) ? 'On-site' : ''; };
  const categoryOf = (t) => /machine learning|data scien|deep learning|\bnlp\b|computer vision|\bai\b|\bml\b|data engineer|artificial intelligence/.test(lower(t)) ? 'AI/ML/Data' : 'Software';

  // ---- hiring history (WORK TERM RATINGS tab) -> compact text ----
  function readHiringHistory() {
    for (const tbl of document.querySelectorAll('table')) {
      const head = clean(tbl.textContent).toLowerCase();
      if (!head.includes('students hired') && !head.includes('hiring history')) continue;
      const rows = [...tbl.querySelectorAll('tr')].map(tr => [...tr.querySelectorAll('th,td')].map(c => clean(c.textContent)));
      if (rows.length) return rows.filter(r => r.join('').length).map(r => r.filter(Boolean).join(' | ')).join('\n');
    }
    return '';
  }

  // ---- scrape a single posting ----
  function scrapePosting() {
    const fields = readFields();
    const hdr = headerBits();
    const title = hdr.title || pick(fields, 'job title', 'position title', 'title');
    const company = pick(fields, 'organization', 'company', 'employer', 'division');
    if (!title || !company) return null;
    const city = pick(fields, 'job - city', 'city');
    const prov = pick(fields, 'job - province', 'province', 'state');
    const country = pick(fields, 'job - country', 'country');
    const region = pick(fields, 'region');
    const loc = [city, prov].filter(Boolean).join(', ') || clean(region) || clean(pick(fields, 'location'));
    const term = clean(pick(fields, 'work term', 'term')).replace(/\n+/g, ' ');
    const jobType = pick(fields, 'job type');
    const level = clean(pick(fields, 'level')).replace(/\n+/g, ', ');
    const openings = clean(pick(fields, 'number of job openings', 'openings'));
    const model = modelOf(pick(fields, 'employment location arrangement', 'location arrangement', 'work location'));
    const description = gather(fields, 'job summary', 'summary', 'job responsibilities', 'responsibilities', 'required skills', 'skills', 'description', 'targeted degrees');
    const countries = /united states|usa|\bus\b/.test(lower(country)) ? ['US'] : ['CA'];
    const terms = [term, jobType && jobType !== term ? jobType : ''].filter(Boolean);
    return {
      id: jobId(fields, hdr), kind: 'intern', title, company, url: location.href.split('#')[0],
      locations: loc ? [loc] : [], countries, terms, level, openings,
      work_model: model, remote_ok: model === 'Remote', category: categoryOf(title + ' ' + description + ' ' + level),
      description, wtr: readHiringHistory(), first_seen: new Date().toISOString(),
    };
  }

  // ---- scrape a results / shortlist table: one record per row ----
  function scrapeList() {
    const out = [];
    for (const tbl of document.querySelectorAll('table')) {
      const headRow = tbl.querySelector('thead tr') || tbl.querySelector('tr');
      if (!headRow) continue;
      const cols = [...headRow.querySelectorAll('th,td')].map(c => lower(c.textContent));
      const idx = (...keys) => cols.findIndex(c => keys.some(k => c.includes(k)));
      const ti = idx('job title', 'title'), ci = idx('organization', 'company', 'employer');
      if (ti < 0 || ci < 0) continue;                      // not a postings table
      const li = idx('location', 'city'), mi = idx('openings'), ji = idx('job id', 'posting id'), tmi = idx('work term', 'term');
      const bodyRows = tbl.querySelectorAll('tbody tr');
      for (const tr of (bodyRows.length ? bodyRows : tbl.querySelectorAll('tr'))) {
        const cells = [...tr.querySelectorAll('td')];
        if (!cells.length) continue;
        const cellTxt = (i) => i >= 0 && cells[i] ? clean(cells[i].textContent) : '';
        const title = cellTxt(ti), company = cellTxt(ci);
        if (!title || !company) continue;
        const link = tr.querySelector('a[href]');
        let id = ji >= 0 ? digits(cellTxt(ji)) : '';
        if (!id) { for (const c of cells) { const d = digits(c.textContent); if (d && /^\d{4,7}$/.test(d)) { id = d; break; } } }
        if (!id && link) id = digits(link.href);
        const rec = {
          id: id ? 'ww:' + id : 'ww:h' + hash(lower(title) + '|' + lower(company)),
          kind: 'intern', title, company,
          url: link ? link.href : location.href.split('#')[0],
          locations: cellTxt(li) ? [cellTxt(li)] : [], openings: cellTxt(mi),
          terms: cellTxt(tmi) ? [cellTxt(tmi)] : [],
          category: categoryOf(title), first_seen: new Date().toISOString(),
        };
        out.push(rec);
      }
      if (out.length) break;                               // first real postings table wins
    }
    return out;
  }

  // ---- persistence ----
  async function store(recs) {
    if (!recs.length) return 0;
    const { wwJobs = {}, wwLast = '' } = await chrome.storage.local.get(['wwJobs', 'wwLast']);
    let last = wwLast;
    for (const rec of recs) {
      const prev = wwJobs[rec.id];
      if (prev) {
        rec.first_seen = prev.first_seen || rec.first_seen;
        // Don't let a thin list-row overwrite a rich posting we already captured.
        for (const k of ['description', 'wtr', 'level', 'work_model', 'remote_ok'])
          if (!rec[k] && prev[k]) rec[k] = prev[k];
      }
      wwJobs[rec.id] = Object.assign({}, prev, rec);
      last = rec.id;
    }
    await chrome.storage.local.set({ wwJobs, wwLast: last });
    return recs.length;
  }

  // Attach hiring-history from the ratings tab onto the posting we last saved.
  async function mergeHistory() {
    const wtr = readHiringHistory();
    if (!wtr) return 0;
    const { wwJobs = {}, wwLast = '' } = await chrome.storage.local.get(['wwJobs', 'wwLast']);
    if (!wwLast || !wwJobs[wwLast]) return 0;
    if (wwJobs[wwLast].wtr === wtr) return 0;
    wwJobs[wwLast].wtr = wtr;
    await chrome.storage.local.set({ wwJobs });
    return 1;
  }

  // Read whatever this page is and save it. Returns [count, what].
  async function captureCurrent() {
    const posting = scrapePosting();
    if (posting) return [await store([posting]), posting.title];
    const list = scrapeList();
    if (list.length) return [await store(list), list.length + ' jobs'];
    const merged = await mergeHistory();
    if (merged) return [merged, 'hiring history'];
    return [0, ''];
  }

  // ---- UI: toast + a Save button with an Auto toggle ----
  function toast(msg, ok) {
    let t = document.getElementById('__rm-toast');
    if (!t) { t = document.createElement('div'); t.id = '__rm-toast'; document.body.appendChild(t); }
    t.textContent = msg;
    t.style.cssText = 'position:fixed;bottom:64px;right:16px;z-index:2147483647;max-width:340px;padding:10px 14px;border-radius:8px;font:13px/1.4 system-ui,sans-serif;color:#fff;background:' + (ok ? '#1a7f4b' : '#b23');
    clearTimeout(toast.t); toast.t = setTimeout(() => t.remove(), 3200);
  }

  async function onSave() {
    const [n, what] = await captureCurrent();
    if (!n) return toast("Couldn't read jobs here. Open a posting or a results list, then press Save.", false);
    toast('Saved to Radar Monkey: ' + what + '.', true);
  }

  let autoOn = false, autoBusy = false, lastSig = '';
  async function autoRun() {
    if (!autoOn || autoBusy) return;
    const sig = location.href + '|' + document.body.innerText.length;
    if (sig === lastSig) return;                           // nothing changed
    autoBusy = true;
    try { const [n, what] = await captureCurrent(); if (n) { lastSig = sig; toast('Auto-saved: ' + what + '.', true); } }
    catch (e) {}
    autoBusy = false;
  }

  function bar() {
    if (document.getElementById('__rm-bar')) return;
    const wrap = document.createElement('div');
    wrap.id = '__rm-bar';
    wrap.style.cssText = 'position:fixed;bottom:16px;right:16px;z-index:2147483647;display:flex;gap:8px;align-items:center;font:600 13px system-ui,sans-serif';
    const save = document.createElement('button');
    save.textContent = 'Save to Radar Monkey';
    save.style.cssText = 'padding:10px 14px;border:0;border-radius:8px;cursor:pointer;color:#fff;background:#2563eb;box-shadow:0 2px 8px rgba(0,0,0,.25)';
    save.addEventListener('click', onSave);
    const lbl = document.createElement('label');
    lbl.style.cssText = 'display:flex;gap:6px;align-items:center;padding:8px 10px;border-radius:8px;background:#fff;color:#111;box-shadow:0 2px 8px rgba(0,0,0,.25);cursor:pointer';
    const cb = document.createElement('input'); cb.type = 'checkbox';
    lbl.append(cb, document.createTextNode('Auto'));
    cb.addEventListener('change', async () => {
      autoOn = cb.checked;
      await chrome.storage.local.set({ wwAuto: autoOn });
      toast(autoOn ? 'Auto-save on. Every posting and list you open is saved.' : 'Auto-save off.', true);
      if (autoOn) autoRun();
    });
    wrap.append(save, lbl);
    document.body.appendChild(wrap);
    chrome.storage.local.get('wwAuto').then(({ wwAuto }) => { autoOn = cb.checked = !!wwAuto; if (autoOn) autoRun(); });
  }

  // WaterlooWorks swaps content without full reloads, so watch for changes.
  function watch() {
    let timer = null;
    new MutationObserver(() => { clearTimeout(timer); timer = setTimeout(autoRun, 800); })
      .observe(document.documentElement, { childList: true, subtree: true });
  }

  function start() { bar(); watch(); }
  if (document.body) start();
  else document.addEventListener('DOMContentLoaded', start);
})();
