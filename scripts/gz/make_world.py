#!/usr/bin/env python3
"""Build a Gazebo Harmonic world from the operating area + fleet (real ArduPilot physics).

    SWARM_FLEET=areas/eko/fleet.yaml python3 scripts/gz/make_world.py
    python3 scripts/gz/make_world.py --fleet areas/eko/fleet.yaml --victims 6 --flood 0.6

Output (default sim/gz/<area>/):
  worlds/swarm.sdf             world: sun, ground, OSM buildings/water/roads, flood plane,
                               survivors, parked cars, the moving target, one drone per fleet entry
  models/swarm_drone_<N>/      ArduPilot's own iris_with_ardupilot with fdm_port_in = 9002 + 10*N
                               and a nadir camera publishing /swarm/D<N>/camera/image
  models/city_*/               extruded meshes (OBJ)
  env.sh                       GZ_SIM_RESOURCE_PATH / GZ_SIM_SYSTEM_PLUGIN_PATH
  world.json                   spawn poses, survivors, target start (for scripts and the GCS)

Every drone's SITL must use the world origin as --home (SITL adds Gazebo's
position to its home); scripts/gz/run_swarm.sh does that.
"""
import argparse
import json
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "ros2_ws", "src", "swarm_common"))

from swarm_common.area import height_grid, point_in_poly, synthetic_city  # noqa: E402
from swarm_common.config import load_fleet  # noqa: E402

FUEL = "https://fuel.gazebosim.org/1.0/OpenRobotics/models/"
PEOPLE = ["Rescue Randy", "Casual female", "Standing person"]
CARS = ["Hatchback blue", "Hatchback red", "SUV", "Pickup"]


# ------------------------------------------------------------------ meshes
def _mesh_buildings(area, out_dir, chunk=400):
    import trimesh
    from shapely.geometry import Polygon
    paths = []
    blds = area["buildings"]
    for c in range(0, len(blds), chunk):
        parts = []
        for b in blds[c:c + chunk]:
            try:
                poly = Polygon(b["poly"])
                if not poly.is_valid:
                    poly = poly.buffer(0)
                if poly.is_empty or poly.area < 4:
                    continue
                polys = list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]
                for p in polys:
                    m = trimesh.creation.extrude_polygon(p, max(2.0, b["h"] - b.get("base", 0.0)))
                    if b.get("base"):
                        m.apply_translation([0, 0, b["base"]])
                    parts.append(m)
            except Exception:
                continue
        if parts:
            name = f"buildings_{c // chunk}.obj"
            trimesh.util.concatenate(parts).export(os.path.join(out_dir, name))
            paths.append(name)
    return paths


def _mesh_flat(polys, out_dir, name, z=0.02, thickness=0.05):
    import trimesh
    from shapely.geometry import Polygon
    parts = []
    for pts in polys:
        try:
            p = Polygon(pts)
            if not p.is_valid:
                p = p.buffer(0)
            if p.is_empty:
                continue
            for q in (list(p.geoms) if p.geom_type == "MultiPolygon" else [p]):
                m = trimesh.creation.extrude_polygon(q, thickness)
                m.apply_translation([0, 0, z])
                parts.append(m)
        except Exception:
            continue
    if not parts:
        return None
    trimesh.util.concatenate(parts).export(os.path.join(out_dir, name))
    return name


def _road_polys(area):
    from shapely.geometry import LineString
    out = []
    for r in area.get("roads", []):
        try:
            g = LineString(r["line"]).buffer(r["w"] / 2.0, cap_style=2)
            for q in (list(g.geoms) if g.geom_type == "MultiPolygon" else [g]):
                out.append(list(q.exterior.coords)[:-1])
        except Exception:
            continue
    return out


