"""Generate the self-contained 3D voxel lattice explorer
(data/output/lattice3d.html) from the v2 emergent lattice.

No external JS libraries — a small hand-rolled Canvas 3D projector, so the
page works under the artifact CSP and offline.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lattice.viz3d import build_lattice3d_data

OUT = Path(__file__).resolve().parents[1] / "data" / "output"

TEMPLATE = r"""<title>LatticeModel — 3D OptionSet Lattice</title>
<style>
  :root {
    --surface: #fcfcfb; --panel: #f4f4f1; --ink: #262625; --ink2: #6b6a63;
    --grid: #e3e3dd; --ghost: #77766c; --edge: #d8d8d2;
    --s0: #2a78d6; --s1: #008300; --s2: #e87ba4; --s3: #eda100; --s4: #1baf7a;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --surface: #1a1a19; --panel: #232322; --ink: #f5f5f2; --ink2: #c3c2b7;
      --grid: #33332f; --ghost: #a3a297; --edge: #3c3c38;
      --s0: #3987e5; --s1: #008300; --s2: #d55181; --s3: #c98500; --s4: #199e70;
    }
  }
  :root[data-theme="dark"] {
    --surface: #1a1a19; --panel: #232322; --ink: #f5f5f2; --ink2: #c3c2b7;
    --grid: #33332f; --ghost: #a3a297; --edge: #3c3c38;
    --s0: #3987e5; --s1: #008300; --s2: #d55181; --s3: #c98500; --s4: #199e70;
  }
  html, body { height: 100%; }
  body {
    margin: 0; background: var(--surface); color: var(--ink);
    font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    display: flex; flex-direction: column; overflow: hidden;
  }
  .mono { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
          font-variant-numeric: tabular-nums; }
  header { padding: 14px 20px 8px; flex: none; }
  header h1 { margin: 0; font-size: 17px; font-weight: 650; letter-spacing: -0.01em; }
  header .stats { margin-top: 2px; font-size: 11.5px; color: var(--ink2); }
  .controls {
    flex: none; display: flex; flex-wrap: wrap; align-items: center;
    gap: 10px 18px; padding: 8px 20px 10px; border-bottom: 1px solid var(--grid);
  }
  .group { display: flex; align-items: center; gap: 8px; }
  .group .lbl {
    font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ink2); font-weight: 600;
  }
  .chips { display: flex; gap: 4px; }
  .chips button {
    font: 12px/1 inherit; padding: 5px 10px; border-radius: 999px;
    border: 1px solid var(--edge); background: var(--panel); color: var(--ink2);
    cursor: pointer;
  }
  .chips button[aria-pressed="true"] {
    background: var(--ink); color: var(--surface); border-color: var(--ink);
  }
  .chips button:focus-visible, .toggle input:focus-visible,
  #reset:focus-visible, #novelty:focus-visible {
    outline: 2px solid var(--s0); outline-offset: 2px;
  }
  #novelty { accent-color: var(--s0); width: 130px; }
  .toggle { display: flex; align-items: center; gap: 6px; font-size: 12.5px;
            color: var(--ink2); cursor: pointer; }
  .toggle input { accent-color: var(--s0); margin: 0; }
  #reset {
    font: 12px/1 inherit; padding: 5px 12px; border-radius: 999px;
    border: 1px solid var(--edge); background: none; color: var(--ink2); cursor: pointer;
  }
  #stage { flex: 1; position: relative; min-height: 0; }
  canvas { position: absolute; inset: 0; width: 100%; height: 100%;
           touch-action: none; cursor: grab; }
  canvas.dragging { cursor: grabbing; }
  #planes { position: absolute; inset: 0; overflow: auto; padding: 14px 20px;
            display: none; }
  #planes.active { display: block; }
  .panelgrid { display: grid; gap: 14px;
               grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }
  .panel { background: var(--panel); border: 1px solid var(--grid);
           border-radius: 10px; padding: 10px 12px 12px; }
  .panel h2 { margin: 0 0 8px; font-size: 12.5px; font-weight: 650; }
  .panel h2 .ghostly { color: var(--ink2); font-weight: 400; }
  .pgrid { display: grid; gap: 3px; }
  .paxis { font-size: 9.5px; color: var(--ink2); align-self: center;
           justify-self: center; }
  .pcell { aspect-ratio: 1; border-radius: 4px; min-width: 30px;
           display: flex; flex-direction: column; align-items: center;
           justify-content: center; font-size: 11px; line-height: 1.1;
           position: relative; cursor: default; }
  .pknown { border: 1.5px solid; font-weight: 600; color: var(--ink); }
  .pslot { background: var(--ghost); }
  .pcount { position: absolute; top: 1px; right: 3px; font-size: 8.5px;
            color: var(--ink2); }
  .controls .disabled { opacity: 0.4; pointer-events: none; }
  #tip {
    position: absolute; pointer-events: none; display: none; max-width: 260px;
    background: var(--panel); border: 1px solid var(--edge); border-radius: 8px;
    padding: 8px 10px; font-size: 12px; box-shadow: 0 4px 14px rgba(0,0,0,.12);
    z-index: 5;
  }
  #tip .head { font-weight: 650; margin-bottom: 3px; }
  #tip .row { color: var(--ink2); }
  footer {
    flex: none; display: flex; flex-wrap: wrap; gap: 6px 16px;
    padding: 9px 20px 12px; border-top: 1px solid var(--grid);
    font-size: 11.5px; color: var(--ink2);
  }
  .key { display: inline-flex; align-items: center; gap: 6px; }
  .sw { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
  .hint { margin-left: auto; }
  @media (max-width: 640px) { .hint { display: none; } }
</style>

<header>
  <h1>3D OptionSet Lattice <span style="color:var(--ink2);font-weight:400">— emergent (v2): spin × charge × mass</span></h1>
  <div class="stats mono" id="stats"></div>
</header>

<div class="controls">
  <div class="group"><span class="lbl">View</span>
    <div class="chips" id="view">
      <button aria-pressed="true" data-v="3d">3D</button>
      <button aria-pressed="false" data-v="planes">Planes</button>
    </div>
  </div>
  <div class="group"><span class="lbl">Layer</span>
    <div class="chips" id="layer">
      <button aria-pressed="true" data-v="fund">Fundamental</button>
      <button aria-pressed="false" data-v="had">Hadrons</button>
    </div>
  </div>
  <div class="group"><span class="lbl">Stability</span>
    <div class="chips" id="stability">
      <button aria-pressed="true" data-v="all">All</button>
      <button aria-pressed="false" data-v="1">Stable</button>
      <button aria-pressed="false" data-v="0">Unstable</button>
    </div>
  </div>
  <div class="group"><span class="lbl">Min novelty</span>
    <input type="range" id="novelty" min="0" max="1" step="0.01" value="0">
    <span class="mono" id="novcount" style="font-size:11.5px;color:var(--ink2)"></span>
  </div>
  <label class="toggle"><input type="checkbox" id="labels" checked> Labels</label>
  <button id="reset">Reset view</button>
</div>

<div id="stage">
  <canvas id="c"></canvas>
  <div id="planes"><div class="panelgrid" id="panelgrid"></div></div>
  <div id="tip"></div>
</div>

<footer id="legend"></footer>

<script>
const DATA = __LATTICE_DATA__;

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const tip = document.getElementById('tip');
const stage = document.getElementById('stage');

// ---------- theme tokens (re-read when the theme changes)
let T = {};
function readTheme() {
  const s = getComputedStyle(document.body);
  T = { surface: s.getPropertyValue('--surface').trim(),
        ink: s.getPropertyValue('--ink').trim(),
        ink2: s.getPropertyValue('--ink2').trim(),
        grid: s.getPropertyValue('--grid').trim(),
        ghost: s.getPropertyValue('--ghost').trim(),
        series: [0,1,2,3,4].map(i => s.getPropertyValue('--s'+i).trim()) };
}
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { readTheme(); draw(); });
new MutationObserver(() => { readTheme(); draw(); })
  .observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

