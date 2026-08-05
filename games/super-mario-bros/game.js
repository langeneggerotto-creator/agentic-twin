"use strict";

/* ============================================================
   PLUMBER BROS — a Super-Mario-Bros-style platformer
   Single-file canvas game engine. All art is drawn procedurally
   (no external image/audio assets required).
   ============================================================ */

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
ctx.imageSmoothingEnabled = false;

const TILE = 32;
const VIEW_W = canvas.width;
const VIEW_H = canvas.height;
const ROWS = VIEW_H / TILE; // 15

const GRAVITY = 0.62;
const MAX_FALL = 16;
const MOVE_ACCEL = 0.55;
const MAX_RUN = 4.4;
const FRICTION = 0.7;
const JUMP_VELOCITY = -11.6;
const JUMP_CUT = 0.5; // releasing jump early cuts upward velocity
const ENEMY_SPEED = 1.1;

// Tile codes
const T_EMPTY = 0;
const T_GROUND = 1;
const T_BRICK = 2;
const T_Q_COIN = 3;
const T_Q_MUSHROOM = 4;
const T_PIPE = 5;
const T_USED = 6; // spent question block
const T_STEP = 7; // solid staircase block (same as ground visually varied)

/* ---------------------------------------------------------
   Audio — tiny WebAudio beeper, no external files
--------------------------------------------------------- */
let actx = null;
function audioInit() {
  if (!actx) {
    try {
      actx = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {
      actx = null;
    }
  }
}
function beep(freq, dur, type = "square", vol = 0.08, delay = 0) {
  if (!actx) return;
  const t0 = actx.currentTime + delay;
  const osc = actx.createOscillator();
  const gain = actx.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, t0);
  gain.gain.setValueAtTime(vol, t0);
  gain.gain.exponentialRampToValueAtTime(0.001, t0 + dur);
  osc.connect(gain).connect(actx.destination);
  osc.start(t0);
  osc.stop(t0 + dur);
}
const sfx = {
  jump: () => beep(520, 0.14, "square", 0.09),
  coin: () => {
    beep(988, 0.08, "square", 0.08);
    beep(1318, 0.12, "square", 0.08, 0.06);
  },
  stomp: () => beep(140, 0.12, "square", 0.1),
  bump: () => beep(220, 0.07, "square", 0.08),
  powerup: () => {
    [523, 659, 784, 1046].forEach((f, i) => beep(f, 0.1, "square", 0.08, i * 0.08));
  },
  death: () => {
    beep(300, 0.15, "sawtooth", 0.1);
    beep(180, 0.2, "sawtooth", 0.1, 0.15);
  },
  flag: () => {
    [400, 500, 600, 700, 800].forEach((f, i) => beep(f, 0.1, "triangle", 0.09, i * 0.07));
  },
  win: () => {
    [523, 587, 659, 784, 1046, 1318].forEach((f, i) => beep(f, 0.15, "square", 0.09, i * 0.12));
  },
};

/* ---------------------------------------------------------
   Input
--------------------------------------------------------- */
const keys = {};
window.addEventListener("keydown", (e) => {
  keys[e.code] = true;
  if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.code)) {
    e.preventDefault();
  }
  if (e.code === "KeyP") togglePause();
});
window.addEventListener("keyup", (e) => {
  keys[e.code] = false;
});

function isDown(...codes) {
  return codes.some((c) => keys[c]);
}

/* ---------------------------------------------------------
   Level construction helpers
--------------------------------------------------------- */
function makeEmptyLevel(cols) {
  const tiles = [];
  for (let r = 0; r < ROWS; r++) tiles.push(new Array(cols).fill(T_EMPTY));
  return tiles;
}

function buildLevel(index) {
  if (index === 0) return buildLevel1();
  return buildLevel2();
}