def _building_boxes(area):
    """One oriented box collider per building (DART crashes on large collision meshes)."""
    from shapely.geometry import Polygon
    out = []
    for b in area["buildings"]:
        try:
            r = Polygon(b["poly"]).minimum_rotated_rectangle
            c = list(r.exterior.coords)[:4]
            (x0, y0), (x1, y1), (x2, y2) = c[0], c[1], c[2]
            L, W = math.hypot(x1 - x0, y1 - y0), math.hypot(x2 - x1, y2 - y1)
            if L < 1 or W < 1:
                continue
            yaw = math.atan2(y1 - y0, x1 - x0)
            cx, cy = r.centroid.x, r.centroid.y
            base = b.get("base", 0.0)
            h = max(2.0, b["h"] - base)
            out.append((cx, cy, base + h / 2, yaw, L, W, h))
        except Exception:
            continue
    return out


def _static_model(models_dir, name, meshes, rgba, collide=True, transparency=0.0, boxes=None):
    d = os.path.join(models_dir, name)
    os.makedirs(os.path.join(d, "meshes"), exist_ok=True)
    links = []
    for k, m in enumerate(meshes):
        uri = f"model://{name}/meshes/{m}"
        col = (f"<collision name='c{k}'><geometry><mesh><uri>{uri}</uri></mesh></geometry></collision>"
               if collide else "")
        shadows = str(collide or bool(boxes)).lower()
        links.append(f"""
      <visual name='v{k}'><geometry><mesh><uri>{uri}</uri></mesh></geometry>
        <material><ambient>{rgba}</ambient><diffuse>{rgba}</diffuse><specular>0.1 0.1 0.1 1</specular></material>
        <transparency>{transparency}</transparency><cast_shadows>{shadows}</cast_shadows></visual>{col}""")
    for k, (cx, cy, cz, yaw, L, W, H) in enumerate(boxes or []):
        links.append(f"""
      <collision name='box{k}'><pose>{cx:.2f} {cy:.2f} {cz:.2f} 0 0 {yaw:.4f}</pose>
        <geometry><box><size>{L:.2f} {W:.2f} {H:.2f}</size></box></geometry></collision>""")
    with open(os.path.join(d, "model.sdf"), "w") as f:
        f.write(f"""<?xml version="1.0"?>
<sdf version="1.9"><model name="{name}"><static>true</static>
  <link name="link">{''.join(links)}
  </link></model></sdf>
""")
    with open(os.path.join(d, "model.config"), "w") as f:
        f.write(f"<?xml version='1.0'?><model><name>{name}</name><version>1.0</version>"
                f"<sdf version='1.9'>model.sdf</sdf></model>\n")
    return d


# ------------------------------------------------------------------ drones
CAMERA_SDF = """
    <!-- swarm: nadir camera for perception (top of image = nose) -->
    <link name="swarm_camera_link">
      <pose relative_to="iris_with_standoffs::base_link">0.12 0 -0.09 0 1.5708 0</pose>
      <inertial><mass>0.01</mass><inertia><ixx>1e-6</ixx><iyy>1e-6</iyy><izz>1e-6</izz></inertia></inertial>
      <sensor name="swarm_camera" type="camera">
        <camera>
          <horizontal_fov>{hfov}</horizontal_fov>
          <image><width>{w}</width><height>{h}</height><format>R8G8B8</format></image>
          <clip><near>0.2</near><far>800</far></clip>
        </camera>
        <always_on>1</always_on><update_rate>{fps}</update_rate><visualize>false</visualize>
        <topic>/swarm/{label}/camera/image</topic>
      </sensor>
    </link>
    <joint name="swarm_camera_joint" type="fixed">
      <parent>iris_with_standoffs::base_link</parent><child>swarm_camera_link</child>
    </joint>
"""


def _drone_model(models_dir, apgz_models, drone_id, label, camera):
    src = os.path.join(apgz_models, "iris_with_ardupilot", "model.sdf")
    with open(src) as f:
        sdf = f.read()
    port = 9002 + 10 * drone_id
    name = f"swarm_drone_{drone_id}"
    sdf, n1 = re.subn(r'<model name="iris_with_ardupilot">', f'<model name="{name}">', sdf, count=1)
    sdf, n2 = re.subn(r"<fdm_port_in>\s*\d+\s*</fdm_port_in>", f"<fdm_port_in>{port}</fdm_port_in>", sdf)
    if not (n1 and n2):
        raise RuntimeError(f"{src}: unexpected format (model name / fdm_port_in not found)")
    if camera:
        cam = CAMERA_SDF.format(label=label, **camera)
        i = sdf.rindex("</model>")
        sdf = sdf[:i] + cam + sdf[i:]
    d = os.path.join(models_dir, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "model.sdf"), "w") as f:
        f.write(sdf)
    with open(os.path.join(d, "model.config"), "w") as f:
        f.write(f"<?xml version='1.0'?><model><name>{name}</name><version>1.0</version>"
                f"<sdf version='1.9'>model.sdf</sdf></model>\n")
    return name, port


