/* Panels, timeline, layer toggles and operator tools. */
'use strict';
var SW = window.SW || (window.SW = {});

SW.settings = {
  get: function (k) { try { return localStorage.getItem('swarm.' + k); } catch (e) { return null; } },
  set: function (k, v) { try { localStorage.setItem('swarm.' + k, v); } catch (e) { /* private mode */ } },
};

function $(id) { return document.getElementById(id); }
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
  return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
function mmss(t) { t = Math.max(0, Math.floor(t)); return ('0' + Math.floor(t / 60)).slice(-2) + ':' + ('0' + t % 60).slice(-2); }

SW.UI = function (store, scene, overlays, source) {
  this.s = store; this.scene = scene; this.ov = overlays; this.src = source;
  this.t0 = source.kind === 'replay' ? 0 : source.now();
  this.op = null; this._searchA = null; this._feedN = -1; this._orbit = false;
  var self = this;
  scene.onSelect = function () { self.renderRoster(); };
  this._wire();
  this._ticks();
  setInterval(function () { self.render(); }, 250);
};

SW.UI.prototype._wire = function () {
  var self = this, src = this.src;
  var mode = $('mode');
  if (src.kind === 'replay') { mode.className = 'pill replay'; mode.textContent = 'REPLAY · ' + (src.meta.name || 'recording'); }
  else { $('transport').style.display = 'none'; $('ops').style.display = 'flex'; }
  $('btnPlay').onclick = function () {
    if (src.t >= src.t1) src.seek(0);
    src.playing = !src.playing; self._transport(); };
  var speeds = [1, 2, 4, 8, 16, 32];
  $('btnSpeed').onclick = function () {
    src.speed = speeds[(speeds.indexOf(src.speed) + 1) % speeds.length]; self._transport(); };
  $('range').oninput = function () { src.seek(src.t1 * this.value / 1000); };
  document.querySelectorAll('[data-layer]').forEach(function (b) {
    b.onclick = function () {
      var k = b.getAttribute('data-layer');
      self.scene.layers[k] = !self.scene.layers[k];
      b.classList.toggle('on', self.scene.layers[k]);
    };
  });
  document.querySelectorAll('[data-tab]').forEach(function (b) {
    b.onclick = function () {
      var el = $(b.getAttribute('data-tab')), on = !el.classList.contains('show');
      document.querySelectorAll('.side').forEach(function (x) { x.classList.remove('show'); });
      document.querySelectorAll('[data-tab]').forEach(function (x) { x.classList.remove('on'); });
      if (on) { el.classList.add('show'); b.classList.add('on'); }
    };
  });
  $('btnLayers').onclick = function () { $('layers').classList.toggle('show'); this.classList.toggle('on'); };
  $('btnOverview2').onclick = function () { self.scene.overview(); };
  $('btnOverview').onclick = function () { self._orbit = false; $('btnOrbit').classList.remove('on'); self.scene.overview(); };
  $('btnOrbit').onclick = function () {
    self._orbit = !self._orbit; this.classList.toggle('on', self._orbit);
    if (self._orbit) self.scene.unfollow();
  };
  $('btnSettings').onclick = function () {
    $('ionToken').value = SW.settings.get('ionToken') || '';
    $('rosUrl').value = SW.settings.get('rosUrl') || '';
    $('heroScale').value = SW.settings.get('heroScale') || 6;
    $('quality').value = SW.settings.get('quality') || 'auto';
    $('settings').style.display = 'block';
  };
  $('closeSettings').onclick = function () { $('settings').style.display = 'none'; };
  $('saveSettings').onclick = function () {
    SW.settings.set('ionToken', $('ionToken').value.trim());
    SW.settings.set('rosUrl', $('rosUrl').value.trim());
    SW.settings.set('heroScale', $('heroScale').value || '6');
    SW.settings.set('quality', $('quality').value === 'auto' ? '' : $('quality').value);
    location.reload();
  };
  // ---- operator tools (live only)
  document.querySelectorAll('[data-op]').forEach(function (b) {
    b.onclick = function () {
      var op = b.getAttribute('data-op');
      self.op = self.op === op ? null : op; self._searchA = null;
      document.querySelectorAll('[data-op]').forEach(function (x) { x.classList.toggle('on', x.getAttribute('data-op') === self.op); });
      if (self.op) self.toast(op === 'SEARCH' ? 'Click the first corner of the search area' : 'Click the map to place ' + op);
    };
  });
  document.querySelectorAll('[data-cmd]').forEach(function (b) {
    b.onclick = function () {
      var cmd = b.getAttribute('data-cmd'), id = self.scene.selected;
      var label = id ? 'D' + id : 'ALL';
      if ((cmd === 'ESTOP' || label === 'ALL') && !confirm(cmd + ' → ' + label + ' ?')) return;
      src.sendCommand(label, cmd);
      self.toast(cmd + ' → ' + label);
    };
  });
  this.scene.onGroundClick = function (lat, lon) {
    if (!self.op || src.kind !== 'live') return;
    var n = Date.now() % 100000;
    if (self.op === 'SEARCH') {
      if (!self._searchA) { self._searchA = [lat, lon]; self.toast('Now click the opposite corner'); return; }
      var a = self._searchA;
      src.sendTask('SEARCH-' + n, (a[0] + lat) / 2, (a[1] + lon) / 2,
                   'area=' + [a[0], a[1], lat, lon].map(function (v) { return v.toFixed(6); }).join(','));
      self._searchA = null;
    } else {
      var prefix = { GOTO: 'T', SWARM: 'SWARM-', INTERCEPT: 'INTERCEPT-' }[self.op];
      src.sendTask(prefix + n, lat, lon, 'operator');
    }
    self.toast(self.op + ' sent - the swarm will allocate it by consensus');
    self.op = null;
    document.querySelectorAll('[data-op]').forEach(function (x) { x.classList.remove('on'); });
  };
};

