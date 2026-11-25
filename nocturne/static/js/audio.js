// The Choir — every sound in the Codex is synthesised live with the Web Audio API.
// Nothing is recorded: bells, wind, fire and chains are built from oscillators,
// noise and a generated cathedral reverb, and they are tuned to the night's mode.

const BELL_PARTIALS = [
  [0.5, 0.55, 1.0], [1, 1, 0.85], [1.183, 0.55, 0.65], [1.506, 0.45, 0.55],
  [2, 0.38, 0.45], [2.514, 0.28, 0.35], [2.662, 0.22, 0.3], [3.011, 0.18, 0.25], [4.166, 0.12, 0.18],
];

const rnd = (lo, hi) => lo + Math.random() * (hi - lo);

export class Choir {
  constructor() {
    this.ctx = null;
    this.enabled = true;
    this.volume = 0.7;
    this.ambience = true;
    this.effects = true;
    this.quillSounds = true;
    this.quillSong = false;
    this.silenced = false;
    this.tonality = { root_hz: 146.83, intervals: [0, 2, 3, 5, 7, 8, 10], mode: 'aeolian' };
    this.drone = null;
    this.bellTimer = null;
  }

  // -- lifecycle -----------------------------------------------------------
  unlock() {
    if (this.ctx) {
      if (this.ctx.state === 'suspended') this.ctx.resume();
      return;
    }
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    this.ctx = ctx;
    this.master = ctx.createGain();
    this.master.gain.value = this.enabled ? this.volume : 0;
    const compressor = ctx.createDynamicsCompressor();
    compressor.threshold.value = -16;
    compressor.ratio.value = 3.5;
    this.master.connect(compressor).connect(ctx.destination);

    this.reverb = ctx.createConvolver();
    this.reverb.buffer = this.impulse(4.2, 2.8);
    const wet = ctx.createGain();
    wet.gain.value = 0.5;
    this.reverb.connect(wet).connect(this.master);

    this.bus = ctx.createGain();
    this.bus.gain.value = 0.9;
    this.bus.connect(this.master);
    this.bus.connect(this.reverb);

    this.ambBus = ctx.createGain();
    this.ambBus.gain.value = 0;
    this.ambBus.connect(this.master);
    this.ambBus.connect(this.reverb);

    this.noiseBuffer = this.makeNoise(3);
    if (this.ambience && !this.silenced) this.startDrone();
  }

  get ready() {
    return Boolean(this.ctx) && this.enabled;
  }

  impulse(seconds, decay) {
    const rate = this.ctx.sampleRate;
    const length = Math.floor(rate * seconds);
    const buffer = this.ctx.createBuffer(2, length, rate);
    for (let channel = 0; channel < 2; channel += 1) {
      const data = buffer.getChannelData(channel);
      for (let i = 0; i < length; i += 1) {
        data[i] = (Math.random() * 2 - 1) * (1 - i / length) ** decay;
      }
    }
    return buffer;
  }

  makeNoise(seconds) {
    const rate = this.ctx.sampleRate;
    const buffer = this.ctx.createBuffer(1, Math.floor(rate * seconds), rate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < data.length; i += 1) data[i] = Math.random() * 2 - 1;
    return buffer;
  }

  // -- settings --------------------------------------------------------------
  configure(settings = {}) {
    if ('master_volume' in settings) this.volume = settings.master_volume;
    if ('effects' in settings) this.effects = settings.effects;
    if ('quill_sounds' in settings) this.quillSounds = settings.quill_sounds;
    if ('ambience' in settings) this.ambience = settings.ambience;
    this.apply();
  }

  setEnabled(enabled) {
    this.enabled = enabled;
    this.apply();
  }

  apply() {
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    this.master.gain.cancelScheduledValues(now);
    this.master.gain.linearRampToValueAtTime(this.enabled ? this.volume : 0, now + 0.3);
    if (this.ambience && !this.silenced && this.enabled) this.startDrone();
    else this.stopDrone();
  }

