/* Overlays that make the swarm's reasoning visible. */
'use strict';
var SW = window.SW || (window.SW = {});

SW.Overlays = function (scene, store) {
  this.scene = scene;
  this.store = store;
  this.v = scene.viewer;
  this.pts = this.v.scene.primitives.add(new Cesium.PointPrimitiveCollection());
  this.obsPts = this.v.scene.primitives.add(new Cesium.PointPrimitiveCollection());
  this.links = {};
  this.items = {};
  this.taskEnts = {};
  this.covEnts = {};
  this.bubbles = {};
  this.footprints = {};
  this._target();
  this._frustum();
};

var C = function (css, a) { return Cesium.Color.fromCssColorString(css).withAlpha(a == null ? 1 : a); };
var GOOD = '#34d399', WARN = '#fbbf24', BAD = '#f87171', INFO = '#38bdf8', MUTED = '#94a3b8';

SW.Overlays.prototype.dronePos = function (id) {
  var e = this.scene.entities[id];
  return e && e.st.s ? e.st.pos : null;
};

/* ------------------------------------------------------- radio links */
SW.Overlays.prototype._link = function (a, b) {
  var key = a < b ? a + '-' + b : b + '-' + a;
  if (this.links[key]) return this.links[key];
  var self = this, L = { q: 0, on: false };
  L.e = this.v.entities.add({
    polyline: {
      positions: new Cesium.CallbackProperty(function () {
        var pa = self.dronePos(a), pb = self.dronePos(b);
        return pa && pb ? [pa, pb] : [];
      }, false),
      width: new Cesium.CallbackProperty(function () { return 0.8 + 1.4 * L.q; }, false),
      material: new Cesium.ColorMaterialProperty(new Cesium.CallbackProperty(function () {
        var c = L.q > 0.8 ? INFO : L.q > 0.5 ? WARN : BAD;
        return C(c, 0.18 + 0.4 * L.q);
      }, false)),
      show: new Cesium.CallbackProperty(function () { return self.scene.layers.links && L.on; }, false),
      arcType: Cesium.ArcType.NONE,
    },
  });
  this.links[key] = L;
  return L;
};

SW.Overlays.prototype.updateLinks = function (t) {
  var s = this.store, self = this, seen = {};
  Object.keys(s.drones).forEach(function (k) {
    var d = s.drones[k];
    if (!d.brain || !s.alive(d, t)) return;
    (d.brain.nb || []).forEach(function (pair) {
      var o = s.drones[pair[0]];
      if (!o || !s.alive(o, t)) return;
      var L = self._link(d.id, pair[0]);
      var key = d.id < pair[0] ? d.id + '-' + pair[0] : pair[0] + '-' + d.id;
      L.q = seen[key] ? Math.min(L.q, pair[1]) : pair[1];       // weakest direction
      seen[key] = 1;
    });
  });
  Object.keys(this.links).forEach(function (k) { self.links[k].on = !!seen[k]; });
};

/* Packets in flight: dots travelling from the sender to every neighbour that hears it. */
SW.Overlays.prototype.updatePulses = function (t) {
  this.pts.removeAll();
  if (!this.scene.layers.packets) return;
  var s = this.store, self = this, DUR = 0.7;
  for (var i = s.pulses.length - 1; i >= 0; i--) {
    var p = s.pulses[i], age = t - p[0];
    if (age < 0) continue;
    if (age > DUR) break;
    var src = s.drones[p[1]];
    if (!src || !src.brain) continue;
    var from = self.dronePos(p[1]);
    if (!from) continue;
    var k = age / DUR;
    (src.brain.nb || []).forEach(function (n) {
      var to = self.dronePos(n[0]);
      if (!to) return;
      self.pts.add({
        position: Cesium.Cartesian3.lerp(from, to, k, new Cesium.Cartesian3()),
        pixelSize: p[2] === 'S' ? 7 : 4,
        color: p[2] === 'S' ? C('#e879f9', 1 - 0.6 * k) : C('#67e8f9', 0.9 - 0.6 * k),
        outlineColor: C('#000', 0.4), outlineWidth: 1,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      });
    });
  }
};

