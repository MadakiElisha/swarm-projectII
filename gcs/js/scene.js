/* 3D world: Cesium globe, imagery/terrain, drone models with physical motion. */
'use strict';
var SW = window.SW || (window.SW = {});

SW.PALETTE = ['#38bdf8', '#f472b6', '#a3e635', '#fbbf24', '#c084fc', '#34d399', '#fb7185',
              '#60a5fa', '#facc15', '#2dd4bf', '#f97316', '#e879f9'];
SW.colorOf = function (id) { return SW.PALETTE[(id - 1) % SW.PALETTE.length]; };

SW.Scene = function (container, store, opts) {
  opts = opts || {};
  this.store = store;
  // drones at TRUE size (~0.8 m survey quad); they stay visible from afar thanks to a
  // minimum on-screen size plus a coloured beacon. droneScale > 1 exaggerates them.
  this.heroScale = opts.heroScale || 1;
  this.modelScale = 1.6 * this.heroScale;
  this.modelUri = opts.modelUri || 'assets/drone.glb';
  this.layers = { links: true, packets: true, consensus: true, avoidance: true, coverage: true,
                  sensors: true, trails: true, target: true, truth: true, labels: true };
  var token = SW.settings.get('ionToken') || window.SW_ION_TOKEN || '';
  if (token) Cesium.Ion.defaultAccessToken = token;
  var imagery = new Cesium.UrlTemplateImageryProvider({
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    maximumLevel: 19, credit: new Cesium.Credit('Imagery © Esri, Maxar, Earthstar Geographics'),
  });
  // quality: 'high' (shadows, MSAA) or 'lite' (phones, weak GPUs); ?lite=1 or settings
  var q = new URLSearchParams(location.search);
  var lite = q.has('lite') || SW.settings.get('quality') === 'lite' ||
             (!SW.settings.get('quality') && (window.innerWidth < 820 || navigator.hardwareConcurrency <= 4));
  this.lite = lite;
  var v = this.viewer = new Cesium.Viewer(container, {
    baseLayer: new Cesium.ImageryLayer(imagery),
    terrainProvider: new Cesium.EllipsoidTerrainProvider(),
    animation: false, timeline: false, baseLayerPicker: false, geocoder: false, homeButton: false,
    sceneModePicker: false, navigationHelpButton: false, fullscreenButton: false, infoBox: false,
    selectionIndicator: false, shadows: !lite, shouldAnimate: false,
    requestRenderMode: false, msaaSamples: lite ? 1 : 4,
  });
  if (lite) v.resolutionScale = Math.min(1, 1.5 / (window.devicePixelRatio || 1));
  v.scene.globe.enableLighting = true;
  v.scene.globe.depthTestAgainstTerrain = false;
  v.scene.fog.enabled = true;
  v.scene.skyAtmosphere.show = true;
  v.scene.postProcessStages.fxaa.enabled = true;
  // a mid-morning sun over the operating area
  v.clock.currentTime = Cesium.JulianDate.fromIso8601('2026-10-21T09:30:00Z');
  v.shadowMap.softShadows = true;
  v.shadowMap.size = 2048;
  v.shadowMap.maximumDistance = 3000;
  v.scene.screenSpaceCameraController.minimumZoomDistance = 15;
  this.groundH = 0;
  // ground + buildings. With a Cesium ion token: real terrain and, by default, Google
  // Photorealistic 3D Tiles (the real city). Without: the area's OSM footprints coloured
  // by height (exactly what the drones plan around). Everything waits for the ground height.
  var hasArea = !!(store.fleet && store.fleet.area);
  this.buildingStyle = SW.settings.get('buildings') || (token ? 'photo' : 'height');   // photo | height | white | off
  this.token = token;
  var self0 = this;
  this.ready = (token ? this._enableTerrain(hasArea) : Promise.resolve(0)).then(function (h) {
    self0.groundH = h || 0;
    if (hasArea && (self0.buildingStyle === 'height' || self0.buildingStyle === 'white'))
      self0._buildCity(store.fleet.area);
    self0._launchSite();
  });
  this.entities = {};
  this.trails = {};
  this.follow = null;
  this.selected = null;
  this._propAngle = 0;
  this._lastT = null;
  var self = this;
  Object.keys(store.drones).forEach(function (k) { self._ensureDrone(store.drones[k]); });
  this._pick();
};

