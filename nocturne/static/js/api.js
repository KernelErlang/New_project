// The only door between the page and the local Codex server.
// Every request carries the per-launch token embedded in the page.

const token = document.querySelector('meta[name="nocturne-token"]')?.content || '';
const svgCache = new Map();

export class CodexError extends Error {
  constructor(message, status, code, data) {
    super(message);
    this.status = status;
    this.code = code;
    this.data = data;
  }
}

async function call(method, path, body) {
  const options = { method, headers: { 'X-Nocturne-Token': token } };
  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(path, options);
  } catch (err) {
    throw new CodexError('The Codex is not answering. Is its window still open?', 0, 'offline');
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new CodexError(data.message || response.statusText, response.status, data.error, data);
  }
  return data;
}

export const api = {
  state: (day) => call('GET', `/api/state${day ? `?day=${encodeURIComponent(day)}` : ''}`),
  draw: () => call('POST', '/api/ritual/draw', {}),
  keep: (keep) => call('POST', '/api/ritual/keep', { keep }),
  createNote: (note) => call('POST', '/api/notes', note),
  updateNote: (id, note) => call('PUT', `/api/notes/${id}`, note),
  moveNote: (id, x, y) => call('PATCH', `/api/notes/${id}`, { x, y }),
  deleteNote: (id) => call('DELETE', `/api/notes/${id}`),
  divine: (note) => call('POST', '/api/divine', note),
  codex: () => call('GET', '/api/codex'),
  calendar: () => call('GET', '/api/calendar'),
  settings: () => call('GET', '/api/settings'),
  saveSettings: (changes) => call('PUT', '/api/settings', changes),
  shutdown: () => call('POST', '/api/shutdown', {}),

  async download(format) {
    const response = await fetch(`/api/export?format=${format}`, {
      headers: { 'X-Nocturne-Token': token },
    });
    if (!response.ok) throw new CodexError('The export failed.', response.status, 'export');
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const name = /filename="([^"]+)"/.exec(disposition)?.[1] || `nocturne-codex.${format}`;
    const url = URL.createObjectURL(blob);
    const link = Object.assign(document.createElement('a'), { href: url, download: name });
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  },

  async svg(url) {
    if (!svgCache.has(url)) {
      svgCache.set(url, fetch(url).then((r) => (r.ok ? r.text() : '')).catch(() => ''));
    }
    return svgCache.get(url);
  },
};