// ---------- world coordinates
const SX = 1.0, SY = 1.55, SZ = 0.62, STOFF = 0.30;
const SPIN_SHELF = { '0': 0, '0.5': 1, '1': 2, '1.5': 3, '2': 4 };
function world(cell) {
  return { x: (cell.m + 9 - 7.5) * SX,
           y: (SPIN_SHELF[String(cell.spin)] - 2) * SY + (cell.st ? -STOFF : STOFF),
           z: cell.q * SZ };
}
const SPIN_LBL = { '0': '0', '0.5': '½', '1': '1', '1.5': '3/2', '2': '2' };
const LAYER_SHELVES = { fund: ['0','0.5','1','2'], had: ['0','0.5','1','1.5'] };
const fmtQ = q => q === 0 ? '0' : (q % 3 === 0 ? (q>0?'+':'−') + Math.abs(q/3) : (q>0?'+':'−') + Math.abs(q) + '/3');
const fmtM = m => m <= -9 ? 'massless' : '~10^' + m + ' MeV';

// ---------- view state
const HOME = { yaw: -0.62, pitch: 0.34, zoom: 1 };
let yaw = HOME.yaw, pitch = HOME.pitch, zoom = HOME.zoom;
const D = 26;  // perspective distance in world units

function project(p, w, h, scale) {
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x1 = cy * p.x + sy * p.z, z1 = -sy * p.x + cy * p.z;
  const y2 = cp * p.y - sp * z1,  z2 = sp * p.y + cp * z1;
  const f = D / (D - z2);
  return { sx: w/2 + x1 * scale * f, sy: h/2 - y2 * scale * f, z: z2, f };
}
function rotN(n) {  // rotate a normal, return view-space vector
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x1 = cy * n.x + sy * n.z, z1 = -sy * n.x + cy * n.z;
  return { x: x1, y: cp * n.y - sp * z1, z: sp * n.y + cp * z1 };
}