function buildLevel1() {
  const cols = 150;
  const tiles = makeEmptyLevel(cols);
  const groundRow = ROWS - 2; // row 13
  const enemies = [];
  const coins = [];

  const fillGround = (c0, c1) => {
    for (let c = c0; c <= c1; c++) {
      tiles[groundRow][c] = T_GROUND;
      tiles[groundRow + 1][c] = T_GROUND;
    }
  };

  // ground with a couple of pits
  fillGround(0, 19);
  fillGround(23, 44);
  fillGround(49, 69);
  fillGround(73, 100);
  fillGround(103, 148);

  // pipes (2 tall then 3 tall)
  const addPipe = (col, height) => {
    for (let h = 0; h < height; h++) {
      tiles[groundRow - 1 - h][col] = T_PIPE;
      tiles[groundRow - 1 - h][col + 1] = T_PIPE;
    }
  };
  addPipe(30, 2);
  addPipe(40, 3);
  addPipe(85, 2);

  // floating blocks
  tiles[9][12] = T_Q_COIN;
  tiles[9][13] = T_Q_MUSHROOM;
  tiles[9][14] = T_BRICK;
  tiles[9][15] = T_BRICK;
  tiles[9][16] = T_Q_COIN;

  tiles[8][55] = T_Q_COIN;
  tiles[8][58] = T_BRICK;
  tiles[8][59] = T_Q_COIN;
  tiles[8][60] = T_BRICK;

  tiles[9][76] = T_Q_MUSHROOM;
  tiles[9][79] = T_Q_COIN;
  tiles[9][80] = T_Q_COIN;

  // ascending staircase near col 63-69 (before a gap)
  let stairCol = 63;
  for (let s = 1; s <= 6; s++) {
    for (let h = 0; h < s; h++) {
      tiles[groundRow - 1 - h][stairCol] = T_STEP;
    }
    stairCol++;
  }
  // descending staircase mirrored around col 96-101
  stairCol = 96;
  for (let s = 5; s >= 1; s--) {
    for (let h = 0; h < s; h++) {
      tiles[groundRow - 1 - h][stairCol] = T_STEP;
    }
    stairCol++;
  }

  // floating coins in arcs
  [5, 6, 7].forEach((c, i) => coins.push({ col: c, row: 9 - (i === 1 ? 1 : 0) }));
  [27, 28, 29].forEach((c) => coins.push({ col: c, row: 10 }));
  [110, 111, 112, 113].forEach((c) => coins.push({ col: c, row: 9 }));

  // enemies
  enemies.push({ col: 15, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 27, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 36, row: groundRow - 1, dir: 1 });
  enemies.push({ col: 55, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 77, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 90, row: groundRow - 1, dir: 1 });
  enemies.push({ col: 105, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 130, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 135, row: groundRow - 1, dir: 1 });

  // flag near the end
  const flagCol = 144;
  for (let h = 0; h < 9; h++) {
    tiles[groundRow - 1 - h][flagCol] = T_EMPTY; // pole occupies visually, not solid
  }
  fillGround(144, 149);

  return {
    tiles,
    cols,
    groundRow,
    enemies,
    coins,
    playerStart: { col: 2, row: groundRow - 1 },
    flagCol,
    theme: "overworld",
    name: "1-1",
  };
}

function buildLevel2() {
  const cols = 120;
  const tiles = makeEmptyLevel(cols);
  const groundRow = ROWS - 2;
  const enemies = [];
  const coins = [];

  const fillGround = (c0, c1) => {
    for (let c = c0; c <= c1; c++) {
      tiles[groundRow][c] = T_GROUND;
      tiles[groundRow + 1][c] = T_GROUND;
    }
  };

  fillGround(0, 15);
  fillGround(18, 35);
  fillGround(39, 55);
  fillGround(59, 82);
  fillGround(86, 118);

  // ceiling blocks (underground feel)
  for (let c = 0; c < cols; c++) {
    if (c % 7 < 4) tiles[3][c] = T_BRICK;
  }

  const addPipe = (col, height) => {
    for (let h = 0; h < height; h++) {
      tiles[groundRow - 1 - h][col] = T_PIPE;
      tiles[groundRow - 1 - h][col + 1] = T_PIPE;
    }
  };
  addPipe(10, 2);
  addPipe(70, 2);

  tiles[9][6] = T_Q_MUSHROOM;
  tiles[9][20] = T_Q_COIN;
  tiles[9][21] = T_BRICK;
  tiles[9][22] = T_Q_COIN;
  tiles[8][45] = T_BRICK;
  tiles[8][46] = T_Q_COIN;
  tiles[8][47] = T_BRICK;
  tiles[9][63] = T_Q_MUSHROOM;
  tiles[9][90] = T_Q_COIN;
  tiles[9][93] = T_Q_COIN;

  // staircases up to a high platform run
  let stairCol = 40;
  for (let s = 1; s <= 5; s++) {
    for (let h = 0; h < s; h++) tiles[groundRow - 1 - h][stairCol] = T_STEP;
    stairCol++;
  }
  stairCol = 51;
  for (let s = 5; s >= 1; s--) {
    for (let h = 0; h < s; h++) tiles[groundRow - 1 - h][stairCol] = T_STEP;
    stairCol++;
  }

  [24, 25, 26].forEach((c) => coins.push({ col: c, row: 10 }));
  [95, 96, 97, 98].forEach((c) => coins.push({ col: c, row: 9 }));

  enemies.push({ col: 12, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 22, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 30, row: groundRow - 1, dir: 1 });
  enemies.push({ col: 44, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 63, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 72, row: groundRow - 1, dir: 1 });
  enemies.push({ col: 90, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 100, row: groundRow - 1, dir: -1 });
  enemies.push({ col: 108, row: groundRow - 1, dir: 1 });

  const flagCol = 114;
  fillGround(114, 119);

  return {
    tiles,
    cols,
    groundRow,
    enemies,
    coins,
    playerStart: { col: 2, row: groundRow - 1 },
    flagCol,
    theme: "underground",
    name: "1-2",
  };
}

