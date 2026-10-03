// Runs the fill script in every frame of the current tab (application forms often live in an iframe).
async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function inject(tabId) {
  await chrome.scripting.executeScript({ target: { tabId, allFrames: true }, files: ['fields.js', 'fill.js'] });
}

async function fill(tabId) {
  const { profile = {}, answers = [], learned = {}, resume = null, overwrite = false } =
    await chrome.storage.local.get(['profile', 'answers', 'learned', 'resume', 'overwrite']);
  await inject(tabId);
  const results = await chrome.scripting.executeScript({
    target: { tabId, allFrames: true },
    func: (data) => window.__rmRun ? window.__rmRun(data) : null,
    args: [{ profile, answers, learned, resume, overwrite }],
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

chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  (async () => {
    const tab = await activeTab();
    try {
      if (msg.type === 'fill') reply({ ok: true, ...(await fill(tab.id)) });
      else if (msg.type === 'learn') reply({ ok: true, count: await learn(tab.id) });
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