# ------------------------------------------------------------------ places
def _open_points(area, n, rnd, avoid, min_sep=40.0, margin=0.15):
    """Random street-level points: outside buildings and water, inside the area."""
    g = height_grid(area, cell=5.0, margin=0.0, dilate=False)
    xs = [p[0] for b in area["buildings"] for p in b["poly"]] or [-500, 500]
    ys = [p[1] for b in area["buildings"] for p in b["poly"]] or [-500, 500]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    dx, dy = (x1 - x0) * margin, (y1 - y0) * margin
    pts, tries = [], 0
    while len(pts) < n and tries < 20000:
        tries += 1
        x, y = rnd.uniform(x0 + dx, x1 - dx), rnd.uniform(y0 + dy, y1 - dy)
        if g.height_at(x, y) > 0 or g.is_water(x, y):
            continue
        if any(math.hypot(x - a, y - b) < min_sep for a, b in pts + avoid):
            continue
        if any(point_in_poly(x, y, w["poly"]) for w in area.get("water", [])):
            continue
        pts.append((round(x, 1), round(y, 1)))
    return pts


def _include(uri, name, x, y, z=0.0, yaw=0.0, static=True):
    return (f"\n    <include><uri>{uri}</uri><name>{name}</name><pose>{x:.2f} {y:.2f} {z:.2f} 0 0 {yaw:.3f}</pose>"
            f"<static>{str(static).lower()}</static></include>")


def _person_or_car(kind, name, x, y, yaw, fuel, rnd):
    if fuel:
        model = rnd.choice(PEOPLE if kind == "person" else CARS)
        return _include(FUEL + model.replace(" ", "%20"), name, x, y, 0.0, yaw)
    if kind == "person":                         # offline stand-in: a primitive body
        geom = ("<geometry><cylinder><radius>0.25</radius><length>1.7</length></cylinder></geometry>",
                "0.85", "0.9 0.4 0.1 1")
    else:
        geom = ("<geometry><box><size>4.2 1.8 1.5</size></box></geometry>", "0.75", "0.2 0.3 0.8 1")
    return f"""
    <model name="{name}"><static>true</static><pose>{x:.2f} {y:.2f} {geom[1]} 0 0 {yaw:.3f}</pose>
      <link name="l"><visual name="v">{geom[0]}<material><diffuse>{geom[2]}</diffuse></material></visual>
      <collision name="c">{geom[0]}</collision></link></model>"""


