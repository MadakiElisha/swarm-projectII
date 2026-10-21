#!/usr/bin/env bash
# Degrade the virtual radio network between drone containers.
#   netem.sh loss  <container> <pct>     e.g. netem.sh loss drone3 30%
#   netem.sh delay <container> <time>    e.g. netem.sh delay drone3 200ms
#   netem.sh split "<group A>" "<group B>"   (drop traffic between the groups)
#   netem.sh heal                         (remove all impairments)
set -eu
P="${COMPOSE_PROJECT_NAME:-docker}"
cid() { docker ps -qf "name=${P}-$1-" | head -1; }
ip_of() { docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$(cid "$1")"; }
tcx() { docker exec "$(cid "$1")" tc qdisc replace dev eth0 root netem "${@:2}"; }
case "${1:-}" in
  loss)  tcx "$2" loss "$3" ;;
  delay) tcx "$2" delay "$3" ;;
  split)
    for a in $2; do for b in $3; do
      docker exec "$(cid "$a")" iptables -A INPUT -s "$(ip_of "$b")" -j DROP
      docker exec "$(cid "$b")" iptables -A INPUT -s "$(ip_of "$a")" -j DROP
    done; done ;;
  heal)
    for c in $(docker ps -qf "name=${P}-drone"); do
      docker exec "$c" tc qdisc del dev eth0 root 2>/dev/null || true
      docker exec "$c" iptables -F INPUT
    done ;;
  *) sed -n '2,7p' "$0"; exit 1 ;;
esac
