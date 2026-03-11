# Autonomous Circuit Design — Bandgap Voltage Reference

You are an autonomous analog circuit designer. Your goal: design a bandgap voltage reference that meets every specification in `specs.json` using the SKY130 foundry PDK.

You have Differential Evolution (DE) as your optimizer. You define topology and parameter ranges — DE finds optimal values. You NEVER set component values manually.

## Files

| File | Editable? | Purpose |
|------|-----------|---------|
| `design.cir` | YES | Parametric SPICE netlist |
| `parameters.csv` | YES | Parameter names, min, max for DE |
| `evaluate.py` | YES | Runs DE, measures, scores, plots |
| `specs.json` | **NO** | Target specifications |
| `program.md` | **NO** | These instructions |
| `de/engine.py` | **NO** | DE optimizer engine |
| `results.tsv` | YES | Experiment log — append after every run |

## Technology

- **PDK:** SkyWater SKY130 (130nm). Models: `.lib "sky130_models/sky130.lib.spice" tt`
- **Devices:** `sky130_fd_pr__nfet_01v8`, `sky130_fd_pr__pfet_01v8` (and LVT/HVT variants)
- **Instantiation:** `XM1 drain gate source bulk sky130_fd_pr__nfet_01v8 W=10u L=0.5u nf=1`
- **Supply:** 1.8V single supply. Nodes: `vdd` = 1.8V, `vss` = 0V
- **Units:** Always specify W and L with `u` suffix (micrometers). Capacitors with `p` or `f`.
- **ngspice settings:** `.spiceinit` must contain `set ngbehavior=hsa` and `set skywaterpdk`

## Design Freedom

You are free to explore any bandgap reference topology. CMOS-only bandgap using parasitic BJTs, Brokaw cell, Banba architecture, curvature-compensated designs, sub-1V bandgap with resistive subdivision — whatever you think will work. Experiment boldly.

SKY130 provides parasitic PNP BJTs (`sky130_fd_pr__pnp_05v5_W0p68L0p68`) that can be used for PTAT current generation. You may also explore MOSFET-only approaches using subthreshold operation for PTAT behavior.

The only constraints are physical reality:

1. **All values parametric.** Every W, L, resistor, capacitor, and bias current uses `{name}` in design.cir with a matching row in parameters.csv.
2. **Ranges must be physically real.** W: 0.5u–500u. L: 0.15u–10u. Resistors: 1kΩ–1MΩ. Caps: 10fF–100pF. Ranges must span at least 10× (one decade).
3. **No hardcoding to game the optimizer.** A range of [5.0, 5.001] is cheating. Every parameter must have real design freedom.
4. **No editing specs.json or model files.** You optimize the circuit to meet the specs, not the other way around.

## The Loop

### 1. Read current state
- `results.tsv` — what you've tried and how it scored
- `design.cir` + `parameters.csv` — current topology
- `specs.json` — what you're targeting

### 2. Design or modify the topology
Change whatever you think will improve performance. You can make small tweaks or try a completely different architecture. Your call.

### 3. Implement
- Edit `design.cir` with the new/modified circuit
- Update `parameters.csv` with ranges for all parameters
- Update `evaluate.py` if measurements need changes
- Verify every `{placeholder}` in design.cir has a parameters.csv entry

### 4. Commit topology
```bash
git add -A
git commit -m "topology: <what changed>"
git push
```
Commit ALL files so any commit can be cloned and understood standalone.

### 5. Run DE
```bash
python evaluate.py 2>&1 | tee run.log          # full run
python evaluate.py --quick 2>&1 | tee run.log   # quick sanity check
```

### 6. Validate — THIS IS MANDATORY

DE found numbers. Now prove they're real. **Do not skip any of these checks.**

#### a) Operating point check
Run `.op` at 27°C. Verify all transistors are in saturation. Verify the output voltage is in the expected range (1.1–1.3V). Check that currents through each branch are reasonable.

#### b) Sanity check against physics
- Vref should be near 1.2V (silicon bandgap). If it's at exactly VDD or 0V, the circuit isn't working.
- PSRR > 80 dB is suspicious at DC — check carefully.
- Tempco < 5 ppm/°C is world-class and unlikely on a first try.
- If the circuit consumes < 1 µW, the bias currents are probably too low to function.

#### c) Temperature sweep verification
Run DC simulation at -40°C, 0°C, 27°C, 85°C, 125°C. Plot Vref vs temperature. The curve should be parabolic (concave down) with a peak near room temperature. If Vref varies monotonically, the PTAT/CTAT cancellation is not working.

#### d) Startup check
Run transient from t=0 with supply ramping from 0 to 1.8V over 10µs. The reference must start up reliably and settle to the correct voltage. Bandgap circuits have a degenerate zero-current operating point — verify the startup circuit kicks it out.

**Only after all four checks pass do you log the result.**

### 7. Generate plots and log results

#### a) Functional plots — `plots/`
Generate these plots every iteration (overwrite previous):
- **`vref_vs_temp.png`** — Vref vs temperature (-40°C to 125°C). Annotate tempco in ppm/°C.
- **`vref_vs_vdd.png`** — Vref vs supply voltage (1.4V to 2.2V). Annotate line regulation in mV/V.
- **`psrr.png`** — PSRR vs frequency (AC analysis with stimulus on VDD).
- **`startup.png`** — Transient startup showing VDD ramp and Vref settling.

Use a dark theme. Label axes with units. Annotate key measurements directly on each plot.

#### b) Progress plot — `plots/progress.png`
Regenerate from `results.tsv` after every run:
- X axis: iteration number
- Y axis: best score so far
- Mark topology changes with vertical dashed lines
- Mark the point where all specs were first met

#### c) Log to results.tsv
Append one line:
```
<commit_hash>	<score>	<topology>	<specs_met>/<total>	<notes>
```

#### d) Commit and push everything
```bash
git add -A
git commit -m "results: <score> — <summary>"
git push
```
Every commit must include ALL files — source, parameters, plots, logs, measurements.

### 8. Decide next step
- Specs not met → analyze what's failing, change topology or ranges
- DE didn't converge → widen ranges or try different architecture
- Specs met → keep improving margins, then check stopping condition

## Stopping Condition

Track a counter: `steps_without_improvement`. After each run:
- If the best score improved → reset counter to 0
- If it did not improve → increment counter

**Stop when BOTH conditions are true:**
1. All specifications in `specs.json` are met (verified by temperature and startup checks)
2. `steps_without_improvement >= 50`

Until both conditions are met, keep iterating.

## Known Pitfalls

**Startup failure.** Every bandgap has a stable zero-current state. Without an explicit startup circuit, the simulator may converge to the wrong operating point. Always include a startup mechanism and verify with transient simulation.

**PTAT/CTAT mismatch.** The bandgap principle relies on cancelling a PTAT current against a CTAT voltage. If the ratio of resistors or transistor areas is wrong, the tempco will be large. The curvature (second-order) term is always present — first-order cancellation targets ~0 at one temperature.

**Resistor ratios matter more than absolute values.** In a bandgap, the tempco depends on resistor ratios and transistor area ratios. DE should optimize these ratios, not just individual values. Consider parameterizing as a ratio plus a scale factor.

**Low supply headroom.** At 1.8V supply generating 1.2V output, there's only 0.6V of headroom. Cascode current mirrors may not fit. Use simple mirrors or regulated cascode with careful biasing.
