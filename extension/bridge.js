// Syncs applications between this extension and your Radar Monkey dashboard tab.
// Only does anything on pages that carry <meta name="radar-monkey">.
(function () {
  if (!document.querySelector('meta[name="radar-monkey"]')) return;
  const target = (location.protocol === 'file:' || location.origin === 'null') ? '*' : location.origin;

  async function send() {
    const { apps = {} } = await chrome.storage.local.get('apps');
    window.postMessage({ rm: 'ext-apps', apps: Object.values(apps) }, target);
  }

  // Jobs you captured on WaterlooWorks (extension/ww.js) get pushed to the dashboard,
  // which merges them into its feed. One-way: the dashboard doesn't write these back.
  async function sendJobs() {
    const { wwJobs = {} } = await chrome.storage.local.get('wwJobs');
    const list = Object.values(wwJobs);
    if (list.length) window.postMessage({ rm: 'ext-jobs', jobs: list }, target);
  }

  async function receive(list) {
    const { apps = {} } = await chrome.storage.local.get('apps');
    let changed = false;
    for (const e of list) {
      if (!e || !e.id) continue;
      for (const old of e.merged_from || []) if (apps[old]) { delete apps[old]; changed = true; }
      const cur = apps[e.id];
      if (e.status === '__deleted') {
        if (cur && (cur.updated || '') <= (e.updated || '')) { delete apps[e.id]; changed = true; }
        continue;
      }
      if (!cur || (e.updated || '') > (cur.updated || '')) { apps[e.id] = e; changed = true; }
    }
    if (changed) await chrome.storage.local.set({ apps });
  }

  async function arm(host) {
    if (!host) return;
    const { armedHosts = {} } = await chrome.storage.local.get('armedHosts');
    armedHosts[host] = Date.now();
    // Keep the list small: drop arms older than 6 hours.
    const cutoff = Date.now() - 6 * 3600e3;
    for (const h of Object.keys(armedHosts)) if (armedHosts[h] < cutoff) delete armedHosts[h];
    await chrome.storage.local.set({ armedHosts });
  }

  window.addEventListener('message', (ev) => {
    if (ev.source !== window || !ev.data) return;
    if (ev.data.rm === 'page-hello') { send(); sendJobs(); }
    if (ev.data.rm === 'page-apps') receive(ev.data.apps || []);
    if (ev.data.rm === 'page-arm') arm(ev.data.host);
  });
  chrome.storage.onChanged.addListener((ch, area) => {
    if (area !== 'local') return;
    if (ch.apps) send();
    if (ch.wwJobs) sendJobs();
  });
  chrome.storage.local.set({ dashboardSeen: location.href.split('#')[0] });
  send();
  sendJobs();
})();
