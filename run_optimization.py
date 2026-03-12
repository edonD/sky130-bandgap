#!/usr/bin/env python3
"""Focused optimization to improve margins on all specs."""
import os, sys, re, json, csv, time, subprocess, tempfile
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

os.chdir("/home/ubuntu/sky130-bandgap")
sys.path.insert(0, ".")
from de.engine import DifferentialEvolution, load_parameters as de_load_params

NGSPICE = "ngspice"
template = open("design.cir").read()
specs = json.load(open("specs.json"))

# Tighter parameter ranges centered on current best
params_tight = [
    {"name": "Wm", "min": 30, "max": 200, "scale": "log"},
    {"name": "Lm", "min": 1, "max": 8, "scale": "log"},
    {"name": "Wd", "min": 5, "max": 80, "scale": "log"},
    {"name": "Ld", "min": 1, "max": 8, "scale": "log"},
    {"name": "Wl", "min": 1, "max": 30, "scale": "log"},
    {"name": "Ll", "min": 2, "max": 10, "scale": "log"},
    {"name": "Rtail", "min": 20000, "max": 500000, "scale": "log"},
    {"name": "Rptat", "min": 10000, "max": 100000, "scale": "log"},
    {"name": "Rratio", "min": 6, "max": 12, "scale": "log"},
    {"name": "Wstart", "min": 0.5, "max": 5, "scale": "log"},
    {"name": "Cc", "min": 1, "max": 20, "scale": "log"},
]

def format_netlist(tmpl, pvals):
    return re.sub(r'\{(\w+)\}', lambda m: str(pvals.get(m.group(1), m.group(0))), tmpl)

def run_simulation(tmpl, pvals, idx, tmp_dir):
    try:
        netlist = format_netlist(tmpl, pvals)
    except Exception as e:
        return {"idx": idx, "error": str(e), "measurements": {}}
    path = os.path.join(tmp_dir, f"sim_{idx}.cir")
    with open(path, "w") as f:
        f.write(netlist)
    try:
        result = subprocess.run([NGSPICE, "-b", path], capture_output=True, text=True, timeout=90)
        output = result.stdout
    except subprocess.TimeoutExpired:
        return {"idx": idx, "error": "timeout", "measurements": {}}
    except Exception as e:
        return {"idx": idx, "error": str(e), "measurements": {}}
    finally:
        try: os.unlink(path)
        except: pass
    if "RESULT_DONE" not in output:
        return {"idx": idx, "error": "no_done", "measurements": {}}
    m = {}
    for line in output.split("\n"):
        if "RESULT_" in line and "RESULT_DONE" not in line:
            match = re.search(r'(RESULT_\w+)\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', line)
            if match:
                m[match.group(1)] = float(match.group(2))
    return {"idx": idx, "error": None, "measurements": m}

def compute_cost(meas):
    if not meas:
        return 1e6
    vref = meas.get("RESULT_VREF_V")
    tc = meas.get("RESULT_TEMPCO_PPM")
    psrr = meas.get("RESULT_PSRR_DB")
    pwr = meas.get("RESULT_POWER_UW")
    lr = meas.get("RESULT_LINE_REG_MV_V")
    if any(v is None for v in [vref, tc, psrr, pwr, lr]):
        return 1e6
    cost = 0
    # Vref: target 1.15-1.25, penalize distance from center
    if 1.15 <= vref <= 1.25:
        cost -= 2.5 * (1 - abs(vref - 1.2) / 0.05)
    else:
        cost += 50 * max(abs(vref - 1.2) - 0.05, 0) ** 2
    # Tempco: target <50, reward lower
    if tc < 50:
        cost -= 2.5 * (1 - tc / 50)
    else:
        cost += 50 * ((tc - 50) / 50) ** 2
    # PSRR: target >40, reward higher
    if psrr > 40:
        cost -= 2.0 * min((psrr - 40) / 40, 1)
    else:
        cost += 50 * ((40 - psrr) / 40) ** 2
    # Power: target <100, reward lower
    if pwr < 100:
        cost -= 1.5 * (1 - pwr / 100)
    else:
        cost += 50 * ((pwr - 100) / 100) ** 2
    # Line reg: target <10, reward lower
    if lr < 10:
        cost -= 1.5 * (1 - lr / 10)
    else:
        cost += 50 * ((lr - 10) / 10) ** 2
    return cost

N_WORKERS = 4

def eval_batch(parameters, **kwargs):
    tmp_dir = tempfile.mkdtemp(prefix="bgr_de_")
    n = len(parameters)
    results = [None] * n
    with ProcessPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {pool.submit(run_simulation, template, p, i, tmp_dir): i for i, p in enumerate(parameters)}
        for f in as_completed(futures):
            r = f.result()
            results[r["idx"]] = r
    metrics = []
    for r in results:
        if r is None or r.get("error"):
            metrics.append(1e6)
        else:
            metrics.append(compute_cost(r["measurements"]))
    try: os.rmdir(tmp_dir)
    except: pass
    return {"metrics": metrics}

# Write temp params CSV
tmp_csv = "/tmp/de_params_tight.csv"
with open(tmp_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["name", "min", "max", "scale"])
    for p in params_tight:
        w.writerow([p["name"], p["min"], p["max"], p["scale"]])
de_params = de_load_params(tmp_csv)

print(f"Starting DE optimization with {len(params_tight)} parameters, 4 workers")
print(f"Pop=60, patience=30, max_iter=200")

de = DifferentialEvolution(
    params=de_params,
    eval_func=eval_batch,
    pop_size=60,
    opt_dir="min",
    min_iterations=20,
    max_iterations=200,
    metric_threshold=-10.0,
    patience=30,
    F1=0.7, F2=0.3, F3=0.1, CR=0.9,
)

t0 = time.time()
result = de.run()
elapsed = time.time() - t0

best = result["best_parameters"]
print(f"\nDE completed in {elapsed:.0f}s, {result['iterations']} iterations")
print(f"Best metric: {result['best_metric']:.4f}")
print("Best parameters:")
for k, v in sorted(best.items()):
    print(f"  {k}: {v:.4f}")

# Final simulation to get measurements
tmp_dir = tempfile.mkdtemp(prefix="bgr_final_")
final = run_simulation(template, best, 0, tmp_dir)
try: os.rmdir(tmp_dir)
except: pass

if final.get("error"):
    print(f"Final sim error: {final['error']}")
    sys.exit(1)

meas = final["measurements"]
print("\nFinal measurements:")
for k, v in sorted(meas.items()):
    print(f"  {k}: {v:.4f}")

# Save
with open("best_parameters.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["name", "value"])
    for k, v in sorted(best.items()):
        w.writerow([k, v])

with open("measurements.json", "w") as f:
    json.dump({"measurements": meas, "parameters": best,
               "de_result": {"iterations": result["iterations"], "best_metric": result["best_metric"],
                             "converged": result["converged"], "stop_reason": result["stop_reason"]}}, f, indent=2)

print("\nSaved best_parameters.csv and measurements.json")
