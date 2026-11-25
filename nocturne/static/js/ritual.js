// The nightly ritual: draw five, keep three (Crown, Heart, Shadow), burn two.

import { api } from './api.js';
import { cardEl, cardReading, POSITION_GLYPH, POSITION_LABEL, POSITION_ROLE } from './cards.js';
import { $, formatDay, h, sleep, toast } from './util.js';

const ORDER = ['crown', 'heart', 'shadow'];

export class Ritual {
  constructor({ root, choir, rites, onSealed }) {
    this.root = root;
    this.choir = choir;
    this.rites = rites;
    this.onSealed = onSealed;
    this.drawn = [];
    this.revealed = 0;
    this.selection = [];
    this.busy = false;
  }

  open(state) {
    this.state = state;
    this.drawn = state.ritual.drawn || [];
    this.revealed = 0;
    this.selection = [];
    this.build();
    this.root.hidden = false;
    document.body.classList.add('in-ritual');
    requestAnimationFrame(() => this.root.classList.add('is-open'));
    if (state.ritual.status === 'drawn') this.revealAll(true);
  }

  close() {
    this.root.classList.remove('is-open', 'is-keeping');
    document.body.classList.remove('in-ritual');
    setTimeout(() => { this.root.hidden = true; this.root.innerHTML = ''; }, 900);
  }

  build() {
    this.root.innerHTML = '';
    this.instr = h('p', { class: 'ritual__instr' }, 'Touch the deck five times. Fate shuffled it long before you came.');
    this.deck = h('button', {
      class: 'deck', type: 'button', 'aria-label': 'Draw a card',
      onclick: () => this.drawNext(),
    }, ...[0, 1, 2].map((i) => h('img', { src: '/art/card/back.svg', alt: '', style: { '--i': i } })),
    h('span', { class: 'deck__count' }, '5'));
    this.hand = h('div', { class: 'hand' }, ...[0, 1, 2, 3, 4].map((i) => h('div', { class: 'hand__slot', dataset: { i } })));
    this.slots = h('div', { class: 'positions' }, ...ORDER.map((pos) => h('div', { class: 'position', dataset: { pos } },
      h('span', { class: 'position__glyph' }, POSITION_GLYPH[pos]),
      h('span', { class: 'position__title' }, POSITION_LABEL[pos]),
      h('span', { class: 'position__role' }, POSITION_ROLE[pos]),
      h('span', { class: 'position__card' }, '—'))));
    this.oracle = h('div', { class: 'oracle' }, h('p', { class: 'oracle__idle' },
      'Hover over a card to read it, and to see what it would decree in each position.'));
    this.bindBtn = h('button', { class: 'btn btn--primary btn--large', type: 'button', disabled: true,
      onclick: () => this.bind() }, 'Bind the Fate');
    this.resetBtn = h('button', { class: 'btn btn--ghost', type: 'button', disabled: true,
      onclick: () => this.resetSelection() }, 'Choose again');
    this.root.append(
      h('div', { class: 'ritual__glow', 'aria-hidden': 'true' }),
      h('header', { class: 'ritual__head' },
        h('p', { class: 'ritual__date' }, formatDay(this.state.today, true)),
        h('h2', { class: 'ritual__title' }, 'The Night’s Draw'),
        this.instr),
      h('div', { class: 'ritual__table' }, this.deck, this.hand),
      h('div', { class: 'ritual__lower' }, this.slots, this.oracle),
      h('footer', { class: 'ritual__foot' }, this.resetBtn, this.bindBtn),
    );
  }

  async drawNext() {
    if (this.busy || this.revealed >= 5) return;
    this.busy = true;
    try {
      if (!this.drawn.length) {
        const ritual = await api.draw();
        this.drawn = ritual.drawn;
      }
      await this.reveal(this.revealed);
      this.revealed += 1;
      $('.deck__count', this.deck).textContent = String(5 - this.revealed);
      if (this.revealed >= 5) this.beginKeeping();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      this.busy = false;
    }
  }

