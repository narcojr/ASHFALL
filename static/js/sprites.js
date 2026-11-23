// Loads the sprite sheets from static/assets/art and draws single frames from them.
(function () {
  'use strict';
  const Ash = window.Ash = window.Ash || {};
  const images = {};
  const masks = new Map();
  let art = null;

  const FOES = ['footman', 'royal', 'elite', 'witch', 'boss'];
  const SHEETS = ['ground', 'stone', 'cap', 'fire', 'fire_big', 'coin', 'core', 'book', 'chest', 'weapons',
    'bg_clouds', 'bg_mist', 'bg_forest', 'bg_ruins',
    'prop_rock_big', 'prop_rock', 'prop_rock_small', 'prop_tree', 'prop_pillar', 'prop_tombstone', 'prop_sign', 'prop_fence',
    'prop_ice_plant', 'prop_lantern'];
  const UI = ['btn', 'btn_hover', 'btn_pause', 'panel', 'icons', 'logo'];

  function fileList() {
    const names = UI.slice();
    for (const tier of Object.keys(art.tiers)) {
      for (let s = 0; s < 4; s++) names.push(`hero_t${tier}_s${s}`);
      FOES.forEach(f => names.push(`foe_${f}_t${tier}`));
      SHEETS.forEach(n => names.push(`${n}_t${tier}`));
    }
    return names;
  }

  function load(meta, onProgress) {
    art = meta;
    const urlFor = name => (window.DECK && window.DECK.images && window.DECK.images[name]) || `assets/art/${name}.png`;
    const names = fileList();
    let done = 0;
    const tick = () => { done++; if (onProgress) onProgress(done, names.length); };
    const jobs = names.map(name => new Promise(resolve => {
      const img = new Image();
      img.onload = () => { images[name] = img; tick(); resolve(); };
      img.onerror = () => { console.warn('missing art', name); images[name] = new Image(); tick(); resolve(); };
      img.src = urlFor(name);
    }));
    const font = document.fonts ? document.fonts.load('16px AshPixel') : Promise.resolve();
    return Promise.all(jobs.concat([font.catch(() => {})])).then(() => { if (onProgress) onProgress(names.length, names.length); });
  }

  const pixelSize = tier => art.tiers[String(tier)].pixel;
  const get = (name, tier) => images[tier ? `${name}_t${tier}` : name];

  // a white copy of a sprite sheet, used for hit flashes
  function mask(img) {
    if (masks.has(img)) return masks.get(img);
    const c = document.createElement('canvas');
    c.width = img.width || 1; c.height = img.height || 1;
    const g = c.getContext('2d');
    g.drawImage(img, 0, 0);
    g.globalCompositeOperation = 'source-in';
    g.fillStyle = '#ffffff';
    g.fillRect(0, 0, c.width, c.height);
    masks.set(img, c);
    return c;
  }

  // Draw frame (col, row) of a sheet whose cells are `cellSize` design pixels wide.
  // (x, y) is the top-left corner of the cell on screen. A flipped sprite mirrors around `pivot`.
  function frame(g, img, tier, cellSize, col, row, x, y, flip, pivot) {
    if (!img.width) return;
    const n = cellSize / pixelSize(tier);
    g.save();
    if (flip) {
      g.translate(pivot, 0);
      g.scale(-1, 1);
      x -= pivot;
    }
    g.drawImage(img, col * n, row * n, n, n, x, y, cellSize, cellSize);
    g.restore();
  }

  Ash.sprites = { load, get, mask, frame, pixelSize, images, get art() { return art; } };
})();