// ---------- filters
let view = '3d', layer = 'fund', stFilter = 'all', novMin = 0, showLabels = true;
const passSt = c => stFilter === 'all' || String(c.st) === stFilter;
const layerData = () => layer === 'fund'
  ? { knowns: DATA.knowns, empties: DATA.empties, maxNov: DATA.max_novelty }
  : { knowns: DATA.hadrons, empties: DATA.hadron_empties, maxNov: DATA.hadron_max_novelty };

// ---------- geometry helpers
const CUBE_H = 0.30;
const CORNERS = [];
for (const dx of [-1,1]) for (const dy of [-1,1]) for (const dz of [-1,1])
  CORNERS.push([dx,dy,dz]);
const FACES = [  // corner indices (into CORNERS) + outward normal
  { idx: [4,5,7,6], n: {x: 1,y:0,z:0} }, { idx: [0,2,3,1], n: {x:-1,y:0,z:0} },
  { idx: [2,6,7,3], n: {x:0,y: 1,z:0} }, { idx: [0,1,5,4], n: {x:0,y:-1,z:0} },
  { idx: [1,3,7,5], n: {x:0,y:0,z: 1} }, { idx: [0,4,6,2], n: {x:0,y:0,z:-1} },
];
const LIGHT = { x: 0.42, y: 0.82, z: 0.39 };
function shade(hex, b) {
  const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16),
        bl = parseInt(hex.slice(5,7),16);
  return `rgb(${Math.round(r*b)},${Math.round(g*b)},${Math.round(bl*b)})`;
}

// ---------- render
let hits = [];  // painter-ordered screen hit targets
function draw() {
  const w = stage.clientWidth, h = stage.clientHeight;
  const dpr = devicePixelRatio || 1;
  if (canvas.width !== w*dpr || canvas.height !== h*dpr) {
    canvas.width = w*dpr; canvas.height = h*dpr;
  }
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.fillStyle = T.surface; ctx.fillRect(0,0,w,h);
  const scale = Math.min(w, h) * 0.055 * zoom * 1.55;
  hits = [];

  drawAxes(w, h, scale);

  const L = layerData();
  const items = [];
  for (const e of L.empties)
    if (passSt(e) && e.nov >= novMin * L.maxNov)
      items.push({ kind: 'ghost', cell: e, p: world(e), maxNov: L.maxNov });
  for (const k of L.knowns)
    if (passSt(k)) items.push({ kind: 'known', cell: k, p: world(k) });
  const preds = layer === 'fund' ? DATA.gen4 : DATA.hadron_preds;
  for (const g of preds)
    if (passSt(g)) items.push({ kind: 'pred', cell: g, p: world(g) });

  for (const it of items) it.pr = project(it.p, w, h, scale);
  items.sort((a,b) => a.pr.z - b.pr.z);  // far → near

  for (const it of items) {
    if (it.kind === 'ghost') drawGhost(it, w, h, scale);
    else if (it.kind === 'pred') drawPred(it, w, h, scale);
    else drawCube(it, w, h, scale);
  }
  document.getElementById('novcount').textContent =
    items.filter(i => i.kind === 'ghost').length + ' shown';
}

