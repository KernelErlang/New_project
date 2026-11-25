// The Rites — every animation of the Codex: an ambient sky, a particle engine and
// thirty theatrical rites drawn on canvas, SVG and CSS. Each rite has its own sound.

import { clamp, digitalRoot, hashString, pick, prefersReducedMotion, rand, seeded, sleep } from './util.js';

const TAU = Math.PI * 2;
const GLYPHS = ['🜁', '☿', '☥', '♀', '♂', '✠', '❦', '☄', '🜍', '✶', '♃', '⚖', '🜄', '☠', '⚗', '⛧',
  '☈', '✦', '☽', '☉', '🜂', '♄', '🜃', '⛤'];
const RAVEN_PATH = 'M-46 12L-22 2C-14 -18 6 -28 22 -24L34 -28L48 -22L35 -15C35 -2 27 9 13 15L21 36H13L5 18L-3 19L-1 36H-9L-12 19C-25 19 -35 17 -46 12Z';
const CROWN_PATH = 'M-42 18L-42 -22L-21 0L0 -36L21 0L42 -22L42 18ZM-42 20H42V34H-42Z';

const DEFAULT_PALETTE = {
  accent: '#b3261e', accent2: '#d9a58a', glow: '#ff6a2b', ink: '#3b0d0a', sky: '#120606',
  parchment: '#e8d9bd',
};

class Layer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.resize();
  }

  resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.w = window.innerWidth;
    this.h = window.innerHeight;
    this.canvas.width = Math.floor(this.w * dpr);
    this.canvas.height = Math.floor(this.h * dpr);
    this.canvas.style.width = `${this.w}px`;
    this.canvas.style.height = `${this.h}px`;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
}