SW.UI.prototype.toast = function (msg) {
  var t = $('toast'); t.textContent = msg; t.style.display = 'block';
  clearTimeout(this._toastT);
  this._toastT = setTimeout(function () { t.style.display = 'none'; }, 3200);
};

SW.UI.prototype._transport = function () {
  var src = this.src;
  $('btnPlay').textContent = src.playing ? '❚❚' : '▶';
  $('btnSpeed').textContent = src.speed + '×';
};

SW.UI.prototype._ticks = function () {
  var src = this.src;
  if (src.kind !== 'replay') return;
  var html = '';
  src.rows.forEach(function (r) {
    if (r[1] !== 'e') return;
    var c = r[2][1] === 'PERIMETER_FORMED' ? '#34d399' : r[2][1] === 'PERIMETER_DEGRADED' ? '#f87171' : '#94a3b8';
    html += '<span style="left:' + (100 * r[0] / src.t1).toFixed(2) + '%;background:' + c + '"></span>';
  });
  (src.meta.story || []).forEach(function (s) {
    html += '<span style="left:' + (100 * s[0] / src.t1).toFixed(2) + '%;background:#e879f9;height:10px;top:-2px"></span>';
  });
  $('ticks').innerHTML = html;
  $('dur').textContent = mmss(src.t1);
};

/* ---------------------------------------------------------- render */
SW.UI.prototype.render = function () {
  var t = this.s.now, src = this.src;
  $('clock').textContent = 'T+' + mmss(t - this.t0);
  if (src.kind === 'replay') {
    $('range').value = Math.round(1000 * src.t / Math.max(1, src.t1));
    this._transport();
    var story = (src.meta.story || []).filter(function (s) { return s[0] <= t && t - s[0] < 24; }).pop();
    var cap = $('caption');
    if (story) { cap.style.display = 'block'; cap.textContent = story[1]; } else cap.style.display = 'none';
  } else {
    var mode = $('mode');
    mode.className = 'pill ' + (src.connected ? 'live' : 'off');
    mode.textContent = src.connected ? 'LIVE' : 'OFFLINE';
  }
  this.renderBanner();
  this.renderRoster();
  this.renderTasks();
  this.renderFeed();
};

