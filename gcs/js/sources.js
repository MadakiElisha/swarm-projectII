/* Data sources. Both write into SW.Store and expose a clock:
 *   ReplaySource - a recording made by scripts/record_demo.py (no ROS needed)
 *   LiveSource   - rosbridge. The GCS LISTENS TO THE SWARM RADIO (/swarm/radio):
 *                  it decodes the very gossip packets the drones exchange, so
 *                  what you see is the drones' own consensus, not a summary.
 */
'use strict';
var SW = window.SW || (window.SW = {});

/* ------------------------------------------------------------- replay */
SW.ReplaySource = function (rec) {
  this.rec = rec;
  this.meta = rec.meta;
  this.rows = rec.rows;
  this.t0 = this.rows.length ? this.rows[0][0] : 0;
  this.t1 = this.meta.duration || (this.rows.length ? this.rows[this.rows.length - 1][0] : 0);
  this.t = 0;
  this.speed = 4;
  this.playing = true;
  this.idx = 0;
  this.kind = 'replay';
};
SW.ReplaySource.prototype.fleet = function () {
  var m = this.meta;
  return { origin: m.origin, drones: m.drones, swarm: m.cfg, area: m.area };
};
SW.ReplaySource.prototype.attach = function (store) {
  this.store = store;
  var fsm = this.meta.fsm_states || [];
  // flight tracks are loaded up front: scrubbing is exact and smooth
  this.rows.forEach(function (r) {
    if (r[1] !== 'v') return;
    var p = r[2];
    store.vehicle(r[0], { id: p[0], lat: p[1], lon: p[2], alt: p[3], vx: p[4], vy: p[5], batt: p[6],
                          roll: p[7], pitch: p[8], yaw: p[9], fsm: fsm[p[10]] || '', latch: p[11],
                          alive: p[12] });
  });
};
SW.ReplaySource.prototype.apply = function (r) {
  var s = this.store, t = r[0], p = r[2];
  switch (r[1]) {
    case 'b': s.brain(t, p); break;
    case 'T': s.setTasks(t, p); break;
    case 'c': s.setCoverage(t, p); break;
    case 'o': s.observation(t, p); break;
    case 'p': s.pulse(t, p[0], p[1]); break;
    case 'e': s.missionEvent(t, p[0], p[1], p[2], p[3]); break;
    case 'a': s.assignment(t, p[0], p[1]); break;
    case 's': s.suggestion(t, p[0], p[1]); break;
    case 'q': s.quarry = { t: t, x: p[0], y: p[1], vx: p[2], vy: p[3] }; break;
  }
};
SW.ReplaySource.prototype.seek = function (t) {
  t = Math.max(0, Math.min(this.t1, t));
  if (t < this.t) {                     // going back: rebuild discrete state from the start
    this.store.reset();
    this.idx = 0;
  }
  this.t = t;
  this.advance();
};
SW.ReplaySource.prototype.advance = function () {
  var rows = this.rows;
  while (this.idx < rows.length && rows[this.idx][0] <= this.t) {
    if (rows[this.idx][1] !== 'v') this.apply(rows[this.idx]);
    this.idx++;
  }
  this.store.now = this.t;
};
SW.ReplaySource.prototype.tick = function (dt) {
  if (this.playing) {
    this.t = Math.min(this.t1, this.t + dt * this.speed);
    if (this.t >= this.t1) this.playing = false;
  }
  this.advance();
  return this.t;
};
SW.ReplaySource.prototype.renderTime = function () { return this.t; };

/* --------------------------------------------------------------- live */
SW.LiveSource = function (url, fleet) {
  this.url = url;
  this._fleet = fleet;
  this.kind = 'live';
  this.connected = false;
  this.nb = {};
  this.seenObs = {};
  this.lastState = {};
};
SW.LiveSource.prototype.fleet = function () { return this._fleet; };
SW.LiveSource.prototype.now = function () { return Date.now() / 1000; };
SW.LiveSource.prototype.renderTime = function () { return this.now() - 0.3; };   // interpolation delay
SW.LiveSource.prototype.tick = function () { var t = this.now(); this.store.now = t; return t; };

