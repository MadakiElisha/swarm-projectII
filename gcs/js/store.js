/* World state for the GCS. Everything the panels and the 3D scene draw
 * comes from here; live and replay sources both write into it.
 *
 * Coordinates: lat/lon for the map, ENU metres (x east, y north) relative
 * to the fleet origin for swarm math (same frame as swarm_common.geo).
 */
'use strict';
var SW = window.SW || (window.SW = {});

SW.geo = (function () {
  var M = 111320.0;
  var origin = [0, 0];
  return {
    setOrigin: function (lat, lon) { origin = [lat, lon]; },
    origin: function () { return origin; },
    toLatLon: function (x, y) {
      return [origin[0] + y / M, origin[1] + x / (M * Math.cos(origin[0] * Math.PI / 180))];
    },
    toEnu: function (lat, lon) {
      return [(lon - origin[1]) * M * Math.cos(origin[0] * Math.PI / 180), (lat - origin[0]) * M];
    },
  };
})();

/* Time-ordered flight samples for one drone; interpolated for smooth motion. */
SW.Track = function () { this.s = []; };
SW.Track.prototype.push = function (sample) {
  var s = this.s;
  if (s.length && sample.t < s[s.length - 1].t) {        // out of order (rare): insert
    var i = s.length - 1;
    while (i > 0 && s[i - 1].t > sample.t) i--;
    s.splice(i, 0, sample);
  } else s.push(sample);
  if (s.length > 20000) s.splice(0, 5000);
};
SW.Track.prototype.at = function (t) {
  var s = this.s, n = s.length;
  if (!n) return null;
  if (t <= s[0].t) return s[0];
  if (t >= s[n - 1].t) return s[n - 1];
  var lo = 0, hi = n - 1;
  while (hi - lo > 1) { var mid = (lo + hi) >> 1; if (s[mid].t <= t) lo = mid; else hi = mid; }
  var a = s[lo], b = s[hi], k = (t - a.t) / Math.max(1e-6, b.t - a.t);
  function L(p) { return a[p] + (b[p] - a[p]) * k; }
  function A(p) {                                        // angle lerp, shortest way round
    var d = b[p] - a[p];
    while (d > Math.PI) d -= 2 * Math.PI;
    while (d < -Math.PI) d += 2 * Math.PI;
    return a[p] + d * k;
  }
  return { t: t, lat: L('lat'), lon: L('lon'), alt: L('alt'), vx: L('vx'), vy: L('vy'),
           batt: L('batt'), roll: A('roll'), pitch: A('pitch'), yaw: A('yaw'),
           fsm: b.fsm, latch: b.latch, alive: b.alive };
};
SW.Track.prototype.last = function () { return this.s.length ? this.s[this.s.length - 1] : null; };

SW.Store = function (fleet) {
  this.fleet = fleet;               // {origin, drones:[{id,label,home}], swarm:{...}}
  this.cfg = fleet.swarm || {};
  this.drones = {};                 // id -> {id,label,home,track,brain,lastBrain,...}
  this.tasks = {};                  // id -> task snapshot {id,k,x,y,st,ct,n,r,ar}
  this.coverage = {};               // task id -> {x0,y0,cell,nx,ny,bits:BigInt}
  this.obs = [];                    // [t, cls, x, y, observer]
  this.quarry = null;               // {t,x,y,vx,vy}  (simulation ground truth)
  this.pulses = [];                 // [t, src, kind]
  this.events = [];                 // feed: {t, icon, text, kind}
  this.mission = {};                // task id -> latest event name
  this.listeners = [];
  this.now = 0;
  this._lastExec = {};              // drone -> item it announced
  var self = this;
  (fleet.drones || []).forEach(function (d) { self.ensure(d.id); });
};

SW.Store.prototype.ensure = function (id) {
  var d = this.drones[id];
  if (!d) {
    var spec = (this.fleet.drones || []).filter(function (x) { return x.id === id; })[0] || {};
    d = this.drones[id] = { id: id, label: 'D' + id, home: spec.home || null, track: new SW.Track(),
                            brain: null, brainT: -1, lost: false };
  }
  return d;
};

SW.Store.prototype.emit = function (what) {
  for (var i = 0; i < this.listeners.length; i++) this.listeners[i](what);
};

SW.Store.prototype.reset = function () {
  var self = this;
  Object.keys(this.drones).forEach(function (k) {
    var d = self.drones[k]; d.brain = null; d.brainT = -1; d.lost = false;
  });
  this.tasks = {}; this.coverage = {}; this.obs = []; this.quarry = null;
  this.pulses = []; this.events = []; this.mission = {}; this._lastExec = {};
  this.emit('reset');
};