/* Colour ramp by height, low warm sand -> tall violet (matches the OSM-buildings look). */
SW.HEIGHT_RAMP = [[0, '#ece6da'], [10, '#f6d58a'], [20, '#f3a65a'], [40, '#e4643f'], [80, '#b8357f'], [150, '#5b2a86']];
SW.heightColor = function (h) {
  var r = SW.HEIGHT_RAMP, i = 0;
  while (i < r.length - 1 && h >= r[i + 1][0]) i++;
  if (i === r.length - 1) return Cesium.Color.fromCssColorString(r[i][1]);
  var a = Cesium.Color.fromCssColorString(r[i][1]), b = Cesium.Color.fromCssColorString(r[i + 1][1]);
  return Cesium.Color.lerp(a, b, (h - r[i][0]) / (r[i + 1][0] - r[i][0]), new Cesium.Color());
};

SW.Scene.prototype._buildCity = function (area) {
  var v = this.viewer, white = this.buildingStyle === 'white', self = this;
  function ring(flat) {
    var out = [];
    for (var k = 0; k + 1 < flat.length; k += 2) {
      var ll = SW.geo.toLatLon(flat[k], flat[k + 1]);
      out.push(ll[1], ll[0]);
    }
    return Cesium.Cartesian3.fromDegreesArray(out);
  }
  var inst = [];
  (area.b || []).forEach(function (b, i) {
    var h = b[0], base = b[1] || 0;
    var col = white ? Cesium.Color.fromCssColorString('#f4f4f2') : SW.heightColor(h);
    try {
      inst.push(new Cesium.GeometryInstance({
        id: 'bldg' + i,
        geometry: new Cesium.PolygonGeometry({
          polygonHierarchy: new Cesium.PolygonHierarchy(ring(b[2])),
          height: self.groundH + base, extrudedHeight: self.groundH + h,
          vertexFormat: Cesium.PerInstanceColorAppearance.VERTEX_FORMAT,
        }),
        attributes: { color: Cesium.ColorGeometryInstanceAttribute.fromColor(col) },
      }));
    } catch (e) { /* degenerate footprint */ }
  });
  this.cityPrims = [];
  if (inst.length) {
    this.city = v.scene.primitives.add(new Cesium.Primitive({
      geometryInstances: inst, shadows: this.lite ? Cesium.ShadowMode.DISABLED : Cesium.ShadowMode.ENABLED,
      appearance: new Cesium.PerInstanceColorAppearance({ translucent: false, closed: true, flat: false }),
      asynchronous: true,
    }));
    this.cityPrims.push(this.city);
  }
  var water = (area.w || []).map(function (w) {
    return new Cesium.GeometryInstance({
      geometry: new Cesium.PolygonGeometry({ polygonHierarchy: new Cesium.PolygonHierarchy(ring(w)),
                                             height: self.groundH + 0.2 }),
      attributes: { color: Cesium.ColorGeometryInstanceAttribute.fromColor(
        Cesium.Color.fromCssColorString('#1d4ed8').withAlpha(0.35)) },
    });
  });
  if (water.length) {
    this.cityPrims.push(v.scene.primitives.add(new Cesium.Primitive({
      geometryInstances: water, appearance: new Cesium.PerInstanceColorAppearance({ translucent: true, flat: true }),
    })));
  }
};