SW.LiveSource.prototype.attach = function (store, onStatus) {
  var self = this;
  this.store = store;
  var ros = this.ros = new ROSLIB.Ros({ url: this.url });
  ros.on('connection', function () { self.connected = true; onStatus && onStatus('live', 'connected'); });
  ros.on('close', function () { self.connected = false; onStatus && onStatus('live', 'disconnected'); });
  ros.on('error', function () { self.connected = false; onStatus && onStatus('live', 'error'); });
  function topic(name, type, cb, throttle) {
    var tp = new ROSLIB.Topic({ ros: ros, name: name, messageType: type, throttle_rate: throttle || 0,
                                queue_length: 50 });
    if (cb) tp.subscribe(cb);
    return tp;
  }
  (this._fleet.drones || []).forEach(function (d) {
    topic('/swarm/' + d.label + '/vehicle_state', 'swarm_interfaces/msg/VehicleState', function (m) {
      if (!m.connected) return;
      store.vehicle(self.now(), { id: m.drone_id, lat: m.lat, lon: m.lon, alt: m.alt, vx: m.vx, vy: m.vy,
                                  batt: m.battery_pct, roll: m.roll, pitch: m.pitch, yaw: m.yaw_enu,
                                  fsm: m.fsm_state, latch: m.latch, alive: 1 });
    }, 100);
  });
  topic('/swarm/neighbors', 'swarm_interfaces/msg/NeighborReport', function (m) {
    self.nb[m.drone_id] = m.neighbors.map(function (l, i) {
      return [parseInt(l.slice(1), 10), m.link_quality[i]];
    });
  });
  topic('/swarm/radio', 'swarm_interfaces/msg/SwarmPacket', function (m) { self.onRadio(m); });
  topic('/swarm/task_assignments', 'swarm_interfaces/msg/TaskAssignment', function (m) {
    store.assignment(self.now(), parseInt(m.assigned_to.slice(1), 10), m.item_id);
  });
  topic('/swarm/mission_event', 'swarm_interfaces/msg/MissionEvent', function (m) {
    store.missionEvent(self.now(), m.task_id, m.event, m.detail, (m.reporter || '').slice(1));
  });
  topic('/swarm/task_suggestions', 'swarm_interfaces/msg/TaskRequest', function (m) {
    store.suggestion(self.now(), m.task_id, 0);
  });
  topic('/swarm/target_track', 'swarm_interfaces/msg/TargetTrack', function (m) {
    var p = SW.geo.toEnu(m.lat, m.lon);
    store.quarry = { t: self.now(), x: p[0], y: p[1], vx: m.vel_e, vy: m.vel_n };
  }, 500);
  (this._fleet.drones || []).forEach(function (d) {          // camera views with detection boxes
    topic('/swarm/' + d.label + '/camera/annotated', 'sensor_msgs/msg/CompressedImage', function (m) {
      store.cams = store.cams || {};
      store.cams[d.id] = { t: Date.now() / 1000, src: 'data:image/jpeg;base64,' + m.data };
    }, 400);
  });
  topic('/swarm/demo/stage', 'std_msgs/msg/String', function (m) {     // exhibition director (scripts/demo.py)
    try { store.demo = JSON.parse(m.data); store.demoV = (store.demoV || 0) + 1; } catch (e) { /* ignore */ }
  });
  topic('/swarm/sim/scene', 'std_msgs/msg/String', function (m) {      // simulation only: the world
    try { store.world = JSON.parse(m.data); store.worldV = (store.worldV || 0) + 1; } catch (e) { /* ignore */ }
  }, 2000);
  this.reqTopic = topic('/swarm/task_requests', 'swarm_interfaces/msg/TaskRequest');
  this.cmdTopic = topic('/swarm/commands', 'swarm_interfaces/msg/DroneCommand');
};

