// Drawing. Every sprite is drawn without smoothing so the pixel art stays sharp.
(function () {
  'use strict';
  const Ash = window.Ash;
  const { W, H, World, centerX, centerY } = Ash;
  const S = Ash.sprites;
  const FONT = 'AshPixel';

  const HERO_ROWS = { idle: 0, run: 1, jump: 2, dash: 3, attack: 4, hurt: 5, death: 6 };
  const FOE_ROWS = { idle: 0, walk: 1, attack: 2, hurt: 3, death: 4 };

  // ---- small helpers -----------------------------------------------------
  function text(g, str, x, y, size, color, align) {
    g.font = `${size}px ${FONT}`;
    g.textAlign = align || 'left';
    g.fillStyle = '#15131d';
    g.fillText(str, x + size / 8, y + size / 8);
    g.fillStyle = color || '#ffffff';
    g.fillText(str, x, y);
  }

  function pixelBar(g, x, y, w, h, share, color, dark, flash) {
    g.fillStyle = flash ? '#ff4a4a' : '#15131d';
    g.fillRect(x - 3, y - 3, w + 6, h + 6);
    g.fillStyle = '#232744';
    g.fillRect(x, y, w, h);
    const fill = Math.round(w * Math.max(0, Math.min(1, share)) / 3) * 3;
    if (fill > 0) {
      g.fillStyle = dark;
      g.fillRect(x, y, fill, h);
      g.fillStyle = color;
      g.fillRect(x, y, fill, Math.max(1, h - Math.min(6, h - 1)));
      if (h >= 9) {
        g.fillStyle = 'rgba(255,255,255,0.35)';
        g.fillRect(x, y, fill, 3);
      }
    }
  }

  // a triangle built from horizontal stripes, with an outline - used for spikes, icicles and ice waves
  function pixelTriangle(g, cx, y, w, h, unit, main, shade, pointDown) {
    const rows = Math.max(1, Math.round(h / unit));
    for (let pass = 0; pass < 2; pass++) {
      for (let r = 0; r < rows; r++) {
        const share = pointDown ? 1 - (r + 0.5) / rows : (r + 0.5) / rows;
        const rw = Math.max(unit, Math.round(w * share / unit) * unit);
        const ry = y + r * unit;
        if (pass === 0) { g.fillStyle = '#15131d'; g.fillRect(cx - rw / 2 - unit, ry - (r === 0 ? unit : 0), rw + unit * 2, unit + (r === 0 ? unit : 0)); }
        else {
          g.fillStyle = main;
          g.fillRect(cx - rw / 2, ry, rw, unit);
          g.fillStyle = shade;
          g.fillRect(cx, ry, rw / 2, unit);
        }
      }
    }
  }

  function pixelDisc(g, x, y, radius, unit, color) {
    g.fillStyle = color;
    for (let dy = -radius; dy <= radius; dy += unit) {
      const half = Math.round(Math.sqrt(radius * radius - dy * dy) / unit) * unit;
      g.fillRect(Math.round(x - half), Math.round(y + dy), half * 2, unit);
    }
  }

  const frameIndex = (animT, fps, count, loop) => {
    const i = Math.floor(animT / 1000 * fps);
    return loop ? i % count : Math.min(count - 1, i);
  };

  // ---- backdrop (shared by the game and the menu) ------------------------
  function drawSky(g) {
    const top = [107, 85, 169], bottom = [79, 76, 100], bandH = 24, bands = Math.ceil(H / bandH);
    for (let i = 0; i <= bands; i++) {
      const t = i / bands, y = i * bandH;
      g.fillStyle = `rgb(${top.map((c, k) => Math.round(c + (bottom[k] - c) * t)).join(',')})`;
      g.fillRect(0, y, W, bandH + 1);
      if (i > 0) {                                  // dithered edge between bands
        g.fillStyle = `rgb(${top.map((c, k) => Math.round(c + (bottom[k] - c) * (t - 1 / bands))).join(',')})`;
        for (let x = (i % 2) * 6; x < W; x += 12) g.fillRect(x, y, 6, 6);
      }
    }
  }

  function drawLayer(g, tier, name, factor, bottom, camX, drift, fadeTop, fadeBottom) {
    const img = S.get(name, tier);
    if (!img.width) return;
    const art = faded(img, fadeTop || 0, fadeBottom || 0);
    const p = S.pixelSize(tier), w = img.width * p, h = img.height * p;
    let x = -(((camX * factor) + (drift || 0)) % w);
    for (; x < W; x += w) g.drawImage(art, Math.round(x), Math.round(bottom - h), w, h);
  }

  // Background tiles are rectangles, so their edges fade into the sky instead of cutting.
  const fadedCache = new WeakMap();
  function faded(img, top, bottom) {
    if (!top && !bottom) return img;
    let cache = fadedCache.get(img);
    if (!cache) { cache = new Map(); fadedCache.set(img, cache); }
    const key = top + ':' + bottom;
    if (cache.has(key)) return cache.get(key);
    const canvas = document.createElement('canvas');
    canvas.width = img.width; canvas.height = img.height;
    const c = canvas.getContext('2d');
    c.drawImage(img, 0, 0);
    c.globalCompositeOperation = 'destination-in';
    const grad = c.createLinearGradient(0, 0, 0, canvas.height);
    grad.addColorStop(0, top ? 'rgba(0,0,0,0)' : 'rgba(0,0,0,1)');
    if (top) grad.addColorStop(Math.min(0.9, top), 'rgba(0,0,0,1)');
    if (bottom) {
      grad.addColorStop(Math.max(0.1, 1 - bottom), 'rgba(0,0,0,1)');
      grad.addColorStop(1, 'rgba(0,0,0,0)');
    } else grad.addColorStop(1, 'rgba(0,0,0,1)');
    c.fillStyle = grad;
    c.fillRect(0, 0, canvas.width, canvas.height);
    cache.set(key, canvas);
    return canvas;
  }

  Ash.drawSky = drawSky;
  Ash.drawLayer = drawLayer;

  Ash.drawVignette = function (g) {
    const grad = g.createRadialGradient(W / 2, H / 2, H * 0.38, W / 2, H / 2, H * 1.08);
    grad.addColorStop(0, 'rgba(8,6,16,0)');
    grad.addColorStop(0.72, 'rgba(8,6,16,0.12)');
    grad.addColorStop(1, 'rgba(8,6,16,0.52)');
    g.fillStyle = grad;
    g.fillRect(0, 0, W, H);
    const scrim = g.createLinearGradient(0, 0, 0, 150);
    scrim.addColorStop(0, 'rgba(8,6,16,0.3)');
    scrim.addColorStop(1, 'rgba(8,6,16,0)');
    g.fillStyle = scrim;
    g.fillRect(0, 0, W, 150);
  };

  Ash.drawBackdrop = function (g, tier, theme, camX, t, ground) {
    drawSky(g);
    g.globalAlpha = 0.85;
    drawLayer(g, tier, 'bg_clouds', 0.05, 200, camX, t * 0.006, 0.22, 0.18);
    g.globalAlpha = 0.55;
    drawLayer(g, tier, 'bg_mist', 0.1, ground + 16, camX, 0, 0.42, 0.4);
    g.globalAlpha = 1;
    const haze = g.createLinearGradient(0, ground - 170, 0, ground + 20);
    haze.addColorStop(0, 'rgba(190,180,230,0)');
    haze.addColorStop(1, theme === 'night' ? 'rgba(255,150,130,0.12)' : 'rgba(200,205,245,0.14)');
    g.fillStyle = haze;
    g.fillRect(0, ground - 170, W, 190);
    drawLayer(g, tier, theme === 'forest' ? 'bg_forest' : 'bg_ruins', theme === 'forest' ? 0.25 : 0.28, ground + 24, camX, 0, theme === 'forest' ? 0.46 : 0.26, 0);
    if (theme === 'night') { g.fillStyle = 'rgba(70,10,50,0.3)'; g.fillRect(0, 0, W, H); }
    else if (theme === 'ruins') { g.fillStyle = 'rgba(30,20,70,0.14)'; g.fillRect(0, 0, W, H); }
  };

  Ash.drawMenuBackdrop = function (g, t) {
    drawSky(g);
    drawLayer(g, 1, 'bg_clouds', 0.012, 230, 0, t * 0.01, 0.22, 0.18);
    g.globalAlpha = 0.6;
    drawLayer(g, 1, 'bg_mist', 0.01, 420, 0, t * 0.004, 0.4, 0.35);
    g.globalAlpha = 1;
    drawLayer(g, 1, 'bg_forest', 0.02, 430, 0, t * 0.008, 0.4, 0);
    const ground = S.get('ground', 1), p = S.pixelSize(1), w = ground.width * p;
    g.fillStyle = '#f4f8ff';
    g.fillRect(0, 440, W, H - 440);
    for (let x = 0; x < W; x += w) g.drawImage(ground, x, 436, w, ground.height * p);
    g.fillStyle = '#3a2a28';
    g.fillRect(0, 436 + ground.height * p, W, H);
    g.fillStyle = '#ffffff';
    for (let i = 0; i < 40; i++) {
      const x = (i * 97 + t * 0.02 * (1 + i % 3)) % W, y = (i * 53 + t * 0.03 * (1 + i % 2)) % H;
      g.fillRect(Math.round(x), Math.round(y), 3, 3);
    }
    Ash.drawVignette(g);
  };

  // ---- the world ----------------------------------------------------------
  const P = World.prototype;

  P.drawGround = function (g, camX) {
    const img = S.get('ground', this.tier), size = 84;
    for (let x = -(camX % size); x < W; x += size) g.drawImage(img, Math.round(x), this.ground - 4, size, size);
  };

  P.drawPlatform = function (g, s, camX) {
    const x = s.x - camX;
    if (x > W || x + s.w < 0) return;
    const tier = this.tier, stone = S.get('stone', tier), cap = S.get('cap', tier), n = 42 / S.pixelSize(tier);
    g.save();
    g.beginPath(); g.rect(x, s.y, s.w, s.h); g.clip();
    for (let tx = 0; tx < s.w; tx += 42) g.drawImage(stone, this.stoneTheme * n, 0, n, n, Math.round(x + tx), s.y - 3, 42, 42);
    g.restore();
    g.fillStyle = '#15131d';
    g.fillRect(x - 3, s.y + s.h, s.w + 6, 3);
    g.fillRect(x - 3, s.y, 3, s.h);
    g.fillRect(x + s.w, s.y, 3, s.h);
    for (let tx = -3; tx < s.w + 3; tx += 42) g.drawImage(cap, Math.round(x + tx), s.y - 8, 42, 18);
  };

  const DECOR = {
    rock: ['prop_rock', 48, 36], rock_small: ['prop_rock_small', 36, 24], tree: ['prop_tree', 90, 132], ice_plant: ['prop_ice_plant', 42, 42],
    sign: ['prop_sign', 48, 54], fence: ['prop_fence', 66, 42], pillar: ['prop_pillar', 42, 84], tombstone: ['prop_tombstone', 36, 48],
    lantern: ['prop_lantern', 30, 60],
  };

  P.drawDecor = function (g, camX) {
    const tier = this.tier;
    for (const [wx, kind] of this.decor) {
      const x = wx - camX;
      if (x < -100 || x > W + 100) continue;
      const [name, w, h] = DECOR[kind], img = S.get(name, tier);
      if (kind === 'lantern') {
        const n = w / S.pixelSize(tier), f = Math.floor(this.t / 300) % 2;
        g.drawImage(img, f * n, 0, n, h / S.pixelSize(tier), Math.round(x - w / 2), this.ground + 4 - h, w, h);
      } else g.drawImage(img, Math.round(x - w / 2), this.ground + 4 - h, w, h);
    }
    for (const fire of this.restFires) {
      const x = fire.x - camX, img = S.get('fire_big', tier), n = 60 / S.pixelSize(tier), f = Math.floor(this.t / 130) % 4;
      g.drawImage(img, f * n, 0, n, 66 / S.pixelSize(tier), Math.round(x - 30), this.ground + 6 - 66, 60, 66);
      if (this.player.hp < this.player.maxHp && Math.abs(centerX(this.player) - fire.x) < 90) {
        g.fillStyle = 'rgba(255,190,90,0.14)';
        pixelDisc(g, x, this.ground - 24, 90, 6, 'rgba(255,190,90,0.14)');
      }
    }
    if (this.layout.end_x !== null) {                       // exit gate
      const x = this.layout.end_x - camX;
      const glow = g.createLinearGradient(0, 0, 0, this.ground);
      glow.addColorStop(0, 'rgba(160,220,255,0)');
      glow.addColorStop(0.55, 'rgba(160,220,255,0.1)');
      glow.addColorStop(1, 'rgba(180,235,255,0.34)');
      g.fillStyle = glow;
      g.fillRect(x - 30, 0, 60, this.ground);
      g.fillStyle = 'rgba(215,245,255,0.3)';
      for (let i = 0; i < 4; i++) {
        const yy = (this.t * 0.05 + i * 60) % this.ground;
        g.fillRect(x - 21, Math.round(yy / 3) * 3, 42, 2);
      }
      g.drawImage(S.get('prop_sign', tier), Math.round(x - 24), this.ground + 4 - 54, 48, 54);
      g.fillStyle = 'rgba(13,11,22,0.7)';
      g.fillRect(x - 26, this.ground - 44, 52, 20);
      text(g, 'EXIT', x, this.ground - 29, 16, '#cfefff', 'center');
    }
  };

  P.drawHazards = function (g, camX) {
    const unit = S.pixelSize(this.tier);
    for (const s of this.spikes) {
      const x = s.x - camX;
      if (x > W || x + s.w < 0) continue;
      const count = Math.max(1, Math.round(s.w / 14)), w = s.w / count;
      for (let i = 0; i < count; i++) pixelTriangle(g, x + w * (i + 0.5), s.y, w - 2, s.h, 3, '#cfe6ff', '#8fc4ee', false);
    }
    const fire = S.get('fire', this.tier), n = 48 / unit;
    for (const f of this.fires) {
      const x = f.x - camX;
      if (x > W + 40 || x < -60) continue;
      const frame = Math.floor(this.t / 120) % 4;
      if (f.active) {
        g.drawImage(fire, frame * n, 0, n, 54 / unit, Math.round(x + 20 - 24), this.ground + 2 - 54, 48, 54);
      } else {
        g.globalAlpha = f.warning ? 0.5 + 0.5 * Math.sin(this.t / 40) : 0.5;
        g.drawImage(fire, 0, 0, n, 54 / unit, Math.round(x + 20 - 14), this.ground + 2 - 32, 28, 32);
        g.globalAlpha = 1;
      }
    }
    for (const ic of this.icicles) {
      const x = ic.x - camX;
      if (x > W + 20 || x < -20 || ic.state === 'gone') continue;
      const shake = ic.state === 'warn' ? Math.round(Math.sin(this.t / 25) * 3 / 3) * 3 : 0;
      pixelTriangle(g, x + shake, ic.state === 'fall' ? ic.y : 0, 15, 39, 3, '#cfe6ff', '#8fc4ee', true);
      if (ic.state === 'warn') { g.fillStyle = 'rgba(255,80,80,0.6)'; g.fillRect(x - 9, this.ground - 3, 18, 3); }
    }
    for (const r of this.iceRain) { g.fillStyle = 'rgba(255,80,80,0.6)'; g.fillRect(r.x - camX - 9, this.ground - 3, 18, 3); }
  };

  P.drawChest = function (g, c, camX) {
    const x = c.x - camX;
    if (x > W || x + c.w < 0) return;
    const img = S.get('chest', this.tier), p = S.pixelSize(this.tier), n = 42 / p, f = c.open ? 1 : c.locked ? 2 : 0;
    g.drawImage(img, f * n, 0, n, 36 / p, Math.round(x + c.w / 2 - 21), c.y + c.h - 34, 42, 36);
    const p1 = this.player;
    if (!c.open && Math.abs(centerX(p1) - centerX(c)) < 44 && Math.abs(centerY(p1) - centerY(c)) < 50) {
      text(g, c.locked ? 'E: OPEN (15 COINS)' : 'E: OPEN', x + c.w / 2, c.y - 14, 16, '#ffffff', 'center');
    }
  };

  P.drawPickups = function (g, camX) {
    const tier = this.tier, p = S.pixelSize(tier);
    for (const c of this.cores) {
      if (c.got) continue;
      const x = c.x - camX;
      if (x > W || x < -30) continue;
      const y = c.y + Math.round(Math.sin(this.t / 250 + c.phase) * 4 / 3) * 3;
      pixelDisc(g, x + 7, y + 7, 18, 6, 'rgba(255,220,110,0.22)');
      g.drawImage(S.get('core', tier), Math.round(x + 7 - 12), y + 7 - 12, 24, 24);
    }
    for (const c of this.coins) if (!c.got && c.x - camX < W && c.x - camX > -30) g.drawImage(S.get('coin', tier), Math.round(c.x - camX), c.y, 22, 22);
    for (const b of this.books) if (!b.got && b.x - camX < W && b.x - camX > -30) g.drawImage(S.get('book', tier), Math.round(b.x - camX - 3), b.y - 4 + Math.round(Math.sin(this.t / 300) * 3 / 3) * 3, 30, 30);
    const weapons = S.get('weapons', tier), n = 48 / p;
    for (const w of this.weaponPickups) {
      if (w.got) continue;
      const x = w.x - camX;
      if (x > W || x < -40) continue;
      const icon = Ash.config.weapons[w.key].icon;
      pixelDisc(g, x + 14, w.y + 14, 20, 6, 'rgba(150,210,255,0.3)');
      g.drawImage(weapons, icon * n, 0, n, n, Math.round(x - 4), w.y - 6 + Math.round(Math.sin(this.t / 260) * 3 / 3) * 3, 36, 36);
      if (Math.abs(centerX(this.player) - (w.x + 14)) < 90) {
        text(g, Ash.config.weapons[w.key].display_name.toUpperCase(), x + 14, w.y - 20, 16, '#cfe6ff', 'center');
      }
    }
  };

  P.drawEnemy = function (g, e, camX) {
    const x = centerX(e) - camX;
    if (x < -90 || x > W + 90) return;
    const meta = Ash.config.art, cellSize = meta.foe_cell, origin = meta.foe_origin;
    const img = S.get('foe_' + e.base.art, this.tier), anim = meta.foes[e.anim];
    let col;
    if (!e.alive) col = Math.min(5, Math.floor(e.deadT / 1000 * meta.foes.death.fps));
    else if (e.anim === 'attack') {
      col = e.windup > 0 ? (1 - e.windup / e.windupTotal < 0.55 ? 0 : 1) : 2 + Math.min(2, Math.floor((1 - e.strikeT / 280) * 3));
    } else if (e.anim === 'hurt') col = Math.min(1, Math.floor(e.animT / 70));
    else col = frameIndex(e.animT, anim.fps, anim.frames, anim.loop);
    const row = e.alive ? FOE_ROWS[e.anim] : FOE_ROWS.death;
    g.fillStyle = 'rgba(0,0,0,0.25)';
    g.fillRect(Math.round(x - e.w * 0.6), e.y + e.h, Math.round(e.w * 1.2), 3);
    const left = Math.round(x - origin[0]), top = Math.round(e.y + e.h - origin[1]);
    g.globalAlpha = e.alive ? 1 : Math.max(0, Math.min(1, (1500 - e.deadT) / 600));
    S.frame(g, img, this.tier, cellSize, col, row, left, top, e.face < 0, x);
    if (e.hurtT > 0 && e.alive) { g.globalAlpha = 0.65; S.frame(g, S.mask(img), this.tier, cellSize, col, row, left, top, e.face < 0, x); }
    g.globalAlpha = 1;
    if (!e.alive) return;
    const bw = Math.max(36, Math.round(e.w / 3) * 3), by = e.y - 13;
    pixelBar(g, Math.round(x - bw / 2), by, bw, 4, e.hp / e.maxHp, '#d83a3a', '#7a2230', false);
    if (e.windup > 0) text(g, '!', x, by - 6, 24, '#ffe25a', 'center');
  };

  P.drawBoss = function (g, camX) {
    const b = this.boss;
    if (!b) return;
    const x = centerX(b) - camX;
    if (x < -120 || x > W + 120) return;
    const meta = Ash.config.art, cellSize = meta.boss_cell, origin = meta.boss_origin, img = S.get('foe_boss', this.tier);
    let col = 0, row = FOE_ROWS.idle;
    const fps = meta.foes;
    if (b.phase === 'dead') { row = FOE_ROWS.death; col = Math.min(5, Math.floor(b.timer / 2200 * 6)); }
    else if (b.anim === 'attack') {
      row = FOE_ROWS.attack;
      if (['windSlash', 'windCharge', 'windJump'].includes(b.phase)) col = 1 - b.timer / b.windTotal < 0.55 ? 0 : 1;
      else if (b.phase === 'slash') col = 2 + Math.min(1, Math.floor((1 - b.timer / 170) * 2));
      else if (b.phase === 'charge') col = 3;
      else if (b.phase === 'air') col = 2;
      else col = 4;
    } else if (b.anim === 'walk') { row = FOE_ROWS.walk; col = frameIndex(b.animT, fps.walk.fps, fps.walk.frames, true); }
    else col = frameIndex(b.animT, fps.idle.fps, fps.idle.frames, true);
    g.fillStyle = 'rgba(0,0,0,0.3)';
    g.fillRect(Math.round(x - b.w * 0.7), b.y + b.h, Math.round(b.w * 1.4), 3);
    if (b.enraged && b.alive) pixelDisc(g, x, centerY(b), 72, 6, 'rgba(255,60,30,0.14)');
    const left = Math.round(x - origin[0]), top = Math.round(b.y + b.h - origin[1]);
    g.globalAlpha = b.phase === 'dead' ? Math.max(0, 1 - b.timer / 2200) : 1;
    S.frame(g, img, this.tier, cellSize, col, row, left, top, b.face < 0, x);
    if (b.hurtT > 0 && b.alive) { g.globalAlpha = 0.65; S.frame(g, S.mask(img), this.tier, cellSize, col, row, left, top, b.face < 0, x); }
    g.globalAlpha = 1;
    if (['windSlash', 'windCharge', 'windJump'].includes(b.phase)) text(g, '!', x, b.y - 12, 32, '#ff5a40', 'center');
  };

  P.drawProjectiles = function (g, camX) {
    for (const q of this.projectiles) {
      const x = q.x - camX;
      if (x < -60 || x > W + 60) continue;
      if (q.kind === 'orb') {
        pixelDisc(g, x + 5, q.y + 5, 12, 3, 'rgba(164,90,240,0.35)');
        pixelDisc(g, x + 5, q.y + 5, 6, 3, q.color);
        g.fillStyle = '#ffffff';
        g.fillRect(Math.round(x + 3), Math.round(q.y + 3), 3, 3);
      } else if (q.kind === 'wave') pixelTriangle(g, x + q.w / 2, q.y, q.w, q.h, 3, '#e6f0ff', '#8fc4ee', false);
      else pixelTriangle(g, x + q.w / 2, q.y, q.w, q.h, 3, '#cfe6ff', '#8fc4ee', true);
    }
  };

  P.drawPlayer = function (g, camX) {
    const p = this.player, x = centerX(p) - camX, meta = Ash.config.art;
    const cell = meta.hero_cell, origin = meta.hero_origin, img = S.get(`hero_t${this.tier}_s${p.stage}`, 0);
    const info = meta.hero[p.anim];
    let col;
    switch (p.anim) {
      case 'attack': col = (p.combo % 3) * 4 + Math.min(3, Math.floor((1 - p.attackAnimT / Ash.ATTACK_ANIM_MS) * 4)); break;
      case 'death': col = Math.min(info.frames - 1, Math.floor(p.deathT / Ash.DEATH_MS * info.frames)); break;
      case 'dash': col = Math.min(2, Math.floor(p.animT / 60)); break;
      case 'hurt': col = Math.min(1, Math.floor(p.animT / 85)); break;
      case 'jump': col = p.vy < -6 ? 0 : p.vy < 2 ? 1 : 2; break;
      default: col = frameIndex(p.animT, info.fps, info.frames, info.loop);
    }
    const row = HERO_ROWS[p.anim];
    for (const gh of p.ghosts) {                                       // dash afterimages
      g.globalAlpha = Math.max(0, gh.life / 200) * 0.45;
      S.frame(g, S.mask(img), this.tier, cell, gh.frame, HERO_ROWS.dash, Math.round(gh.x - camX - origin[0]), Math.round(gh.bottom - origin[1]), gh.face < 0, gh.x - camX);
    }
    g.globalAlpha = 1;
    if (p.alive) {
      g.fillStyle = 'rgba(0,0,0,0.25)';
      g.fillRect(Math.round(x - p.w * 0.7), this.ground, Math.round(p.w * 1.4), 3);
    }
    if (p.evolveT > 0) pixelDisc(g, x, centerY(p), 48, 6, `rgba(255,220,120,${0.3 * Math.min(1, p.evolveT / 600)})`);
    const blink = p.alive && p.hurtT > 0 && p.dashT <= 0 && Math.floor(p.hurtT / 70) % 2 === 0;
    g.globalAlpha = blink ? 0.4 : p.anim === 'death' ? Math.max(0.3, 1 - Math.max(0, p.deathT - 700) / 700) : 1;
    S.frame(g, img, this.tier, cell, col, row, Math.round(x - origin[0]), Math.round(p.y + p.h - origin[1]) + 1, p.face < 0, x);
    g.globalAlpha = 1;
    if (p.dashT > 0) {                                                 // speed lines
      g.fillStyle = 'rgba(235,245,255,0.75)';
      for (let i = 0; i < 4; i++) {
        const yy = Math.round(p.y + 9 + i * (p.h - 15) / 3), start = x - p.dashDir * (p.w / 2 + 6 + i * 3);
        g.fillRect(Math.round(Math.min(start, start - p.dashDir * (24 + i * 6))), yy, 24 + i * 6, 3);
      }
    }
  };

  P.draw = function (g) {
    const sh = this.shake > 0 ? { x: Math.round((Math.random() * 2 - 1) * this.shake), y: Math.round((Math.random() * 2 - 1) * this.shake) } : { x: 0, y: 0 };
    const camX = Math.round(this.cam);
    g.save();
    g.translate(sh.x, sh.y);
    g.imageSmoothingEnabled = false;
    Ash.drawBackdrop(g, this.tier, this.theme, camX, this.t, this.ground);
    this.drawGround(g, camX);
    this.drawDecor(g, camX);
    this.platforms.forEach(s => this.drawPlatform(g, s, camX));
    this.drawHazards(g, camX);
    this.chests.forEach(c => this.drawChest(g, c, camX));
    this.drawPickups(g, camX);
    this.enemies.forEach(e => this.drawEnemy(g, e, camX));
    this.drawBoss(g, camX);
    this.drawProjectiles(g, camX);
    this.drawPlayer(g, camX);
    for (const q of this.particles) {
      g.globalAlpha = Math.max(0, q.life / q.maxLife);
      g.fillStyle = q.color;
      g.fillRect(Math.round((q.x - camX) / 3) * 3, Math.round(q.y / 3) * 3, 3, 3);
    }
    g.globalAlpha = 1;
    for (const q of this.texts) {
      g.globalAlpha = Math.min(1, q.life / 400);
      text(g, q.text, Math.round(q.x - camX), Math.round(q.y), 16, q.color, 'center');
    }
    g.globalAlpha = 1;
    if (this.arenaLocked) {
      const pulse = 0.1 + 0.05 * Math.sin(this.t / 260);
      const left = this.arena.start - camX, right = this.arena.end - camX;
      const lg = g.createLinearGradient(left, 0, left + 90, 0);
      lg.addColorStop(0, 'rgba(140,200,255,' + (pulse + 0.12).toFixed(3) + ')');
      lg.addColorStop(1, 'rgba(140,200,255,0)');
      g.fillStyle = lg; g.fillRect(left, 0, 90, this.ground);
      const rg = g.createLinearGradient(right, 0, right - 90, 0);
      rg.addColorStop(0, 'rgba(140,200,255,' + (pulse + 0.12).toFixed(3) + ')');
      rg.addColorStop(1, 'rgba(140,200,255,0)');
      g.fillStyle = rg; g.fillRect(right - 90, 0, 90, this.ground);
      g.fillStyle = 'rgba(160,220,255,0.5)';
      g.fillRect(left - 3, 0, 3, this.ground);
      g.fillRect(right, 0, 3, this.ground);
    }
    g.fillStyle = this.theme === 'night' ? 'rgba(255,170,140,0.8)' : 'rgba(255,255,255,0.85)';
    for (const f of this.snow) {                                       // falling snow
      f.y += f.speed;
      f.x += Math.sin(this.t / 700 + f.drift) * 0.4 - 0.15;
      if (f.y > H) { f.y = -4; f.x = Math.random() * W; }
      if (f.x < -4) f.x = W;
      g.fillRect(Math.round(f.x / 3) * 3, Math.round(f.y / 3) * 3, 3, 3);
    }
    g.restore();
    Ash.drawVignette(g);
  };

  // ---- HUD ---------------------------------------------------------------
  const BOX = { dark: '#15131d', stone: '#686d80', light: '#b4bacc', snow: '#f4f8ff', navy: '#232744' };

  function frameBox(g, x, y, w, h) {
    g.fillStyle = BOX.dark; g.fillRect(x - 3, y - 3, w + 6, h + 6);
    g.fillStyle = BOX.stone; g.fillRect(x, y, w, h);
    g.fillStyle = BOX.navy; g.fillRect(x + 3, y + 3, w - 6, h - 6);
    g.fillStyle = BOX.snow; g.fillRect(x, y, w, 3);
  }

  function chip(g, x, y, w, h) {
    g.fillStyle = 'rgba(13,11,22,0.74)';
    g.fillRect(x, y, w, h);
    g.fillStyle = 'rgba(180,200,240,0.22)';
    g.fillRect(x, y, w, 2);
  }

  Ash.drawHud = function (g, world, options) {
    const p = world.player, cfg = Ash.config, tier = world.tier;
    g.imageSmoothingEnabled = false;
    // portrait: head and shoulders from the idle frame
    frameBox(g, 12, 12, 66, 66);
    const meta = cfg.art, pix = S.pixelSize(tier), hero = S.get(`hero_t${tier}_s${p.stage}`, 0);
    g.save();
    g.beginPath(); g.rect(15, 15, 60, 60); g.clip();
    const sx = 33 / pix, sy = 36 / pix, sw = 60 / pix;
    g.drawImage(hero, sx, sy, sw, sw, 15, 15, 60, 60);
    g.restore();

    const icons = S.get('icons', 0), barX = 118, barW = 168;
    g.drawImage(icons, 0, 0, 8, 8, 90, 14, 24, 24);
    pixelBar(g, barX, 15, barW, 18, p.hp / p.maxHp, '#e0484c', '#8a2432', false);
    text(g, `${Math.ceil(p.hp)}/${p.maxHp}`, barX + barW - 6, 30, 16, '#ffffff', 'right');
    g.drawImage(icons, 8, 0, 8, 8, 90, 40, 24, 24);
    pixelBar(g, barX, 42, barW, 18, p.sta / p.maxSta, '#6cc24a', '#3a7a2a', p.noStaminaT > 0);
    text(g, String(Math.floor(p.sta)), barX + barW - 6, 57, 16, '#ffffff', 'right');
    const stages = cfg.stages, next = stages[p.stage + 1], now = stages[p.stage];
    g.drawImage(icons, 16, 0, 8, 8, 90, 66, 24, 24);
    pixelBar(g, barX, 69, barW, 18, next ? (p.cores - now.cores_required) / (next.cores_required - now.cores_required) : 1, '#f0c040', '#a0701c', false);
    text(g, next ? `${p.cores}/${next.cores_required}` : `${p.cores} MAX`, barX + barW - 6, 84, 16, '#ffffff', 'right');

    chip(g, 8, 94, 322, 26);
    text(g, now.name.toUpperCase(), 16, 112, 16, '#ffe9a8');
    g.drawImage(S.get('coin', tier), 246, 99, 18, 18);
    text(g, String(p.coins), 272, 112, 16, '#ffe9a8');

    // weapon and dash
    const w = cfg.weapons[p.weapon], wx = W - 206;
    frameBox(g, wx, 12, 54, 54);
    const n = 48 / pix;
    g.drawImage(S.get('weapons', tier), w.icon * n, 0, n, n, wx + 3, 15, 48, 48);
    chip(g, wx - 40, 72, 134, 48);
    text(g, w.display_name.toUpperCase(), wx + 27, 88, 16, '#dfe9ff', 'center');
    const ready = p.dashCd <= 0 && p.dashT <= 0, share = p.dashT > 0 ? 0 : 1 - Math.max(0, p.dashCd) / cfg.physics.dash_cooldown;
    pixelBar(g, wx, 102, 54, 6, share, ready ? '#8fc4ee' : '#4a78a8', '#24468a', false);
    if (world.time < 6000) text(g, Ash.isTouch ? 'TAP >> DASH' : 'SHIFT DASH', wx + 27, 134, 16, ready ? '#c9f3ff' : '#8fa8c8', 'center');

    chip(g, W / 2 - 190, 12, 380, 24);
    text(g, `LEVEL ${world.layout.id}  ${world.layout.name.toUpperCase()}`, W / 2, 30, 16, '#e8f3ff', 'center');
    const b = world.boss;
    if (b && world.arenaLocked && b.phase !== 'dormant') {
      chip(g, W / 2 - 190, 44, 380, 44);
      text(g, cfg.boss.name.toUpperCase(), W / 2, 62, 16, '#ff8a70', 'center');
      pixelBar(g, W / 2 - 150, 70, 300, 15, b.hp / b.maxHp, b.enraged ? '#ff4a2a' : '#c62d3a', '#7a1824', false);
      if (b.enraged) text(g, 'ENRAGED', W / 2 + 162, 81, 16, '#ff6a50', 'left');
    }
    if (p.evolveT > 0) text(g, 'EVOLVED: ' + now.name.toUpperCase(), W / 2, 148, 32, '#ffd86a', 'center');
    if (world.banner) {
      const bn = world.banner;
      g.globalAlpha = Math.max(0, Math.min(1, bn.t / 400, (bn.max - bn.t) / 250 + 0.2));
      text(g, bn.text, W / 2, 210, 32, bn.color || '#ff6a55', 'center');
      g.globalAlpha = 1;
    }
    if (options && options.fps) text(g, options.fps + ' FPS', W - 12, H - 10, 16, '#9fe39f', 'right');
  };
})();
