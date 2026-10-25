# AGENTS.md — Battle Beneath the Sea

An underwater side-scroller for **military IT developers** (it started as a kids' game, then Space Invaders). You drive a black French attack sub
(Suffren / Barracuda class) and fight mines, octopuses, electric eels, enemy subs, boats, helicopters, drones and
kamikaze belugas.

## Project shape

- **One file: `index.html`.** HTML, CSS and all the JavaScript (about 2550 lines) live in it.
  There is no build, no dependencies and no assets: every graphic is drawn on a Canvas 2D and every
  sound is synthesized with Web Audio. Keep it that way: no libraries, images or extra files unless
  the owner asks.
- **Git repo** `ebuildy/sub-strike` (public, branch `main`). Commit or push only when the owner asks. Before a
  risky edit, back up the file to your scratch directory.
- **To run it:** `open index.html` on macOS. It works from `file://` and needs no server. Reopen it
  for the owner after each change.
- **Published on GitHub Pages:** https://ebuildy.github.io/sub-strike/ serves `index.html` from the root of
  `main`. Every push to `main` goes live about a minute later, so push only a tested, working game.
  - The site is static and read-only: no backend, so scores, coins and ships stay in each player's `localStorage`.
    A shared leaderboard would need an outside service.
  - Keep every path relative and the game working from `file://` and from the `/sub-strike/` subpath.

## Language

- **The owner** writes in French or English, often short with typos ("bugger" means "bigger",
  "rocket" means torpedo).
- **The in-game UI text is English, in military vocabulary (owner: very important).** All messages, HUD, title,
  shop and end screens: e.g. "VAMPIRE! INCOMING MISSILE", "SPLASH ONE HELO", "WEAPONS OFFLINE", "MISSION 2", "ARMORY".
  Keep new strings short, uppercase for messages, plain ASCII. The owner still writes requests in French or English.
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
     - Other layered effects: `shoot`, `pop`, `launch` (H-bomb ejection: thump, gas blast, hiss), `motor` (the
       guided H-bomb's rocket lighting after 20 steps: crack, roar, `crackle()` pops, muffled under water), `ignite` (rocket
       leaving the water, with crackle), `bubbles` (bubble screen), `mega`, `impact` (metal ring), `sam` and `droneOut` (Rampart launches) and `die`.
     - Pass the position when you call them.
   - `tone(freq, dur, type, vol, slideTo)` and `noise()` stay for simple beeps, UI sounds and the
     music from `music()`.
   - **Boss theme (`bossMusic()`, owner: "perfect")** plays instead of `music()` while a boss is alive, from its first
     beat (`bossStep = 0` in `spawnBoss`). Original swashbuckler-style tune (owner asked for Pirates of the Caribbean;
     do not copy that copyrighted melody): 6/8 in D minor, `BM_STEP = 11` steps per eighth (~110 BPM), Dm-Dm-Bb-C-Dm-Gm-A-A.
     Cello eighths, low strings, big drum and brass hits on 1 and 4, snare, cymbal, a drum roll in bar 8, and a lead
     (`BM_LEAD`). Voices go through `syn()` (filtered oscillator) to the music bus `mbus` at `BM_VOL = 0.4` (owner: softer).
   - Storm sounds: `sfx.thunder(x, delay)` (crack plus rolling rumble) and `rainSound(v)`, a persistent filtered-noise hiss
    whose volume follows `storm` (muted on pause and outside play/briefing).
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
   - Spawning: `spawnEnemy()`, `spawnAir()`, `spawnBeluga()` and `spawnBoss()`.
   - Mine fuse: `proximityFuse()`.
   - Outcomes: `damagePlayer()` and `killEnemy()`. When an enemy dies, a `wreck` particle sinks or
     falls.
5. **Update:** `update()` is the whole simulation for one step.
6. **Draw:** `draw()` plus one `drawX()` per object:
   - Ships and weapons: `drawShip`, `drawCIWS`, `drawTorpedo`, `drawCharge`, `drawLaser`, `drawHBomb`, `drawRampart`, `drawASM`, `drawSAM`, `drawShkval` and `drawBubbleWall` (boss).
   - Sea enemies: `drawMine`, `drawOcto` (drawn at `OCTO_K = 0.5`, owner: 2x smaller; box 17x15), `drawBeluga`, `drawDiver`, `drawEel` and `drawBoss`.
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
  `torp`, `charge`, `asm`, `sam`, `atr`, `cm`, and the boss's `brk` and `bcl`), `missiles`, `pickups` and `particles`.
- **Removing an entity:** set `.dead = true`. The arrays are filtered once per step.
- **Enemies** have `{type, x, y, w, h, hp, pts}` plus fields for their own type.
  - Each step, the shared enemy loop moves every enemy left by `scroll` plus `e.vx`.
  - To add an enemy type:
    - Add a spawn path.
    - Add a behavior block in the enemy loop.
    - Add a `drawX()` function and a line in `drawEnemy`.
    - Check `impact()` debris colors and `addMark()`; the beluga, for example, gets no burn marks.
- **Particles** have `{kind, x, y, vx, vy, life, max, ...}`. Their kinds are fire, smoke, bubble,
  ring, drop, flash, spark, debris and wreck.
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
- **Messages (`flash = { msg, t, danger }`)** show on a dark dashboard strip at the bottom center, sized to the text,
  with a blinking LED. **Danger messages** (`danger: true`, `dashRed`) are dark red with a fast red LED: threats to
  the sub or its weapons (VAMPIRE, EMP HIT, DRONE DOWN, SAM LAUNCH, LOCKED TARGET). **Everything else is orange**
  (`#e07a1a`): status and good news (CIWS ONLINE, SPLASH ONE..., MISSION n). An info message must not overwrite a
  live danger message on purpose (use `if (!flash)` or check `flash.danger`).
  - **"LOCKED TARGET - <TORPEDO / MISSILE / KAMIKAZE WHALE / COMBAT SWIMMER / DRONE> INBOUND":** the threat warning
    remembers the closest threat object and shows this once per threat (`warned`), the moment it locks onto the sub.
    Anti-ship missiles are pre-marked `warned`, since their launch already shows VAMPIRE. `dashA` (0..1, eased 0.12 per step in `update`) fades and slides it in and
  out; `dashMsg` keeps the last text so it can fade out after `flash` is cleared. Keep new messages short.
- **Comments:** short `//` comments that say why or what, in the same tone as the existing ones.

## Gameplay rules the owner asked for (keep them)

- **Audience and feel (owner):** players are military IT developers, so tone, vocabulary and visuals can be
  military and realistic rather than childish. But the game must stay **as easy to pick up as Mario**: one key per
  action, instant feedback, short missions, forgiving early missions, new mechanics introduced one mission at a time
  (see progressive missions). Do not add complexity to mission 1.

- **Progressive missions (owner: the game was too complicated).** `UNLOCK = { decoys: 2, swimmers: 2, bubbles: 3, drone: 3 }`:
  - Mission 1: torpedoes, laser, H-bomb, CIWS only. No belugas, no combat swimmers.
  - Mission 2: decoys (D) are issued; belugas, combat swimmers (and, as before, electric eels) appear.
  - Mission 3: bubble screen (E) and air drone (W) are issued; enemy subs start using decoys.
  - A weapon not issued yet: its HUD row is hidden, and its key buzzes with "NOT ISSUED BEFORE MISSION n" (`locked()`).
    The help page says "D issued from mission 2, E and W from mission 3".
  - **Mission briefing (`state = 'brief'`, `drawBrief`):** after "MISSION n ACCOMPLISHED", the next mission starts frozen
    under a briefing panel listing `NEWS[level]` (green key boxes for new weapons, red "!" boxes for new threats; from
    mission 4 a generic "HEAVIER RESISTANCE" line). ENTER deploys, or it starts by itself after `BRIEF_TIME = 300`
    steps (5 s, countdown shown). Add a line to `NEWS` whenever a feature is tied to a mission.
  - **From mission 5 (`LIFE_LEVEL`):** `startLevel` gives +1 life when the sub has fewer than 3 ("RESUPPLY: +1 LIFE"),
    and `LIFE_DROPS = 2` life pickups (`type: 'life'`, a pulsing heart in a ring) come in like coins at 30% and 65% of
    the mission: +1 life each ("MEDEVAC CRATE: +1 LIFE"). Tested: mission 5 with 2 lives starts with 3, with 3 stays 3;
    both crates dropped and were collected; none in mission 4. A `+` line in `NEWS` is drawn green like a weapon.
  - **Bosses at the end of missions 4 and 5:** see Bosses below.
  - **Mission 1 is training (owner):** passing it once sets `trained` (`localStorage` key `si_trained`, saved by `save()`).
    From then on every new game (`reset()`) starts at mission 2, and `redeploy()` opens it on the mission 2 briefing
    (`state = 'brief'`). Retries still restart the failed mission. Tested: fresh browser -> mission 1; game over before
    passing it -> mission 1; after it -> mission 2 with briefing, also after a page reload.
  - **Mission retries (`RETRIES = 3`, owner):** when the sub's hearts run out, one of 3 game lives is spent
    (`retries--` in `damagePlayer`). With lives left, the lost screen shows "SUB LOST - MISSION n FAILED", "n LIVES
    REMAINING" with hearts, and ENTER/tap (`redeploy()` -> `retryLevel()`) restarts **that mission** with a fresh sub,
    full hearts and the score/kills/allies it started with (`lvlSave`, taken at the end of `startLevel`). With none left:
    "GAME OVER - NO LIVES REMAINING", ENTER starts a new game (mission 1, or mission 2 once trained, see below). These lives are **only shown on the lost
    screen**, never on the HUD. The armory opened from the lost screen returns to it (`shopFrom`).

- **Controls** (the owner uses an AZERTY keyboard; keep the action keys together under the left hand)
  - Action keys are read by physical position (`e.code`, `keys.KeyF`, `keys.Space`), so they are the
    same keys on AZERTY and QWERTY: SPACE torpedo, F laser (hold), D decoys (unlimited, reloads in
    5 s), E bubble screen (5 per level), S H-bomb (8 per level).
  - **W air drone goes by letter** (`e.key === 'w'`), not by position: on the owner's AZERTY the W is bottom left.
  - Arrow keys move the sub (no WASD/ZQSD movement). The sub is heavy and has inertia.
  - Enter starts the game, S opens the shop from the title or game-over screen.
  - **ESC pauses** (`state = 'pause'`): `update()` returns at once (everything frozen, laser and CIWS sounds off,
    held keys cleared), and `draw()` paints the frozen game, a dark veil, then the welcome help page `drawHelp(true)`
    ("GAME PAUSED", "ESC or ENTER to resume"). The title screen uses the same `drawHelp(false)`.
  - **CLEAR DATA (pause screen, owner):** a red button bottom right (`CLEAR_BTN`), mouse click or tap. The first press
    arms it ("CONFIRM?" for 3 s, `clearArm`), the second calls `clearData()`: removes every `si_*` key (not
    `localStorage.clear()`: the ebuildy.github.io origin is shared with other pages), resets coins, ships and `trained`,
    and goes back to the title screen.
  - **Welcome screen (`drawHelp`) is full-canvas** "THREAT RECOGNITION // CLASSIFIED": a dark veil with a faint
    sonar grid, the title, then **3D** models of our sub, the enemy sub and the frigate (`SHOWCASE`), then 8 **2D**
    threat cards (`ROSTER`: mine, octopus, eel, whale, swimmer, helo, drone, anti-ship missile, each drawn with the
    game's own `drawX`, scaled into a clipped card, with a one-line tip and "FROM MISSION n" in red when locked
    early), then the controls and ENTER / ARMORY / coins. **Add any new enemy to `ROSTER` (2D) or `SHOWCASE` (3D).**
    The grid is full (4x2); the bosses are not on it, they are announced by the mission 4 and 5 briefings.
  - **Tiny 3D engine** (no library): meshes are face lists `{ p: [[x,y,z]...], c: [r,g,b] }` (x = length, y = up),
    built once into `MESH` by `subMesh(hull, fins)` (hull of revolution, sail, planes, X rudders) and `frigateMesh()`
    (lofted hull, superstructure, pyramid mast, hangar, radome, Rampart) with `box3`. `draw3D(mesh, cx, cy, scale,
    yaw, pitch)` rotates, flat-shades (two-sided Lambert), sorts faces far to near and fills them; no culling.
    The models sway ±0.32 rad around a 3/4 view (pitch 0.22) instead of spinning. Cost: about 1 ms per frame.
- **Mobile / tablet (`MOBILE`):** detected by `matchMedia('(pointer: coarse)')` (or `?mobile=1` to test on desktop);
  adds `body.mobile`. Landscape and full screen only: the canvas fills the screen (16:9, letterboxed), the first tap
  in a menu calls `goFullscreen()` (Android: fullscreen + landscape lock; iPhone Safari has no fullscreen API), and
  portrait shows the `#rotate` overlay and pauses the game. Hiding the page also pauses it.
  - **Easier:** spawn gaps (sea and air) x`MOB_SPAWN = 1.6`, belugas `level - 1` instead of `2 × level − 3`. No laser
    and no air drone (`UNLOCK.drone = Infinity`, the NEWS line and laser mentions are left out). Enemy drones stay.
    Tested on mission 2: 10 sea / 3 air spawns vs 15 / 5 on desktop.
  - **Touch controls** (bottom of the script): a floating stick anywhere on the left 55% (`stick`, analog -1..1,
    mixed into `tx/ty`), and round buttons on the right (`BTN`): FIRE (hold = `keys.Space`, so CIWS when surfaced),
    H-BOMB, DECOY (mission 2+), BUBBLE (mission 3+), plus a pause button top left. `drawTouch()` draws them; the
    keyboard HUD weapon rows are hidden on mobile because the buttons show the ammo.
  - **Menus:** taps act on touchend, only for a touch that began in that same state (holding FIRE when the sub dies
    must not redeploy). `touchBtn()` draws the ARMORY / BACK buttons; in the shop, tap a row to select, again to buy.
- **Surfacing and the CIWS:** the sub can rise to `SURF_Y = SURFACE - 25`, where the sail and the top of
  the hull stick out and the sub floats flat (`player.up` once `player.y < SURFACE - 16`).
  - A Phalanx CIWS (`player.ciws` 0..1, about 0.7 s) rises out of a hatch on the bow deck, at
    (player.x + 80.6, player.y + 23.4), forward of the sail. `drawCIWS` is drawn before the hull, clipped at the
    deck, so it comes out of the sub. It shows "CIWS ONLINE" when it is up.
  - While surfaced, SPACE fires the CIWS instead of torpedoes. It auto-aims (radar) at the nearest helicopter
    or drone within `CIWS_RANGE = 340`, turning 0.1 rad/step in the upper half only, with green lock brackets.
    One tracer every 2 steps at 11 px/step. `CIWS_HITS = 10` rounds take 1 hp (a heli dies in about 0.7 s).
    Rounds also destroy the Rampart's air/air missiles (`sam`), stop at the water, and are blocked by the eel's jam.
  - The top ally stays under water while the sub is surfaced.
- **Threat warning:** each step `update()` finds the closest threat aimed at the sub, within `WARN_RANGE = 400`
  px (`player.threat`, or Infinity when there is none). Threats are:
  - an anti-ship missile homing on the surfaced sub;
  - an enemy torpedo whose course passes within 40 px of the sub;
  - a beluga or swimmer with its bomb, hunting the sub (not one lured by a decoy, falling from a heli or giving up);
  - a drone, while the sub is in its laser zone (`player.y < SURFACE + 70`) or while it aims or fires.
  - **Beep:** a short square beep every `6 + 48 × dist / 400` steps (about 0.9 s far away, 0.1 s close), higher
    and louder under `WARN_RED = 150` px.
  - **Light:** `drawWarnLight` draws a lamp on the sail at (player.x + 66.3, player.y + 17.5), inside the sub's
    tilt transform. It is green when clear, orange when something is aimed at the sub, and red and bigger when
    close; it blinks with the beep.
- **Target lock and guided H-bomb (S):** `player.lock` is always the single closest enemy `sub` or `boat` on screen,
  marked with orange corner brackets and "TARGET" (dimmed when there are no H-bombs left or the sub is jammed). A
  short chirp plays when the lock changes.
  - **Guided flight (`m.guided`):** the bomb is ejected upward for 20 steps, then the motor lights and it turns
    0.08 rad/step onto the target (2.8 px/step under water, 4 in the air). It splashes when it crosses the surface.
  - **Retargeting:** if the target dies, it takes the next lock or flies straight.
  - **Blast (owner's rule: not too powerful):** it explodes (`megaBoom(x, y, victim)`) on the sub or boat it touches,
    or on the ground. The big flash, rings and shake stay, but it kills **only that one enemy**: no area damage,
    it does not clear enemy shots, and it flies straight past helicopters and drones without hurting them.
  - **Nothing locked:** the old unguided path, straight up. It only kills a frigate it flies into; when it
    goes off in the sky it hurts nobody.
- **Enemy sub countermeasures, from level 3 (`SUB_CM_LEVEL`):** each player torpedo whose course hits an enemy sub
  within `SUB_CM_RANGE = 220` px, and each guided H-bomb aimed at it under water, gets one random roll (`t.cm` /
  `m.cm`, `SUB_CM_SAVE = 0.5`). On a yes the sub throws a red decoy (`cm` eShot, `drawCM`, double ping,
  "ENEMY DECOY DEPLOYED", one every 20 steps). It drifts and pings for 5 s; the weapon gets `lure` and turns onto it
  (torpedo 0.07 rad/step, H-bomb as usual) and blows up there (the H-bomb's megaBoom kills nobody). Tested at
  level 3: 26/60 torpedoes and 16/30 H-bombs decoyed; level 2: 0/60.
- **Air drone (W), `launchDrone()` / `updateMyDrone()`:** 1 per level (`droneAmmo`), blocked while jammed. HUD: "W" with a
  small dark drone.
  - **Launch:** a dark gray rocket with a green band (`droneRocket`) rises from the sub (thump), bursts at the surface
    (pop, splash, smoke, "DRONE AWAY") and throws `myDrone`: a `drawDrone` with `mine: true` (dark gray `GR.droneMine`,
    green status, arm and lens lights, green laser via `drawLaser({ green })`). It is not in `enemies`.
  - **Targets:** the closest enemy drone first. It stands off 130 px and fires a laser duel: it aims for `MY_DRONE_AIM = 54`
    steps (locks for the last 18), then a 15-step green beam that kills the drone ("SPLASH ONE DRONE"), and waits 50 steps.
    With no enemy drone, it dives kamikaze into a helicopter at 4.5 px/step ("DRONE ON ATTACK RUN", then "SPLASH ONE HELO"),
    and is spent. With nothing to fight, it waits over the sub.
  - **Enemy drones** within 260 px aim at our drone instead of the sub (`e.atMine`). Their beam kills it
    (`killMyDrone`: boom and a falling wreck, "DRONE DOWN"). Tested 1 vs 1: we win 36 of 60 duels
    (aim 48 gave 39/40, aim 60 gave 19/40).
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
  - **Count:** exactly `2 × level − 3` per level from mission 2 (0, 1, 3, 5, ...), spread evenly over the level.
  - **Speed:** they chase the sub at 2.5 px/step, turn heavily and give up after 12 s.
  - **Torpedoes:** 1 torpedo kills one, but **each beluga dodges the first torpedo aimed at it, and
    only that one**.
  - **Their bomb** uses the same proximity fuse as the mines.
  - **Neutralized, no happy escape (owner):** when the bomb is destroyed (torpedo, laser, bubble screen) the whale
    is removed in the blast and scored; when its bomb goes off, it dies in its own blast (no score). The old `freed`
    particle and `freeSwimmer()` are gone.
- **Combat swimmers (`diver`):** a frogman with a bomb on his back.
  - **Where they come from:** from mission 2, each boat or helicopter has a 35% chance to release one swimmer,
    once. It jumps off the deck or falls from the heli, splashes into the sea, then hunts like a
    beluga.
  - **How they hunt:** they use the shared `steer()` / `swim()` helpers at 1.7 px/step, are lured
    by decoys, use the proximity fuse, die from 1 torpedo and are worth 30 points.
  - **No dodging:** they don't dodge torpedoes.
  - **Neutralized** the same way as the whale: no swim-away.
- **Decoys (D):** each throw launches 2 decoys, one up and one down (about 86 px from the sub),
  that ping and drift back for 6 s.
  - **What they lure:** belugas, enemy torpedoes (which home in on them), mines (which break free of
    their chain) and depth charges, within 400 px (`DECOY_RANGE`).
  - **The fuse:** a lured threat ignores the sub for its fuse, so it arms and explodes only on the
    decoy. Its blast still hurts the sub if the sub is within 55 px.
  - **Timing:** thrown less than about 1 s before a beluga arrives, the decoys are too late.
- **Bubble screen (E), `bubbleBurst()`:** defense only, `BUBBLE_AMMO = 5` per level, `BUBBLE_COOL = 45` steps
  between bursts, works while jammed. A burst of 90 bubbles and two rings, and `sfx.bubbles`.
  - Everything under water within `BUBBLE_RANGE = 120` px of the sub center is pushed away (`e.blow`, `e.bx/e.by`,
    decaying 0.9 per step).
  - Small enemies (`BUBBLE_SMALL`: mine, beluga, swimmer, octopus) get speed 7, their fuse is cleared, they skip
    their AI and contact for 26 steps, then die with `killEnemy(e, true)`: `safe` means the swimmer's bomb can't
    hurt the sub. Belugas and swimmers are neutralized like any other kill. They count as kills.
  - Big ones (sub, eel) get speed 5 for 30 steps, keep their AI and take no damage. Boats, aircraft and rocks
    are ignored.
  - Enemy torpedoes in range are turned straight away at the same speed; depth charges under water are
    destroyed (+5).
  - Blown swimmers are not counted by the threat warning. HUD: "E" with 5 bubble circles.
- **Electric eels (`eel`), from level 2:**
  - **Spawning:** about 12% of `spawnEnemy` calls, one on screen at a time.
  - **Movement:** an eel undulates toward the sub's depth, and its yellow spots and crackles warn the
    player when it is close.
  - **Touching the sub:** no life lost, but an electric shock (`shockPlayer`) sets
    `player.jam = JAM_TIME` (600 steps = 10 s).
  - **While jammed:** torpedoes (allies too), the laser and the H-bomb are off. The trigger keys
    buzz (`sfx.denied`), cyan arcs crackle over the hull, and the HUD shows "WEAPONS OFFLINE Ns".
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
  - **Rampart turret** (Naval Group's modular launcher) replaces the old 76 mm gun on the bow. `drawRampart` draws a
    gray block of 4 modules (seams, tube mouths on the front face, electro-optical sensor with a blinking red
    designator) on a pedestal at (x + 14, y + 11). It turns 0.1 rad/step (`e.rpA`, upper half only, level toward
    a target below the deck), fires only when aligned, recoils (`e.rpKick`) and puffs smoke. Priority of jobs:
    0. **Ship defense (`atr` eShot), first priority:** each player torpedo whose course hits the frigate within
       `RAMPART_ASW = 260` px, and each guided H-bomb aimed at it under water, gets one random roll
       (`t.atr` / `m.atr`, `RAMPART_SAVE = 0.5`). On a yes the Rampart fires an anti-torpedo rocket ("ENEMY COUNTERMEASURE",
       one every 20 steps): it arcs over, dives into the sea and homes (0.16 rad/step) until it blows up on the weapon
       ("TORPEDO INTERCEPTED" or "H-BOMB INTERCEPTED"). It never hurts the sub. Drawn with `drawSAM`.
       Tested: 27/60 torpedoes and 18/30 guided H-bombs stopped.
    1. **Air/air (`sam` eShot):** at an H-bomb within `RAMPART_AA = 480` px that is rising (heard by sonar from
       160 px below the surface), one missile per bomb (`m.samBy`), "SAM LAUNCH - H-BOMB TARGETED". The SAM flies at up to
       6 px/step, loiters slowly over the bomb while it is under water, then strikes when it comes out
       ("H-BOMB INTERCEPTED", the bomb is lost and does not go off). It never hurts the sub, dies in the water
       or after 4 s. The CIWS targets it like an anti-ship missile. Tested: about half of the unguided (sky)
       bombs get intercepted; guided bombs on the frigate itself come out right beside it, so only the ship-defense roll can stop them.
    2. **Air/sea (`asm` eShot):** see below.
    3. **Drones:** a `drone` enemy launched from a module (`climb: 70` steps up to its flying height, no laser
       while climbing), first after 2 to 4 s, then every ~11 s (`max(420, 720 - 30 × level)` steps), only while
       fewer than 2 drones are on screen.
  - **Anti-ship missiles (`asm` eShot):** only while the sub is surfaced (`player.up`), the Rampart fires one, lofted
    toward the sub, first after 1.5 s, then every ~4.5 s (`max(150, 270 - 15 × level)` steps). There is an alarm and
    "VAMPIRE! INCOMING MISSILE". The missile boosts for 12 steps, then turns (0.1 rad/step, up to 3.4 px/step) and dives
    onto the sail. If the sub dives, it loses its lock and falls into the sea. A hit costs 1 life.
    - **The CIWS targets incoming missiles first**, before aircraft; `ASM_HITS = 3` rounds destroy one
      ("MISSILE SPLASHED", 20 points). Decoys don't lure missiles. Drawn by `drawASM`.
  - **Helicopter:** each frigate spawns a heli parked on its flight deck (`parked`, if no other heli is
    around). It lifts off 1 to 3 s after the frigate is on screen (`lift`), then flies as a normal heli.
    It takes off at once if the frigate is sunk.
- **Aircraft art (owner: realistic, gray):** `drawHeli` is a navy-gray NH90 / Caiman-style naval helicopter
  (rounded nose, tinted cockpit, engine housing, sliding door, sponson, wheels, swept fin, tail rotor, red
  anti-collision light; two foreshortened main blades over a blur disc, folded back while `parked`). `drawDrone` is a
  gray military quadcopter (front and rear arms, motors, prop blur, GPS puck, antenna, landing legs, gimbal ball whose
  lens turns red when it aims; the laser still starts at (x + 12, y + 12)). Both draw in local space with cached
  gradients `GR.heli` and `GR.drone`.
- **Creature art (owner: realistic, no cartoon):** the beluga is gray-white with mottled skin, a dorsal ridge, a
  short beak, a straight mouth line and a small dark eye (no smile, blush or glossy eye). The octopus is a common
  octopus: red-brown mottled mantle swept back, gold eye with a slit pupil, tapering curled arms with suckers
  (`GR.octo`). The combat swimmer wears black fins, a dark tactical mask and a rebreather.
- **Damaged enemies** smoke, leak bubbles, get knocked back, and tilt or list.

- **Weather (owner): storm from mid-mission 2 to mid-mission 3, heavy storm from mid-mission 4 to mid-mission 5.**
  `stormTarget()` gives 1 (`level === 2 && dist >= levelLen / 2` or `level === 3 && dist < levelLen / 2`), 2 (same for
  levels 4 and 5) or 0. `storm` (0..2) eases 0.004 per step toward it (~4 s per unit); `startLevel` sets it at once
  (missions 3 and 5 and their retries start in the storm). `heavy()` = `storm - 1` clamped at 0. Messages (info, never
  over a danger message): "WEATHER ALERT: STORM FRONT", "STORM WARNING: SEA STATE 7", "STORM CLEARING". Missions 1 and
  6+ are clear. Visual and sound only, no gameplay effect (hit boxes and `SURFACE` are unchanged).
  - `drawBackground`: dark sky overlay, sun and white clouds fade out, two layers of dark storm clouds, a gloomy veil
    on the sea, sun rays hidden. `drawRain()` (after the particles, before the HUD): 150 slanted streaks (320 and more
    slant in the heavy storm) plus splash rings, positions from `hash()` and `T` (no allocations).
  - Lightning: above `storm > 0.8`, a 1/360 chance per step (~6 s; 1/140 in the heavy storm): `lightning = 1` (decays
    0.85 per step) lights the sky, a `bolt()` strikes from the cloud base at `boltX`, thunder follows 0.2 to 1.2 s later.
  - **Big waves (heavy storm):** `waveY(sx)` adds steep swells with sharp crests ~200 px apart, up to ~22 px above
    `SURFACE` (never below `SURFACE + 3`, where the CSS water starts), with a whitecap line and spray (`drop` particles)
    blown off the crests. In `drawEnemy`, frigates (and the heli parked on deck) heave with `waveY` and pitch with its slope.
  - Tested: mission 2 storm at 50%, 5 strikes; mission 3 clears at 50%; mission 4 heavy storm at 50%, 14 strikes;
    mission 5 clears at 50%, 19 strikes; missions 1 and 6 clear. Draw cost ~1.1 ms clear, ~2.5 ms in the heavy storm.
  - The NEWS for missions 2, 4 and 5 have a "WEATHER:" line. The title screen always shows clear weather.

- **Bosses (`BOSSES[level]`, `spawnBoss()`, `updateBoss()`, `drawBoss()`):** when `dist` reaches `levelLen` in a mission
  that has an entry, `dist` is held there and the boss comes in; the mission ends 150 steps (`bossEnd`) after it is sunk.
  Normal spawning has stopped by then, so it is a one-on-one fight. The global `boss` is the live boss (or null).
  | | Mission 4: TYPHOON | Mission 5: BELGOROD |
  |---|---|---|
  | hp | 10 | 20 |
  | max speed (`speed`, px/step; our sub 1.75) | 2 | 2.6 |
  | weapons defeated (`save`) | 70% | 80% |
  | swimmers (`swim`) | no | 2 every 360 steps, max `BOSS_DIVERS = 3` out |
  - **Art:** `drawShip` at scale 5, flipped, `hull` color per boss; box 180x28 drawn at y - 42 (the sail sticks out above
    the box). Bow laser emitter at (x - 2, y + 14). `pts` = 50 per hp.
  - **Movement:** cancels the scroll (holds its place on screen) and roams between random waypoints in the right half
    (x from W/2), turning every 1.5 to 3 s. Ramming it costs a life and pushes the sub back.
  - **Shkval salvo (`brk` eShot):** every `BOSS_FIRE = 300` steps, one rocket-torpedo out of the sail and one out of the
    keel ("SHKVAL LAUNCH - 2 ROCKETS INBOUND"). Ejected for 18 steps, then the motor lights and it homes (0.035 rad/step,
    up to 3 px/step) on the sub or the nearest decoy; 7 s life. Runs just under the surface. Killed by torpedoes, the
    laser (F), the bubble screen (E); 1 life on a hit. Counted by the threat warning ("LOCKED TARGET - SHKVAL INBOUND").
    Tested: a sub sitting still lost 5 lives to 12 rockets in 30 s.
  - **Bow laser:** within `BOSS_LASER_RANGE = 170` px it aims for 40 steps (dotted line, "LASER LOCK - BREAK AWAY"),
    locks for the last 24 (solid line, time to dodge), fires 20 steps (1 life, kills allies), then cools 120 steps.
    Tested: parked in front of it, 7 shots, 5 hits (the other 2 during invincibility).
  - **Defense (`bossDefend`):** each torpedo whose course hits it (40 to `BOSS_CM_RANGE = 260` px out) and each guided
    H-bomb aimed at it under water (more than 110 px out) gets one roll at `save`. On a yes, 50/50: a decoy (`cm`, the
    weapon gets `lure`) or a bubble wall (`bcl` eShot, radius up to `BOSS_BCL_R = 30`, 150 steps) halfway along its path
    that sets off any torpedo or H-bomb entering it ("TORPEDO DEFEATED", "H-BOMB DEFEATED"). One reaction per 20 steps.
    Tested with the boss held still: Typhoon let 29/100 and 39/100 torpedoes through (two runs) and 9/40 H-bombs;
    Belgorod 25/100 torpedoes. A moving boss also dodges many torpedoes: expect long fights.
  - **H-bomb:** locks onto the boss; a hit takes `BOSS_HBOMB = 3` hp instead of killing it (`megaBoom`).
  - **Swimmers (Belgorod):** 2 `diver`s out of a hatch behind the sail (one up, one down), hunting at once like any
    swimmer ("COMBAT SWIMMERS DEPLOYED"). Tested: 10 launches in 60 s.
  - **HUD:** the progress bar becomes a red bar with one segment per hp and the boss name under it.
  - **Death:** big blast, its live rockets blow up, "SPLASH ONE <NAME> - BOSS DOWN", a burning wreck sinks.
  - **To test a boss fast:** `reset(); level = 5; startLevel(); dist = levelLen; enemies = []; state = 'play';`

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
