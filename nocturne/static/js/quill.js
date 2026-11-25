// The Quill: composing notes, weaving sigils and watching the omen candle.

import { api } from './api.js';
import { allSigils, expandShortcodes, sigilById, sigilsIn, wordsIn } from './ink.js';
import { $, debounce, h, hashString, localTime, seeded, toast } from './util.js';

export class Quill {
  constructor({ root, choir, onInscribed }) {
    this.root = root;
    this.choir = choir;
    this.onInscribed = onInscribed;
    this.title = $('#note-title', root);
    this.body = $('#note-body', root);
    this.palette = $('#sigil-palette', root);
    this.meters = $('#quill-meters', root);
    this.candle = $('#omen-candle', root);
    this.velocityEl = $('#velocity', root);
    this.sealedEl = $('#quill-sealed', root);
    this.formEl = $('#quill-body', root);
    this.inscribeBtn = $('#inscribe', root);
    this.cancelBtn = $('#cancel-edit', root);
    this.editing = null;
    this.state = null;
    this.typed = 0;
    this.activeMs = 0;
    this.lastKey = 0;
    this.busy = false;
    this.divine = debounce(() => this.consultOmen(), 450);

    this.body.addEventListener('input', () => this.onInput(this.body));
    this.title.addEventListener('input', () => this.onInput(this.title));
    for (const field of [this.title, this.body]) {
      field.addEventListener('keydown', (event) => this.onKey(event));
    }
    this.inscribeBtn.addEventListener('click', () => this.inscribe());
    $('#clear-note', root).addEventListener('click', () => this.clear());
    this.cancelBtn.addEventListener('click', () => this.clear());
  }

  get rules() { return this.state?.rules || null; }

  configure(state) {
    this.state = state;
    const open = state.is_today && state.rules;
    this.formEl.hidden = !open;
    this.sealedEl.hidden = Boolean(open);
    if (!open) {
      this.sealedEl.replaceChildren(
        h('p', { class: 'quill__sealed-glyph' }, '✒'),
        h('p', {}, state.is_today ? 'Draw the night’s cards before you write.'
          : 'This night is sealed. Its ink has long since dried; you may read, but not write.'),
        state.is_today ? h('button', { class: 'btn btn--primary', id: 'open-ritual' }, 'Begin the Draw') : null,
      );
      return;
    }
    this.velocityEl.hidden = !state.rules.effects.velocity;
    this.renderPalette();
    this.measure();
  }

  renderPalette() {
    const states = this.rules?.sigil_states || {};
    let sigils = allSigils();
    if (this.rules?.effects?.scramble) {
      const r = seeded(this.rules.scramble_seed || hashString(this.state.day));
      sigils = sigils.map((s) => [r(), s]).sort((a, b) => a[0] - b[0]).map(([, s]) => s);
    }
    this.palette.replaceChildren(...sigils.map((sigil) => {
      const state = states[sigil.id] || 'plain';
      const label = { awakened: 'awakened tonight', ashen: 'banished — crumbles to ash', forbidden: 'FORBIDDEN — binds in chains', wild: 'wild — counts as every element', plain: '' }[state];
      return h('button', {
        class: `sigil sigil--${state}`, type: 'button',
        title: `${sigil.name} ${sigil.shortcode}${label ? ` · ${label}` : ''}\n${sigil.lore}`,
        'aria-label': `Inscribe ${sigil.name}${label ? `, ${label}` : ''}`,
        onclick: () => this.insert(sigil.id),
      }, h('span', { class: 'sigil__glyph' }, sigil.glyph));
    }));
  }

  insert(sigilId) {
    const sigil = sigilById(sigilId);
    if (!sigil) return;
    const field = document.activeElement === this.title ? this.title : this.body;
    const start = field.selectionStart ?? field.value.length;
    const end = field.selectionEnd ?? field.value.length;
    field.setRangeText(sigil.glyph, start, end, 'end');
    field.focus();
    const state = this.rules?.sigil_states?.[sigilId];
    this.choir.play(state === 'forbidden' ? 'error' : state === 'ashen' ? 'fizzle' : 'sigil');
    this.onInput(field, true);
  }