/* ---------------------------------------------------------
   Game state
--------------------------------------------------------- */
const LEVEL_BUILDERS = [buildLevel1, buildLevel2];
let levelIndex = 0;
let level = null;
let entities = { goombas: [], coinPops: [], mushrooms: [], particles: [] };
let cameraX = 0;
let frame = 0;

let player = null;
function newPlayer() {
  return {
    x: 0,
    y: 0,
    w: 24,
    h: 30,
    vx: 0,
    vy: 0,
    onGround: false,
    facing: 1,
    big: false,
    invincible: 0,
    dead: false,
    sliding: false,
    walkFrame: 0,
    hurtFlash: 0,
  };
}

let score = 0;
let coinCount = 0;
let lives = 3;
let timeLeft = 400;
let timeAccum = 0;
let gameState = "start"; // start, playing, paused, levelcomplete, gameover, win
let stateTimer = 0;

const scoreEl = document.getElementById("score");
const coinsEl = document.getElementById("coins");
const worldEl = document.getElementById("world");
const timeEl = document.getElementById("time");
const livesEl = document.getElementById("lives");
const overlay = document.getElementById("overlay");
const startBtn = document.getElementById("start-btn");

function loadLevel(idx) {
  level = LEVEL_BUILDERS[idx]();
  entities = { goombas: [], coinPops: [], mushrooms: [], particles: [] };
  level.enemies.forEach((e) => {
    entities.goombas.push({
      x: e.col * TILE,
      y: e.row * TILE,
      w: 26,
      h: 26,
      vx: ENEMY_SPEED * e.dir,
      alive: true,
      squished: 0,
    });
  });
  player = newPlayer();
  player.x = level.playerStart.col * TILE;
  player.y = level.playerStart.row * TILE;
  cameraX = 0;
  timeLeft = 400;
  timeAccum = 0;
}

function resetGame() {
  score = 0;
  coinCount = 0;
  lives = 3;
  levelIndex = 0;
  loadLevel(levelIndex);
  gameState = "playing";
}

function tileAt(tiles, col, row) {
  if (row < 0 || row >= ROWS || col < 0 || col >= tiles[0].length) return T_GROUND; // treat out of bounds sides as solid to avoid escaping
  return tiles[row][col];
}
function isSolid(code) {
  return (
    code === T_GROUND ||
    code === T_BRICK ||
    code === T_Q_COIN ||
    code === T_Q_MUSHROOM ||
    code === T_PIPE ||
    code === T_USED ||
    code === T_STEP
  );
}

/* ---------------------------------------------------------
   Update
--------------------------------------------------------- */
function togglePause() {
  if (gameState === "playing") {
    gameState = "paused";
    showOverlay("PAUSED", "Press P to resume");
  } else if (gameState === "paused") {
    hideOverlay();
    gameState = "playing";
  }
}

function showOverlay(title, sub, showBtn = false) {
  overlay.innerHTML = `<h1>${title}</h1>${sub ? `<p id="overlay-sub">${sub}</p>` : ""}`;
  if (showBtn) {
    const btn = document.createElement("button");
    btn.id = "start-btn";
    btn.textContent = "Press Start";
    btn.addEventListener("click", onStartClick);
    overlay.appendChild(btn);
  }
  overlay.classList.remove("hidden");
}
function hideOverlay() {
  overlay.classList.add("hidden");
}

