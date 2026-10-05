const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const { PROFILE } = window.RM_FIELDS;

const STARTER_ANSWERS = [
  { q: 'why do you want to work', a: '' },
  { q: 'tell us about a project', a: '' },
  { q: 'salary expectation', a: 'Open to discussing; flexible based on the role.' },
  { q: 'notice period', a: 'Available from my start date' },
  { q: 'security clearance', a: 'No' },
];

function renderProfile(p) {
  const groups = {};
  for (const [key, label, def, group, hint] of PROFILE) (groups[group] = groups[group] || []).push([key, label, def, hint]);
  $('profile').innerHTML = Object.entries(groups).map(([g, items]) => `<h2>${esc(g)}</h2><div class="grid">${items.map(([k, l, d, h]) =>
    `<label>${esc(l)}${h ? `<span class="hint">${esc(h)}</span>` : ''}<input type="text" data-k="${k}" value="${esc(p[k] ?? d)}"></label>`).join('')}</div>`).join('');
}
function answerRow(a) {
  const d = document.createElement('div'); d.className = 'qa';
  d.innerHTML = `<input type="text" placeholder="Question contains…" value="${esc(a.q)}"><textarea placeholder="Your answer">${esc(a.a)}</textarea><button class="btn" title="Remove">✕</button>`;
  d.querySelector('button').onclick = () => d.remove();
  $('answers').appendChild(d);
}
function renderLearned(learned) {
  const ent = Object.entries(learned);
  $('learned').innerHTML = ent.length ? '' : '<div class="hint" style="display:block">Nothing yet.</div>';
  for (const [q, a] of ent) {
    const d = document.createElement('div');
    d.innerHTML = `<span>${esc(q)}</span><span title="${esc(a)}">${esc(a)}</span><button class="btn" style="padding:1px 8px">✕</button>`;
    d.querySelector('button').onclick = async () => { const { learned = {} } = await chrome.storage.local.get('learned'); delete learned[q]; await chrome.storage.local.set({ learned }); d.remove(); };
    $('learned').appendChild(d);
  }
}

async function load() {
  const s = await chrome.storage.local.get(['profile', 'answers', 'learned', 'resume', 'overwrite', 'dashboardUrl', 'dashboardSeen', 'apiKey', 'genContext']);
  renderProfile(s.profile || {});
  $('answers').innerHTML = '';
  (s.answers && s.answers.length ? s.answers : STARTER_ANSWERS).forEach(answerRow);
  renderLearned(s.learned || {});
  $('resume-name').textContent = s.resume ? `Current: ${s.resume.name}` : 'No resume yet';
  $('overwrite').checked = !!s.overwrite;
  $('dashboardUrl').value = s.dashboardUrl || s.dashboardSeen || '';
  $('apiKey').value = s.apiKey || '';
  $('genContext').value = s.genContext || '';
}

async function save() {
  const profile = {};
  document.querySelectorAll('[data-k]').forEach(i => profile[i.dataset.k] = i.value.trim());
  const answers = [...document.querySelectorAll('.qa')].map(r => ({ q: r.querySelector('input').value.trim(), a: r.querySelector('textarea').value })).filter(x => x.q && x.a);
  await chrome.storage.local.set({ profile, answers, overwrite: $('overwrite').checked, dashboardUrl: $('dashboardUrl').value.trim(), apiKey: $('apiKey').value.trim(), genContext: $('genContext').value.trim() });
  $('saved').hidden = false; setTimeout(() => $('saved').hidden = true, 1600);
}

$('save').onclick = save;
$('add-answer').onclick = () => answerRow({ q: '', a: '' });
$('resume').onchange = (e) => {
  const f = e.target.files[0]; if (!f) return;
  const r = new FileReader();
  r.onload = async () => { await chrome.storage.local.set({ resume: { name: f.name, type: f.type, dataUrl: r.result } }); $('resume-name').textContent = `Current: ${f.name}`; };
  r.readAsDataURL(f);
};
$('export').onclick = async () => {
  const s = await chrome.storage.local.get(['profile', 'answers', 'learned', 'overwrite', 'dashboardUrl']);
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(s, null, 1)], { type: 'application/json' }));
  a.download = 'radar-monkey-autofill-settings.json'; a.click();
};
$('import').onchange = async (e) => {
  const f = e.target.files[0]; if (!f) return;
  try {
    const d = JSON.parse(await f.text());
    const keep = {}; for (const k of ['profile', 'answers', 'learned', 'overwrite', 'dashboardUrl']) if (k in d) keep[k] = d[k];
    await chrome.storage.local.set(keep); await load();
  } catch (err) { alert('That file is not a Radar Monkey settings export.'); }
};
load();
