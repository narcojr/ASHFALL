// Save data and level layouts. When the Python backend is running it is used for
// saves; otherwise the game reads the static JSON in api/ and stores progress in
// localStorage, so the same build runs on any static host.
(function () {
  'use strict';

  const KEY = 'ashfall.save.v1';
  const LEVELS = 3;
  const DEFAULT_SETTINGS = { master: 80, music: 60, sfx: 80, music_on: true, sfx_on: true, shake: true, fps: false, difficulty: 'normal' };
  const SETTING_RULES = {
    master: ['int', 0, 100], music: ['int', 0, 100], sfx: ['int', 0, 100],
    music_on: ['bool'], sfx_on: ['bool'], shake: ['bool'], fps: ['bool'],
    difficulty: ['choice', ['easy', 'normal', 'hard']],
  };

  let remote = false;
  const levelCache = {};

  const sum = (value, fallback) => (Number.isFinite(value) ? value : fallback);
  const clamp = (value, lo, hi) => Math.max(lo, Math.min(hi, value));

  function defaultSave() {
    return { unlocked: 1, best: {}, deaths: 0, settings: Object.assign({}, DEFAULT_SETTINGS) };
  }

  function cleanSettings(raw, current) {
    const out = Object.assign({}, current || DEFAULT_SETTINGS);
    if (!raw || typeof raw !== 'object') return out;
    for (const [key, rule] of Object.entries(SETTING_RULES)) {
      const value = raw[key];
      if (rule[0] === 'int' && Number.isInteger(value)) out[key] = clamp(value, rule[1], rule[2]);
      else if (rule[0] === 'bool' && typeof value === 'boolean') out[key] = value;
      else if (rule[0] === 'choice' && rule[1].includes(value)) out[key] = value;
    }
    return out;
  }

  function normalize(raw) {
    const save = defaultSave();
    if (!raw || typeof raw !== 'object') return save;
    if (Number.isInteger(raw.unlocked)) save.unlocked = clamp(raw.unlocked, 1, LEVELS);
    if (raw.best && typeof raw.best === 'object') {
      for (let level = 1; level <= LEVELS; level++) {
        const entry = raw.best[String(level)];
        if (!entry || typeof entry !== 'object') continue;
        const time = Number(entry.time);
        if (!Number.isFinite(time) || time <= 0) continue;
        save.best[String(level)] = {
          time: Math.round(time * 10) / 10,
          cores: Math.max(0, Math.round(sum(Number(entry.cores), 0))),
          coins: Math.max(0, Math.round(sum(Number(entry.coins), 0))),
        };
      }
    }
    if (Number.isInteger(raw.deaths)) save.deaths = Math.max(0, raw.deaths);
    save.settings = cleanSettings(raw.settings);
    return save;
  }

  function readLocal() {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? normalize(JSON.parse(raw)) : null;
    } catch (err) {
      return null;
    }
  }

  function writeLocal(save) {
    try { localStorage.setItem(KEY, JSON.stringify(save)); } catch (err) { /* private mode */ }
  }

  async function fetchJson(path, body) {
    const options = body === undefined
      ? { cache: 'no-store' }
      : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
    const response = await fetch(path, options);
    if (!response.ok) throw new Error(path + ' ' + response.status);
    return response.json();
  }

  async function init() {
    remote = false;
    try {
      const health = await fetchJson('api/health');
      remote = !!(health && health.ok);
    } catch (err) {
      remote = false;
    }
    return remote;
  }

  async function loadConfig() {
    if (remote) {
      try { return await fetchJson('api/config'); } catch (err) { /* fall through to static */ }
    }
    return fetchJson('api/config.json');
  }

  async function loadSave() {
    const local = readLocal();
    if (remote) {
      try {
        const save = normalize(await fetchJson('api/save'));
        writeLocal(save);
        return save;
      } catch (err) { /* offline save */ }
    }
    return local || defaultSave();
  }

  async function getLevel(number) {
    if (!levelCache[number]) {
      const job = remote
        ? fetchJson('api/level/' + number).catch(() => fetchJson('api/level/' + number + '.json'))
        : fetchJson('api/level/' + number + '.json');
      levelCache[number] = await job;
    }
    return JSON.parse(JSON.stringify(levelCache[number]));
  }

  async function persist(save, path, body) {
    save = normalize(save);
    writeLocal(save);
    if (remote) {
      try {
        const server = normalize(await fetchJson(path, body === undefined ? save : body));
        writeLocal(server);
        return server;
      } catch (err) { /* keep the local copy */ }
    }
    return save;
  }

  async function saveSettings(settings) {
    const save = readLocal() || defaultSave();
    save.settings = cleanSettings(settings, save.settings);
    writeLocal(save);
    if (remote) {
      try { await fetchJson('api/settings', save.settings); } catch (err) { /* local copy is enough */ }
    }
    return save.settings;
  }

  async function complete(level, time, cores, coins) {
    const save = readLocal() || defaultSave();
    const result = {
      time: Math.max(0, Math.round(time * 10) / 10),
      cores: Math.max(0, Math.round(cores)),
      coins: Math.max(0, Math.round(coins)),
    };
    const best = save.best[String(level)];
    if (!best || result.time < best.time) save.best[String(level)] = result;
    save.unlocked = Math.max(save.unlocked, Math.min(LEVELS, level + 1));
    return persist(save, 'api/complete', Object.assign({ level }, result));
  }

  async function death() {
    const save = readLocal() || defaultSave();
    save.deaths += 1;
    return persist(save, 'api/death', {});
  }

  async function unlockAll() {
    const save = readLocal() || defaultSave();
    save.unlocked = LEVELS;
    return persist(save, 'api/unlock_all', {});
  }

  async function reset() {
    const save = readLocal() || defaultSave();
    const fresh = defaultSave();
    fresh.settings = save.settings;
    return persist(fresh, 'api/reset', {});
  }

  window.AshStore = {
    get remote() { return remote; },
    init, loadConfig, loadSave, getLevel, saveSettings, complete, death, unlockAll, reset,
    defaultSave, readLocal, writeLocal, cleanSettings,
  };
})();
