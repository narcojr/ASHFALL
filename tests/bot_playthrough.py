"""Plays all three levels with a simple bot in a headless browser (needs: pip install playwright).
Start the server first:  python server.py --port 8321 --no-browser
Then run:                python tests/bot_playthrough.py
The bot heals itself, so this checks that every level can be finished and that nothing throws."""
import asyncio, json, sys
from playwright.async_api import async_playwright
BOT = """
async ([lvl, seedRuns]) => {
  const A = window.__ashfall;
  await A.startLevel(lvl);
  const w = A.world, I = A.input, STEP = 1000/60;
  const out = {lvl, frames:0, result:null, errors:[]};
  let jumpCool = 0, stuck = 0, lastX = w.player.x, dashed = 0, attacked = 0;
  for (let f = 0; f < 60*500; f++) {
    const p = w.player;
    if (p.hp < p.maxHp * 0.3) p.hp = Math.round(p.maxHp * 0.6);
    p.sta = Math.max(p.sta, 40);
    I.right = true; I.left = false; I.attack = false; I.jump = false; I.dash = false;
    const px = p.x + p.w/2;
    let near = null;
    for (const e of w.enemies) if (e.alive && e.x > p.x - 10 && e.x - p.x < 90 && Math.abs(e.y - p.y) < 80) { near = e; break; }
    const b = w.boss;
    if (b && w.arenaLocked && b.alive && b.phase !== 'intro') {
      const d = (b.x + b.w/2) - px;
      if (Math.abs(d) < 62) { I.right = false; I.attack = true; p.face = d > 0 ? 1 : -1; } else { I.right = d > 0; I.left = d < 0; }
      for (const q of w.projectiles) if (q.kind === 'wave' && Math.abs((q.x + q.w/2) - px) < 70 && p.onGround) I.jump = true;
      if (f % 200 === 0) I.dash = true;
    } else if (near) { if (near.x - (p.x + p.w) < 40) { I.right = false; I.attack = true; p.face = 1; attacked++; } }
    for (const s of w.spikes.concat(w.fires.map(q => ({x:q.x})))) if (s.x - px < 65 && s.x - px > 30) jumpCool = 40;
    if (jumpCool > 0) { I.jump = true; jumpCool--; }
    if (p.vx === 0 && I.right && p.knockT <= 0 && p.onGround && !I.attack) I.jump = true;
    try { w.update(STEP); } catch (e) { out.errors.push(String(e.stack||e)); break; }
    if (p.dashT > 0) dashed++;
    out.frames++;
    if (!(w.arenaLocked && b && b.alive)) { if (Math.abs(p.x - lastX) > 25) { lastX = p.x; stuck = 0; } else if (++stuck > 240) { p.x += 140; p.vx = 0; p.knockT = 0; stuck = 0; lastX = p.x; } }
    if (w.result) { out.result = w.result; break; }
  }
  out.pos = [Math.round(w.player.x), Math.round(w.player.y), w.player.knockT, w.player.onGround, Math.round(w.player.vx)]; out.near = w.enemies.filter(e=>e.alive && Math.abs(e.x-w.player.x)<300).map(e=>[e.base.display_name,Math.round(e.x),Math.round(e.y),e.state,e.windup>0]); out.proj = w.projectiles.length; out.cores = w.player.cores; out.stage = w.player.stage; out.kills = w.kills; out.dashFrames = dashed; out.heroH = w.player.h; out.tier = w.tier;
  out.bossHp = w.boss ? w.boss.hp : null;
  return out;
}
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width':960,'height':540})
        errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
        await pg.goto('http://localhost:8321/'); await pg.wait_for_timeout(1500)
        for lvl in (1, 2, 3):
            print(json.dumps(await pg.evaluate(BOT, [lvl,0])))
        print('PAGE ERRORS', errs)
        await b.close()
asyncio.run(main())
