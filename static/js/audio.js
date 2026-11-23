// Sound effects and music, generated with the Web Audio API (no audio files).
// The audio context starts on the first click or key press because browsers block it before that.
(function () {
  'use strict';
  let ctx = null, master, musicBus, sfxBus, noiseBuf;
  const S = { master: 0.8, music: 0.6, sfx: 0.8, musicOn: true, sfxOn: true };
  let theme = null, timer = null, nextTime = 0, step = 0, wantTheme = null;

  function init() {
    if (ctx) return true;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return false;
    try { ctx = new AC(); } catch (e) { ctx = null; return false; }
    master = ctx.createGain(); musicBus = ctx.createGain(); sfxBus = ctx.createGain();
    musicBus.connect(master); sfxBus.connect(master); master.connect(ctx.destination);
    noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
    const d = noiseBuf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    applyVolumes(true);
    return true;
  }
  function resume() {
    if (!init()) return;
    if (ctx.state === 'suspended') ctx.resume().catch(() => {});
    if (wantTheme && !timer) startMusic(wantTheme);
  }
  function applyVolumes(instant) {
    if (!ctx) return;
    const t = ctx.currentTime, tc = instant ? 0.001 : 0.05;
    master.gain.setTargetAtTime(S.master, t, tc);
    musicBus.gain.setTargetAtTime(S.musicOn ? S.music * 0.5 : 0, t, tc);
    sfxBus.gain.setTargetAtTime(S.sfxOn ? S.sfx : 0, t, tc);
  }
  function configure(o) { Object.assign(S, o); applyVolumes(); }
  function tone(freq, dur, type, vol, slideTo, when, bus) {
    if (!ctx) return;
    const t = (when || ctx.currentTime), o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type || 'square';
    o.frequency.setValueAtTime(freq, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(Math.max(1, slideTo), t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(Math.max(0.0002, vol), t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(bus || sfxBus);
    o.start(t); o.stop(t + dur + 0.05);
  }
  function noise(dur, freq, vol, kind, when, bus, slideTo) {
    if (!ctx) return;
    const t = (when || ctx.currentTime), s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain();
    s.buffer = noiseBuf; f.type = kind || 'lowpass';
    f.frequency.setValueAtTime(freq, t);
    if (slideTo) f.frequency.exponentialRampToValueAtTime(Math.max(20, slideTo), t + dur);
    g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    s.connect(f); f.connect(g); g.connect(bus || sfxBus);
    s.start(t, Math.random() * 0.5); s.stop(t + dur + 0.05);
  }
  const seq = (notes, gap, type, vol) => notes.forEach((n, i) => tone(n, 0.16, type || 'square', vol || 0.12, null, ctx.currentTime + i * gap));

  const SFX = {
    click: () => tone(520, 0.06, 'square', 0.08, 700),
    back: () => tone(420, 0.07, 'square', 0.08, 260),
    jump: () => tone(280, 0.14, 'square', 0.1, 620),
    swing: () => noise(0.12, 2400, 0.18, 'bandpass', 0, null, 600),
    hit: () => { noise(0.12, 900, 0.3, 'lowpass'); tone(160, 0.1, 'sawtooth', 0.12, 70); },
    hurt: () => { tone(260, 0.28, 'sawtooth', 0.16, 70); noise(0.15, 600, 0.2, 'lowpass'); },
    coin: () => { tone(988, 0.07, 'square', 0.09); tone(1319, 0.14, 'square', 0.09, null, ctx.currentTime + 0.06); },
    core: () => seq([660, 880, 1100, 1320], 0.05, 'triangle', 0.14),
    book: () => seq([523, 659, 784], 0.07, 'triangle', 0.13),
    evolve: () => seq([392, 494, 587, 784, 988, 1175], 0.09, 'square', 0.12),
    chest: () => { noise(0.2, 700, 0.2, 'lowpass'); tone(330, 0.2, 'triangle', 0.14, 660); },
    locked: () => tone(140, 0.18, 'square', 0.12, 110),
    weapon: () => seq([330, 440, 660], 0.06, 'sawtooth', 0.1),
    enemyDie: () => { noise(0.3, 1200, 0.25, 'lowpass', 0, null, 200); tone(220, 0.3, 'square', 0.1, 60); },
    shoot: () => tone(520, 0.12, 'triangle', 0.1, 190),
    cast: () => tone(330, 0.3, 'sine', 0.12, 900),
    spike: () => noise(0.12, 3000, 0.2, 'highpass'),
    fire: () => noise(0.2, 1800, 0.12, 'bandpass', 0, null, 500),
    icicleWarn: () => tone(2400, 0.1, 'sine', 0.05, 2800),
    icicleBreak: () => { noise(0.25, 5000, 0.3, 'highpass'); tone(1800, 0.15, 'triangle', 0.08, 600); },
    slam: () => { noise(0.45, 400, 0.45, 'lowpass', 0, null, 80); tone(70, 0.4, 'sine', 0.3, 35); },
    roar: () => { tone(110, 0.9, 'sawtooth', 0.2, 45); noise(0.7, 500, 0.25, 'lowpass', 0, null, 120); },
    charge: () => tone(90, 0.5, 'sawtooth', 0.14, 240),
    dash: () => { noise(0.18, 3500, 0.2, 'bandpass', 0, null, 500); tone(300, 0.12, 'triangle', 0.07, 700); },
    win: () => seq([523, 659, 784, 1047, 784, 1047, 1319], 0.12, 'square', 0.12),
    lose: () => seq([392, 330, 262, 196, 147], 0.18, 'sawtooth', 0.12),
  };
  function sfx(name) {
    if (!ctx || ctx.state !== 'running' || !S.sfxOn || !SFX[name]) return;
    try { SFX[name](); } catch (e) { /* never let audio break the game */ }
  }
  const mtof = m => 440 * Math.pow(2, (m - 69) / 12);
  const CHORDS = [[0, 3, 7], [-4, 0, 3], [3, 7, 10], [-2, 2, 5]];   // i  VI  III  VII
  const THEMES = {
    menu:   { bpm: 64, root: 57, arp: [0, 2, 1, 2, 0, 2, 1, 2], wave: 'sine',     bass: 'sine',     drums: false, arpVol: 0.07, padVol: 0.07 },
    forest: { bpm: 76, root: 57, arp: [0, 1, 2, 1, 2, 1, 0, 1], wave: 'triangle', bass: 'sine',     drums: false, arpVol: 0.08, padVol: 0.06 },
    ruins:  { bpm: 92, root: 54, arp: [0, 2, 1, 2, 2, 1, 2, 0], wave: 'triangle', bass: 'sawtooth', drums: false, arpVol: 0.08, padVol: 0.06 },
    night:  { bpm: 84, root: 52, arp: [0, 1, 2, 1, 0, 2, 1, 2], wave: 'square',   bass: 'sawtooth', drums: false, arpVol: 0.05, padVol: 0.07 },
    boss:   { bpm: 140, root: 50, arp: [0, 2, 1, 2, 2, 1, 2, 1], wave: 'sawtooth', bass: 'sawtooth', drums: true,  arpVol: 0.05, padVol: 0.07 },
  };
  function scheduleStep(th, t, i) {
    const barStep = i % 8, bar = Math.floor(i / 8) % CHORDS.length, ch = CHORDS[bar];
    const sec = 60 / th.bpm / 2;
    if (barStep === 0) {   // pad
      ch.forEach(n => tone(mtof(th.root + n + 12), sec * 8, 'triangle', th.padVol, null, t, musicBus));
    }
    if (barStep % 4 === 0 || (th.drums && barStep % 2 === 0)) tone(mtof(th.root + ch[0] - 12), sec * 1.8, th.bass, th.drums ? 0.16 : 0.13, null, t, musicBus);
    const a = ch[th.arp[barStep] % 3] + 12 + (barStep === 7 ? 12 : 0);
    if (!(th === THEMES.menu && barStep % 2)) tone(mtof(th.root + a), sec * 0.9, th.wave, th.arpVol, null, t, musicBus);
    if (th.drums) {
      if (barStep % 4 === 0) tone(150, 0.18, 'sine', 0.35, 40, t, musicBus);
      if (barStep % 4 === 2) noise(0.12, 1800, 0.18, 'bandpass', t, musicBus);
      if (barStep % 2 === 1) noise(0.04, 7000, 0.07, 'highpass', t, musicBus);
    }
  }
  function pump() {
    if (!ctx || !theme) return;
    const sec = 60 / theme.bpm / 2;
    if (nextTime < ctx.currentTime) nextTime = ctx.currentTime + 0.05;
    while (nextTime < ctx.currentTime + 0.3) {
      scheduleStep(theme, nextTime, step++);
      nextTime += sec;
    }
  }
  function startMusic(name) {
    wantTheme = name;
    if (!THEMES[name]) return;
    if (!ctx || ctx.state !== 'running') return;        // starts on resume()
    if (theme === THEMES[name] && timer) return;
    theme = THEMES[name]; step = 0; nextTime = ctx.currentTime + 0.1;
    if (!timer) timer = setInterval(pump, 60);
    pump();
  }
  function stopMusic() {
    wantTheme = null; theme = null;
    if (timer) { clearInterval(timer); timer = null; }
  }

  window.GameAudio = { resume, configure, sfx, startMusic, stopMusic, get ready() { return !!ctx && ctx.state === 'running'; } };
})();
