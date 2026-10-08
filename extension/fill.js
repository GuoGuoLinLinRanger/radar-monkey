// Radar Monkey autofill engine. Injected only when you click "Fill" (or press Alt+Shift+F).
// It types into fields the same way you would, highlights what it filled, and NEVER clicks submit.
(function () {
  if (window.__rmRun) return;
  const { RULES, DECLINE } = window.RM_FIELDS;
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const norm = (s) => String(s || '').toLowerCase().replace(/\s+/g, ' ').replace(/[*:?]+/g, '').trim();
  const GOOD = '2px solid #0f7b5f', TODO = '2px dashed #d08a00';

  // ---------- reading the page ----------
  function visible(el) {
    if (!el || el.disabled) return false;
    if (el.type === 'hidden') return false;
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    // file inputs and radios are often visually hidden behind a styled label
    if (el.type === 'file' || el.type === 'radio' || el.type === 'checkbox') return st.display !== 'none';
    return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none';
  }
  function textOf(el) { return el ? (el.innerText || el.textContent || '').trim() : ''; }
  function labelFor(el) {
    const parts = [];
    const by = el.getAttribute('aria-labelledby');
    if (by) by.split(/\s+/).forEach(id => { const x = document.getElementById(id); if (x) parts.push(textOf(x)); });
    if (el.labels && el.labels.length) parts.push(...[...el.labels].map(textOf));
    if (el.getAttribute('aria-label')) parts.push(el.getAttribute('aria-label'));
    if (!parts.join('').trim()) {
      const wrap = el.closest('label'); if (wrap) parts.push(textOf(wrap));
    }
    if (!parts.join('').trim() && el.placeholder) parts.push(el.placeholder);
    if (!parts.join('').trim()) {
      // walk up a few levels and take the first bit of question-like text
      let p = el.parentElement;
      for (let i = 0; i < 4 && p; i++, p = p.parentElement) {
        const lab = p.querySelector('label, legend, [class*="label" i], [data-automation-id*="formLabel" i]');
        if (lab && !lab.contains(el) && textOf(lab)) { parts.push(textOf(lab)); break; }
      }
    }
    return parts.join(' ').replace(/\s+/g, ' ').trim().slice(0, 300);
  }
  function hints(el) {
    return [el.name, el.id, el.getAttribute('data-automation-id'), el.getAttribute('autocomplete')].filter(Boolean).join(' ').replace(/[_\-.\[\]]/g, ' ');
  }
  function questionFor(el) {
    // for radio groups / custom widgets: fieldset legend, role=radiogroup label, or nearest question text
    const fs = el.closest('fieldset');
    if (fs) { const lg = fs.querySelector('legend'); if (lg && textOf(lg)) return textOf(lg); }
    const grp = el.closest('[role="radiogroup"], [role="group"]');
    if (grp) { const l = labelFor(grp); if (l) return l; }
    const isOptionLabel = (lab) => {
      if (lab.querySelector('input')) return true;
      const f = lab.htmlFor && document.getElementById(lab.htmlFor);
      return !!(f && (f.type === 'radio' || f.type === 'checkbox'));
    };
    let p = el.parentElement;
    for (let i = 0; i < 5 && p; i++, p = p.parentElement) {
      for (const lab of p.querySelectorAll('legend, label, [class*="question" i], [data-automation-id*="formLabel" i], [class*="label" i]')) {
        if (lab.contains(el) || isOptionLabel(lab)) continue;
        if (textOf(lab).length > 3) return textOf(lab);
      }
    }
    return labelFor(el);
  }
  const isRequired = (el, label) => el.required || el.getAttribute('aria-required') === 'true' || /\*\s*$/.test(label);

  // ---------- deciding what goes where ----------
  function keyFor(desc) {
    const d = norm(desc);
    for (const [key, re] of RULES) if (re.test(d)) return key;
    return null;
  }
  function valueFor(key, desc, el, P) {
    const d = norm(desc);
    const ca = /canad/.test(d);
    switch (key) {
      case 'full_name': return [P.first_name, P.last_name].filter(Boolean).join(' ');
      case 'preferred_name': return P.preferred_name || P.first_name;
      case 'work_auth': return ca ? P.work_auth_ca : P.work_auth_us;
      case 'sponsor': return ca ? P.need_sponsor_ca : P.need_sponsor_us;
      case 'grad': {
        if (el && el.type === 'month') return P.grad_year && `${P.grad_year}-${String(monthNum(P.grad_month)).padStart(2, '0')}`;
        if (el && el.type === 'date') return P.grad_year && `${P.grad_year}-${String(monthNum(P.grad_month)).padStart(2, '0')}-01`;
        if (/month/.test(d)) return P.grad_month;
        if (/year/.test(d)) return P.grad_year;
        return [P.grad_month, P.grad_year].filter(Boolean).join(' ');
      }
      case 'phone': return P.phone;
      case 'phone_ext': case 'middle_name': case 'address2': return '';
      default: return P[key] || '';
    }
  }
  function monthNum(m) {
    const i = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'].indexOf(norm(m).slice(0, 3));
    return i < 0 ? (parseInt(m) || 1) : i + 1;
  }
  function customFor(desc, answers) {
    const d = norm(desc);
    for (const a of answers || []) {
      const q = (a.q || '').trim();
      if (!q) continue;
      if (q.startsWith('/') && q.lastIndexOf('/') > 0) {
        try { if (new RegExp(q.slice(1, q.lastIndexOf('/')), q.slice(q.lastIndexOf('/') + 1) || 'i').test(desc)) return a.a; } catch (e) {}
      } else if (d.includes(norm(q))) return a.a;
    }
    return null;
  }

  // ---------- choosing among options ----------
  const YES = ['yes', 'y', 'true', 'i am', 'i do', 'i will', 'i have'];
  const NO = ['no', 'n', 'false', 'i am not', 'i do not', "i don't", 'i will not', 'i have not', 'none'];
  const DECL = ['decline', 'prefer not', "don't wish", 'do not wish', 'not to answer', 'not to disclose', 'choose not', 'not wish to', 'rather not', 'not specified', 'i don’t wish'];
  function score(opt, want) {
    const o = norm(opt), w = norm(want);
    if (!o || !w) return 0;
    if (/^(select|choose|--|please select)/.test(o)) return 0;
    if (o === w) return 100;
    if (DECL.some(x => w.includes(x))) return DECL.some(x => o.includes(x)) ? 90 : 0;
    if (YES.includes(w)) return YES.some(x => o === x || o.startsWith(x + ' ') || o.startsWith(x + ',')) ? 90 : 0;
    if (NO.includes(w)) return NO.some(x => o === x || o.startsWith(x + ' ') || o.startsWith(x + ',')) ? 90 : 0;
    if (o.startsWith(w)) return 80;
    if (o.includes(w)) return 65;
    if (w.includes(o) && o.length > 2) return 55;
    // loose: every word of the answer appears
    const ws = w.split(' ').filter(x => x.length > 2);
    if (ws.length && ws.every(x => o.includes(x))) return 50;
    return 0;
  }
  function best(options, want, textFn) {
    let top = null, s = 0;
    for (const o of options) { const v = score(textFn(o), want); if (v > s) { s = v; top = o; } }
    return s >= 50 ? top : null;
  }
  // An answer can list fallbacks with "|", e.g. "Asian | Chinese". Try each in order
  // and take the first that matches an option, so forms that offer only the specific
  // wording ("Chinese") and forms that offer only the general one ("Asian") both fill.
  const alts = (v) => String(v || '').split('|').map(s => s.trim()).filter(Boolean);
  function bestAny(options, wants, textFn) {
    for (const w of wants) { const hit = best(options, w, textFn); if (hit) return hit; }
    return null;
  }

  // ---------- writing to the page ----------
  function setValue(el, v) {
    const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : el instanceof HTMLSelectElement ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    el.focus();
    setter.call(el, v);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
  }
  function mark(el, ok) { try { el.style.outline = ok ? GOOD : TODO; el.style.outlineOffset = '1px'; } catch (e) {} }
  function clickLike(el) {
    el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
    el.click();
  }
  async function pickFromListbox(want) {
    const wants = Array.isArray(want) ? want : alts(want);
    for (let i = 0; i < 10; i++) {
      await sleep(120);
      const opts = [...document.querySelectorAll('[role="option"], [data-automation-id="promptOption"]')].filter(visible);
      if (opts.length) {
        const hit = bestAny(opts, wants, textOf);
        if (hit) { clickLike(hit); await sleep(200); return true; }
        return false;
      }
    }
    return false;
  }

  // ---------- main ----------
  window.__rmRun = async function (data) {
    const P = data.profile || {};
    const answers = (data.answers || []).concat(Object.entries(data.learned || {}).map(([q, a]) => ({ q, a })));
    const overwrite = !!data.overwrite;
    const report = { filled: 0, needs: [], frame: location.host };
    const done = new Set();

    const resolve = (desc, el) => {
      const custom = customFor(desc, answers);
      if (custom != null) return { key: 'custom', value: custom };
      const key = keyFor(desc);
      if (!key) return null;
      return { key, value: valueFor(key, desc, el, P) };
    };

    // 1) plain inputs, textareas, selects
    const fields = [...document.querySelectorAll('input, textarea, select')].filter(visible);
    for (const el of fields) {
      if (done.has(el)) continue;
      const t = (el.type || '').toLowerCase();
      if (['submit', 'button', 'reset', 'image', 'password', 'search', 'checkbox'].includes(t)) continue;
      const label = labelFor(el);
      const desc = (label + ' ' + hints(el)).trim();

      if (t === 'file') {
        if (data.resume && /resume|cv\b|curriculum/i.test(desc + ' ' + questionFor(el)) && !/cover/i.test(label) && !el.files.length) {
          try {
            const blob = await (await fetch(data.resume.dataUrl)).blob();
            const dt = new DataTransfer();
            dt.items.add(new File([blob], data.resume.name, { type: data.resume.type || blob.type }));
            el.files = dt.files;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            report.filled++; mark(el.closest('div') || el, true);
          } catch (e) { report.needs.push('Resume upload'); }
        }
        continue;
      }

      if (t === 'radio') {
        const name = el.name;
        const group = name ? fields.filter(x => x.type === 'radio' && x.name === name) : [el];
        group.forEach(x => done.add(x));
        if (group.some(x => x.checked) && !overwrite) continue;
        const q = questionFor(el);
        const r = resolve(q + ' ' + hints(el), el);
        if (!r || !r.value) { if (isRequired(el, q)) report.needs.push(q.slice(0, 80)); continue; }
        const hit = bestAny(group, alts(r.value), labelFor);
        if (hit) { clickLike(hit); report.filled++; mark(hit.closest('label') || hit, true); }
        else report.needs.push(q.slice(0, 80));
        continue;
      }

      const r = resolve(desc, el);
      const hasValue = el.tagName === 'SELECT' ? (el.selectedIndex > 0 && norm(el.options[el.selectedIndex].text) && !/select|choose/.test(norm(el.options[el.selectedIndex].text))) : !!el.value;
      if (hasValue && !overwrite) continue;
      if (!r || r.value == null || r.value === '') {
        if (isRequired(el, label) && !hasValue) { report.needs.push(label.slice(0, 80) || hints(el)); mark(el, false); }
        continue;
      }

      if (el.tagName === 'SELECT') {
        const hit = bestAny([...el.options], alts(r.value), o => o.text);
        if (hit) { setValue(el, hit.value); report.filled++; mark(el, true); }
        else { report.needs.push(label.slice(0, 80)); mark(el, false); }
        continue;
      }

      const combo = el.getAttribute('role') === 'combobox' || el.getAttribute('aria-autocomplete') === 'list';
      const vals = alts(r.value);
      setValue(el, vals[0]);
      if (combo) {
        const ok = await pickFromListbox(vals);
        if (!ok) el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      }
      report.filled++; mark(el, true);
    }

    // 2) custom dropdown buttons (Workday and friends)
    const buttons = [...document.querySelectorAll('button[aria-haspopup="listbox"], [role="button"][aria-haspopup="listbox"], div[role="combobox"]:not(:has(input))')].filter(visible);
    for (const b of buttons) {
      const label = labelFor(b) || questionFor(b);
      const current = norm(textOf(b));
      if (current && !/select one|select|choose/.test(current) && !overwrite) continue;
      const r = resolve(label + ' ' + hints(b), b);
      if (!r || !r.value) { if (isRequired(b, label)) report.needs.push(label.slice(0, 80)); continue; }
      clickLike(b);
      const ok = await pickFromListbox(r.value);
      if (ok) { report.filled++; mark(b, true); }
      else { document.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); report.needs.push(label.slice(0, 80)); mark(b, false); }
      await sleep(150);
    }

    report.needs = [...new Set(report.needs.filter(Boolean))];
    return report;
  };

  // "Remember my answers": save what you typed into questions the profile doesn't cover.
  window.__rmLearn = function () {
    const out = {};
    for (const el of document.querySelectorAll('input, textarea, select')) {
      if (!visible(el)) continue;
      const t = (el.type || '').toLowerCase();
      if (['submit', 'button', 'hidden', 'password', 'file', 'checkbox', 'search'].includes(t)) continue;
      let label, value;
      if (t === 'radio') { if (!el.checked) continue; label = questionFor(el); value = labelFor(el); }
      else if (el.tagName === 'SELECT') { if (el.selectedIndex <= 0) continue; label = labelFor(el); value = el.options[el.selectedIndex].text; }
      else { label = labelFor(el); value = el.value; }
      label = norm(label);
      if (!value || !label || label.length < 6 || label.length > 200) continue;
      if (keyFor(label + ' ' + hints(el))) continue; // already covered by the profile
      out[label] = String(value).slice(0, 4000);
    }
    return out;
  };

  // Page info for "I applied"
  window.__rmPageInfo = function () {
    const og = (p) => (document.querySelector(`meta[property="og:${p}"]`) || {}).content || '';
    const h1 = textOf(document.querySelector('h1, [data-automation-id="jobPostingHeader"]'));
    const hostCo = (() => {
      const h = location.host, p = location.pathname.split('/').filter(Boolean);
      if (/myworkdayjobs|myworkdaysite/.test(h)) return h.split('.')[0];
      if (/greenhouse|lever|ashbyhq/.test(h)) return p[0] || '';
      return og('site_name') || h.replace(/^www\.|^careers\.|^jobs\./, '').split('.')[0];
    })();
    return { url: location.href, title: h1 || og('title') || document.title, company: hostCo.replace(/[-_]/g, ' ') };
  };
})();
