// Living hero background: glowing particles drift inward and converge
// toward the title, with faint circuit links — a "motion video" feel.
(function () {
  const cv = document.getElementById('heroCanvas');
  if (!cv) return;
  const ctx = cv.getContext('2d');
  const hero = document.getElementById('heroTop');
  let W, H, parts = [];
  const N = 90;

  function size() {
    const r = hero.getBoundingClientRect();
    W = cv.width = r.width;
    H = cv.height = r.height;
  }
  function spawn(edge) {
    const cx = W / 2, cy = H * 0.42;
    let x, y;
    if (edge) {
      const side = Math.floor(Math.random() * 4);
      x = side === 0 ? -20 : side === 1 ? W + 20 : Math.random() * W;
      y = side === 2 ? -20 : side === 3 ? H + 20 : Math.random() * H;
    } else { x = Math.random() * W; y = Math.random() * H; }
    const dx = cx - x, dy = cy - y;
    const d = Math.hypot(dx, dy) || 1;
    const sp = 0.25 + Math.random() * 0.55;
    return {
      x, y, vx: (dx / d) * sp, vy: (dy / d) * sp,
      r: 1 + Math.random() * 2.2, life: 0,
      max: 260 + Math.random() * 260,
      hue: Math.random() < 0.75 ? '0,242,254' : '79,172,254',
    };
  }
  function reset() {
    parts = [];
    for (let i = 0; i < N; i++) parts.push(spawn(false));
  }
  size(); reset();
  addEventListener('resize', () => { size(); reset(); });

  let t = 0;
  (function frame() {
    t += 0.016;
    ctx.clearRect(0, 0, W, H);
    const cx = W / 2, cy = H * 0.42;
    // soft core glow behind title, gently pulsing
    const pulse = 0.10 + 0.035 * Math.sin(t * 1.4);
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.min(W, H) * 0.55);
    g.addColorStop(0, `rgba(0,242,254,${pulse})`);
    g.addColorStop(1, 'rgba(0,242,254,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    for (const p of parts) {
      p.x += p.vx + Math.sin(t * 2 + p.y * 0.02) * 0.15;
      p.y += p.vy + Math.cos(t * 1.7 + p.x * 0.02) * 0.15;
      p.life++;
      const dc = Math.hypot(cx - p.x, cy - p.y);
      const fade = Math.max(0, 1 - dc / (Math.min(W, H) * 0.6));
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, 7);
      ctx.fillStyle = `rgba(${p.hue},${0.15 + fade * 0.65})`;
      ctx.shadowColor = `rgba(${p.hue},.9)`;
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0;
      if (p.life > p.max || dc < 26) Object.assign(p, spawn(true));
    }
    // faint links between near neighbours = circuit feel
    ctx.lineWidth = 0.6;
    for (let i = 0; i < parts.length; i += 3) {
      for (let j = i + 3; j < Math.min(i + 9, parts.length); j += 3) {
        const a = parts[i], b = parts[j];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 110) {
          ctx.strokeStyle = `rgba(0,242,254,${(1 - d / 110) * 0.14})`;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
    }
    requestAnimationFrame(frame);
  })();
})();
