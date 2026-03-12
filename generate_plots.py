#!/usr/bin/env python3
"""Generate all required plots for the bandgap reference design."""
import subprocess, os, sys
import numpy as np
os.chdir("/home/ubuntu/sky130-bandgap")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'figure.facecolor': '#1a1a2e', 'axes.facecolor': '#16213e',
    'axes.edgecolor': '#e94560', 'axes.labelcolor': '#eee',
    'text.color': '#eee', 'xtick.color': '#aaa', 'ytick.color': '#aaa',
    'grid.color': '#333', 'grid.alpha': 0.5, 'lines.linewidth': 2, 'font.size': 11,
})

PARAMS = {'Wm': 85, 'Lm': 2, 'Wd': 20, 'Ld': 4, 'Wl': 5, 'Ll': 10,
          'Rptat': 30000, 'Rratio': 7.7, 'Rtail': 50000, 'Wstart': 2, 'Cc': 3}

def base_netlist():
    return f"""* SKY130 Bandgap Voltage Reference
.lib "sky130_models/sky130.lib.spice" tt
.param rptat_val = {PARAMS['Rptat']}
.param rratio_val = {PARAMS['Rratio']}
Vdd vdd 0 dc 1.8 ac 1
Vss vss 0 0
XQ1 vss vss n1 vss sky130_fd_pr__pnp_05v5_W0p68L0p68 m=1
XQ2 vss vss ne2 vss sky130_fd_pr__pnp_05v5_W0p68L0p68 m=8
Rptat n2 ne2 {PARAMS['Rptat']}
XMp1 n1 ng vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wm']}u L={PARAMS['Lm']}u nf=1
XMp2 n2 ng vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wm']}u L={PARAMS['Lm']}u nf=1
XMp3 vref ng vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wm']}u L={PARAMS['Lm']}u nf=1
XMd1 na n2 nsc vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wd']}u L={PARAMS['Ld']}u nf=1
XMd2 ng n1 nsc vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wd']}u L={PARAMS['Ld']}u nf=1
Rtail vdd nsc {PARAMS['Rtail']}
XMl1 na na vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wl']}u L={PARAMS['Ll']}u nf=1
XMl2 ng na vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wl']}u L={PARAMS['Ll']}u nf=1
XQ3 vss vss nq3 vss sky130_fd_pr__pnp_05v5_W0p68L0p68 m=1
Rout vref nq3 'rptat_val * rratio_val'
XMs n1 vref vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wstart']}u L=4u nf=1
Cc ng vss {PARAMS['Cc']}p
.ic v(n1)=0.75 v(n2)=0.75 v(vref)=1.2 v(ng)=1.0 v(nsc)=1.4
.options gmin=1e-11 abstol=1e-11 reltol=0.01 itl1=500 srcsteps=10
"""

def run_sim(netlist, outfile="/tmp/plot_sim.cir"):
    with open(outfile, 'w') as f:
        f.write(netlist)
    r = subprocess.run(['ngspice', '-b', outfile], capture_output=True, text=True, timeout=120,
                       cwd="/home/ubuntu/sky130-bandgap")
    return r.stdout

os.makedirs("plots", exist_ok=True)

# 1. Vref vs Temperature
print("1. vref_vs_temp.png...")
net = base_netlist() + """.control
dc temp -40 125 1
wrdata /tmp/plot_vref_temp.csv v(vref)
.endc
.end
"""
run_sim(net)
data = np.loadtxt("/tmp/plot_vref_temp.csv")
temps, vrefs = data[:,0], data[:,1]
vmax, vmin = vrefs.max(), vrefs.min()
vmean = (vmax+vmin)/2
tempco = (vmax-vmin)/vmean/165*1e6
fig, ax = plt.subplots(figsize=(10,6))
ax.plot(temps, vrefs*1000, '-', color='#e94560')
ax.set_xlabel('Temperature (C)'); ax.set_ylabel('Vref (mV)')
ax.set_title('Bandgap Reference: Vref vs Temperature')
ax.annotate(f'TC = {tempco:.1f} ppm/C\nVref = {vmean*1000:.1f} mV\nRange: {(vmax-vmin)*1000:.2f} mV',
    xy=(0.05,0.95), xycoords='axes fraction', va='top', fontsize=12, color='#e94560',
    bbox=dict(boxstyle='round', fc='#16213e', ec='#e94560', alpha=0.9))
ax.grid(True); plt.tight_layout()
plt.savefig('plots/vref_vs_temp.png', dpi=150); plt.close()

# 2. Vref vs VDD
print("2. vref_vs_vdd.png...")
net = base_netlist() + """.control
dc Vdd 1.4 2.2 0.01
wrdata /tmp/plot_vref_vdd.csv v(vref)
.endc
.end
"""
run_sim(net)
data = np.loadtxt("/tmp/plot_vref_vdd.csv")
vdds, vrefs_v = data[:,0], data[:,1]
line_reg = abs(vrefs_v[-1]-vrefs_v[0])/(vdds[-1]-vdds[0])*1000
fig, ax = plt.subplots(figsize=(10,6))
ax.plot(vdds, vrefs_v*1000, '-', color='#0f3460')
ax.set_xlabel('VDD (V)'); ax.set_ylabel('Vref (mV)')
ax.set_title('Bandgap Reference: Vref vs Supply Voltage')
ax.annotate(f'Line Reg = {line_reg:.2f} mV/V', xy=(0.05,0.95), xycoords='axes fraction',
    va='top', fontsize=12, color='#0f3460',
    bbox=dict(boxstyle='round', fc='#16213e', ec='#0f3460', alpha=0.9))
