// Rendering text that contains sigils.

import { escapeHtml } from './util.js';

const byGlyph = new Map();
const byId = new Map();

export function setSigils(sigils) {
  byGlyph.clear();
  byId.clear();
  for (const sigil of sigils) {
    byGlyph.set(sigil.glyph, sigil);
    byId.set(sigil.id, sigil);
  }
}

export const sigilById = (id) => byId.get(id);
export const sigilByGlyph = (glyph) => byGlyph.get(glyph);
export const allSigils = () => [...byId.values()];

/** Replace :shortcodes: with glyphs. */
export function expandShortcodes(text) {
  return text.replace(/:([a-z]+):/g, (whole, id) => byId.get(id)?.glyph ?? whole);
}

/** Ids of the sigils in a text, in reading order. */
export function sigilsIn(text) {
  const out = [];
  for (const ch of expandShortcodes(text)) {
    const sigil = byGlyph.get(ch);
    if (sigil) out.push(sigil.id);
  }
  return out;
}

export function stripSigils(text) {
  let out = '';
  for (const ch of expandShortcodes(text)) if (!byGlyph.has(ch) && ch !== '︎' && ch !== '️') out += ch;
  return out;
}

export function wordsIn(text) {
  return stripSigils(text).normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .match(/[a-z]+(?:'[a-z]+)?/g) || [];
}

/** Escape text and wrap each sigil in a span coloured by its state tonight. */
export function renderInk(text, states = {}, { limit = Infinity } = {}) {
  let html = '';
  let count = 0;
  for (const ch of text) {
    if (count >= limit) {
      html += '…';
      break;
    }
    count += 1;
    const sigil = byGlyph.get(ch);
    if (sigil) {
      const state = states[sigil.id] || 'plain';
      html += `<span class="sg sg--${state}" title="${escapeHtml(sigil.name)}">${ch}</span>`;
    } else if (ch === '\n') {
      html += '<br>';
    } else {
      html += escapeHtml(ch);
    }
  }
  return html;
}

/** Text for speech: sigils are read aloud by name. */
export function speakable(text) {
  let out = '';
  for (const ch of text) {
    const sigil = byGlyph.get(ch);
    out += sigil ? ` ${sigil.name}, ` : ch;
  }
  return out;
}