function updatePlayer(dt) {
  if (player.sliding) {
    player.y += 3;
    const poleBottom = (level.groundRow) * TILE - player.h;
    if (player.y >= poleBottom) {
      player.y = poleBottom;
      player.sliding = false;
      player.walkOff = true;
      player.vx = 2.4;
    }
    return;
  }
  if (player.walkOff) {
    player.x += player.vx;
    if (player.x > (level.flagCol + 5) * TILE) {
      gameState = "levelcomplete";
      stateTimer = 0;
      score += Math.floor(timeLeft) * 10;
      sfx.flag();
    }
    return;
  }

  const left = isDown("ArrowLeft", "KeyA");
  const right = isDown("ArrowRight", "KeyD");
  const jumpPressed = isDown("Space", "ArrowUp", "KeyW");

  if (left && !right) {
    player.vx -= MOVE_ACCEL;
    player.facing = -1;
  } else if (right && !left) {
    player.vx += MOVE_ACCEL;
    player.facing = 1;
  } else {
    player.vx *= FRICTION;
    if (Math.abs(player.vx) < 0.05) player.vx = 0;
  }
  player.vx = Math.max(-MAX_RUN, Math.min(MAX_RUN, player.vx));

  if (jumpPressed && player.onGround && !player.jumpLock) {
    player.vy = JUMP_VELOCITY;
    player.onGround = false;
    player.jumpLock = true;
    sfx.jump();
  }
  if (!jumpPressed) player.jumpLock = false;
  if (!jumpPressed && player.vy < 0) {
    player.vy *= JUMP_CUT ** 0.15; // gentle cut, avoid abrupt snap
  }

  player.vy += GRAVITY;
  if (player.vy > MAX_FALL) player.vy = MAX_FALL;

  moveAndCollide(dt);

  if (player.hurtFlash > 0) player.hurtFlash--;
  if (player.invincible > 0) player.invincible--;

  // fell into a pit
  if (player.y > ROWS * TILE + 64) {
    killPlayer(true);
  }

  // reached flagpole
  if (!player.sliding && !player.walkOff && player.x + player.w / 2 >= level.flagCol * TILE) {
    player.sliding = true;
    player.x = level.flagCol * TILE;
    player.vx = 0;
    player.vy = 0;
  }
}

function moveAndCollide(dt) {
  const tiles = level.tiles;

  // horizontal
  player.x += player.vx;
  let pc0 = Math.floor(player.x / TILE);
  let pc1 = Math.floor((player.x + player.w) / TILE);
  let pr0 = Math.floor(player.y / TILE);
  let pr1 = Math.floor((player.y + player.h - 1) / TILE);
  if (player.vx > 0) {
    for (let r = pr0; r <= pr1; r++) {
      if (isSolid(tileAt(tiles, pc1, r))) {
        player.x = pc1 * TILE - player.w;
        player.vx = 0;
        break;
      }
    }
  } else if (player.vx < 0) {
    for (let r = pr0; r <= pr1; r++) {
      if (isSolid(tileAt(tiles, pc0, r))) {
        player.x = (pc0 + 1) * TILE;
        player.vx = 0;
        break;
      }
    }
  }
  if (player.x < 0) player.x = 0;

  // vertical
  player.y += player.vy;
  pc0 = Math.floor(player.x / TILE);
  pc1 = Math.floor((player.x + player.w - 1) / TILE);
  pr0 = Math.floor(player.y / TILE);
  pr1 = Math.floor((player.y + player.h) / TILE);
  player.onGround = false;
  if (player.vy > 0) {
    for (let c = pc0; c <= pc1; c++) {
      if (isSolid(tileAt(tiles, c, pr1))) {
        player.y = pr1 * TILE - player.h;
        player.vy = 0;
        player.onGround = true;
        break;
      }
    }
  } else if (player.vy < 0) {
    for (let c = pc0; c <= pc1; c++) {
      const code = tileAt(tiles, c, pr0);
      if (isSolid(code)) {
        player.y = (pr0 + 1) * TILE;
        player.vy = 0;
        hitBlock(c, pr0, code);
        break;
      }
    }
  }
}

function hitBlock(col, row, code) {
  if (code === T_Q_COIN) {
    level.tiles[row][col] = T_USED;
    coinCount++;
    score += 200;
    entities.coinPops.push({ x: col * TILE, y: row * TILE, t: 0 });
    sfx.coin();
  } else if (code === T_Q_MUSHROOM) {
    level.tiles[row][col] = T_USED;
    entities.mushrooms.push({
      x: col * TILE,
      y: row * TILE - TILE,
      w: 26,
      h: 26,
      vx: 1.2,
      vy: 0,
      spawning: true,
      spawnY: row * TILE,
    });
    sfx.bump();
  } else if (code === T_BRICK) {
    if (player.big) {
      level.tiles[row][col] = T_EMPTY;
      score += 50;
      sfx.stomp();
    } else {
      sfx.bump();
    }
  }
}

