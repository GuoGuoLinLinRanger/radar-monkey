// Syncs applications between this extension and your Radar Monkey dashboard tab.
// Only does anything on pages that carry <meta name="radar-monkey">.
(function () {
  if (!document.querySelector('meta[name="radar-monkey"]')) return;
  const target = (location.protocol === 'file:' || location.origin === 'null') ? '*' : location.origin;

  async function send() {
    const { apps = {} } = await chrome.storage.local.get('apps');
    window.postMessage({ rm: 'ext-apps', apps: Object.values(apps) }, target);
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

  window.addEventListener('message', (ev) => {
    if (ev.source !== window || !ev.data) return;
    if (ev.data.rm === 'page-hello') send();
    if (ev.data.rm === 'page-apps') receive(ev.data.apps || []);
  });
  chrome.storage.onChanged.addListener((ch, area) => { if (area === 'local' && ch.apps) send(); });
  chrome.storage.local.set({ dashboardSeen: location.href.split('#')[0] });
  send();
})();
