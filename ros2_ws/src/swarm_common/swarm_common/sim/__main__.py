"""Run simulator scenarios from the command line.

    python3 -m swarm_common.sim                       # all scenarios
    python3 -m swarm_common.sim perimeter intercept   # some
    python3 -m swarm_common.sim perimeter --plot out.png --loss 0.3 --seed 4
"""
import argparse
import inspect
import sys
import time

from . import scenarios


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m swarm_common.sim")
    ap.add_argument("names", nargs="*", help=f"scenarios (default: all): {', '.join(scenarios.ALL)}")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--loss", type=float, default=None, help="packet loss 0..1 (where supported)")
    ap.add_argument("--plot", default=None, help="write a trajectory plot (single scenario)")
    ap.add_argument("--log", action="store_true", help="print brain/FSM logs")
    a = ap.parse_args(argv)
    names = a.names or list(scenarios.ALL)
    bad = [n for n in names if n not in scenarios.ALL]
    if bad:
        ap.error(f"unknown scenario(s): {bad}")
    ok = True
    for n in names:
        fn = scenarios.ALL[n]
        kw = {}
        params = inspect.signature(fn).parameters
        if a.seed is not None and "seed" in params:
            kw["seed"] = a.seed
        if a.loss is not None and "loss" in params:
            kw["loss"] = a.loss
        t0 = time.time()
        r = fn(**kw)
        print(r.summary(), f"[{time.time() - t0:.1f} s wall]")
        if a.log:
            for t, line in r.sim.logs:
                print(f"   {t:7.1f}  {line}")
        if a.plot and len(names) == 1:
            plot(r, a.plot)
            print(f"   plot written to {a.plot}")
        ok &= r.passed
    return 0 if ok else 1


def plot(result, path: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sim = result.sim
    fig, ax = plt.subplots(figsize=(8, 8))
    for i, pts in sim.track.items():
        if pts:
            ax.plot([p[1] for p in pts], [p[2] for p in pts], lw=1, label=f"D{i}")
            ax.plot(*sim.veh[i].home, "k^", ms=5)
    for v in sim.victims:
        ax.plot(v.x, v.y, "r*", ms=12)
    ax.set_aspect("equal")
    ax.set_xlabel("east (m)")
    ax.set_ylabel("north (m)")
    ax.set_title(f"{result.name}: {'PASS' if result.passed else 'FAIL'}")
    ax.legend(fontsize=7)
    fig.savefig(path, dpi=110, bbox_inches="tight")


if __name__ == "__main__":
    sys.exit(main())