function updateGoombas() {
  const tiles = level.tiles;
  entities.goombas.forEach((g) => {
    if (!g.alive) {
      g.squished += 1;
      return;
    }
    g.vy = (g.vy || 0) + GRAVITY;
    if (g.vy > MAX_FALL) g.vy = MAX_FALL;

    // horizontal move + wall turn
    const nextX = g.x + g.vx;
    const c = g.vx > 0 ? Math.floor((nextX + g.w) / TILE) : Math.floor(nextX / TILE);
    const rowMid = Math.floor((g.y + g.h / 2) / TILE);
    if (isSolid(tileAt(tiles, c, rowMid))) {
      g.vx *= -1;
    } else {
      g.x = nextX;
    }

    // ledge detection: turn around if no ground ahead
    const aheadCol = g.vx > 0 ? Math.floor((g.x + g.w + 2) / TILE) : Math.floor((g.x - 2) / TILE);
    const belowRow = Math.floor((g.y + g.h + 2) / TILE);
    if (!isSolid(tileAt(tiles, aheadCol, belowRow))) {
      g.vx *= -1;
    }

    // vertical
    g.y += g.vy;
    const gr0 = Math.floor(g.y / TILE);
    const gr1 = Math.floor((g.y + g.h) / TILE);
    const gc0 = Math.floor(g.x / TILE);
    const gc1 = Math.floor((g.x + g.w) / TILE);
    if (g.vy >= 0) {
      for (let c2 = gc0; c2 <= gc1; c2++) {
        if (isSolid(tileAt(tiles, c2, gr1))) {
          g.y = gr1 * TILE - g.h;
          g.vy = 0;
          break;
        }
      }
    }
  });
  entities.goombas = entities.goombas.filter((g) => g.alive || g.squished < 30);
}

function updateMushrooms() {
  const tiles = level.tiles;
  entities.mushrooms.forEach((m) => {
    if (m.spawning) {
      m.y -= 1.2;
      if (m.y <= m.spawnY - TILE) {
        m.spawning = false;
      }
      return;
    }
    m.vy += GRAVITY;
    if (m.vy > MAX_FALL) m.vy = MAX_FALL;
    const nextX = m.x + m.vx;
    const c = m.vx > 0 ? Math.floor((nextX + m.w) / TILE) : Math.floor(nextX / TILE);
    const rowMid = Math.floor((m.y + m.h / 2) / TILE);
    if (isSolid(tileAt(tiles, c, rowMid))) {
      m.vx *= -1;
    } else {
      m.x = nextX;
    }
    m.y += m.vy;
    const gr1 = Math.floor((m.y + m.h) / TILE);
    const gc0 = Math.floor(m.x / TILE);
    const gc1 = Math.floor((m.x + m.w) / TILE);
    for (let c2 = gc0; c2 <= gc1; c2++) {
      if (isSolid(tileAt(tiles, c2, gr1))) {
        m.y = gr1 * TILE - m.h;
        m.vy = 0;
        break;
      }
    }
  });
}

function aabb(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function checkEntityCollisions() {
  // goombas vs player
  entities.goombas.forEach((g) => {
    if (!g.alive) return;
    if (!aabb(player, g)) return;
    const playerBottom = player.y + player.h;
    const stomp = player.vy > 0 && playerBottom - g.y < 16;
    if (stomp) {
      g.alive = false;
      g.squished = 0;
      player.vy = -7;
      score += 100;
      sfx.stomp();
    } else if (player.invincible <= 0) {
      damagePlayer();
    }
  });

  // mushrooms vs player
  entities.mushrooms = entities.mushrooms.filter((m) => {
    if (aabb(player, m)) {
      growPlayer();
      score += 1000;
      sfx.powerup();
      return false;
    }
    return true;
  });

  // standalone coins
  level.coins = level.coins.filter((c) => {
    const cx = c.col * TILE + 8;
    const cy = c.row * TILE + 8;
    const box = { x: cx, y: cy, w: 16, h: 16 };
    if (aabb(player, box)) {
      coinCount++;
      score += 200;
      sfx.coin();
      return false;
    }
    return true;
  });
}

function growPlayer() {
  if (!player.big) {
    player.big = true;
    player.h = 56;
    player.y -= 26;
  }
  player.invincible = 60;
}

function damagePlayer() {
  if (player.invincible > 0 || player.dead) return;
  if (player.big) {
    player.big = false;
    player.h = 30;
    player.invincible = 90;
    player.hurtFlash = 90;
    sfx.bump();
  } else {
    killPlayer(false);
  }
}

function killPlayer(fell) {
  if (player.dead) return;
  player.dead = true;
  sfx.death();
  lives--;
  gameState = "dying";
  stateTimer = 0;
  player.vy = fell ? player.vy : -10;
  player.vx = 0;
}

function updateCamera() {
  const targetX = player.x - VIEW_W / 2.5;
  cameraX = Math.max(0, Math.min(targetX, level.cols * TILE - VIEW_W));
}

function updateCoinPops() {
  entities.coinPops.forEach((p) => (p.t += 1));
  entities.coinPops = entities.coinPops.filter((p) => p.t < 24);
}

function updateHUD() {
  scoreEl.textContent = String(score).padStart(6, "0");
  coinsEl.textContent = "x" + String(coinCount).padStart(2, "0");
  worldEl.textContent = level ? level.name : "1-1";
  timeEl.textContent = Math.max(0, Math.ceil(timeLeft));
  livesEl.textContent = "x" + lives;
}

function update(dt) {
  if (gameState === "playing") {
    timeAccum += dt;
    if (timeAccum > 1000) {
      timeAccum -= 1000;
      timeLeft -= 1;
      if (timeLeft <= 0) killPlayer(false);
    }
    updatePlayer(dt);
    updateGoombas();
    updateMushrooms();
    checkEntityCollisions();
    updateCoinPops();
    updateCamera();
  } else if (gameState === "dying") {
    stateTimer += dt;
    player.vy += GRAVITY;
    player.y += player.vy;
    if (stateTimer > 1600) {
      if (lives <= 0) {
        gameState = "gameover";
        showOverlay("GAME OVER", "", true);
      } else {
        loadLevel(levelIndex);
        gameState = "playing";
      }
    }
  } else if (gameState === "levelcomplete") {
    stateTimer += dt;
    if (stateTimer > 2000) {
      levelIndex++;
      if (levelIndex >= LEVEL_BUILDERS.length) {
        gameState = "win";
        sfx.win();
        showOverlay("YOU WIN!", "You rescued the Princess! Final score: " + score, true);
      } else {
        loadLevel(levelIndex);
        gameState = "playing";
      }
    }
  }
  updateHUD();
}

/* ---------------------------------------------------------
   Rendering
--------------------------------------------------------- */
function drawBackground() {
  const sky = level.theme === "underground" ? "#000010" : "#5c94fc";
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, VIEW_W, VIEW_H);

  if (level.theme === "overworld") {
    // parallax hills
    ctx.fillStyle = "#3fae3f";
    const hillOffset = -(cameraX * 0.3) % 400;
    for (let i = -1; i < 4; i++) {
      const bx = hillOffset + i * 400;
      drawHill(bx + 60, VIEW_H - 64, 70);
      drawHill(bx + 220, VIEW_H - 64, 50);
    }
    // clouds
    ctx.fillStyle = "#ffffff";
    const cloudOffset = -(cameraX * 0.5) % 500;
    for (let i = -1; i < 4; i++) {
      const cx = cloudOffset + i * 500;
      drawCloud(cx + 80, 70);
      drawCloud(cx + 320, 110);
    }
    // bushes
    ctx.fillStyle = "#2e8b2e";
    const bushOffset = -(cameraX * 0.6) % 450;
    for (let i = -1; i < 4; i++) {
      const bx = bushOffset + i * 450;
      drawBush(bx + 150, VIEW_H - 66);
    }
  }
}

