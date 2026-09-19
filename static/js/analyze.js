const drop = document.getElementById('drop');
const input = document.getElementById('fileInput');
const st = document.getElementById('upStatus');
const out = document.getElementById('upResult');
const browseBtn = document.getElementById('browseBtn');
const dropPanel = document.getElementById('dropPanel');
const resultPanel = document.getElementById('resultPanel');
const resName = document.getElementById('resName');
const prev = document.getElementById('preview');

browseBtn.addEventListener('click', () => input.click());
['dragover', 'dragenter'].forEach(e => drop.addEventListener(e, ev => { ev.preventDefault(); drop.classList.add('over'); }));
['dragleave', 'drop'].forEach(e => drop.addEventListener(e, ev => { ev.preventDefault(); drop.classList.remove('over'); }));
drop.addEventListener('drop', ev => {
  if (ev.dataTransfer.files.length) { input.files = ev.dataTransfer.files; send(ev.dataTransfer.files[0]); }
});
input.addEventListener('change', () => { if (input.files.length) send(input.files[0]); });
document.getElementById('againBtn').addEventListener('click', () => {
  resultPanel.hidden = true;
  dropPanel.hidden = false;
  out.innerHTML = '';
  input.value = '';
  checkModel();
});

async function checkModel() {
  try {
    const r = await fetch('/api/model-status');
    const j = await r.json();
    if (j.state === 'ready') {
      st.innerHTML = '<span class="ok">Model ready — upload an image.</span>';
      return true;
    }
    if (j.state === 'loading') {
      st.innerHTML = '<span class="warn">Model is loading into memory... this page will update automatically.</span>';
    } else {
      st.innerHTML = `<span class="warn">Model not ready yet (${j.detail || j.state}). ` +
        `The one-time download (~1 GB) may still be running in the background. </span>` +
        `<button class="btn" id="retryBtn" type="button">Check again</button>`;
      const rb = document.getElementById('retryBtn');
      if (rb) rb.addEventListener('click', async () => {
        rb.disabled = true;
        try { await fetch('/api/model-retry', { method: 'POST' }); } catch (e) { /* ignore */ }
        setTimeout(checkModel, 3000);
      });
    }
  } catch (e) {
    st.innerHTML = '<span class="warn">Cannot reach server. Is <code>python app.py</code> running?</span>';
  }
  return false;
}

async function send(f) {
  prev.src = URL.createObjectURL(f);
  out.innerHTML = '';
  resName.textContent = 'Analyzing...';
  dropPanel.hidden = true;
  resultPanel.hidden = false;
  resultPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 10 * 60 * 1000);
  try {
    const fd = new FormData();
    fd.append('image', f);
    const r = await fetch('/api/predict', { method: 'POST', body: fd, signal: ctrl.signal });
    let j;
    try { j = await r.json(); }
    catch { throw new Error('Server returned non-JSON response (HTTP ' + r.status + ')'); }
    if (!r.ok) throw new Error((j.error || 'HTTP ' + r.status) + (j.hint ? ' — ' + j.hint : ''));
    resName.textContent = j.interpretation;
    const nm = (id) => (j.names && j.names[String(id)]) || 'Visual group';
    const votes = Object.entries(j.vote_distribution).map(([c, n]) => `${nm(c)} ×${n}`).join(' · ');
    const topNames = j.top5.map(t => `<li>${nm(t.community)} · similarity ${t.score} · ${t.filename}</li>`).join('');
    out.innerHTML = `
      <p>Neighbour agreement: <strong>${j.neighbour_agreement_pct}%</strong>
        <span class="muted">(kNN vote share, not a classifier probability)</span></p>
      <p>Community statistics: ${j.size} images · ${j.share_pct}% of dataset · coherence ${j.coherence}</p>
      <p class="muted">Votes: ${votes}</p>
      <h4>Most similar reference images</h4>
      <ul>${topNames}</ul>`;
  } catch (e) {
    resName.textContent = 'Analysis failed';
    out.innerHTML = '<p><span class="err">Failed: ' + (e.name === 'AbortError'
      ? 'request timed out after 10 minutes.'
      : String(e.message || e)) + '</span></p>';
  } finally {
    clearTimeout(timer);
  }
}

checkModel();
setInterval(async () => {
  if (!dropPanel.hidden && !document.getElementById('retryBtn')) checkModel();
}, 15000);
