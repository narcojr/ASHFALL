This folder already contains real pixel-art you supplied, wired into the
game automatically by src/assets.py:

  enemy_witch.png              - the Witch
  enemy_low_level_knight.png   - Low Level Knight
  enemy_royal_knight.png       - Royal Knight (also reused, palette-swapped,
                                  for Royal Knight II and the Dominion boss)
  weapon_sword_silver.png      - Gladius Voltaic
  weapon_spear_fire.png        - Pilum Rocketa
  weapon_dagger_purple.png     - Pugio Sparkspike
  weapon_trident_teal.png      - Hasta Longwire
  weapon_scythe_black.png      - Falx Rustbite
  weapon_axe_blood.png         - Securis Ashborn
  weapon_axe_silver.png        - Bipennis Warbreaker
  weapon_bow.png                - Arcus Scavenger (ranged - fires an arrow)
  tile_stone_gray.png          - "Cracked Quarry" biome ground/platforms
  tile_brick_gray.png          - "Ashfall Ruins" biome ground/platforms
  tile_stone_navy.png          - "Midnight Hollow" biome ground/platforms
  item_coin_stack.png          - Coin pickup
  item_book_skull.png          - Lore Book pickup (bonus Pixel Core)
  prop_lock.png                - drawn over locked chests
  prop_campfire.png            - decorative prop
  prop_tombstone.png           - decorative prop

Still missing (falls back to a colored placeholder block until you add
them): The Heir's own sprite. Drop these in to replace the placeholder for
each evolution stage:

  player_stage_0.png   -> The Exile (starting form)
  player_stage_1.png   -> The Wanderer
  player_stage_2.png   -> The Reclaimer
  player_stage_3.png   -> The Heir Ascendant

Any size PNG works - everything gets scaled to its configured size in
src/data.py automatically. To add a brand new enemy or weapon art asset,
add the PNG here and reference its filename in the "image"/"icon" field
of the matching entry in src/data.py.
