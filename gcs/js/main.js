/* Boot: pick a data source, build the scene, run the frame loop.
 *   index.html                       -> try the live swarm (rosbridge), fall back to the demo recording
 *   index.html?replay=demos/x.json   -> replay a recording
 *   index.html?live=ws://host:9090   -> live only
 */
'use strict';
var SW = window.SW || (window.SW = {});

(function () {
  var q = new URLSearchParams(location.search);

  function fetchJSON(url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error(url + ': ' + r.status); return r.json(); });
  }

  function start(source) {
    var fleet = source.fleet();
    SW.geo.setOrigin(fleet.origin[0], fleet.origin[1]);
    var store = SW.store = new SW.Store(fleet);
    source.attach(store, function () {});
    var hero = parseFloat(SW.settings.get('heroScale') || '6') || 6;
    var scene = SW.scene = new SW.Scene('globe', store, { heroScale: hero, modelUri: SW.MODEL_URI || 'assets/drone.glb' });
    var ov = SW.overlays = new SW.Overlays(scene, store);
    if (source.kind === 'replay') ov.addTruth(source.meta.victims);
    var ui = SW.ui = new SW.UI(store, scene, ov, source);
    if (!SW.settings.get('ionToken') && !window.SW_ION_TOKEN && !SW.settings.get('tokenHint')) {
      SW.settings.set('tokenHint', '1');
      setTimeout(function () {
        ui.toast('Tip: paste a free Cesium ion token in ⚙ Settings for 3D terrain, city buildings and photorealistic tiles');
      }, 4000);
    }
    if (source.kind === 'replay') source.seek(q.has('t') ? parseFloat(q.get('t')) : 0);
    scene.overview(true);
    var last = performance.now(), sinceView = 0;
    scene.viewer.scene.preRender.addEventListener(function () {
      var now = performance.now(), dt = Math.min(0.1, (now - last) / 1000);
      last = now;
      source.tick(dt);
      var rt = source.renderTime();
      scene.update(rt, dt);
      ov.update(rt);
      ui.frame(dt);
      // re-frame once the mission has spread out (first time only)
      sinceView += dt;
      if (sinceView > 6 && !SW._reframed && Object.keys(store.tasks).length) { SW._reframed = true; scene.overview(); }
    });
    if (q.has('orbit')) document.getElementById('btnOrbit').click();
  }

  function replay(url) {
    if (window.SW_EMBEDDED_RECORDING) return start(new SW.ReplaySource(window.SW_EMBEDDED_RECORDING));
    return fetchJSON(url).then(function (rec) { start(new SW.ReplaySource(rec)); });
  }

  function live(url) {
    // fleet.local.json (written by scripts/gz/up.sh for the running area) wins over the repo's fleet.json
    return fetchJSON('fleet.local.json').catch(function () { return fetchJSON('fleet.json'); }).then(function (fleet) {
      var src = new SW.LiveSource(url, fleet);
      start(src);
      return src;
    });
  }

  if (window.SW_EMBEDDED_RECORDING || q.has('replay')) { replay(q.get('replay') || 'demos/showcase.json'); return; }
  var url = q.get('live') || SW.settings.get('rosUrl') || ('ws://' + (location.hostname || 'localhost') + ':9090');
  if (q.has('live')) { live(url); return; }
  // default: probe rosbridge briefly; no swarm -> play the recorded showcase
  var probe;
  try { probe = new WebSocket(url); } catch (e) { probe = null; }
  var decided = false;
  function decide(isLive) {
    if (decided) return;
    decided = true;
    try { probe && probe.close(); } catch (e) { /* ignore */ }
    if (isLive) live(url).catch(function () { replay('demos/showcase.json'); });
    else replay('demos/showcase.json').then(function () {
      SW.ui && SW.ui.toast('No live swarm at ' + url + ' - playing the recorded showcase mission');
    });
  }
  if (probe) { probe.onopen = function () { decide(true); }; probe.onerror = function () { decide(false); }; }
  setTimeout(function () { decide(false); }, 2500);
})();
