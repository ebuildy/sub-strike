# AGENTS.md — Bataille sous la mer

A kids' underwater side-scroller (it started as Space Invaders). You drive a black French attack sub
(Suffren / Barracuda class) and fight mines, octopuses, electric eels, enemy subs, boats, helicopters, drones and
kamikaze belugas.

## Project shape

- **One file: `index.html`.** HTML, CSS and all the JavaScript (about 1100 lines) live in it.
  There is no build, no dependencies and no assets: every graphic is drawn on a Canvas 2D and every
  sound is synthesized with Web Audio. Keep it that way: no libraries, images or extra files unless
  the owner asks.
- **Not a git repo.** Before a risky edit, back up the file to your scratch directory.
- **To run it:** `open index.html` on macOS. It works from `file://` and needs no server. Reopen it
  for the owner after each change.

## Language

- **The owner** writes in French or English, often short with typos ("bugger" means "bigger",
  "rocket" means torpedo).
- **The in-game UI text is French.** Keep it French, without accents: the existing strings avoid
  them, e.g. "Tres rapide".
- **Code, comments and identifiers are English.**

## Code layout (in file order)

1. **Setup**
   - Canvas is 1600x900 at `SCALE = 2`, so logical `W = 800`, `H = 450`. All game coordinates are
     logical pixels.
   - `SURFACE = 70` is the y of the sea surface.
   - The sky and water gradient is CSS on the `<canvas>`; the canvas itself is transparent.