function drawGhost(it, w, h, scale) {
  const { sx, sy, f } = it.pr;
  const e = it.cell;
  const count = e.count || 1;
  const r = Math.max(2.2, 0.115 * scale * f) * Math.min(2.2, 0.75 + 0.3 * Math.sqrt(count));
  const a = 0.13 + 0.55 * (e.nov / it.maxNov);
  ctx.globalAlpha = a;
  ctx.fillStyle = T.ghost;
  ctx.fillRect(sx - r, sy - r, 2*r, 2*r);
  ctx.globalAlpha = 1;
  if (e.graviton) drawGraviton(it, w, h, scale);
  hits.push({ sx, sy, r: Math.max(r, 5), item: it });
}

function drawGraviton(it, w, h, scale) {
  const c = it.p, hh = CUBE_H * 1.25;
  const pts = CORNERS.map(([dx,dy,dz]) =>
    project({ x: c.x+dx*hh, y: c.y+dy*hh, z: c.z+dz*hh }, w, h, scale));
  const EDGES = [[0,1],[0,2],[1,3],[2,3],[4,5],[4,6],[5,7],[6,7],[0,4],[1,5],[2,6],[3,7]];
  ctx.save();
  ctx.strokeStyle = T.ink; ctx.setLineDash([4,3]); ctx.lineWidth = 1.4;
  for (const [a,b] of EDGES) {
    ctx.beginPath(); ctx.moveTo(pts[a].sx, pts[a].sy);
    ctx.lineTo(pts[b].sx, pts[b].sy); ctx.stroke();
  }
  ctx.restore();
  if (showLabels) {
    ctx.fillStyle = T.ink;
    ctx.font = '600 12px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('★ graviton?', it.pr.sx, it.pr.sy - 0.5 * scale * it.pr.f);
  }
}

function drawPred(it, w, h, scale) {
  const c = it.p, hh = CUBE_H * 1.05;
  const pts = CORNERS.map(([dx,dy,dz]) =>
    project({ x: c.x+dx*hh, y: c.y+dy*hh, z: c.z+dz*hh }, w, h, scale));
  const EDGES = [[0,1],[0,2],[1,3],[2,3],[4,5],[4,6],[5,7],[6,7],[0,4],[1,5],[2,6],[3,7]];
  ctx.save();
  ctx.strokeStyle = T.ink2; ctx.setLineDash([3,3]); ctx.lineWidth = 1.3;
  for (const [a,b] of EDGES) {
    ctx.beginPath(); ctx.moveTo(pts[a].sx, pts[a].sy);
    ctx.lineTo(pts[b].sx, pts[b].sy); ctx.stroke();
  }
  ctx.restore();
  const { sx, sy, f } = it.pr;
  if (showLabels) {
    ctx.fillStyle = T.ink2;
    ctx.font = '600 12px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('◇ ' + it.cell.label + '?', sx, sy - (CUBE_H*1.5) * scale * f);
  }
  hits.push({ sx, sy, r: Math.max(9, CUBE_H * scale * f), item: it });
}

function drawCube(it, w, h, scale) {
  const c = it.p, k = it.cell, hh = CUBE_H;
  const pts = CORNERS.map(([dx,dy,dz]) =>
    project({ x: c.x+dx*hh, y: c.y+dy*hh, z: c.z+dz*hh }, w, h, scale));
  const color = T.series[layer === 'fund' ? k.fam : k.mult];
  const faces = FACES.map(fc => ({ fc, n: rotN(fc.n) }))
    .filter(o => o.n.z > 0.02)
    .sort((a,b) => a.n.z - b.n.z);
  for (const { fc, n } of faces) {
    const lum = 0.6 + 0.4 * Math.max(0, n.x*LIGHT.x + n.y*LIGHT.y + n.z*LIGHT.z);
    ctx.fillStyle = shade(color, lum);
    ctx.strokeStyle = T.surface; ctx.lineWidth = 1.5;
    ctx.beginPath();
    fc.idx.forEach((i, j) => j ? ctx.lineTo(pts[i].sx, pts[i].sy)
                                : ctx.moveTo(pts[i].sx, pts[i].sy));
    ctx.closePath(); ctx.fill(); ctx.stroke();
  }
  const { sx, sy, f } = it.pr;
  if (showLabels) {
    ctx.fillStyle = T.ink;
    ctx.font = '600 12px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(k.occupants.join(' '), sx, sy - (CUBE_H*1.45) * scale * f);
  }
  hits.push({ sx, sy, r: Math.max(9, CUBE_H * scale * f), item: it });
}