/* -> Promise(ground ellipsoid height at the origin). Sets up terrain / 3D tiles. */
SW.Scene.prototype._enableTerrain = function (haveArea) {
  var v = this.viewer, style = this.buildingStyle, o = SW.geo.origin();
  var ground = Cesium.createWorldTerrainAsync().then(function (tp) {
    if (style !== 'photo') {
      v.scene.terrainProvider = tp;
      v.scene.globe.depthTestAgainstTerrain = true;
    }
    return Cesium.sampleTerrainMostDetailed(tp, [Cesium.Cartographic.fromDegrees(o[1], o[0])]);
  }).then(function (r) { return (r[0] && r[0].height) || 0; })
    .catch(function (e) { console.warn('terrain unavailable', e); return 0; });
  if (style === 'photo') {                     // Google Photorealistic 3D Tiles via ion: the real city
    var site = this._siteCentre();
    return Cesium.createGooglePhotorealistic3DTileset().then(function (t) {
      v.scene.primitives.add(t);
      v.scene.globe.show = false;
      // the ground in the 3D tiles at the launch site is what pads and drones must sit on
      return v.scene.sampleHeightMostDetailed([Cesium.Cartographic.fromDegrees(site[1], site[0])]);
    }).then(function (r) {
      var h = r && r[0] && r[0].height;
      return (h === undefined || h === null || !isFinite(h)) ? ground : h;
    }).catch(function (e) { console.warn('photorealistic tiles unavailable', e); v.scene.globe.show = true; return ground; });
  } else if (!haveArea && style !== 'off') {   // no OSM area of our own: Cesium OSM Buildings everywhere
    Cesium.createOsmBuildingsAsync().then(function (b) {
      var hexpr = "(${feature['cesium#estimatedHeight']} === undefined ? 10 : Number(${feature['cesium#estimatedHeight']}))";
      var conds = style === 'white' ? [['true', "color('#f4f4f2')"]] :
        SW.HEIGHT_RAMP.slice().reverse().map(function (r) { return [hexpr + ' >= ' + r[0], "color('" + r[1] + "')"]; });
      b.style = new Cesium.Cesium3DTileStyle({ color: { conditions: conds } });
      v.scene.primitives.add(b);
    }).catch(function (e) { console.warn('OSM buildings unavailable', e); });
  }
  return ground;
};

SW.Scene.prototype._siteCentre = function () {
  var s = this.store, la = 0, lo = 0, n = 0;
  Object.keys(s.drones).forEach(function (k) { var h = s.drones[k].home; if (h) { la += h[0]; lo += h[1]; n++; } });
  return n ? [la / n, lo / n] : SW.geo.origin();
};

/* Launch site: a concrete apron with one marked helipad per drone (pads draped on
   terrain / 3D tiles), so the swarm visibly takes off from and lands on its base. */
SW.padTexture = function (label, css) {
  var c = document.createElement('canvas'); c.width = c.height = 256;
  var g = c.getContext('2d');
  g.fillStyle = '#3b3f45'; g.fillRect(0, 0, 256, 256);
  g.strokeStyle = '#f5c518'; g.lineWidth = 10; g.strokeRect(8, 8, 240, 240);
  g.strokeStyle = '#f1f1f1'; g.lineWidth = 9; g.beginPath(); g.arc(128, 128, 92, 0, 2 * Math.PI); g.stroke();
  g.fillStyle = '#f1f1f1'; g.font = 'bold 120px Inter, Arial, sans-serif'; g.textAlign = 'center';
  g.textBaseline = 'middle'; g.fillText('H', 128, 132);
  g.fillStyle = css; g.font = 'bold 34px Inter, Arial, sans-serif'; g.fillText(label, 210, 36);
  return c;
};

