// The Tome: a drawer holding the Codex of Rites, the sigils, the archive of past
// nights, the Houses, the whole deck and the settings.

import { api } from './api.js';
import { cardEl, cardReading } from './cards.js';
import { allSigils } from './ink.js';
import { $, $$, formatDay, h, shortDay, toast } from './util.js';

const TABS = ['rites', 'sigils', 'archive', 'houses', 'deck', 'settings'];

export class Tome {
  constructor({ root, app }) {
    this.root = root;
    this.app = app;
    this.body = $('#tome-body', root);
    this.tab = 'rites';
    $$('[data-tab]', root).forEach((btn) => btn.addEventListener('click', () => this.show(btn.dataset.tab)));
    $('#tome-close', root).addEventListener('click', () => this.close());
  }

  get isOpen() { return this.root.classList.contains('is-open'); }

  open(tab = this.tab) {
    this.root.classList.add('is-open');
    this.root.setAttribute('aria-hidden', 'false');
    this.app.choir.play('page');
    this.show(tab);
  }

  close() {
    this.root.classList.remove('is-open');
    this.root.setAttribute('aria-hidden', 'true');
  }

  toggle(tab) {
    if (this.isOpen && (!tab || tab === this.tab)) this.close(); else this.open(tab);
  }

  async show(tab) {
    if (!TABS.includes(tab)) return;
    this.tab = tab;
    $$('[data-tab]', this.root).forEach((btn) => btn.setAttribute('aria-selected', String(btn.dataset.tab === tab)));
    this.body.replaceChildren(h('p', { class: 'tome__loading' }, 'Turning the pages…'));
    try {
      const view = await this[`render_${tab}`]();
      if (this.tab === tab) this.body.replaceChildren(view);
    } catch (err) {
      this.body.replaceChildren(h('p', { class: 'tome__loading' }, err.message));
    }
  }

  // -- rites ------------------------------------------------------------------
  async render_rites() {
    const { rites } = await api.codex();
    const found = rites.filter((r) => r.discovered).length;
    return h('section', { class: 'tome__section' },
      h('h2', {}, 'The Codex of Rites'),
      h('p', { class: 'tome__lede' }, `Hidden formulas weigh every note you inscribe. You have uncovered ${found} of ${rites.length}. `
        + 'Undiscovered rites show only a riddle; experiment with words, sigils, numbers and the hour.'),
      h('div', { class: 'progress' }, h('span', { style: { width: `${(found / rites.length) * 100}%` } })),
      h('div', { class: 'rites-grid' }, rites.map((rite) => h('article', { class: `rite-card${rite.discovered ? ' is-found' : ''} tier-${rite.tier}` },
        h('h3', {}, rite.discovered ? rite.name : '? ? ?'),
        h('p', { class: 'rite-card__hint' }, `“${rite.hint}”`),
        rite.discovered ? h('p', { class: 'rite-card__lore' }, rite.lore) : null,
        rite.discovered ? h('p', { class: 'rite-card__meta' }, `Performed ${rite.count}× · first on ${shortDay(rite.first_day)}`) : null,
        rite.discovered ? h('button', { class: 'btn btn--small', onclick: () => this.app.replay(rite) }, 'Perform again') : null))));
  }

  // -- sigils -----------------------------------------------------------------
  async render_sigils() {
    const states = this.app.state?.rules?.sigil_states || {};
    const label = { awakened: 'Awakened', ashen: 'Banished', forbidden: 'Forbidden', wild: 'Wild', plain: '' };
    return h('section', { class: 'tome__section' },
      h('h2', {}, 'The Sigils'),
      h('p', { class: 'tome__lede' }, 'Click a sigil in the Quill, or type its shortcode (for example :sol:). '
        + 'Each has an element, a polarity and a value — the number of the card that rules it.'),
      h('div', { class: 'sigil-table' }, allSigils().map((s) => h('article', { class: `sigil-row sigil-row--${states[s.id] || 'plain'}` },
        h('span', { class: 'sigil-row__glyph' }, s.glyph),
        h('div', {},
          h('h3', {}, s.name, ' ', h('code', {}, s.shortcode), states[s.id] && states[s.id] !== 'plain' ? h('span', { class: 'tag' }, label[states[s.id]]) : null),
          h('p', { class: 'sigil-row__meta' }, `${s.element} · ${s.polarity} · value ${s.value}`),
          h('p', {}, s.lore))))));
  }