/* -------------------------------------------------- tasks & consensus */
SW.Overlays.prototype._taskEntity = function (tk) {
  var self = this, ent = this.taskEnts[tk.id];
  if (ent) return ent;
  var color = tk.k === 'RESCUE' ? BAD : tk.k === 'SEARCH' ? INFO : tk.k === 'INTERCEPT' ? '#fb923c' : GOOD;
  ent = { tk: tk, list: [] };
  var ll = function () { var t2 = self.taskEnts[tk.id].tk; return SW.geo.toLatLon(t2.x, t2.y); };
  if (tk.k === 'SEARCH' && tk.ar) {
    var a = SW.geo.toLatLon(tk.ar[0], tk.ar[1]), b = SW.geo.toLatLon(tk.ar[2], tk.ar[3]);
    var ring = [[a[0], a[1]], [a[0], b[1]], [b[0], b[1]], [b[0], a[1]], [a[0], a[1]]];
    ent.list.push(this.v.entities.add({
      polyline: { positions: ring.map(function (p) { return self.scene.pos(p[0], p[1], 0.5); }),
                  width: 2, material: new Cesium.PolylineDashMaterialProperty({ color: C(INFO, 0.9) }) },
    }));
  }
  if (tk.k === 'GOTO' || tk.k === 'RESCUE' || tk.k === 'SEARCH') {
    ent.list.push(this.v.entities.add({
      position: new Cesium.CallbackProperty(function () { var p = ll(); return self.scene.pos(p[0], p[1], 1); }, false),
      point: { pixelSize: tk.k === 'RESCUE' ? 13 : 10, color: new Cesium.CallbackProperty(function () {
        var st = self.taskEnts[tk.id].tk.st;
        return st === 'SUGGESTED' ? C(WARN, 0.5 + 0.5 * Math.abs(Math.sin(Date.now() / 300))) :
               st === 'DONE' ? C(GOOD, 0.6) : st === 'MERGED' ? C(MUTED, 0.4) : C(color);
      }, false), outlineColor: C('#020617'), outlineWidth: 2,
      disableDepthTestDistance: Number.POSITIVE_INFINITY },
      label: { text: new Cesium.CallbackProperty(function () {
        var t2 = self.taskEnts[tk.id].tk;
        var icon = t2.k === 'RESCUE' ? '✚ ' : t2.k === 'SEARCH' ? '⌕ ' : '◎ ';
        return icon + t2.id + (t2.st !== 'OPEN' ? ' · ' + t2.st.toLowerCase() : '');
      }, false), font: '600 12px Inter, system-ui, sans-serif', fillColor: C(color),
               outlineColor: C('#020617'), outlineWidth: 3, style: Cesium.LabelStyle.FILL_AND_OUTLINE,
               pixelOffset: new Cesium.Cartesian2(0, -18), disableDepthTestDistance: Number.POSITIVE_INFINITY,
               distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 12000) },
    }));
  }
  if (tk.k === 'FORMATION' || tk.k === 'INTERCEPT') {
    ent.ring = { cx: tk.x, cy: tk.y, r: tk.r || 300 };
    ent.list.push(this.v.entities.add({
      polyline: {
        positions: new Cesium.CallbackProperty(function () {
          var R = ent.ring, out = [], alt = ((self.store.cfg.motion || {}).base_alt_m || 30) + 10;
          for (var i = 0; i <= 72; i++) {
            var a2 = 2 * Math.PI * i / 72, p = SW.geo.toLatLon(R.cx + R.r * Math.cos(a2), R.cy + R.r * Math.sin(a2));
            out.push(self.scene.pos(p[0], p[1], alt));
          }
          return out;
        }, false),
        width: 2.5, arcType: Cesium.ArcType.NONE,
        show: new Cesium.CallbackProperty(function () { return self.taskEnts[tk.id].tk.st === 'OPEN'; }, false),
        material: new Cesium.PolylineGlowMaterialProperty({ glowPower: 0.2,
          color: new Cesium.CallbackProperty(function () {
            var ev = self.store.mission[tk.id], st = self.taskEnts[tk.id].tk.st;
            if (st !== 'OPEN') return C(MUTED, 0.0);
            return ev === 'PERIMETER_FORMED' ? C(GOOD, 0.9) : ev === 'PERIMETER_DEGRADED' ? C(BAD, 0.9) : C(color, 0.7);
          }, false) }),
      },
    }));
  }
  this.taskEnts[tk.id] = ent;
  return ent;
};