/* ---------------------------------------------------------------- inputs */
SW.Store.prototype.vehicle = function (t, v) {   // v: {id,lat,lon,alt,vx,vy,batt,roll,pitch,yaw,fsm,latch,alive}
  var d = this.ensure(v.id);
  v.t = t;
  d.track.push(v);
};

SW.Store.prototype.brain = function (t, b) {     // b: {i, ph, tk, sc, nb:[[id,q]], z:{item:winner}, y:{}}
  var d = this.ensure(b.i);
  var prev = d.brain;
  d.brain = b; d.brainT = t;
  if (prev && prev.ph !== b.ph && (b.ph === 'RTB' || b.ph === 'FAILSAFE'))
    this.feed(t, b.ph === 'FAILSAFE' ? '⛔' : '↩', d.label + ' → ' + b.ph, b.ph === 'FAILSAFE' ? 'bad' : 'info');
  if (prev && prev.sc < 1.3 && b.sc >= 1.3)
    this.feed(t, '🔋', d.label + ' learned its battery drains ' + b.sc.toFixed(1) + '× the model', 'warn');
};

SW.Store.prototype.setTasks = function (t, list) {
  var self = this, seen = {};
  list.forEach(function (tk) {
    seen[tk.id] = 1;
    var old = self.tasks[tk.id];
    if (!old) self.feed(t, '＋', tk.id + ' ' + (tk.st === 'SUGGESTED' ? 'suggested by perception' : 'created'),
                        tk.st === 'SUGGESTED' ? 'warn' : 'info');
    else if (old.st !== tk.st) {
      var icon = { OPEN: '✔', DONE: '✓', MERGED: '⇢', CANCELLED: '✕' }[tk.st] || '•';
      var txt = tk.st === 'OPEN' && old.st === 'SUGGESTED' ? 'confirmed by operator' :
                tk.st === 'MERGED' ? 'merged (same survivor seen twice)' : tk.st.toLowerCase();
      self.feed(t, icon, tk.id + ' ' + txt, tk.st === 'DONE' ? 'good' : 'info');
    }
    self.tasks[tk.id] = tk;
  });
};

SW.Store.prototype.setCoverage = function (t, c) {
  var bits;
  try { bits = BigInt('0x' + (c.bits || '0')); } catch (e) { return; }
  var key = c.water ? c.id + '#water' : c.id;     // flood recon: cells seen under water
  this.coverage[key] = { x0: c.x0, y0: c.y0, cell: c.cell, nx: c.nx, ny: c.ny, bits: bits, t: t,
                         task: c.id, water: !!c.water };
  this.emit('coverage');
};

SW.Store.prototype.observation = function (t, o) { // o: [cls, x, y, observer]
  this.obs.push([t, o[0], o[1], o[2], o[3]]);
  if (this.obs.length > 5000) this.obs.splice(0, 1000);
};

SW.Store.prototype.pulse = function (t, src, kind) {
  this.pulses.push([t, src, kind]);
  if (this.pulses.length > 600) this.pulses.splice(0, 200);
};

SW.Store.prototype.missionEvent = function (t, task, ev, detail, reporter) {
  if (this.mission[task] === ev) return;          // every drone reports; show once
  this.mission[task] = ev;
  var icon = { PERIMETER_FORMED: '⬢', PERIMETER_DEGRADED: '⬡', RELEASED: '◌', INTRUDER: '⚠', FLOOD_MAP: '≋' }[ev] || '•';
  var kind = ev === 'PERIMETER_FORMED' ? 'good' : (ev === 'PERIMETER_DEGRADED' || ev === 'INTRUDER') ? 'bad' :
             ev === 'FLOOD_MAP' ? 'warn' : 'info';
  this.feed(t, icon, task + ' ' + ev.replace('PERIMETER_', '').toLowerCase() + ' · ' + detail +
            (reporter ? ' (D' + reporter + ')' : ''), kind);
  this.banner = { t: t, task: task, ev: ev, detail: detail };
  this.emit('banner');
};

SW.Store.prototype.assignment = function (t, id, item) {
  var d = this.ensure(id), prev = this._lastExec[id];
  this._lastExec[id] = item;
  if (item) this.feed(t, '◆', d.label + ' executing ' + item, 'info');
  else if (prev) {
    var parent = prev.split('/')[0], tk = this.tasks[parent];
    var open = tk && tk.st === 'OPEN';
    this.feed(t, open ? '⇄' : '◇', d.label + (open ? ' handed off ' : ' finished ') + prev, open ? 'warn' : 'info');
  }
};

SW.Store.prototype.suggestion = function (t, tid, id) {
  if (this.tasks[tid] && this.tasks[tid]._sugg) return;
  if (this.tasks[tid]) this.tasks[tid]._sugg = true;
};

