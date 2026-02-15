from flask import Flask, render_template_string, jsonify, request
import os
import math
import random
import time
import itertools

app = Flask(__name__)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Komi AI: Algorithm Select</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: 'Segoe UI', sans-serif; background: #1e272e; color: #d2dae2; margin: 0; height: 100vh; display: flex; flex-direction: column; overflow: hidden; touch-action: none; }

    .container { display: flex; width: 100%; height: 100%; }

    /* Desktop */
    .map-area { flex: 3; background: #000; display: flex; justify-content: center; align-items: center; position: relative; overflow: hidden; }
    .sidebar { flex: 1; background: #2f3640; padding: 20px; border-left: 2px solid #485460; overflow-y: auto; min-width: 350px; z-index: 10; }

    canvas {
      background: #f5f6fa;
      box-shadow: 0 0 30px rgba(0,0,0,0.5);
      border-radius: 4px;
      cursor: crosshair;
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
      touch-action: none;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
    }

    h1 { color: #f1c40f; margin: 0 0 15px 0; font-size: 1.6rem; text-align: center; }
    h2 { color: #0fb9b1; font-size: 1.1rem; border-bottom: 1px solid #485460; padding-bottom: 5px; margin-top: 22px; margin-bottom: 10px; }
    p.info { font-size: 0.85rem; color: #bdc3c7; margin-bottom: 15px; text-align: center; font-style: italic; }

    .legend-container { background: #1e272e; padding: 10px; border-radius: 6px; border: 1px solid #485460; font-size: 0.85rem; }
    
    #terrain-legend-items { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
    .legend-item { 
        display: flex; align-items: center; gap: 6px; font-size: 0.85rem; width: 48%; 
        background: rgba(255,255,255,0.05); padding: 4px; border-radius: 4px;
    }
    .l-box { width: 18px; height: 18px; border-radius: 3px; border: 1px solid rgba(0,0,0,0.2); box-shadow: inset 0 0 2px rgba(255,255,255,0.2); }
    .legend-val { font-weight: bold; text-shadow: 1px 1px 1px rgba(0,0,0,0.5); }

    .pill-btn {
      width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
      color: #d2dae2; padding: 10px; border-radius: 10px; cursor: pointer; font-weight: 700; margin-top: 8px;
    }

    /* Inputy i Selecty */
    .control-group { margin-bottom: 10px; }
    .control-label { font-size: 0.8rem; color: #bdc3c7; margin-bottom: 4px; display: block; }
    
    input[type="number"], select {
      width: 100%; padding: 10px; background: #1e272e; border: 1px solid #485460;
      color: white; border-radius: 4px; font-weight: bold; font-family: inherit;
    }
    select { cursor: pointer; }
    input[type="number"] { text-align: center; }

    button {
      width: 100%; padding: 12px; margin-top: 10px; border: none; border-radius: 4px;
      font-weight: bold; cursor: pointer; transition: 0.2s; font-size: 0.9rem;
    }
    button:disabled { background: #57606f !important; cursor: not-allowed; opacity: 0.75; }

    .btn-gen { background: #0984e3; color: white; }
    .btn-reset { background: #d63031; color: white; }
    .btn-anim { background: #34495e; color: white; }
    .btn-anim2 { background: #2c3e50; color: white; }

    .row-2btn { display: flex; gap: 10px; }
    .row-2btn button { width: 100%; }

    .stats-box { background: #1e272e; padding: 12px; border-radius: 6px; margin-bottom: 10px; border-left: 5px solid #bdc3c7; transition: transform 0.2s, background 0.3s; }
    .stat-val { font-size: 1.4rem; font-weight: bold; display: block; margin-top: 3px; }
    
    .winner-glow { background: #16a085; transform: scale(1.02); border-left-color: #fff; }
    .loser-dim { opacity: 0.6; }

    #loading { display: none; color: #f1c40f; font-weight: bold; text-align: center; margin-top: 10px; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }

    #error-modal, #result-modal { display: none; position: fixed; top: 20px; left: 50%; transform: translateX(-50%); padding: 15px 30px; border-radius: 8px; z-index: 1000; text-align: center; font-weight: bold; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
    #error-modal { background: #c0392b; color: white; }
    #result-modal { background: #27ae60; color: white; top: 40%; font-size: 1.5rem; }

    /* MOBILE */
    @media (max-width: 900px) {
      .container { flex-direction: column; }
      .map-area { flex: none; height: 55vh; width: 100%; border-bottom: 2px solid #485460; padding: 0; }
      .sidebar { flex: 1; width: 100%; min-width: 0; border-left: none; padding: 15px; box-shadow: 0 -5px 20px rgba(0,0,0,0.3); }
      h1 { font-size: 1.3rem; margin-bottom: 10px; }
      .info { display: none; }
      canvas { width: 100%; height: 100%; }
    }
  </style>
</head>
<body>

<div id="error-modal">Błąd</div>
<div id="result-modal">Wynik!</div>

<div class="container">
  <div class="map-area">
    <canvas id="gameCanvas" width="1000" height="800"></canvas>
  </div>

  <div class="sidebar">
    <h1>Komi: Algo Select</h1>
    <p class="info">Klikaj miasta, narysuj pętlę. Po domknięciu wyścig rusza!</p>

    <div class="legend-container">
      <div style="font-weight:bold; margin-bottom:8px; color:#fff;">Teren (Mnożnik):</div>
      <div id="terrain-legend-items"></div>

      <div style="font-weight:bold; margin:12px 0 6px 0; color:#fff;">Widoczność:</div>
      <div style="display:flex; gap:10px;">
        <button class="pill-btn" id="btnToggleUser" style="margin-top:0; padding:6px; font-size:0.8rem; border-color:#2563eb; color:#2563eb;">🧍 User</button>
        <button class="pill-btn" id="btnToggleCpu" style="margin-top:0; padding:6px; font-size:0.8rem; border-color:#be2edd; color:#be2edd;">💻 AI</button>
      </div>

      <button class="pill-btn" id="btnOverlapMode" type="button" style="padding:8px; font-size:0.85rem;">Nakładanie: User</button>
    </div>

    <h2 style="margin-top:15px; margin-bottom:5px;">Akcje</h2>
    
    <div style="display:flex; gap:10px;">
        <div class="control-group" style="flex:1;">
            <label class="control-label">Liczba miast:</label>
            <input type="number" id="pointsCount" value="10" min="3" max="80" onchange="updateAlgoList()">
        </div>
        <div class="control-group" style="flex:1;">
            <label class="control-label">Max czas AI (s):</label>
            <input type="number" id="aiTimeLimit" value="2.0" min="0.5" max="60.0" step="0.5">
        </div>
    </div>

    <div class="control-group">
        <label class="control-label">Algorytm AI:</label>
        <select id="algoSelect">
            </select>
    </div>

    <div class="row-2btn">
      <button class="btn-gen" onclick="generateMap()" style="margin-top:0;">Generuj</button>
      <button class="btn-reset" onclick="resetRoute()" style="margin-top:0;">Reset</button>
    </div>

    <h2 style="margin-top:15px; margin-bottom:5px;">Wyniki</h2>
    <div style="display:flex; gap:10px;">
        <div class="stats-box" id="boxUser" style="flex:1; border-color:#2563eb; padding:8px; margin:0;">
          <div style="font-size:0.8rem;">Ty</div>
          <span class="stat-val" id="userTime" style="font-size:1.1rem;">0.00h</span>
        </div>
        <div class="stats-box" id="boxCpu" style="flex:1; border-color:#be2edd; padding:8px; margin:0;">
          <div style="font-size:0.8rem;">AI</div>
          <span class="stat-val" id="cpuTime" style="font-size:1.1rem;">--</span>
        </div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#7f8c8d; margin-top:5px;">
        <span>Twój postęp: <span id="userProg">--</span></span>
        <span>AI postęp: <span id="cpuProg">--</span></span>
    </div>

    <div id="loading">AI liczy...</div>

    <div class="row-2btn" style="margin-top:10px;">
      <button class="btn-anim" id="btnAnimToggle" onclick="toggleAnimation()">Start</button>
      <button class="btn-anim2" id="btnAnimReset" onclick="resetIcons()">Reset ikon</button>
    </div>
  </div>
</div>

<script>
  // --- KONFIGURACJA ---
  const SCALE = 0.2;
  const BASE_SPEED = 50;
  const COLORS = { user: "#2563eb", cpu: "#d012be" }; 

  const ANIM_ACCEL = 2000;
  const TRAIL_MAX_POINTS = 90;
  const TRAIL_MAX_MS = 1600;
  const ROUTE_W = 3.2;
  const OPP_DASH = [10, 9];
  const HIT_RADIUS_PX = 44;

  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');

  const staticLayer = document.createElement('canvas');
  staticLayer.width = canvas.width;
  staticLayer.height = canvas.height;
  const sctx = staticLayer.getContext('2d');
  let staticDirty = true;

  let animationRunning = false;
  let lastTs = null;
  let progAcc = 0;
  let overlapMode = "user";

  // Cache dla wybranego algorytmu
  let selectedAlgoCache = "ils";

  const pointer = {
    active: false,
    id: null,
    hoverId: null,
    lastClientX: 0,
    lastClientY: 0
  };

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
    colors: COLORS,
    costs: { user: null, cpu: null },
    dirSign: null,
    raceStartId: null,
    solvingAll: false,
    resultsRevealed: false,
    pending: { aiCtrl: null },
    runners: {
      user:  { emoji: "🧍", dist: 0, trail: [], finished: false },
      cpu:   { emoji: "💻", dist: 0, trail: [], finished: false }
    },
    routeGeom: { user: null, cpu: null }
  };

  // --- LOGIKA LISTY ALGORYTMÓW ---
  const ALGORITHMS = [
      { id: 'random', name: 'Losowy (Bardzo Słaby)', maxPoints: 9999 },
      { id: 'nn', name: 'Najbliższy Sąsiad (Słaby)', maxPoints: 9999 },
      { id: 'nn_2opt', name: 'Szybki 2-Opt (Średni)', maxPoints: 9999 },
      { id: 'ils', name: 'Komi AI (Dobry - Domyślny)', maxPoints: 9999 },
      { id: 'brute', name: 'Brute Force (Optymalny)', maxPoints: 10 } // Tylko dla max 10 miast
  ];

  function updateAlgoList() {
      const n = parseInt(document.getElementById('pointsCount').value, 10) || 10;
      const select = document.getElementById('algoSelect');
      const currentVal = select.value || selectedAlgoCache;

      select.innerHTML = "";
      
      let validOptions = [];
      ALGORITHMS.forEach(algo => {
          if (n <= algo.maxPoints) {
              const opt = document.createElement('option');
              opt.value = algo.id;
              opt.innerText = algo.name;
              select.appendChild(opt);
              validOptions.push(algo.id);
          }
      });

      // Przywróć wybór jeśli nadal jest ważny, w przeciwnym razie ustaw domyślny
      if (validOptions.includes(currentVal)) {
          select.value = currentVal;
      } else {
          select.value = 'ils'; // Fallback
      }
  }
  
  // Zapisz wybór użytkownika
  document.getElementById('algoSelect').addEventListener('change', (e) => {
      selectedAlgoCache = e.target.value;
  });

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

  function showResultModal(text, color) {
    const el = document.getElementById('result-modal');
    el.innerText = text;
    el.style.backgroundColor = color;
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3500);
  }

  function revealResults() {
      if (gameState.resultsRevealed) return;
      gameState.resultsRevealed = true;

      if (gameState.costs.cpu !== null) {
          document.getElementById('cpuTime').innerText = gameState.costs.cpu.toFixed(2) + "h";
      }

      const u = gameState.costs.user;
      const c = gameState.costs.cpu;
      const boxUser = document.getElementById('boxUser');
      const boxCpu = document.getElementById('boxCpu');

      boxUser.classList.remove('winner-glow', 'loser-dim');
      boxCpu.classList.remove('winner-glow', 'loser-dim');

      if (u !== null && c !== null) {
          // POPRAWIONA LOGIKA REMISU (Epsilon 0.01h)
          const diff = Math.abs(u - c);
          
          if (diff < 0.01) {
             showResultModal("REMIS! 🤝", "#f39c12");
          } else if (u < c) {
              showResultModal("WYGRANA! 🎉", "#27ae60");
              boxUser.classList.add('winner-glow');
              boxCpu.classList.add('loser-dim');
          } else {
              showResultModal("PRZEGRANA... 💀", "#c0392b");
              boxUser.classList.add('loser-dim');
              boxCpu.classList.add('winner-glow');
          }
      }
  }

  function markStaticDirty() { staticDirty = true; }

  function isUserRouteClosed() {
    const n = gameState.cities.length;
    const p = gameState.userPath;
    return n > 0 && p.length === n + 1 && p[0] === p[p.length - 1];
  }

  function hexToRgb(hex) {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!m) return {r:255,g:255,b:255};
    return { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) };
  }
  function rgbaStr({r,g,b}, a=1) { return `rgba(${r}, ${g}, ${b}, ${a})`; }

  function overlapColorRgb() {
    if (overlapMode === "user") return hexToRgb(gameState.colors.user);
    if (overlapMode === "comp") return hexToRgb(gameState.colors.cpu);
    return {r:0,g:0,b:0}; 
  }

  function cycleOverlapMode() {
    const modes = ["user", "comp", "multiply"];
    const idx = modes.indexOf(overlapMode);
    overlapMode = modes[(idx + 1) % modes.length];
    document.getElementById('btnOverlapMode').innerText =
      "Nakładanie: " + (overlapMode === 'multiply' ? 'Wspólne' : (overlapMode === 'comp' ? 'AI' : 'User'));
    markStaticDirty();
  }

  function setShow(key, val) {
    gameState.show[key] = !!val;
    if (!gameState.show[key]) gameState.runners[key].trail = [];
    const btn = document.getElementById(key === 'user' ? 'btnToggleUser' : 'btnToggleCpu');
    btn.style.opacity = val ? '1' : '0.4';
    markStaticDirty();
  }

  function getTerrainAt(x, y) {
    for (let t of gameState.terrains) {
      let inside = false;
      const vs = t.vertices;
      for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
        let xi = vs[i].x, yi = vs[i].y, xj = vs[j].x, yj = vs[j].y;
        if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) inside = !inside;
      }
      if (inside) return t.val;
    }
    return 1.0;
  }

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

  async function buildMatrixOnce() {
    const myVersion = ++gameState.matrixVersion;
    gameState.matrixReady = false;
    gameState.matrix = null;
    setLoading(true, "Liczę mapę...");

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
    setLoading(false);
    updateUserStats();
  }

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

  function updateProgressUI() {
    const set = (id, key) => {
      const el = document.getElementById(id);
      const geom = gameState.routeGeom[key];
      const cost = gameState.costs[key];
      if (!geom || cost == null) { el.innerText = "--"; return; }
      if (gameState.runners[key].finished) { el.innerText = "100%"; return; }
      const p = Math.max(0, Math.min(100, (gameState.runners[key].dist / geom.total) * 100));
      el.innerText = Math.floor(p) + "%";
    };
    set("userProg", "user");
    set("cpuProg", "cpu");
  }

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
    return Math.max(20, Math.min(pxPerSec, 800));
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
      const w = 3.8 + 6.8 * alpha;
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
    ctx.font = "22px Segoe UI Emoji";
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

  function drawHoverRing() {
    if (pointer.hoverId === null || pointer.hoverId === undefined) return;
    const c = gameState.cities[pointer.hoverId];
    if (!c) return;
    ctx.save();
    ctx.shadowColor = "rgba(0,0,0,0.35)";
    ctx.shadowBlur = 10;
    ctx.globalAlpha = 0.98;
    ctx.beginPath();
    ctx.arc(c.x, c.y, 20, 0, Math.PI * 2);
    ctx.lineWidth = 3.5;
    ctx.strokeStyle = "rgba(255,255,255,0.95)";
    ctx.stroke();
    ctx.restore();
  }

  function undirKey(a, b) { return (a < b) ? (a + "-" + b) : (b + "-" + a); }
  function dirKey(a, b) { return a + ">" + b; }

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
      if (cpuDir.has(dirKey(a,b))) { same.push([a,b]); }
      else if (cpuDir.has(dirKey(b,a))) { opp.push([a,b]); oppSet.add(u); }
      else { same.push([a,b]); }
    }
    return { same, opp, oppSet };
  }

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
        if (drawing) { ctx2.stroke(); ctx2.beginPath(); drawing = false; }
        continue;
      }
      const A = gameState.cities[a], B = gameState.cities[b];
      if (!A || !B) continue;
      if (!drawing) { ctx2.moveTo(A.x, A.y); drawing = true; }
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

  function renderStaticLayer() {
    staticDirty = false;
    sctx.fillStyle = '#f5f6fa';
    sctx.fillRect(0, 0, staticLayer.width, staticLayer.height);

    gameState.terrains.forEach(t => {
      sctx.fillStyle = t.color; 
      sctx.beginPath();
      t.vertices.forEach((v, i) => i === 0 ? sctx.moveTo(v.x, v.y) : sctx.lineTo(v.x, v.y));
      sctx.fill();
    });

    const showUser = !!gameState.show.user;
    const showCpu  = !!gameState.show.cpu;
    const haveUserLine = gameState.userPath && gameState.userPath.length >= 2;
    const haveCpuLine  = gameState.cpuPath  && gameState.cpuPath.length  >= 2;
    const overlapReady = (isUserRouteClosed() && gameState.costs.user != null && gameState.costs.cpu != null && haveCpuLine);

    let overlap = null;
    if (overlapReady) overlap = buildOverlapSets(gameState.userPath, gameState.cpuPath);
    const bothVisible = showUser && showCpu;
    const userStroke = rgbaStr(hexToRgb(gameState.colors.user), 1.0);
    const cpuStroke  = rgbaStr(hexToRgb(gameState.colors.cpu), 1.0);

    if (overlapMode === "multiply") {
      if (overlapReady) {
        if (bothVisible) {
          drawFilteredPath(sctx, gameState.cpuPath,  cpuStroke,  ROUTE_W, overlap.oppSet);
          drawFilteredPath(sctx, gameState.userPath, userStroke, ROUTE_W, overlap.oppSet);
          drawSegments(sctx, overlap.same, "#000000", ROUTE_W + 1, []);
          drawSegments(sctx, overlap.opp,  "#000000", ROUTE_W + 1, OPP_DASH);
        } else {
          drawSegments(sctx, overlap.same, "#000000", ROUTE_W + 1, []);
          drawSegments(sctx, overlap.opp,  "#000000", ROUTE_W + 1, OPP_DASH);
        }
      } else {
        if (showCpu && haveCpuLine)  drawFilteredPath(sctx, gameState.cpuPath,  cpuStroke,  ROUTE_W, null);
        if (showUser && haveUserLine) drawFilteredPath(sctx, gameState.userPath, userStroke, ROUTE_W, null);
      }
    } else {
      if (showCpu && haveCpuLine) {
        const skip = (bothVisible && overlapReady) ? overlap.oppSet : null;
        drawFilteredPath(sctx, gameState.cpuPath, cpuStroke, ROUTE_W, skip);
      }
      if (showUser && haveUserLine) {
        const skip = (bothVisible && overlapReady) ? overlap.oppSet : null;
        drawFilteredPath(sctx, gameState.userPath, userStroke, ROUTE_W, skip);
      }
      if (bothVisible && overlapReady) {
        const col = overlapColorRgb();
        const stroke = rgbaStr(col, 0.98);
        drawSegments(sctx, overlap.same, stroke, ROUTE_W, []);
        drawSegments(sctx, overlap.opp,  stroke, ROUTE_W, OPP_DASH);
      }
    }

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

    if (gameState.raceStartId !== null && gameState.userPath.length >= 1) {
      const sc = gameState.cities[gameState.raceStartId];
      if (sc) {
        sctx.save();
        sctx.beginPath();
        sctx.arc(sc.x, sc.y, 16, 0, Math.PI*2);
        sctx.strokeStyle = "rgba(22, 160, 133, 0.95)";
        sctx.lineWidth = 3;
        sctx.stroke();
        sctx.restore();
      }
    }
  }

  function tick(ts) {
    if (lastTs === null) lastTs = ts;
    const dt = Math.min(0.05, (ts - lastTs) / 1000);
    lastTs = ts;
    const nowMs = performance.now();

    if (animationRunning) {
      let bothFinished = true;
      ["user","cpu"].forEach(key => {
        const geom = gameState.routeGeom[key];
        const cost = gameState.costs[key];
        if (!geom || cost == null) return;

        if (!gameState.runners[key].finished) {
            bothFinished = false; 
            const pos = positionAlongRoute(key, gameState.runners[key].dist);
            if (pos) {
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
            }
        }
      });

      if (bothFinished) {
          animationRunning = false;
          document.getElementById('btnAnimToggle').innerText = "Koniec";
          revealResults();
      }
    }

    if (staticDirty) renderStaticLayer();
    ctx.drawImage(staticLayer, 0, 0);

    drawHoverRing();

    drawTrail("cpu", nowMs);
    drawTrail("user", nowMs);
    drawRunner("cpu");
    drawRunner("user");

    progAcc += dt;
    if (progAcc >= 0.10) { progAcc = 0; updateProgressUI(); }
    requestAnimationFrame(tick);
  }

  function setRaceNotReady(text="⏳") {
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
    if (gameState.costs.user == null || gameState.costs.cpu == null) return;
    animationRunning = !animationRunning;
    document.getElementById('btnAnimToggle').innerText = animationRunning ? "⏸ Pauza" : "▶ Start";
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
    if (p.length <= 1) {
      document.getElementById('userTime').innerText = "0.00h";
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
    document.getElementById('userTime').innerText = t.toFixed(2) + "h";

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
    if (gameState.raceStartId === null) return;

    gameState.solvingAll = true;
    gameState.resultsRevealed = false;
    abortPendingSolves();
    setRaceNotReady("AI...");
    setLoading(true, "AI liczy...");

    document.getElementById('cpuTime').innerText = "???"; 
    document.getElementById('boxUser').classList.remove('winner-glow', 'loser-dim');
    document.getElementById('boxCpu').classList.remove('winner-glow', 'loser-dim');

    gameState.cpuPath = [];
    gameState.costs.cpu = null;
    gameState.routeGeom.cpu = null;

    const version = gameState.matrixVersion;
    const ctrl = new AbortController();
    gameState.pending.aiCtrl = ctrl;
    
    // Pobierz parametry z UI
    const algo = document.getElementById('algoSelect').value || 'ils';
    const timeLimit = parseFloat(document.getElementById('aiTimeLimit').value) || 2.0;

    try {
      const res = await fetch('/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            matrix: gameState.matrix, 
            start: gameState.raceStartId,
            algo: algo,
            time_limit: timeLimit
        }),
        signal: ctrl.signal
      });
      if (!res.ok) throw new Error("Błąd AI");
      const data = await res.json();
      if (version !== gameState.matrixVersion) return;

      gameState.cpuPath = data.path;
      gameState.costs.cpu = data.cost;
      
      rebuildRouteGeom('cpu', false);
      resetIcons();
      setLoading(false);

      if (gameState.costs.user != null && gameState.costs.cpu != null) {
        setRaceReadyAndStart();
      } else {
        setRaceNotReady("Brak");
      }
      markStaticDirty();
    } catch (e) {
      if (e.name !== "AbortError") {
        showError("Błąd AI");
        document.getElementById('cpuTime').innerText = "--";
      }
    } finally {
      gameState.solvingAll = false;
      setLoading(false);
      if (gameState.pending.aiCtrl === ctrl) gameState.pending.aiCtrl = null;
    }
  }

  // --- SMART INPUT ---
  function clientToCanvas(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (clientX - rect.left) * scaleX;
    const y = (clientY - rect.top) * scaleY;
    const scaleAvg = (scaleX + scaleY) * 0.5;
    return { x, y, scaleAvg };
  }

  function pickNearestCity(canvasX, canvasY) {
    let best = null;
    let minDst = Infinity;
    for (const c of gameState.cities) {
      const d = Math.hypot(c.x - canvasX, c.y - canvasY);
      if (d < minDst) { minDst = d; best = c; }
    }
    return { city: best, dist: minDst };
  }

  function updateHover(clientX, clientY) {
    pointer.lastClientX = clientX;
    pointer.lastClientY = clientY;

    const { x, y, scaleAvg } = clientToCanvas(clientX, clientY);
    const { city, dist } = pickNearestCity(x, y);

    const hitRadiusCanvas = HIT_RADIUS_PX * scaleAvg;
    if (!city || dist > hitRadiusCanvas) {
      pointer.hoverId = null;
      return;
    }
    pointer.hoverId = city.id;
  }

  function selectCityId(cityId) {
    if (gameState.isLocked) return;
    if (isUserRouteClosed()) return;
    const city = gameState.cities[cityId];
    if (!city) return;

    const path = gameState.userPath;

    if (path.length === 0) {
      path.push(city.id);
      gameState.raceStartId = city.id;
      updateUserStats();
      setRaceNotReady("Rysuj...");
      markStaticDirty();
      return;
    }

    if (path.length > 0 && path[path.length - 1] === city.id) return;

    if (path.includes(city.id)) {
      if (city.id === path[0] && path.length === gameState.cities.length) {
        path.push(city.id);
      } else {
        return;
      }
    } else {
      path.push(city.id);
    }

    updateUserStats();
    setRaceNotReady("Rysuj...");
    markStaticDirty();

    if (isUserRouteClosed() && gameState.matrixReady) {
      gameState.userPath = normalizeCycleToStart(gameState.userPath, gameState.raceStartId);
      updateUserStats();
      solveAIBackground();
    }
  }

  canvas.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'touch') e.preventDefault();
    canvas.setPointerCapture(e.pointerId);
    pointer.active = true;
    pointer.id = e.pointerId;
    updateHover(e.clientX, e.clientY);
  }, { passive: false });

  canvas.addEventListener('pointermove', (e) => {
    if (!pointer.active || e.pointerId !== pointer.id) return;
    if (e.pointerType === 'touch') e.preventDefault();
    updateHover(e.clientX, e.clientY);
  }, { passive: false });

  canvas.addEventListener('pointerup', (e) => {
    if (!pointer.active || e.pointerId !== pointer.id) return;
    if (e.pointerType === 'touch') e.preventDefault();

    if (pointer.hoverId !== null && pointer.hoverId !== undefined) {
      selectCityId(pointer.hoverId);
    }

    pointer.active = false;
    pointer.id = null;
    pointer.hoverId = null;
  }, { passive: false });

  canvas.addEventListener('pointercancel', () => {
    pointer.active = false;
    pointer.id = null;
    pointer.hoverId = null;
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
    gameState.resultsRevealed = false;

    document.getElementById('cpuTime').innerText = "--";
    document.getElementById('userTime').innerText = "0.00h";
    document.getElementById('boxUser').classList.remove('winner-glow', 'loser-dim');
    document.getElementById('boxCpu').classList.remove('winner-glow', 'loser-dim');

    setRaceNotReady("Start");
    resetIcons();
    markStaticDirty();
  }

  // --- AKTUALIZACJA LEGENDY (DYNAMICZNE MNOŻNIKI) ---
  function updateLegend(types) {
    const container = document.getElementById('terrain-legend-items');
    container.innerHTML = "";
    const sorted = [...types].sort((a,b) => a.val - b.val);
    sorted.forEach(t => {
       const div = document.createElement('div');
       div.className = "legend-item";
       const txt = "x" + (Number.isInteger(t.val) ? t.val + ".0" : t.val);
       div.innerHTML = `<div class="l-box" style="background:${t.color}"></div><span class="legend-val">${txt}</span>`;
       container.appendChild(div);
    });
  }

  async function generateMap() {
    let n = parseInt(document.getElementById('pointsCount').value, 10);
    if (!Number.isFinite(n) || n < 3) n = 10;
    if (n > 120) n = 120;
    
    // Update listy algorytmów przy zmianie liczby punktów
    updateAlgoList();

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
    gameState.resultsRevealed = false;

    ["user","cpu"].forEach(k => {
      gameState.runners[k].dist = 0;
      gameState.runners[k].finished = false;
      gameState.runners[k].trail = [];
    });

    document.getElementById('userTime').innerText = "0.00h";
    document.getElementById('cpuTime').innerText = "--";
    document.getElementById('boxUser').classList.remove('winner-glow', 'loser-dim');
    document.getElementById('boxCpu').classList.remove('winner-glow', 'loser-dim');

    setRaceNotReady("Start");
    resetIcons();
    markStaticDirty();

    try {
      const res = await fetch('/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ n_points: n })
      });
      if (!res.ok) throw new Error("Błąd");
      const data = await res.json();
      gameState.cities = data.cities;
      gameState.terrains = data.terrains;
      
      const uniqueTypes = [];
      const seen = new Set();
      data.terrains.forEach(t => {
         if(!seen.has(t.val)) {
            seen.add(t.val);
            uniqueTypes.push({ val: t.val, color: t.color });
         }
      });
      updateLegend(uniqueTypes);

      markStaticDirty();
      buildMatrixOnce();
    } catch(e) {
      showError("Błąd sieci");
    }
  }

  function initLegendControls() {
    document.getElementById('btnOverlapMode').addEventListener('click', cycleOverlapMode);
    document.getElementById('btnToggleUser').addEventListener('click', () => setShow('user', !gameState.show.user));
    document.getElementById('btnToggleCpu').addEventListener('click', () => setShow('cpu', !gameState.show.cpu));
    overlapMode = "user";
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

# --- BACKEND ---

def get_terrain_color(val):
    alpha = 0.65 
    if val <= 0.3: return f"rgba(231, 76, 60, {alpha})"
    if val <= 0.6: return f"rgba(230, 126, 34, {alpha})"
    if val <= 0.9: return f"rgba(241, 196, 15, {alpha})"
    if val <= 3.0: return f"rgba(46, 204, 113, {alpha})"
    if val <= 5.0: return f"rgba(39, 174, 96, {alpha})"
    if val <= 7.0: return f"rgba(22, 160, 133, {alpha})"
    return f"rgba(0, 206, 209, {alpha})"

@app.route("/")
def home():
    print("--- START APP ---", flush=True)
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate_map():
    try:
        data = request.json or {}
        n = int(data.get('n_points', 10))

        if n < 3: return jsonify({'error': 'Min 3 miasta.'}), 400
        if n > 120: return jsonify({'error': 'Limit backend 120.'}), 400

        width, height = 1000, 800

        slow_pool = [round(x * 0.1, 1) for x in range(1, 10)]
        fast_pool = [float(x) for x in range(2, 11)]
        all_possible = slow_pool + fast_pool

        num_types = random.randint(3, 5)
        
        chosen_vals = set()
        chosen_vals.add(random.choice(slow_pool))
        chosen_vals.add(random.choice(fast_pool))

        while len(chosen_vals) < num_types:
            chosen_vals.add(random.choice(all_possible))
        
        sorted_vals = sorted(list(chosen_vals))
        terrain_defs = []
        for v in sorted_vals:
            terrain_defs.append({'val': v, 'color': get_terrain_color(v)})

        terrains = []
        attempts = 0
        while len(terrains) < 9 and attempts < 500:
            attempts += 1
            t_radius = random.uniform(50, 120)
            x = random.uniform(t_radius + 10, width - t_radius - 10)
            y = random.uniform(t_radius + 10, height - t_radius - 10)

            overlap = False
            for t in terrains:
                if math.hypot(t['x'] - x, t['y'] - y) < (t['radius'] + t_radius + 20):
                    overlap = True
                    break

            if not overlap:
                t_def = random.choice(terrain_defs)
                verts = []
                num = random.randint(9, 14)
                base_angle = random.uniform(0, 2*math.pi)
                for i in range(num):
                    a = base_angle + (2 * math.pi * i / num)
                    r_var = t_radius * random.uniform(0.6, 1.15) 
                    verts.append({'x': x + math.cos(a) * r_var, 'y': y + math.sin(a) * r_var})
                
                terrains.append({
                    'x': x, 'y': y, 'radius': t_radius, 
                    'val': t_def['val'], 'color': t_def['color'], 
                    'vertices': verts
                })

        cities = []
        attempts = 0
        max_attempts = 15000 if n > 80 else 6000 if n > 50 else 3000
        while len(cities) < n and attempts < max_attempts:
            attempts += 1
            cx, cy = random.uniform(40, width - 40), random.uniform(40, height - 40)
            if not any(math.hypot(c['x'] - cx, c['y'] - cy) < 55 for c in cities):
                cities.append({'id': len(cities), 'x': cx, 'y': cy})

        if len(cities) < n:
            return jsonify({'error': f'Nie udało się rozmieścić {n} miast. Spróbuj mniejszej liczby.'}), 400

        return jsonify({'cities': cities, 'terrains': terrains})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---- SOLVERS ----

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
                if j - i == 1: continue
                c, d = route[j], route[j + 1]
                d1 = matrix[a][b] + matrix[c][d]
                d2 = matrix[a][c] + matrix[b][d]
                if d2 < d1 - 1e-9:
                    route[i:j + 1] = reversed(route[i:j + 1])
                    improved = True
                    break
                checks += 1
                if max_checks is not None and checks >= max_checks: return route
            if improved: break
    return route

def double_bridge(route):
    n = len(route) - 1
    core = route[:-1]
    start = core[0]
    if n < 8: return route[:]
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
        if not candidates: nxt = unvisited.pop()
        else:
            take = candidates[:max(1, min(k, len(candidates)))]
            weights = [1.0 / (r + 1) for r in range(len(take))]
            s = sum(weights)
            x = random.random() * s
            acc = 0.0
            nxt = take[-1]
            for node, w in zip(take, weights):
                acc += w
                if x <= acc: nxt = node; break
            unvisited.remove(nxt)
        route.append(nxt)
        curr = nxt
    route.append(start)
    return route

# --- DISPATCHER ---
@app.route('/solve', methods=['POST'])
def solve_smart_ai():
    try:
        payload = request.json or {}
        matrix = payload.get('matrix')
        if matrix is None: return jsonify({'error': 'Brak macierzy'}), 400
        n = len(matrix)
        start = int(payload.get('start', 0))
        if start < 0 or start >= n: start = 0
        
        algo = payload.get('algo', 'ils')
        time_limit = float(payload.get('time_limit', 2.0))
        # Limit bezpieczeństwa
        if time_limit > 60.0: time_limit = 60.0
        if time_limit < 0.1: time_limit = 0.1

        t0 = time.perf_counter()
        
        best_route = None
        best_cost = float('inf')
        meta = ""

        # --- 1. RANDOM (Losowy) ---
        if algo == 'random':
            nodes = list(range(n))
            nodes.remove(start)
            random.shuffle(nodes)
            best_route = [start] + nodes + [start]
            best_cost = route_cost(matrix, best_route)
            meta = "Random shuffle"

        # --- 2. NN (Najbliższy Sąsiad - Greedy) ---
        elif algo == 'nn':
            # k=1 oznacza czysty Greedy Nearest Neighbor
            best_route = randomized_nearest_neighbor(matrix, start=start, k=1)
            best_cost = route_cost(matrix, best_route)
            meta = "Greedy NN"

        # --- 3. NN + 2-opt (Lokalne ulepszanie) ---
        elif algo == 'nn_2opt':
            best_route = randomized_nearest_neighbor(matrix, start=start, k=1)
            best_route = two_opt_first_improve(matrix, best_route, max_checks=None)
            best_cost = route_cost(matrix, best_route)
            meta = "NN + 2-opt"

        # --- 4. ILS (Obecny - Iterated Local Search) ---
        elif algo == 'ils':
            # Domyślny algorytm z ograniczeniem czasowym
            if n <= 60: max_checks = None
            else: max_checks = 20000

            restarts = 0
            loops = 0
            
            while time.perf_counter() - t0 < time_limit:
                restarts += 1
                route = randomized_nearest_neighbor(matrix, start=start, k=5)
                route = two_opt_first_improve(matrix, route, max_checks=max_checks)
                cost = route_cost(matrix, route)

                if cost < best_cost:
                    best_cost = cost
                    best_route = route[:]

                inner_steps = 4
                for _ in range(inner_steps):
                    loops += 1
                    if time.perf_counter() - t0 >= time_limit: break
                    pert = double_bridge(route)
                    pert = two_opt_first_improve(matrix, pert, max_checks=max_checks)
                    c2 = route_cost(matrix, pert)
                    if c2 < cost or random.random() < 0.08:
                        route, cost = pert, c2
                        if cost < best_cost: best_cost = cost; best_route = route[:]
            
            meta = f"ILS ({time_limit:.1f}s)"

        # --- 5. BRUTE FORCE (Tylko dla małych N) ---
        elif algo == 'brute':
            if n > 11: # Zabezpieczenie
                best_route = randomized_nearest_neighbor(matrix, start=start, k=1)
                best_cost = route_cost(matrix, best_route)
                meta = "Fallback (N too big)"
            else:
                nodes = list(range(n))
                nodes.remove(start)
                # Sprawdź wszystkie permutacje
                for perm in itertools.permutations(nodes):
                    current_route = [start] + list(perm) + [start]
                    c = route_cost(matrix, current_route)
                    if c < best_cost:
                        best_cost = c
                        best_route = current_route
                meta = "Brute Force (Exact)"

        # Fallback
        if best_route is None:
             best_route = randomized_nearest_neighbor(matrix, start=start, k=1)
             best_cost = route_cost(matrix, best_route)

        return jsonify({'path': best_route, 'cost': float(best_cost), 'meta': meta})
    except Exception as e: return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