SW.Overlays.prototype.updateTasks = function (t) {
  var self = this, s = this.store;
  Object.keys(s.tasks).forEach(function (id) {
    var ent = self._taskEntity(s.tasks[id]);
    ent.tk = s.tasks[id];
  });
  Object.keys(this.taskEnts).forEach(function (id) {
    if (!s.tasks[id]) {
      self.taskEnts[id].list.forEach(function (e) { self.v.entities.remove(e); });
      delete self.taskEnts[id];
    }
  });
  var items = s.workItems(t), cons = s.consensus(t), live = {};
  items.forEach(function (it) {
    live[it.id] = 1;
    var te = self.taskEnts[it.parent];
    if (te && te.ring && it.cx != null) { te.ring.cx = it.cx; te.ring.cy = it.cy; te.ring.r = it.r; }
    var I = self.items[it.id] || self._item(it.id);
    I.it = it;
    I.c = cons[it.id] || { winners: [], agreed: false, voters: 0 };
  });
  Object.keys(this.items).forEach(function (id) { self.items[id].on = !!live[id]; });
};

SW.Overlays.prototype._item = function (id) {
  var self = this, I = { on: true, it: null, c: null };
  var alt = function () { return ((self.store.cfg.motion || {}).base_alt_m || 30) + 10; };
  var where = function () { var p = SW.geo.toLatLon(I.it.x, I.it.y); return self.scene.pos(p[0], p[1], I.it.slot != null ? alt() : 2); };
  var stateColor = function () {
    if (!I.c || !I.c.winners.length) return C(MUTED, 0.9);
    return I.c.agreed ? C(GOOD) : C(WARN);
  };
  if (id.indexOf('/s') > 0) {      // ring slot marker
    I.slot = this.v.entities.add({
      position: new Cesium.CallbackProperty(where, false),
      point: { pixelSize: 9, color: new Cesium.CallbackProperty(stateColor, false),
               outlineColor: C('#020617'), outlineWidth: 2, disableDepthTestDistance: Number.POSITIVE_INFINITY,
               show: new Cesium.CallbackProperty(function () { return I.on && self.scene.layers.consensus; }, false) },
    });
  }
  // claim lines: one per drone that anyone believes holds this item
  I.lines = [0, 1, 2].map(function (k) {
    return self.v.entities.add({
      polyline: {
        positions: new Cesium.CallbackProperty(function () {
          if (!I.on || !I.c || k >= I.c.winners.length) return [];
          var p = self.dronePos(I.c.winners[k]);
          return p ? [p, where()] : [];
        }, false),
        width: new Cesium.CallbackProperty(function () { return I.c && I.c.agreed ? 2 : 2.5; }, false),
        arcType: Cesium.ArcType.NONE,
        material: new Cesium.PolylineDashMaterialProperty({
          color: new Cesium.CallbackProperty(function () { return (I.c && I.c.agreed ? C(GOOD, 0.55) : C(WARN, 0.95)); }, false),
          dashLength: new Cesium.CallbackProperty(function () { return I.c && I.c.agreed ? 40 : 10; }, false),
        }),
        show: new Cesium.CallbackProperty(function () { return self.scene.layers.consensus; }, false),
      },
    });
  });
  this.items[id] = I;
  return I;
};

