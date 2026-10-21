#!/usr/bin/env python3
"""Generate gcs/assets/drone.glb: an original X-frame survey quadcopter.

Nodes `prop_1`..`prop_4` are separate so the GCS can spin each propeller
(Cesium nodeTransformations). glTF is Y-up; +X is the nose (camera gimbal).
Scale: metres, ~0.7 m motor-to-motor diagonal (X500 class).
"""
import math
import os

import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gcs", "assets", "drone.glb")


def mat(rgb, metal=0.1, rough=0.6, emissive=None):
    m = PBRMaterial(baseColorFactor=[*rgb, 1.0], metallicFactor=metal, roughnessFactor=rough)
    if emissive:
        m.emissiveFactor = emissive
    return m


def painted(mesh, material):
    mesh.visual = trimesh.visual.TextureVisuals(material=material)
    return mesh


def ypose(mesh, x=0.0, y=0.0, z=0.0, rot=None):
    """Translate (glTF axes: x fwd, y up, z right)."""
    T = np.eye(4)
    if rot is not None:
        T[:3, :3] = rot
    T[:3, 3] = [x, y, z]
    mesh.apply_transform(T)
    return mesh


def rot_axis(axis, ang):
    return trimesh.transformations.rotation_matrix(ang, axis)[:3, :3]


CARBON = mat((0.08, 0.08, 0.09), 0.3, 0.45)
SHELL = mat((0.92, 0.93, 0.95), 0.05, 0.35)
ACCENT = mat((0.0, 0.62, 0.86), 0.1, 0.4)
MOTOR = mat((0.55, 0.57, 0.6), 0.9, 0.3)
PROP = mat((0.12, 0.12, 0.13), 0.0, 0.5)
LENS = mat((0.02, 0.02, 0.03), 0.6, 0.1)
LED_F = mat((0.1, 1.0, 0.3), 0.0, 0.3, emissive=[0.1, 1.0, 0.3])
LED_R = mat((1.0, 0.15, 0.1), 0.0, 0.3, emissive=[1.0, 0.15, 0.1])


def build():
    scene = trimesh.Scene()
    arm_r = 0.25                                  # centre -> motor
    # --- fuselage: rounded shell + top canopy + battery tray
    body = trimesh.creation.box(extents=[0.26, 0.07, 0.17])
    body = painted(ypose(body, y=0.0), SHELL)
    canopy = painted(ypose(trimesh.creation.icosphere(subdivisions=3, radius=1.0), y=0.035), SHELL)
    canopy.apply_scale([0.12, 0.045, 0.08])
    canopy.apply_translation([0.02, 0.035, 0.0])
    stripe = painted(ypose(trimesh.creation.box(extents=[0.27, 0.012, 0.175]), y=0.01), ACCENT)
    batt = painted(ypose(trimesh.creation.box(extents=[0.18, 0.04, 0.09]), y=-0.055), CARBON)
    for name, m in (("body", body), ("canopy", canopy), ("stripe", stripe), ("battery", batt)):
        scene.add_geometry(m, node_name=name, geom_name=name)
    # --- arms, motors, props (X configuration: 45, 135, 225, 315 deg)
    for k, deg in enumerate((45, 135, 225, 315), start=1):
        a = math.radians(deg)
        mx, mz = arm_r * math.cos(a), arm_r * math.sin(a)
        # cylinder default axis is Z -> rotate to lie along the arm direction
        arm_fix = trimesh.creation.cylinder(radius=0.011, height=arm_r, sections=16)
        arm_fix.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        direction = np.array([math.cos(a), 0, math.sin(a)])
        R = trimesh.geometry.align_vectors([1, 0, 0], direction)
        arm_fix.apply_transform(R)
        arm_fix.apply_translation([mx / 2, 0.0, mz / 2])
        scene.add_geometry(painted(arm_fix, CARBON), node_name=f"arm_{k}", geom_name=f"arm_{k}")
        motor = trimesh.creation.cylinder(radius=0.022, height=0.035, sections=24)
        motor.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        motor.apply_translation([mx, 0.02, mz])
        scene.add_geometry(painted(motor, MOTOR), node_name=f"motor_{k}", geom_name=f"motor_{k}")
        # propeller: two tapered blades + hub, modelled around its own origin, placed by node
        hub = trimesh.creation.cylinder(radius=0.008, height=0.012, sections=16)
        hub.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        blades = []
        for s in (1, -1):
            b = trimesh.creation.box(extents=[0.115, 0.003, 0.022])
            b.apply_translation([s * 0.06, 0.0, 0.0])
            b.apply_transform(trimesh.transformations.rotation_matrix(s * 0.18, [1, 0, 0]))
            blades.append(b)
        prop = trimesh.util.concatenate([hub] + blades)
        prop = painted(prop, PROP)
        T = np.eye(4)
        T[:3, 3] = [mx, 0.045, mz]
        scene.add_geometry(prop, node_name=f"prop_{k}", geom_name=f"prop_{k}", transform=T)
    # --- landing gear
    for s in (1, -1):
        leg = trimesh.creation.cylinder(radius=0.006, height=0.12, sections=10)
        leg.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        leg.apply_translation([0.0, -0.09, s * 0.07])
        skid = trimesh.creation.cylinder(radius=0.007, height=0.24, sections=10)
        skid.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        skid.apply_translation([0.0, -0.15, s * 0.07])
        scene.add_geometry(painted(trimesh.util.concatenate([leg, skid]), CARBON),
                           node_name=f"gear_{'l' if s > 0 else 'r'}")
    # --- gimbal camera at the nose (+X)
    gimbal = painted(ypose(trimesh.creation.icosphere(subdivisions=3, radius=0.032),
                           x=0.14, y=-0.06), CARBON)
    lens = trimesh.creation.cylinder(radius=0.014, height=0.012, sections=20)
    lens.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    lens.apply_translation([0.17, -0.06, 0.0])
    scene.add_geometry(gimbal, node_name="gimbal")
    scene.add_geometry(painted(lens, LENS), node_name="lens")
    # --- nav LEDs: green front, red rear
    for name, x, m in (("led_front", 0.135, LED_F), ("led_rear", -0.135, LED_R)):
        led = painted(ypose(trimesh.creation.icosphere(subdivisions=2, radius=0.012), x=x, y=0.02), m)
        scene.add_geometry(led, node_name=name)
    return scene


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    data = build().export(file_type="glb")
    with open(OUT, "wb") as f:
        f.write(data)
    print(f"wrote {OUT} ({len(data) / 1024:.0f} KiB)")
