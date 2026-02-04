from flask import Flask, render_template_string, jsonify, request
import os
import math
import random
import time

app = Flask(__name__)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <title>Komi AI: Ultimate Edition</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: 'Segoe UI', sans-serif; background: #1e272e; color: #d2dae2; margin: 0; height: 100vh; display: flex; overflow: hidden; }
    .container { display: flex; width: 100%; height: 100%; }
    .map-area { flex: 3; background: #000; display: flex; justify-content: center; align-items: center; position: relative; }
    .sidebar { flex: 1; background: #2f3640; padding: 20px; border-left: 2px solid #485460; overflow-y: auto; min-width: 340px; }
    canvas { background: #f5f6fa; box-shadow: 0 0 30px rgba(0,0,0,0.5); border-radius: 4px; cursor: crosshair; }

    h1 { color: #f1c40f; margin: 0 0 15px 0; font-size: 1.6rem; text-align: center; }
    h2 { color: #0fb9b1; font-size: 1.1rem; border-bottom: 1px solid #485460; padding-bottom: 5px; margin-top: 22px; margin-bottom: 10px; }
    p.info { font-size: 0.85rem; color: #bdc3c7; margin-bottom: 15px; text-align: center; font-style: italic; }

    .legend-container { background: #1e272e; padding: 10px; border-radius: 6px; border: 1px solid #485460; font-size: 0.85rem; }
    .legend-row { display: flex; align-items: center; margin-bottom: 8px; justify-content: space-between; gap: 10px; }
    .legend-row:last-child { margin-bottom: 0; }

    .l-box { width: 14px; height: 14px; border-radius: 3px; margin-right: 10px; border: 1px solid rgba(255,255,255,0.2); }
    .bg-fast { background: rgba(46, 204, 113, 0.8); }
    .bg-slow { background: rgba(241, 196, 15, 0.8); }
    .bg-swamp { background: rgba(231, 76, 60, 0.8); }

    .route-sample { width: 26px; height: 4px; border-radius: 2px; background: #fff; opacity: 0.9; }

    .route-actions { display:flex; gap:6px; }
    .icon-btn {
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.12);
      color: #d2dae2;
      padding: 6px 8px;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 700;
      line-height: 1;
      user-select: none;
    }
    .icon-btn:hover { background: rgba(255,255,255,0.10); }
    .icon-btn.dim { opacity: 0.55; }

    .pill-btn {
      width: 100%;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.12);
      color: #d2dae2;
      padding: 10px;
      border-radius: 10px;
      cursor: pointer;
      font-weight: 700;
      margin-top: 8px;
    }
    .pill-btn:hover { background: rgba(255,255,255,0.10); }

    input[type="number"] {
      width: 100%; padding: 10px; background: #1e272e;
      border: 1px solid #485460; color: white;
      border-radius: 4px; font-weight: bold; text-align: center;
    }

    button {
      width: 100%; padding: 12px; margin-top: 10px; border: none;
      border-radius: 4px; font-weight: bold; cursor: pointer;
      transition: 0.2s; font-size: 0.9rem;
    }
    button:hover { filter: brightness(1.1); transform: translateY(-1px); }
    button:disabled { background: #57606f !important; cursor: not-allowed; opacity: 0.75; transform: none; }

    .btn-gen { background: #0984e3; color: white; }
    .btn-reset { background: #d63031; color: white; }
    .btn-anim { background: #34495e; color: white; }
    .btn-anim2 { background: #2c3e50; color: white; }
    .row-2btn { display: flex; gap: 10px; }
    .row-2btn button { width: 100%; }

    .stats-box { background: #1e272e; padding: 12px; border-radius: 6px; margin-bottom: 10px; border-left: 5px solid #bdc3c7; }
    .stat-val { font-size: 1.4rem; font-weight: bold; display: block; margin-top: 3px; }
    .sub-stat { font-size: 0.8rem; color: #7f8c8d; display: block; }
    .hint { font-size: 0.78rem; color: #95a5a6; margin-top: 8px; line-height: 1.25rem; }

    #loading { display: none; color: #f1c40f; font-weight: bold; text-align: center; margin-top: 10px; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }

    #error-modal { display: none; position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #c0392b; color: white; padding: 15px 30px; border-radius: 8px; z-index: 1000; box-shadow: 0 5px 15px rgba(0,0,0,0.5); text-align: center; font-weight: bold; }
  </style>
</head>
<body>

<div id="error-modal">Błąd</div>

<div class="container">
  <div class="map-area">
    <canvas id="gameCanvas" width="1000" height="800"></canvas>
  </div>

  <div class="sidebar">
    <h1>Komi: Ultimate</h1>
    <p class="info">Klikaj miasta, narysuj pętlę. Po domknięciu 🧍 i 💻 ruszą w wyścigu (prędkość zależna od terenu).</p>

    <div class="legend-container">
      <div style="font-weight:bold; margin-bottom:5px; color:#fff;">Teren (prędkość):</div>
      <div class="legend-row" style="justify-content:flex-start;"><div class="l-box bg-fast"></div> Autostrada (x2.0)</div>
      <div class="legend-row" style="justify-content:flex-start;"><div class="l-box bg-slow"></div> Piasek (x0.5)</div>
      <div class="legend-row" style="justify-content:flex-start;"><div class="l-box bg-swamp"></div> Bagno (x0.2)</div>

      <div style="font-weight:bold; margin:12px 0 6px 0; color:#fff;">Trasy (kolor / widoczność):</div>

      <div class="legend-row" id="rowUser">
        <div style="display:flex; align-items:center; gap:8px;">
          <div class="route-sample" id="sampleUser"></div><span>🧍 Użytkownik</span>
        </div>
        <div class="route-actions">
          <button class="icon-btn" id="btnToggleUser" title="Pokaż/ukryj">👁</button>
        </div>
      </div>

      <div class="legend-row" id="rowCpu">
        <div style="display:flex; align-items:center; gap:8px;">
          <div class="route-sample" id="sampleCpu"></div><span>💻 Komputer</span>
        </div>
        <div class="route-actions">
          <button class="icon-btn" id="btnToggleCpu" title="Pokaż/ukryj">👁</button>
        </div>
      </div>

      <button class="pill-btn" id="btnOverlapMode" type="button">Tryb nakładania: User</button>

      <div class="hint">
        Ukrycie trasy nie zatrzymuje biegu ikonki – po włączeniu wraca w tym samym miejscu.
      </div>
    </div>

    <h2>Konfiguracja</h2>
    <label style="font-size:0.9rem; display:block; margin-bottom:5px;">
      Liczba miast (zalecane ≤ 60, max 120):
    </label>
    <input type="number" id="pointsCount" value="10" min="3" max="120">
    <button class="btn-gen" onclick="generateMap()">Generuj Mapę</button>
    <button class="btn-reset" onclick="resetRoute()">Resetuj Trasę</button>

    <h2>Wyniki</h2>
    <div class="stats-box" style="border-color:#2563eb">
      Twój wynik
      <span class="stat-val" id="userTime">0.00 h</span>
      <span class="sub-stat">Postęp: <span id="userProg">--</span></span>
      <span class="sub-stat">Macierz: <span id="matrixStatus">--</span></span>
    </div>

    <div class="stats-box" style="border-color:#e84118">
      Komputer (AI)
      <span class="stat-val" id="cpuTime">-- h</span>
      <span class="sub-stat">Postęp: <span id="cpuProg">--</span></span>
      <span class="sub-stat">Czas heurystyki: <span id="cpuMeta">--</span></span>
    </div>

    <div id="loading">Python pracuje...</div>

    <h2>Animacja</h2>
    <div class="row-2btn">
      <button class="btn-anim" id="btnAnimToggle" onclick="toggleAnimation()">⏳ Czekam na trasy...</button>
      <button class="btn-anim2" id="btnAnimReset" onclick="resetIcons()">↺ Reset ikon</button>
    </div>
    <div class="hint">
      Reset ikon: wszyscy ruszają od startu (kółeczko) i kończą po 1 okrążeniu w tym samym punkcie.
    </div>
  </div>
</div>

<script>
  // --- KONFIGURACJA ---
  const SCALE = 0.2;
  const BASE_SPEED = 50;
  const TERRAIN_MODS = { 'FAST': 2.0, 'SLOW': 0.5, 'SWAMP': 0.2 };
  const TERRAIN_COLORS = { 'FAST': 'rgba(46, 204, 113, 0.6)', 'SLOW': 'rgba(241, 196, 15, 0.6)', 'SWAMP': 'rgba(231, 76, 60, 0.6)' };

  // Animation
  const ANIM_ACCEL = 2000;
  const TRAIL_MAX_POINTS = 90;
  const TRAIL_MAX_MS = 1600;

  // Linie: jedna grubość dla wszystkich tras
  const ROUTE_W = 3.2;

  // Dash for opposite-direction overlap segments
  const OPP_DASH = [10, 9];

  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');

  // offscreen static
  const staticLayer = document.createElement('canvas');
  staticLayer.width = canvas.width;
  staticLayer.height = canvas.height;
  const sctx = staticLayer.getContext('2d');
  let staticDirty = true;

  let animationRunning = false; // start stopped until routes computed
  let lastTs = null;
  let progAcc = 0;

  // domyślnie: User
  let overlapMode = "user";

  let gameState = {
    cities: [],
    terrains: [],
    userPath: [],
    cpuPath: [],
    isLocked: false,

    matrix: null,
    matrixReady: false,
    matrixVersion: 0,

    show: { user: true, cpu: true },

    // kolory stałe (bez pickerów)
    colors: { user: "#2563eb", cpu: "#e84118" },

    costs: { user: null, cpu: null },

    dirSign: null,

    // start city for race ring (set only after first click)
    raceStartId: null,

    solvingAll: false,
    pending: { aiCtrl: null },

    runners: {
      user:  { emoji: "🧍", dist: 0, trail: [], finished: false },
      cpu:   { emoji: "💻", dist: 0, trail: [], finished: false }
    },

    routeGeom: { user: null, cpu: null }
  };

  // --- helpers ---
  function setLoading(on, text="Python pracuje...") {
    const el = document.getElementById('loading');
    el.innerText = text;
    el.style.display = on ? 'block' : 'none';
  }

  function showError(msg) {
    const el = document.getElementById('error-modal');
    el.innerText = msg; el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 2600);
  }

  function markStaticDirty() { staticDirty = true; }

  function isUserRouteClosed() {
    const n = gameState.cities.length;
    const p = gameState.userPath;
    return n > 0 && p.length === n + 1 && p[0] === p[p.length - 1];
  }

  // --- color utils ---
  function hexToRgb(hex) {
    const h = (hex || "").trim();
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(h);
    if (!m) return {r:255,g:255,b:255};
    return { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) };
  }
  function rgbaStr({r,g,b}, a=1) { return `rgba(${r}, ${g}, ${b}, ${a})`; }

  // "Multiply" + lekkie podbicie jasności, żeby wspólny fragment był czytelny
  function blendMultiplyVivid(hexA, hexB) {
    const a = hexToRgb(hexA), b = hexToRgb(hexB);
    let r = Math.round((a.r * b.r) / 255);
    let g = Math.round((a.g * b.g) / 255);
    let bb = Math.round((a.b * b.b) / 255);

    // boost: rozjaśnij i zwiększ kontrast, żeby overlap był "wow"
    const boost = (x) => Math.max(0, Math.min(255, Math.round(x * 1.9 + 25)));
    return { r: boost(r), g: boost(g), b: boost(bb) };
  }

  function overlapColorRgb() {
    if (overlapMode === "user") return hexToRgb(gameState.colors.user);
    if (overlapMode === "comp") return hexToRgb(gameState.colors.cpu);
    return blendMultiplyVivid(gameState.colors.user, gameState.colors.cpu); // multiply
  }

  function visibleCount() {
    return (gameState.show.user ? 1 : 0) + (gameState.show.cpu ? 1 : 0);
  }

  function onlyVisibleWhich() {
    if (gameState.show.user && !gameState.show.cpu) return "user";
    if (!gameState.show.user && gameState.show.cpu) return "comp";
    return null;
  }

  function availableModes() {
    const cnt = visibleCount();
    if (cnt === 2) return ["user", "comp", "multiply"];
    const which = onlyVisibleWhich();
    if (which === "user") return ["user", "multiply"];
    if (which === "comp") return ["comp", "multiply"];
    return ["user", "comp", "multiply"];
  }

  function ensureOverlapModeValid() {
    const modes = availableModes();
    if (!modes.includes(overlapMode)) overlapMode = modes[0];
  }

  function overlapModeLabel() {
    const cnt = visibleCount();
    if (overlapMode === "user") return "User";
    if (overlapMode === "comp") return "Comp";
    if (cnt === 1) return "Multiply (wspólna)";
    return "Multiply";
  }

  function updateOverlapBtn() {
    const btn = document.getElementById('btnOverlapMode');
    if (btn) btn.innerText = "Tryb nakładania: " + overlapModeLabel();
  }

  function cycleOverlapMode() {
    ensureOverlapModeValid();
    const modes = availableModes();
    const idx = Math.max(0, modes.indexOf(overlapMode));
    overlapMode = modes[(idx + 1) % modes.length];
    updateOverlapBtn();
    markStaticDirty();
  }

  function updateLegendSamples() {
    document.getElementById('sampleUser').style.background = gameState.colors.user;
    document.getElementById('sampleCpu').style.background = gameState.colors.cpu;

    // stats border colors
    document.querySelectorAll('.stats-box')[0].style.borderColor = gameState.colors.user;
    document.querySelectorAll('.stats-box')[1].style.borderColor = gameState.colors.cpu;

    // dim eye buttons when hidden
    document.getElementById('btnToggleUser').classList.toggle('dim', !gameState.show.user);
    document.getElementById('btnToggleCpu').classList.toggle('dim', !gameState.show.cpu);

    ensureOverlapModeValid();
    updateOverlapBtn();
    markStaticDirty();
  }

  function setShow(key, val) {
    gameState.show[key] = !!val;
    // hide => keep moving, but restart trail for clarity
    if (!gameState.show[key]) gameState.runners[key].trail = [];
    updateLegendSamples();
  }

  // --- terrain ---
  function getTerrainAt(x, y) {
    for (let t of gameState.terrains) {
      let inside = false;
      const vs = t.vertices;
      for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
        let xi = vs[i].x, yi = vs[i].y, xj = vs[j].x, yj = vs[j].y;
        if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) inside = !inside;
      }
      if (inside) return TERRAIN_MODS[t.type];
    }
    return 1.0;
  }

  // symmetric cost via midpoint sampling
  function calculateCost(p1, p2) {
    let dx = p2.x - p1.x, dy = p2.y - p1.y;
    let distPx = Math.hypot(dx, dy);
    let steps = Math.max(1, Math.ceil(distPx / 4));

    let stepDist = (distPx * SCALE) / steps;
    let time = 0;

    for (let i = 0; i < steps; i++) {
      let t = (i + 0.5) / steps;
      let cx = p1.x + dx * t;
      let cy = p1.y + dy * t;
      let mod = getTerrainAt(cx, cy);
      time += stepDist / (BASE_SPEED * mod);
    }
    return time;
  }

  function abortPendingSolves() {
    try { gameState.pending.aiCtrl?.abort(); } catch(e) {}
    gameState.pending.aiCtrl = null;
  }

  // --- matrix once ---
  async function buildMatrixOnce() {
    const myVersion = ++gameState.matrixVersion;
    gameState.matrixReady = false;
    gameState.matrix = null;
    document.getElementById('matrixStatus').innerText = "liczę...";
    setLoading(true, "Liczę macierz kosztów...");

    const n = gameState.cities.length;
    let matrix = Array(n).fill(null).map(() => Array(n).fill(0));
    await new Promise(r => setTimeout(r, 20));

    for (let i = 0; i < n; i++) {
      matrix[i][i] = 0;
      for (let j = i + 1; j < n; j++) {
        let c = calculateCost(gameState.cities[i], gameState.cities[j]);
        c = parseFloat(c.toFixed(6));
        matrix[i][j] = c;
        matrix[j][i] = c;
      }
      if (i % 2 === 0) await new Promise(r => setTimeout(r, 0));
    }

    if (myVersion !== gameState.matrixVersion) return;

    gameState.matrix = matrix;
    gameState.matrixReady = true;
    document.getElementById('matrixStatus').innerText = "OK";
    setLoading(false);

    updateUserStats();
  }

  // --- cycle normalize + direction ---
  function normalizeCycleToStart(path, startId) {
    if (!path || path.length < 2) return path;
    if (path[path.length - 1] !== path[0]) return path;
    const core = path.slice(0, -1);
    const idx = core.indexOf(startId);
    if (idx === -1) return core.concat([core[0]]);
    const rotated = core.slice(idx).concat(core.slice(0, idx));
    rotated.push(startId);
    return rotated;
  }

  function reverseCycleKeepStart(cycle, startId) {
    if (!cycle || cycle.length < 3) return cycle;
    const core = cycle.slice(0, -1);
    const rev = [core[0]].concat(core.slice(1).reverse());
    rev.push(core[0]);
    return normalizeCycleToStart(rev, startId);
  }

  function cycleOrientationSign(cycle) {
    if (!cycle || cycle.length < 4) return 1;
    const core = cycle.slice(0, -1);
    let s = 0;
    for (let i = 0; i < core.length; i++) {
      const a = gameState.cities[core[i]];
      const b = gameState.cities[core[(i + 1) % core.length]];
      s += (a.x * b.y - b.x * a.y);
    }
    return s >= 0 ? 1 : -1;
  }

  function buildRouteGeomFromPath(path) {
    if (!path || path.length < 2) return null;
    const pts = path.map(id => ({ x: gameState.cities[id].x, y: gameState.cities[id].y }));
    const seg = [];
    let total = 0;
    for (let i = 0; i < pts.length - 1; i++) {
      const dx = pts[i+1].x - pts[i].x;
      const dy = pts[i+1].y - pts[i].y;
      const len = Math.hypot(dx, dy);
      seg.push(len);
      total += len;
    }
    if (total <= 0) return null;
    return { pts, seg, total };
  }

  function rebuildRouteGeom(key, isReference=false) {
    const startId = gameState.raceStartId;
    if (startId === null || startId === undefined) return;

    let p = (key === 'user') ? gameState.userPath : gameState.cpuPath;
    p = normalizeCycleToStart(p, startId);

    if (key === 'user') gameState.userPath = p;
    if (key === 'cpu') gameState.cpuPath = p;

    if (!p || p.length < 2) {
      gameState.routeGeom[key] = null;
      return;
    }

    if (isReference) {
      gameState.dirSign = cycleOrientationSign(p);
    } else if (gameState.dirSign !== null && p[p.length-1] === p[0]) {
      const s = cycleOrientationSign(p);
      if (s !== gameState.dirSign) {
        p = reverseCycleKeepStart(p, startId);
        if (key === 'cpu') gameState.cpuPath = p;
      }
    }

    gameState.routeGeom[key] = buildRouteGeomFromPath(p);
    gameState.runners[key].dist = 0;
    gameState.runners[key].finished = false;
    gameState.runners[key].trail = [];
  }

  // --- progress ---
  function progressPercent(key) {
    const geom = gameState.routeGeom[key];
    if (!geom || geom.total <= 0) return null;
    const d = gameState.runners[key].dist;
    return Math.max(0, Math.min(100, (d / geom.total) * 100));
  }

  function updateProgressUI() {
    const set = (id, key) => {
      const el = document.getElementById(id);
      const geom = gameState.routeGeom[key];
      const cost = gameState.costs[key];
      if (!geom || cost == null) { el.innerText = "--"; return; }
      if (gameState.runners[key].finished) { el.innerText = "100% 🏁"; return; }
      const p = progressPercent(key);
      el.innerText = (p === null) ? "--" : (Math.floor(p).toString() + "%");
    };
    set("userProg", "user");
    set("cpuProg", "cpu");
  }

  // --- animation mechanics ---
  function positionAlongRoute(key, distPx) {
    const geom = gameState.routeGeom[key];
    if (!geom) return null;
    let d = Math.max(0, Math.min(distPx, geom.total));
    const pts = geom.pts;
    const seg = geom.seg;

    for (let i = 0; i < seg.length; i++) {
      const L = seg[i];
      if (d <= L) {
        const t = (L === 0) ? 0 : (d / L);
        const x = pts[i].x + (pts[i+1].x - pts[i].x) * t;
        const y = pts[i].y + (pts[i+1].y - pts[i].y) * t;
        return { x, y };
      }
      d -= L;
    }
    return { x: pts[pts.length-1].x, y: pts[pts.length-1].y };
  }

  function speedPxPerSecAtPosition(x, y) {
    const mod = getTerrainAt(x, y);
    const pxPerHour = (BASE_SPEED * mod) / SCALE;
    const pxPerSec = (pxPerHour / 3600) * ANIM_ACCEL;
    return Math.max(25, Math.min(pxPerSec, 420));
  }

  function pushTrailPoint(key, x, y, nowMs) {
    const tr = gameState.runners[key].trail;
    tr.push({x, y, t: nowMs});
    if (tr.length > TRAIL_MAX_POINTS) tr.splice(0, tr.length - TRAIL_MAX_POINTS);
    while (tr.length > 0 && (nowMs - tr[0].t) > TRAIL_MAX_MS) tr.shift();
  }

  function drawTrail(key, nowMs) {
    if (!gameState.show[key]) return;
    const tr = gameState.runners[key].trail;
    if (!tr || tr.length < 2) return;

    ctx.save();
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.strokeStyle = (key === "user") ? rgbaStr(hexToRgb(gameState.colors.user), 1.0)
                                       : rgbaStr(hexToRgb(gameState.colors.cpu), 1.0);

    for (let i = 0; i < tr.length - 1; i++) {
      const a = tr[i], b = tr[i+1];
      const age = nowMs - a.t;
      const alpha = Math.max(0, 1.0 - (age / TRAIL_MAX_MS));

      const w = 3.8 + 6.8 * alpha;   // thick tails
      ctx.globalAlpha = 0.55 * alpha;
      ctx.lineWidth = w;

      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawRunner(key) {
    if (!gameState.show[key]) return;
    const geom = gameState.routeGeom[key];
    const cost = gameState.costs[key];
    if (!geom || cost == null) return;

    const pos = positionAlongRoute(key, gameState.runners[key].dist);
    if (!pos) return;

    ctx.save();
    ctx.font = "22px Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    ctx.globalAlpha = 0.95;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 14, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255,255,255,0.88)";
    ctx.fill();

    ctx.globalAlpha = 1.0;
    ctx.fillText(gameState.runners[key].emoji, pos.x, pos.y + 1);
    ctx.restore();
  }

  // --- drawing helpers ---
  function undirKey(a, b) { return (a < b) ? (a + "-" + b) : (b + "-" + a); }
  function dirKey(a, b) { return a + ">" + b; }

  // overlap: same direction (solid), opposite direction (dashed)
  function buildOverlapSets(userPath, cpuPath) {
    const cpuDir = new Set();
    const cpuUndir = new Set();
    for (let i = 0; i < cpuPath.length - 1; i++) {
      const a = cpuPath[i], b = cpuPath[i+1];
      cpuDir.add(dirKey(a,b));
      cpuUndir.add(undirKey(a,b));
    }

    const same = [];
    const opp = [];
    const oppSet = new Set();

    for (let i = 0; i < userPath.length - 1; i++) {
      const a = userPath[i], b = userPath[i+1];
      const u = undirKey(a,b);
      if (!cpuUndir.has(u)) continue;

      if (cpuDir.has(dirKey(a,b))) {
        same.push([a,b]);
      } else if (cpuDir.has(dirKey(b,a))) {
        opp.push([a,b]);
        oppSet.add(u);
      } else {
        same.push([a,b]);
      }
    }
    return { same, opp, oppSet };
  }

  // Draw polyline path; optional skipUndirSet to avoid "covering" dashed segments
  function drawFilteredPath(ctx2, path, strokeStyle, width, skipUndirSet=null) {
    if (!path || path.length < 2) return;
    ctx2.save();
    ctx2.strokeStyle = strokeStyle;
    ctx2.globalAlpha = 0.70;
    ctx2.lineWidth = width;
    ctx2.setLineDash([]);
    ctx2.lineJoin = "round";
    ctx2.lineCap = "round";

    ctx2.beginPath();
    let drawing = false;

    for (let i = 0; i < path.length - 1; i++) {
      const a = path[i], b = path[i+1];
      const u = undirKey(a,b);

      if (skipUndirSet && skipUndirSet.has(u)) {
        if (drawing) {
          ctx2.stroke();
          ctx2.beginPath();
          drawing = false;
        }
        continue;
      }

      const A = gameState.cities[a];
      const B = gameState.cities[b];
      if (!A || !B) continue;

      if (!drawing) {
        ctx2.moveTo(A.x, A.y);
        drawing = true;
      }
      ctx2.lineTo(B.x, B.y);
    }

    if (drawing) ctx2.stroke();
    ctx2.restore();
  }

  function drawSegments(ctx2, segments, strokeStyle, width, dash=[]) {
    if (!segments || segments.length === 0) return;
    ctx2.save();
    ctx2.strokeStyle = strokeStyle;
    ctx2.lineWidth = width;
    ctx2.setLineDash(dash);
    ctx2.lineJoin = "round";
    ctx2.lineCap = "round";
    ctx2.globalAlpha = 0.95;

    for (const [a,b] of segments) {
      const A = gameState.cities[a], B = gameState.cities[b];
      if (!A || !B) continue;
      ctx2.beginPath();
      ctx2.moveTo(A.x, A.y);
      ctx2.lineTo(B.x, B.y);
      ctx2.stroke();
    }
    ctx2.restore();
  }

  // --- static rendering ---
  function renderStaticLayer() {
    staticDirty = false;

    sctx.fillStyle = '#f5f6fa';
    sctx.fillRect(0, 0, staticLayer.width, staticLayer.height);

    // terrains
    gameState.terrains.forEach(t => {
      sctx.fillStyle = TERRAIN_COLORS[t.type];
      sctx.beginPath();
      t.vertices.forEach((v, i) => i === 0 ? sctx.moveTo(v.x, v.y) : sctx.lineTo(v.x, v.y));
      sctx.fill();
    });

    const showUser = !!gameState.show.user;
    const showCpu  = !!gameState.show.cpu;

    // rysuj user OD RAZU (już od 2 punktów), CPU dopiero jak istnieje
    const haveUserLine = gameState.userPath && gameState.userPath.length >= 2;
    const haveCpuLine  = gameState.cpuPath  && gameState.cpuPath.length  >= 2;

    const overlapReady = (isUserRouteClosed() && gameState.costs.user != null && gameState.costs.cpu != null && haveCpuLine);

    let overlap = null;
    if (overlapReady) overlap = buildOverlapSets(gameState.userPath, gameState.cpuPath);

    const bothVisible = showUser && showCpu;
    const oneVisible = (showUser ? 1 : 0) + (showCpu ? 1 : 0) === 1;

    const userStroke = rgbaStr(hexToRgb(gameState.colors.user), 1.0);
    const cpuStroke  = rgbaStr(hexToRgb(gameState.colors.cpu), 1.0);

    // --- ROUTES ---
    if (overlapMode === "multiply") {
      if (overlapReady) {
        const col = overlapColorRgb();
        const stroke = rgbaStr(col, 0.98);

        if (bothVisible) {
          // 2 trasy widoczne -> pełny widok + overlay jak wcześniej
          drawFilteredPath(sctx, gameState.cpuPath,  cpuStroke,  ROUTE_W, overlap.oppSet);
          drawFilteredPath(sctx, gameState.userPath, userStroke, ROUTE_W, overlap.oppSet);

          drawSegments(sctx, overlap.same, stroke, ROUTE_W, []);
          drawSegments(sctx, overlap.opp,  stroke, ROUTE_W, OPP_DASH);
        } else {
          // tylko jedna widoczna -> w multiply pokazuj TYLKO część wspólną
          drawSegments(sctx, overlap.same, stroke, ROUTE_W, []);
          drawSegments(sctx, overlap.opp,  stroke, ROUTE_W, OPP_DASH);
        }
      } else {
        // brak overlapu (AI jeszcze nie policzyło) -> pokazuj to co jest (żeby nie było "pusto")
        if (showCpu && haveCpuLine)  drawFilteredPath(sctx, gameState.cpuPath,  cpuStroke,  ROUTE_W, null);
        if (showUser && haveUserLine) drawFilteredPath(sctx, gameState.userPath, userStroke, ROUTE_W, null);
      }
    } else {
      // user/comp
      if (showCpu && haveCpuLine) {
        const skip = (bothVisible && overlapReady) ? overlap.oppSet : null;
        drawFilteredPath(sctx, gameState.cpuPath, cpuStroke, ROUTE_W, skip);
      }
      if (showUser && haveUserLine) {
        const skip = (bothVisible && overlapReady) ? overlap.oppSet : null;
        drawFilteredPath(sctx, gameState.userPath, userStroke, ROUTE_W, skip);
      }

      // overlay (same+opp) TYLKO gdy obie trasy są widoczne
      if (bothVisible && overlapReady) {
        const col = overlapColorRgb();
        const stroke = rgbaStr(col, 0.98);
        drawSegments(sctx, overlap.same, stroke, ROUTE_W, []);
        drawSegments(sctx, overlap.opp,  stroke, ROUTE_W, OPP_DASH);
      }
    }

    // cities as dots (no numbers)
    gameState.cities.forEach(c => {
      sctx.beginPath();
      sctx.arc(c.x, c.y, 7.5, 0, Math.PI*2);

      const inPath = gameState.userPath.includes(c.id);
      sctx.fillStyle = inPath ? "#2ecc71" : "#2f3640";
      sctx.fill();

      sctx.strokeStyle = "white";
      sctx.lineWidth = 2;
      sctx.stroke();
    });

    // start ring only after first click
    if (gameState.raceStartId !== null && gameState.userPath.length >= 1) {
      const sc = gameState.cities[gameState.raceStartId];
      if (sc) {
        sctx.save();
        sctx.beginPath();
        sctx.arc(sc.x, sc.y, 16, 0, Math.PI*2);
        sctx.strokeStyle = "rgba(22, 160, 133, 0.95)";
        sctx.lineWidth = 3;
        sctx.setLineDash([]);
        sctx.stroke();
        sctx.restore();
      }
    }
  }

  // --- animation loop ---
  function tick(ts) {
    if (lastTs === null) lastTs = ts;
    const dt = Math.min(0.05, (ts - lastTs) / 1000);
    lastTs = ts;

    const nowMs = performance.now();

    // RUCH ZAWSZE DZIAŁA (nawet gdy trasa ukryta)
    if (animationRunning) {
      ["user","cpu"].forEach(key => {
        const geom = gameState.routeGeom[key];
        const cost = gameState.costs[key];
        if (!geom || cost == null) return;
        if (gameState.runners[key].finished) return;

        const pos = positionAlongRoute(key, gameState.runners[key].dist);
        if (!pos) return;

        const v = speedPxPerSecAtPosition(pos.x, pos.y);
        gameState.runners[key].dist += v * dt;

        if (gameState.runners[key].dist >= geom.total) {
          gameState.runners[key].dist = geom.total;
          gameState.runners[key].finished = true;
          const endPos = positionAlongRoute(key, geom.total);
          if (endPos && gameState.show[key]) pushTrailPoint(key, endPos.x, endPos.y, nowMs);
        } else {
          const pos2 = positionAlongRoute(key, gameState.runners[key].dist);
          if (pos2 && gameState.show[key]) pushTrailPoint(key, pos2.x, pos2.y, nowMs);
        }
      });
    }

    if (staticDirty) renderStaticLayer();
    ctx.drawImage(staticLayer, 0, 0);

    // tails then runners
    drawTrail("cpu", nowMs);
    drawTrail("user", nowMs);

    drawRunner("cpu");
    drawRunner("user");

    progAcc += dt;
    if (progAcc >= 0.10) {
      progAcc = 0;
      updateProgressUI();
    }

    requestAnimationFrame(tick);
  }

  function setRaceNotReady(text="⏳ Czekam na trasy...") {
    animationRunning = false;
    const btn = document.getElementById('btnAnimToggle');
    if (btn) btn.innerText = text;
    lastTs = null;
  }

  function setRaceReadyAndStart() {
    const btn = document.getElementById('btnAnimToggle');
    if (btn) btn.innerText = "⏸ Pauza";
    animationRunning = true;
    lastTs = null;
  }

  function toggleAnimation() {
    const ok = (gameState.costs.user != null && gameState.costs.cpu != null);
    if (!ok) return;

    animationRunning = !animationRunning;
    const btn = document.getElementById('btnAnimToggle');
    btn.innerText = animationRunning ? "⏸ Pauza" : "▶ Start";
    lastTs = null;
  }

  function resetIcons() {
    ["user","cpu"].forEach(k => {
      gameState.runners[k].dist = 0;
      gameState.runners[k].finished = false;
      gameState.runners[k].trail = [];
    });

    const nowMs = performance.now();
    ["user","cpu"].forEach(k => {
      if (!gameState.routeGeom[k]) return;
      if (gameState.costs[k] == null) return;
      const pos = positionAlongRoute(k, 0);
      if (pos && gameState.show[k]) pushTrailPoint(k, pos.x, pos.y, nowMs);
    });

    updateProgressUI();
    lastTs = null;
  }

  function updateUserStats() {
    const p = gameState.userPath;

    // pokaż czas nawet dla częściowej trasy
    if (p.length <= 1) {
      document.getElementById('userTime').innerText = "0.00 h";
      gameState.costs.user = null;
      gameState.routeGeom.user = null;
      gameState.dirSign = null;
      return;
    }

    let t = 0;
    if (gameState.matrixReady && gameState.matrix) {
      for (let i = 0; i < p.length - 1; i++) t += gameState.matrix[p[i]][p[i+1]];
    } else {
      for (let i = 0; i < p.length - 1; i++) t += calculateCost(gameState.cities[p[i]], gameState.cities[p[i+1]]);
    }
    document.getElementById('userTime').innerText = t.toFixed(2) + " h";

    if (isUserRouteClosed() && gameState.matrixReady) {
      gameState.costs.user = t;
      rebuildRouteGeom('user', true);
      resetIcons();
      markStaticDirty();
    } else {
      gameState.costs.user = null;
      gameState.routeGeom.user = null;
      gameState.dirSign = null;
    }
  }

  async function solveAIBackground() {
    if (!gameState.matrixReady || !gameState.matrix) return;
    if (!isUserRouteClosed()) return;
    if (gameState.solvingAll) return;
    if (gameState.raceStartId === null || gameState.raceStartId === undefined) return;

    gameState.solvingAll = true;
    abortPendingSolves();

    setRaceNotReady("⏳ Liczę trasę AI...");
    setLoading(true, "Liczę trasę AI...");

    document.getElementById('cpuTime').innerText = "liczę...";
    document.getElementById('cpuMeta').innerText = "--";
    gameState.cpuPath = [];
    gameState.costs.cpu = null;
    gameState.routeGeom.cpu = null;

    const version = gameState.matrixVersion;
    const ctrl = new AbortController();
    gameState.pending.aiCtrl = ctrl;

    try {
      const res = await fetch('/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matrix: gameState.matrix, start: gameState.raceStartId }),
        signal: ctrl.signal
      });

      if (!res.ok) {
        const txt = await res.text();
        let msg = txt;
        try { msg = (JSON.parse(txt).error || txt); } catch(_) {}
        throw new Error(msg);
      }

      const data = await res.json();
      if (version !== gameState.matrixVersion) return;

      document.getElementById('cpuTime').innerText = data.cost.toFixed(2) + " h";
      document.getElementById('cpuMeta').innerText = data.meta || "--";
      gameState.cpuPath = data.path;
      gameState.costs.cpu = data.cost;

      rebuildRouteGeom('cpu', false);
      resetIcons();
      setLoading(false);

      if (gameState.costs.user != null && gameState.costs.cpu != null) {
        setRaceReadyAndStart();
      } else {
        setRaceNotReady("⏳ Brak tras...");
      }
      markStaticDirty();

    } catch (e) {
      if (e.name === "AbortError") return;
      showError(e.message);
      document.getElementById('cpuTime').innerText = "-- h";
      gameState.cpuPath = [];
      gameState.costs.cpu = null;
      gameState.routeGeom.cpu = null;
      setRaceNotReady("⏳ Brak tras...");
      markStaticDirty();
    } finally {
      gameState.solvingAll = false;
      setLoading(false);
      if (gameState.pending.aiCtrl === ctrl) gameState.pending.aiCtrl = null;
    }
  }

  // --- click: build user path ---
  canvas.addEventListener('mousedown', e => {
    if (gameState.isLocked) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);

    const city = gameState.cities.find(c => Math.hypot(c.x - x, c.y - y) < 20);
    if (!city) return;

    // if already closed: ignore (no changing start later)
    if (isUserRouteClosed()) return;

    const path = gameState.userPath;

    if (path.length === 0) {
      path.push(city.id);
      gameState.raceStartId = city.id; // start fixed = pierwszy klik
      updateUserStats();
      setRaceNotReady();
      markStaticDirty();
      return;
    }

    if (path.length > 0 && path[path.length - 1] === city.id) return;

    if (path.includes(city.id)) {
      if (city.id === path[0] && path.length === gameState.cities.length) {
        path.push(city.id); // close cycle
      }
    } else {
      path.push(city.id);
    }

    updateUserStats();
    setRaceNotReady();
    markStaticDirty();

    if (isUserRouteClosed() && gameState.matrixReady) {
      gameState.userPath = normalizeCycleToStart(gameState.userPath, gameState.raceStartId);
      updateUserStats();
      solveAIBackground();
    }
  });

  function resetRoute() {
    abortPendingSolves();
    gameState.solvingAll = false;

    gameState.userPath = [];
    gameState.cpuPath = [];
    gameState.costs = { user: null, cpu: null };
    gameState.routeGeom = { user: null, cpu: null };
    gameState.dirSign = null;

    gameState.raceStartId = null;

    document.getElementById('cpuTime').innerText = "-- h";
    document.getElementById('userTime').innerText = "0.00 h";
    document.getElementById('cpuMeta').innerText = "--";
    document.getElementById('userProg').innerText = "--";
    document.getElementById('cpuProg').innerText = "--";

    setRaceNotReady();
    resetIcons();
    markStaticDirty();
  }

  async function generateMap() {
    let n = parseInt(document.getElementById('pointsCount').value, 10);
    if (!Number.isFinite(n) || n < 3) { showError("Podaj liczbę miast ≥ 3."); return; }
    if (n > 120) { showError("Max 120 (dla płynności)."); return; }

    abortPendingSolves();
    gameState.solvingAll = false;

    gameState.cities = [];
    gameState.terrains = [];
    gameState.userPath = [];
    gameState.cpuPath = [];
    gameState.costs = { user: null, cpu: null };
    gameState.routeGeom = { user: null, cpu: null };
    gameState.dirSign = null;
    gameState.raceStartId = null;

    ["user","cpu"].forEach(k => {
      gameState.runners[k].dist = 0;
      gameState.runners[k].finished = false;
      gameState.runners[k].trail = [];
    });

    document.getElementById('userTime').innerText = "0.00 h";
    document.getElementById('cpuTime').innerText = "-- h";
    document.getElementById('matrixStatus').innerText = "--";
    document.getElementById('cpuMeta').innerText = "--";
    document.getElementById('userProg').innerText = "--";
    document.getElementById('cpuProg').innerText = "--";

    setRaceNotReady();
    resetIcons();
    markStaticDirty();

    try {
      const res = await fetch('/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ n_points: n })
      });
      if (!res.ok) throw new Error("Błąd serwera");
      const data = await res.json();

      gameState.cities = data.cities;
      gameState.terrains = data.terrains;

      markStaticDirty();
      buildMatrixOnce();

    } catch(e) {
      showError("Błąd połączenia: " + e);
    }
  }

  // --- UI wiring ---
  function initLegendControls() {
    document.getElementById('btnOverlapMode').addEventListener('click', cycleOverlapMode);

    document.getElementById('btnToggleUser').addEventListener('click', () => {
      setShow('user', !gameState.show.user);
      document.getElementById('btnToggleUser').innerText = gameState.show.user ? "👁" : "🚫";
    });
    document.getElementById('btnToggleCpu').addEventListener('click', () => {
      setShow('cpu', !gameState.show.cpu);
      document.getElementById('btnToggleCpu').innerText = gameState.show.cpu ? "👁" : "🚫";
    });

    document.getElementById('btnToggleUser').innerText = "👁";
    document.getElementById('btnToggleCpu').innerText = "👁";

    // start: user
    overlapMode = "user";
    updateLegendSamples();
  }

  window.onload = () => {
    initLegendControls();
    generateMap();
    requestAnimationFrame(tick);
  };
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return "Komi AI Ultimate działa 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

@app.route('/generate', methods=['POST'])
def generate_map():
    try:
        data = request.json or {}
        n = int(data.get('n_points', 10))

        if n < 3:
            return jsonify({'error': 'Min 3 miasta.'}), 400
        if n > 120:
            return jsonify({'error': 'Limit backend 120.'}), 400

        width, height = 1000, 800

        terrains = []
        attempts = 0
        while len(terrains) < 8 and attempts < 400:
            attempts += 1
            t_radius = random.uniform(60, 100)
            x = random.uniform(t_radius + 20, width - t_radius - 20)
            y = random.uniform(t_radius + 20, height - t_radius - 20)

            overlap = False
            for t in terrains:
                if math.hypot(t['x'] - x, t['y'] - y) < (t['radius'] + t_radius + 50):
                    overlap = True
                    break

            if not overlap:
                t_type = random.choice(['FAST', 'SLOW', 'SWAMP'])
                verts = []
                num = random.randint(8, 12)
                for i in range(num):
                    a = 2 * math.pi * i / num
                    r = t_radius * random.uniform(0.7, 1.0)
                    verts.append({'x': x + math.cos(a) * r, 'y': y + math.sin(a) * r})
                terrains.append({'x': x, 'y': y, 'radius': t_radius, 'type': t_type, 'vertices': verts})

        cities = []
        attempts = 0
        max_attempts = 15000 if n > 80 else 6000 if n > 50 else 2500
        while len(cities) < n and attempts < max_attempts:
            attempts += 1
            cx, cy = random.uniform(50, width - 50), random.uniform(50, height - 50)
            if not any(math.hypot(c['x'] - cx, c['y'] - cy) < 60 for c in cities):
                cities.append({'id': len(cities), 'x': cx, 'y': cy})

        if len(cities) < n:
            return jsonify({'error': f'Nie udało się rozmieścić {n} miast z odstępem 60px. Spróbuj mniejszej liczby.'}), 400

        return jsonify({'cities': cities, 'terrains': terrains})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---- AI: ILS (randomized NN) + 2-opt + double-bridge, time-bounded ----
def route_cost(matrix, route):
    return sum(matrix[route[i]][route[i + 1]] for i in range(len(route) - 1))

def two_opt_first_improve(matrix, route, max_checks=None):
    n = len(matrix)
    checks = 0
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            a, b = route[i - 1], route[i]
            for j in range(i + 1, n):
                if j - i == 1:
                    continue
                c, d = route[j], route[j + 1]
                d1 = matrix[a][b] + matrix[c][d]
                d2 = matrix[a][c] + matrix[b][d]
                if d2 < d1 - 1e-9:
                    route[i:j + 1] = reversed(route[i:j + 1])
                    improved = True
                    break
                checks += 1
                if max_checks is not None and checks >= max_checks:
                    return route
            if improved:
                break
    return route

def double_bridge(route):
    n = len(route) - 1
    core = route[:-1]
    start = core[0]
    if n < 8:
        return route[:]
    cuts = sorted(random.sample(range(1, n), 4))
    a, b, c, d = cuts
    new_core = core[:a] + core[c:d] + core[b:c] + core[a:b] + core[d:]
    if new_core[0] != start:
        idx = new_core.index(start)
        new_core = new_core[idx:] + new_core[:idx]
    return new_core + [start]

def randomized_nearest_neighbor(matrix, start=0, k=5):
    n = len(matrix)
    route = [start]
    unvisited = set(range(n))
    unvisited.remove(start)
    curr = start

    neigh = []
    for i in range(n):
        order = list(range(n))
        order.sort(key=lambda j: matrix[i][j])
        neigh.append(order)

    while unvisited:
        candidates = [j for j in neigh[curr] if j in unvisited]
        if not candidates:
            nxt = unvisited.pop()
        else:
            take = candidates[:max(1, min(k, len(candidates)))]
            weights = [1.0 / (r + 1) for r in range(len(take))]
            s = sum(weights)
            x = random.random() * s
            acc = 0.0
            nxt = take[-1]
            for node, w in zip(take, weights):
                acc += w
                if x <= acc:
                    nxt = node
                    break
            unvisited.remove(nxt)
        route.append(nxt)
        curr = nxt

    route.append(start)
    return route

@app.route('/solve', methods=['POST'])
def solve_smart_ai():
    try:
        payload = request.json or {}
        matrix = payload.get('matrix')
        if matrix is None:
            return jsonify({'error': 'Brak macierzy'}), 400

        n = len(matrix)
        if n < 3:
            return jsonify({'error': 'Min 3 miasta'}), 400

        start = int(payload.get('start', 0))
        if start < 0 or start >= n:
            start = 0

        if n <= 30:
            time_limit = 1.2
        elif n <= 60:
            time_limit = 1.8
        elif n <= 90:
            time_limit = 2.2
        else:
            time_limit = 2.6

        t0 = time.perf_counter()

        if n <= 60:
            max_checks = None
        elif n <= 90:
            max_checks = 25000
        else:
            max_checks = 20000

        best_route = None
        best_cost = float('inf')

        restarts = 0
        loops = 0

        while time.perf_counter() - t0 < time_limit:
            restarts += 1
            route = randomized_nearest_neighbor(matrix, start=start, k=6 if n <= 60 else 5)
            route = two_opt_first_improve(matrix, route, max_checks=max_checks)
            cost = route_cost(matrix, route)

            if cost < best_cost:
                best_cost = cost
                best_route = route[:]

            inner_steps = 6 if n <= 60 else 4
            for _ in range(inner_steps):
                loops += 1
                if time.perf_counter() - t0 >= time_limit:
                    break
                pert = double_bridge(route)
                pert = two_opt_first_improve(matrix, pert, max_checks=max_checks)
                c2 = route_cost(matrix, pert)

                if c2 < cost or random.random() < 0.08:
                    route, cost = pert, c2
                    if cost < best_cost:
                        best_cost = cost
                        best_route = route[:]

        if best_route is None:
            best_route = randomized_nearest_neighbor(matrix, start=start, k=5)
            best_route = two_opt_first_improve(matrix, best_route, max_checks=max_checks)
            best_cost = route_cost(matrix, best_route)

        meta = f"{time_limit:.1f}s | restarty: {restarts} | kroki: {loops}"
        return jsonify({'path': best_route, 'cost': float(best_cost), 'meta': meta})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # lokalnie OK; na Railway i tak odpalisz gunicornem
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
