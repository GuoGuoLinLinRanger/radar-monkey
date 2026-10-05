// Opt-in auto-fill. When the "Auto-fill each page" setting is on, this fills the
// visible fields as a page loads and as new fields appear (e.g. Workday steps).
// It uses the same engine as the Fill button and, like it, NEVER clicks next or submit.
(function () {
  if (window.__rmAuto) return;
  window.__rmAuto = true;

  let enabled = false;
  let busy = false;
  let timer = null;
  let observer = null;

  async function getData() {
    return chrome.storage.local.get(['profile', 'answers', 'learned', 'resume', 'overwrite', 'autofill']);
  }

  async function run() {
    if (busy || !enabled) return;
    const data = await getData();
    if (!data.autofill || !data.profile || !Object.keys(data.profile).length) return;
    // Don't fight the user: if they're typing in a field with content, wait and retry.
    const ae = document.activeElement;
    if (ae && /^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName) && ae.value) { schedule(1500); return; }
    busy = true;
    try { if (window.__rmRun) await window.__rmRun(data); } catch (e) {}
    busy = false;
  }

  function schedule(delay) {
    clearTimeout(timer);
    timer = setTimeout(run, delay || 900);
  }

  function watch() {
    if (observer) return;
    observer = new MutationObserver((muts) => {
      if (busy) return;
      for (const m of muts) {
        for (const n of m.addedNodes) {
          if (n.nodeType !== 1) continue;
          if ((n.matches && n.matches('input,select,textarea,button,[role="combobox"]')) ||
              (n.querySelector && n.querySelector('input,select,textarea,[role="combobox"]'))) {
            schedule(); return;
          }
        }
      }
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  async function start() {
    const { autofill } = await chrome.storage.local.get('autofill');
    enabled = !!autofill;
    if (!enabled) return;
    schedule(500);  // initial page
    watch();        // dynamic steps (Workday and friends)
  }

  // React to the toggle being flipped while a page is open.
  chrome.storage.onChanged.addListener((ch, area) => {
    if (area !== 'local' || !ch.autofill) return;
    enabled = !!ch.autofill.newValue;
    if (enabled) { schedule(300); watch(); }
  });

  start();
})();