# ------------------------------------------------------------------- world
def build(args):
    fleet = load_fleet(args.fleet)
    area = fleet.area
    if area is None:
        if not args.synthetic:
            sys.exit("fleet has no area_file - create one with scripts/make_area.py (or pass --synthetic)")
        area = synthetic_city(blocks=6)
    o = fleet.swarm.origin
    out = os.path.abspath(args.out or os.path.join(ROOT, "sim", "gz", area.get("name", "area")))
    models, worlds = os.path.join(out, "models"), os.path.join(out, "worlds")
    os.makedirs(models, exist_ok=True)
    os.makedirs(worlds, exist_ok=True)
    rnd = random.Random(args.seed)

    # --- city meshes
    bdir = os.path.join(models, "city_buildings", "meshes")
    os.makedirs(bdir, exist_ok=True)
    bmeshes = _mesh_buildings(area, bdir)
    _static_model(models, "city_buildings", bmeshes, "0.78 0.77 0.74 1", collide=False,
                  boxes=_building_boxes(area))
    parts = ["city_buildings"]
    wdir = os.path.join(models, "city_water", "meshes")
    os.makedirs(wdir, exist_ok=True)
    wm = _mesh_flat([w["poly"] for w in area.get("water", [])], wdir, "water.obj", z=0.01)
    if wm:
        _static_model(models, "city_water", [wm], "0.10 0.35 0.55 1", collide=False)
        parts.append("city_water")
    rdir = os.path.join(models, "city_roads", "meshes")
    os.makedirs(rdir, exist_ok=True)
    rm = _mesh_flat(_road_polys(area), rdir, "roads.obj", z=0.03)
    if rm:
        _static_model(models, "city_roads", [rm], "0.16 0.16 0.17 1", collide=False)
        parts.append("city_roads")

    # --- drones
    apgz = os.path.abspath(os.path.expanduser(args.ardupilot_gazebo))
    camera = None if args.no_camera else {"w": args.cam_w, "h": args.cam_h, "fps": args.cam_fps,
                                          "hfov": round(math.radians(fleet.swarm.perception.hfov_deg), 4)}
    drones, spawns = "", []
    for d in fleet.drones:
        name, port = _drone_model(models, os.path.join(apgz, "models"), d.id, d.label, camera)
        x, y = o.to_enu(d.home_lat, d.home_lon)
        spawns.append({"id": d.id, "label": d.label, "model": name, "x": round(x, 2), "y": round(y, 2),
                       "fdm_port": port})
        drones += f"\n    <include><uri>model://{name}</uri><name>{d.label}</name>" \
                  f"<pose degrees='true'>{x:.2f} {y:.2f} 0.195 0 0 90</pose></include>"

    # --- people, cars, the moving target
    avoid = [(s["x"], s["y"]) for s in spawns]
    victims = _open_points(area, args.victims, rnd, avoid)
    cars = _open_points(area, args.cars, rnd, avoid + victims, min_sep=25.0)
    actors = ""
    for k, (x, y) in enumerate(victims):
        actors += _person_or_car("person", f"survivor_{k}", x, y, rnd.uniform(0, 6.28), not args.no_fuel, rnd)
    for k, (x, y) in enumerate(cars):
        actors += _person_or_car("car", f"parked_car_{k}", x, y, rnd.uniform(0, 6.28), not args.no_fuel, rnd)
    qx, qy = _open_points(area, 1, rnd, avoid + victims + cars)[0] if args.target else (None, None)
    if args.target:
        actors += _person_or_car("car", "quarry", qx, qy, 0.0, not args.no_fuel, rnd).replace(
            "<static>true</static>", "<static>false</static>", 1)

    flood = ""
    if args.flood > 0:
        xs = [p[0] for b in area["buildings"] for p in b["poly"]] or [-800, 800]
        ys = [p[1] for b in area["buildings"] for p in b["poly"]] or [-800, 800]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        sx, sy = max(xs) - min(xs) + 200, max(ys) - min(ys) + 200
        flood = f"""
    <model name="flood_water"><static>true</static><pose>{cx:.1f} {cy:.1f} {args.flood / 2:.2f} 0 0 0</pose>
      <link name="l"><visual name="v"><geometry><box><size>{sx:.0f} {sy:.0f} {args.flood:.2f}</size></box></geometry>
        <material><ambient>0.25 0.33 0.30 1</ambient><diffuse>0.30 0.38 0.32 1</diffuse>
          <specular>0.6 0.6 0.6 1</specular></material><transparency>0.35</transparency></visual></link></model>"""

    city = "".join(f"\n    <include><uri>model://{p}</uri><name>{p}</name></include>" for p in parts)
    sensors = ("""
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>""" if camera else "")
    world = f"""<?xml version="1.0"?>
<!-- Generated by scripts/gz/make_world.py from area '{area.get("name")}' (OSM (c) OpenStreetMap contributors) -->
<sdf version="1.9">
  <world name="swarm">
    <physics name="1ms" type="ignore"><max_step_size>0.001</max_step_size><real_time_factor>1.0</real_time_factor></physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
    <plugin filename="gz-sim-navsat-system" name="gz::sim::systems::NavSat"/>{sensors}
    <scene><ambient>0.6 0.6 0.6 1</ambient><background>0.65 0.78 0.9 1</background><shadows>true</shadows></scene>
    <spherical_coordinates>
      <surface_model>EARTH_WGS84</surface_model><world_frame_orientation>ENU</world_frame_orientation>
      <latitude_deg>{o.lat:.7f}</latitude_deg><longitude_deg>{o.lon:.7f}</longitude_deg>
      <elevation>0</elevation><heading_deg>0</heading_deg>
    </spherical_coordinates>
    <light type="directional" name="sun"><cast_shadows>true</cast_shadows><pose>0 0 400 0 0 0</pose>
      <diffuse>0.95 0.92 0.85 1</diffuse><specular>0.3 0.3 0.3 1</specular>
      <direction>-0.4 0.3 -0.85</direction></light>
    <model name="ground"><static>true</static>
      <link name="l">
        <collision name="c"><geometry><plane><normal>0 0 1</normal><size>20000 20000</size></plane></geometry></collision>
        <visual name="v"><geometry><plane><normal>0 0 1</normal><size>20000 20000</size></plane></geometry>
          <material><ambient>0.42 0.45 0.36 1</ambient><diffuse>0.45 0.48 0.38 1</diffuse></material></visual>
      </link></model>{city}{flood}{actors}{drones}
  </world>
</sdf>
"""
    with open(os.path.join(worlds, "swarm.sdf"), "w") as f:
        f.write(world)
    info = {"area": area.get("name"), "origin": [o.lat, o.lon], "drones": spawns,
            "survivors": victims, "cars": cars, "target": [qx, qy] if args.target else None,
            "camera": camera, "flood_m": args.flood}
    with open(os.path.join(out, "world.json"), "w") as f:
        json.dump(info, f, indent=1)
    with open(os.path.join(out, "env.sh"), "w") as f:
        f.write(f"""# source this before starting Gazebo
export GZ_SIM_RESOURCE_PATH="{models}:{worlds}:{apgz}/models:{apgz}/worlds${{GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}}"
export GZ_SIM_SYSTEM_PLUGIN_PATH="{apgz}/build${{GZ_SIM_SYSTEM_PLUGIN_PATH:+:$GZ_SIM_SYSTEM_PLUGIN_PATH}}"
export SWARM_GZ_WORLD="{worlds}/swarm.sdf"
export SWARM_GZ_INFO="{out}/world.json"
""")
    print(f"world: {worlds}/swarm.sdf  ({len(area['buildings'])} buildings in {len(bmeshes)} meshes, "
          f"{len(spawns)} drones, {len(victims)} survivors, {len(cars)} cars"
          f"{', moving target' if args.target else ''}{f', flood {args.flood} m' if args.flood else ''})")
    print(f"next: source {out}/env.sh && scripts/gz/run_swarm.sh")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fleet", default=None, help="fleet.yaml (default $SWARM_FLEET)")
    ap.add_argument("--ardupilot-gazebo", default=os.environ.get("ARDUPILOT_GAZEBO", "~/ardupilot_gazebo"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--victims", type=int, default=6)
    ap.add_argument("--cars", type=int, default=10)
    ap.add_argument("--target", action="store_true", default=True)
    ap.add_argument("--no-target", dest="target", action="store_false")
    ap.add_argument("--flood", type=float, default=0.0, help="flood water depth in metres (0 = dry)")
    ap.add_argument("--no-camera", action="store_true", help="physics only (no GPU needed)")
    ap.add_argument("--cam-w", type=int, default=640)
    ap.add_argument("--cam-h", type=int, default=400)
    ap.add_argument("--cam-fps", type=float, default=5.0)
    ap.add_argument("--no-fuel", action="store_true", help="primitive people/cars (no internet)")
    ap.add_argument("--synthetic", action="store_true", help="synthetic city if the fleet has no area")
    ap.add_argument("--seed", type=int, default=1)
    build(ap.parse_args())


if __name__ == "__main__":
    main()
