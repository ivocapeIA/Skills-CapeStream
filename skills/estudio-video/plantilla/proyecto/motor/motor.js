// Motor de la pieza: todo se dibuja en función del tiempo t (segundos), sin
// transiciones ni animaciones CSS, para que cada cuadro salga igual siempre.
// La pieza define window.render(t) y lee sus textos/colores de window.VAR.
// render.mjs escribe out/datos.js (VIDEO, VARIANTES, CLIPS) antes de abrirla.
// Basado en el motor de videos/10-carteleria-monitor.
(function () {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const ease = {
    lin: k => k,
    out: k => 1 - Math.pow(1 - k, 3),
    in: k => k * k * k,
    inOut: k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
    expo: k => (k >= 1 ? 1 : 1 - Math.pow(2, -10 * k)),
    back: k => 1 + 2.4 * Math.pow(k - 1, 3) + 1.4 * Math.pow(k - 1, 2),
    sine: k => 0.5 - 0.5 * Math.cos(Math.PI * k),
    elastic: k => (k <= 0 ? 0 : k >= 1 ? 1 : Math.pow(2, -9 * k) * Math.sin((k * 10 - 0.75) * (2 * Math.PI / 3)) + 1),
  };
  // progreso 0..1 entre a y b, con curva
  const k = (t, a, b, e = ease.out) => e(clamp((t - a) / (b - a)));
  // entra en [a, a+inD] y sale en [b-outD, b]
  const win = (t, a, b, inD = 0.4, outD = 0.4, e = ease.out) => Math.min(k(t, a, a + inD, e), 1 - k(t, b - outD, b, ease.in));

  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];

  function css(el, props) {
    for (const p in props) {
      const v = props[p];
      if (p.startsWith("--")) el.style.setProperty(p, v);
      else el.style[p] = v;
    }
  }

  // Muestra el elemento solo si está "vivo" (ahorra trabajo de pintado)
  function vis(el, on) {
    el.style.visibility = on ? "visible" : "hidden";
  }

  // Ruido determinista (para temblores, partículas)
  function hash(n) {
    const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
    return x - Math.floor(x);
  }
  function noise1(x) {
    const i = Math.floor(x), f = x - i;
    return lerp(hash(i), hash(i + 1), f * f * (3 - 2 * f));
  }

  // ---- variante activa: ?v=B en la URL (por defecto, la primera)
  const VIDEO = window.VIDEO || { w: innerWidth, h: innerHeight, fps: 30, dur: 15 };
  const VARIANTES = window.VARIANTES || { A: {} };
  const vid = new URLSearchParams(location.search).get("v") || Object.keys(VARIANTES)[0];
  window.VAR = VARIANTES[vid];
  if (!window.VAR) throw new Error("variante desconocida: " + vid);
  window.VAR.id = vid;
  window.DUR = window.VAR.dur || VIDEO.dur;

  // ---- clips: secuencias de cuadros JPG pre-extraídas por frames.mjs
  const pending = new Set();
  const CLIPS = window.CLIPS || {};
  function clip(img, id, localT, opts = {}) {
    const c = CLIPS[id];
    if (!c) throw new Error("clip desconocido: " + id + " (¿corriste node frames.mjs?)");
    const speed = opts.speed ?? c.speed ?? 1;
    let i = Math.floor(Math.max(0, localT) * speed * c.fps + 1e-6);
    if (opts.loop) i = i % c.count;
    i = Math.min(c.count - 1, i) + 1;
    const src = `out/frames/${id}/${String(i).padStart(4, "0")}.jpg`;
    if (img.dataset.src !== src) {
      img.dataset.src = src;
      img.src = src;
      const p = img.decode().catch(() => {}).finally(() => pending.delete(p));
      pending.add(p);
    }
  }

  // Texto que se arma letra por letra: envuelve cada letra en un span
  function splitChars(el) {
    if (el.dataset.split) return $$(".ch", el);
    const words = el.textContent.split(" ");
    el.innerHTML = words.map(w => `<span class="w">${[...w].map(c => `<span class="ch">${c}</span>`).join("")}</span>`).join(" ");
    el.dataset.split = 1;
    return $$(".ch", el);
  }

  // ---- subtítulos: agrupa las palabras de la voz (VAR.palabras: [{w, s, e}])
  // en renglones cortos y devuelve el renglón y la palabra que suenan en t.
  function renglones(palabras, maxCar = 22, maxPal = 4) {
    const out = [];
    let cur = [];
    for (const p of palabras || []) {
      const largo = cur.map(x => x.w).join(" ").length + p.w.length + 1;
      const pausa = cur.length && p.s - cur[cur.length - 1].e > 0.35;
      if (cur.length && (largo > maxCar || cur.length >= maxPal || pausa)) { out.push(cur); cur = []; }
      cur.push(p);
      if (/[.?!…]$/.test(p.w)) { out.push(cur); cur = []; }
    }
    if (cur.length) out.push(cur);
    return out.map(ps => ({ s: ps[0].s, e: ps[ps.length - 1].e, palabras: ps }));
  }
  let cacheR = null;
  // Escribe en el elemento el renglón activo, con la palabra que suena en <b>.
  function subtitulo(el, t, opts = {}) {
    if (!cacheR) cacheR = renglones(window.VAR.palabras, opts.maxCar, opts.maxPal);
    const r = cacheR.find((x, i) => t >= x.s - 0.05 && t < (cacheR[i + 1] ? Math.min(cacheR[i + 1].s, x.e + 0.6) : x.e + 0.6));
    const html = r ? r.palabras.map(p => (t >= p.s - 0.03 && t < p.e + 0.05 ? `<b>${p.w}</b>` : p.w)).join(" ") : "";
    if (el.dataset.html !== html) { el.innerHTML = html; el.dataset.html = html; }
    return r;
  }

  // ---- ritmo: BPM de los estilos de scripts/musica.py y un pulso que vale 1 en
  // cada golpe y cae rápido (para que las cosas "respiren" con la música)
  const BPM = { house: 122, lofi: 84, marimba: 104, synthwave: 110, cine: 72, noticiero: 124, minimal: 96 };
  const bpm = estilo => (typeof estilo === "number" ? estilo : BPM[estilo] || 0);
  const golpe = (t, b, caida = 6) => (b ? Math.exp(-((t * b / 60) % 1) * caida) : 0);

  window.M = { clamp, lerp, ease, k, win, $, $$, css, vis, hash, noise1, clip, splitChars, renglones, subtitulo, bpm, golpe };

  window.seek = async t => {
    window.render(t);
    if (pending.size) await Promise.all([...pending]);
  };

  // Precarga: todas las fuentes declaradas e imágenes estáticas antes del primer cuadro
  window.addEventListener("load", async () => {
    await Promise.all([...document.fonts].map(f => f.load().catch(() => {})));
    await document.fonts.ready;
    await Promise.all([...document.images].filter(i => i.src).map(i => i.decode().catch(() => {})));
    if (window.setup) await window.setup();
    window.render(0);
    if (pending.size) await Promise.all([...pending]);
    window.READY = true;
  });

  // Vista previa en un navegador común: ?play reproduce en tiempo real (sin sonido)
  if (new URLSearchParams(location.search).has("play")) {
    addEventListener("load", () => {
      const t0 = performance.now();
      const loop = () => { window.seek(((performance.now() - t0) / 1000) % window.DUR); requestAnimationFrame(loop); };
      setTimeout(loop, 300);
    });
  }
})();