ax.grid(True); plt.tight_layout()
plt.savefig('plots/vref_vs_vdd.png', dpi=150); plt.close()

# 3. PSRR
print("3. psrr.png...")
net = base_netlist() + """.control
op
ac dec 50 1 1G
wrdata /tmp/plot_psrr.csv vdb(vref)
.endc
.end
"""
run_sim(net)
data = np.loadtxt("/tmp/plot_psrr.csv")
freqs, vdb = data[:,0], data[:,1]
psrr = -vdb
psrr_dc = np.interp(100, freqs, psrr)
psrr_1k = np.interp(1000, freqs, psrr)
fig, ax = plt.subplots(figsize=(10,6))
ax.semilogx(freqs, psrr, '-', color='#533483')
ax.set_xlabel('Frequency (Hz)'); ax.set_ylabel('PSRR (dB)')
ax.set_title('Bandgap Reference: PSRR')
ax.annotate(f'PSRR @ 100Hz = {psrr_dc:.1f} dB\nPSRR @ 1kHz = {psrr_1k:.1f} dB',
    xy=(0.05,0.95), xycoords='axes fraction', va='top', fontsize=12, color='#533483',
    bbox=dict(boxstyle='round', fc='#16213e', ec='#533483', alpha=0.9))
ax.grid(True); plt.tight_layout()
plt.savefig('plots/psrr.png', dpi=150); plt.close()

# 4. Startup
print("4. startup.png...")
startup_net = f"""* Startup
.lib "sky130_models/sky130.lib.spice" tt
.param rptat_val = {PARAMS['Rptat']}
.param rratio_val = {PARAMS['Rratio']}
Vdd vdd 0 dc PULSE(0 1.8 0 10u 0 100u)
Vss vss 0 0
XQ1 vss vss n1 vss sky130_fd_pr__pnp_05v5_W0p68L0p68 m=1
XQ2 vss vss ne2 vss sky130_fd_pr__pnp_05v5_W0p68L0p68 m=8
Rptat n2 ne2 {PARAMS['Rptat']}
XMp1 n1 ng vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wm']}u L={PARAMS['Lm']}u nf=1
XMp2 n2 ng vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wm']}u L={PARAMS['Lm']}u nf=1
XMp3 vref ng vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wm']}u L={PARAMS['Lm']}u nf=1
XMd1 na n2 nsc vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wd']}u L={PARAMS['Ld']}u nf=1
XMd2 ng n1 nsc vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wd']}u L={PARAMS['Ld']}u nf=1
Rtail vdd nsc {PARAMS['Rtail']}
XMl1 na na vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wl']}u L={PARAMS['Ll']}u nf=1
XMl2 ng na vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wl']}u L={PARAMS['Ll']}u nf=1
XQ3 vss vss nq3 vss sky130_fd_pr__pnp_05v5_W0p68L0p68 m=1
Rout vref nq3 'rptat_val * rratio_val'
XMs n1 vref vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wstart']}u L=4u nf=1
Cc ng vss {PARAMS['Cc']}p
.ic v(n1)=0 v(n2)=0 v(vref)=0 v(ng)=0 v(nsc)=0
.options reltol=0.01 itl4=200 itl1=500
.control
tran 0.05u 50u uic
wrdata /tmp/plot_startup.csv v(vref) v(vdd)
.endc
.end
"""
with open('/tmp/startup_sim.cir','w') as f: f.write(startup_net)
subprocess.run(['ngspice','-b','/tmp/startup_sim.cir'], capture_output=True, text=True, timeout=120,
               cwd="/home/ubuntu/sky130-bandgap")
data = np.loadtxt("/tmp/plot_startup.csv")
times, vref_t, vdd_t = data[:,0]*1e6, data[:,1], data[:,2]
fig, ax = plt.subplots(figsize=(10,6))
ax.plot(times, vdd_t, '--', color='#aaa', linewidth=1.5, label='VDD')
ax.plot(times, vref_t, '-', color='#e94560', linewidth=2, label='Vref')
ax.set_xlabel('Time (us)'); ax.set_ylabel('Voltage (V)')
ax.set_title('Bandgap Reference: Startup Transient')
vref_final = vref_t[-1]
settled = np.where(np.abs(vref_t - vref_final) < 0.01*abs(vref_final))[0]
if len(settled)>0:
    ts = times[settled[0]]
    ax.annotate(f'Settled to {vref_final:.3f}V at t={ts:.1f}us',
        xy=(0.4,0.5), xycoords='axes fraction', fontsize=12, color='#e94560',
        bbox=dict(boxstyle='round', fc='#16213e', ec='#e94560', alpha=0.9))
ax.legend(loc='center right'); ax.grid(True); plt.tight_layout()
plt.savefig('plots/startup.png', dpi=150); plt.close()

print("All plots generated!")