function drawHill(cx, baseY, r) {
  ctx.beginPath();
  ctx.moveTo(cx - r, baseY);
  ctx.quadraticCurveTo(cx, baseY - r * 1.4, cx + r, baseY);
  ctx.closePath();
  ctx.fill();
}
function drawCloud(cx, cy) {
  ctx.beginPath();
  ctx.arc(cx, cy, 16, 0, Math.PI * 2);
  ctx.arc(cx + 18, cy - 8, 20, 0, Math.PI * 2);
  ctx.arc(cx + 38, cy, 16, 0, Math.PI * 2);
  ctx.fill();
}
function drawBush(cx, cy) {
  ctx.beginPath();
  ctx.arc(cx, cy, 14, 0, Math.PI * 2);
  ctx.arc(cx + 16, cy - 6, 18, 0, Math.PI * 2);
  ctx.arc(cx + 34, cy, 14, 0, Math.PI * 2);
  ctx.fill();
}

function drawTiles() {
  const tiles = level.tiles;
  const c0 = Math.max(0, Math.floor(cameraX / TILE) - 1);
  const c1 = Math.min(tiles[0].length - 1, Math.ceil((cameraX + VIEW_W) / TILE) + 1);
  for (let r = 0; r < ROWS; r++) {
    for (let c = c0; c <= c1; c++) {
      const code = tiles[r][c];
      if (code === T_EMPTY) continue;
      const x = c * TILE - cameraX;
      const y = r * TILE;
      drawTile(code, x, y);
    }
  }
  // flagpole
  const fx = level.flagCol * TILE - cameraX;
  ctx.fillStyle = "#dddddd";
  ctx.fillRect(fx + 14, TILE * 4, 4, (level.groundRow - 4) * TILE);
  ctx.fillStyle = player.sliding || player.walkOff || gameState === "levelcomplete" ? "#2ecc71" : "#e74c3c";
  const flagY = player.sliding || player.walkOff || gameState === "levelcomplete"
    ? player.y
    : TILE * 4;
  ctx.beginPath();
  ctx.moveTo(fx + 18, flagY + 6);
  ctx.lineTo(fx + 40, flagY + 14);
  ctx.lineTo(fx + 18, flagY + 22);
  ctx.closePath();
  ctx.fill();
  ctx.beginPath();
  ctx.arc(fx + 16, TILE * 4, 6, 0, Math.PI * 2);
  ctx.fillStyle = "#ffd700";
  ctx.fill();
}