SW.Store.prototype.feed = function (t, icon, text, kind) {
  this.events.push({ t: t, icon: icon, text: text, kind: kind || 'info' });
  if (this.events.length > 400) this.events.splice(0, 100);
  this.emit('feed');
};

/* ------------------------------------------------------------ derived */
SW.Store.prototype.alive = function (d, t) {
  var last = d.track.last();
  if (!last) return false;
  if (last.alive === 0 && last.t <= t) return false;
  return d.brainT < 0 || t - d.brainT < 12;
};

/* Work items exactly as the drones derive them (swarm_common.tasks.derive_work_items). */
SW.Store.prototype.workItems = function (t) {
  var out = [], f = this.cfg.formation || {};
  var self = this;
  Object.keys(this.tasks).sort().forEach(function (id) {
    var tk = self.tasks[id];
    if (tk.st !== 'OPEN') return;
    if (tk.k === 'GOTO' || tk.k === 'RESCUE') out.push({ id: id, parent: id, kind: tk.k, x: tk.x, y: tk.y });
    else if (tk.k === 'FORMATION' || tk.k === 'INTERCEPT') {
      var n = tk.n || f.max_slots || 5, r = tk.r || f.ring_radius_m || 300;
      var c = tk.k === 'INTERCEPT' ? (self.fusedTrack(t) || { x: tk.x, y: tk.y }) : { x: tk.x, y: tk.y };
      for (var s = 0; s < n; s++) {
        var th = 2 * Math.PI * s / n + 2 * Math.PI * (t - (tk.ct || 0)) / (f.ring_period_s || 480);
        out.push({ id: id + '/s' + s, parent: id, kind: tk.k, slot: s,
                   x: c.x + r * Math.cos(th), y: c.y + r * Math.sin(th), cx: c.x, cy: c.y, r: r });
      }
    }
  });
  return out;
};

/* Consensus view: who does each live drone believe holds each item? */
SW.Store.prototype.consensus = function (t) {
  var self = this, res = {};
  Object.keys(this.drones).forEach(function (k) {
    var d = self.drones[k];
    if (!d.brain || !self.alive(d, t)) return;
    var z = d.brain.z || {};
    Object.keys(z).forEach(function (item) {
      var r = res[item] || (res[item] = { claims: {}, voters: 0 });
      r.voters++;
      r.claims[z[item]] = (r.claims[z[item]] || 0) + 1;
    });
  });
  Object.keys(res).forEach(function (item) {
    var winners = Object.keys(res[item].claims);
    res[item].winners = winners.map(Number);
    res[item].agreed = winners.length === 1;
  });
  return res;
};

/* Constant-velocity least-squares fit of recent target sightings from ALL drones
 * (same as swarm_common.perception.WorldModel.moving_track). */
SW.Store.prototype.fusedTrack = function (t) {
  var win = (this.cfg.perception || {}).target_track_window_s || 8, pts = [];
  for (var i = this.obs.length - 1; i >= 0; i--) {
    var o = this.obs[i];
    if (t - o[0] > win) break;
    if (o[1] === 'target' && o[0] <= t) pts.push(o);
  }
  if (!pts.length) return null;
  var n = pts.length, tm = 0, xm = 0, ym = 0;
  pts.forEach(function (o) { tm += o[0]; xm += o[2]; ym += o[3]; });
  tm /= n; xm /= n; ym /= n;
  var v = 0, sx = 0, sy = 0;
  pts.forEach(function (o) { var d = o[0] - tm; v += d * d; sx += d * (o[2] - xm); sy += d * (o[3] - ym); });
  var vx = v > 1e-6 ? sx / v : 0, vy = v > 1e-6 ? sy / v : 0;
  var res = 0;
  pts.forEach(function (o) {
    var px = xm + vx * (o[0] - tm), py = ym + vy * (o[0] - tm);
    res += (o[2] - px) * (o[2] - px) + (o[3] - py) * (o[3] - py);
  });
  return { x: xm + vx * (t - tm), y: ym + vy * (t - tm), vx: vx, vy: vy, n: n,
           sigma: Math.sqrt(res / Math.max(1, n - 2)) + 2 };
};

/* Battery left after flying home (same model as swarm_common.energy, with learned drain). */
SW.Store.prototype.homeMargin = function (d, s) {
  var e = this.cfg.energy || {}, home = d.home;
  if (!s || !home) return null;
  var p = SW.geo.toEnu(s.lat, s.lon), h = SW.geo.toEnu(home[0], home[1]);
  var dist = Math.hypot(p[0] - h[0], p[1] - h[1]);
  var scale = d.brain ? d.brain.sc || 1 : 1;
  return s.batt - dist * (e.pct_per_m || 0.005) * scale - (e.reserve_pct || 20);
};
