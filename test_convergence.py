#!/usr/bin/env python3
import random, subprocess, re, os

os.chdir("/home/ubuntu/sky130-bandgap")
template = open("design.cir").read()
success = 0
total = 10

for trial in range(total):
    params = {
        "Wm": 10**random.uniform(0.3, 2.3),
        "Lm": 10**random.uniform(-0.3, 1),
        "Wd": 10**random.uniform(0.3, 2),
        "Ld": 10**random.uniform(-0.3, 1),
        "Wl": 10**random.uniform(0, 1.7),
        "Ll": 10**random.uniform(-0.3, 1),
        "Rtail": 10**random.uniform(4.7, 6.3),
        "Rptat": 10**random.uniform(3.7, 5.3),
        "Rratio": 10**random.uniform(0.7, 1.3),
        "Wstart": 10**random.uniform(-0.3, 1),
        "Cc": 10**random.uniform(0, 1.7),
    }
    netlist = re.sub(r'\{(\w+)\}', lambda m: str(params.get(m.group(1), m.group(0))), template)
    path = "/tmp/test_conv_%d.cir" % trial
    with open(path, "w") as f:
        f.write(netlist)
    try:
        r = subprocess.run(
            ["ngspice", "-b", path],
            capture_output=True, text=True, timeout=60,
            cwd="/home/ubuntu/sky130-bandgap"
        )
        done = "RESULT_DONE" in r.stdout
    except Exception:
        done = False
    if done:
        success += 1
        for line in r.stdout.split("\n"):
            if "RESULT_VREF_V" in line:
                print("Trial %d: OK %s Rratio=%.1f" % (trial, line.strip(), params["Rratio"]))
    else:
        print("Trial %d: FAIL" % trial)
    try:
        os.unlink(path)
    except Exception:
        pass

print("Success: %d/%d" % (success, total))
