#!/usr/bin/env python3
"""Quick targeted parameter sweeps - one param at a time."""
import subprocess, re, os, sys, json, csv
os.chdir("/home/ubuntu/sky130-bandgap")

FAST_TEMPLATE = open("fast_design.cir").read()

def run_sim(params):
    netlist = re.sub(r'\{(\w+)\}', lambda m: str(params.get(m.group(1), m.group(0))), FAST_TEMPLATE)
    with open("/tmp/qs_sim.cir", "w") as f:
        f.write(netlist)
    try:
        r = subprocess.run(["ngspice", "-b", "/tmp/qs_sim.cir"], capture_output=True, text=True,
                          timeout=60, cwd="/home/ubuntu/sky130-bandgap")
        out = r.stdout
    except:
        return None
    if "RESULT_DONE" not in out:
        return None
    meas = {}
    for line in out.split("\n"):
        if "RESULT_" in line and "DONE" not in line:
            match = re.search(r'(RESULT_\w+)\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', line)
            if match:
                meas[match.group(1)] = float(match.group(2))
    return meas

def check_all(m):
    if not m: return False
    return (1.15 <= m.get("RESULT_VREF_V",0) <= 1.25 and
            m.get("RESULT_TEMPCO_PPM",999) < 50 and
            m.get("RESULT_PSRR_DB",0) > 40 and
            m.get("RESULT_POWER_UW",999) < 100 and
            m.get("RESULT_LINE_REG_MV_V",999) < 10)

def score(m):
    """Lower is better. Combines margins on all specs."""
    if not m or not check_all(m): return 999
    tc = m["RESULT_TEMPCO_PPM"]
    lr = m["RESULT_LINE_REG_MV_V"]
    psrr = m["RESULT_PSRR_DB"]
    # Weighted: lower tempco, lower line_reg, higher PSRR
    return tc + lr * 2 - psrr * 0.3

base = {"Wm": 85, "Lm": 2, "Wd": 20, "Ld": 4, "Wl": 5, "Ll": 10,
        "Rptat": 30000, "Rratio": 7.7, "Rtail": 50000, "Wstart": 2, "Cc": 3}

def sweep_param(name, values, base_params):
    print(f"\n--- Sweep {name} ---")
    best_s = score(run_sim(base_params))
    best_v = base_params[name]
    for v in values:
        p = dict(base_params)
        p[name] = v
        m = run_sim(p)
        s = score(m) if m else 999
        if m and check_all(m):
            tc = m["RESULT_TEMPCO_PPM"]
            lr = m["RESULT_LINE_REG_MV_V"]
            psrr = m["RESULT_PSRR_DB"]
            vref = m["RESULT_VREF_V"]
            marker = " <-- BEST" if s < best_s else ""
            print(f"  {name}={v}: TC={tc:.1f} LR={lr:.1f} PSRR={psrr:.1f} Vref={vref:.4f} score={s:.1f}{marker}")
            if s < best_s:
                best_s = s
                best_v = v
    base_params[name] = best_v
    print(f"  Selected {name}={best_v}")
    return base_params

# Sweep each parameter
import numpy as np

base = sweep_param("Rratio", np.arange(6.5, 9.0, 0.1), base)
base = sweep_param("Rptat", [15000, 20000, 25000, 30000, 40000, 50000, 60000, 80000], base)
base = sweep_param("Rratio", np.arange(6.0, 10.0, 0.1), base)  # re-sweep with new Rptat
base = sweep_param("Rtail", [20000, 30000, 40000, 50000, 70000, 100000, 150000, 200000], base)
base = sweep_param("Wm", [30, 50, 85, 120, 150, 200], base)
base = sweep_param("Lm", [1, 1.5, 2, 3, 4, 6], base)
base = sweep_param("Wd", [10, 15, 20, 30, 50, 80], base)
base = sweep_param("Ld", [2, 3, 4, 5, 6, 8], base)
base = sweep_param("Wl", [2, 3, 5, 8, 12, 20], base)
base = sweep_param("Ll", [3, 4, 6, 8, 10], base)
base = sweep_param("Rratio", np.arange(base["Rratio"]-0.5, base["Rratio"]+0.6, 0.05), base)  # final fine-tune

# Final result
print(f"\n{'='*60}")
print(f"OPTIMIZED PARAMETERS: {base}")
m = run_sim(base)
if m:
    print(f"Vref = {m.get('RESULT_VREF_V',0):.4f} V")
    print(f"TC   = {m.get('RESULT_TEMPCO_PPM',0):.1f} ppm/C")
    print(f"PSRR = {m.get('RESULT_PSRR_DB',0):.1f} dB")
    print(f"LR   = {m.get('RESULT_LINE_REG_MV_V',0):.1f} mV/V")
    print(f"Pwr  = {m.get('RESULT_POWER_UW',0):.1f} uW")
    print(f"All met: {check_all(m)}")
    with open("best_parameters.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "value"])
        for k, v in sorted(base.items()):
            w.writerow([k, v])
    with open("measurements.json", "w") as f:
        json.dump({"measurements": m, "parameters": base, "score": 1.0 if check_all(m) else 0.0}, f, indent=2)
    print("Saved!")