function drawAxes(w, h, scale) {
  const x0 = -8.5*SX, x1 = 7.5*SX, y0 = -2*SY - 0.9, z0 = -6.9*SZ, z1 = 6.9*SZ;
  ctx.strokeStyle = T.grid; ctx.lineWidth = 1;
  ctx.fillStyle = T.ink2;
  ctx.font = '10.5px ui-monospace, Menlo, monospace';
  ctx.textAlign = 'center';

  // shelf outlines (one per spin level in the active layer)
  for (const sp of LAYER_SHELVES[layer]) {
    const y = (SPIN_SHELF[sp] - 2) * SY;
    const q = [{x:x0,y,z:z0},{x:x1,y,z:z0},{x:x1,y,z:z1},{x:x0,y,z:z1}]
      .map(p => project(p, w, h, scale));
    ctx.globalAlpha = 0.55;
    ctx.beginPath();
    q.forEach((p,i) => i ? ctx.lineTo(p.sx,p.sy) : ctx.moveTo(p.sx,p.sy));
    ctx.closePath(); ctx.stroke();
    ctx.globalAlpha = 1;
    const lbl = project({x: x0 - 0.7, y, z: z0}, w, h, scale);
    ctx.fillText('spin ' + SPIN_LBL[sp], lbl.sx, lbl.sy);
  }
  // mass ticks along front-bottom edge
  for (const m of [-9,-6,-3,0,3,6]) {
    const p = project({x:(m+9-7.5)*SX, y: y0, z: z1}, w, h, scale);
    ctx.fillText(m <= -9 ? '0' : '10^'+m, p.sx, p.sy + 12);
  }
  const ml = project({x: 0, y: y0 - 0.55, z: z1}, w, h, scale);
  ctx.fillText('mass (MeV) →', ml.sx, ml.sy + 22);
  // charge ticks along the side-bottom edge
  for (const q of [-6,-3,0,3,6]) {
    const p = project({x: x1 + 0.55, y: y0, z: q*SZ}, w, h, scale);
    ctx.fillText((q>0?'+':'') + (q/3) + 'e', p.sx, p.sy + 12);
  }
  const ql = project({x: x1 + 1.7, y: y0 - 0.4, z: 0}, w, h, scale);
  ctx.fillText('charge →', ql.sx, ql.sy + 18);
}

// ---------- interaction
let dragging = false, px = 0, py = 0;
const pointers = new Map();
canvas.addEventListener('pointerdown', ev => {
  canvas.setPointerCapture(ev.pointerId);
  pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
  dragging = true; px = ev.clientX; py = ev.clientY;
  canvas.classList.add('dragging'); tip.style.display = 'none';
});
canvas.addEventListener('pointerup', ev => {
  pointers.delete(ev.pointerId);
  if (!pointers.size) { dragging = false; canvas.classList.remove('dragging'); }
});
canvas.addEventListener('pointercancel', ev => {
  pointers.delete(ev.pointerId); dragging = false;
  canvas.classList.remove('dragging');
});
canvas.addEventListener('pointermove', ev => {
  if (pointers.size === 2) {  // pinch zoom
    const old = [...pointers.values()];
    const d0 = Math.hypot(old[0].x - old[1].x, old[0].y - old[1].y);
    pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    const cur = [...pointers.values()];
    const d1 = Math.hypot(cur[0].x - cur[1].x, cur[0].y - cur[1].y);
    if (d0 > 0) zoom = Math.min(3, Math.max(0.4, zoom * d1 / d0));
    draw(); return;
  }
  if (dragging) {
    pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    yaw += (ev.clientX - px) * 0.0075;
    pitch = Math.min(1.35, Math.max(-1.35, pitch + (ev.clientY - py) * 0.0075));
    px = ev.clientX; py = ev.clientY;
    draw(); return;
  }
  hover(ev);
});
canvas.addEventListener('wheel', ev => {
  ev.preventDefault();
  zoom = Math.min(3, Math.max(0.4, zoom * (ev.deltaY < 0 ? 1.09 : 0.92)));
  draw();
}, { passive: false });
canvas.addEventListener('dblclick', resetView);
document.getElementById('reset').addEventListener('click', resetView);
function resetView() {
  yaw = HOME.yaw; pitch = HOME.pitch; zoom = HOME.zoom; draw();
}

