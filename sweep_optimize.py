#!/usr/bin/env python3
"""Targeted parameter sweep to improve margins."""
import subprocess, re, os, sys, json, csv
import numpy as np

os.chdir("/home/ubuntu/sky130-bandgap")

FAST_TEMPLATE = open("fast_design.cir").read()
NGSPICE = "ngspice"

def run_sim(params):
    netlist = re.sub(r'\{(\w+)\}', lambda m: str(params.get(m.group(1), m.group(0))), FAST_TEMPLATE)
    path = "/tmp/sweep_sim.cir"
    with open(path, "w") as f:
        f.write(netlist)
    try:
        r = subprocess.run([NGSPICE, "-b", path], capture_output=True, text=True, timeout=60,
                          cwd="/home/ubuntu/sky130-bandgap")
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

def check_specs(m):
    if not m: return False, {}
    vref = m.get("RESULT_VREF_V", 0)
    tc = m.get("RESULT_TEMPCO_PPM", 999)
    psrr = m.get("RESULT_PSRR_DB", 0)
    pwr = m.get("RESULT_POWER_UW", 999)
    lr = m.get("RESULT_LINE_REG_MV_V", 999)
    met = {
        "vref": 1.15 <= vref <= 1.25,
        "tc": tc < 50,
        "psrr": psrr > 40,
        "pwr": pwr < 100,
        "lr": lr < 10,
    }
    return all(met.values()), met

# Base params - current best
base = {"Wm": 85, "Lm": 2, "Wd": 20, "Ld": 4, "Wl": 5, "Ll": 10,
        "Rptat": 30000, "Rratio": 7.7, "Rtail": 50000, "Wstart": 2, "Cc": 3}

best_params = dict(base)
best_score = None

# Phase 1: Sweep Rratio for best tempco (keeping Vref in range)
print("=== Phase 1: Sweep Rratio for minimum tempco ===")
best_tc = 999
best_ratio = 7.7
for ratio_10x in range(65, 90):
    ratio = ratio_10x / 10.0
    p = dict(base)
    p["Rratio"] = ratio
    m = run_sim(p)
    if m:
        tc = m.get("RESULT_TEMPCO_PPM", 999)
        vref = m.get("RESULT_VREF_V", 0)
        all_met, _ = check_specs(m)
        marker = " ***" if all_met else ""
        if tc < best_tc and 1.10 <= vref <= 1.30:
            best_tc = tc
            best_ratio = ratio
        print(f"  Rratio={ratio:.1f}: Vref={vref:.4f}V TC={tc:.1f}ppm{marker}")

print(f"\n  Best: Rratio={best_ratio:.1f} -> TC={best_tc:.1f}ppm")
base["Rratio"] = best_ratio

# Phase 2: Sweep Rptat for best overall (affects current level -> headroom -> PSRR)
print("\n=== Phase 2: Sweep Rptat ===")
best_metric = 999
best_rptat = base["Rptat"]
for rptat in [15000, 20000, 25000, 30000, 35000, 40000, 50000, 60000, 80000]:
    p = dict(base)
    p["Rptat"] = rptat
    m = run_sim(p)
    if m:
        tc = m.get("RESULT_TEMPCO_PPM", 999)
        vref = m.get("RESULT_VREF_V", 0)
        psrr = m.get("RESULT_PSRR_DB", 0)
        lr = m.get("RESULT_LINE_REG_MV_V", 999)
        pwr = m.get("RESULT_POWER_UW", 999)
        all_met, _ = check_specs(m)
        metric = tc + lr - psrr + (0 if all_met else 1000)
        marker = " ***" if all_met else ""
        if metric < best_metric:
            best_metric = metric
            best_rptat = rptat
        print(f"  Rptat={rptat}: Vref={vref:.4f} TC={tc:.1f} PSRR={psrr:.1f} LR={lr:.1f} Pwr={pwr:.1f}{marker}")

base["Rptat"] = best_rptat
print(f"  Best Rptat={best_rptat}")

# Re-sweep Rratio with new Rptat
print("\n=== Phase 3: Re-sweep Rratio with new Rptat ===")
best_tc = 999
best_ratio = base["Rratio"]
for ratio_10x in range(60, 95):
    ratio = ratio_10x / 10.0
    p = dict(base)
    p["Rratio"] = ratio
    m = run_sim(p)
    if m:
        tc = m.get("RESULT_TEMPCO_PPM", 999)
        vref = m.get("RESULT_VREF_V", 0)
        all_met, _ = check_specs(m)
        if tc < best_tc and all_met:
            best_tc = tc
            best_ratio = ratio
            print(f"  Rratio={ratio:.1f}: Vref={vref:.4f}V TC={tc:.1f}ppm ***")

