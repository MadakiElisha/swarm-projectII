/* 3D world: Cesium globe, imagery/terrain, drone models with physical motion. */
'use strict';
var SW = window.SW || (window.SW = {});

SW.PALETTE = ['#38bdf8', '#f472b6', '#a3e635', '#fbbf24', '#c084fc', '#34d399', '#fb7185',
              '#60a5fa', '#facc15', '#2dd4bf', '#f97316', '#e879f9'];
SW.colorOf = function (id) { return SW.PALETTE[(id - 1) % SW.PALETTE.length]; };

SW.Scene = function (container, store, opts) {
  opts = opts || {};
  this.store = store;
  this.heroScale = opts.heroScale || 6;            // drones drawn larger than life for visibility
  this.modelUri = opts.modelUri || 'assets/drone.glb';
  this.layers = { links: true, packets: true, consensus: true, avoidance: true, coverage: true,
                  sensors: true, trails: true, target: true, truth: false, labels: true };
  var token = SW.settings.get('ionToken');
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
  // buildings: the operating area's own OSM footprints (exactly what the drones plan
  // around - no token needed); with a token also terrain + Cesium OSM Buildings, or
  // Google Photorealistic 3D Tiles
  this.buildingStyle = SW.settings.get('buildings') || 'height';     // height | white | photo | off
  if (token) this._enableTerrain(!!(store.fleet && store.fleet.area));
  if (store.fleet && store.fleet.area && this.buildingStyle !== 'off' && this.buildingStyle !== 'photo')
    this._buildCity(store.fleet.area);
  this.entities = {};
  this.trails = {};
  this.follow = null;
  this.selected = null;
  this._propAngle = 0;
  this._lastT = null;
  var self = this;
  Object.keys(store.drones).forEach(function (k) { self._ensureDrone(store.drones[k]); });
  this._homePads();
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
          height: base, extrudedHeight: h,
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
                                             height: 0.2 }),
      attributes: { color: Cesium.ColorGeometryInstanceAttribute.fromColor(
        Cesium.Color.fromCssColorString('#1d4ed8').withAlpha(0.35)) },
    });
  });
  if (water.length) {
    this.cityPrims.push(v.scene.primitives.add(new Cesium.Primitive({
      geometryInstances: water, appearance: new Cesium.PerInstanceColorAppearance({ translucent: true, flat: true }),
    })));
  }
  this._liftCity();
};

/* Footprints are built at ellipsoid height 0; lift them onto the sampled terrain. */
SW.Scene.prototype._liftCity = function () {
  if (!this.cityPrims || !this.cityPrims.length) return;
  var o = SW.geo.origin();
  var up = Cesium.Ellipsoid.WGS84.geodeticSurfaceNormal(Cesium.Cartesian3.fromDegrees(o[1], o[0]), new Cesium.Cartesian3());
  var m = Cesium.Matrix4.fromTranslation(Cesium.Cartesian3.multiplyByScalar(up, this.groundH, up));
  this.cityPrims.forEach(function (p) { p.modelMatrix = m; });
};

SW.Scene.prototype._enableTerrain = function (haveArea) {
  var v = this.viewer, self = this, style = this.buildingStyle;
  try {
    if (style === 'photo') {                                 // Google Photorealistic 3D Tiles via ion
      v.scene.globe.show = false;
      Cesium.createGooglePhotorealistic3DTileset().then(function (t) { v.scene.primitives.add(t); })
        .catch(function (e) { console.warn('photorealistic tiles unavailable', e); v.scene.globe.show = true; });
      return;
    }
    v.scene.setTerrain(Cesium.Terrain.fromWorldTerrain());
    v.scene.globe.depthTestAgainstTerrain = true;
    // the area's own footprints are drawn when present (same data the drones plan with);
    // otherwise show Cesium OSM Buildings everywhere, styled the same way
    if (!haveArea && style !== 'off') {
      Cesium.createOsmBuildingsAsync().then(function (b) {
        var hexpr = "(${feature['cesium#estimatedHeight']} === undefined ? 10 : Number(${feature['cesium#estimatedHeight']}))";
        var conds = style === 'white' ? [['true', "color('#f4f4f2')"]] :
          SW.HEIGHT_RAMP.slice().reverse().map(function (r) { return [hexpr + ' >= ' + r[0], "color('" + r[1] + "')"]; });
        b.style = new Cesium.Cesium3DTileStyle({ color: { conditions: conds } });
        v.scene.primitives.add(b);
      });
    }
    var o = SW.geo.origin();
    Cesium.Terrain && Cesium.sampleTerrainMostDetailed && v.scene.terrainProvider &&
      setTimeout(function () {
        Cesium.sampleTerrainMostDetailed(v.scene.terrainProvider,
          [Cesium.Cartographic.fromDegrees(o[1], o[0])]).then(function (r) {
          self.groundH = (r[0] && r[0].height) || 0;
          self._liftCity();
        }).catch(function () {});
      }, 3000);
  } catch (e) { console.warn('terrain unavailable', e); }
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
      uri: this.modelUri, scale: this.heroScale, minimumPixelSize: 34, maximumScale: 400,
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
    ellipse: { semiMajorAxis: 4, semiMinorAxis: 4, material: color.withAlpha(0.35), height: 0.2 },
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

SW.Scene.prototype._homePads = function () {
  var v = this.viewer, self = this;
  Object.keys(this.store.drones).forEach(function (k) {
    var d = self.store.drones[k];
    if (!d.home) return;
    v.entities.add({
      position: self.pos(d.home[0], d.home[1], 0.1),
      ellipse: { semiMajorAxis: 5, semiMinorAxis: 5, material: Cesium.Color.WHITE.withAlpha(0.12),
                 outline: true, outlineColor: Cesium.Color.WHITE.withAlpha(0.5), height: 0.1 },
    });
  });
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
  var k = this.heroScale / 6;
  ent.e.viewFrom = new Cesium.Cartesian3(-22 * k, -22 * k, 9 * k);     // close chase camera
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
    st.pos = self.pos(smp.lat, smp.lon, Math.max(0.15 * self.heroScale, smp.alt));
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