function hover(ev) {
  const rect = canvas.getBoundingClientRect();
  const mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
  let found = null;
  for (let i = hits.length - 1; i >= 0; i--) {  // front-most first
    const t = hits[i];
    if (Math.abs(mx - t.sx) <= t.r && Math.abs(my - t.sy) <= t.r) { found = t; break; }
  }
  if (!found) { tip.style.display = 'none'; return; }
  const c = found.item.cell;
  if (found.item.kind === 'pred') {
    const gev = c.mass_mev / 1000;
    const caveat = layer === 'fund'
      ? `<div class="row">Caveat: precision electroweak fits disfavor a sequential 4th generation.</div>`
      : '';
    tip.innerHTML =
      `<div class="head">◇ ${c.label} — ${c.head}</div>
       <div class="row mono">spin ${SPIN_LBL[String(c.spin)]} · Q ${fmtQ(c.q)} e · mass ≈ ${gev >= 1000
          ? (gev/1000).toFixed(1) + ' TeV' : gev.toFixed(2) + ' GeV'}` +
      (c.band_true > 6 ? ' (beyond mass axis)' : '') + `</div>
       <div class="row mono">${c.method}</div>` + caveat;
    tip.style.display = 'block';
    positionTip(ev);
    return;
  }
  const opts = `spin ${SPIN_LBL[String(c.spin)]} · Q ${fmtQ(c.q)} e · ${fmtM(c.m)} · ${c.st ? 'stable' : 'unstable'}`;
  if (found.item.kind === 'known') {
    tip.innerHTML = layer === 'fund'
      ? `<div class="head">${c.occupants.join(', ')}</div>
         <div class="row mono">${opts}</div>
         <div class="row">${DATA.family_labels[c.fam]}</div>`
      : `<div class="head">${c.occupants.join(' ')}</div>
         <div class="row mono">${opts}</div>
         <div class="row mono">${c.details.join('<br>')}</div>
         <div class="row">${DATA.multiplet_labels[c.mult]}</div>`;
  } else {
    tip.innerHTML = layer === 'fund'
      ? `<div class="head">${c.graviton ? '★ graviton candidate cell' : 'empty candidate slot'}</div>
         <div class="row mono">${opts}</div>
         <div class="row mono">novelty ${c.nov.toFixed(2)} · nearest known: ${c.near}</div>`
      : `<div class="head">${c.count} allowed flavor slot${c.count > 1 ? 's' : ''} in this cell</div>
         <div class="row mono">${opts}</div>
         <div class="row mono">max novelty ${c.nov.toFixed(2)} · nearest known: ${c.near}</div>`;
  }
  tip.style.display = 'block';
  positionTip(ev);
}
function positionTip(ev) {
  const rect = canvas.getBoundingClientRect();
  const mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
  const tw = tip.offsetWidth, th = tip.offsetHeight;
  tip.style.left = Math.min(mx + 14, rect.width - tw - 8) + 'px';
  tip.style.top = Math.max(8, Math.min(my - th - 12, rect.height - th - 8)) + 'px';
}
canvas.addEventListener('pointerleave', () => { tip.style.display = 'none'; });

// ---------- multiplet planes view
const planesEl = document.getElementById('planes');
const panelgrid = document.getElementById('panelgrid');
let PCELLS = [];

