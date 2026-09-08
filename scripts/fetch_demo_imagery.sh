#!/bin/bash
# Maritime/press scenes VisDrone lacks. LOCAL demo use only (git-ignored).
D="$(dirname "$0")/../ros2_ws/src/swarm_perception/assets"
mkdir -p "$D"
B="https://image.qwenlm.ai/public_source/602ca67f-593c-450e-aa17-cf8792f6b678"
curl -sL "$B/15aa84dd5-9c15-411b-948b-4c61733498eb9517.png" -o "$D/rnli_speed.png"
curl -sL "$B/85aa84dd5-9c15-411b-948b-4c61733498eb7613.png" -o "$D/water_rescue.png"
curl -sL "$B/65aa84dd5-9c15-411b-948b-4c61733498eb1597.png" -o "$D/sea_sar_aerial.png"
ls -l "$D"