function hexToRgb(hex) {
  const v = (hex || '#ffffff').replace('#', '');
  return [parseInt(v.slice(0, 2), 16), parseInt(v.slice(2, 4), 16), parseInt(v.slice(4, 6), 16)];
}
const rgba = (hex, a) => {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r},${g},${b},${a})`;
};

function polygon(n, r, rot = -90) {
  return Array.from({ length: n }, (_, i) => {
    const a = ((rot + (i * 360) / n) * Math.PI) / 180;
    return `${(r * Math.cos(a)).toFixed(1)},${(r * Math.sin(a)).toFixed(1)}`;
  }).join(' ');
}

function starPoly(n, outer, inner, rot = -90) {
  return Array.from({ length: n * 2 }, (_, i) => {
    const r = i % 2 ? inner : outer;
    const a = ((rot + (i * 180) / n) * Math.PI) / 180;
    return `${(r * Math.cos(a)).toFixed(1)},${(r * Math.sin(a)).toFixed(1)}`;
  }).join(' ');
}

// --- particles -----------------------------------------------------------------

function drawParticle(ctx, p, palette) {
  const life = 1 - p.age / p.life;
  const alpha = clamp(Math.min(life * 1.6, p.age * 3, 1) * (p.alpha ?? 1), 0, 1);
  if (alpha <= 0) return;
  ctx.save();
  ctx.translate(p.x, p.y);
  if (p.rot) ctx.rotate(p.rot);
  const colour = p.color || palette.glow;
  switch (p.kind) {
    case 'ember':
    case 'mote':
    case 'spore': {
      ctx.globalCompositeOperation = 'lighter';
      const flicker = p.kind === 'ember' ? 0.6 + 0.4 * Math.sin(p.age * 18 + p.phase) : 1;
      const r = p.size * (p.kind === 'spore' ? 2 : 3.2);
      const g = ctx.createRadialGradient(0, 0, 0, 0, 0, r);
      g.addColorStop(0, rgba(colour, alpha * flicker));
      g.addColorStop(1, rgba(colour, 0));
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(0, 0, r, 0, TAU);
      ctx.fill();
      break;
    }
    case 'ash':
      ctx.fillStyle = rgba(p.color || '#9c948c', alpha * 0.8);
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.7);
      break;
    case 'petal':
      ctx.fillStyle = rgba(p.color || '#c2185b', alpha);
      ctx.beginPath();
      ctx.ellipse(0, 0, p.size, p.size * 0.55 * Math.abs(Math.sin(p.age * 2 + p.phase)) + 1, 0, 0, TAU);
      ctx.fill();
      break;
    case 'star': {
      ctx.globalCompositeOperation = 'lighter';
      const tw = 0.5 + 0.5 * Math.sin(p.age * 3 + p.phase);
      ctx.strokeStyle = rgba(colour, alpha * (0.4 + 0.6 * tw));
      ctx.lineWidth = 1;
      const s = p.size * (1.5 + tw);
      ctx.beginPath();
      ctx.moveTo(-s, 0); ctx.lineTo(s, 0); ctx.moveTo(0, -s); ctx.lineTo(0, s);
      ctx.stroke();
      ctx.fillStyle = rgba('#ffffff', alpha * tw);
      ctx.beginPath(); ctx.arc(0, 0, p.size * 0.5, 0, TAU); ctx.fill();
      break;
    }
    case 'feather':
      ctx.strokeStyle = rgba(p.color || '#d8d2c4', alpha * 0.8);
      ctx.fillStyle = rgba(p.color || '#d8d2c4', alpha * 0.35);
      ctx.beginPath();
      ctx.ellipse(0, 0, p.size * 2.2, p.size * 0.6, 0, 0, TAU);
      ctx.fill();
      ctx.beginPath(); ctx.moveTo(-p.size * 2.6, 0); ctx.lineTo(p.size * 2.2, 0); ctx.stroke();
      break;
    case 'droplet':
      ctx.strokeStyle = rgba(colour, alpha * 0.7);
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(0, 0, p.size, 0, TAU); ctx.stroke();
      break;
    case 'moth': {
      const flap = 0.35 + 0.65 * Math.abs(Math.sin(p.age * 22 + p.phase));
      ctx.fillStyle = rgba(p.color || '#e3dccb', alpha * 0.9);
      ctx.beginPath();
      ctx.ellipse(-p.size * 0.6 * flap, 0, p.size * flap, p.size * 0.65, -0.4, 0, TAU);
      ctx.ellipse(p.size * 0.6 * flap, 0, p.size * flap, p.size * 0.65, 0.4, 0, TAU);
      ctx.fill();
      ctx.fillStyle = rgba('#2a2420', alpha);
      ctx.fillRect(-0.8, -p.size * 0.6, 1.6, p.size * 1.2);
      break;
    }
    case 'spark':
      ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba(colour, alpha);
      ctx.lineWidth = p.size;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-p.vx * 0.04, -p.vy * 0.04); ctx.stroke();
      break;
    case 'ring':
      ctx.strokeStyle = rgba(colour, alpha * 0.8);
      ctx.lineWidth = p.width || 2;
      ctx.beginPath(); ctx.arc(0, 0, p.size + p.age * (p.speed || 300), 0, TAU); ctx.stroke();
      break;
    case 'shooting': {
      ctx.globalCompositeOperation = 'lighter';
      const len = p.size * 18;
      const ang = Math.atan2(p.vy, p.vx);
      const g = ctx.createLinearGradient(0, 0, -Math.cos(ang) * len, -Math.sin(ang) * len);
      g.addColorStop(0, rgba('#ffffff', alpha));
      g.addColorStop(1, rgba(colour, 0));
      ctx.strokeStyle = g;
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-Math.cos(ang) * len, -Math.sin(ang) * len); ctx.stroke();
      break;
    }
    case 'smoke': {
      const r = p.size + p.age * 40;
      const g = ctx.createRadialGradient(0, 0, 0, 0, 0, r);
      g.addColorStop(0, rgba(p.color || '#6b6460', alpha * 0.35));
      g.addColorStop(1, rgba(p.color || '#6b6460', 0));
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.fill();
      break;
    }
    case 'streak':
      ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba(colour, alpha * 0.7);
      ctx.lineWidth = p.size;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-p.vx * 0.12, -p.vy * 0.12); ctx.stroke();
      break;
    default:
      break;
  }
  ctx.restore();
}

function stepParticle(p, dt) {
  p.age += dt;
  p.vx += (p.ax || 0) * dt;
  p.vy += (p.ay || 0) * dt;
  if (p.drag) {
    p.vx *= 1 - p.drag * dt;
    p.vy *= 1 - p.drag * dt;
  }
  const sway = p.sway ? Math.sin(p.age * (p.swayRate || 1.6) + p.phase) * p.sway : 0;
  p.x += (p.vx + sway) * dt;
  p.y += p.vy * dt;
  if (p.vr) p.rot = (p.rot || 0) + p.vr * dt;
  if (p.kind === 'moth') {
    p.vx += rand(-260, 260) * dt;
    p.vy += rand(-200, 140) * dt;
  }
  return p.age < p.life;
}

const AMBIENT = {
  embers: (w, h) => ({ kind: 'ember', x: rand(0, w), y: h + 10, vx: rand(-6, 6), vy: rand(-38, -14), size: rand(0.8, 2.2), life: rand(7, 14), sway: 10 }),
  ash: (w) => ({ kind: 'ash', x: rand(0, w), y: -10, vx: rand(-5, 5), vy: rand(10, 26), size: rand(1.5, 3.5), life: rand(14, 26), sway: 14, vr: rand(-1, 1), rot: rand(0, 3) }),
  petals: (w) => ({ kind: 'petal', x: rand(0, w), y: -10, vx: rand(-8, 8), vy: rand(14, 30), size: rand(3, 6), life: rand(14, 24), sway: 22, vr: rand(-1.5, 1.5), rot: rand(0, 3), color: pick(['#c2185b', '#e57399', '#8e1b3a']) }),
  motes: (w, h) => ({ kind: 'mote', x: rand(0, w), y: rand(0, h), vx: rand(-5, 5), vy: rand(-8, 3), size: rand(0.6, 1.6), life: rand(8, 16), sway: 6 }),
  stars: (w, h) => ({ kind: 'star', x: rand(0, w), y: rand(0, h * 0.8), vx: 0, vy: 0, size: rand(0.8, 2), life: rand(10, 20) }),
  feathers: (w) => ({ kind: 'feather', x: rand(0, w), y: -10, vx: rand(-6, 6), vy: rand(10, 22), size: rand(3, 5), life: rand(18, 28), sway: 26, vr: rand(-0.8, 0.8), rot: rand(0, 3) }),
  droplets: (w, h) => ({ kind: 'droplet', x: rand(0, w), y: h + 10, vx: rand(-4, 4), vy: rand(-26, -10), size: rand(1.5, 4), life: rand(10, 20), sway: 8 }),
  spores: (w, h) => ({ kind: 'spore', x: rand(0, w), y: rand(h * 0.3, h), vx: rand(-4, 4), vy: rand(-12, -4), size: rand(0.8, 1.6), life: rand(10, 18), sway: 9, color: '#c8e07a' }),
};

// --- overlays ----------------------------------------------------------------

const SVGNS = 'http://www.w3.org/2000/svg';

function mandalaSvg(c) {
  const petals = Array.from({ length: 12 }, (_, i) => `<path pathLength="100" class="draw d3" d="M0 -60C24 -100 24 -140 0 -170C-24 -140 -24 -100 0 -60Z" transform="rotate(${i * 30})"/>`).join('');
  return `<svg viewBox="-200 -200 400 400" class="mandala"><g fill="none" stroke="${c}" stroke-width="1.6">
    <circle pathLength="100" class="draw" r="186"/><circle pathLength="100" class="draw d1" r="176"/>
    <polygon pathLength="100" class="draw d2" points="${polygon(8, 172)}"/>
    <polygon pathLength="100" class="draw d2" points="${polygon(8, 172, -67.5)}"/>
    ${petals}
    <polygon pathLength="100" class="draw d4" points="${starPoly(6, 58, 34)}"/>
    <circle pathLength="100" class="draw d4" r="34"/></g>
    <circle r="22" fill="${c}" class="core"/></svg>`;
}

// --- the Rites ------------------------------------------------------------------

export class Rites {
  constructor({ sky, canvas, layer, banner, choir }) {
    this.skyLayer = new Layer(sky);
    this.fg = new Layer(canvas);
    this.layer = layer;
    this.banner = banner;
    this.choir = choir;
    this.palette = { ...DEFAULT_PALETTE };
    this.ambient = [];
    this.particles = [];
    this.effects = [];
    this.ambientKind = 'motes';
    this.ambientOn = true;
    this.starfield = false;
    this.noteStars = [];
    this.skyStars = [];
    this.bannerTimer = null;
    window.addEventListener('resize', () => {
      this.skyLayer.resize();
      this.fg.resize();
      this.buildSkyStars();
    });
    this.buildSkyStars();
    this.last = performance.now();
    requestAnimationFrame((t) => this.loop(t));
  }

  get w() { return this.fg.w; }
  get h() { return this.fg.h; }
  center() { return { x: this.w / 2, y: this.h / 2 }; }

  configure(rules) {
    this.palette = { ...DEFAULT_PALETTE, ...(rules?.aspect?.palette || {}) };
    this.ambientKind = rules?.aspect?.particle || 'motes';
    this.ambientOn = !rules?.effects?.no_particles;
    this.starfield = Boolean(rules?.effects?.starfield);
    this.ambient = [];
    this.buildSkyStars();
  }

  setNotes(notes) {
    this.noteStars = (notes || []).map((n) => {
      const r = seeded(hashString(`star-${n.id}`));
      return { x: 0.08 + r() * 0.84, y: 0.06 + r() * 0.42, size: 1.6 + r() * 1.4, phase: r() * 6 };
    });
  }

  buildSkyStars() {
    const r = seeded(hashString(`${this.palette.glow}-${this.w}`));
    this.skyStars = Array.from({ length: 70 }, () => ({ x: r(), y: r() * 0.55, s: r() * 1.2 + 0.3, p: r() * 6 }));
  }

  // -- frame loop ---------------------------------------------------------------
  loop(now) {
    const dt = Math.min(0.05, (now - this.last) / 1000);
    this.last = now;
    if (!document.hidden) {
      this.drawSky(dt, now / 1000);
      this.drawForeground(dt, now / 1000);
    }
    requestAnimationFrame((t) => this.loop(t));
  }

  drawSky(dt, time) {
    const { ctx, w, h } = this.skyLayer;
    ctx.clearRect(0, 0, w, h);
    const still = prefersReducedMotion();
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (const s of this.skyStars) {
      const tw = still ? 0.6 : 0.5 + 0.5 * Math.sin(time * 1.3 + s.p);
      ctx.fillStyle = rgba('#ffffff', 0.12 + 0.25 * tw);
      ctx.beginPath(); ctx.arc(s.x * w, s.y * h, s.s, 0, TAU); ctx.fill();
    }
    if (this.starfield && this.noteStars.length) {
      ctx.strokeStyle = rgba(this.palette.glow, 0.35);
      ctx.lineWidth = 1;
      ctx.beginPath();
      this.noteStars.forEach((s, i) => {
        const x = s.x * w;
        const y = s.y * h;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();
      for (const s of this.noteStars) {
        const tw = 0.6 + 0.4 * Math.sin(time * 2 + s.phase);
        const r = s.size * 4;
        const g = ctx.createRadialGradient(s.x * w, s.y * h, 0, s.x * w, s.y * h, r * 2.5);
        g.addColorStop(0, rgba('#ffffff', 0.95 * tw));
        g.addColorStop(0.25, rgba(this.palette.glow, 0.6 * tw));
        g.addColorStop(1, rgba(this.palette.glow, 0));
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(s.x * w, s.y * h, r * 2.5, 0, TAU); ctx.fill();
      }
    }
    ctx.restore();
    if (still || !this.ambientOn) return;
    const factory = AMBIENT[this.ambientKind] || AMBIENT.motes;
    const target = Math.round(Math.min(70, (w * h) / 26000));
    if (this.ambient.length < target && Math.random() < 0.3) this.ambient.push({ age: 0, phase: rand(0, 6), ...factory(w, h) });
    this.ambient = this.ambient.filter((p) => stepParticle(p, dt) && p.y > -40 && p.y < h + 40);
    for (const p of this.ambient) drawParticle(ctx, p, this.palette);
  }

  drawForeground(dt, time) {
    const { ctx, w, h } = this.fg;
    ctx.clearRect(0, 0, w, h);
    this.effects = this.effects.filter((fx) => fx(ctx, dt, time) !== false);
    this.particles = this.particles.filter((p) => stepParticle(p, dt));
    for (const p of this.particles) drawParticle(ctx, p, this.palette);
  }

  // -- building blocks ------------------------------------------------------------
  spawn(p) {
    if (this.particles.length > 1400) return;
    this.particles.push({ age: 0, phase: rand(0, 6), ...p });
  }

  burst(kind, count, origin, opts = {}) {
    const { speed = 160, life = 1.6, size = [1, 3], spread = TAU, angle = 0, gravity = 0,
      drag = 1.2, color, sway = 0, vr = 0 } = opts;
    for (let i = 0; i < count; i += 1) {
      const a = angle + (Math.random() - 0.5) * spread;
      const v = speed * (0.3 + Math.random() * 0.9);
      this.spawn({
        kind, x: origin.x + rand(-6, 6), y: origin.y + rand(-6, 6), vx: Math.cos(a) * v, vy: Math.sin(a) * v,
        ay: gravity, drag, size: rand(size[0], size[1]), life: life * rand(0.6, 1.2), color, sway,
        vr: vr ? rand(-vr, vr) : 0, rot: rand(0, TAU),
      });
    }
  }

  overlay(className, html, ms, style = {}) {
    const el = document.createElement('div');
    el.className = `rite-overlay ${className}`;
    el.innerHTML = html;
    Object.assign(el.style, style);
    el.style.setProperty('--glow', this.palette.glow);
    el.style.setProperty('--accent', this.palette.accent);
    el.style.setProperty('--dur', `${ms}ms`);
    this.layer.append(el);
    setTimeout(() => el.remove(), ms);
    return el;
  }

  flash(colour = '#ffffff', ms = 500, opacity = 0.8) {
    this.overlay('rite-flash', '', ms, { background: colour, '--flash': opacity });
  }

  shake(ms = 600, target = document.getElementById('sanctum')) {
    if (!target) return;
    target.classList.remove('quake');
    void target.offsetWidth; // restart the animation
    target.classList.add('quake');
    setTimeout(() => target.classList.remove('quake'), ms);
  }

  announce(perf, isNew) {
    const el = this.banner;
    if (!el) return;
    const tags = [perf.awakened ? '<span class="tag tag--awake">Awakened</span>' : '',
      isNew ? '<span class="tag tag--new">A rite discovered</span>' : ''].join('');
    el.innerHTML = `<div class="rite-banner__name">✦ ${perf.name} ✦</div>${tags ? `<div class="rite-banner__tags">${tags}</div>` : ''}`;
    el.classList.add('is-shown');
    clearTimeout(this.bannerTimer);
    this.bannerTimer = setTimeout(() => el.classList.remove('is-shown'), 3400);
  }

  async perform(perf, origin, context = {}) {
    const fn = ANIMATIONS[perf.animation] || ANIMATIONS.settle;
    const at = origin || this.center();
    const intensity = clamp(perf.intensity || 1, 0.6, 2.2);
    if (perf.id !== 'ink_settles') this.announce(perf, context.isNew);
    this.choir?.play(perf.sound);
    if (perf.awakened) this.choir?.play('sparkle');
    if (prefersReducedMotion()) {
      this.overlay('rite-gentle', '', 1800);
      await sleep(1500);
      return;
    }
    await fn.call(this, at, intensity, perf, context);
  }

  async performAll(list, origin, context = {}) {
    const fresh = new Set(context.newIds || []);
    for (const perf of list || []) {
      await this.perform(perf, origin, { ...context, isNew: fresh.has(perf.id) });
      await sleep(260);
    }
  }
}

// Every animation, keyed by the rite's `animation`. `this` is the Rites instance.
const ANIMATIONS = {
  async settle(o) {
    this.burst('mote', 22, o, { speed: 90, life: 1.5, size: [1, 2.2] });
    await sleep(700);
  },

  async resonance(o, k) {
    this.overlay('rite-mandala', mandalaSvg(this.palette.glow), 4600);
    const c = this.center();
    for (let i = 0; i < 3; i += 1) this.spawn({ kind: 'ring', x: c.x, y: c.y, vx: 0, vy: 0, size: 20, speed: 260 + i * 60, life: 2.4, width: 2, color: '#f6e7a8' });
    this.burst('mote', Math.round(70 * k), c, { speed: 260, life: 3, size: [1, 2.6], color: '#f6e7a8' });
    await sleep(4000);
  },

  async master(o, k, perf, ctx) {
    const n = digitalRoot(ctx.weight || 11, true);
    const rays = Array.from({ length: 24 }, (_, i) => `<line x1="0" y1="-120" x2="0" y2="-190" transform="rotate(${i * 15})"/>`).join('');
    this.overlay('rite-master', `<svg viewBox="-200 -200 400 400"><g class="spin" stroke="#f6e7a8" stroke-width="2">${rays}</g>
      <circle r="112" fill="none" stroke="#f6e7a8" stroke-width="3"/><circle r="100" fill="none" stroke="${this.palette.glow}" stroke-width="1.5"/>
      <text y="34" text-anchor="middle" class="numeral">${[11, 22, 33].includes(n) ? n : 11}</text></svg>`, 4400);
    this.burst('spark', Math.round(60 * k), this.center(), { speed: 420, life: 1.4, size: [1, 2], color: '#f6e7a8' });
    await sleep(4000);
  },

  async crown(o, k) {
    this.overlay('rite-crown', `<svg viewBox="-60 -60 120 120"><defs><linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff3c4"/><stop offset="1" stop-color="#c9a227"/></linearGradient></defs><path d="${CROWN_PATH}" fill="url(#cg)"/></svg>`, 4200);
    for (let i = 0; i < Math.round(90 * k); i += 1) {
      this.spawn({ kind: 'mote', x: rand(this.w * 0.3, this.w * 0.7), y: rand(-20, this.h * 0.3), vx: rand(-10, 10), vy: rand(30, 90), size: rand(1, 2.4), life: rand(2, 4), color: '#f6e7a8' });
    }
    await sleep(3800);
  },

  async eclipse() {
    this.overlay('rite-eclipse', `<svg viewBox="-200 -200 400 400"><defs>
      <radialGradient id="sun" r="50%"><stop offset="0" stop-color="#fff7d6"/><stop offset=".6" stop-color="#ffd36b"/><stop offset="1" stop-color="#ff8a2b"/></radialGradient>
      <radialGradient id="corona" r="50%"><stop offset=".55" stop-color="#fff2c4" stop-opacity=".9"/><stop offset="1" stop-color="#fff2c4" stop-opacity="0"/></radialGradient></defs>
      <circle r="170" fill="url(#corona)" class="corona"/><circle r="92" fill="url(#sun)"/>
      <circle r="94" fill="#050307" class="moon"/><circle cx="64" cy="-66" r="10" fill="#fff" class="ring"/></svg>`, 5600);
    await sleep(5200);
  },

  async bloodmoon(o, k) {
    this.overlay('rite-bloodmoon', `<div class="tint"></div><svg viewBox="-200 -200 400 400"><defs><radialGradient id="bm" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#ff6b5b"/><stop offset=".7" stop-color="#8b0a1a"/><stop offset="1" stop-color="#3a0208"/></radialGradient></defs>
      <circle r="150" fill="url(#bm)"/><circle cx="-40" cy="-30" r="22" fill="#000" opacity=".18"/><circle cx="50" cy="20" r="30" fill="#000" opacity=".15"/><circle cx="-10" cy="70" r="16" fill="#000" opacity=".2"/></svg>`, 5200);
    for (let i = 0; i < Math.round(40 * k); i += 1) {
      this.spawn({ kind: 'ember', x: rand(0, this.w), y: this.h + 10, vx: rand(-10, 10), vy: rand(-90, -40), size: rand(1, 2.5), life: rand(3, 5), color: '#ff2e4d' });
    }
    await sleep(4800);
  },

  async toll(o, k) {
    const c = this.center();
    for (let i = 0; i < 3; i += 1) {
      setTimeout(() => {
        this.spawn({ kind: 'ring', x: c.x, y: c.y, vx: 0, vy: 0, size: 10, speed: 520, life: 2.2, width: 3, color: this.palette.accent2 });
        this.spawn({ kind: 'ring', x: c.x, y: c.y, vx: 0, vy: 0, size: 10, speed: 380, life: 2.2, width: 1.5, color: this.palette.glow });
        this.shake(500);
      }, i * 1300);
    }
    this.overlay('rite-bell', `<svg viewBox="-60 -60 120 120"><path d="M-30 24C-30 -2 -24 -34 0 -34C24 -34 30 -2 30 24L40 34H-40Z" fill="${this.palette.accent2}"/><circle cy="41" r="7" fill="${this.palette.accent2}"/></svg>`, 4200);
    await sleep(4000 * Math.min(1, k));
  },

  async witching() {
    const numerals = ['XII', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']
      .map((n, i) => {
        const a = ((i * 30 - 90) * Math.PI) / 180;
        return `<text x="${(150 * Math.cos(a)).toFixed(1)}" y="${(150 * Math.sin(a) + 9).toFixed(1)}" text-anchor="middle">${n}</text>`;
      }).join('');
    const runes = GLYPHS.slice(0, 12).map((g, i) => `<span style="--i:${i}">${g}</span>`).join('');
    this.overlay('rite-witching', `<svg viewBox="-200 -200 400 400"><circle r="182" fill="rgba(5,3,10,.55)" stroke="#d9b65c" stroke-width="3"/>
      <circle r="120" fill="none" stroke="#d9b65c" stroke-width="1" opacity=".5"/><g class="numerals">${numerals}</g>
      <line class="hand hour" x1="0" y1="10" x2="0" y2="-80"/><line class="hand minute" x1="0" y1="14" x2="0" y2="-130"/><circle r="7" fill="#d9b65c"/></svg>
      <div class="runes">${runes}</div>`, 5200);
    await sleep(4800);
  },

  async raven(o, k) {
    const birds = Array.from({ length: k > 1.3 ? 5 : 3 }, (_, i) => `<svg class="bird" style="--i:${i}" viewBox="-60 -60 120 120"><path d="${RAVEN_PATH}" fill="#0b0809" stroke="${this.palette.accent2}" stroke-width="1.2"/></svg>`).join('');
    this.overlay('rite-raven', birds, 4800);
    for (let i = 0; i < 26; i += 1) {
      setTimeout(() => this.spawn({ kind: 'feather', x: rand(0, this.w), y: rand(this.h * 0.1, this.h * 0.5), vx: rand(-20, 20), vy: rand(20, 50), size: rand(3, 5), life: rand(3, 5), sway: 30, vr: rand(-2, 2), color: '#2a2430' }), i * 120);
    }
    await sleep(4400);
  },

  async moths(o, k) {
    const count = Math.round(26 * k);
    for (let i = 0; i < count; i += 1) {
      this.spawn({ kind: 'moth', x: o.x + rand(-30, 30), y: o.y + rand(-20, 20), vx: rand(-60, 60), vy: rand(-140, -60), size: rand(4, 7), life: rand(2.8, 4.6), drag: 0.6 });
    }
    await sleep(3600);
  },

  async lightning(o, k) {
    const start = { x: o.x + rand(-120, 120), y: -10 };
    const bolt = [];
    let x = start.x;
    const steps = 14;
    for (let i = 0; i <= steps; i += 1) {
      const y = start.y + ((o.y - start.y) * i) / steps;
      x += rand(-34, 34);
      bolt.push([i === steps ? o.x : x, y]);
    }
    const branches = [3, 6, 9].map((idx) => {
      const [bx, by] = bolt[idx];
      return Array.from({ length: 5 }, (_, j) => [bx + (j + 1) * rand(-30, 30), by + (j + 1) * rand(14, 30)]);
    });
    let age = 0;
    this.effects.push((ctx, dt) => {
      age += dt;
      if (age > 1.3) return false;
      const flicker = (age < 0.12 || (age > 0.25 && age < 0.38) || (age > 0.55 && age < 0.66)) ? 1 : 0.25;
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      for (const [width, alpha] of [[9, 0.15], [4, 0.45], [1.6, 1]]) {
        ctx.strokeStyle = rgba(width > 5 ? this.palette.glow : '#ffffff', alpha * flicker * (1 - age / 1.3));
        ctx.lineWidth = width;
        ctx.beginPath();
        bolt.forEach(([bx, by], i) => (i ? ctx.lineTo(bx, by) : ctx.moveTo(bx, by)));
        for (const branch of branches) {
          const root = bolt[branches.indexOf(branch) * 3 + 3];
          ctx.moveTo(root[0], root[1]);
          for (const [bx, by] of branch) ctx.lineTo(bx, by);
        }
        ctx.stroke();
      }
      ctx.restore();
      return true;
    });
    this.flash('#e8f0ff', 700, 0.75);
    this.shake(700);
    this.burst('spark', Math.round(50 * k), o, { speed: 360, life: 1, size: [1, 2], color: '#e8f0ff', gravity: 400 });
    await sleep(1600);
    this.flash('#e8f0ff', 400, 0.4);
    await sleep(800);
  },

  async scales() {
    this.overlay('rite-scales', `<svg viewBox="-80 -80 160 160"><g fill="none" stroke="#e9cf7a" stroke-width="3" stroke-linecap="round">
      <path d="M0 -50V60M-26 62H26"/><circle cy="-56" r="6" fill="#e9cf7a"/>
      <g class="beam"><path d="M-60 -40H60"/><path d="M-60 -40L-74 0M-60 -40L-46 0M60 -40L46 0M60 -40L74 0"/>
      <path d="M-80 0H-40A20 12 0 0 1 -80 0ZM40 0H80A20 12 0 0 1 40 0Z" fill="#e9cf7a"/></g></g></svg>`, 4600);
    await sleep(4200);
  },

  async twin(o, k) {
    let age = 0;
    const colours = [this.palette.glow, this.palette.accent2];
    const trail = [];
    this.effects.push((ctx, dt) => {
      age += dt;
      if (age > 3.2) return false;
      const rise = age * 120;
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 2; i += 1) {
        const a = age * 6 + i * Math.PI;
        const r = 50 * (1 - age / 3.2) + 6;
        const x = o.x + Math.cos(a) * r;
        const y = o.y - rise + Math.sin(a) * r * 0.35;
        trail.push({ x, y, c: colours[i], t: age });
        const g = ctx.createRadialGradient(x, y, 0, x, y, 18 * k);
        g.addColorStop(0, rgba('#ffffff', 0.95));
        g.addColorStop(0.4, rgba(colours[i], 0.7));
        g.addColorStop(1, rgba(colours[i], 0));
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(x, y, 18 * k, 0, TAU); ctx.fill();
      }
      for (const p of trail) {
        const fade = 1 - (age - p.t) / 0.8;
        if (fade <= 0) continue;
        ctx.fillStyle = rgba(p.c, 0.25 * fade);
        ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, TAU); ctx.fill();
      }
      ctx.restore();
      return true;
    });
    await sleep(3300);
    this.burst('mote', 40, { x: o.x, y: o.y - 380 }, { speed: 200, life: 1.6, color: '#ffffff' });
  },

  async conjunction(o, k) {
    const c = this.center();
    const left = { x: -40, y: c.y };
    const right = { x: this.w + 40, y: c.y };
    let age = 0;
    this.effects.push((ctx, dt) => {
      age += dt;
      const t = Math.min(1, age / 2);
      const ease = t * t * (3 - 2 * t);
      if (age > 2.1) return false;
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      for (const [from, colour] of [[left, '#ff5a2b'], [right, '#4fc3dc']]) {
        const x = from.x + (c.x - from.x) * ease;
        const y = c.y + Math.sin(ease * Math.PI) * (from === left ? -80 : 80);
        const g = ctx.createRadialGradient(x, y, 0, x, y, 40 * k);
        g.addColorStop(0, rgba('#ffffff', 0.9));
        g.addColorStop(0.35, rgba(colour, 0.7));
        g.addColorStop(1, rgba(colour, 0));
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(x, y, 40 * k, 0, TAU); ctx.fill();
      }
      ctx.restore();
      return true;
    });
    await sleep(2050);
    this.flash('#ffffff', 600, 0.6);
    for (let i = 0; i < 3; i += 1) this.spawn({ kind: 'ring', x: c.x, y: c.y, vx: 0, vy: 0, size: 10, speed: 300 + i * 120, life: 1.8, width: 2.5, color: '#ffffff' });
    this.burst('spark', Math.round(90 * k), c, { speed: 480, life: 1.6, size: [1, 2.2], color: '#ffe9c4' });
    await sleep(1800);
  },

  async embers(o, k) {
    const n = Math.round(180 * k);
    for (let i = 0; i < n; i += 1) {
      this.spawn({ kind: 'ember', x: rand(0, this.w), y: this.h + rand(0, 60), vx: rand(-30, 30), vy: rand(-320, -120), size: rand(1, 3.2), life: rand(2, 4), sway: 30, color: pick(['#ff6a2b', '#ffb347', '#ff2e1f']) });
    }
    this.burst('ember', Math.round(60 * k), o, { speed: 260, life: 2, angle: -Math.PI / 2, spread: 2.2, gravity: -60, color: '#ffb347' });
    this.overlay('rite-heat', '', 3600);
    await sleep(3400);
  },

  async tide(o, k) {
    let age = 0;
    const { w, h } = this;
    this.effects.push((ctx, dt) => {
      age += dt;
      if (age > 4.4) return false;
      const level = Math.sin(Math.min(1, age / 4.4) * Math.PI) * h * 0.42 * Math.min(1.2, k);
      ctx.save();
      for (let band = 0; band < 3; band += 1) {
        ctx.fillStyle = rgba(band === 0 ? '#0b3b4a' : band === 1 ? '#1f6f80' : '#5fd4e8', 0.28 - band * 0.06);
        ctx.beginPath();
        ctx.moveTo(0, h);
        for (let x = 0; x <= w; x += 16) {
          const y = h - level + band * 26 + Math.sin(x / (90 + band * 30) + age * (2 + band)) * (16 + band * 6);
          ctx.lineTo(x, y);
        }
        ctx.lineTo(w, h);
        ctx.fill();
      }
      ctx.restore();
      if (Math.random() < 0.6) this.spawn({ kind: 'droplet', x: rand(0, w), y: h - rand(0, level), vx: 0, vy: rand(-90, -30), size: rand(2, 5), life: 1.6, sway: 10, color: '#bff4ff' });
      return true;
    });
    await sleep(4400);
  },

  async gale(o, k) {
    for (let i = 0; i < Math.round(70 * k); i += 1) {
      setTimeout(() => this.spawn({ kind: 'streak', x: -60, y: rand(0, this.h), vx: rand(900, 1500), vy: rand(-40, 40), size: rand(0.6, 1.6), life: 1.6, color: '#e8e4ff' }), i * 35);
    }
    for (let i = 0; i < Math.round(40 * k); i += 1) {
      setTimeout(() => this.spawn({ kind: 'feather', x: -30, y: rand(0, this.h), vx: rand(380, 700), vy: rand(-60, 60), size: rand(3, 6), life: 2.4, sway: 40, vr: rand(-6, 6) }), i * 60);
    }
    await sleep(3400);
  },

  async thorns() {
    const vines = [
      'M0 1000C120 820 160 700 330 640C420 610 460 520 420 430',
      'M1000 1000C860 840 860 700 690 650C600 620 560 540 600 450',
      'M0 0C140 160 120 300 300 340C390 360 430 420 420 500',
      'M1000 0C860 150 900 300 700 330C610 345 580 420 590 500',
    ];
    const roses = [[420, 430], [600, 450], [420, 500], [590, 500]];
    const thorns = vines.map((d, i) => `<path class="vine" style="--i:${i}" pathLength="100" d="${d}"/>`).join('');
    const blooms = roses.map(([x, y], i) => `<g class="bloom" style="--i:${i}" transform="translate(${x} ${y})">${[0, 72, 144, 216, 288].map((a) => `<circle r="16" cx="${(14 * Math.cos((a * Math.PI) / 180)).toFixed(1)}" cy="${(14 * Math.sin((a * Math.PI) / 180)).toFixed(1)}"/>`).join('')}<circle r="9" class="heart"/></g>`).join('');
    this.overlay('rite-thorns', `<svg viewBox="0 0 1000 1000" preserveAspectRatio="none">${thorns}${blooms}</svg>`, 5000);
    await sleep(4600);
  },

  async starfall(o, k) {
    for (let i = 0; i < Math.round(22 * k); i += 1) {
      setTimeout(() => this.spawn({ kind: 'shooting', x: rand(this.w * 0.1, this.w * 1.1), y: rand(-40, this.h * 0.3), vx: rand(-700, -420), vy: rand(260, 420), size: rand(4, 8), life: 1.4, color: this.palette.glow }), i * 140);
    }
    for (let i = 0; i < 40; i += 1) this.spawn({ kind: 'star', x: rand(0, this.w), y: rand(0, this.h * 0.7), vx: 0, vy: 0, size: rand(1, 2.4), life: rand(2.5, 4.5) });
    await sleep(3800);
  },

  async petals(o, k) {
    for (let i = 0; i < Math.round(120 * k); i += 1) {
      this.spawn({ kind: 'petal', x: rand(-40, this.w), y: rand(-200, -10), vx: rand(10, 40), vy: rand(60, 140), size: rand(4, 8), life: rand(4, 7), sway: 40, vr: rand(-2, 2), color: pick(['#c2185b', '#e57399', '#8e1b3a', '#f2a7c3']) });
    }
    await sleep(4200);
  },

  async quicksilver(o, k) {
    for (let i = 0; i < 6; i += 1) {
      setTimeout(() => this.spawn({ kind: 'ring', x: o.x, y: o.y, vx: 0, vy: 0, size: 6, speed: 240, life: 1.8, width: 2.5, color: i % 2 ? '#e8eef5' : '#9aa7b6' }), i * 220);
    }
    this.burst('droplet', Math.round(50 * k), o, { speed: 300, life: 1.6, size: [2, 5], gravity: 600, color: '#dfe7f0' });
    this.overlay('rite-mirror', '', 3000);
    await sleep(2800);
  },

  async prayer() {
    const ring = (glyphs, r, cls) => `<div class="ring ${cls}">${glyphs.map((g, i) => `<span style="transform: rotate(${(360 / glyphs.length) * i}deg) translateY(-${r}px)">${g}</span>`).join('')}</div>`;
    this.overlay('rite-prayer', ring(GLYPHS.slice(0, 12), 170, 'r1') + ring(GLYPHS.slice(12), 110, 'r2') + '<div class="halo"></div>', 5200);
    this.choir?.play('chord');
    await sleep(4800);
  },

  async glint(o) {
    this.overlay('rite-glint', `<svg viewBox="-50 -50 100 100"><polygon points="${starPoly(4, 48, 6)}" fill="#ffffff"/></svg>`, 1800, { left: `${o.x}px`, top: `${o.y}px` });
    this.burst('spark', 24, o, { speed: 200, life: 0.9, color: '#ffffff' });
    await sleep(1500);
  },

  async streak(o, k) {
    for (let i = 0; i < Math.round(60 * k); i += 1) {
      setTimeout(() => this.spawn({ kind: 'streak', x: -40, y: o.y + rand(-160, 160), vx: rand(1400, 2200), vy: 0, size: rand(1, 2.4), life: 1.2, color: this.palette.glow }), i * 25);
    }
    setTimeout(() => this.spawn({ kind: 'shooting', x: -40, y: o.y, vx: 1500, vy: -40, size: 14, life: 1.6, color: '#ffffff' }), 300);
    await sleep(2400);
  },

  async lantern(o) {
    const el = this.overlay('rite-lantern', '', 4400);
    const start = performance.now();
    const tick = (now) => {
      const t = (now - start) / 4400;
      if (t >= 1 || !el.isConnected) return;
      const r = 40 + Math.sin(Math.min(1, t * 1.6) * Math.PI * 0.5) * Math.max(this.w, this.h) * 0.7;
      el.style.background = `radial-gradient(circle at ${o.x}px ${o.y}px, rgba(255,214,130,.25) 0, rgba(255,214,130,.08) ${r * 0.6}px, rgba(0,0,0,${0.88 * (1 - t)}) ${r}px)`;
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    this.burst('mote', 40, o, { speed: 80, life: 3, color: '#ffd28a' });
    await sleep(4000);
  },

  async rays() {
    const beams = Array.from({ length: 9 }, (_, i) => `<i style="--i:${i}; --a:${-40 + i * 10}deg"></i>`).join('');
    this.overlay('rite-rays', beams, 5000);
    for (let i = 0; i < 50; i += 1) this.spawn({ kind: 'mote', x: rand(this.w * 0.2, this.w * 0.8), y: rand(0, this.h), vx: rand(-4, 4), vy: rand(-10, 10), size: rand(0.8, 1.8), life: rand(3, 5), color: '#fff3c4' });
    await sleep(4600);
  },

  async ouroboros(o, k) {
    const elements = [['🜂', 0, -150], ['🜄', 150, 0], ['🜁', 0, 150], ['🜃', -150, 0]]
      .map(([g, x, y], i) => `<text x="${x}" y="${y + 12}" text-anchor="middle" style="--i:${i}">${g}</text>`).join('');
    this.overlay('rite-ouroboros', `<svg viewBox="-200 -200 400 400"><g class="turn">
      <circle class="body" r="110" pathLength="100"/><circle class="scales" r="110" pathLength="100"/>
      <g class="head"><ellipse cx="0" cy="-110" rx="20" ry="14"/><circle cx="8" cy="-114" r="3" fill="#0b0809"/></g></g>
      <g class="elements">${elements}</g></svg>`, 6000);
    await sleep(3600);
    this.burst('mote', Math.round(80 * k), this.center(), { speed: 300, life: 2.4, color: '#b5f2b8' });
    await sleep(2000);
  },

  async chains(o) {
    const link = (i) => `<ellipse cx="${-480 + i * 48}" cy="0" rx="28" ry="15" transform="rotate(${i % 2 ? 0 : 0} ${-480 + i * 48} 0)" class="${i % 2 ? 'side' : ''}"/>`;
    const chain = Array.from({ length: 21 }, (_, i) => link(i)).join('');
    this.overlay('rite-chains', `<div class="tint"></div><svg viewBox="-500 -300 1000 600"><g class="chain a" transform="rotate(28)">${chain}</g><g class="chain b" transform="rotate(-28)">${chain}</g>
      <g class="lock"><path d="M-30 -10V-36A30 30 0 0 1 30 -36V-10" fill="none" stroke="#b9b2a6" stroke-width="10"/><rect x="-44" y="-12" width="88" height="70" rx="8" fill="#6d665e" stroke="#2b2622" stroke-width="3"/><circle cy="18" r="8" fill="#1b1714"/><path d="M0 22V40" stroke="#1b1714" stroke-width="6"/></g></svg>`, 3600);
    setTimeout(() => this.shake(500), 350);
    await sleep(3200);
  },

  async ward(o) {
    this.overlay('rite-ward', `<svg viewBox="-60 -60 120 120"><polygon points="${polygon(6, 54, -90)}" fill="rgba(160,210,255,.12)" stroke="#bfe3ff" stroke-width="2.5"/><polygon points="${polygon(6, 40, -90)}" fill="none" stroke="#bfe3ff" stroke-width="1" opacity=".6"/></svg>`, 2400, { left: `${o.x}px`, top: `${o.y}px` });
    this.burst('spark', 30, o, { speed: 160, life: 1, color: '#bfe3ff' });
    await sleep(2000);
  },

  async ash(o, k) {
    this.burst('ash', Math.round(50 * k), o, { speed: 90, life: 2.6, size: [1.5, 4], gravity: 60, sway: 18, vr: 3 });
    this.burst('smoke', 8, o, { speed: 30, life: 2.4, size: [10, 22] });
    await sleep(1800);
  },
};

export const ANIMATION_NAMES = Object.keys(ANIMATIONS);
export { SVGNS };