function renderPlanes() {
  PCELLS = [];
  const frag = [];
  for (const panel of DATA.planes) {
    const cells = panel.cells.map(c => ({
      S: c.S, q: c.q,
      knowns: c.knowns.filter(k => stFilter === 'all' || String(k.st) === stFilter),
      slots: c.slots.filter(s =>
        (stFilter === 'all' || String(s.st) === stFilter) &&
        s.nov >= novMin * DATA.hadron_max_novelty),
    })).filter(c => c.knowns.length || c.slots.length);
    if (!cells.length) continue;

    const qs = [...new Set(cells.map(c => c.q))].sort((a,b) => a-b);
    const Ss = [...new Set(cells.map(c => c.S))].sort((a,b) => b-a);
    const nKnown = cells.reduce((n,c) => n + c.knowns.length, 0);
    const cols = qs.length + 1;

    let html = `<div class="panel"><h2>${panel.title}` +
      (nKnown ? '' : ' <span class="ghostly">— unexplored</span>') +
      `</h2><div class="pgrid" style="grid-template-columns: 22px repeat(${qs.length}, 1fr)">`;
    for (const S of Ss) {
      html += `<div class="paxis mono">S ${S >= 0 ? '+' + S : S}</div>`;
      for (const q of qs) {
        const c = cells.find(x => x.S === S && x.q === q);
        if (!c) { html += `<div class="pcell"></div>`; continue; }
        const id = PCELLS.length;
        PCELLS.push({ panel, cell: c });
        if (c.knowns.length) {
          const mult = c.knowns[0].mult;
          html += `<div class="pcell pknown" data-pc="${id}" ` +
            `style="border-color: var(--s${mult}); ` +
            `background: color-mix(in srgb, var(--s${mult}) 20%, var(--surface))">` +
            c.knowns.map(k => `<span>${k.label}</span>`).join('') +
            (c.slots.length ? `<span class="pcount mono">+${c.slots.length}</span>` : '') +
            `</div>`;
        } else {
          const nov = Math.max(...c.slots.map(s => s.nov));
          const a = (0.12 + 0.5 * nov / DATA.hadron_max_novelty).toFixed(2);
          html += `<div class="pcell pslot" data-pc="${id}" style="opacity:${a}">` +
            (c.pm ? `<span class="mono" style="font-size:8.5px">~${(c.pm/1000).toFixed(1)}G</span>` : '') +
            (c.slots.length > 1 ? `<span class="pcount mono">${c.slots.length}</span>` : '') +
            `</div>`;
        }
      }
      html += '';
    }
    html += `<div class="paxis"></div>` +
      qs.map(q => `<div class="paxis mono">${fmtQ(q)}</div>`).join('') +
      `</div></div>`;
    frag.push(html);
  }
  panelgrid.innerHTML = frag.join('');
}

planesEl.addEventListener('mousemove', ev => {
  const el = ev.target.closest('[data-pc]');
  if (!el) { tip.style.display = 'none'; return; }
  const { cell } = PCELLS[+el.dataset.pc];
  const rows = [];
  if (cell.pm) rows.push(`GMO mass estimate ≈ ${cell.pm.toLocaleString('en')} MeV`);
  for (const k of cell.knowns)
    rows.push(`${k.label} · ${fmtM(k.m)} · ${k.st ? 'stable' : 'unstable'}`);
  const top = [...cell.slots].sort((a,b) => b.nov - a.nov).slice(0, 3);
  for (const s of top)
    rows.push(`slot: ${fmtM(s.m)} · ${s.st ? 'stable' : 'unstable'} · nov ${s.nov.toFixed(2)} · near ${s.near}`);
  if (cell.slots.length > 3) rows.push(`… +${cell.slots.length - 3} more slots`);
  tip.innerHTML =
    `<div class="head">${cell.knowns.length
      ? cell.knowns.map(k => k.label).join(' ')
      : cell.slots.length + ' empty slot' + (cell.slots.length > 1 ? 's' : '')}</div>` +
    `<div class="row mono">Q ${fmtQ(cell.q)} e · S ${cell.S >= 0 ? '+' + cell.S : cell.S}</div>` +
    rows.map(r => `<div class="row mono">${r}</div>`).join('');
  tip.style.display = 'block';
  const srect = stage.getBoundingClientRect();
  const mx = ev.clientX - srect.left, my = ev.clientY - srect.top;
  tip.style.left = Math.min(mx + 14, srect.width - tip.offsetWidth - 8) + 'px';
  tip.style.top = Math.max(8, Math.min(my + 14, srect.height - tip.offsetHeight - 8)) + 'px';
});
planesEl.addEventListener('mouseleave', () => { tip.style.display = 'none'; });