function drawTile(code, x, y) {
  switch (code) {
    case T_GROUND:
      ctx.fillStyle = level.theme === "underground" ? "#5a3d1e" : "#c87137";
      ctx.fillRect(x, y, TILE, TILE);
      ctx.strokeStyle = "rgba(0,0,0,0.25)";
      ctx.strokeRect(x + 1, y + 1, TILE - 2, TILE - 2);
      ctx.fillStyle = "rgba(255,255,255,0.15)";
      ctx.fillRect(x, y, TILE, 4);
      break;
    case T_STEP:
      ctx.fillStyle = level.theme === "underground" ? "#6b4a24" : "#b0631f";
      ctx.fillRect(x, y, TILE, TILE);
      ctx.strokeStyle = "rgba(0,0,0,0.3)";
      ctx.strokeRect(x + 1, y + 1, TILE - 2, TILE - 2);
      break;
    case T_BRICK:
      ctx.fillStyle = "#b5502e";
      ctx.fillRect(x, y, TILE, TILE);
      ctx.strokeStyle = "#7a2f16";
      ctx.lineWidth = 2;
      ctx.strokeRect(x + 2, y + 2, TILE - 4, TILE - 4);
      ctx.beginPath();
      ctx.moveTo(x + TILE / 2, y + 2);
      ctx.lineTo(x + TILE / 2, y + TILE - 2);
      ctx.stroke();
      break;
    case T_Q_COIN:
    case T_Q_MUSHROOM: {
      const bob = Math.sin(frame / 10) * 1.5;
      ctx.fillStyle = "#f5b942";
      ctx.fillRect(x, y + bob, TILE, TILE);
      ctx.strokeStyle = "#8a5a12";
      ctx.lineWidth = 2;
      ctx.strokeRect(x + 2, y + 2 + bob, TILE - 4, TILE - 4);
      ctx.fillStyle = "#8a5a12";
      ctx.font = "bold 18px monospace";
      ctx.textAlign = "center";
      ctx.fillText("?", x + TILE / 2, y + 23 + bob);
      break;
    }
    case T_USED:
      ctx.fillStyle = "#8a5a2a";
      ctx.fillRect(x, y, TILE, TILE);
      ctx.strokeStyle = "rgba(0,0,0,0.3)";
      ctx.strokeRect(x + 1, y + 1, TILE - 2, TILE - 2);
      break;
    case T_PIPE:
      ctx.fillStyle = "#2fae2f";
      ctx.fillRect(x, y, TILE, TILE);
      ctx.strokeStyle = "#146214";
      ctx.lineWidth = 2;
      ctx.strokeRect(x + 1, y + 1, TILE - 2, TILE - 2);
      break;
  }
}

function drawPlayer() {
  const px = player.x - cameraX;
  const py = player.y;
  ctx.save();
  if (player.hurtFlash > 0 && Math.floor(frame / 3) % 2 === 0) {
    ctx.globalAlpha = 0.4;
  }
  ctx.translate(px + player.w / 2, py + player.h / 2);
  ctx.scale(player.facing, 1);
  ctx.translate(-player.w / 2, -player.h / 2);

  const bodyColor = player.big ? "#e74c3c" : "#e74c3c";
  const skin = "#ffcc99";
  const overalls = "#3355cc";

  if (!player.big) {
    // small mario 24x30
    ctx.fillStyle = bodyColor;
    ctx.fillRect(4, 4, 16, 8); // cap
    ctx.fillStyle = skin;
    ctx.fillRect(4, 10, 16, 8); // face
    ctx.fillStyle = bodyColor;
    ctx.fillRect(0, 12, 6, 4); // cap brim
    ctx.fillStyle = overalls;
    ctx.fillRect(2, 18, 20, 10); // overalls
    ctx.fillStyle = bodyColor;
    ctx.fillRect(2, 16, 20, 4); // shirt strip
    ctx.fillStyle = "#7a4a26";
    const legOffset = player.onGround ? (Math.floor(player.walkFrame / 6) % 2) * 3 : 2;
    ctx.fillRect(3, 26, 7, 4 + legOffset);
    ctx.fillRect(14, 26, 7, 4 - legOffset + 2);
  } else {
    // big mario 24x56
    ctx.fillStyle = bodyColor;
    ctx.fillRect(4, 0, 16, 10);
    ctx.fillStyle = skin;
    ctx.fillRect(4, 8, 16, 10);
    ctx.fillStyle = bodyColor;
    ctx.fillRect(0, 10, 6, 5);
    ctx.fillStyle = overalls;
    ctx.fillRect(2, 22, 20, 20);
    ctx.fillStyle = bodyColor;
    ctx.fillRect(2, 18, 20, 6);
    ctx.fillStyle = skin;
    ctx.fillRect(0, 22, 4, 10);
    ctx.fillRect(20, 22, 4, 10);
    ctx.fillStyle = "#7a4a26";
    const legOffset = player.onGround ? (Math.floor(player.walkFrame / 6) % 2) * 4 : 2;
    ctx.fillRect(3, 42, 8, 10 + legOffset);
    ctx.fillRect(13, 42, 8, 10 - legOffset + 4);
  }
  ctx.restore();
}

