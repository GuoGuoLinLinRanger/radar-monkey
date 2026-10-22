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
  let scrolling = null;   // truthy while the user is actively scrolling
  // Only react to genuinely new form fields — not every button/tooltip/row a page adds while
  // scrolling. Custom dropdowns are still caught via their combobox/listbox roles.
  const FIELD_SEL = 'input,select,textarea,[role="combobox"],[aria-haspopup="listbox"]';

  async function getData() {
    return chrome.storage.local.get(['profile', 'answers', 'learned', 'resume', 'cover', 'overwrite', 'autofill', 'armedHosts']);
  }

  // Armed = you opened this site from the dashboard. Keeps auto-fill alive through
  // the whole application (all its pages) without the global toggle.
  function isArmed(armedHosts) {
    if (!armedHosts) return false;
    const ts = armedHosts[location.host];
    return !!ts && (Date.now() - ts) < 6 * 3600e3;
  }

  async function run() {
    if (busy) return;
    if (scrolling) { schedule(500); return; }   // wait until scrolling stops, then fill once
    const data = await getData();
    if (!data.autofill && !isArmed(data.armedHosts)) return;
    if (!data.profile || !Object.keys(data.profile).length) return;
    // Don't fight the user: if they're typing in a field with content, wait and retry.
    const ae = document.activeElement;
    if (ae && /^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName) && ae.value) { schedule(1500); return; }
    busy = true;
    try { if (window.__rmRun) await window.__rmRun({ ...data, auto: true }); } catch (e) {}
    busy = false;
  }

  function schedule(delay) {
    clearTimeout(timer);
    timer = setTimeout(run, delay || 1100);
  }

  function watch() {
    if (observer) return;
    observer = new MutationObserver((muts) => {
      if (busy) return;
      for (const m of muts) {
        for (const n of m.addedNodes) {
          if (n.nodeType !== 1) continue;
          if ((n.matches && n.matches(FIELD_SEL)) ||
              (n.querySelector && n.querySelector(FIELD_SEL))) {
            schedule(); return;
          }
        }
      }
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  async function start() {
    const { autofill, armedHosts } = await chrome.storage.local.get(['autofill', 'armedHosts']);
    enabled = !!autofill || isArmed(armedHosts);
    if (!enabled) return;
    schedule(500);  // initial page
    watch();        // dynamic steps (Workday and friends)
  }

  // React to the global toggle flipping, or this host being armed, while a page is open.
  chrome.storage.onChanged.addListener((ch, area) => {
    if (area !== 'local') return;
    if (ch.autofill) enabled = !!ch.autofill.newValue || enabled;
    if (ch.armedHosts && isArmed(ch.armedHosts.newValue)) enabled = true;
    if ((ch.autofill || ch.armedHosts) && enabled) { schedule(300); watch(); }
  });

  // Defer fills while the user scrolls, so a page that lazy-renders on scroll doesn't make us
  // re-run (and jump focus) on every frame. We only ever fill once scrolling settles.
  addEventListener('scroll', () => {
    if (!enabled) return;
    clearTimeout(scrolling);
    scrolling = setTimeout(() => { scrolling = null; }, 400);
    if (timer) schedule(600);   // push any pending fill past the scroll
  }, { passive: true, capture: true });

  start();
})();