  // -- archive ------------------------------------------------------------------
  async render_archive() {
    const { days } = await api.calendar();
    if (!days.length) return h('p', { class: 'tome__lede' }, 'No nights have been observed yet.');
    return h('section', { class: 'tome__section' },
      h('h2', {}, 'The Archive of Nights'),
      h('p', { class: 'tome__lede' }, 'Every night keeps its own cards, colours, music and notes. Visit one to read it as it was.'),
      h('ol', { class: 'archive' }, days.map((d) => h('li', {},
        h('button', { class: `archive__day${d.day === this.app.state?.day ? ' is-current' : ''}`, onclick: () => { this.close(); this.app.loadDay(d.day); } },
          d.house ? h('img', { src: `/art/crest/${d.house}.svg`, alt: '', class: 'archive__crest' }) : h('span', { class: 'archive__crest' }),
          h('span', { class: 'archive__text' },
            h('b', {}, formatDay(d.day, true)),
            h('span', {}, d.sealed ? d.kept.map((k) => `${k.name}${k.reversed ? ' ℞' : ''}`).join(' · ') : 'Drawn, never bound'),
            d.aspect ? h('i', {}, d.aspect) : null),
          h('span', { class: 'archive__count' }, `${d.note_count} ${d.note_count === 1 ? 'note' : 'notes'}`))))));
  }

  // -- houses -------------------------------------------------------------------
  async render_houses() {
    const { houses } = this.app.catalogue;
    const current = this.app.state?.house?.id;
    const preview = h('img', { class: 'forge__crest', alt: 'Your forged crest' });
    const input = h('input', { class: 'forge__input', maxlength: '60', placeholder: 'Your name, or a motto…',
      value: this.app.state?.settings?.crest_name || '' });
    const refresh = () => { preview.src = `/art/forge.svg?name=${encodeURIComponent(input.value || 'Nameless')}`; };
    input.addEventListener('input', refresh);
    refresh();
    return h('section', { class: 'tome__section' },
      h('h2', {}, 'The Twelve Houses'),
      h('p', { class: 'tome__lede' }, 'One House presides over each sealed night, chosen by the cards you keep. Its crest seals every note.'),
      h('div', { class: 'houses' }, houses.map((house) => h('article', { class: `house-card${house.id === current ? ' is-current' : ''}` },
        h('img', { src: house.art, alt: `Crest of ${house.name}` }),
        h('h3', {}, house.name),
        h('p', { class: 'house-card__motto' }, `“${house.motto}”`),
        h('p', {}, house.blurb)))),
      h('div', { class: 'forge' },
        h('h3', {}, 'The Forge'),
        h('p', {}, 'Forge a crest of your own. The same name always yields the same arms.'),
        h('div', { class: 'forge__row' }, preview, h('div', {}, input,
          h('button', { class: 'btn btn--small', onclick: async () => {
            await this.app.saveSettings({ crest_name: input.value.trim() });
            toast('Your crest is borne upon the threshold.');
          } }, 'Bear this crest')))));
  }

  // -- deck -----------------------------------------------------------------------
  async render_deck() {
    const { deck } = this.app.catalogue;
    const groups = [['The Major Arcana', deck.filter((c) => c.arcana === 'major')]];
    for (const suit of ['wands', 'cups', 'swords', 'pentacles']) {
      groups.push([`The Suit of ${suit[0].toUpperCase()}${suit.slice(1)}`, deck.filter((c) => c.suit === suit)]);
    }
    return h('section', { class: 'tome__section' },
      h('h2', {}, 'The Deck of Seventy-Eight'),
      h('p', { class: 'tome__lede' }, 'Majors carry an arcanum — a signature mechanic. Minors work by suit and rank. Click any card to read it.'),
      groups.map(([title, cards]) => h('div', {},
        h('h3', { class: 'deck-group' }, title),
        h('div', { class: 'deck-grid' }, cards.map((card) => {
          const el = cardEl(card, { size: 'sm', interactive: true });
          el.addEventListener('click', () => this.app.showCard(card));
          return el;
        })))));
  }