function drawGoombas() {
  entities.goombas.forEach((g) => {
    const gx = g.x - cameraX;
    if (gx < -40 || gx > VIEW_W + 40) return;
    ctx.save();
    if (!g.alive) {
      ctx.translate(gx, g.y + g.h - 10);
      ctx.scale(1, 0.3);
      ctx.fillStyle = "#8b5a2b";
      ctx.fillRect(0, 0, g.w, g.h);
    } else {
      ctx.translate(gx, g.y);
      ctx.fillStyle = "#8b5a2b";
      ctx.beginPath();
      ctx.arc(g.w / 2, g.h / 2, g.w / 2, Math.PI, 0);
      ctx.fillRect(0, g.h / 2, g.w, g.h / 2 - 4);
      ctx.fill();
      ctx.fillStyle = "#5a3a1a";
      const stepOffset = Math.floor(frame / 8) % 2 === 0 ? 0 : 2;
      ctx.fillRect(2, g.h - 6, 8, 6 + stepOffset);
      ctx.fillRect(g.w - 10, g.h - 6, 8, 6 - stepOffset + 2);
      ctx.fillStyle = "#fff";
      ctx.fillRect(g.w / 2 - 8, g.h / 2 - 4, 6, 6);
      ctx.fillRect(g.w / 2 + 2, g.h / 2 - 4, 6, 6);
      ctx.fillStyle = "#000";
      ctx.fillRect(g.w / 2 - 6, g.h / 2 - 2, 3, 3);
      ctx.fillRect(g.w / 2 + 4, g.h / 2 - 2, 3, 3);
    }
    ctx.restore();
  });
}

function drawMushrooms() {
  entities.mushrooms.forEach((m) => {
    const mx = m.x - cameraX;
    ctx.save();
    ctx.translate(mx, m.y);
    ctx.fillStyle = "#e74c3c";
    ctx.beginPath();
    ctx.arc(m.w / 2, m.h / 2, m.w / 2, Math.PI, 0);
    ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.beginPath();
    ctx.arc(8, m.h / 2 - 4, 4, 0, Math.PI * 2);
    ctx.arc(m.w - 8, m.h / 2 - 4, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#f5cba7";
    ctx.fillRect(6, m.h / 2, m.w - 12, m.h / 2 - 2);
    ctx.restore();
  });
}

function drawCoins() {
  level.coins.forEach((c) => {
    const x = c.col * TILE - cameraX;
    const y = c.row * TILE;
    const squeeze = Math.abs(Math.sin(frame / 8 + c.col));
    ctx.save();
    ctx.translate(x + 16, y + 16);
    ctx.scale(squeeze * 0.8 + 0.2, 1);
    ctx.fillStyle = "#ffd700";
    ctx.beginPath();
    ctx.arc(0, 0, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#c9960c";
    ctx.beginPath();
    ctx.arc(0, 0, 10, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  });
}

function drawCoinPops() {
  entities.coinPops.forEach((p) => {
    const x = p.x - cameraX + 16;
    const y = p.y - p.t * 2;
    ctx.globalAlpha = 1 - p.t / 24;
    ctx.fillStyle = "#ffd700";
    ctx.beginPath();
    ctx.arc(x, y, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  });
}

function render() {
  if (!level) return;
  drawBackground();
  drawTiles();
  drawCoins();
  drawGoombas();
  drawMushrooms();
  if (!player.dead || gameState === "dying") drawPlayer();
  drawCoinPops();
}

/* ---------------------------------------------------------
   Main loop
--------------------------------------------------------- */
let lastTime = performance.now();
function loop(now) {
  const dt = Math.min(50, now - lastTime);
  lastTime = now;
  frame++;
  if (gameState === "playing" && (isDown("ArrowLeft", "ArrowRight", "KeyA", "KeyD"))) {
    player.walkFrame++;
  }
  update(dt);
  render();
  requestAnimationFrame(loop);
}

function onStartClick() {
  audioInit();
  hideOverlay();
  resetGame();
}

startBtn.addEventListener("click", onStartClick);

requestAnimationFrame(loop);
