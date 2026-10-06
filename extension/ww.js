// Capture the job posting you're looking at on WaterlooWorks into Radar Monkey.
// Local only: it reads the page you already have open (you're logged in) and saves
// a job record to the extension's storage, which syncs to your dashboard feed.
// It NEVER applies, shortlists, or clicks anything on WaterlooWorks — only reads
// the page when YOU press the button it adds.
(function () {
  if (window.__rmWW || window.top !== window) return;
  window.__rmWW = true;

  const clean = (s) => String(s || '').replace(/\s+/g, ' ').trim();
  const lower = (s) => clean(s).toLowerCase();

  // Build a label -> value map from the posting's tables and definition lists.
  function readFields() {
    const fields = [];
    const add = (label, value) => { label = clean(label); value = clean(value); if (label && value && value.length < 4000) fields.push([lower(label), value]); };
    document.querySelectorAll('table tr').forEach(tr => {
      const cells = tr.querySelectorAll('th,td');
      if (cells.length === 2) add(cells[0].textContent, cells[1].textContent);
    });
    document.querySelectorAll('dl').forEach(dl => {
      const dts = dl.querySelectorAll('dt'), dds = dl.querySelectorAll('dd');
      for (let i = 0; i < Math.min(dts.length, dds.length); i++) add(dts[i].textContent, dds[i].textContent);
    });
    return fields;
  }
  // First field whose label contains any of the given substrings.
  const pick = (fields, ...keys) => { for (const [l, v] of fields) if (keys.some(k => l.includes(k))) return v; return ''; };
  // All fields whose label contains any key, joined (for multi-part descriptions).
  function gather(fields, ...keys) {
    const parts = [];
    for (const [l, v] of fields) if (keys.some(k => l.includes(k))) parts.push(v);
    return parts.join('\n\n');
  }

  function jobId(fields) {
    const n = pick(fields, 'job id', 'posting id', 'job posting id');
    const m = n.match(/\d{3,}/);
    if (m) return 'ww:' + m[0];
    try { const q = new URL(location.href).searchParams; for (const k of ['ck_jobid', 'jobId', 'postingId', 'id']) { const v = q.get(k); if (v && /\d/.test(v)) return 'ww:' + v; } } catch (e) {}
    // Stable fallback from title+company so re-saving updates rather than duplicates.
    const seed = lower(pick(fields, 'job title', 'title') + '|' + pick(fields, 'organization', 'company', 'employer'));
    let h = 0; for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) | 0;
    return 'ww:h' + (h >>> 0).toString(36);
  }

  function modelOf(s) {
    s = lower(s);
    if (s.includes('remote')) return 'Remote';
    if (s.includes('hybrid')) return 'Hybrid';
    if (s.includes('in-person') || s.includes('on-site') || s.includes('onsite') || s.includes('in person')) return 'On-site';
    return '';
  }
  function categoryOf(text) {
    return /machine learning|data scien|deep learning|\bnlp\b|computer vision|\bai\b|\bml\b|data engineer/.test(lower(text)) ? 'AI/ML/Data' : 'Software';
  }

  function scrape() {
    const fields = readFields();
    const title = pick(fields, 'job title', 'position title', 'title');
    const company = pick(fields, 'organization', 'company', 'employer', 'division');
    if (!title || !company) return null;  // not on a posting page
    const city = pick(fields, 'job - city', 'city', 'location');
    const prov = pick(fields, 'province', 'state');
    const country = pick(fields, 'country');
    const loc = [city, prov].filter(Boolean).join(', ') || clean(pick(fields, 'location'));
    const term = pick(fields, 'work term', 'term');
    const model = modelOf(pick(fields, 'location arrangement', 'employment location', 'work location', 'arrangement'));
    const description = gather(fields, 'job summary', 'summary', 'responsibilities', 'required skills', 'skills', 'description');
    const countries = /united states|usa|\bus\b/.test(lower(country)) ? ['US'] : ['CA'];
    return {
      id: jobId(fields), kind: 'intern', title, company, url: location.href.split('#')[0],
      locations: loc ? [loc] : [], countries, terms: term ? [term] : [],
      work_model: model, remote_ok: model === 'Remote', category: categoryOf(title + ' ' + description),
      description, first_seen: new Date().toISOString(),
    };
  }

  function toast(msg, ok) {
    let t = document.getElementById('__rm-toast');
    if (!t) { t = document.createElement('div'); t.id = '__rm-toast'; document.body.appendChild(t); }
    t.textContent = msg;
    t.style.cssText = 'position:fixed;bottom:64px;right:16px;z-index:2147483647;max-width:320px;padding:10px 14px;border-radius:8px;font:13px/1.4 system-ui,sans-serif;color:#fff;background:' + (ok ? '#1a7f4b' : '#b23');
    clearTimeout(toast.t); toast.t = setTimeout(() => { t.remove(); }, 3000);
  }

  async function save() {
    const rec = scrape();
    if (!rec) return toast("Couldn't read a job here. Open a posting first, then press Save.", false);
    const { wwJobs = {} } = await chrome.storage.local.get('wwJobs');
    if (wwJobs[rec.id] && wwJobs[rec.id].first_seen) rec.first_seen = wwJobs[rec.id].first_seen;  // keep original date
    wwJobs[rec.id] = rec;
    await chrome.storage.local.set({ wwJobs });
    toast('Saved to Radar Monkey: ' + rec.title + (rec.company ? ' · ' + rec.company : ''), true);
  }

  function button() {
    if (document.getElementById('__rm-save')) return;
    const b = document.createElement('button');
    b.id = '__rm-save';
    b.textContent = 'Save to Radar Monkey';
    b.style.cssText = 'position:fixed;bottom:16px;right:16px;z-index:2147483647;padding:10px 14px;border:0;border-radius:8px;cursor:pointer;font:600 13px system-ui,sans-serif;color:#fff;background:#2563eb;box-shadow:0 2px 8px rgba(0,0,0,.25)';
    b.addEventListener('click', save);
    document.body.appendChild(b);
  }

  if (document.body) button();
  else document.addEventListener('DOMContentLoaded', button);
})();