  async reveal(i, quick = false) {
    const card = this.drawn[i];
    const slot = this.hand.children[i];
    const el = cardEl(card, { flipped: false, size: 'lg', interactive: true });
    el.classList.add('is-arriving');
    el.addEventListener('click', () => this.toggle(i));
    el.addEventListener('mouseenter', () => this.read(i));
    el.addEventListener('focus', () => this.read(i));
    slot.append(el);
    this.choir.play('swish');
    await sleep(quick ? 80 : 420);
    el.classList.add('is-flipped');
    this.choir.play('flip');
    this.read(i);
    await sleep(quick ? 60 : 380);
  }

  async revealAll(quick) {
    this.busy = true;
    for (let i = 0; i < 5; i += 1) await this.reveal(i, quick);
    this.revealed = 5;
    $('.deck__count', this.deck).textContent = '0';
    this.busy = false;
    this.beginKeeping();
  }

  beginKeeping() {
    this.deck.classList.add('is-spent');
    this.root.classList.add('is-keeping');
    this.instr.textContent = 'Keep three. The first you choose becomes the Crown, the second the Heart, '
      + 'the third the Shadow. The two you spurn will burn — and even ashes have power.';
  }

  focusPosition() {
    return ORDER[this.selection.length] || 'burned';
  }

  read(i) {
    const card = this.drawn[i];
    if (!card) return;
    const chosen = this.selection.indexOf(i);
    const focus = chosen >= 0 ? ORDER[chosen] : this.focusPosition();
    this.oracle.replaceChildren(cardReading(card, { previews: card.previews, focus }));
  }

  toggle(i) {
    if (this.revealed < 5 || this.busy) return;
    const at = this.selection.indexOf(i);
    if (at >= 0) {
      this.selection.splice(at, 1);
      this.choir.play('deselect');
    } else if (this.selection.length < 3) {
      this.selection.push(i);
      this.choir.play('select');
    } else {
      toast('Three are already kept. Release one to choose another.');
      return;
    }
    this.renderSelection();
    this.read(i);
  }

  resetSelection() {
    this.selection = [];
    this.renderSelection();
  }

  renderSelection() {
    [...this.hand.children].forEach((slot, i) => {
      const el = slot.firstElementChild;
      if (!el) return;
      const at = this.selection.indexOf(i);
      el.classList.toggle('is-chosen', at >= 0);
      el.querySelector('.tcard__pos')?.remove();
      if (at >= 0) el.append(h('span', { class: 'tcard__pos' }, `${POSITION_GLYPH[ORDER[at]]} ${POSITION_LABEL[ORDER[at]]}`));
    });
    ORDER.forEach((pos, at) => {
      const slot = this.slots.children[at];
      const index = this.selection[at];
      slot.classList.toggle('is-filled', index !== undefined);
      $('.position__card', slot).textContent = index !== undefined
        ? `${this.drawn[index].name}${this.drawn[index].reversed ? ' (reversed)' : ''}` : '—';
    });
    this.bindBtn.disabled = this.selection.length !== 3;
    this.resetBtn.disabled = this.selection.length === 0;
  }

  async bind() {
    if (this.selection.length !== 3 || this.busy) return;
    this.busy = true;
    this.bindBtn.disabled = true;
    try {
      const state = await api.keep(this.selection);
      this.instr.textContent = 'It is done. The spurned cards burn; the kept ones take their thrones.';
      this.choir.play('burn');
      [...this.hand.children].forEach((slot, i) => {
        const el = slot.firstElementChild;
        if (!el) return;
        if (this.selection.includes(i)) {
          el.classList.add('is-kept');
        } else {
          el.classList.add('is-burning');
          const box = el.getBoundingClientRect();
          this.rites.burst('ember', 70, { x: box.left + box.width / 2, y: box.top + box.height / 2 }, {
            speed: 140, life: 2.2, angle: -Math.PI / 2, spread: 2.4, gravity: -80, color: '#ff8a3d',
          });
          this.rites.burst('ash', 30, { x: box.left + box.width / 2, y: box.top + box.height * 0.8 }, {
            speed: 60, life: 2.6, gravity: 50, sway: 14,
          });
        }
      });
      await sleep(1500);
      this.choir.play('bind');
      await sleep(900);
      this.close();
      this.onSealed(state);
    } catch (err) {
      toast(err.message, 'error');
      this.bindBtn.disabled = false;
    } finally {
      this.busy = false;
    }
  }
}
