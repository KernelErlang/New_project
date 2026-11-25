// The Sanctum board: the night's notes pinned like parchment on dark stone.

import { api } from './api.js';
import { renderInk } from './ink.js';
import { clamp, h, hashString, hourName, rand, seeded, shortDay, toast } from './util.js';

export class Board {
  constructor({ el, notesEl, emptyEl, onOpen }) {
    this.el = el;
    this.notesEl = notesEl;
    this.emptyEl = emptyEl;
    this.onOpen = onOpen;
    this.notes = [];
    this.state = null;
  }

  get rules() { return this.state?.rules || null; }
  get states() { return this.rules?.sigil_states || {}; }
  get movable() {
    return Boolean(this.state?.is_today && this.rules && !this.rules.effects.anchored);
  }

  render(state) {
    this.state = state;
    this.notes = [...state.notes];
    this.notesEl.replaceChildren();
    const ordered = this.rules?.effects?.mirror ? [...this.notes].reverse() : this.notes;
    ordered.forEach((note, i) => this.notesEl.append(this.noteEl(note, i)));
    if (state.echo) this.notesEl.append(this.echoEl(state.echo));
    this.renderEmpty();
  }

  renderEmpty() {
    const { state } = this;
    let text = '';
    if (!this.notes.length) {
      if (state.ritual.status === 'unobserved') text = 'This night passed unobserved. No cards were drawn, no ink was spilled.';
      else if (!state.is_today) text = 'No ink was spilled this night.';
      else if (!state.rules) text = 'The board waits for the night’s draw.';
      else text = 'The board is bare. Take up the quill, and let the night decide what your words awaken.';
    }
    this.emptyEl.textContent = text;
    this.emptyEl.hidden = !text;
  }

  noteEl(note, index = 0) {
    const r = seeded(hashString(`tilt-${note.id}`));
    const tilt = (r() * 6 - 3).toFixed(2);
    const house = this.state?.house?.id;
    const rites = (note.rite_names || []).map((name) => h('span', { class: 'note__rite', title: name }, '✦'));
    const el = h('article', {
      class: `note${note.bound ? ' is-bound' : ''}`,
      tabindex: '0',
      role: 'button',
      'aria-label': `Note: ${note.title || 'Untitled'}`,
      dataset: { id: note.id },
      style: { '--x': note.x, '--y': note.y, '--tilt': `${tilt}deg`, '--z': index + 1, '--drift': `${(r() * 8 + 12).toFixed(1)}s` },
    },
    h('header', { class: 'note__head' },
      h('h3', { class: 'note__title' }, note.title || 'Untitled'),
      h('time', { class: 'note__time', title: hourName(note.local_time) }, note.local_time)),
    h('div', { class: 'note__body', html: renderInk(note.body, this.states, { limit: 220 }) }),
    h('footer', { class: 'note__foot' },
      h('span', { class: 'note__rites' }, rites),
      note.bound ? h('span', { class: 'note__chain', title: 'Bound in chains' }, '⛓') : null,
      house ? h('span', { class: 'note__seal' }, h('img', { src: `/art/crest/${house}.svg`, alt: '' })) : null));
    this.enableDrag(el, note);
    el.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        this.onOpen(note);
      }
    });
    return el;
  }

  echoEl(note) {
    return h('article', { class: 'note note--echo', style: { '--x': 0.84, '--y': 0.84, '--tilt': '-4deg' }, tabindex: '0',
      onclick: () => this.onOpen(note, { echo: true }) },
    h('p', { class: 'note__echo-label' }, `An echo from ${shortDay(note.day)}`),
    h('h3', { class: 'note__title' }, note.title || 'Untitled'),
    h('div', { class: 'note__body', html: renderInk(note.body, {}, { limit: 120 }) }));
  }

  enableDrag(el, note) {
    let start = null;
    el.addEventListener('pointerdown', (event) => {
      if (event.button !== 0) return;
      start = { x: event.clientX, y: event.clientY, moved: false };
      if (this.movable) el.setPointerCapture(event.pointerId);
    });
    el.addEventListener('pointermove', (event) => {
      if (!start || !this.movable) return;
      const dx = event.clientX - start.x;
      const dy = event.clientY - start.y;
      if (!start.moved && Math.hypot(dx, dy) < 5) return;
      start.moved = true;
      el.classList.add('is-dragging');
      const box = this.el.getBoundingClientRect();
      const x = clamp((event.clientX - box.left) / box.width, 0.04, 0.96);
      const y = clamp((event.clientY - box.top) / box.height, 0.05, 0.95);
      el.style.setProperty('--x', x);
      el.style.setProperty('--y', y);
    });
    el.addEventListener('pointerup', async (event) => {
      if (!start) return;
      const moved = start.moved;
      start = null;
      el.classList.remove('is-dragging');
      if (!moved) {
        this.onOpen(note);
        return;
      }
      const box = this.el.getBoundingClientRect();
      let x = clamp((event.clientX - box.left) / box.width, 0.04, 0.96);
      let y = clamp((event.clientY - box.top) / box.height, 0.05, 0.95);
      if (this.rules?.effects?.grid) {
        x = 0.14 + Math.round(clamp((x - 0.14) / 0.24, 0, 3)) * 0.24;
        y = 0.18 + Math.round(clamp((y - 0.18) / 0.3, 0, 2)) * 0.3;
        el.style.setProperty('--x', x);
        el.style.setProperty('--y', y);
      }
      try {
        const { note: saved } = await api.moveNote(note.id, x, y);
        Object.assign(note, saved);
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  }

  element(id) {
    return this.notesEl.querySelector(`.note[data-id="${id}"]`);
  }

  origin(id) {
    const el = this.element(id);
    if (!el) return null;
    const box = el.getBoundingClientRect();
    return { x: box.left + box.width / 2, y: box.top + box.height / 2 };
  }

  add(note) {
    this.notes.push(note);
    this.state.notes = this.notes;
    const el = this.noteEl(note, this.notes.length);
    el.classList.add('is-new');
    this.notesEl.append(el);
    this.renderEmpty();
    return el;
  }

  replace(note) {
    const at = this.notes.findIndex((n) => n.id === note.id);
    if (at >= 0) this.notes[at] = note;
    const old = this.element(note.id);
    const el = this.noteEl(note, at + 1);
    if (old) old.replaceWith(el); else this.notesEl.append(el);
  }

  remove(id) {
    this.notes = this.notes.filter((n) => n.id !== id);
    this.state.notes = this.notes;
    const el = this.element(id);
    if (el) {
      el.classList.add('is-leaving');
      setTimeout(() => el.remove(), 700);
    }
    this.renderEmpty();
  }

  quake() {
    this.el.classList.remove('quake');
    void this.el.offsetWidth;
    this.el.classList.add('quake');
  }

  async scatter(exceptId) {
    for (const note of this.notes) {
      if (note.id === exceptId) continue;
      const x = clamp(note.x + rand(-0.18, 0.18), 0.08, 0.92);
      const y = clamp(note.y + rand(-0.18, 0.18), 0.1, 0.9);
      const el = this.element(note.id);
      if (el) {
        el.style.setProperty('--x', x);
        el.style.setProperty('--y', y);
      }
      try {
        const { note: saved } = await api.moveNote(note.id, x, y);
        Object.assign(note, saved);
      } catch {
        /* anchored nights refuse; the quake alone will do */
      }
    }
  }
}