SW.UI.prototype.renderBanner = function () {
  var b = this.s.banner, el = $('banner');
  if (!b || this.s.now - b.t > 25 || this.s.now < b.t) { el.style.display = 'none'; return; }
  var cls = b.ev === 'PERIMETER_FORMED' ? 'good' : b.ev === 'PERIMETER_DEGRADED' ? 'bad' : 'info';
  el.className = 'glass ' + cls; el.style.display = 'block';
  el.textContent = { PERIMETER_FORMED: '⬢ PERIMETER FORMED', PERIMETER_DEGRADED: '⬡ PERIMETER DEGRADED',
                     RELEASED: '◌ RELEASED' }[b.ev] + ' · ' + b.task + ' · ' + b.detail;
};

SW.UI.prototype.renderRoster = function () {
  var s = this.s, sc = this.scene, t = s.now, html = '', alive = 0, air = 0;
  var e = s.cfg.energy || {};
  Object.keys(s.drones).map(Number).sort(function (a, b) { return a - b; }).forEach(function (id) {
    var d = s.drones[id], smp = d.track.at(t), b = d.brain || {};
    if (!smp) return;
    var ok = s.alive(d, t);
    if (ok) alive++;
    if (ok && smp.alt > 1) air++;
    var ph = !ok ? 'LOST' : (smp.latch ? 'FAILSAFE' : (b.ph || '—'));
    var batt = Math.max(0, smp.batt), margin = s.homeMargin(d, smp);
    var reserveAt = margin == null ? (e.reserve_pct || 20) : batt - margin;   // battery needed to get home
    var bc = batt > 50 ? '#34d399' : batt > 25 ? '#fbbf24' : '#f87171';
    var nb = (b.nb || []).length, q = (b.nb || []).reduce(function (a, n) { return a + n[1]; }, 0) / Math.max(1, nb);
    html += '<div class="drone' + (sc.selected === id ? ' sel' : '') + (ok ? '' : ' lost') + '" data-id="' + id + '">' +
      '<div class="row"><span class="dot" style="color:' + SW.colorOf(id) + ';background:' + SW.colorOf(id) + '"></span>' +
      '<span class="name">' + d.label + '</span><span class="chip ' + esc(ph) + '">' + esc(ph) + '</span>' +
      '<span class="task">' + esc(b.tk || '') + '</span></div>' +
      '<div class="batt"><i style="width:' + batt.toFixed(0) + '%;background:' + bc + '"></i>' +
      '<b title="needed to get home + reserve" style="left:' + Math.max(0, Math.min(100, reserveAt)).toFixed(0) + '%"></b></div>' +
      '<div class="meta"><span>' + batt.toFixed(0) + '%</span>' +
      (margin != null ? '<span class="' + (margin < 5 ? 'bad' : margin < 15 ? 'warn' : 'good') + '">home +' + Math.max(0, margin).toFixed(0) + '%</span>' : '') +
      '<span>' + smp.alt.toFixed(0) + ' m</span><span>' + Math.hypot(smp.vx, smp.vy).toFixed(1) + ' m/s</span>' +
      '<span title="neighbours heard directly · mean packet-receipt ratio">⇋ ' + nb + (nb ? ' · ' + Math.round(q * 100) + '%' : '') + '</span>' +
      (b.sc && b.sc > 1.2 ? '<span class="warn" title="learned drain vs model">drain ' + b.sc.toFixed(1) + '×</span>' : '') +
      (smp.latch ? '<span class="bad">🔒 ' + esc(smp.latch) + '</span>' : '') + '</div></div>';
  });
  $('roster').innerHTML = html;
  $('fleetSummary').textContent = alive + ' alive · ' + air + ' airborne';
  var self = this;
  document.querySelectorAll('.drone').forEach(function (el) {
    el.onclick = function () { self.scene.select(parseInt(el.getAttribute('data-id'), 10)); self.renderRoster(); };
    el.ondblclick = function () { self.scene.followDrone(parseInt(el.getAttribute('data-id'), 10)); };
  });
};

