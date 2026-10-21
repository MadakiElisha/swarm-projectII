#!/usr/bin/env python3
"""Acceptance figure from a ros_acceptance.py CSV: altitude, battery, phases, events."""
import csv
import sys
import warnings

import matplotlib

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PHASES = ["LANDED", "IDLE", "CLAIMING", "ENROUTE", "ON_TASK", "ON_STATION", "SEARCH", "RTB", "FAILSAFE"]


def main():
    path = sys.argv[1]
    png = sys.argv[2] if len(sys.argv) > 2 else path.replace(".csv", ".png")
    rows = list(csv.DictReader(open(path)))
    labels = sorted({r["label"] for r in rows if r["kind"] == "telem"}, key=lambda s: int(s[1:]))
    fig, ax = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    for lab in labels:
        tr = [r for r in rows if r["kind"] == "telem" and r["label"] == lab]
        ax[0].plot([float(r["t"]) for r in tr], [float(r["alt"]) for r in tr], lw=1, label=lab)
        ax[1].plot([float(r["t"]) for r in tr], [float(r["batt"]) for r in tr], lw=1)
        ph = [r for r in rows if r["kind"] == "phase" and r["label"] == lab]
        ax[2].plot([float(r["t"]) for r in ph],
                   [PHASES.index(r["phase"]) if r["phase"] in PHASES else -1 for r in ph],
                   lw=1, drawstyle="steps-post")
    for e in (r for r in rows if r["kind"] == "event"):
        c = "g" if "FORMED" in e["event"] else ("orange" if "DEGRADED" in e["event"] else "gray")
        for a in ax:
            a.axvline(float(e["t"]), color=c, ls=":", lw=1)
    ax[0].set_title("Swarm acceptance run")
    ax[0].set_ylabel("altitude (m)")
    ax[1].set_ylabel("battery (%)")
    ax[2].set_yticks(range(len(PHASES)), PHASES, fontsize=7)
    ax[2].set_xlabel("t (s)")
    ax[0].legend(ncol=6, fontsize=8)
    fig.tight_layout()
    fig.savefig(png, dpi=110)
    print(f"GRAPH: {png}")


if __name__ == "__main__":
    main()