/* ------------------------------------------------ collision avoidance */
SW.Overlays.prototype.updateAvoidance = function (t) {
  var s = this.store, m = s.cfg.motion || {}, R = m.safety_radius_m || 6, lay = m.layer_spacing_m || 6;
  var self = this, close = {};
  var ids = Object.keys(s.drones).map(Number), snap = {};
  ids.forEach(function (i) { var e = self.scene.entities[i]; if (e && e.st.s && e.st.alive) snap[i] = e.st.s; });
  for (var a = 0; a < ids.length; a++) for (var b = a + 1; b < ids.length; b++) {
    var A = snap[ids[a]], B = snap[ids[b]];
    if (!A || !B || A.alt < 2 || B.alt < 2) continue;
    var pa = SW.geo.toEnu(A.lat, A.lon), pb = SW.geo.toEnu(B.lat, B.lon);
    var dh = Math.hypot(pa[0] - pb[0], pa[1] - pb[1]), dv = Math.abs(A.alt - B.alt);
    if (dv < 0.8 * lay && dh < 6 * R) {
      var sev = Math.max(0, Math.min(1, (6 * R - dh) / (4 * R)));
      close[ids[a]] = Math.max(close[ids[a]] || 0, sev);
      close[ids[b]] = Math.max(close[ids[b]] || 0, sev);
    }
  }
  ids.forEach(function (i) {
    var B = self.bubbles[i];
    if (!B) {
      B = self.bubbles[i] = { sev: 0 };
      B.e = self.v.entities.add({
        position: new Cesium.CallbackProperty(function () { return self.dronePos(i) || undefined; }, false),
        ellipsoid: { radii: new Cesium.Cartesian3(R, R, R),        // ORCA radius: keep bubbles apart
                     material: new Cesium.ColorMaterialProperty(new Cesium.CallbackProperty(function () {
                       return C(B.sev > 0.6 ? BAD : WARN, 0.10 + 0.22 * B.sev); }, false)),
                     outline: false, slicePartitions: 24, stackPartitions: 16 },
        show: new Cesium.CallbackProperty(function () { return self.scene.layers.avoidance && B.sev > 0; }, false),
      });
    }
    B.sev = close[i] || 0;
  });
};

/* ------------------------------------------------- coverage heatmap */
SW.Overlays.prototype.updateCoverage = function () {
  var s = this.store, self = this;
  Object.keys(s.coverage).forEach(function (id) {
    var c = s.coverage[id], E = self.covEnts[id];
    if (!E) {
      E = self.covEnts[id] = { canvas: document.createElement('canvas'), bits: null };
      E.canvas.width = c.nx; E.canvas.height = c.ny;
      var a = SW.geo.toLatLon(c.x0, c.y0), b = SW.geo.toLatLon(c.x0 + c.nx * c.cell, c.y0 + c.ny * c.cell);
      E.e = self.v.entities.add({
        rectangle: {
          coordinates: Cesium.Rectangle.fromDegrees(a[1], a[0], b[1], b[0]),
          material: new Cesium.ImageMaterialProperty({ image: new Cesium.CallbackProperty(function () { return E.canvas; }, false),
                                                       transparent: true }),
          height: 0.3,
          show: new Cesium.CallbackProperty(function () {
            var tk = s.tasks[id];
            return self.scene.layers.coverage && (!tk || tk.st === 'OPEN' || tk.st === 'DONE');
          }, false),
        },
      });
    }
    if (E.bits === c.bits) return;
    E.bits = c.bits;
    var ctx = E.canvas.getContext('2d'), img = ctx.createImageData(c.nx, c.ny), bits = c.bits;
    for (var i = 0; i < c.nx; i++) for (var j = 0; j < c.ny; j++) {
      var on = (bits >> BigInt(i * c.ny + j)) & 1n;
      var px = ((c.ny - 1 - j) * c.nx + i) * 4;          // canvas rows go north->south
      if (on) { img.data[px] = 103; img.data[px + 1] = 232; img.data[px + 2] = 249; img.data[px + 3] = 58; }
      else { img.data[px] = 2; img.data[px + 1] = 6; img.data[px + 2] = 23; img.data[px + 3] = 18; }
    }
    ctx.putImageData(img, 0, 0);
  });
};

