// <wtl> project: watchthelight-labs.github.io | file: src/starfield.js | author: watchthelight </wtl>
// The uprooted.sh starfield, rebuilt: square-pixel stars that twinkle, three depth layers that drift slowly and
// follow the cursor and the scroll position (deeper layers move less), a sage tint on a few stars, and a rare
// shooting star. Static with prefers-reduced-motion; paused while the tab is hidden.
(() => {
  const canvas = document.getElementById("stars");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const LAYERS = [
    { parallax: 0.25, drift: 0.04, scroll: 0.04, size: 1 },
    { parallax: 0.5, drift: 0.07, scroll: 0.09, size: 1 },
    { parallax: 1.0, drift: 0.12, scroll: 0.16, size: 2 },
  ];
  const STAR = [200, 210, 220];
  const SAGE = [122, 170, 126];
  let w = 0, h = 0, dpr = 1, stars = [], shooting = [], raf = 0;
  let px = 0, py = 0, cx = 0, cy = 0, nextShot = 0;

  function seed() {
    const count = Math.floor((w * h) / 7000);
    stars = Array.from({ length: count }, (_, i) => {
      const layer = i % 3;
      return {
        x: Math.random() * w, y: Math.random() * h, layer,
        size: layer === 2 && Math.random() < 0.5 ? 2 : 1,
        a: Math.random() * 0.5 + 0.15, d: Math.random() * 0.003 + 0.001,
        sage: Math.random() < 0.1,
      };
    });
  }

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = window.innerWidth; h = window.innerHeight;
    canvas.width = Math.floor(w * dpr); canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px"; canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    seed();
    if (reduced) draw(0);
  }

  function shoot(t) {
    const angle = Math.PI * (0.15 + Math.random() * 0.2);
    shooting.push({ x: Math.random() * w * 0.8, y: Math.random() * h * 0.35, angle,
      speed: 5 + Math.random() * 5, length: 50 + Math.random() * 60, life: 1, decay: 0.012 + Math.random() * 0.01 });
    nextShot = t + 7000 + Math.random() * 9000;
  }

  function draw(t) {
    ctx.clearRect(0, 0, w, h);
    cx += (px - cx) * 0.04; cy += (py - cy) * 0.04;
    const time = t * 0.001;
    const sy = window.scrollY || 0;
    for (const s of stars) {
      const L = LAYERS[s.layer];
      if (!reduced) {
        s.x -= L.drift; s.y += L.drift * 0.6;
        if (s.x < -2) s.x += w + 4;
        if (s.y > h + 2) s.y -= h + 4;
      }
      let x = s.x + cx * L.parallax * 24;
      let y = s.y + cy * L.parallax * 24 - sy * L.scroll;
      y = ((y % h) + h) % h;
      const a = reduced ? s.a : Math.max(0, s.a + Math.sin(time * s.d * 300 + s.x) * 0.08);
      const [r, g, b] = s.sage ? SAGE : STAR;
      ctx.fillStyle = `rgba(${r},${g},${b},${a})`;
      ctx.fillRect(Math.floor(x), Math.floor(y), s.size, s.size);
    }
    for (let i = shooting.length - 1; i >= 0; i--) {
      const m = shooting[i];
      m.x += Math.cos(m.angle) * m.speed; m.y += Math.sin(m.angle) * m.speed; m.life -= m.decay;
      if (m.life <= 0 || m.x > w + 100 || m.y > h + 100) { shooting.splice(i, 1); continue; }
      const tx = m.x - Math.cos(m.angle) * m.length, ty = m.y - Math.sin(m.angle) * m.length;
      const grad = ctx.createLinearGradient(tx, ty, m.x, m.y);
      grad.addColorStop(0, "rgba(200,210,220,0)");
      grad.addColorStop(1, `rgba(200,210,220,${0.55 * m.life})`);
      ctx.strokeStyle = grad; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(m.x, m.y); ctx.stroke();
      ctx.fillStyle = `rgba(230,236,240,${0.8 * m.life})`;
      ctx.fillRect(Math.floor(m.x), Math.floor(m.y), 2, 2);
    }
  }

  function frame(t) {
    if (!nextShot) nextShot = t + 4000;
    if (t > nextShot) shoot(t);
    draw(t);
    raf = requestAnimationFrame(frame);
  }

  window.addEventListener("resize", resize);
  window.addEventListener("pointermove", (e) => { px = (e.clientX / w - 0.5) * 2; py = (e.clientY / h - 0.5) * 2; },
    { passive: true });
  if (reduced) window.addEventListener("scroll", () => draw(0), { passive: true });
  document.addEventListener("visibilitychange", () => {
    if (reduced) return;
    if (document.hidden) cancelAnimationFrame(raf); else raf = requestAnimationFrame(frame);
  });
  resize();
  if (!reduced) raf = requestAnimationFrame(frame);
})();
