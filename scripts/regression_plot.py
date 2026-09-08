#!/usr/bin/env python3
"""Renders the acceptance figure from a regression CSV."""
import sys, csv, warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    csv_path = sys.argv[1]
    png = sys.argv[2] if len(sys.argv) > 2 else csv_path.replace('.csv', '.png')
    rows = list(csv.DictReader(open(csv_path)))
    labels = sorted({r['label'] for r in rows if r['kind'] == 'telem' and r['label']})
    fig, ax = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    for L in labels:
        tr = [r for r in rows if r['kind'] == 'telem' and r['label'] == L]
        ax[0].plot([float(r['t']) for r in tr], [float(r['alt']) for r in tr], label=L, lw=1)
        ax[2].plot([float(r['t']) for r in tr], [float(r['batt']) for r in tr], lw=1)
        sr = [r for r in rows if r['kind'] == 'status' and r['label'] == L]
        ax[1].plot([float(r['t']) for r in sr], [float(r['dist']) for r in sr], lw=1)
    ax[1].axhline(120, color='r', ls='--', lw=1, label='criterion: ON_STATION band 120 m')
    for e in [r for r in rows if r['kind'] == 'event']:
        ev = e.get('event') or ''
        c = 'g' if 'FORMED' in ev else ('orange' if 'DEGRADED' in ev else 'gray')
        try:
            t = float(e['t'])
        except ValueError:
            continue
        for a in ax: a.axvline(t, color=c, ls=':', lw=1)
        ax[0].annotate(ev, (t + 1, ax[0].get_ylim()[1] * 0.85), fontsize=8, color=c)
    ax[0].set_title('Regression acceptance run'); ax[0].set_ylabel('altitude (m)')
    ax[1].set_ylabel('|dist - R| (m)'); ax[2].set_ylabel('battery (%)'); ax[2].set_xlabel('t (s)')
    ax[0].legend(ncol=5, fontsize=8); ax[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(png, dpi=110)
    print(f'GRAPH: {png}')

if __name__ == '__main__':
    main()