/* Decode one gossip packet exactly like a drone would. */
SW.LiveSource.prototype.onRadio = function (m) {
  var t = this.now(), s = this.store;
  s.pulse(t, m.src, m.kind);
  if (m.kind !== 'S') return;
  // the GCS only needs ~1 state packet per drone per second
  if (t - (this.lastState[m.src] || 0) < 0.9) return;
  this.lastState[m.src] = t;
  var pkt;
  try { pkt = JSON.parse(m.payload); } catch (e) { return; }
  var d = pkt.d || {}, self = this;
  var me = (d.r || []).filter(function (e) { return e.id === m.src; })[0] || {};
  var cb = d.cbba || {};
  s.brain(t, { i: m.src, ph: me.phase, tk: me.task, sc: me.drain || 1, nb: this.nb[m.src] || [],
               z: cb.z || {}, y: cb.y || {} });
  var cell = ((s.cfg.coverage || {}).cell_m) || 40;
  var tasks = (d.tasks || []).map(function (w) {
    var p = w.params || {}, o = { id: w.id, k: w.kind, x: w.x, y: w.y, st: w.status, ct: w.created_t };
    if (p.n_slots) o.n = p.n_slots;
    if (p.radius) o.r = p.radius;
    if (p.area) o.ar = p.area;
    if (p.desc) o.d = p.desc;
    return o;
  });
  // union with what we already know (another drone may be ahead on some tasks)
  var rank = { SUGGESTED: 0, OPEN: 1, DONE: 2, CANCELLED: 3, MERGED: 4 };
  var merged = tasks.filter(function (tk) {
    var old = s.tasks[tk.id];
    return !old || rank[tk.st] >= rank[old.st];
  });
  if (merged.length) s.setTasks(t, merged.concat(Object.keys(s.tasks).map(function (k) { return s.tasks[k]; })
    .filter(function (o) { return !merged.some(function (x) { return x.id === o.id; }); })));
  Object.keys(d.cov || {}).forEach(function (tid) {
    var tk = s.tasks[tid];
    if (!tk || !tk.ar) return;
    var x0 = Math.min(tk.ar[0], tk.ar[2]), y0 = Math.min(tk.ar[1], tk.ar[3]);
    var nx = Math.max(1, Math.ceil(Math.abs(tk.ar[2] - tk.ar[0]) / cell));
    var ny = Math.max(1, Math.ceil(Math.abs(tk.ar[3] - tk.ar[1]) / cell));
    var prev = s.coverage[tid], bits;
    try { bits = BigInt('0x' + (d.cov[tid] || '0')); } catch (e) { return; }
    if (prev) bits = bits | prev.bits;                    // G-Set union, like the drones
    s.setCoverage(t, { id: tid, x0: x0, y0: y0, cell: cell, nx: nx, ny: ny, bits: bits.toString(16) });
  });
  Object.keys(d.flood || {}).forEach(function (tid) {    // flood recon: cells under water
    var tk = s.tasks[tid];
    if (!tk || !tk.ar) return;
    var x0 = Math.min(tk.ar[0], tk.ar[2]), y0 = Math.min(tk.ar[1], tk.ar[3]);
    var nx = Math.max(1, Math.ceil(Math.abs(tk.ar[2] - tk.ar[0]) / cell));
    var ny = Math.max(1, Math.ceil(Math.abs(tk.ar[3] - tk.ar[1]) / cell));
    var prev = s.coverage[tid + '#water'], bits;
    try { bits = BigInt('0x' + (d.flood[tid] || '0')); } catch (e) { return; }
    if (prev) bits = bits | prev.bits;
    s.setCoverage(t, { id: tid, water: 1, x0: x0, y0: y0, cell: cell, nx: nx, ny: ny, bits: bits.toString(16) });
  });
  (d.obs || []).forEach(function (o) {
    if (self.seenObs[o.oid]) return;
    self.seenObs[o.oid] = 1;
    s.observation(o.t || t, [o.cls, o.x, o.y, o.observer]);
  });
};

SW.LiveSource.prototype.sendTask = function (id, lat, lon, desc) {
  if (!this.reqTopic) return;
  this.reqTopic.publish(new ROSLIB.Message({ task_id: id, lat: lat, lon: lon, description: desc || '' }));
};
SW.LiveSource.prototype.sendCommand = function (label, cmd) {
  if (!this.cmdTopic) return;
  this.cmdTopic.publish(new ROSLIB.Message({ label: label, command: cmd }));
};
