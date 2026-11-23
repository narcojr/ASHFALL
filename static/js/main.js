// Menus, game flow and the main loop. Level data and saves come from the Python
// backend when it is running, and from static JSON + localStorage otherwise.
(function () {
  'use strict';
  const { W, H, STEP, input } = window.Ash;
  const Ash = window.Ash;
  const Audio = window.GameAudio;
  const Store = window.AshStore;
  const $ = id => document.getElementById(id);
  const stage = $('stage'), canvas = $('game'), g = canvas.getContext('2d');
  const isTouch = (window.matchMedia && matchMedia('(pointer: coarse)').matches) || navigator.maxTouchPoints > 0;
  Ash.isTouch = isTouch;
  if (isTouch) stage.classList.add('touch');

  let config = null, save = null;
  let state = 'loading';        // loading, menu, playing, paused, over, complete, victory
  let screen = null;
  let history = [];
  let world = null, run = null;
  let menuTime = 0, fps = 0, fpsTime = 0, fpsFrames = 0, ready = false;

  // ---- loading and transitions ----
  function setLoading(share) {
    const fill = $('load-fill'), label = $('load-label');
    if (fill) fill.style.width = Math.round(Math.max(0, Math.min(1, share)) * 100) + '%';
    if (label) label.textContent = share >= 1 ? 'READY' : 'LOADING ' + Math.round(share * 100) + '%';
  }

  function fade(on) {
    const el = $('fade');
    if (el) el.classList.toggle('on', on);
  }

  let settingsTimer = null;
  function saveSettings() {
    clearTimeout(settingsTimer);
    settingsTimer = setTimeout(() => Store.saveSettings(save.settings), 250);
  }

  // ---- screen size ----
  function resize() {
    const width = stage.clientWidth, dpr = Math.min(window.devicePixelRatio || 1, 2);
    stage.style.setProperty('--u', (width / W).toFixed(4));
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(width * dpr * H / W);
    g.setTransform(canvas.width / W, 0, 0, canvas.height / H, 0, 0);
  }
  window.addEventListener('resize', resize);

  // ---- screens ----
  const SCREENS = ['loading', 'error', 'menu', 'levels', 'settings', 'pause', 'over', 'complete', 'victory', 'exit'];

  function show(name) {
    screen = name;
    SCREENS.forEach(s => $('scr-' + s).classList.toggle('hidden', s !== name));
    $('btn-pause').classList.toggle('hidden', state !== 'playing');
    $('touch').classList.toggle('hidden', !(state === 'playing' && isTouch));
    if (name) {
      const first = $('scr-' + name).querySelector('.btn:not(.locked), button');
      if (first) first.focus({ preventScroll: true });
    } else if (document.activeElement) document.activeElement.blur();
  }

  function goTo(name) { history.push(screen); show(name); Audio.sfx('click'); }

  function goBack() {
    Audio.sfx('back');
    const previous = history.pop() || 'menu';
    if (previous === 'pause') state = 'paused';
    show(previous);
  }

  // ---- settings ----
  function applyAudio() {
    const s = save.settings;
    Audio.configure({ master: s.master / 100, music: s.music / 100, sfx: s.sfx / 100, musicOn: s.music_on, sfxOn: s.sfx_on });
  }

  function showSettings() {
    const s = save.settings;
    for (const key of ['master', 'music', 'sfx']) {
      $('set-' + key).value = s[key];
      $('val-' + key).textContent = s[key];
    }
    for (const key of ['music_on', 'sfx_on', 'shake', 'fps']) $('tg-' + key).classList.toggle('on', !!s[key]);
    document.querySelectorAll('#seg-difficulty button').forEach(b => b.classList.toggle('on', b.dataset.v === s.difficulty));
  }

  function bindSettings() {
    for (const key of ['master', 'music', 'sfx']) {
      $('set-' + key).addEventListener('input', e => {
        save.settings[key] = +e.target.value;
        $('val-' + key).textContent = e.target.value;
        applyAudio();
        saveSettings();
      });
      $('set-' + key).addEventListener('change', () => Audio.sfx('coin'));
    }
    for (const key of ['music_on', 'sfx_on', 'shake', 'fps']) {
      $('tg-' + key).addEventListener('click', () => {
        save.settings[key] = !save.settings[key];
        showSettings();
        applyAudio();
        saveSettings();
        Audio.sfx('click');
      });
    }
    document.querySelectorAll('#seg-difficulty button').forEach(b => b.addEventListener('click', () => {
      save.settings.difficulty = b.dataset.v;
      showSettings();
      saveSettings();
      Audio.sfx('click');
    }));
  }

  // ---- level list ----
  const formatTime = seconds => { const s = Math.round(seconds); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };

  function buildLevelList() {
    const list = $('level-list');
    list.innerHTML = '';
    for (const level of config.levels) {
      const locked = level.id > save.unlocked, best = save.best[String(level.id)];
      const button = document.createElement('button');
      button.className = 'btn' + (locked ? ' locked' : '');
      button.dataset.act = 'startlevel';
      button.dataset.level = level.id;
      const note = locked ? 'LOCKED' : best ? 'BEST ' + formatTime(best.time) : level.tagline.toUpperCase();
      button.innerHTML = `<span>LEVEL ${level.id} ${level.name.toUpperCase()}<small>${note}</small></span>`;
      list.appendChild(button);
    }
  }

  // ---- game flow ----
  const MUSIC = { forest: 'forest', ruins: 'ruins', night: 'night' };

  function playSceneMusic() {
    if (state === 'menu') Audio.startMusic('menu');
    else if (world) Audio.startMusic(world.arenaLocked ? 'boss' : MUSIC[world.theme] || 'forest');
  }

  async function startLevel(number, options) {
    options = options || {};
    fade(true);
    try {
      const layout = await Store.getLevel(number);
      let player;
      if (options.carry && run && run.carried) player = run.carried;
      else if (options.saved) player = Ash.createPlayer(layout.start.x, options.saved.cores, options.saved.weapon, options.saved.coins);
      else player = Ash.createPlayer(layout.start.x, layout.start.cores, config.default_weapon, 0);
      run = { level: number, saved: Ash.savePlayer(player), carried: null };
      world = new Ash.World(layout, { player, settings: save.settings });
      world.onBoss = () => Audio.startMusic('boss');
      Object.keys(input).forEach(k => { input[k] = false; });
      state = 'playing';
      history = [];
      show(null);
      Audio.sfx('click');
      playSceneMusic();
      requestAnimationFrame(() => fade(false));
    } catch (err) {
      console.error(err);
      fade(false);
      state = 'loading';
      show('error');
    }
  }

  function toMenu() {
    fade(true);
    setTimeout(() => {
      state = 'menu'; world = null; history = []; show('menu');
      Audio.startMusic('menu');
      fade(false);
    }, 150);
  }

  function pauseGame() {
    if (state !== 'playing') return;
    state = 'paused';
    Object.keys(input).forEach(k => { input[k] = false; });
    $('pause-stats').innerHTML = `LEVEL ${run.level} ${config.levels[run.level - 1].name.toUpperCase()}<br>` +
      `CORES ${world.player.cores}  KILLS ${world.kills}  TIME ${formatTime(world.time / 1000)}`;
    show('pause');
    Audio.sfx('click');
  }

  function resumeGame() { if (state === 'paused') { state = 'playing'; show(null); Audio.sfx('click'); } }

  async function finishRun(result) {
    const p = world.player, seconds = world.time / 1000, minutes = formatTime(seconds);
    if (result === 'dead') {
      state = 'over';
      $('over-stats').innerHTML = `LEVEL ${run.level} ${config.levels[run.level - 1].name.toUpperCase()}<br>CORES ${p.cores}  KILLS ${world.kills}<br>TIME ${minutes}`;
      show('over');
      Store.death().then(s => { save.deaths = s.deaths; }).catch(() => {});
      Audio.stopMusic();
      return;
    }
    const last = run.level >= config.levels.length;
    const before = save.best[String(run.level)];
    const newBest = !before || seconds < before.time;
    const bestLine = newBest ? '<br><span class="best">NEW BEST TIME</span>' : '';
    state = last ? 'victory' : 'complete';
    run.carried = p;
    $(last ? 'victory-stats' : 'complete-stats').innerHTML =
      `TIME ${minutes}${bestLine}<br>CORES ${p.cores}  COINS ${p.coins}<br>ENEMIES DEFEATED ${world.kills}`;
    show(last ? 'victory' : 'complete');
    Audio.sfx('win');
    Audio.stopMusic();
    try {
      const updated = await Store.complete(run.level, seconds, p.cores, p.coins);
      save.unlocked = updated.unlocked;
      save.best = updated.best;
    } catch (err) { console.error(err); }
  }

  // ---- buttons ----
  const actions = {
    play() { startLevel(1); },
    levels() { buildLevelList(); goTo('levels'); },
    settings() { showSettings(); goTo('settings'); },
    exit() { goTo('exit'); setTimeout(() => { try { window.close(); } catch (e) { /* the tab stays open */ } }, 50); },
    back: goBack,
    startlevel(el) {
      const number = +el.dataset.level;
      if (number > save.unlocked) {
        el.classList.remove('shake');
        void el.offsetWidth;
        el.classList.add('shake');
        Audio.sfx('locked');
        return;
      }
      startLevel(number);
    },
    pause: pauseGame,
    resume: resumeGame,
    restart() { startLevel(run.level, { saved: run.saved }); },
    retry() { startLevel(run.level, { saved: run.saved }); },
    next() { startLevel(run.level + 1, { carry: true }); },
    menu() { Audio.sfx('click'); toMenu(); },
    fullscreen() {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (stage.requestFullscreen) stage.requestFullscreen();
    },
    async 'unlock-all'() {
      save = Object.assign(save, await Store.unlockAll()); Audio.sfx('weapon'); showSettings();
    },
    async reset() {
      if (!confirm('Reset saved progress (unlocked levels and best times)?')) return;
      const fresh = await Store.reset();
      save.unlocked = fresh.unlocked; save.best = fresh.best; save.deaths = 0;
      Audio.sfx('lose'); showSettings();
    },
    'retry-load'() { init(); },
  };

  document.addEventListener('click', e => {
    Audio.resume();
    const el = e.target.closest('[data-act]');
    if (!el || !actions[el.dataset.act]) return;
    actions[el.dataset.act](el);
    if (el.id === 'btn-pause') el.blur();
  });

  // ---- keyboard and touch ----
  const KEYS = {
    KeyA: 'left', ArrowLeft: 'left', KeyD: 'right', ArrowRight: 'right',
    Space: 'jump', KeyW: 'jump', ArrowUp: 'jump', KeyJ: 'attack', KeyK: 'attack', Enter: 'attack',
    ShiftLeft: 'dash', ShiftRight: 'dash', KeyL: 'dash',
  };

  window.addEventListener('keydown', e => {
    Audio.resume();
    if (state === 'playing') {
      const action = KEYS[e.code];
      if (action) { input[action] = true; e.preventDefault(); return; }
      if (e.code === 'KeyE' && !e.repeat) input.interact = true;
      else if (e.code === 'Escape' || e.code === 'KeyP') { e.preventDefault(); pauseGame(); }
      return;
    }
    if (state === 'paused' && screen === 'pause' && (e.code === 'Escape' || e.code === 'KeyP')) { e.preventDefault(); resumeGame(); return; }
    if (e.code === 'Escape' && ['levels', 'settings', 'exit'].includes(screen)) { e.preventDefault(); goBack(); return; }
    if (screen && (e.code === 'ArrowDown' || e.code === 'ArrowUp')) {         // move between menu buttons
      const items = [...$('scr-' + screen).querySelectorAll('button')].filter(b => !b.disabled && b.offsetParent !== null);
      if (!items.length) return;
      e.preventDefault();
      let i = items.indexOf(document.activeElement);
      i = e.code === 'ArrowDown' ? (i + 1) % items.length : (i - 1 + items.length) % items.length;
      items[i].focus();
      Audio.sfx('click');
    }
  });

  window.addEventListener('keyup', e => { const action = KEYS[e.code]; if (action) input[action] = false; });
  window.addEventListener('blur', () => { Object.keys(input).forEach(k => { input[k] = false; }); pauseGame(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden) pauseGame(); });

  document.querySelectorAll('#touch button').forEach(button => {
    const action = button.dataset.k;
    const set = value => e => { e.preventDefault(); Audio.resume(); input[action] = value; button.classList.toggle('down', value); };
    button.addEventListener('pointerdown', set(true));
    ['pointerup', 'pointercancel', 'pointerleave'].forEach(type => button.addEventListener(type, set(false)));
  });
  stage.addEventListener('contextmenu', e => e.preventDefault());

  // ---- main loop ----
  let lastTime = 0, accumulator = 0;

  function frame(now) {
    const dt = Math.min(100, now - lastTime || STEP);
    lastTime = now;
    fpsTime += dt; fpsFrames++;
    if (fpsTime >= 500) { fps = Math.round(fpsFrames * 1000 / fpsTime); fpsTime = 0; fpsFrames = 0; }

    if (state === 'playing' && world) {
      accumulator += dt;
      let steps = 0;
      while (accumulator >= STEP && steps < 6) {
        world.update(STEP);
        accumulator -= STEP;
        steps++;
        if (world.result) break;
      }
      if (steps === 6) accumulator = 0;
      if (world.result && state === 'playing') finishRun(world.result);
    } else accumulator = 0;

    if (world && state !== 'menu' && state !== 'loading') {
      world.draw(g);
      Ash.drawHud(g, world, { fps: save.settings.fps ? fps : 0 });
    } else if (ready) {
      menuTime += dt;
      Ash.drawMenuBackdrop(g, menuTime);
    }
    requestAnimationFrame(frame);
  }

  // ---- start ----
  async function init() {
    state = 'loading';
    fade(false);
    setLoading(0);
    show('loading');
    try {
      await Store.init();
      [config, save] = await Promise.all([Store.loadConfig(), Store.loadSave()]);
      Ash.setConfig(config);
      await Ash.sprites.load(config.art, (done, total) => setLoading(total ? done / total : 1));
    } catch (err) {
      console.error(err);
      show('error');
      return;
    }
    setLoading(1);
    ready = true;
    applyAudio();
    state = 'menu';
    show('menu');
    Audio.startMusic('menu');        // the context starts on the first click or key press
  }

  bindSettings();
  resize();
  requestAnimationFrame(frame);
  init();

  // used by the automated tests
  window.__ashfall = {
    get world() { return world; }, get state() { return state; }, input, startLevel,
    pause: pauseGame, resume: resumeGame, restart: actions.restart, retry: actions.retry,
    get save() { return save; }, get config() { return config; }, store: Store,
  };
})();
