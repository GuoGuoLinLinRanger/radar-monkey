// Ship a default resume + cover letter with the extension so autofill uploads them out
// of the box. Force-set once per DOCS_VERSION (so a new bundled doc rolls out on reload);
// after that the user can replace either from the options page without it being clobbered.
const DOCS_VERSION = 4;
const B64_CHUNK = 0x8000;
function bufToDataUrl(buf) {
  const bytes = new Uint8Array(buf);
  let bin = '';
  for (let i = 0; i < bytes.length; i += B64_CHUNK) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + B64_CHUNK));
  return 'data:application/pdf;base64,' + btoa(bin);
}
async function bundledDoc(path, name) {
  const buf = await (await fetch(chrome.runtime.getURL(path))).arrayBuffer();
  return { name, type: 'application/pdf', dataUrl: bufToDataUrl(buf) };
}
let _docsReady = null;
async function ensureDocs() {
  if (_docsReady) return _docsReady;
  _docsReady = (async () => {
    const { docsVersion } = await chrome.storage.local.get('docsVersion');
    if (docsVersion === DOCS_VERSION) return;
    try {
      const resume = await bundledDoc('general_resume.pdf', 'Tian Yi Tong - Resume.pdf');
      const cover = await bundledDoc('general_cover.pdf', 'Tian Yi Tong - Cover Letter.pdf');
      await chrome.storage.local.set({ resume, cover, docsVersion: DOCS_VERSION });
    } catch (e) { /* bundled file missing; leave whatever the user already set */ }
  })();
  return _docsReady;
}
chrome.runtime.onInstalled.addListener(ensureDocs);
chrome.runtime.onStartup.addListener(ensureDocs);
ensureDocs();

// Runs the fill script in every frame of the current tab (application forms often live in an iframe).
async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function inject(tabId) {
  await chrome.scripting.executeScript({ target: { tabId, allFrames: true }, files: ['fields.js', 'fill.js'] });
}

async function fill(tabId) {
  await ensureDocs();
  const { profile = {}, answers = [], learned = {}, resume = null, cover = null, overwrite = false } =
    await chrome.storage.local.get(['profile', 'answers', 'learned', 'resume', 'cover', 'overwrite']);
  await inject(tabId);
  const results = await chrome.scripting.executeScript({
    target: { tabId, allFrames: true },
    func: (data) => window.__rmRun ? window.__rmRun(data) : null,
    args: [{ profile, answers, learned, resume, cover, overwrite }],
  });
  const out = { filled: 0, needs: [] };
  for (const r of results) if (r && r.result) { out.filled += r.result.filled; out.needs.push(...r.result.needs); }
  out.needs = [...new Set(out.needs)];
  if (!Object.keys(profile).length) out.noProfile = true;
  return out;
}

async function learn(tabId) {
  await inject(tabId);
  const results = await chrome.scripting.executeScript({ target: { tabId, allFrames: true }, func: () => window.__rmLearn ? window.__rmLearn() : {} });
  const found = Object.assign({}, ...results.map(r => r.result || {}));
  const { learned = {} } = await chrome.storage.local.get('learned');
  Object.assign(learned, found);
  await chrome.storage.local.set({ learned });
  return Object.keys(found).length;
}

function hash(s) { let h = 0; for (const c of s) h = (h * 31 + c.charCodeAt(0)) | 0; return (h >>> 0).toString(36); }

async function logApplied(tabId, status) {
  await inject(tabId);
  const [r] = await chrome.scripting.executeScript({ target: { tabId }, func: () => window.__rmPageInfo() });
  const info = r.result;
  const clean = info.url.split('#')[0].replace(/[?&](utm_[^&]*|source=[^&]*|gh_src=[^&]*)/g, '');
  const id = 'ext:' + hash(clean.replace(/\/(apply|application)\/?$/, ''));
  const { apps = {} } = await chrome.storage.local.get('apps');
  const today = new Date().toLocaleDateString('en-CA');
  const e = apps[id] || { id, title: info.title, company: info.company, url: clean, location: '', kind: '', dates: {}, notes: '', follow_up: '' };
  e.status = status; e.dates[status] = e.dates[status] || today; e.updated = new Date().toISOString();
  if (status === 'applied' && !e.follow_up) e.follow_up = new Date(Date.now() + 14 * 864e5).toLocaleDateString('en-CA');
  apps[id] = e;
  await chrome.storage.local.set({ apps });
  return e;
}

// Writes a tailored answer to a posting-specific question (e.g. "Why this company?") from the
// page's own text + your "about you" note, using your Anthropic key. Called by fill.js when an
// answer is set to [[generate]]. Returns '' if no key, on any error, so the field just stays empty.
async function generateAnswer(msg) {
  const { apiKey = '', genContext = '' } = await chrome.storage.local.get(['apiKey', 'genContext']);
  if (!apiKey) return '';
  const system = 'You write short, specific, genuinely human answers to job-application questions, in the applicant\'s own voice. Rules: first person; concrete and specific to this company and role using the posting text; 3 to 5 sentences; confident but not boastful; plain everyday language. Never use em dashes. Avoid cliches like "I am passionate", "fast-paced environment", "I thrive", "excited for the opportunity". Output only the answer text, nothing else.';
  const user = `QUESTION:\n${msg.question}\n\nABOUT THE APPLICANT:\n${genContext || '(none provided)'}\n\nJOB POSTING / PAGE CONTEXT:\n${(msg.pageText || '').slice(0, 5000)}`;
  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'anthropic-dangerous-direct-browser-access': 'true' },
      body: JSON.stringify({ model: 'claude-sonnet-5-5', max_tokens: 600, system, messages: [{ role: 'user', content: user }] }),
    });
    if (!r.ok) return '';
    const d = await r.json();
    return ((d.content && d.content[0] && d.content[0].text) || '').trim();
  } catch (e) { return ''; }
}

chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  (async () => {
    const tab = await activeTab();
    try {
      if (msg.type === 'fill') reply({ ok: true, ...(await fill(tab.id)) });
      else if (msg.type === 'learn') reply({ ok: true, count: await learn(tab.id) });
      else if (msg.type === 'generate') reply({ ok: true, text: await generateAnswer(msg) });
      else if (msg.type === 'log') reply({ ok: true, entry: await logApplied(tab.id, msg.status || 'applied') });
    } catch (e) {
      reply({ ok: false, error: String(e && e.message || e) });
    }
  })();
  return true;
});

chrome.commands.onCommand.addListener(async (cmd) => {
  if (cmd !== 'fill-page') return;
  const tab = await activeTab();
  try {
    const r = await fill(tab.id);
    chrome.action.setBadgeBackgroundColor({ color: '#0f7b5f' });
    chrome.action.setBadgeText({ tabId: tab.id, text: String(r.filled) });
  } catch (e) {
    chrome.action.setBadgeText({ tabId: tab.id, text: '!' });
  }
});

chrome.runtime.onInstalled.addListener(({ reason }) => { if (reason === 'install') chrome.runtime.openOptionsPage(); });
