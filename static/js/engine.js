// Game rules and simulation. Numbers (stats, weapons, enemies, levels) come from the Python backend.
(function () {
  'use strict';

  const W = 960, H = 540;
  const STEP = 1000 / 60;            // the game always advances in 1/60 s steps
  const ATTACK_ANIM_MS = 300;        // length of one attack animation
  const COMBO_MS = 700;              // press attack again within this time to chain the next swing
  const DEATH_MS = 1100;

  let CFG = null;
  const input = { left: false, right: false, jump: false, attack: false, interact: false, dash: false };

  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const rand = (lo, hi) => lo + Math.random() * (hi - lo);
  const centerX = e => e.x + e.w / 2;
  const centerY = e => e.y + e.h / 2;
  const hit = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h - 0.001 && a.y + a.h > b.y + 0.001;

  // ---- hero -------------------------------------------------------------
  function stageFor(cores) {
    let stage = 0;
    CFG.stages.forEach((s, i) => { if (cores >= s.cores_required) stage = i; });
    return stage;
  }

  function applyStage(p, stage, first) {
    const s = CFG.stages[stage];
    const hpShare = first ? 1 : p.hp / p.maxHp;
    p.stage = stage;
    p.maxHp = s.max_health;
    p.maxSta = s.max_stamina;
    p.damageMult = s.damage_mult;
    p.speedMult = s.speed_mult;
    p.hp = Math.round(p.maxHp * hpShare);
    p.sta = first ? p.maxSta : Math.min(p.sta, p.maxSta);
  }

  function createPlayer(startX, cores, weapon, coins) {
    const [w, h] = CFG.hero_size;
    const p = {
      x: startX, y: CFG.physics.ground_y - h, w, h, vx: 0, vy: 0, face: 1, onGround: true, alive: true,
      hp: 1, maxHp: 1, sta: 1, maxSta: 1, damageMult: 1, speedMult: 1, stage: 0,
      cores: cores || 0, coins: coins || 0, weapon: weapon || CFG.default_weapon,
      attackCd: 0, swingT: 0, swingHits: new Set(), hurtT: 0, knockT: 0, coyote: 0, jumpBuffer: 0, jumpHeld: false,
      deathT: 0, evolveT: 0, noStaminaT: 0,
      dashT: 0, dashCd: 0, dashDir: 1, dashHeld: false, ghosts: [],
      attackAnimT: 0, combo: 0, comboT: 0, anim: 'idle', animT: 0,
    };
    applyStage(p, stageFor(p.cores), true);
    return p;
  }

  const savePlayer = p => ({ cores: p.cores, coins: p.coins, weapon: p.weapon });

  // ---- world ------------------------------------------------------------
  class World {
    constructor(layout, opts) {
      this.layout = layout;
      this.settings = opts.settings;
      this.ground = CFG.physics.ground_y;
      this.width = layout.width;
      this.tier = layout.tier;
      this.theme = layout.theme;
      this.stoneTheme = layout.stone_theme;
      this.t = 0;
      this.time = 0;
      this.result = null;
      this.cam = 0;
      this.shake = 0;
      this.freeze = 0;
      this.kills = 0;
      this.banner = null;

      const diff = CFG.difficulty[this.settings.difficulty] || CFG.difficulty.normal;
      this.diff = diff;

      const p = opts.player || createPlayer(layout.start.x, layout.start.cores, layout.start.weapon, 0);
      Object.assign(p, {
        x: layout.start.x, y: this.ground - p.h, vx: 0, vy: 0, hp: p.maxHp, sta: p.maxSta, alive: true,
        hurtT: 0, knockT: 0, deathT: 0, attackCd: 0, swingT: 0, dashT: 0, dashCd: 0, ghosts: [],
        attackAnimT: 0, comboT: 0, combo: 0, anim: 'idle', animT: 0,
      });
      this.player = p;

      this.platforms = layout.platforms.map(([x, y, w, h]) => ({ x, y, w, h }));
      this.walls = [];
      this.cores = layout.cores.map(([x, y]) => ({ x, y, w: 14, h: 14, got: false, phase: Math.random() * 6 }));
      this.coins = layout.coins.map(([x, y]) => ({ x, y, w: 22, h: 22, got: false, amount: 5 }));
      this.books = layout.books.map(([x, y]) => ({ x, y, w: 24, h: 24, got: false }));
      this.weaponPickups = layout.weapons.map(([x, y, key]) => ({ x, y, w: 28, h: 28, got: false, key }));
      this.chests = layout.chests.map(([x, y, locked]) => ({ x, y, w: 34, h: 28, locked: !!locked, open: false }));
      const spikeH = CFG.traps.spike.height;
      this.spikes = layout.spikes.map(([x, w]) => ({ x, y: this.ground - spikeH, w, h: spikeH }));
      this.icicles = layout.icicles.map(([x]) => ({ x, y: 0, vy: 0, state: 'idle', t: 0 }));
      this.fires = layout.fires.map(([x, phase]) => ({ x, y: this.ground - 46, w: 40, h: 46, phase, active: false }));
      this.restFires = (layout.rest || []).map(([x]) => ({ x }));
      this.decor = layout.decor;

      this.enemies = layout.enemies.map(([x, y, type]) => this.makeEnemy(x, y, type));
      this.projectiles = [];
      this.particles = [];
      this.texts = [];
      this.snow = Array.from({ length: 70 }, () => ({ x: Math.random() * W, y: Math.random() * H, speed: rand(0.4, 1.4), drift: rand(0, 6) }));

      this.boss = null;
      this.arena = layout.arena;
      this.arenaLocked = false;
      this.iceRain = [];
      if (layout.boss) this.boss = this.makeBoss(layout.boss);
      this.cam = clamp(p.x - W / 2, 0, this.width - W);
    }

    makeEnemy(x, y, type) {
      const base = CFG.enemies[type], scale = this.layout.enemy_scale;
      const hp = Math.round(base.max_health * scale.health * this.diff.enemy_health);
      return {
        type, base, x, y, w: base.size[0], h: base.size[1], vx: 0, vy: 0, face: Math.random() < 0.5 ? -1 : 1,
        onGround: false, alive: true, hp, maxHp: hp,
        damage: base.damage * scale.damage * this.diff.enemy_damage, speed: base.speed * scale.speed,
        state: 'patrol', home: x + base.size[0] / 2, patrolDir: Math.random() < 0.5 ? -1 : 1,
        windup: 0, windupTotal: base.windup, strikeT: 0, cooldown: 400 + Math.random() * 600,
        hurtT: 0, knockT: 0, deadT: 0, anim: 'idle', animT: Math.random() * 600,
      };
    }

    makeBoss(spot) {
      const B = CFG.boss, hp = Math.round(B.max_health * this.diff.enemy_health);
      return {
        x: spot.x, y: spot.y, w: B.size[0], h: B.size[1], vx: 0, vy: 0, face: -1, onGround: true,
        hp, maxHp: hp, damage: B.damage * this.diff.enemy_damage, speed: B.speed,
        phase: 'dormant', timer: 0, cooldown: 0, enraged: false, hurtT: 0, hitDone: false, contactCd: 0, dir: 1, airT: 0,
        alive: true, anim: 'idle', animT: 0,
      };
    }

    // ---- physics ----
    solids() { return this.walls.length ? this.platforms.concat(this.walls) : this.platforms; }

    move(e) {
      const solids = this.solids();
      e.x += e.vx;
      for (const s of solids) {
        if (hit(e, s)) e.x = e.vx > 0 ? s.x - e.w : s.x + s.w;
      }
      e.x = clamp(e.x, 0, this.width - e.w);
      e.y += e.vy;
      e.onGround = false;
      if (e.y + e.h >= this.ground) {
        e.y = this.ground - e.h;
        if (e.vy > 0) e.vy = 0;
        e.onGround = true;
      }
      for (const s of solids) {
        if (!hit(e, s)) continue;
        if (e.vy > 0) { e.y = s.y - e.h; e.vy = 0; e.onGround = true; }
        else if (e.vy < 0) { e.y = s.y + s.h; e.vy = 0; }
      }
    }

    fall(e) { e.vy = Math.min(e.vy + CFG.physics.gravity, CFG.physics.max_fall); }

    solidAt(x, y) {
      if (y >= this.ground) return true;
      return this.platforms.some(s => x >= s.x && x <= s.x + s.w && y >= s.y && y <= s.y + s.h);
    }

    // ---- effects ----
    say(x, y, text, color) { this.texts.push({ x, y, text, color: color || '#ffffff', life: 900 }); }

    burst(x, y, count, color, speed, gravity) {
      for (let i = 0; i < count; i++) {
        const a = Math.random() * Math.PI * 2, s = rand(0.5, speed || 3);
        this.particles.push({ x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s - 1, life: rand(300, 700), maxLife: 700, color,
          size: 3, gravity: gravity === undefined ? 0.12 : gravity });
      }
    }

    addShake(n) { if (this.settings.shake) this.shake = Math.max(this.shake, n); }
    hitStop(ms) { if (!this.result) this.freeze = Math.max(this.freeze, ms); }
    sound(name) { window.GameAudio.sfx(name); }

    // ---- hero ----
    hurtPlayer(damage, fromX, pushX, pushY) {
      const p = this.player;
      if (!p.alive || p.hurtT > 0 || this.result) return;
      damage = Math.max(1, Math.round(damage));
      p.hp -= damage;
      p.hurtT = CFG.physics.hurt_cooldown;
      p.knockT = 170;
      p.vx = (centerX(p) < fromX ? -1 : 1) * (pushX === undefined ? 4.5 : pushX);
      p.vy = pushY === undefined ? -4 : pushY;
      this.say(centerX(p), p.y - 6, '-' + damage, '#ff6a6a');
      this.burst(centerX(p), centerY(p), 8, '#d94040', 3);
      this.addShake(5);
      this.hitStop(90);
      this.sound('hurt');
      if (p.hp <= 0) {
        p.hp = 0; p.alive = false; p.deathT = 0; p.vy = -4;
        this.sound('lose');
      }
    }

    heal(amount) {
      const p = this.player, before = p.hp;
      p.hp = Math.min(p.maxHp, p.hp + amount);
      if (p.hp > before) this.say(centerX(p), p.y - 10, '+' + Math.round(p.hp - before), '#6aff8a');
    }

    collectCore() {
      const p = this.player;
      p.cores++;
      this.sound('core');
      const stage = stageFor(p.cores);
      if (stage > p.stage) {
        applyStage(p, stage, false);
        p.hp = Math.min(p.maxHp, p.hp + Math.round(p.maxHp * 0.4));
        p.evolveT = 1800;
        this.sound('evolve');
        this.addShake(4);
        this.burst(centerX(p), centerY(p), 30, '#ffd86a', 5, 0.05);
      }
    }

    equip(key) {
      this.player.weapon = key;
      this.sound('weapon');
      this.say(centerX(this.player), this.player.y - 18, CFG.weapons[key].display_name, '#9fd0ff');
    }

    attack() {
      const p = this.player, weapon = CFG.weapons[p.weapon], phys = CFG.physics;
      if (p.attackCd > 0 || !p.alive) return;
      if (p.sta < phys.attack_stamina) { p.noStaminaT = 300; return; }
      p.attackCd = Math.max(phys.attack_cooldown, weapon.cooldown);
      p.sta -= phys.attack_stamina;
      p.swingHits = new Set();
      p.combo = p.comboT > 0 ? p.combo + 1 : 0;
      p.comboT = COMBO_MS;
      p.attackAnimT = ATTACK_ANIM_MS;
      p.swingT = 190;
      this.sound('swing');
    }

    meleeBox() {
      const p = this.player, reach = CFG.weapons[p.weapon].range;
      return { x: p.face > 0 ? p.x + p.w : p.x - reach, y: p.y, w: reach, h: p.h };
    }

    chooseAnim(p, dt) {
      p.ghosts = p.ghosts.filter(g => (g.life -= dt) > 0);
      let name = 'idle';
      if (!p.alive) name = 'death';
      else if (p.dashT > 0) name = 'dash';
      else if (p.knockT > 0) name = 'hurt';
      else if (p.attackAnimT > 0) name = 'attack';
      else if (!p.onGround) name = 'jump';
      else if (Math.abs(p.vx) > 0.5) name = 'run';
      if (name !== p.anim) { p.anim = name; p.animT = 0; }
      else p.animT += dt;
    }

    updatePlayer(dt) {
      const p = this.player, phys = CFG.physics;
      if (!p.alive) {
        p.deathT += dt;
        this.fall(p);
        p.vx *= 0.95;
        this.move(p);
        this.chooseAnim(p, dt);
        if (p.deathT > DEATH_MS && !this.result) this.result = 'dead';
        return;
      }
      p.evolveT = Math.max(0, p.evolveT - dt);
      p.noStaminaT = Math.max(0, p.noStaminaT - dt);
      p.dashCd = Math.max(0, p.dashCd - dt);
      p.attackAnimT = Math.max(0, p.attackAnimT - dt);
      p.comboT = Math.max(0, p.comboT - dt);
      p.attackCd = Math.max(0, p.attackCd - dt);
      p.hurtT = Math.max(0, p.hurtT - dt);

      if (input.dash && !p.dashHeld && p.dashT <= 0 && p.dashCd <= 0 && p.knockT <= 0 && p.sta >= phys.dash_stamina) {
        p.dashT = phys.dash_ms;
        p.sta -= phys.dash_stamina;
        p.dashDir = input.right ? 1 : input.left ? -1 : p.face;
        p.face = p.dashDir;
        p.hurtT = Math.max(p.hurtT, phys.dash_ms + 30);    // brief invulnerability
        p.swingT = 0;
        p.attackAnimT = 0;
        this.sound('dash');
        this.burst(centerX(p), p.y + p.h - 4, 8, '#dfeaff', 2.4, 0.03);
      }
      p.dashHeld = input.dash;

      if (p.dashT > 0) {
        p.dashT -= dt;
        p.vx = p.dashDir * phys.dash_speed;
        p.vy = 0;
        if (Math.floor(this.t / 40) !== Math.floor((this.t - dt) / 40)) {
          p.ghosts.push({ x: centerX(p), bottom: p.y + p.h, face: p.dashDir, frame: Math.min(2, Math.floor((phys.dash_ms - p.dashT) / 60)), life: 200 });
        }
        this.move(p);
        if (p.dashT <= 0) { p.vx = 0; p.dashCd = phys.dash_cooldown; }
        p.sta = Math.min(p.maxSta, p.sta + phys.stamina_regen);
        this.chooseAnim(p, dt);
        return;
      }

      if (p.knockT > 0) p.knockT -= dt;
      else {
        const dir = (input.right ? 1 : 0) - (input.left ? 1 : 0);
        p.vx = dir * phys.move_speed * p.speedMult;
        if (dir) p.face = dir;
      }

      // coyote time and a short jump buffer make jumping forgiving
      p.coyote = p.onGround ? 90 : p.coyote - dt;
      if (input.jump && !p.jumpHeld) p.jumpBuffer = 110;
      p.jumpBuffer -= dt;
      if (p.jumpBuffer > 0 && p.coyote > 0 && p.knockT <= 0) {
        p.vy = phys.jump_power;
        p.jumpBuffer = 0;
        p.coyote = 0;
        this.sound('jump');
        this.burst(centerX(p), p.y + p.h, 5, '#dfeaff', 1.6, 0.05);
      }
      if (!input.jump && p.jumpHeld && p.vy < -4.5) p.vy = -4.5;      // let go early for a short hop
      p.jumpHeld = input.jump;

      if (input.attack) this.attack();
      const wasGround = p.onGround;
      this.fall(p);
      const fallSpeed = p.vy;
      this.move(p);
      if (!wasGround && p.onGround && fallSpeed > 5) {
        const n = fallSpeed > 9 ? 10 : 6;
        this.burst(centerX(p), p.y + p.h - 2, n, '#e8f1ff', 1.8, 0.06);
        this.addShake(fallSpeed > 9 ? 2.5 : 1.2);
      }
      p.sta = Math.min(p.maxSta, p.sta + phys.stamina_regen);
      p.swingT = Math.max(0, p.swingT - dt);
      this.chooseAnim(p, dt);

      if (p.swingT > 0) {                      // each enemy is hit once per swing
        const box = this.meleeBox(), damage = CFG.weapons[p.weapon].damage * p.damageMult;
        for (const e of this.enemies) {
          if (e.alive && !p.swingHits.has(e) && hit(box, e)) { p.swingHits.add(e); this.hurtEnemy(e, damage, centerX(p)); }
        }
        const b = this.boss;
        if (b && b.alive && !p.swingHits.has(b) && hit(box, b)) { p.swingHits.add(b); this.hurtBoss(damage); }
      }
    }

    // ---- enemies ----
    hurtEnemy(e, damage, fromX) {
      damage = Math.round(damage);
      e.hp -= damage;
      e.hurtT = 140;
      e.knockT = 160;
      e.vx = (centerX(e) < fromX ? -1 : 1) * 3;
      e.windup = 0;
      this.say(centerX(e), e.y - 6, String(damage), '#ffe27a');
      this.burst(centerX(e), centerY(e), 6, '#ffd9a0', 3);
      this.hitStop(45);
      this.sound('hit');
      if (e.hp > 0) return;
      e.alive = false;
      e.deadT = 0;
      this.kills++;
      this.burst(centerX(e), centerY(e), 14, e.base.projectile_color || '#c9c9d4', 4);
      this.sound('enemyDie');
      if (Math.random() < 0.35) {
        this.coins.push({ x: centerX(e) - 11, y: Math.min(e.y + e.h - 24, this.ground - 26), w: 22, h: 22, got: false, amount: 5 });
      }
    }

    updateEnemy(e, dt) {
      e.animT += dt;
      if (!e.alive) { e.deadT += dt; return; }
      const p = this.player, base = e.base;
      e.hurtT = Math.max(0, e.hurtT - dt);
      e.cooldown -= dt;
      e.strikeT = Math.max(0, e.strikeT - dt);
      let anim = 'idle';

      if (e.knockT > 0) {
        e.knockT -= dt;
        e.vx *= 0.9;
        anim = 'hurt';
      } else {
        const dx = centerX(p) - centerX(e), dist = Math.abs(dx), dy = Math.abs(centerY(p) - centerY(e));
        let state = 'patrol';
        if (p.alive && dist <= base.attack_range && dy < Math.max(60, e.h)) state = 'attack';
        else if (p.alive && dist <= base.detect_range && dy < 150) state = 'chase';
        if (e.windup > 0) state = 'attack';
        e.state = state;

        if (state === 'patrol') {
          e.vx = e.speed * 0.7 * e.patrolDir;
          e.face = e.patrolDir;
          if (Math.abs(centerX(e) - e.home) > 90) e.patrolDir = centerX(e) > e.home ? -1 : 1;
          if (e.onGround && e.y + e.h < this.ground - 1) {        // on a platform: turn at the edge
            if (!this.solidAt(centerX(e) + e.patrolDir * (e.w / 2 + 6), e.y + e.h + 3)) e.patrolDir *= -1;
          }
          anim = 'walk';
        } else if (state === 'chase') {
          e.face = dx >= 0 ? 1 : -1;
          e.vx = e.speed * e.face;
          anim = 'walk';
        } else {
          e.face = dx >= 0 ? 1 : -1;
          e.vx = 0;
          if (e.windup > 0) {
            e.windup -= dt;
            if (e.windup <= 0) this.enemyStrike(e, dx, dy);
          } else if (e.cooldown <= 0) {
            e.windup = e.windupTotal;
            e.cooldown = base.attack_cooldown;
            if (base.ranged) this.sound('cast');
          }
        }
        if (e.windup > 0 || e.strikeT > 0) anim = 'attack';
      }
      if (anim !== e.anim) { e.anim = anim; e.animT = 0; }
      this.fall(e);
      this.move(e);
    }

    enemyStrike(e, dx, dy) {
      const p = this.player, base = e.base;
      e.strikeT = 280;
      if (base.ranged) {
        this.projectiles.push({ kind: 'orb', owner: 'enemy', x: centerX(e) - 5, y: centerY(e) - 5, w: 10, h: 10,
          vx: base.projectile_speed * (dx >= 0 ? 1 : -1), vy: 0, damage: e.damage, life: 3000, color: base.projectile_color });
      } else if (p.alive && Math.abs(centerX(p) - centerX(e)) <= base.attack_range + 14 && dy < Math.max(60, e.h)) {
        this.hurtPlayer(e.damage, centerX(e));
        this.sound('hit');
      }
    }

    // ---- boss ----
    hurtBoss(damage) {
      const b = this.boss;
      if (!b.alive || b.phase === 'dormant' || b.phase === 'intro') return;
      damage = Math.round(damage);
      b.hp -= damage;
      b.hurtT = 110;
      this.say(centerX(b), b.y - 8, String(damage), '#ffe27a');
      this.burst(centerX(b), centerY(b), 6, '#ff9a8a', 3);
      this.hitStop(70);
      this.sound('hit');
      if (!b.enraged && b.hp / b.maxHp <= CFG.boss.enrage_at) {
        b.enraged = true;
        this.sound('roar');
        this.addShake(8);
        this.banner = { text: 'THE DOMINION IS ENRAGED', t: 1600, max: 1600 };
      }
      if (b.hp <= 0) {
        b.hp = 0; b.alive = false; b.phase = 'dead'; b.timer = 0; b.vx = 0;
        this.projectiles = this.projectiles.filter(q => q.owner === 'player');
        this.iceRain = [];
        this.burst(centerX(b), centerY(b), 40, '#ff6a50', 6, 0.08);
        this.addShake(12);
        this.sound('roar');
        this.banner = { text: 'THE DOMINION HAS FALLEN', t: 2200, max: 2200 };
      }
    }

    lockArena() {
      const a = this.arena, b = this.boss;
      this.arenaLocked = true;
      this.walls = [{ x: a.start - 80, y: -1000, w: 80, h: 2000 }, { x: a.end, y: -1000, w: 80, h: 2000 }];
      b.phase = 'intro';
      b.timer = CFG.boss.intro_ms;
      this.banner = { text: CFG.boss.name.toUpperCase(), t: CFG.boss.intro_ms, max: CFG.boss.intro_ms };
      this.sound('roar');
      this.addShake(6);
      if (this.onBoss) this.onBoss();
    }

    updateBoss(dt) {
      const b = this.boss, p = this.player;
      if (!b || b.phase === 'dormant') return;
      b.animT += dt;
      b.hurtT = Math.max(0, b.hurtT - dt);
      b.contactCd -= dt;
      const dx = centerX(p) - centerX(b), dist = Math.abs(dx), dir = dx >= 0 ? 1 : -1, angry = b.enraged;
      this.fall(b);

      if (b.phase === 'dead') {
        b.timer += dt;
        b.vx = 0;
        this.move(b);
        if (b.timer % 160 < dt) this.burst(b.x + rand(0, b.w), b.y + rand(0, b.h), 5, '#ff7a5a', 4, 0.06);
        if (b.timer > 2200 && !this.result) this.result = 'complete';
        return;
      }

      b.timer -= dt;
      switch (b.phase) {
        case 'intro':
          b.vx = 0; b.face = dir;
          if (b.timer <= 0) { b.phase = 'idle'; b.cooldown = 700; }
          break;
        case 'idle':
          b.face = dir;
          b.vx = dist > 70 ? dir * b.speed * (angry ? 1.35 : 1) : 0;
          b.cooldown -= dt;
          if (b.cooldown <= 0 && p.alive) this.pickBossAttack(b, dist, dir, angry);
          break;
        case 'windSlash':
          b.vx = 0; b.face = b.dir;
          if (b.timer <= 0) { b.phase = 'slash'; b.timer = 170; b.hitDone = false; this.sound('swing'); }
          break;
        case 'slash': {
          b.vx = 0;
          const box = { x: b.dir > 0 ? b.x + b.w : b.x - 96, y: b.y, w: 96, h: b.h };
          if (!b.hitDone && p.alive && hit(box, p)) { b.hitDone = true; this.hurtPlayer(b.damage, centerX(b), 6, -5); }
          if (b.timer <= 0) { b.phase = 'recover'; b.timer = 450; }
          break;
        }
        case 'windCharge':
          b.vx = 0; b.face = b.dir;
          if (b.timer <= 0) { b.phase = 'charge'; b.timer = 700; b.hitDone = false; }
          break;
        case 'charge': {
          const startX = b.x;
          b.vx = b.dir * 8 * (angry ? 1.2 : 1);
          if (!b.hitDone && p.alive && hit(b, p)) { b.hitDone = true; this.hurtPlayer(b.damage * 1.2, centerX(b), 7, -5); }
          if (b.timer <= 0 || (Math.abs(b.x - startX) < 0.1 && b.timer < 650)) { b.phase = 'recover'; b.timer = 800; b.vx = 0; }
          break;
        }
        case 'windJump':
          b.vx = 0; b.face = b.dir;
          if (b.timer <= 0) { b.vy = -14; b.vx = clamp(dx / 40, -5, 5); b.phase = 'air'; b.airT = 0; }
          break;
        case 'air':
          b.airT += dt;
          if (b.airT > 120 && b.onGround) { b.vx = 0; this.slam(); b.phase = 'recover'; b.timer = angry ? 500 : 700; }
          break;
        case 'recover':
          b.vx = 0;
          if (b.timer <= 0) { b.phase = 'idle'; b.cooldown = angry ? 450 : 850; }
          break;
      }
      this.move(b);

      if (b.phase !== 'intro' && b.phase !== 'charge' && p.alive && b.contactCd <= 0 && hit(b, p)) {
        b.contactCd = 700;
        this.hurtPlayer(b.damage * 0.5, centerX(b), 5, -4);
      }

      for (const r of this.iceRain) r.t -= dt;
      for (const r of this.iceRain.filter(q => q.t <= 0)) {
        this.projectiles.push({ kind: 'shard', owner: 'enemy', x: r.x - 7, y: -30, w: 14, h: 30, vx: 0, vy: 2,
          damage: 14 * this.diff.enemy_damage, life: 4000 });
      }
      this.iceRain = this.iceRain.filter(q => q.t > 0);

      let anim = 'idle';
      if (b.phase === 'hurt') anim = 'hurt';
      else if (['windSlash', 'windCharge', 'windJump', 'slash', 'air', 'recover', 'charge'].includes(b.phase)) anim = 'attack';
      else if (Math.abs(b.vx) > 0.1) anim = 'walk';
      if (anim !== b.anim) { b.anim = anim; b.animT = 0; }
    }

    pickBossAttack(b, dist, dir, angry) {
      const r = Math.random();
      if (dist < 120) {
        if (r < 0.6) { b.phase = 'windSlash'; b.timer = angry ? 380 : 520; }
        else if (r < 0.8) { b.phase = 'windJump'; b.timer = 350; }
        else { b.phase = 'windCharge'; b.timer = 600; }
      } else if (r < 0.45) { b.phase = 'windCharge'; b.timer = angry ? 450 : 600; }
      else if (r < 0.9) { b.phase = 'windJump'; b.timer = angry ? 260 : 350; }
      else { b.cooldown = 300; return; }
      b.dir = dir;
      b.hitDone = false;
      b.vx = 0;
      b.windTotal = b.timer;
      if (b.phase === 'windCharge') this.sound('charge');
    }

    slam() {
      const b = this.boss;
      this.sound('slam');
      this.addShake(9);
      this.burst(centerX(b), this.ground, 20, '#e6f0ff', 5, 0.15);
      for (const d of [-1, 1]) {
        this.projectiles.push({ kind: 'wave', owner: 'enemy', x: centerX(b) - 17, y: this.ground - 26, w: 34, h: 26, vx: d * 5, vy: 0,
          damage: CFG.boss.wave_damage * this.diff.enemy_damage, life: 2400, hit: false });
      }
      if (b.enraged) {
        for (let i = 0; i < 3; i++) {
          this.iceRain.push({ t: 700 + i * 380, x: clamp(centerX(this.player) + rand(-170, 170), this.arena.start + 30, this.arena.end - 30) });
        }
      }
    }

    // ---- projectiles, traps, pickups ----
    updateProjectiles(dt) {
      const p = this.player;
      for (const q of this.projectiles) {
        q.life -= dt;
        if (q.kind === 'shard') q.vy = Math.min(q.vy + 0.5, 13);
        q.x += q.vx;
        q.y += q.vy;
        if (q.life <= 0 || q.x < -50 || q.x > this.width + 50) { q.dead = true; continue; }
        if (q.kind !== 'wave') {
          const blocked = this.solids().some(s => hit(q, s)) || q.y + q.h >= this.ground;
          if (blocked) {
            q.dead = true;
            if (q.kind === 'shard') { this.burst(q.x + 7, q.y + q.h, 8, '#cfe6ff', 3); this.sound('icicleBreak'); }
            continue;
          }
        }
        if (p.alive && hit(q, p) && !q.hit) {
          this.hurtPlayer(q.damage, q.x, 4, -4);
          if (q.kind === 'wave') q.hit = true; else q.dead = true;
        }
      }
      this.projectiles = this.projectiles.filter(q => !q.dead);
    }

    updateTraps(dt) {
      const p = this.player, T = CFG.traps;
      if (!p.alive) return;
      for (const s of this.spikes) {
        if (hit({ x: p.x + 3, y: p.y, w: p.w - 6, h: p.h }, { x: s.x + 4, y: s.y + 5, w: s.w - 8, h: s.h - 5 })) {
          if (p.hurtT <= 0) this.sound('spike');
          this.hurtPlayer(T.spike.damage, centerX(s), 3, -8);
        }
      }
      const cycle = T.fire.on_ms + T.fire.off_ms;
      for (const f of this.fires) {
        const phase = (this.t + f.phase) % cycle;
        f.active = phase < T.fire.on_ms;
        f.warning = !f.active && phase > cycle - 350;
        if (f.active && Math.abs(centerX(p) - (f.x + 20)) < 400 && Math.floor(this.t / 400) !== Math.floor((this.t - dt) / 400)) this.sound('fire');
        if (f.active && hit(p, { x: f.x + 6, y: f.y + 8, w: f.w - 12, h: f.h - 8 })) this.hurtPlayer(T.fire.damage, f.x + 20, 3, -7);
      }
      for (const ic of this.icicles) {
        if (ic.state === 'idle' && Math.abs(centerX(p) - ic.x) < T.icicle.trigger && p.y + p.h > 100) {
          ic.state = 'warn';
          ic.t = T.icicle.warn_ms;
          this.sound('icicleWarn');
        } else if (ic.state === 'warn') {
          ic.t -= dt;
          if (ic.t <= 0) { ic.state = 'fall'; ic.vy = 2; ic.y = 40; }
        } else if (ic.state === 'fall') {
          ic.vy = Math.min(ic.vy + 0.55, 14);
          ic.y += ic.vy;
          const box = { x: ic.x - 7, y: ic.y, w: 14, h: 34 };
          const landed = box.y + box.h >= this.ground || this.platforms.some(s => hit(box, s));
          if (hit(box, p) || landed) {
            if (hit(box, p)) this.hurtPlayer(T.icicle.damage, ic.x, 3, -5);
            ic.state = 'gone';
            this.sound('icicleBreak');
            this.burst(ic.x, ic.y + 34, 10, '#cfe6ff', 3);
          }
        }
      }
    }

    updatePickups(dt) {
      const p = this.player;
      if (!p.alive) return;
      const reach = { x: p.x - 4, y: p.y - 4, w: p.w + 8, h: p.h + 8 };
      for (const c of this.cores) if (!c.got && hit(reach, c)) { c.got = true; this.collectCore(); }
      for (const c of this.coins) {
        if (c.got || !hit(reach, c)) continue;
        c.got = true;
        p.coins += c.amount;
        this.sound('coin');
        this.say(centerX(c), c.y - 4, '+' + c.amount, '#ffd86a');
      }
      for (const b of this.books) {
        if (b.got || !hit(reach, b)) continue;
        b.got = true;
        this.sound('book');
        this.collectCore();
        this.say(centerX(b), b.y - 6, 'LORE BOOK +1 CORE', '#d9b8ff');
      }
      for (const w of this.weaponPickups) if (!w.got && hit(reach, w)) { w.got = true; this.equip(w.key); }

      if (input.interact) {
        input.interact = false;
        const near = this.chests.find(c => !c.open && hit({ x: p.x - 14, y: p.y - 8, w: p.w + 28, h: p.h + 16 }, c));
        if (near && near.locked && p.coins < 15) {
          this.sound('locked');
          this.say(centerX(near), near.y - 22, 'NEEDS 15 COINS', '#ff9a8a');
        } else if (near) {
          if (near.locked) p.coins -= 15;
          near.open = true;
          this.sound('chest');
          this.heal(near.locked ? 45 : 25);
          if (near.locked) this.collectCore();
          this.burst(centerX(near), near.y, 10, '#ffd86a', 3);
        }
      }
      for (const fire of this.restFires) {
        if (Math.abs(centerX(p) - fire.x) < 90 && p.hp < p.maxHp && Math.floor(this.t / 500) !== Math.floor((this.t - dt) / 500)) this.heal(3);
      }
    }

    update(dt) {
      this.t += dt;
      if (this.freeze > 0) {
        this.freeze = Math.max(0, this.freeze - dt);
        if (this.shake > 0) this.shake = Math.max(0, this.shake - 0.35);
        return;
      }
      const p = this.player;
      if (p.alive && !this.result) this.time += dt;
      this.updatePlayer(dt);
      if (!this.result || this.result === 'complete') {
        this.enemies.forEach(e => this.updateEnemy(e, dt));
        this.updateBoss(dt);
        this.updateTraps(dt);
        this.updateProjectiles(dt);
        this.updatePickups(dt);
      }
      if (this.boss && !this.arenaLocked && p.alive && centerX(p) > this.arena.start + 160) this.lockArena();
      if (!this.result && p.alive && this.layout.end_x !== null && centerX(p) >= this.layout.end_x) this.result = 'complete';

      for (const q of this.particles) { q.life -= dt; q.vy += q.gravity; q.x += q.vx; q.y += q.vy; }
      this.particles = this.particles.filter(q => q.life > 0);
      for (const q of this.texts) { q.life -= dt; q.y -= 0.35; }
      this.texts = this.texts.filter(q => q.life > 0);
      this.enemies = this.enemies.filter(e => e.alive || e.deadT < 1600);
      if (this.shake > 0) this.shake = Math.max(0, this.shake - 0.35);
      if (this.banner && (this.banner.t -= dt) <= 0) this.banner = null;

      let target = clamp(centerX(p) - W / 2 + p.face * 40, 0, this.width - W);
      if (this.arenaLocked) target = this.arena.start;
      this.cam = clamp(this.cam + (target - this.cam) * (this.arenaLocked ? 0.08 : 0.12), 0, this.width - W);
    }
  }

  window.Ash = Object.assign(window.Ash || {}, {
    W, H, STEP, ATTACK_ANIM_MS, DEATH_MS, input, World, createPlayer, savePlayer, stageFor,
    centerX, centerY, clamp, rand,
    setConfig(c) { CFG = c; },
  });
  Object.defineProperty(window.Ash, 'config', { get: () => CFG });
})();
