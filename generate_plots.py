#!/usr/bin/env python3
"""Generate validation plots for the bandgap reference."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import subprocess
import tempfile
import os
import re

# Dark theme
plt.rcParams.update({
    'figure.facecolor': '#1a1a2e', 'axes.facecolor': '#16213e',
    'axes.edgecolor': '#e94560', 'axes.labelcolor': '#eee',
    'text.color': '#eee', 'xtick.color': '#aaa', 'ytick.color': '#aaa',
    'grid.color': '#333', 'grid.alpha': 0.5, 'lines.linewidth': 2,
})

PLOTS_DIR = "plots"
os.makedirs(PLOTS_DIR, exist_ok=True)

# Best parameters
params = {
    'Wm': 85, 'Lm': 2, 'Wd': 20, 'Ld': 4, 'Wl': 5, 'Ll': 10,
    'Rtail': 50000, 'Rptat': 30000, 'Rratio': 7.7, 'Wstart': 2, 'Cc': 3
}

def run_spice(control_block):
    """Run an ngspice simulation and return raw output."""
    netlist = f"""* SKY130 Bandgap — Plot Generation
.lib "sky130_models/sky130.lib.spice" tt
.param rptat_val = {params['Rptat']}
.param rratio_val = {params['Rratio']}

Vdd vdd 0 dc 1.8 ac 1
Vss vss 0 0

XQ1 vss vss n1 vss sky130_fd_pr__pnp_05v5_W0p68L0p68 m=1
XQ2 vss vss ne2 vss sky130_fd_pr__pnp_05v5_W0p68L0p68 m=8
Rptat n2 ne2 {params['Rptat']}

XMp1 n1 ng vdd vdd sky130_fd_pr__pfet_01v8 W={params['Wm']}u L={params['Lm']}u nf=1
XMp2 n2 ng vdd vdd sky130_fd_pr__pfet_01v8 W={params['Wm']}u L={params['Lm']}u nf=1
XMp3 vref ng vdd vdd sky130_fd_pr__pfet_01v8 W={params['Wm']}u L={params['Lm']}u nf=1

XMd1 na n2 nsc vdd sky130_fd_pr__pfet_01v8 W={params['Wd']}u L={params['Ld']}u nf=1
XMd2 ng n1 nsc vdd sky130_fd_pr__pfet_01v8 W={params['Wd']}u L={params['Ld']}u nf=1
Rtail vdd nsc {params['Rtail']}

XMl1 na na vss vss sky130_fd_pr__nfet_01v8 W={params['Wl']}u L={params['Ll']}u nf=1
XMl2 ng na vss vss sky130_fd_pr__nfet_01v8 W={params['Wl']}u L={params['Ll']}u nf=1

XQ3 vss vss nq3 vss sky130_fd_pr__pnp_05v5_W0p68L0p68 m=1
Rout vref nq3 {{rptat_val * rratio_val}}

XMs n1 vref vdd vdd sky130_fd_pr__pfet_01v8 W={params['Wstart']}u L=4u nf=1
Cc ng vss {params['Cc']}p

.ic v(n1)=0.75 v(n2)=0.75 v(vref)=1.2 v(ng)=1.0 v(nsc)=1.4
.options gmin=1e-11 abstol=1e-11 reltol=0.01 itl1=500 srcsteps=10

.control
{control_block}
.endc
.end
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False) as f:
        f.write(netlist)
        path = f.name

    try:
        result = subprocess.run(['ngspice', '-b', path], capture_output=True, text=True, timeout=120)
        return result.stdout + result.stderr
    finally:
        os.unlink(path)

def parse_wrdata(filename):
    """Parse wrdata output file."""
    data = []
    with open(filename) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    data.append([float(x) for x in parts[:2]])
                except ValueError:
                    continue
    return np.array(data) if data else np.array([])

# === Plot 1: Vref vs Temperature ===
print("Generating vref_vs_temp.png...")
tmpfile = "/tmp/bgr_temp.dat"
output = run_spice(f"""
dc temp -40 125 1
wrdata {tmpfile} v(vref)
""")
data = parse_wrdata(tmpfile)
if len(data) > 0:
    temps = data[:, 0]
    vrefs = data[:, 1]
    tempco = (vrefs.max() - vrefs.min()) / np.mean(vrefs) / 165 * 1e6

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(temps, vrefs * 1000, '-', color='#e94560', linewidth=2)
    ax.set_xlabel('Temperature (°C)')
    ax.set_ylabel('Vref (mV)')
    ax.set_title('Bandgap Reference: Vref vs Temperature')
    ax.annotate(f'TC = {tempco:.1f} ppm/°C\nΔVref = {(vrefs.max()-vrefs.min())*1000:.2f} mV',
                xy=(0.05, 0.95), xycoords='axes fraction', va='top',
                fontsize=12, color='#e94560',
                bbox=dict(boxstyle='round', fc='#16213e', ec='#e94560', alpha=0.8))
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'vref_vs_temp.png'), dpi=150)
    plt.close()
    print(f"  Tempco: {tempco:.1f} ppm/°C")
