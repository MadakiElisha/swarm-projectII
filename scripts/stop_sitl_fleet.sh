#!/usr/bin/env bash
pkill -f "arducopter|MAVProxy" 2>/dev/null
echo "[fleet] SITL fleet stopped"