2. **Audio**
   - Everything plays through `master` -> a compressor (so stacked explosions don't clip). Effects also
     feed `verb`, a generated dark reverb that gives the underwater echo.
   - Realistic effects are layered from `nz()` (filtered noise with a filter sweep), `os()` (oscillator
     with a pitch slide) and `bubbles()`, sent to `sfxOut(x, wet, life)`, which pans by screen x.
     - `sfx.boom(x, y)` sounds different under water (deep thump plus a bubble-pulse second kick and
       fizz) and in the air (crack and rumble).
     - Other layered effects: `shoot`, `pop`, `launch` (H-bomb ejection), `ignite` (rocket leaving the
       water), `mega`, `impact` (metal ring), `gun` and `die`.
     - Pass the position when you call them.
   - `tone(freq, dur, type, vol, slideTo)` and `noise()` stay for simple beeps, UI sounds and the
     music from `music()`.
   - The laser is a persistent oscillator, `laserSound(on)`. The CIWS is another persistent sound,
     `ciwsSound(on)`: noise chopped by a 75 Hz sawtooth LFO (one crack per round) plus a buzzing sawtooth,
     spin-up on start and a spin-down whine on stop. `sfx.surface`, `sfx.dive` and `sfx.raise` go with it.
3. **Shop**
   - `SHIPS` lists the ships with price, color, speed, cool, lives and double.
   - Coins, owned ships and the selected ship are saved with `load`/`save` in `localStorage`, always
     inside try/catch.
4. **Game state** and the main helpers:
   - Hit boxes: `playerBox()` and `allyBox(i)`.
   - Effects: `boom()`, `impact()` and `addMark()` (burning damage holes).
   - Spawning: `spawnEnemy()`, `spawnAir()` and `spawnBeluga()`.
   - Mine fuse: `proximityFuse()`.
   - Outcomes: `damagePlayer()` and `killEnemy()`. When an enemy dies, a `wreck` particle sinks or
     falls.
5. **Update:** `update()` is the whole simulation for one step.
6. **Draw:** `draw()` plus one `drawX()` per object:
   - Ships and weapons: `drawShip`, `drawCIWS`, `drawTorpedo`, `drawCharge`, `drawLaser` and `drawHBomb`.
   - Sea enemies: `drawMine`, `drawOcto`, `drawBeluga`, `drawDiver` and `drawEel`.
   - Surface and air enemies: `drawBoat`, `drawHeli` and `drawDrone`.
   - Scenery: `drawRock`.
   - `drawEnemy` dispatches by `e.type`.
7. **Loop**
   - The game logic runs at a **fixed timestep of 60 updates/second** (`STEP`, accumulator); drawing
     happens once per `requestAnimationFrame`.
   - All speeds and timers count in steps: 60 steps = 1 second.
   - Key handling is at the bottom.

## Conventions

- **Entities are plain objects in arrays:** `enemies`, `torps` (player torpedoes), `bullets` (CIWS rounds), `eShots` (enemy
  `torp` and `charge`), `missiles`, `pickups` and `particles`.
- **Removing an entity:** set `.dead = true`. The arrays are filtered once per step.
- **Enemies** have `{type, x, y, w, h, hp, pts}` plus fields for their own type.
  - Each step, the shared enemy loop moves every enemy left by `scroll` plus `e.vx`.
  - To add an enemy type:
    - Add a spawn path.
    - Add a behavior block in the enemy loop.
    - Add a `drawX()` function and a line in `drawEnemy`.
    - Check `impact()` debris colors and `addMark()`; the beluga, for example, gets no burn marks.
- **Particles** have `{kind, x, y, vx, vy, life, max, ...}`. Their kinds are fire, smoke, bubble,
  ring, drop, flash, spark, debris, wreck and freed (a beluga or swimmer swimming away
  without its bomb).
  - The list is capped at 500.
  - A new kind needs code in both the particle update and `drawParticles`.
- **The player sub** is drawn with `drawShip(x, y, color, dbl, 2.6)`.
  - Its center is at **(player.x + 46, player.y + 24)**.
  - It is rotated by **`player.vy * 0.1`** (tilt). Torpedoes, the laser and the propeller bubbles
    start from points rotated with that tilt, so if you change the sub's size or art, update
    those offsets too.
  - Bow tube is about 42 px ahead of center, nose about 48 px, stern about 56 px.
- **`drawShip`** has a 36 px reference box and a `scale` argument:
  - Allies are drawn at scale 1.6.
  - Enemy subs at scale 3, flipped.
  - The title and shop screens use the old, smaller scales.
- **Performance:** gradients are cached in `GR` where possible. Avoid per-frame allocations in hot
  draw code and avoid `shadowBlur`.
- **Comments:** short `//` comments that say why or what, in the same tone as the existing ones.

## Gameplay rules the owner asked for (keep them)

- **Controls** (the owner uses an AZERTY keyboard; keep the action keys together under the left hand)
  - Action keys are read by physical position (`e.code`, `keys.KeyF`, `keys.Space`), so they are the
    same keys on AZERTY and QWERTY: SPACE torpedo, F laser (hold), D decoys (unlimited, reloads in
    5 s), S H-bomb (8 per level).
  - Arrow keys move the sub (no WASD/ZQSD movement). The sub is heavy and has inertia.
  - Enter starts the game, S opens the shop from the title or game-over screen.
- **Surfacing and the CIWS:** the sub can rise to `SURF_Y = SURFACE - 25`, where the sail and the top of
  the hull stick out and the sub floats flat (`player.up` once `player.y < SURFACE - 16`).
  - A Phalanx CIWS (`player.ciws` 0..1, about 0.7 s) rises out of a hatch on the bow deck, at
    (player.x + 80.6, player.y + 23.4), forward of the sail. `drawCIWS` is drawn before the hull, clipped at the
    deck, so it comes out of the sub. It shows "CANON ANTI-AERIEN PRET !" when it is up.
  - While surfaced, SPACE fires the CIWS instead of torpedoes. It auto-aims (radar) at the nearest helicopter
    or drone within `CIWS_RANGE = 340`, turning 0.1 rad/step in the upper half only, with green lock brackets.
    One tracer every 2 steps at 11 px/step. `CIWS_HITS = 10` rounds take 1 hp (a heli dies in about 0.7 s).
    Rounds also destroy frigate shells still in the air, stop at the water, and are blocked by the eel's jam.
  - The top ally stays under water while the sub is surfaced.
- **Torpedoes** fire along the sub's tilt.
  - Torpedoes are drawn like real heavyweight torpedoes (`drawTorpedo`: ogive nose, cylinder, tail
    cone, cross fins, pump-jet with a spinning rotor), in local space with the nose toward +x.
  - The player's torpedoes are slim and fully dark.
  - Enemy torpedoes are gray with a red warhead and a yellow band. Enemy subs aim at the player's position at the
    moment they fire (clamped to about 70°) at a speed of 1.8 + 0.2 × level.
  - A torpedo dies at the surface (splash) or on the ground.
- **Laser:** red beam with an electric sound and short range (`LASER_RANGE = 150`), following the
  sub's tilt. It instantly destroys depth charges. It burns mines in 0.75 s (`MINE_BURN`) and
  everything else in 3 s per hp (`LASER_BURN`). Rocks block it.
- **Mines and depth charges** have a proximity fuse:
  - They arm within 38 px of the sub, then beep and blink for 0.4 s.
  - Then they explode with a 55 px blast, which damages the player and kills allies.
  - The sub can escape if it moves away fast.
- **Belugas** are kamikaze whales with a bomb strapped on their back.
  - **Count:** exactly `2 × level − 1` per level (1, 3, 5, ...), spread evenly over the level.
  - **Speed:** they chase the sub at 2.5 px/step, turn heavily and give up after 12 s.
  - **Torpedoes:** 1 torpedo kills one, but **each beluga dodges the first torpedo aimed at it, and
    only that one**.
  - **Their bomb** uses the same proximity fuse as the mines.
  - **They never die (kids' game):** when the bomb is destroyed or goes off, the whale swims away
    happily as a `freed` particle.
- **Combat swimmers (`diver`):** a frogman with a bomb on his back.
  - **Where they come from:** each boat or helicopter has a 35% chance to release one swimmer,
    once. It jumps off the deck or falls from the heli, splashes into the sea, then hunts like a
    beluga.
  - **How they hunt:** they use the shared `steer()` / `swim()` helpers at 1.7 px/step, are lured
    by decoys, use the proximity fuse, die from 1 torpedo and are worth 30 points.
  - **No dodging:** they don't dodge torpedoes.
  - **Nobody dies:** when the bomb is gone, the swimmer swims up to the surface and away.
- **Decoys (D):** each throw launches 2 decoys, one up and one down (about 86 px from the sub),
  that ping and drift back for 6 s.
  - **What they lure:** belugas, enemy torpedoes (which home in on them), mines (which break free of
    their chain) and depth charges, within 400 px (`DECOY_RANGE`).
  - **The fuse:** a lured threat ignores the sub for its fuse, so it arms and explodes only on the
    decoy. Its blast still hurts the sub if the sub is within 55 px.
  - **Timing:** thrown less than about 1 s before a beluga arrives, the decoys are too late.
- **Electric eels (`eel`), from level 2:**
  - **Spawning:** about 12% of `spawnEnemy` calls, one on screen at a time.
  - **Movement:** an eel undulates toward the sub's depth, and its yellow spots and crackles warn the
    player when it is close.
  - **Touching the sub:** no life lost, but an electric shock (`shockPlayer`) sets
    `player.jam = JAM_TIME` (600 steps = 10 s).
  - **While jammed:** torpedoes (allies too), the laser and the H-bomb are off. The trigger keys
    buzz (`sfx.denied`), cyan arcs crackle over the hull, and the HUD shows "ARMES EN PANNE Ns".
    Decoys still work.
  - **After the shock:** each eel discharges once (`e.spent`), then dives away dim. 2 torpedoes kill
    it (40 points).
- **Drones** don't drop bombs: they fire a laser (`droneLaser`), only when the sub is near the
  surface (`player.y < SURFACE + 70`, within 260 px horizontally).
  - The drone's eye turns red and a dotted line tracks the sub for 0.5 s, then locks for 0.5 s
    (`DRONE_LOCK`), then a short red beam fires for 1/3 s and ends just past the locked point.
  - **To dodge:** dive, or move away after the lock. The water stops the beam 100 px below the surface
    (`DRONE_DEPTH`). The beam costs 1 life and kills allies it crosses; decoys don't fool it.
- **Allies:** you get an ally sub every 10 kills, up to 2. After that, every 10 kills gives an
  extra life.
- **Enemy boat** is a gray stealth frigate modeled on Naval Group's FDI (inverted bow, pyramid mast,
  radome, hangar, helipad), facing left, `w: 110`. Smoke comes from the exhaust at (x + 61, y).
  - One frigate always opens each level (`startLevel`); after that `boatChance = 0.25`, max one at a time.
  - **Gun:** the 76 mm gun on the bow turns toward the sub (`e.gunA`, 0.15 to 1.2 rad down) and fires a
    `shell` eShot every ~5 s (`max(200, 315 - 15 × level)` steps), only when the sub is ahead of the bow. Shells fly ballistic, slow down
    in the water, hurt the sub or kill allies, and are not lured by decoys.
  - **Helicopter:** each frigate spawns a heli parked on its flight deck (`parked`, if no other heli is
    around). It lifts off 1 to 3 s after the frigate is on screen (`lift`), then flies as a normal heli.
    It takes off at once if the frigate is sunk.
- **Damaged enemies** smoke, leak bubbles, get knocked back, and tilt or list.

## How to test (no test suite)

1. **Syntax check:**
   ```sh
   sed -n '/<script>/,/<\/script>/p' index.html | sed '1d;$d' > /tmp/g.js && node --check /tmp/g.js
   ```
2. **Behavior:** open the page in Chrome (DevTools or another browser tool) and drive the
   simulation by hand with an injected script. The top-level `let`/`function` names are reachable
   from evaluated scripts.
   - **Start a game properly** with `reset(); state = 'play';`. Setting only `state` leaves `scroll`
     undefined, which turns `camX` into NaN.
   - **Call `update()` in a loop** instead of waiting for real time: rAF is throttled in background
     tabs.
   - **For a stable screenshot:** call `draw()` once, then `draw = () => {}` so the live loop does
     not paint over it.
   - **Keep the scene quiet:** reset `spawnTimer = 99999` and `airTimer = 99999` each step and set
     `belugaLeft = 0`.
   - **Keep the player alive:** set `player.inv` and `lives`.
   - **Report numbers:** distances, lives lost, steps until an event, spawn counts per level. Not
     just "it works".
3. **Reopen the game** for the owner with `open index.html`.

## Balance notes

- The owner tunes by feel and changes their mind often. Make the requested change exactly, then
  mention the side effects.
  - Example: 2x bigger subs make the player easier to hit.
- Offer a tuning knob (distance, delay, speed) in one short line instead of asking questions first.