SW.UI.prototype.renderTasks = function () {
  var s = this.s, t = s.now, cons = s.consensus(t), items = s.workItems(t), html = '';
  var byParent = {};
  items.forEach(function (it) { (byParent[it.parent] = byParent[it.parent] || []).push(it); });
  var ids = Object.keys(s.tasks).sort(function (a, b) {
    var ra = s.tasks[a].st === 'OPEN' || s.tasks[a].st === 'SUGGESTED' ? 0 : 1;
    var rb = s.tasks[b].st === 'OPEN' || s.tasks[b].st === 'SUGGESTED' ? 0 : 1;
    return ra - rb || (s.tasks[b].ct || 0) - (s.tasks[a].ct || 0);
  });
  var open = 0, agreedAll = 0, total = 0;
  ids.slice(0, 14).forEach(function (id) {
    var tk = s.tasks[id], its = byParent[id] || [];
    if (tk.st === 'OPEN') open++;
    var slots = its.map(function (it) {
      var c = cons[it.id], w = c && c.winners.length ? c.winners : [];
      total++;
      if (c && c.agreed) agreedAll++;
      var cls = !w.length ? '' : c.agreed ? 'agreed' : 'contested';
      var lab = (it.slot != null ? 's' + it.slot + ' ' : '') + (w.length ? w.map(function (x) { return 'D' + x; }).join('|') : 'open');
      return '<span class="slot ' + cls + '" title="' + (cls === 'contested' ? 'drones disagree - consensus in progress' : '') + '">' + lab + '</span>';
    }).join('');
    var extra = '';
    if (tk.k === 'SEARCH' && s.coverage[id]) {
      var c = s.coverage[id], n = 0, bits = c.bits;
      while (bits > 0n) { n += Number(bits & 1n); bits >>= 1n; }
      extra = '<span class="slot agreed">covered ' + Math.round(100 * n / (c.nx * c.ny)) + '%</span>';
    }
    var stc = { OPEN: 'ENROUTE', SUGGESTED: 'RTB', DONE: 'ON_TASK', MERGED: '', CANCELLED: 'FAILSAFE' }[tk.st] || '';
    html += '<div class="tk"><div class="hd"><span class="id">' + esc(id) + '</span><span class="chip">' + esc(tk.k) +
      '</span><span class="chip st ' + stc + '">' + esc(tk.st) + '</span></div>' +
      (tk.d ? '<div style="color:var(--dim);font-size:11px;margin-top:3px">' + esc(tk.d) + '</div>' : '') +
      ((slots || extra) ? '<div class="slots">' + slots + extra + '</div>' : '') + '</div>';
  });
  $('tasks').innerHTML = html || '<div style="color:var(--dim);padding:4px">No tasks yet.</div>';
  $('mindSummary').textContent = open + ' open · ' + (total ? Math.round(100 * agreedAll / total) : 100) + '% agreed';
};

SW.UI.prototype.renderFeed = function () {
  var s = this.s, t = s.now;
  var ev = s.events.filter(function (e) { return e.t <= t; });
  if (ev.length === this._feedN) return;
  this._feedN = ev.length;
  var t0 = this.t0;
  $('feed').innerHTML = ev.slice(-60).reverse().map(function (e) {
    return '<div class="ev ' + e.kind + '"><span class="t">' + mmss(e.t - t0) + '</span><span class="i">' + e.icon +
           '</span><span>' + esc(e.text) + '</span></div>';
  }).join('');
};

/* cinematic orbit around the action */
SW.UI.prototype.frame = function (wallDt) {
  if (!this._orbit) return;
  var v = this.scene.viewer, cam = v.camera, cv = v.scene.canvas;
  var c = cam.pickEllipsoid(new Cesium.Cartesian2(cv.clientWidth / 2, cv.clientHeight / 2));
  if (!c) return;
  cam.lookAtTransform(Cesium.Transforms.eastNorthUpToFixedFrame(c));
  cam.rotateRight(0.05 * wallDt);
  cam.lookAtTransform(Cesium.Matrix4.IDENTITY);
};
