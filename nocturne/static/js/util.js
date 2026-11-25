// Small helpers shared by every module of the Codex front end.

export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

/** Create an element: h('div', {class: 'x', onclick: fn}, child, 'text'). */
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === 'class') el.className = value;
    else if (key === 'html') el.innerHTML = value;
    else if (key === 'text') el.textContent = value;
    else if (key === 'style' && typeof value === 'object') Object.assign(el.style, value);
    else if (key === 'dataset') Object.assign(el.dataset, value);
    else if (key.startsWith('on') && typeof value === 'function') el.addEventListener(key.slice(2), value);
    else el.setAttribute(key, value === true ? '' : value);
  }
  for (const child of children.flat()) {
    if (child === undefined || child === null || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return el;
}

export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export function escapeHtml(text) {
  return String(text ?? '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[ch]));
}

/** FNV-1a 32-bit hash of a string. */
export function hashString(text) {
  let hash = 0x811c9dc5;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}

/** A tiny seeded PRNG (mulberry32) for repeatable visual jitter. */
export function seeded(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function ordinal(n) {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
  'September', 'October', 'November', 'December'];
const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

export function parseDay(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
}

export function isoDay(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function shiftDay(iso, days) {
  const date = parseDay(iso);
  date.setDate(date.getDate() + days);
  return isoDay(date);
}

/** "Wednesday, the 25th of November" */
export function formatDay(iso, withYear = false) {
  const date = parseDay(iso);
  const text = `${WEEKDAYS[date.getDay()]}, the ${ordinal(date.getDate())} of ${MONTHS[date.getMonth()]}`;
  return withYear ? `${text}, ${date.getFullYear()}` : text;
}

export function shortDay(iso) {
  const date = parseDay(iso);
  return `${ordinal(date.getDate())} ${MONTHS[date.getMonth()].slice(0, 3)} ${date.getFullYear()}`;
}

export function localTime() {
  const now = new Date();
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
}

export function hourName(stamp) {
  if (!stamp) return '';
  const [hh, mm] = stamp.split(':').map(Number);
  const names = ['midnight', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
    'ten', 'eleven', 'noon'];
  const hour12 = hh % 12;
  const base = hh === 0 ? 'midnight' : hh === 12 ? 'noon' : names[hour12];
  const half = hh < 12 ? 'of the morning' : hh < 18 ? 'of the afternoon' : 'of the night';
  if (hh === 0 || hh === 12) return mm ? `${mm} past ${base}` : base;
  return mm ? `${mm} past ${base} ${half}` : `${base} ${half}`;
}

export function digitalRoot(n, keepMaster = false) {
  let value = Math.abs(n);
  while (value > 9) {
    if (keepMaster && [11, 22, 33].includes(value)) return value;
    value = String(value).split('').reduce((a, d) => a + Number(d), 0);
  }
  return value;
}

export function prefersReducedMotion() {
  return document.body.classList.contains('reduced-motion')
    || window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

let toastTimer = null;
export function toast(message, kind = 'info', ms = 4200) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = message;
  el.dataset.kind = kind;
  el.classList.add('is-shown');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('is-shown'), ms);
}

export function debounce(fn, ms) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

export const clamp = (value, lo, hi) => Math.max(lo, Math.min(hi, value));
export const rand = (lo, hi) => lo + Math.random() * (hi - lo);
export const pick = (items) => items[Math.floor(Math.random() * items.length)];
