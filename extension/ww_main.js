// Runs in the PAGE's JS world (manifest "world": "MAIN") so it can see WaterlooWorks'
// own fetch/XHR calls. Its only job: when you open any one posting, learn the reusable
// session "action" token that the detail request uses, and hand it to the content
// script. It reads nothing else and sends nothing off the page. The token is per-session
// and useless elsewhere. This NEVER triggers applications — it only observes.
(function () {
  if (window.__rmMain) return;
  window.__rmMain = true;

  // A detail response is the posting HTML; it contains these section headers.
  const isDetail = (txt) => !!txt && /Job Posting Information|Job Summary:|Job Responsibilities:/.test(txt);

  function offer(bodyStr, txt) {
    if (!isDetail(txt)) return;
    const m = /(?:^|&)action=([^&]+)/.exec(bodyStr || '');
    if (m) window.postMessage({ rm: 'ww-token', token: decodeURIComponent(m[1]) }, location.origin);
  }

  const bodyToStr = (b) => typeof b === 'string' ? b : (b instanceof URLSearchParams ? b.toString() : '');

  const origFetch = window.fetch;
  window.fetch = function (input, init) {
    const url = (input && input.url) || input || '';
    const body = bodyToStr(init && init.body);
    const p = origFetch.apply(this, arguments);
    if (/\/jobs\.htm/.test(String(url)) && body) {
      p.then(r => r.clone().text()).then(t => offer(body, t)).catch(() => {});
    }
    return p;
  };

  const OrigXHR = window.XMLHttpRequest;
  function PatchedXHR() {
    const x = new OrigXHR();
    let url = '', body = '';
    const open = x.open;
    x.open = function (m, u) { url = u; return open.apply(x, arguments); };
    const send = x.send;
    x.send = function (b) {
      body = bodyToStr(b);
      if (/\/jobs\.htm/.test(String(url)) && body) {
        x.addEventListener('load', () => { try { offer(body, x.responseText); } catch (e) {} });
      }
      return send.apply(x, arguments);
    };
    return x;
  }
  PatchedXHR.prototype = OrigXHR.prototype;
  window.XMLHttpRequest = PatchedXHR;
})();