base["Rratio"] = best_ratio
print(f"  Best: Rratio={best_ratio:.1f} -> TC={best_tc:.1f}ppm")

# Phase 4: Sweep OTA sizing for PSRR/line reg
print("\n=== Phase 4: Sweep OTA sizing ===")
best_metric = 999
best_ota = (base["Wd"], base["Ld"], base["Wl"], base["Ll"])
for wd in [10, 15, 20, 30, 50]:
    for ld in [2, 4, 6, 8]:
        for wl in [3, 5, 8, 12]:
            for ll in [4, 6, 8, 10]:
                p = dict(base)
                p["Wd"] = wd
                p["Ld"] = ld
                p["Wl"] = wl
                p["Ll"] = ll
                m = run_sim(p)
                if m:
                    tc = m.get("RESULT_TEMPCO_PPM", 999)
                    psrr = m.get("RESULT_PSRR_DB", 0)
                    lr = m.get("RESULT_LINE_REG_MV_V", 999)
                    all_met, _ = check_specs(m)
                    if all_met:
                        metric = tc + lr - psrr * 0.5
                        if metric < best_metric:
                            best_metric = metric
                            best_ota = (wd, ld, wl, ll)
                            vref = m.get("RESULT_VREF_V", 0)
                            pwr = m.get("RESULT_POWER_UW", 999)
                            print(f"  Wd={wd} Ld={ld} Wl={wl} Ll={ll}: TC={tc:.1f} PSRR={psrr:.1f} LR={lr:.1f} Vref={vref:.4f} Pwr={pwr:.1f} ***")

base["Wd"], base["Ld"], base["Wl"], base["Ll"] = best_ota
print(f"  Best OTA: Wd={best_ota[0]} Ld={best_ota[1]} Wl={best_ota[2]} Ll={best_ota[3]}")

# Phase 5: Sweep mirror sizing
print("\n=== Phase 5: Sweep mirror sizing ===")
best_metric = 999
best_mirror = (base["Wm"], base["Lm"])
for wm in [30, 50, 85, 120, 180]:
    for lm in [1, 2, 4, 6]:
        p = dict(base)
        p["Wm"] = wm
        p["Lm"] = lm
        m = run_sim(p)
        if m:
            tc = m.get("RESULT_TEMPCO_PPM", 999)
            psrr = m.get("RESULT_PSRR_DB", 0)
            lr = m.get("RESULT_LINE_REG_MV_V", 999)
            all_met, _ = check_specs(m)
            if all_met:
                metric = tc + lr - psrr * 0.5
                if metric < best_metric:
                    best_metric = metric
                    best_mirror = (wm, lm)
                    vref = m.get("RESULT_VREF_V", 0)
                    pwr = m.get("RESULT_POWER_UW", 999)
                    print(f"  Wm={wm} Lm={lm}: TC={tc:.1f} PSRR={psrr:.1f} LR={lr:.1f} Vref={vref:.4f} Pwr={pwr:.1f} ***")

base["Wm"], base["Lm"] = best_mirror

# Phase 6: Final Rratio fine-tune
print("\n=== Phase 6: Final Rratio fine-tune ===")
best_tc = 999
best_ratio = base["Rratio"]
for ratio_100x in range(int(base["Rratio"]*10)-10, int(base["Rratio"]*10)+11):
    ratio = ratio_100x / 10.0
    p = dict(base)
    p["Rratio"] = ratio
    m = run_sim(p)
    if m:
        tc = m.get("RESULT_TEMPCO_PPM", 999)
        vref = m.get("RESULT_VREF_V", 0)
        all_met, _ = check_specs(m)
        if tc < best_tc and all_met:
            best_tc = tc
            best_ratio = ratio

base["Rratio"] = best_ratio

# Final evaluation
print(f"\n{'='*60}")
print(f"FINAL PARAMETERS: {base}")
m = run_sim(base)
if m:
    all_met, details = check_specs(m)
    print(f"\nVref = {m.get('RESULT_VREF_V', 0):.4f} V")
    print(f"TC   = {m.get('RESULT_TEMPCO_PPM', 0):.1f} ppm/C")
    print(f"PSRR = {m.get('RESULT_PSRR_DB', 0):.1f} dB")
    print(f"LR   = {m.get('RESULT_LINE_REG_MV_V', 0):.1f} mV/V")
    print(f"Pwr  = {m.get('RESULT_POWER_UW', 0):.1f} uW")
    print(f"All specs met: {all_met}")
    print(f"Details: {details}")

    # Save
    with open("best_parameters.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "value"])
        for k, v in sorted(base.items()):
            w.writerow([k, v])
    with open("measurements.json", "w") as f:
        json.dump({"measurements": m, "parameters": base, "score": 1.0 if all_met else 0.0}, f, indent=2)
    print("Saved!")