/* ---------------------------------------------- sensors & sightings */
SW.Overlays.prototype.updateSensors = function (t) {
  var s = this.store, self = this, p = s.cfg.perception || {};
  var half = ((p.hfov_deg || 78) + (p.vfov_deg || 49)) / 4 * Math.PI / 180;
  Object.keys(s.drones).forEach(function (k) {
    var id = Number(k), F = self.footprints[id];
    if (!F) {
      F = self.footprints[id] = { r: 1 };
      F.e = self.v.entities.add({
        position: new Cesium.CallbackProperty(function () {
          var e = self.scene.entities[id];
          return e && e.st.s ? self.scene.pos(e.st.s.lat, e.st.s.lon, 0.4) : undefined;
        }, false),
        ellipse: { semiMajorAxis: new Cesium.CallbackProperty(function () { return F.r; }, false),
                   semiMinorAxis: new Cesium.CallbackProperty(function () { return F.r; }, false),
                   material: C(SW.colorOf(id), 0.06), outline: true, outlineColor: C(SW.colorOf(id), 0.7),
                   height: 0.4 },
        show: new Cesium.CallbackProperty(function () { return self.scene.layers.sensors && F.r > 3; }, false),
      });
    }
    var e = self.scene.entities[id];
    F.r = e && e.st.s && e.st.alive && e.st.s.alt > 8 ? e.st.s.alt * Math.tan(half) : 0;
  });
  // recent sightings from every drone
  this.obsPts.removeAll();
  if (!this.scene.layers.sensors) return;
  for (var i = s.obs.length - 1; i >= 0; i--) {
    var o = s.obs[i], age = t - o[0];
    if (age < 0) continue;
    if (age > 90) break;
    var ll = SW.geo.toLatLon(o[2], o[3]);
    this.obsPts.add({ position: this.scene.pos(ll[0], ll[1], 0.8), pixelSize: o[1] === 'person' ? 6 : 4,
                      color: C(o[1] === 'person' ? '#fde047' : '#fb923c', Math.max(0.15, 1 - age / 90)),
                      outlineColor: C(SW.colorOf(o[4]), 0.9), outlineWidth: 1.5 });
  }
};

SW.Overlays.prototype._frustum = function () {
  var self = this, s = this.store;
  var corners = function () {
    var id = self.scene.selected, e = self.scene.entities[id];
    if (!e || !e.st.s || e.st.s.alt < 8 || !self.scene.layers.sensors) return null;
    var p = s.cfg.perception || {}, smp = e.st.s, c = SW.geo.toEnu(smp.lat, smp.lon);
    var hx = smp.alt * Math.tan((p.hfov_deg || 78) * Math.PI / 360);
    var hy = smp.alt * Math.tan((p.vfov_deg || 49) * Math.PI / 360);
    var yaw = smp.yaw, out = [];
    [[1, 1], [1, -1], [-1, -1], [-1, 1]].forEach(function (q) {
      var fx = q[0] * hy, fy = q[1] * hx;                  // forward / left in body frame
      var x = c[0] + fx * Math.cos(yaw) - fy * Math.sin(yaw), y = c[1] + fx * Math.sin(yaw) + fy * Math.cos(yaw);
      var ll = SW.geo.toLatLon(x, y);
      out.push(self.scene.pos(ll[0], ll[1], 0.5));
    });
    return { apex: e.st.pos, c: out };
  };
  [0, 1, 2, 3].forEach(function (k) {
    self.v.entities.add({ polyline: { positions: new Cesium.CallbackProperty(function () {
      var f = corners(); return f ? [f.apex, f.c[k]] : []; }, false), width: 1.2, material: C('#e2e8f0', 0.6),
      arcType: Cesium.ArcType.NONE } });
  });
  this.v.entities.add({ polyline: { positions: new Cesium.CallbackProperty(function () {
    var f = corners(); return f ? f.c.concat([f.c[0]]) : []; }, false), width: 1.5, material: C('#e2e8f0', 0.8),
    arcType: Cesium.ArcType.NONE } });
};