  setNight(rules) {
    if (rules?.tonality?.intervals) this.tonality = rules.tonality;
    this.silenced = Boolean(rules?.effects?.silence);
    this.quillSong = Boolean(rules?.effects?.quill_song);
    if (this.drone) {
      this.stopDrone(true);
    }
    this.apply();
  }

  /** Frequency of a scale degree in the night's mode. */
  note(degree, octave = 0) {
    const steps = this.tonality.intervals;
    const n = steps.length;
    const wrapped = ((degree % n) + n) % n;
    const extra = Math.floor(degree / n);
    const semitones = steps[wrapped] + 12 * (octave + extra);
    return this.tonality.root_hz * 2 ** (semitones / 12);
  }

  // -- primitives ------------------------------------------------------------
  osc({ type = 'sine', freq = 440, start = 0, dur = 1, attack = 0.01, gain = 0.2,
    glide = null, detune = 0, dest = null, vibrato = 0 } = {}) {
    const ctx = this.ctx;
    const t = ctx.currentTime + start;
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    o.detune.value = detune;
    if (glide) o.frequency.exponentialRampToValueAtTime(Math.max(20, glide), t + dur);
    if (vibrato) {
      const lfo = ctx.createOscillator();
      const depth = ctx.createGain();
      lfo.frequency.value = 5.5;
      depth.gain.value = vibrato;
      lfo.connect(depth).connect(o.frequency);
      lfo.start(t);
      lfo.stop(t + dur + 0.1);
    }
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(Math.max(0.0002, gain), t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(dest || this.bus);
    o.start(t);
    o.stop(t + dur + 0.05);
    return o;
  }

  noise({ start = 0, dur = 0.5, type = 'bandpass', freq = 1000, q = 1, gain = 0.2,
    attack = 0.01, sweep = null, dest = null } = {}) {
    const ctx = this.ctx;
    const t = ctx.currentTime + start;
    const src = ctx.createBufferSource();
    src.buffer = this.noiseBuffer;
    src.loop = true;
    const filter = ctx.createBiquadFilter();
    filter.type = type;
    filter.frequency.setValueAtTime(freq, t);
    filter.Q.value = q;
    if (sweep) filter.frequency.exponentialRampToValueAtTime(sweep, t + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(Math.max(0.0002, gain), t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(filter).connect(g).connect(dest || this.bus);
    src.start(t, Math.random() * 2);
    src.stop(t + dur + 0.05);
  }

  bell(freq, { start = 0, dur = 4, gain = 0.2 } = {}) {
    for (const [ratio, amp, life] of BELL_PARTIALS) {
      this.osc({ freq: freq * ratio, start, dur: dur * life, attack: 0.004, gain: gain * amp * 0.5 });
    }
  }

  pluck(freq, { start = 0, dur = 1.2, gain = 0.16 } = {}) {
    this.osc({ type: 'triangle', freq, start, dur, attack: 0.003, gain });
    this.osc({ type: 'sine', freq: freq * 2, start, dur: dur * 0.5, attack: 0.003, gain: gain * 0.3 });
  }

  pad(freqs, { start = 0, dur = 3, gain = 0.08, type = 'sawtooth', cutoff = 1400 } = {}) {
    const ctx = this.ctx;
    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.value = cutoff;
    filter.connect(this.bus);
    for (const freq of freqs) {
      for (const detune of [-7, 0, 7]) {
        this.osc({ type, freq, start, dur, attack: dur * 0.35, gain: gain / 3, detune, dest: filter });
      }
    }
  }

  crackle({ start = 0, dur = 1, count = 24, gain = 0.12 } = {}) {
    for (let i = 0; i < count; i += 1) {
      this.noise({ start: start + Math.random() * dur, dur: 0.02 + Math.random() * 0.03,
        type: 'highpass', freq: 1800 + Math.random() * 3000, gain: gain * Math.random() });
    }
  }

  // -- the repertoire ----------------------------------------------------------
  play(name, opts = {}) {
    if (!this.ctx || !this.enabled || !this.effects) return;
    if (this.ctx.state === 'suspended') this.ctx.resume();
    const fn = SOUNDS[name];
    if (fn) fn.call(this, opts);
  }

  /** A keystroke of the quill: a dry scratch, or a sung note on Unbound Tongue nights. */
  quill(char = '') {
    if (!this.ctx || !this.enabled || !this.quillSounds) return;
    if (this.quillSong && char.trim()) {
      const degree = (char.toLowerCase().charCodeAt(0) * 7) % 10;
      this.pluck(this.note(degree, 1), { gain: 0.06, dur: 0.9 });
      return;
    }
    this.noise({ dur: 0.035, type: 'highpass', freq: 3000 + Math.random() * 2500, gain: 0.025 });
  }

  // -- ambience ---------------------------------------------------------------
  startDrone() {
    if (!this.ctx || this.drone) return;
    const ctx = this.ctx;
    const now = ctx.currentTime;
    const root = this.tonality.root_hz / 2;
    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.value = 520;
    filter.Q.value = 2;
    const lfo = ctx.createOscillator();
    const lfoDepth = ctx.createGain();
    lfo.frequency.value = 0.045;
    lfoDepth.gain.value = 260;
    lfo.connect(lfoDepth).connect(filter.frequency);
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.09, now + 6);
    filter.connect(gain).connect(this.ambBus);
    const voices = [];
    for (const [ratio, type, level] of [[1, 'sawtooth', 0.3], [1.5, 'sawtooth', 0.18],
      [0.5, 'sine', 0.6], [2, 'triangle', 0.08]]) {
      for (const detune of [-5, 5]) {
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.type = type;
        o.frequency.value = root * ratio;
        o.detune.value = detune;
        g.gain.value = level;
        o.connect(g).connect(filter);
        o.start(now);
        voices.push(o);
      }
    }
    // a slow wind beneath the organ
    const wind = ctx.createBufferSource();
    wind.buffer = this.noiseBuffer;
    wind.loop = true;
    const windFilter = ctx.createBiquadFilter();
    windFilter.type = 'bandpass';
    windFilter.frequency.value = 420;
    windFilter.Q.value = 0.8;
    const windGain = ctx.createGain();
    windGain.gain.value = 0.05;
    const windLfo = ctx.createOscillator();
    const windDepth = ctx.createGain();
    windLfo.frequency.value = 0.07;
    windDepth.gain.value = 240;
    windLfo.connect(windDepth).connect(windFilter.frequency);
    wind.connect(windFilter).connect(windGain).connect(gain);
    wind.start(now);
    windLfo.start(now);
    lfo.start(now);
    this.ambBus.gain.cancelScheduledValues(now);
    this.ambBus.gain.linearRampToValueAtTime(1, now + 2);
    this.drone = { gain, voices: [...voices, wind, windLfo, lfo] };
    this.scheduleBell();
  }

  scheduleBell() {
    clearTimeout(this.bellTimer);
    this.bellTimer = setTimeout(() => {
      if (!this.drone || !this.enabled) return;
      const degree = [0, 2, 4, 7][Math.floor(Math.random() * 4)];
      this.bell(this.note(degree, Math.random() < 0.5 ? 0 : 1), { gain: 0.035, dur: 6 });
      this.scheduleBell();
    }, rnd(9000, 21000));
  }

  stopDrone(immediate = false) {
    clearTimeout(this.bellTimer);
    if (!this.drone || !this.ctx) return;
    const { gain, voices } = this.drone;
    const now = this.ctx.currentTime;
    const fade = immediate ? 0.4 : 2.5;
    gain.gain.cancelScheduledValues(now);
    gain.gain.setValueAtTime(Math.max(0.0001, gain.gain.value), now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + fade);
    for (const voice of voices) voice.stop(now + fade + 0.1);
    this.drone = null;
  }
}

// Every named sound. `this` is the Choir.
const SOUNDS = {
  swish() {
    this.noise({ dur: 0.42, freq: 500, sweep: 3200, q: 1.4, gain: 0.16 });
  },
  flip() {
    this.noise({ dur: 0.09, type: 'highpass', freq: 2400, gain: 0.12 });
    this.osc({ freq: 240, glide: 120, dur: 0.16, gain: 0.08 });
  },
  select() {
    this.bell(this.note(4, 1), { gain: 0.1, dur: 1.8 });
  },
  deselect() {
    this.osc({ type: 'triangle', freq: this.note(0), dur: 0.3, gain: 0.07 });
  },
  bind() {
    this.bell(this.note(0, -1), { gain: 0.32, dur: 7 });
    this.bell(this.note(4), { start: 0.25, gain: 0.14, dur: 5 });
    this.pad([this.note(0, -1), this.note(2, -1), this.note(4, -1)], { dur: 5, gain: 0.1 });
  },
  burn() {
    this.noise({ dur: 1.8, type: 'lowpass', freq: 900, gain: 0.14, attack: 0.2 });
    this.crackle({ dur: 1.8, count: 40, gain: 0.18 });
  },
  toll() {
    for (let i = 0; i < 3; i += 1) this.bell(this.note(0, -1), { start: i * 1.3, gain: 0.34, dur: 6 });
  },
  chord() {
    this.pad([0, 2, 4, 6].map((d) => this.note(d)), { dur: 4.5, gain: 0.12, type: 'triangle' });
    [0, 2, 4, 7, 9].forEach((d, i) => this.bell(this.note(d, 1), { start: 0.3 + i * 0.18, gain: 0.06, dur: 3 }));
  },
  seal() {
    this.osc({ freq: 110, glide: 48, dur: 0.32, gain: 0.22 });
    this.noise({ dur: 0.18, type: 'lowpass', freq: 500, gain: 0.12 });
    this.bell(this.note(4, 1), { start: 0.12, gain: 0.04, dur: 2 });
  },
  sigil() {
    const degree = Math.floor(Math.random() * 7);
    this.bell(this.note(degree, 1), { gain: 0.07, dur: 1.6 });
  },
  error() {
    this.osc({ type: 'square', freq: this.note(1, -1), dur: 0.35, gain: 0.05 });
    this.osc({ type: 'square', freq: this.note(0, -1), dur: 0.35, gain: 0.05 });
  },
  chains() {
    for (let i = 0; i < 6; i += 1) {
      this.noise({ start: i * 0.09, dur: 0.12, freq: 2600 + Math.random() * 1500, q: 9, gain: 0.2 });
      this.osc({ type: 'square', freq: 170 + Math.random() * 60, start: i * 0.09, dur: 0.08, gain: 0.03 });
    }
    this.osc({ freq: 70, glide: 40, start: 0.55, dur: 0.6, gain: 0.25 });
  },
  fizzle() {
    this.noise({ dur: 0.8, type: 'highpass', freq: 4200, sweep: 600, gain: 0.09 });
    this.crackle({ dur: 0.6, count: 10, gain: 0.08 });
  },
  eclipse() {
    this.pad([this.note(0, -2), this.note(4, -2)], { dur: 6, gain: 0.16, cutoff: 600 });
    [0, 4, 7, 11].forEach((d, i) => this.bell(this.note(d, 1), { start: 2 + i * 0.25, gain: 0.05, dur: 4 }));
  },
  heartbeat() {
    for (let i = 0; i < 4; i += 1) {
      this.osc({ freq: 62, glide: 40, start: i * 0.9, dur: 0.22, gain: 0.4 });
      this.osc({ freq: 55, glide: 38, start: i * 0.9 + 0.24, dur: 0.2, gain: 0.3 });
    }
    this.pad([this.note(0, -1), this.note(1, -1)], { dur: 4, gain: 0.06, cutoff: 500 });
  },
  thunder() {
    this.noise({ dur: 0.25, type: 'highpass', freq: 2000, gain: 0.3 });
    this.noise({ start: 0.1, dur: 3.5, type: 'lowpass', freq: 320, sweep: 90, gain: 0.5, attack: 0.08 });
    this.crackle({ dur: 0.6, count: 20, gain: 0.25 });
  },
  raven() {
    for (let i = 0; i < 6; i += 1) {
      this.noise({ start: i * 0.22, dur: 0.15, type: 'lowpass', freq: 700, gain: 0.16 });
    }
    for (const start of [0.4, 1.2]) {
      this.osc({ type: 'sawtooth', freq: 760, glide: 430, start, dur: 0.35, gain: 0.06 });
      this.noise({ start, dur: 0.32, freq: 1100, q: 4, gain: 0.06 });
    }
  },
  flutter() {
    for (let i = 0; i < 26; i += 1) {
      this.noise({ start: i * 0.07 + Math.random() * 0.04, dur: 0.05, type: 'highpass', freq: 1400, gain: 0.05 });
    }
  },
  wind() {
    this.noise({ dur: 4, freq: 300, sweep: 1100, q: 0.9, gain: 0.22, attack: 1.2 });
    this.noise({ start: 1.4, dur: 3, freq: 900, sweep: 260, q: 1.2, gain: 0.14, attack: 0.8 });
  },
  water() {
    this.noise({ dur: 3.5, type: 'lowpass', freq: 800, gain: 0.16, attack: 0.6 });
    for (let i = 0; i < 14; i += 1) {
      const f = rnd(260, 520);
      this.osc({ freq: f, glide: f * 2.4, start: Math.random() * 3, dur: 0.12, gain: 0.05 });
    }
  },
  fire() {
    this.noise({ dur: 3, type: 'lowpass', freq: 1300, gain: 0.18, attack: 0.3 });
    this.crackle({ dur: 3, count: 60, gain: 0.2 });
  },
  creak() {
    this.osc({ type: 'sawtooth', freq: 74, glide: 58, dur: 2.4, gain: 0.06, vibrato: 6, attack: 0.4 });
    this.noise({ dur: 2.4, freq: 300, q: 6, gain: 0.08, attack: 0.5 });
    this.bell(this.note(0, -1), { start: 1.6, gain: 0.05, dur: 4 });
  },
  sparkle() {
    for (let i = 0; i < 10; i += 1) {
      this.bell(this.note(Math.floor(Math.random() * 9), 2), { start: i * 0.13, gain: 0.04, dur: 1.4 });
    }
  },
  harp() {
    for (let i = 0; i < 10; i += 1) this.pluck(this.note(i), { start: i * 0.09, gain: 0.1 });
  },
  glass() {
    this.osc({ freq: this.note(4, 2), dur: 3, gain: 0.08, attack: 0.4, vibrato: 3 });
    this.osc({ freq: this.note(0, 2), dur: 3.4, gain: 0.06, attack: 0.6, vibrato: 2 });
    this.bell(this.note(7, 1), { start: 0.4, gain: 0.05, dur: 3 });
  },
  choir() {
    const ctx = this.ctx;
    const formant = ctx.createBiquadFilter();
    formant.type = 'bandpass';
    formant.frequency.value = 900;
    formant.Q.value = 1.6;
    formant.connect(this.bus);
    for (const d of [0, 2, 4, 7]) {
      for (const detune of [-9, 0, 9]) {
        this.osc({ type: 'sawtooth', freq: this.note(d), dur: 5, attack: 1.6, gain: 0.05,
          detune, dest: formant, vibrato: 2.5 });
      }
    }
  },
  glint() {
    this.osc({ freq: 1800, glide: 4200, dur: 0.4, gain: 0.05 });
    this.bell(this.note(4, 2), { start: 0.1, gain: 0.08, dur: 2.2 });
  },
  gallop() {
    for (let i = 0; i < 12; i += 1) {
      const start = Math.floor(i / 3) * 0.42 + (i % 3) * 0.1;
      this.noise({ start, dur: 0.06, type: 'lowpass', freq: 380, gain: 0.3 });
    }
    this.osc({ type: 'sawtooth', freq: this.note(0), glide: this.note(4, 1), dur: 1.6, gain: 0.04 });
  },
  chime() {
    this.bell(this.note(4, 1), { gain: 0.12, dur: 3.5 });
    this.bell(this.note(7, 1), { start: 0.5, gain: 0.08, dur: 3 });
  },
  organ() {
    for (const d of [0, 2, 4]) {
      for (const [harmonic, level] of [[1, 1], [2, 0.5], [3, 0.3], [4, 0.2], [6, 0.12], [8, 0.08]]) {
        this.osc({ freq: this.note(d, -1) * harmonic, dur: 4.5, attack: 0.25, gain: 0.05 * level });
      }
    }
  },
  fanfare() {
    [0, 2, 4, 7].forEach((d, i) => {
      this.osc({ type: 'sawtooth', freq: this.note(d), start: i * 0.2, dur: 1.4, gain: 0.07, attack: 0.04 });
      this.osc({ type: 'square', freq: this.note(d, -1), start: i * 0.2, dur: 1.4, gain: 0.025 });
    });
    this.bell(this.note(7, 1), { start: 0.8, gain: 0.1, dur: 4 });
  },
  alchemy() {
    this.osc({ freq: this.note(0, -1), glide: this.note(4), dur: 2, gain: 0.08, attack: 0.3 });
    this.osc({ freq: this.note(4, 1), glide: this.note(4), dur: 2, gain: 0.06, attack: 0.3 });
    this.bell(this.note(4), { start: 1.9, gain: 0.18, dur: 4 });
  },
  twin() {
    this.osc({ freq: this.note(0), dur: 3.2, attack: 0.5, gain: 0.08 });
    this.osc({ freq: this.note(0) * 1.503, dur: 3.2, attack: 0.5, gain: 0.07 });
    this.bell(this.note(4, 1), { start: 0.9, gain: 0.06, dur: 3 });
  },
  scales() {
    for (let i = 0; i < 4; i += 1) {
      this.bell(this.note(i % 2 ? 4 : 0, 1), { start: i * 0.55, gain: 0.08, dur: 1.6 });
    }
  },
  witching() {
    for (let i = 0; i < 12; i += 1) {
      const start = 2.6 * (1 - (1 - i / 12) ** 1.6);
      this.noise({ start, dur: 0.03, freq: 3400, q: 6, gain: 0.12 });
    }
    this.bell(this.note(0, -1), { start: 2.8, gain: 0.3, dur: 6 });
  },
  serpent() {
    this.noise({ dur: 3, type: 'highpass', freq: 5200, gain: 0.08, attack: 0.6 });
    this.pad([this.note(0, -1), this.note(4, -1), this.note(7, -1)], { dur: 5, gain: 0.12, cutoff: 900 });
    this.bell(this.note(0), { start: 2.6, gain: 0.16, dur: 5 });
  },
  ward() {
    this.noise({ dur: 1.5, freq: 2400, q: 12, gain: 0.08, attack: 0.2 });
    this.bell(this.note(4, 1), { gain: 0.1, dur: 2.5 });
  },
  discover() {
    [0, 2, 4, 7, 9, 11].forEach((d, i) => this.bell(this.note(d, 1), { start: i * 0.12, gain: 0.07, dur: 2.5 }));
    SOUNDS.organ.call(this);
  },
  page() {
    this.noise({ dur: 0.3, freq: 1200, sweep: 3400, q: 0.8, gain: 0.08 });
  },
};

export const SOUND_NAMES = Object.keys(SOUNDS);