  onKey(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      this.inscribe();
      return;
    }
    if (event.key.length === 1 && !event.ctrlKey && !event.metaKey) {
      const now = performance.now();
      if (this.lastKey) this.activeMs += Math.min(2000, now - this.lastKey);
      this.lastKey = now;
      this.typed += 1;
      this.choir.quill(event.key);
    }
  }

  get velocity() {
    if (this.activeMs < 4000) return 0;
    return Math.round((this.typed / this.activeMs) * 60000);
  }

  onInput(field, silent = false) {
    if (field.value.includes(':')) {
      const caret = field.selectionStart;
      const before = field.value.slice(0, caret);
      const expanded = expandShortcodes(before);
      if (expanded !== before) {
        field.value = expanded + field.value.slice(caret);
        field.setSelectionRange(expanded.length, expanded.length);
        if (!silent) this.choir.play('sigil');
      }
    }
    this.measure();
    this.divine();
  }

  /** Mirror of the server's edict checks, for instant feedback. */
  measure() {
    const rules = this.rules;
    if (!rules) return [];
    const c = rules.constraints;
    const text = `${this.title.value}\n${this.body.value}`;
    const found = sigilsIn(text);
    const chars = [...this.body.value].length;
    const words = wordsIn(text).length;
    const items = [];
    const add = (ok, label) => items.push({ ok, label });
    if (c.char_limit) add(chars <= c.char_limit, `${chars} / ${c.char_limit} characters`);
    if (c.min_sigils) add(found.length >= c.min_sigils, `${found.length} / ${c.min_sigils} sigils`);
    if (c.min_words) add(words >= c.min_words, `${words} / ${c.min_words} words`);
    if (c.begin_with_sigil) {
      const first = [...expandShortcodes(this.body.value).trimStart()][0] || '';
      add(sigilsIn(first).length > 0, 'begins with a sigil');
    }
    if (c.even_sigils) add(found.length % 2 === 0, 'sigils in pairs');
    if (c.balanced_sigils) {
      const light = found.filter((id) => sigilById(id)?.polarity === 'light').length;
      add(light * 2 === found.length, `light ${light} · dark ${found.length - light}`);
    }
    for (const id of c.require || []) add(found.includes(id), `bears ${sigilById(id)?.glyph}`);
    const forbidden = found.filter((id) => rules.sigil_states[id] === 'forbidden');
    const warn = forbidden.length && !rules.modifiers.includes('ward');
    this.meters.replaceChildren(
      ...items.map((item) => h('span', { class: `meter ${item.ok ? 'is-ok' : 'is-bad'}` }, item.ok ? '✓ ' : '✗ ', item.label)),
      ...(warn ? [h('span', { class: 'meter is-bad meter--chain' }, '⛓ a forbidden sigil will bind this note')] : []),
    );
    if (this.rules.effects.velocity) {
      const v = this.velocity;
      this.velocityEl.firstElementChild.style.width = `${Math.min(100, v / 3)}%`;
      this.velocityEl.title = `${v} characters a minute`;
    }
    const ok = items.every((i) => i.ok) && (this.title.value.trim() || this.body.value.trim());
    this.inscribeBtn.disabled = !ok || this.busy;
    return items;
  }

  payload() {
    return {
      title: this.title.value.trim(),
      body: this.body.value,
      local_time: localTime(),
      velocity: this.velocity,
    };
  }

  async consultOmen() {
    if (!this.rules || !this.state?.is_today) return;
    const draft = this.payload();
    if (!draft.title && !draft.body.trim()) {
      this.setFlames(0);
      return;
    }
    try {
      const omen = await api.divine(draft);
      this.setFlames(omen.flames);
    } catch {
      /* the omen is a luxury, never an obstacle */
    }
  }

  setFlames(n) {
    [...this.candle.children].forEach((flame, i) => flame.classList.toggle('is-lit', i < n));
    this.candle.title = n ? `The candle flares: ${n} rite${n > 1 ? 's' : ''} stir${n > 1 ? '' : 's'}.`
      : 'The candle is still. No rite stirs.';
  }

  edit(note) {
    this.editing = note;
    this.title.value = note.title;
    this.body.value = note.body;
    this.root.classList.add('is-editing');
    this.inscribeBtn.firstChild.textContent = 'Re-inscribe ';
    this.cancelBtn.hidden = false;
    this.body.focus();
    this.measure();
    this.divine();
  }

  clear() {
    this.editing = null;
    this.title.value = '';
    this.body.value = '';
    this.typed = 0;
    this.activeMs = 0;
    this.lastKey = 0;
    this.root.classList.remove('is-editing');
    this.inscribeBtn.firstChild.textContent = 'Inscribe ';
    this.cancelBtn.hidden = true;
    this.setFlames(0);
    this.measure();
  }

  async inscribe() {
    if (this.busy || !this.rules) return;
    const problems = this.measure().filter((i) => !i.ok);
    if (problems.length) {
      this.choir.play('error');
      toast(`The ink will not take: ${problems[0].label}.`, 'error');
      return;
    }
    const draft = this.payload();
    if (!draft.title && !draft.body.trim()) return;
    this.busy = true;
    this.inscribeBtn.disabled = true;
    try {
      const editing = this.editing;
      const result = editing ? await api.updateNote(editing.id, draft) : await api.createNote(draft);
      this.clear();
      // The rites play on while the quill is already free for the next note.
      Promise.resolve(this.onInscribed(result, { edited: Boolean(editing) }))
        .catch((err) => toast(err.message, 'error'));
    } catch (err) {
      this.choir.play('error');
      toast(err.message, 'error');
    } finally {
      this.busy = false;
      this.measure();
    }
  }
}