/* --------------------------------------------------- moving target */
SW.Overlays.prototype._target = function () {
  var self = this, s = this.store;
  var truth = function () {
    var q = s.quarry;
    if (!q || s.now - q.t > 5) return null;
    var dt = s.now - q.t, ll = SW.geo.toLatLon(q.x + q.vx * dt, q.y + q.vy * dt);
    return self.scene.pos(ll[0], ll[1], 1.5);
  };
  this.v.entities.add({
    position: new Cesium.CallbackProperty(function () { return truth() || undefined; }, false),
    point: { pixelSize: 12, color: C(BAD), outlineColor: C('#fff', 0.8), outlineWidth: 2,
             disableDepthTestDistance: Number.POSITIVE_INFINITY,
             show: new Cesium.CallbackProperty(function () { return self.scene.layers.target && !!truth(); }, false) },
    label: { text: 'target', font: '600 11px Inter, system-ui, sans-serif', fillColor: C(BAD),
             outlineColor: C('#020617'), outlineWidth: 3, style: Cesium.LabelStyle.FILL_AND_OUTLINE,
             pixelOffset: new Cesium.Cartesian2(14, 0), horizontalOrigin: Cesium.HorizontalOrigin.LEFT,
             disableDepthTestDistance: Number.POSITIVE_INFINITY,
             show: new Cesium.CallbackProperty(function () { return self.scene.layers.target && !!truth(); }, false) },
  });
  var fused = function () { return s.fusedTrack(s.now); };
  this.v.entities.add({
    position: new Cesium.CallbackProperty(function () {
      var f = fused(); if (!f) return undefined;
      var ll = SW.geo.toLatLon(f.x, f.y); return self.scene.pos(ll[0], ll[1], 0.6);
    }, false),
    ellipse: { semiMajorAxis: new Cesium.CallbackProperty(function () { var f = fused(); return f ? 3 * f.sigma : 1; }, false),
               semiMinorAxis: new Cesium.CallbackProperty(function () { var f = fused(); return f ? 3 * f.sigma : 1; }, false),
               material: C('#fb923c', 0.25), outline: true, outlineColor: C('#fb923c'), height: 0.6 },
    show: new Cesium.CallbackProperty(function () { return self.scene.layers.target && !!fused(); }, false),
  });
  this.v.entities.add({     // 30 s prediction from the fused constant-velocity track
    polyline: { positions: new Cesium.CallbackProperty(function () {
      var f = fused(); if (!f) return [];
      var a = SW.geo.toLatLon(f.x, f.y), b = SW.geo.toLatLon(f.x + f.vx * 30, f.y + f.vy * 30);
      return [self.scene.pos(a[0], a[1], 1), self.scene.pos(b[0], b[1], 1)];
    }, false), width: 8, arcType: Cesium.ArcType.NONE,
    material: new Cesium.PolylineArrowMaterialProperty(C('#fb923c', 0.9)),
    show: new Cesium.CallbackProperty(function () { return self.scene.layers.target && !!fused(); }, false) },
  });
};

/* Ground-truth survivors (simulation only, off by default) */
SW.Overlays.prototype.addTruth = function (victims) {
  var self = this;
  (victims || []).forEach(function (v) {
    var ll = SW.geo.toLatLon(v[0], v[1]);
    self.v.entities.add({ position: self.scene.pos(ll[0], ll[1], 0.5),
      point: { pixelSize: 8, color: C('#fff', 0.85), outlineColor: C(BAD), outlineWidth: 2,
               show: new Cesium.CallbackProperty(function () { return self.scene.layers.truth; }, false) },
      label: { text: 'survivor (truth)', font: '11px Inter, system-ui, sans-serif', pixelOffset: new Cesium.Cartesian2(0, 14),
               fillColor: C('#fff'), outlineColor: C('#020617'), outlineWidth: 3, style: Cesium.LabelStyle.FILL_AND_OUTLINE,
               show: new Cesium.CallbackProperty(function () { return self.scene.layers.truth; }, false) } });
  });
};

SW.Overlays.prototype.update = function (t) {
  this.updateLinks(t);
  this.updatePulses(t);
  this.updateTasks(t);
  this.updateAvoidance(t);
  this.updateCoverage();
  this.updateSensors(t);
};