SW.Scene.prototype._launchSite = function () {
  var v = this.viewer, self = this, pads = [];
  Object.keys(this.store.drones).forEach(function (k) {
    var d = self.store.drones[k];
    if (d.home) pads.push({ d: d, e: SW.geo.toEnu(d.home[0], d.home[1]) });
  });
  if (!pads.length) return;
  var xs = pads.map(function (p) { return p.e[0]; }), ys = pads.map(function (p) { return p.e[1]; });
  var x0 = Math.min.apply(null, xs) - 12, x1 = Math.max.apply(null, xs) + 12;
  var y0 = Math.min.apply(null, ys) - 12, y1 = Math.max.apply(null, ys) + 12;
  var corners = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]].map(function (p) {
    var ll = SW.geo.toLatLon(p[0], p[1]); return Cesium.Cartesian3.fromDegrees(ll[1], ll[0]);
  });
  v.entities.add({ polygon: { hierarchy: corners, material: Cesium.Color.fromCssColorString('#8d8f8a'),
                              height: this.groundH + 0.03 } });
  var c = SW.geo.toLatLon((x0 + x1) / 2, y1 + 4);
  this.siteLabel = v.entities.add({ position: Cesium.Cartesian3.fromDegrees(c[1], c[0], this.groundH + 3),
    label: { text: 'LAUNCH SITE', font: '700 13px Inter, system-ui, sans-serif', fillColor: Cesium.Color.WHITE,
             outlineColor: Cesium.Color.fromCssColorString('#020617'), outlineWidth: 3,
             style: Cesium.LabelStyle.FILL_AND_OUTLINE, disableDepthTestDistance: Number.POSITIVE_INFINITY,
             distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 6000) } });
  pads.forEach(function (p) {
    var h = 3.5, a = SW.geo.toLatLon(p.e[0] - h, p.e[1] - h), b = SW.geo.toLatLon(p.e[0] + h, p.e[1] + h);
    v.entities.add({ rectangle: {
      coordinates: Cesium.Rectangle.fromDegrees(a[1], a[0], b[1], b[0]),
      material: new Cesium.ImageMaterialProperty({ image: SW.padTexture(p.d.label, SW.colorOf(p.d.id)) }),
      height: self.groundH + 0.06 } });
  });
};

SW.Scene.prototype.pos = function (lat, lon, alt) {
  return Cesium.Cartesian3.fromDegrees(lon, lat, this.groundH + alt);
};

SW.Scene.prototype._ensureDrone = function (d) {
  if (this.entities[d.id]) return this.entities[d.id];
  var self = this, v = this.viewer, color = Cesium.Color.fromCssColorString(SW.colorOf(d.id));
  var st = { s: null, pos: undefined, q: Cesium.Quaternion.IDENTITY, props: [] };
  for (var k = 0; k < 4; k++) st.props.push(Cesium.Quaternion.IDENTITY);
  var nodes = {};
  [1, 2, 3, 4].forEach(function (k) {
    nodes['prop_' + k] = new Cesium.NodeTransformationProperty({
      rotation: new Cesium.CallbackProperty(function () { return st.props[k - 1]; }, false) });
  });
  var e = v.entities.add({
    id: 'drone-' + d.id,
    position: new Cesium.CallbackProperty(function () { return st.pos; }, false),
    orientation: new Cesium.CallbackProperty(function () { return st.q; }, false),
    model: {
      uri: this.modelUri, scale: this.modelScale, minimumPixelSize: 56, maximumScale: 4000,
      shadows: self.lite ? Cesium.ShadowMode.DISABLED : Cesium.ShadowMode.ENABLED, nodeTransformations: nodes,
      silhouetteColor: color, silhouetteSize: new Cesium.CallbackProperty(function () {
        return self.selected === d.id ? 2.5 : 1.0; }, false),
      color: new Cesium.CallbackProperty(function () {
        return st.s && !st.alive ? Cesium.Color.DIMGRAY : Cesium.Color.WHITE; }, false),
      colorBlendMode: Cesium.ColorBlendMode.MIX, colorBlendAmount: 0.15,
    },
    label: {
      text: new Cesium.CallbackProperty(function () { return st.label || d.label; }, false),
      font: '600 13px Inter, system-ui, sans-serif', fillColor: color,
      outlineColor: Cesium.Color.fromCssColorString('#020617'), outlineWidth: 3,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE, pixelOffset: new Cesium.Cartesian2(0, -34),
      show: new Cesium.CallbackProperty(function () { return self.layers.labels && !!st.s; }, false),
      distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 9000),
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
  });
  // beacon: a coloured ring that keeps every drone findable from far away
  v.entities.add({
    position: new Cesium.CallbackProperty(function () { return st.pos; }, false),
    billboard: { image: SW.beacon(SW.colorOf(d.id)), scale: 0.5, disableDepthTestDistance: Number.POSITIVE_INFINITY,
                 distanceDisplayCondition: new Cesium.DistanceDisplayCondition(450, 1e7),
                 show: new Cesium.CallbackProperty(function () { return !!st.s; }, false) },
  });
  // drop line + ground ring: makes altitude readable
  v.entities.add({
    polyline: {
      positions: new Cesium.CallbackProperty(function () {
        if (!st.s || !st.pos) return [];
        return [st.pos, self.pos(st.s.lat, st.s.lon, 0)];
      }, false),
      width: 1, material: color.withAlpha(0.45),
    },
  });
  v.entities.add({
    position: new Cesium.CallbackProperty(function () { return st.s ? self.pos(st.s.lat, st.s.lon, 0.2) : undefined; }, false),
    ellipse: { semiMajorAxis: 4, semiMinorAxis: 4, material: color.withAlpha(0.35),
               height: new Cesium.CallbackProperty(function () { return self.groundH + 0.3; }, false) },
  });
  // trail
  var trail = this.trails[d.id] = [];
  v.entities.add({
    polyline: {
      positions: new Cesium.CallbackProperty(function () { return trail.length > 1 ? trail : []; }, false),
      width: 3,
      material: new Cesium.PolylineGlowMaterialProperty({ glowPower: 0.25, color: color.withAlpha(0.8) }),
      show: new Cesium.CallbackProperty(function () { return self.layers.trails; }, false),
    },
  });
  this.entities[d.id] = { e: e, st: st, color: color };
  return this.entities[d.id];
};