function applyView() {
  const planesActive = view === 'planes';
  planesEl.classList.toggle('active', planesActive);
  canvas.style.display = planesActive ? 'none' : 'block';
  document.getElementById('layer').parentElement
    .classList.toggle('disabled', planesActive);
  document.getElementById('labels').parentElement
    .classList.toggle('disabled', planesActive);
  tip.style.display = 'none';
  renderStats(); renderLegend();
  if (planesActive) renderPlanes(); else draw();
}

// ---------- controls
document.querySelectorAll('#view button').forEach(b =>
  b.addEventListener('click', () => {
    document.querySelectorAll('#view button')
      .forEach(x => x.setAttribute('aria-pressed', String(x === b)));
    view = b.dataset.v; applyView();
  }));
document.querySelectorAll('#layer button').forEach(b =>
  b.addEventListener('click', () => {
    document.querySelectorAll('#layer button')
      .forEach(x => x.setAttribute('aria-pressed', String(x === b)));
    layer = b.dataset.v; renderStats(); renderLegend(); draw();
  }));
document.querySelectorAll('#stability button').forEach(b =>
  b.addEventListener('click', () => {
    document.querySelectorAll('#stability button')
      .forEach(x => x.setAttribute('aria-pressed', String(x === b)));
    stFilter = b.dataset.v;
    view === 'planes' ? renderPlanes() : draw();
  }));
document.getElementById('novelty').addEventListener('input', ev => {
  novMin = parseFloat(ev.target.value);
  view === 'planes' ? renderPlanes() : draw();
});
document.getElementById('labels').addEventListener('change', ev => {
  showLabels = ev.target.checked; draw();
});
new ResizeObserver(() => draw()).observe(stage);

// ---------- header + legend
function renderStats() {
  if (view === 'planes') {
    document.getElementById('stats').textContent =
      `${DATA.planes.length} multiplet panels (charge × strangeness) · ` +
      `41 known hadrons · 693 allowed-but-empty flavor slots · ` +
      `panels split by baryon number, spin, charm, beauty`;
    return;
  }
  const L = layerData();
  const n = L.knowns.reduce((s,k) => s + k.occupants.length, 0);
  document.getElementById('stats').textContent = layer === 'fund'
    ? `${n} known particles in ${L.knowns.length} cells · ${L.empties.length} allowed-but-empty slots · grid: 4 spins × 13 charges × 16 mass bands × 2 stability`
    : `${n} known hadrons in ${L.knowns.length} cells · ${L.empties.reduce((s,e) => s + e.count, 0)} allowed-but-empty flavor slots in ${L.empties.length} cells · axes + baryon number, S, C, B̃`;
}
function renderLegend() {
  const planesActive = view === 'planes';
  const labels = (layer === 'fund' && !planesActive)
    ? DATA.family_labels : DATA.multiplet_labels;
  const extra = planesActive
    ? `<span class="key">cell count = slot variants in that cell</span>`
    : layer === 'fund'
      ? `<span class="key">★ graviton cell</span><span class="key">◇ predicted gen-4 cell</span>`
      : `<span class="key">ghost size = allowed flavor variants</span><span class="key">◇ registered forward prediction</span>`;
  const hint = planesActive
    ? `<span class="hint">hover any cell for details · panels sorted known-first</span>`
    : `<span class="hint">drag to rotate · scroll/pinch to zoom · double-click to reset</span>`;
  document.getElementById('legend').innerHTML =
    labels.map((l, i) =>
      `<span class="key"><span class="sw" style="background:var(--s${i})"></span>${l}</span>`).join('') +
    `<span class="key"><span class="sw" style="background:var(--ghost);opacity:.45"></span>empty slot (darker = more novel)</span>` +
    extra + hint;
}

readTheme();
renderStats();
renderLegend();
draw();
</script>
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = build_lattice3d_data()
    html = TEMPLATE.replace("__LATTICE_DATA__", json.dumps(data, ensure_ascii=False))
    out = OUT / "lattice3d.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
