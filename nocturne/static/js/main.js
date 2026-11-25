// Nocturne Codex — the conductor that wires every part of the page together.

import { api } from './api.js';
import { Choir } from './audio.js';
import { Board } from './board.js';
import { cardEl, cardReading, POSITION_GLYPH } from './cards.js';
import { Rites } from './fx.js';
import { renderInk, setSigils, speakable } from './ink.js';
import { Quill } from './quill.js';
import { Ritual } from './ritual.js';
import { applyTheme } from './theme.js';
import { cardDialogContent, Tome } from './tome.js';
import { $, formatDay, h, hourName, isoDay, shiftDay, shortDay, sleep, toast } from './util.js';

const POSITIONS = ['crown', 'heart', 'shadow'];

const app = {
  state: null,
  catalogue: null,
  choir: new Choir(),
  entered: false,

  async boot() {
    try {
      const [state, catalogue] = await Promise.all([api.state(), api.codex()]);
      this.catalogue = catalogue;
      setSigils(catalogue.sigils);
      this.rites = new Rites({
        sky: $('#sky'), canvas: $('#rite-canvas'), layer: $('#rite-layer'), banner: $('#rite-banner'), choir: this.choir,
      });
      this.board = new Board({ el: $('#board'), notesEl: $('#board-notes'), emptyEl: $('#board-empty'), onOpen: (note, opts) => this.openNote(note, opts) });
      this.quill = new Quill({ root: $('#quill'), choir: this.choir, onInscribed: (result, opts) => this.onInscribed(result, opts) });
      this.ritual = new Ritual({ root: $('#ritual'), choir: this.choir, rites: this.rites, onSealed: (s) => this.onSealed(s) });
      this.tome = new Tome({ root: $('#tome'), app: this });
      this.bindChrome();
      this.setState(state);
      this.showThreshold();
      document.body.classList.remove('is-loading');
    } catch (err) {
      document.body.classList.remove('is-loading');
      $('#threshold-line').textContent = `The Codex could not be opened: ${err.message}`;
    }
  },

  // -- state ----------------------------------------------------------------
  setState(state) {
    this.state = state;
    const rules = state.rules;
    applyTheme(rules, { isToday: state.is_today, settings: state.settings });
    this.choir.configure(state.settings);
    this.choir.setNight(rules);
    this.rites.configure(rules);
    this.rites.setNotes(state.notes);
    this.renderHeader();
    this.renderAltar();
    this.board.render(state);
    this.quill.configure(state);
    $('#open-ritual')?.addEventListener('click', () => this.ritual.open(this.state));
  },

  async loadDay(day) {
    try {
      const state = await api.state(day);
      this.choir.play('page');
      this.setState(state);
    } catch (err) {
      toast(err.message, 'error');
    }
  },

  async refresh() {
    this.setState(await api.state(this.state.day));
  },

  // -- chrome -----------------------------------------------------------------
  bindChrome() {
    $('#prev-day').addEventListener('click', () => this.loadDay(shiftDay(this.state.day, -1)));
    $('#next-day').addEventListener('click', () => this.loadDay(shiftDay(this.state.day, 1)));
    $('#day-label').addEventListener('click', () => this.tome.toggle('archive'));
    $('#tome-toggle').addEventListener('click', () => this.tome.toggle());
    $('#sound-toggle').addEventListener('click', () => this.toggleSound());
    $('#today-btn').addEventListener('click', () => this.loadDay(this.state.today));
    $('#enter').addEventListener('click', () => this.enter());
    document.addEventListener('keydown', (event) => this.onKey(event));
    document.addEventListener('pointermove', (event) => {
      if (!document.body.classList.contains('fx-lantern')) return;
      document.documentElement.style.setProperty('--lx', `${event.clientX}px`);
      document.documentElement.style.setProperty('--ly', `${event.clientY}px`);
    });
    setInterval(() => this.watchMidnight(), 30000);
    document.addEventListener('nocturne:stale', () => this.watchMidnight(true));
    for (const id of ['note-dialog', 'card-dialog']) {
      const dialog = document.getElementById(id);
      dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
    }
  },

  /** When midnight passes with the Codex open, seal the old night and offer the new draw. */
  async watchMidnight(force = false) {
    if (!this.entered || !this.state || document.body.classList.contains('in-ritual')) return;
    if (!force && isoDay(new Date()) === this.state.today) return;
    try {
      const state = await api.state();
      if (state.today === this.state.today && !force) return;
      toast('Midnight has passed. The old night is sealed; a new hand waits.', 'info', 7000);
      this.setState(state);
      if (state.ritual.status !== 'sealed') this.ritual.open(state);
    } catch {
      /* the Codex may have been closed; nothing to do */
    }
  },

  onKey(event) {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '');
    if (event.key === 'Escape') {
      if (this.tome.isOpen) this.tome.close();
      return;
    }
    if (typing || event.ctrlKey || event.metaKey || event.altKey || !this.entered) return;
    if (document.body.classList.contains('in-ritual')) {
      if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); this.ritual.drawNext(); }
      return;
    }
    if (event.key === 'm' || event.key === 'M') this.toggleSound();
    else if (event.key === 't' || event.key === 'T') this.tome.toggle();
    else if (event.key === 'ArrowLeft') this.loadDay(shiftDay(this.state.day, -1));
    else if (event.key === 'ArrowRight' && !this.state.is_today) this.loadDay(shiftDay(this.state.day, 1));
    else if (event.key === '/') { event.preventDefault(); $('#note-body').focus(); }
  },

  toggleSound() {
    this.choir.unlock();
    this.choir.setEnabled(!this.choir.enabled);
    $('#sound-toggle').classList.toggle('is-muted', !this.choir.enabled);
    toast(this.choir.enabled ? 'The choir sings again.' : 'The choir falls silent.');
  },

  showThreshold() {
    const { state } = this;
    $('#threshold-date').textContent = formatDay(state.today, true);
    const name = state.settings.crest_name;
    const crest = $('#threshold-crest');
    if (name) {
      crest.replaceChildren(h('img', { src: `/art/forge.svg?name=${encodeURIComponent(name)}`, alt: `Crest of ${name}` }));
      $('#threshold-line').textContent = `Welcome back, ${name}. The night is waiting.`;
    }
    $('#enter').textContent = state.ritual.status === 'sealed' ? 'Return to the Codex' : 'Light the Candle';
    $('#enter').focus();
  },

  enter() {
    this.entered = true;
    this.choir.unlock();
    this.choir.configure(this.state.settings);
    this.choir.setNight(this.state.rules);
    const threshold = $('#threshold');
    threshold.classList.add('is-leaving');
    setTimeout(() => { threshold.hidden = true; }, 1200);
    this.choir.play('chime');
    if (this.state.is_today && this.state.ritual.status !== 'sealed') {
      setTimeout(() => this.ritual.open(this.state), 700);
    }
  },

  // -- header & altar ------------------------------------------------------------
  renderHeader() {
    const { state } = this;
    $('#day-label').textContent = state.is_today ? `Tonight · ${formatDay(state.day)}` : formatDay(state.day, true);
    $('#next-day').disabled = state.is_today;
    $('#today-btn').hidden = state.is_today;
    $('#omen-line').textContent = state.rules?.omen || (state.is_today ? 'The cards have not yet been drawn.' : '');
    const crest = $('#day-crest');
    crest.replaceChildren(state.house ? h('img', { src: state.house.art, alt: `Crest of ${state.house.name}` }) : h('span', { class: 'crest-empty' }, '☾'));
    crest.title = state.house ? `${state.house.name} — “${state.house.motto}”` : 'No House presides yet';
  },

  renderAltar() {
    const { state } = this;
    const spread = $('#spread');
    const edictsEl = $('#edicts');
    const houseEl = $('#house');
    const rules = state.rules;
    edictsEl.replaceChildren();
    houseEl.replaceChildren();
    if (!rules) {
      spread.replaceChildren(h('div', { class: 'altar__empty' },
        h('p', {}, state.is_today ? 'The altar is bare. Five cards wait in the dark.' : 'No hand was bound this night.'),
        state.is_today ? h('button', { class: 'btn btn--primary', onclick: () => this.ritual.open(this.state) }, 'Begin the Draw') : null));
      return;
    }
    const drawn = state.ritual.drawn;
    const keep = state.ritual.keep;
    const kept = POSITIONS.map((pos, i) => {
      const card = drawn[keep[i]];
      const el = cardEl(card, { size: 'sm', interactive: true, label: `${POSITION_GLYPH[pos]} ${pos}` });
      el.addEventListener('click', () => this.showCard(card));
      return el;
    });
    const burned = drawn.filter((_, i) => !keep.includes(i)).map((card) => h('button', {
      class: 'ash-token', type: 'button', title: `${card.name} — burned`, onclick: () => this.showCard(card),
    }, '🜂 ', card.name));
    spread.replaceChildren(h('div', { class: 'spread__kept' }, kept), h('div', { class: 'spread__ashes' }, burned));
    edictsEl.replaceChildren(...rules.edicts.map((e) => h('li', { class: `edict edict--${e.tone}` },
      h('span', { class: 'edict__glyph' }, POSITION_GLYPH[e.position] || '✦'),
      h('div', {}, h('b', {}, e.title), h('p', {}, e.text)))));
    if (state.house) {
      houseEl.append(
        h('img', { src: state.house.art, alt: '' }),
        h('div', {}, h('p', { class: 'house__label' }, 'Presiding House'), h('b', {}, state.house.name), h('p', { class: 'house__motto' }, `“${state.house.motto}”`)));
    }
  },

  // -- the ritual ---------------------------------------------------------------------
  async onSealed(state) {
    this.setState(state);
    await sleep(400);
    this.choir.play('toll');
    const items = [...document.querySelectorAll('#edicts .edict')];
    items.forEach((el) => el.classList.add('is-hidden'));
    for (const el of items) {
      await sleep(380);
      el.classList.remove('is-hidden');
      el.classList.add('is-revealed');
    }
    toast(state.rules.omen, 'info', 7000);
  },

  // -- notes ----------------------------------------------------------------------------
  async onInscribed(result, { edited }) {
    const { note, invocation, new_discoveries: fresh } = result;
    const rules = this.state.rules;
    if (edited) this.board.replace(note); else this.board.add(note);
    this.rites.setNotes(this.board.notes);
    await sleep(80);
    const origin = this.board.origin(note.id);
    this.choir.play('seal');
    if (rules.effects.tremor) {
      this.board.quake();
      this.choir.play('thunder');
    }
    if (rules.effects.bloom && origin) this.rites.burst('petal', 30, origin, { speed: 120, life: 2.6, gravity: 40, sway: 20, vr: 2 });
    await this.rites.performAll(invocation.performed, origin, {
      weight: invocation.weight, newIds: fresh.map((r) => r.id),
    });
    if (rules.effects.scatter) this.board.scatter(note.id);
    for (const rite of fresh) {
      toast(`A rite discovered: ${rite.name}. Its secret is written in the Tome.`, 'discovery', 6000);
      this.choir.play('discover');
      await sleep(600);
    }
  },

  openNote(note, { echo = false } = {}) {
    const dialog = $('#note-dialog');
    const states = this.state.rules?.sigil_states || {};
    const editable = this.state.is_today && !echo && !note.bound && this.state.rules;
    const rites = (note.rites || []).map((id) => this.catalogue.rites.find((r) => r.id === id)).filter(Boolean);
    dialog.replaceChildren(h('article', { class: 'scroll__inner' },
      echo ? h('p', { class: 'scroll__echo' }, `An echo from ${formatDay(note.day, true)}`) : null,
      h('header', {},
        h('h2', {}, note.title || 'Untitled'),
        h('p', { class: 'scroll__meta' }, `Inscribed at ${hourName(note.local_time) || note.local_time} · ${shortDay(note.day)}`,
          note.bound ? ' · bound in chains ⛓' : '')),
      h('div', { class: 'scroll__body', html: renderInk(note.body, echo ? {} : states) }),
      h('dl', { class: 'scroll__numbers' },
        h('dt', {}, 'Weight'), h('dd', {}, String(note.weight)),
        h('dt', {}, 'Sigils'), h('dd', {}, String((note.sigils || []).length)),
        h('dt', {}, 'Rites'), h('dd', {}, note.rite_names?.length ? note.rite_names.join(', ') : 'none — the ink settled')),
      h('footer', { class: 'scroll__actions' },
        h('button', { class: 'btn', onclick: () => this.recite(note) }, '🕯 Recite'),
        rites.length && !echo ? h('button', { class: 'btn', onclick: async () => {
          dialog.close();
          await this.rites.performAll(rites.map((r) => ({ ...r, intensity: 1 })), this.board.origin(note.id), { weight: note.weight });
        } }, '✦ Replay rites') : null,
        editable ? h('button', { class: 'btn', onclick: () => { dialog.close(); this.quill.edit(note); } }, '✒ Edit') : null,
        !echo ? h('button', { class: 'btn btn--danger', onclick: () => this.deleteNote(note, dialog) }, '🜂 Burn') : null,
        h('button', { class: 'btn btn--ghost', onclick: () => dialog.close() }, 'Close'))));
    this.choir.play('page');
    dialog.showModal();
  },

  async deleteNote(note, dialog) {
    if (!window.confirm(`Burn “${note.title || 'Untitled'}” forever? This cannot be undone.`)) return;
    try {
      const origin = this.board.origin(note.id);
      const result = await api.deleteNote(note.id);
      dialog.close();
      this.board.remove(note.id);
      this.rites.setNotes(this.board.notes);
      if (result.moths && origin) {
        await this.rites.perform({ id: 'moths', name: 'The Moths Depart', animation: 'moths', sound: 'flutter', intensity: 1 }, origin);
      } else if (origin) {
        this.choir.play('burn');
        this.rites.burst('ember', 50, origin, { speed: 120, life: 1.8, angle: -Math.PI / 2, spread: 2, gravity: -50, color: '#ff8a3d' });
        this.rites.burst('ash', 30, origin, { speed: 60, life: 2.2, gravity: 50, sway: 12 });
      }
    } catch (err) {
      toast(err.message, 'error');
    }
  },

  recite(note) {
    const synth = window.speechSynthesis;
    if (!synth) {
      toast('This browser has no voice to lend.');
      return;
    }
    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(speakable(`${note.title}. ${note.body}`));
    utterance.pitch = 0.6;
    utterance.rate = 0.86;
    const chosen = synth.getVoices().find((v) => v.name === this.state.settings.voice);
    if (chosen) utterance.voice = chosen;
    synth.speak(utterance);
  },

  showCard(card) {
    const dialog = $('#card-dialog');
    const edicts = (this.state.rules?.edicts || []).filter((e) => e.source === card.id);
    dialog.replaceChildren(h('div', { class: 'scroll__inner' },
      cardDialogContent(card, edicts),
      h('footer', { class: 'scroll__actions' }, h('button', { class: 'btn btn--ghost', onclick: () => dialog.close() }, 'Close'))));
    this.choir.play('flip');
    dialog.showModal();
  },

  async replay(rite) {
    this.tome.close();
    await sleep(300);
    await this.rites.perform({ ...rite, intensity: 1.2 }, null, { weight: 29 });
  },

  async saveSettings(changes) {
    try {
      const settings = await api.saveSettings(changes);
      this.state.settings = settings;
      this.choir.configure(settings);
      applyTheme(this.state.rules, { isToday: this.state.is_today, settings });
    } catch (err) {
      toast(err.message, 'error');
    }
  },

  async extinguish() {
    if (!window.confirm('Snuff the candle and close the Codex?')) return;
    this.choir.stopDrone();
    this.choir.play('toll');
    try { await api.shutdown(); } catch { /* already gone */ }
    document.body.replaceChildren(h('div', { class: 'farewell' },
      h('h1', {}, 'The candle is snuffed.'),
      h('p', {}, 'Your notes rest safely on this computer. Open the Codex again with its launcher whenever the night calls.')));
  },
};

// Expose a little for curious hands in the console (and for tests).
window.nocturne = app;
app.boot();

export { app, cardReading };
