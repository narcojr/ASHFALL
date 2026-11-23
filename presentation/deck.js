(function () {
  'use strict';
  const D = window.DECK, Ash = window.Ash, S = Ash.sprites, CFG = D.cfg, ART = CFG.art;
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  const deck = $('#deck'), STEP = 1000 / 60;
  const clone = o => JSON.parse(JSON.stringify(o));

  // ---- size, images ----
  const resize = () => deck.style.setProperty('--u', (deck.clientWidth / 960).toFixed(4));
  window.addEventListener('resize', resize);
  resize();
  $$('[data-img]').forEach(el => { el.src = D.images[el.dataset.img]; });
  const bg = $('#bg').getContext('2d');

  // ---- small drawing helpers ----
  const HERO_ROWS = { idle: 0, run: 1, jump: 2, dash: 3, attack: 4, hurt: 5, death: 6 };
  const FOE_ROWS = { idle: 0, walk: 1, attack: 2, hurt: 3, death: 4 };
  const HERO_BOX = [24, 26, 78, 98];          // the part of the hero cell that holds the character
  const FOE_BOX = { 1: [22, 26, 82, 98], boss: [26, 28, 128, 142] };

  function canvasFor(w, h, scale) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    c.style.width = (w * scale / 16) + 'em';
    c.style.height = (h * scale / 16) + 'em';
    return c;
  }
  const frameIndex = (t, fps, n, loop) => { const i = Math.floor(t / 1000 * fps); return loop ? i % n : Math.min(n - 1, i); };

  // animations that run only while their slide is visible
  const live = [];
  function addLive(slide, fn) { live.push({ slide, fn }); }

  // ---- slide 3: one design, three pixel sizes ----
  $('#tiers').innerHTML = [1, 2, 3].map(t => `<div class="box card grow"><h3>LEVEL ${t}</h3>
      <div class="stat">ART PIXEL = <b>${ART.tiers[t].pixel} PX</b><br>HERO CELL <b>${126 / ART.tiers[t].pixel} X ${126 / ART.tiers[t].pixel}</b> PX</div><div id="tier${t}"></div></div>`).join('');
  [1, 2, 3].forEach(t => {
    const c = canvasFor(300, 190, 1.05);
    $('#tier' + t).appendChild(c);
    const g = c.getContext('2d');
    addLive(2, time => {
      g.imageSmoothingEnabled = false;
      Ash.drawSky(g);
      Ash.drawLayer(g, t, 'bg_forest', 0, 150, 0, 0);
      const ground = S.get('ground', t);
      for (let x = 0; x < 300; x += 84) g.drawImage(ground, x, 134, 84, 84);
      const rock = S.get('prop_rock', t); g.drawImage(rock, 130, 134 + 4 - 36, 48, 36);
      const hero = S.get(`hero_t${t}_s0`, 0), h = ART.hero.idle;
      S.frame(g, hero, t, 126, frameIndex(time, h.fps, h.frames, true), 0, 80 - 63, 140 - 118, false, 80);
      const foe = S.get('foe_footman_t' + t, 0), f = ART.foes.idle;
      S.frame(g, foe, t, 126, frameIndex(time, f.fps, f.frames, true), 0, 220 - 63, 140 - 118, true, 220);
    });
  });

  // ---- slide 4: the four forms ----
  $('#stages').innerHTML = CFG.stages.map((s, i) => `<div class="box card grow" style="${i === 3 ? 'border-image-source:url(' + D.images.panel + ')' : ''}">
      <div id="stage${i}"></div><h3 style="color:#ffd86a">${s.name.toUpperCase()}</h3>
      <div class="stat">HP <b>${s.max_health}</b> STAMINA <b>${s.max_stamina}</b><br>DAMAGE <b>X${s.damage_mult}</b> SPEED <b>X${s.speed_mult}</b><br>CORES <b>${s.cores_required}</b></div></div>`).join('');
  CFG.stages.forEach((s, i) => {
    const c = canvasFor(HERO_BOX[2], HERO_BOX[3], 1.6);
    $('#stage' + i).appendChild(c);
    const g = c.getContext('2d');
    addLive(3, time => {
      g.clearRect(0, 0, c.width, c.height);
      const h = ART.hero.idle;
      S.frame(g, S.get(`hero_t3_s${i}`, 0), 3, 126, frameIndex(time, h.fps, h.frames, true), 0, -HERO_BOX[0], -HERO_BOX[1], false, 63);
    });
  });

  // ---- slide 5: hero animations ----
  let heroTier = 1;
  const HERO_LIST = [['idle', 'IDLE'], ['run', 'RUN'], ['jump', 'JUMP'], ['dash', 'DASH'], ['attack', 'ATTACK'], ['hurt', 'HURT'], ['death', 'DEATH']];
  $('#hero-anims').innerHTML = HERO_LIST.map(([k, label]) => `<div class="anim" id="ha-${k}"><span>${label}</span><small>${ART.hero[k].frames} FRAMES ${k === 'jump' ? 'BY SPEED' : ART.hero[k].fps + ' FPS'}</small></div>`).join('');
  HERO_LIST.forEach(([k]) => {
    const c = canvasFor(HERO_BOX[2], HERO_BOX[3], 1);
    $('#ha-' + k).insertBefore(c, $('#ha-' + k).firstChild);
    const g = c.getContext('2d'), info = ART.hero[k];
    addLive(4, time => {
      g.clearRect(0, 0, c.width, c.height);
      g.imageSmoothingEnabled = false;
      let col = frameIndex(time, info.fps, info.frames, info.loop || k === 'attack' || k === 'jump' || k === 'dash' || k === 'hurt' || k === 'death');
      if (k === 'jump') col = Math.floor(time / 450) % 3;
      if (k === 'death') col = Math.min(5, Math.floor((time % 2400) / 1000 * info.fps));
      if (k === 'hurt') col = Math.floor(time / 180) % 2;
      S.frame(g, S.get(`hero_t${heroTier}_s0`, 0), heroTier, 126, col, HERO_ROWS[k], -HERO_BOX[0], -HERO_BOX[1], false, 63);
    });
  });

  // ---- slide 6: enemies ----
  let foeTier = 1;
  const FOES = [['low_level_knight', 'footman'], ['royal_knight', 'royal'], ['royal_knight_2', 'elite'], ['witch', 'witch']];
  const CYCLE = [['idle', 1400], ['walk', 1400], ['attack', 1100], ['hurt', 600], ['death', 1300]];
  const cards = FOES.map(([key, art]) => ({ key, art, name: CFG.enemies[key].display_name, e: CFG.enemies[key] }))
    .concat([{ key: 'boss', art: 'boss', name: CFG.boss.name, e: { max_health: CFG.boss.max_health, damage: CFG.boss.damage, speed: CFG.boss.speed, size: CFG.boss.size }, boss: true }]);
  $('#foes').innerHTML = cards.map((c, i) => `<div class="box card grow" style="${c.boss ? '' : ''}"><div id="foe${i}"></div><h3 style="color:${c.boss ? '#ff8a70' : '#ffd86a'}">${c.name.toUpperCase()}</h3>
      <div class="stat" id="foe-label${i}">IDLE</div><div class="stat">HITBOX <b>${c.e.size[0]} X ${c.e.size[1]}</b><br>HP <b>${c.e.max_health}</b> DMG <b>${c.e.damage}</b></div></div>`).join('');
  cards.forEach((c, i) => {
    const box = c.boss ? FOE_BOX.boss : FOE_BOX[1], cell = c.boss ? ART.boss_cell : 126;
    const cv = canvasFor(box[2], box[3], c.boss ? 0.8 : 1.1);
    $('#foe' + i).appendChild(cv);
    const g = cv.getContext('2d');
    addLive(5, time => {
      g.clearRect(0, 0, cv.width, cv.height);
      g.imageSmoothingEnabled = false;
      let t = time % CYCLE.reduce((a, b) => a + b[1], 0), name = 'idle', local = 0;
      for (const [n, ms] of CYCLE) { if (t < ms) { name = n; local = t; break; } t -= ms; }
      const info = ART.foes[name];
      let col = frameIndex(local, info.fps, info.frames, info.loop);
      if (name === 'attack') col = Math.min(4, Math.floor(local / 1100 * 5));
      if (name === 'hurt') col = Math.min(1, Math.floor(local / 150));
      $('#foe-label' + i).textContent = name.toUpperCase();
      S.frame(g, S.get('foe_' + c.art, foeTier), foeTier, cell, col, FOE_ROWS[name], -box[0], -box[1], false, cell / 2);
    });
  });

  // ---- slide 7: assets ----
  $('#weapons').innerHTML = Object.values(CFG.weapons).map(w => `<div><canvas width="48" height="48" data-icon="${w.icon}"></canvas><br>${w.display_name.toUpperCase()}<br>DMG ${w.damage} RNG ${w.range}</div>`).join('');
  $$('#weapons canvas').forEach(c => {
    const n = 48 / S.pixelSize(3), g = c.getContext('2d');
    g.imageSmoothingEnabled = false;
    g.drawImage(S.get('weapons', 3), +c.dataset.icon * n, 0, n, n, 0, 0, 48, 48);
  });
  function picture(sheet, tier, cellW, cellH, col, scale) {
    const c = canvasFor(cellW, cellH, scale), p = S.pixelSize(tier);
    c.getContext('2d').drawImage(S.get(sheet, tier), col * cellW / p, 0, cellW / p, cellH / p, 0, 0, cellW, cellH);
    return c;
  }
  const items = $('#items');
  [['coin', 24, 24, 0], ['core', 24, 24, 0], ['book', 30, 30, 0], ['chest', 42, 36, 0], ['chest', 42, 36, 1], ['chest', 42, 36, 2]].forEach(([n, w, h, col]) => items.appendChild(picture(n, 3, w, h, col, 1.2)));
  const fire = canvasFor(48, 54, 1); items.appendChild(fire);
  addLive(6, time => { const g = fire.getContext('2d'); g.clearRect(0, 0, 48, 54); g.drawImage(S.get('fire', 3), Math.floor(time / 130) % 4 * 16, 0, 16, 18, 0, 0, 48, 54); });
  const props = $('#props');
  [['prop_tree', 90, 132, 0.45], ['prop_pillar', 42, 84, 0.7], ['prop_rock_big', 66, 54, 0.9], ['prop_sign', 48, 54, 0.9], ['prop_fence', 66, 42, 0.9], ['prop_tombstone', 36, 48, 0.9], ['prop_ice_plant', 42, 42, 0.9]]
    .forEach(([n, w, h, s]) => props.appendChild(picture(n.replace('prop_', 'prop_'), 3, w, h, 0, s)));

  // ---- slide 8: tileset and tilemap ----
  let tileTier = 1;
  function fillTiles() {
    const box = $('#tiles'); box.innerHTML = '';
    const t = tileTier, p = S.pixelSize(t);
    box.appendChild(picture('ground', t, 84, 84, 0, 0.8));
    [0, 1, 2].forEach(i => box.appendChild(picture('stone', t, 42, 42, i, 1.2)));
    const cap = canvasFor(42, 18, 1.2); cap.getContext('2d').drawImage(S.get('cap', t), 0, 0, 42, 18); box.appendChild(cap);
    $('#tile-note').textContent = `GROUND ${84 / p}X${84 / p} ART PX, STONE ${42 / p}X${42 / p}. EACH ART PIXEL IS ${p} SCREEN PX.`;
  }
  const LAYERS = ['SKY BANDS', 'CLOUDS 0.05', 'MIST HILLS 0.12', 'FOREST 0.25', 'GROUND ROW 84 PX', 'PLATFORMS 42 PX', 'PROPS', 'PICKUPS AND ENEMIES'];
  $('#layer-list').innerHTML = LAYERS.map((l, i) => `<li id="ly${i}">${l}</li>`).join('');
  const layerCanvas = $('#cv-layers'), lg = layerCanvas.getContext('2d');
  let layerWorld = null, layerT = 0;
  function newLayerWorld() {
    const layout = clone(D.levels[1]); layout.tier = tileTier;
    layerWorld = new Ash.World(layout, { player: Ash.createPlayer(520, 0, CFG.default_weapon, 0), settings: { shake: false, difficulty: 'normal' } });
    layerWorld.player.x = 560;
    layerT = 0;
  }
  addLive(7, (time, dt) => {
    if (!layerWorld) newLayerWorld();
    layerT += dt;
    const w = layerWorld, step = Math.min(7, Math.floor(layerT / 1300) % 11);
    const cam = 330; w.t += dt;
    lg.imageSmoothingEnabled = false;
    lg.fillStyle = '#222'; lg.fillRect(0, 0, 960, 540);
    const s = step > 7 ? 7 : step;
    if (s >= 0) Ash.drawSky(lg);
    if (s >= 1) Ash.drawLayer(lg, tileTier, 'bg_clouds', 0.05, 200, cam, w.t * 0.006);
    if (s >= 2) Ash.drawLayer(lg, tileTier, 'bg_mist', 0.12, w.ground + 12, cam, 0);
    if (s >= 3) Ash.drawLayer(lg, tileTier, 'bg_forest', 0.25, w.ground + 24, cam, 0);
    if (s >= 4) w.drawGround(lg, cam);
    if (s >= 5) w.platforms.forEach(p => w.drawPlatform(lg, p, cam));
    if (s >= 6) w.drawDecor(lg, cam);
    if (s >= 7) { w.chests.forEach(c => w.drawChest(lg, c, cam)); w.drawPickups(lg, cam); w.enemies.forEach(e => w.drawEnemy(lg, e, cam)); w.drawPlayer(lg, cam); }
    $$('#layer-list li').forEach((li, i) => { li.style.color = i <= s ? '#ffd86a' : '#8f95a6'; });
  });

  // ---- slide 9: levels ----
  const LV = [
    ['FROSTBOUND PATH', '3,400 PX LONG', 'ONLY BASIC ENEMIES', ['9 FOOTMEN', '10 PIXEL CORES', 'NO TRAPS', 'HERO: THE EXILE']],
    ['SHATTERED RUINS', '4,200 PX LONG', 'ENEMIES + TRAPS', ['10 ENEMIES', '4 SPIKES 3 FIRE VENTS 5 ICICLES', '12 PIXEL CORES', 'HERO: THE WANDERER']],
    ["THE DOMINION'S GATE", '3,300 PX + ARENA', 'ENEMIES + BOSS', ['11 ENEMIES', 'THE DOMINION 520 HP', '12 PIXEL CORES', 'HERO: THE RECLAIMER']],
  ];
  $('#levels').innerHTML = LV.map((l, i) => `<div class="box card grow"><h3 style="font-size:2em;color:#ffd86a">${i + 1}</h3><h3>${l[0]}</h3><div class="small" style="color:#8fc4ee">${l[2]}</div>
      <div class="stat" style="text-align:left;margin-top:.5em">${l[1]}<br>${l[3].join('<br>')}<br>ART: <b>${ART.tiers[i + 1].pixel} PX PIXELS</b></div></div>`).join('');

  // ---- slide 10: the real game played by a bot ----
  const mock = $('#cv-level'), mg = mock.getContext('2d');
  let mockWorld = null, mockLevel = 1, mockSpeed = 2, endT = 0, lastX = 0, stuck = 0, jump = 0, acc = 0;
  const WEAPON = { 1: 'gladius_voltaic', 2: 'gladius_voltaic', 3: 'securis_ashborn' }, CORES = { 1: 0, 2: 6, 3: 14 };
  function startMock(n) {
    mockLevel = n;
    const layout = clone(D.levels[n]);
    if (n === 3) layout.start.x = layout.arena.start - 260;
    mockWorld = new Ash.World(layout, { player: Ash.createPlayer(layout.start.x, CORES[n], WEAPON[n], 0), settings: { shake: true, difficulty: 'normal' } });
    endT = 0; stuck = 0; jump = 0; lastX = layout.start.x;
    Object.keys(Ash.input).forEach(k => { Ash.input[k] = false; });
  }
  function bot(w) {
    const p = w.player, I = Ash.input, b = w.boss;
    if (p.hp < p.maxHp * 0.3) p.hp = Math.round(p.maxHp * 0.55);
    p.sta = Math.max(p.sta, 40);
    I.right = true; I.left = false; I.attack = false; I.jump = false; I.dash = false;
    const px = p.x + p.w / 2;
    const near = w.enemies.find(e => e.alive && e.x > p.x - 10 && e.x - p.x < 90 && Math.abs(e.y - p.y) < 80);
    if (b && w.arenaLocked && b.alive && b.phase !== 'intro') {
      const d = (b.x + b.w / 2) - px;
      if (Math.abs(d) < 62) { I.right = false; I.attack = true; p.face = d > 0 ? 1 : -1; } else { I.right = d > 0; I.left = d < 0; }
      if (w.projectiles.some(q => q.kind === 'wave' && Math.abs(q.x + q.w / 2 - px) < 70) && p.onGround) I.jump = true;
      if (Math.floor(w.t / 3000) !== Math.floor((w.t - 17) / 3000)) I.dash = true;
    } else if (near && near.x - (p.x + p.w) < 40) { I.right = false; I.attack = true; p.face = 1; }
    if (w.spikes.concat(w.fires).some(s => s.x - px < 65 && s.x - px > 30)) jump = 40;
    if (jump > 0) { I.jump = true; jump--; }
    if (p.vx === 0 && I.right && p.knockT <= 0 && p.onGround && !I.attack) I.jump = true;
  }
  addLive(9, (time, dt) => {
    if (!mockWorld) startMock(mockLevel);
    acc += Math.min(dt, 100);
    while (acc >= STEP) {
      acc -= STEP;
      for (let s = 0; s < mockSpeed; s++) {
        const w = mockWorld;
        if (w.result) { endT += STEP; if (endT > 1400) { startMock(mockLevel); break; } continue; }
        bot(w); w.update(STEP);
        const p = w.player;
        if (!(w.arenaLocked && w.boss && w.boss.alive)) { if (Math.abs(p.x - lastX) > 25) { lastX = p.x; stuck = 0; } else if (++stuck > 240) { p.x += 140; p.vx = 0; p.knockT = 0; stuck = 0; lastX = p.x; } }
      }
    }
    mockWorld.draw(mg);
    Ash.drawHud(mg, mockWorld, null);
  });
  $$('[data-tabs=mock] .tab[data-t]').forEach(b => { b.onclick = () => { $$('[data-tabs=mock] .tab[data-t]').forEach(x => x.classList.toggle('on', x === b)); startMock(+b.dataset.t); }; });
  $('#speed').onclick = () => { mockSpeed = mockSpeed === 1 ? 2 : mockSpeed === 2 ? 3 : 1; $('#speed').textContent = 'SPEED ' + mockSpeed + 'X'; };

  // ---- tabs on slides 5, 6 and 8 ----
  $$('[data-tabs=hero] .tab').forEach(b => b.onclick = () => { heroTier = +b.dataset.t; $$('[data-tabs=hero] .tab').forEach(x => x.classList.toggle('on', x === b)); $('#hero-size').textContent = `${126 / S.pixelSize(heroTier)} X ${126 / S.pixelSize(heroTier)}`; $('#hero-pixel').textContent = S.pixelSize(heroTier) + ' PX'; });
  $$('[data-tabs=foe] .tab').forEach(b => b.onclick = () => { foeTier = +b.dataset.t; $$('[data-tabs=foe] .tab').forEach(x => x.classList.toggle('on', x === b)); });
  $$('[data-tabs=tile] .tab').forEach(b => b.onclick = () => { tileTier = +b.dataset.t; $$('[data-tabs=tile] .tab').forEach(x => x.classList.toggle('on', x === b)); fillTiles(); newLayerWorld(); });
  fillTiles();

  // ---- navigation, timer, notes ----
  const slides = $$('.slide'), dots = $('#dots');
  slides.forEach((_, i) => { const d = document.createElement('div'); d.className = 'dot'; d.onclick = () => go(i); dots.appendChild(d); });
  let current = 0, started = 0;
  function go(i) {
    current = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach((s, k) => s.classList.toggle('active', k === current));
    $$('.dot').forEach((d, k) => d.classList.toggle('on', k === current));
    $('#count').textContent = `${current + 1} / ${slides.length}`;
    $('#notes').textContent = slides[current].dataset.notes || '';
    Object.keys(Ash.input).forEach(k => { Ash.input[k] = false; });
    if (history.replaceState) history.replaceState(null, '', '#' + (current + 1));
    if (current > 0 && !started) started = Date.now();
  }
  $('#prev').onclick = () => go(current - 1);
  $('#next').onclick = () => go(current + 1);
  window.addEventListener('keydown', e => {
    const k = e.key;
    if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); go(current + 1); }
    else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); go(current - 1); }
    else if (k === 'Home') go(0); else if (k === 'End') go(slides.length - 1);
    else if (/^[1-9]$/.test(k)) go(+k - 1);
    else if (k === 'f' || k === 'F') { document.fullscreenElement ? document.exitFullscreen() : deck.requestFullscreen && deck.requestFullscreen(); }
    else if (k === 't' || k === 'T') { $('#timer').classList.toggle('show'); if (!started) started = Date.now(); }
    else if (k === 'n' || k === 'N') $('#notes').classList.toggle('show');
  });

  // ---- main loop ----
  let last = performance.now(), start = last, menuT = 0;
  function frame(now) {
    const dt = Math.min(100, now - last);
    last = now; menuT += dt;
    Ash.drawMenuBackdrop(bg, menuT);
    try { live.filter(a => a.slide === current).forEach(a => a.fn(now - start, dt)); } catch (e) { console.error(e); }
    if (started) {
      const sec = Math.floor((Date.now() - started) / 1000), t = $('#timer');
      t.textContent = String(Math.floor(sec / 60)).padStart(2, '0') + ':' + String(sec % 60).padStart(2, '0') + ' / 10:00';
      t.classList.toggle('warn', sec >= 540 && sec < 600); t.classList.toggle('over', sec >= 600);
    }
    requestAnimationFrame(frame);
  }
  go(Math.max(0, (parseInt((location.hash || '#1').slice(1), 10) || 1) - 1));
  requestAnimationFrame(frame);
  window.__deck = { go, get current() { return current; } };
})();
