const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const out = (html) => { $('out').innerHTML = html; };
function send(type, extra) { return chrome.runtime.sendMessage(Object.assign({ type }, extra)); }
function busy(btn, on) { btn.disabled = on; }

$('fill').addEventListener('click', async (e) => {
  busy(e.currentTarget, true); out('Filling…');
  const r = await send('fill');
  busy(e.currentTarget, false);
  if (!r.ok) return out(`Couldn't run on this page: ${esc(r.error)}`);
  if (r.noProfile) return out('Add your profile first. <a href="#" id="go">Open settings</a>');
  out(`<span class="ok">Filled ${r.filled} field${r.filled === 1 ? '' : 's'}.</span> Green = filled, dashed = needs you.` +
    (r.needs.length ? `<div>Check these yourself:</div><ul>${r.needs.slice(0, 8).map(n => `<li>${esc(n)}</li>`).join('')}</ul>` : '') +
    '<div class="hint" style="margin-top:6px">Review everything, then submit yourself.</div>');
});
$('learn').addEventListener('click', async () => {
  const r = await send('learn');
  out(r.ok ? `Saved ${r.count} answer${r.count === 1 ? '' : 's'}. They'll be reused when a question matches.` : esc(r.error));
});
async function log(status) {
  const r = await send('log', { status });
  if (!r.ok) return out(esc(r.error));
  out(`<span class="ok">${status === 'applied' ? 'Logged as applied' : 'Saved'}:</span> ${esc(r.entry.company)}: ${esc(r.entry.title)}<div class="hint">Shows up in your tracker next time the dashboard is open.</div>`);
}
$('applied').addEventListener('click', () => log('applied'));
$('save').addEventListener('click', () => log('saved'));
document.addEventListener('click', (e) => { if (e.target.id === 'settings' || e.target.id === 'go') { e.preventDefault(); chrome.runtime.openOptionsPage(); } });
chrome.storage.local.get(['dashboardUrl', 'dashboardSeen']).then(({ dashboardUrl, dashboardSeen }) => {
  const url = dashboardUrl || dashboardSeen;
  if (url) { $('dash').hidden = false; $('dash').onclick = (e) => { e.preventDefault(); chrome.tabs.create({ url: url + '#tracker' }); }; }
});