os.unlink(tmpfile) if os.path.exists(tmpfile) else None

# === Plot 2: Vref vs VDD ===
print("Generating vref_vs_vdd.png...")
tmpfile = "/tmp/bgr_vdd.dat"
output = run_spice(f"""
dc Vdd 1.4 2.2 0.01
wrdata {tmpfile} v(vref)
""")
data = parse_wrdata(tmpfile)
if len(data) > 0:
    vdds = data[:, 0]
    vrefs = data[:, 1]
    line_reg = abs(vrefs[-1] - vrefs[0]) / (vdds[-1] - vdds[0]) * 1000

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(vdds, vrefs * 1000, '-', color='#0f3460', linewidth=2)
    ax.set_xlabel('VDD (V)')
    ax.set_ylabel('Vref (mV)')
    ax.set_title('Bandgap Reference: Vref vs Supply Voltage')
    ax.annotate(f'Line Reg = {line_reg:.1f} mV/V',
                xy=(0.05, 0.95), xycoords='axes fraction', va='top',
                fontsize=12, color='#0f3460',
                bbox=dict(boxstyle='round', fc='#16213e', ec='#0f3460', alpha=0.8))
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'vref_vs_vdd.png'), dpi=150)
    plt.close()
    print(f"  Line reg: {line_reg:.1f} mV/V")
os.unlink(tmpfile) if os.path.exists(tmpfile) else None

# === Plot 3: PSRR ===
print("Generating psrr.png...")
tmpfile = "/tmp/bgr_psrr.dat"
output = run_spice(f"""
op
ac dec 100 1 1G
wrdata {tmpfile} vdb(vref)
""")
data = parse_wrdata(tmpfile)
if len(data) > 0:
    freqs = data[:, 0]
    psrr = -data[:, 1]  # PSRR = -vdb(vref)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.semilogx(freqs, psrr, '-', color='#533483', linewidth=2)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('PSRR (dB)')
    ax.set_title('Bandgap Reference: Power Supply Rejection Ratio')
    ax.axhline(y=40, color='#e94560', linestyle='--', alpha=0.5, label='Spec: >40 dB')
    # Find PSRR at key frequencies
    for freq_target in [100, 1000, 1e6]:
        idx = np.argmin(np.abs(freqs - freq_target))
        if idx < len(psrr):
            ax.annotate(f'{psrr[idx]:.1f} dB @ {freq_target:.0f} Hz',
                       xy=(freqs[idx], psrr[idx]), fontsize=9, color='#aaa')
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'psrr.png'), dpi=150)
    plt.close()
    print(f"  PSRR @ 100Hz: {psrr[np.argmin(np.abs(freqs-100))]:.1f} dB")
os.unlink(tmpfile) if os.path.exists(tmpfile) else None

# === Plot 4: Startup ===
print("Generating startup.png...")
tmpfile = "/tmp/bgr_startup.dat"
tmpfile2 = "/tmp/bgr_startup_vdd.dat"
output = run_spice(f"""
* Startup with settled circuit
tran 100n 50u uic
wrdata {tmpfile} v(vref)
wrdata {tmpfile2} v(vdd)
""")
data = parse_wrdata(tmpfile)
data_vdd = parse_wrdata(tmpfile2)
if len(data) > 0:
    times = data[:, 0] * 1e6  # to microseconds
    vrefs = data[:, 1]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(times, vrefs, '-', color='#e94560', linewidth=2, label='Vref')
    ax1.set_xlabel('Time (µs)')
    ax1.set_ylabel('Vref (V)', color='#e94560')
    ax1.set_title('Bandgap Reference: Startup Transient')

    if len(data_vdd) > 0:
        vdds = data_vdd[:, 1]
        ax2 = ax1.twinx()
        ax2.plot(times[:len(vdds)], vdds, '--', color='#0f3460', linewidth=1.5, label='VDD')
        ax2.set_ylabel('VDD (V)', color='#0f3460')

    ax1.axhline(y=1.2, color='#aaa', linestyle=':', alpha=0.5)
    ax1.grid(True)
    fig.legend(loc='upper left', bbox_to_anchor=(0.12, 0.88))
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'startup.png'), dpi=150)
    plt.close()
    print(f"  Vref final: {vrefs[-1]:.4f} V")
for f in [tmpfile, tmpfile2]:
    if os.path.exists(f): os.unlink(f)

# === Progress plot ===
print("Generating progress.png...")
from evaluate import generate_progress_plot
generate_progress_plot("results.tsv", PLOTS_DIR)

print("\nAll plots saved to plots/")