SW.beacon = function (css) {
  var c = document.createElement('canvas'); c.width = c.height = 64;
  var g = c.getContext('2d');
  g.strokeStyle = css; g.lineWidth = 6; g.beginPath(); g.arc(32, 32, 24, 0, 2 * Math.PI); g.stroke();
  g.fillStyle = css; g.beginPath(); g.arc(32, 32, 7, 0, 2 * Math.PI); g.fill();
  g.strokeStyle = 'rgba(2,6,23,.8)'; g.lineWidth = 2; g.beginPath(); g.arc(32, 32, 28, 0, 2 * Math.PI); g.stroke();
  return c;
};

SW.Scene.prototype._pick = function () {
  var self = this, h = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);
  h.setInputAction(function (ev) {
    var p = self.viewer.scene.pick(ev.position);
    if (p && p.id && typeof p.id.id === 'string' && p.id.id.indexOf('drone-') === 0) {
      self.select(parseInt(p.id.id.slice(6), 10));
      return;
    }
    if (self.onGroundClick) {
      var c = self.viewer.camera.pickEllipsoid(ev.position);
      if (c) {
        var g = Cesium.Cartographic.fromCartesian(c);
        self.onGroundClick(Cesium.Math.toDegrees(g.latitude), Cesium.Math.toDegrees(g.longitude), ev.position);
      }
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
  h.setInputAction(function (ev) {
    var p = self.viewer.scene.pick(ev.position);
    if (p && p.id && typeof p.id.id === 'string' && p.id.id.indexOf('drone-') === 0)
      self.followDrone(parseInt(p.id.id.slice(6), 10));
  }, Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
};

SW.Scene.prototype.select = function (id) {
  this.selected = id;
  if (this.onSelect) this.onSelect(id);
};

SW.Scene.prototype.followDrone = function (id) {
  this.select(id);
  var ent = this.entities[id];
  if (!ent) return;
  this.viewer.trackedEntity = ent.e;
  var k = Math.max(1, this.heroScale);
  ent.e.viewFrom = new Cesium.Cartesian3(-9 * k, -9 * k, 4 * k);       // close chase camera
  this.follow = id;
};

SW.Scene.prototype.unfollow = function () { this.viewer.trackedEntity = undefined; this.follow = null; };

SW.Scene.prototype.overview = function (instant) {
  this.unfollow();
  var pts = [];
  var s = this.store;
  Object.keys(s.drones).forEach(function (k) {
    var d = s.drones[k], l = d.track.last();
    if (l) pts.push([l.lat, l.lon]); else if (d.home) pts.push(d.home);
  });
  Object.keys(s.tasks).forEach(function (k) {
    var tk = s.tasks[k];
    pts.push(SW.geo.toLatLon(tk.x, tk.y));
    if (tk.ar) { pts.push(SW.geo.toLatLon(tk.ar[0], tk.ar[1])); pts.push(SW.geo.toLatLon(tk.ar[2], tk.ar[3])); }
  });
  if (!pts.length) pts.push(SW.geo.origin());
  var lat = 0, lon = 0, n = pts.length, r = 300;
  pts.forEach(function (p) { lat += p[0]; lon += p[1]; });
  lat /= n; lon /= n;
  pts.forEach(function (p) {
    var e = SW.geo.toEnu(p[0], p[1]), c = SW.geo.toEnu(lat, lon);
    r = Math.max(r, Math.hypot(e[0] - c[0], e[1] - c[1]));
  });
  var narrow = window.innerWidth < 820;
  if (narrow) {         // phones: panels cover the bottom, so aim a little south of the action
    var c0 = SW.geo.toEnu(lat, lon), ll2 = SW.geo.toLatLon(c0[0], c0[1] - r * 0.45);
    lat = ll2[0]; lon = ll2[1];
  }
  var target = Cesium.Cartesian3.fromDegrees(lon, lat, this.groundH);
  var range = Math.max(900, r * (narrow ? 3.6 : 2.6));
  var off = new Cesium.HeadingPitchRange(Cesium.Math.toRadians(20), Cesium.Math.toRadians(narrow ? -58 : -38), range);
  if (instant) this.viewer.camera.lookAt(target, off);
  else this.viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(target, r * 1.1),
                                              { offset: off, duration: 1.6 });
  this.viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
};

/* Per-frame update: interpolated pose, physical attitude, props, trails. */
SW.Scene.prototype.update = function (t, wallDt) {
  var self = this, s = this.store;
  this._propAngle += wallDt;
  Object.keys(s.drones).forEach(function (k) {
    var d = s.drones[k], ent = self._ensureDrone(d), st = ent.st;
    var smp = d.track.at(t);
    if (!smp || smp.t > t + 5) { st.s = null; st.pos = undefined; return; }
    st.alive = s.alive(d, t);
    var last = d.track.last();
    if (last && last.alive === 0 && t >= last.t) {       // lost: fall and tumble, then lie on the ground
      var fall = t - last.t;
      smp = Object.assign({}, last, { alt: Math.max(0, last.alt - 4.9 * fall * fall),
                                      roll: Math.min(1.4, fall * 1.6), pitch: Math.min(0.6, fall * 0.7),
                                      vx: 0, vy: 0 });
    }
    st.s = smp;
    st.pos = self.pos(smp.lat, smp.lon, Math.max(0.24 * self.modelScale, smp.alt + 0.24 * self.modelScale));
    // heading: Cesium = clockwise from north; swarm yaw_enu = CCW from east
    var heading = Math.PI / 2 - smp.yaw;
    var hpr = new Cesium.HeadingPitchRoll(heading, -smp.pitch, smp.roll);
    st.q = Cesium.Transforms.headingPitchRollQuaternion(st.pos, hpr);
    // props: idle on the ground, faster with climb and speed
    var air = smp.alt > 0.6 && st.alive;
    var rate = air ? 55 + 2.5 * Math.hypot(smp.vx, smp.vy) : (smp.fsm === 'TAKEOFF' ? 30 : 0);
    var base = self._propAngle * rate;
    for (var i = 0; i < 4; i++) {
      var dir = (i % 2 === 0) ? 1 : -1;
      st.props[i] = Cesium.Quaternion.fromAxisAngle(Cesium.Cartesian3.UNIT_Y, dir * base + i);
    }
    var b = d.brain;
    st.label = !st.alive ? d.label + ' · LOST' :
      (self.selected === d.id ? d.label + (b && b.ph ? ' · ' + b.ph : '') + (b && b.tk ? ' · ' + b.tk : '') : d.label);
    // trail: one point every 0.5 s of mission time, last ~90 s
    var tr = self.trails[d.id];
    if (!st._lt || t < st._lt || t - st._lt >= 0.5) {
      if (st._lt && t < st._lt) tr.length = 0;          // scrubbed backwards
      st._lt = t;
      if (air) tr.push(st.pos);
      if (tr.length > 180) tr.shift();
    }
  });
};
