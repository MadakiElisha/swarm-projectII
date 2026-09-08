#!/usr/bin/env bash
# Liveness check that never connects (no EOF noise): processes + listeners.
echo "processes: $(pgrep -c arducopter 2>/dev/null)"
ss -tlnp 2>/dev/null | grep -E ":(5770|5780|5790|5800|5810)" | awk '{print "listening:", $4}'