  // -- settings ---------------------------------------------------------------------
  async render_settings() {
    const s = this.app.state.settings;
    const toggle = (key, label, hint) => {
      const input = h('input', { type: 'checkbox', checked: s[key] ? true : null });
      input.addEventListener('change', () => this.app.saveSettings({ [key]: input.checked }));
      return h('label', { class: 'setting' }, input, h('span', {}, h('b', {}, label), h('small', {}, hint)));
    };
    const volume = h('input', { type: 'range', min: '0', max: '1', step: '0.05', value: String(s.master_volume) });
    volume.addEventListener('change', () => this.app.saveSettings({ master_volume: Number(volume.value) }));
    volume.addEventListener('input', () => this.app.choir.configure({ master_volume: Number(volume.value) }));
    const voices = window.speechSynthesis?.getVoices?.() || [];
    const voice = h('select', {}, h('option', { value: '' }, 'Default voice'),
      voices.map((v) => h('option', { value: v.name, selected: v.name === s.voice ? true : null }, `${v.name} (${v.lang})`)));
    voice.addEventListener('change', () => this.app.saveSettings({ voice: voice.value }));
    return h('section', { class: 'tome__section settings' },
      h('h2', {}, 'Settings'),
      h('label', { class: 'setting setting--range' }, h('span', {}, h('b', {}, 'Volume'), h('small', {}, 'The whole choir')), volume),
      toggle('ambience', 'Ambient organ', 'A low drone, wind and distant bells in the night’s mode.'),
      toggle('effects', 'Rite sounds', 'Bells, thunder, wings and chains.'),
      toggle('quill_sounds', 'Quill sounds', 'The scratch of the nib as you type.'),
      toggle('reduced_motion', 'Stillness', 'Calmer animations for tired eyes.'),
      toggle('veil_all', 'Veil every note', 'Blur notes until you hover them, for privacy from wandering eyes.'),
      h('label', { class: 'setting setting--range' }, h('span', {}, h('b', {}, 'Reciting voice'), h('small', {}, 'Used when a note is read aloud.')), voice),
      h('h3', {}, 'Your notes are private'),
      h('p', { class: 'tome__lede' }, 'Everything lives in one file on this computer and is never sent anywhere. '
        + 'The Codex only answers your own browser.'),
      h('p', {}, h('code', { class: 'path' }, this.app.state.data_dir || '(data folder)')),
      h('div', { class: 'row' },
        h('button', { class: 'btn', onclick: () => api.download('json').catch((e) => toast(e.message, 'error')) }, 'Export as JSON'),
        h('button', { class: 'btn', onclick: () => api.download('markdown').catch((e) => toast(e.message, 'error')) }, 'Export as Markdown')),
      h('h3', {}, 'Keys of the Codex'),
      h('ul', { class: 'keys' },
        h('li', {}, h('kbd', {}, 'Ctrl'), ' + ', h('kbd', {}, '↵'), ' inscribe the note'),
        h('li', {}, h('kbd', {}, 'M'), ' mute or unmute'),
        h('li', {}, h('kbd', {}, 'T'), ' open or close the Tome'),
        h('li', {}, h('kbd', {}, '←'), ' ', h('kbd', {}, '→'), ' walk between nights'),
        h('li', {}, h('kbd', {}, '/'), ' take up the quill'),
        h('li', {}, h('kbd', {}, 'Esc'), ' close what is open')),
      h('h3', {}, 'Snuff the candle'),
      h('p', { class: 'tome__lede' }, 'Close the Codex entirely. You can reopen it any time with the launcher.'),
      h('button', { class: 'btn btn--danger', onclick: () => this.app.extinguish() }, 'Snuff the candle'));
  }
}

export function cardDialogContent(card, edicts) {
  return h('div', { class: 'card-detail' },
    cardEl(card, { size: 'xl' }),
    cardReading(card, { previews: card.previews || null, effects: edicts }));
}
