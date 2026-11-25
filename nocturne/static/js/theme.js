// Applies a night's edicts to the page: palette, effect classes and the omen line.

export const EFFECT_FLAGS = [
  'veil', 'lantern', 'silence', 'starfield', 'no_particles', 'mirror', 'fading', 'moths',
  'illusion', 'gilded', 'illuminate', 'bloom', 'echo', 'velocity', 'drift', 'tremor', 'scatter',
  'anchored', 'grid', 'scramble', 'chains', 'quill_song',
];

const DEFAULT_PALETTE = {
  accent: '#9b2a22', accent2: '#cdb7a0', glow: '#ff7a3d', ink: '#2a1210', sky: '#0d0709',
  parchment: '#e6d7bb',
};

export function applyTheme(rules, { isToday = true, settings = {} } = {}) {
  const root = document.documentElement;
  const palette = { ...DEFAULT_PALETTE, ...(rules?.aspect?.palette || {}) };
  for (const [key, value] of Object.entries(palette)) root.style.setProperty(`--${key}`, value);
  const effects = rules?.effects || {};
  for (const flag of EFFECT_FLAGS) {
    document.body.classList.toggle(`fx-${flag.replace('_', '-')}`, Boolean(effects[flag]));
  }
  document.body.classList.toggle('is-past', !isToday);
  document.body.classList.toggle('is-eclipsed', Boolean(rules?.aspect?.eclipsed));
  document.body.classList.toggle('veil-all', Boolean(settings.veil_all));
  document.body.classList.toggle('reduced-motion', Boolean(settings.reduced_motion));
  document.body.dataset.element = rules?.aspect?.element || 'none';
  document.body.dataset.particle = rules?.aspect?.particle || 'motes';
}
