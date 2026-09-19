// Insights visualizations — labels use tentative names, never C-numbers.
async function jget(u) { const r = await fetch(u); return r.json(); }

async function init() {
  const [pts, sizes] = await Promise.all([jget('/api/umap2d'), jget('/api/sizes')]);
  const label = {};
  sizes.forEach(s => { label[s.id] = s.interpretation; });

  // UMAP, grouped + named by tentative interpretation
  const byL = {};
  pts.forEach(p => {
    const l = label[p.c] || ('Group ' + p.c);
    (byL[l] = byL[l] || []).push(p);
  });
  const traces = Object.keys(byL).sort().map(l => {
    const arr = byL[l];
    return {
      x: arr.map(p => p.x), y: arr.map(p => p.y),
      mode: 'markers', type: 'scattergl', name: l,
      text: arr.map(p => `${l} · ${p.f}`),
      marker: { size: 4, opacity: 0.75 },
    };
  });
  Plotly.newPlot('umap', traces, {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#f2f6ff', size: 11 }, margin: { t: 10 },
    xaxis: { title: 'UMAP-1' }, yaxis: { title: 'UMAP-2' },
    legend: { orientation: 'h' },
  }, { responsive: true });

  // Bar chart: aggregate by tentative name (several communities can share
  // one name), top-15 largest first, each row its own gradient hue.
  const agg = {};
  sizes.forEach(d => {
    agg[d.interpretation] = agg[d.interpretation] || { label: d.interpretation, size: 0 };
    agg[d.interpretation].size += d.size;
  });
  const total = sizes.reduce((a, d) => a + d.size, 0);
  const top = Object.values(agg).sort((a, b) => b.size - a.size).slice(0, 15);
  // Plotly draws y[0] at the bottom, so feed ascending to put largest on top.
  const rows = [...top].reverse();
  const colors = rows.map((_, i) => {
    const hue = 45 + (i / Math.max(rows.length - 1, 1)) * 255; // gold -> green -> blue -> purple
    return `hsl(${hue.toFixed(0)},85%,60%)`;
  });
  Plotly.newPlot('sizes', [{
    x: rows.map(d => d.size), y: rows.map(d => d.label),
    type: 'bar', orientation: 'h',
    marker: { color: colors, opacity: 0.9,
      line: { color: 'rgba(255,255,255,.35)', width: 1 } },
    text: rows.map(d => d.size + ' · ' + (d.size / total * 100).toFixed(2) + '%'),
    textposition: 'outside',
    hovertemplate: '%{y}<br>%{x} images (%{text})<extra></extra>',
  }], {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#f2f6ff', size: 12 }, margin: { t: 10, l: 250, r: 90 },
    xaxis: { title: 'Images', gridcolor: 'rgba(139,150,179,.15)' },
    yaxis: { automargin: true },
  }, { responsive: true });
}
init();
