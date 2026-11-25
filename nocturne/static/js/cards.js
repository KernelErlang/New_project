// Tarot card elements shared by the ritual, the altar and the tome.

import { h } from './util.js';

export const POSITION_LABEL = {
  crown: 'The Crown', heart: 'The Heart', shadow: 'The Shadow', burned: 'The Ashes',
};
export const POSITION_ROLE = {
  crown: 'what reigns — aspect, colours, music',
  heart: 'what stirs — number and awakened sigils',
  shadow: 'what binds — the night\'s constraint',
  burned: 'what was refused — banished and forbidden',
};
export const POSITION_GLYPH = { crown: '♔', heart: '❦', shadow: '☾', burned: '🜂' };

/** Build a flippable card. */
export function cardEl(card, { flipped = true, size = 'md', label = '', interactive = false } = {}) {
  const front = h('div', { class: 'tcard__face tcard__front' },
    h('img', { src: card.art, alt: '', draggable: 'false', loading: 'lazy' }),
    h('span', { class: 'tcard__numeral' }, card.numeral),
    h('span', { class: 'tcard__name' }, card.name),
    card.reversed ? h('span', { class: 'tcard__rev' }, 'Reversed') : null);
  const back = h('div', { class: 'tcard__face tcard__back' },
    h('img', { src: '/art/card/back.svg', alt: '', draggable: 'false' }));
  const el = h(interactive ? 'button' : 'div', {
    class: `tcard tcard--${size}${card.reversed ? ' is-reversed' : ''}${flipped ? ' is-flipped' : ''}`,
    type: interactive ? 'button' : null,
    'aria-label': `${card.name}${card.reversed ? ' (reversed)' : ''}`,
    dataset: { id: card.id },
  }, h('div', { class: 'tcard__inner' }, back, front));
  if (label) el.append(h('span', { class: 'tcard__pos' }, label));
  return el;
}

/** The oracle's reading of a card, with what it would do in each position. */
export function cardReading(card, { previews = null, focus = null, effects = null } = {}) {
  const keywords = card.reversed ? card.reversed_keywords : card.upright;
  const wrap = h('div', { class: 'reading' },
    h('h3', { class: 'reading__name' }, card.name,
      card.reversed ? h('span', { class: 'reading__rev' }, ' · reversed') : null),
    h('p', { class: 'reading__epigraph' }, `“${card.epigraph}”`),
    h('p', { class: 'reading__keys' }, keywords.join(' · ')));
  if (previews) {
    const list = h('dl', { class: 'reading__previews' });
    for (const position of ['crown', 'heart', 'shadow', 'burned']) {
      const edicts = previews[position] || [];
      list.append(
        h('dt', { class: position === focus ? 'is-focus' : '' },
          `${POSITION_GLYPH[position]} ${position === 'burned' ? 'If burned' : `In ${POSITION_LABEL[position]}`}`),
        h('dd', { class: position === focus ? 'is-focus' : '' },
          edicts.map((e) => h('span', { class: `edict-chip edict-chip--${e.tone}` }, h('b', {}, e.title), ' — ', e.text))),
      );
    }
    wrap.append(list);
  }
  if (effects?.length) {
    wrap.append(h('div', { class: 'reading__tonight' },
      h('h4', {}, 'Tonight it decrees'),
      effects.map((e) => h('p', { class: `edict-chip edict-chip--${e.tone}` }, h('b', {}, e.title), ' — ', e.text))));
  }
  return wrap;
}
