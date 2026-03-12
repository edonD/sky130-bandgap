v {xschem version=3.4.5 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {SKY130 Bandgap Voltage Reference} 50 -700 0 0 0.6 0.6 {}
T {=== PNP BJT Core ===} 50 -660 0 0 0.4 0.4 {}
T {=== PMOS Current Mirror (driven by OTA output ng) ===} 50 -630 0 0 0.4 0.4 {}
T {=== OTA: PMOS diff pair + NMOS active load ===} 50 -600 0 0 0.4 0.4 {}
T {=== Output: VBE (CTAT) + IPTAT * Rout (PTAT) ===} 50 -570 0 0 0.4 0.4 {}
T {=== Startup: PMOS injects current when vref is low ===} 50 -540 0 0 0.4 0.4 {}
T {=== Measurements ===} 50 -510 0 0 0.4 0.4 {}
C {devices/vsource.sym} 80 -220 0 0 {name=Vdd
value=1.8}
C {devices/vsource.sym} 120 -20 0 0 {name=Vss
value=0}
C {sky130_fd_pr/pnp_05v5_W0p68L0p68.sym} 1670 -370 0 0 {name=XQ1
m=1
spiceprefix=X}
C {sky130_fd_pr/pnp_05v5_W0p68L0p68.sym} 1840 -420 0 0 {name=XQ2
m=8
spiceprefix=X}
C {devices/res.sym} 1500 -500 0 0 {name=Rptat
value={Rptat}}
C {sky130_fd_pr/pfet_01v8.sym} 1080 -280 0 0 {name=XMp1
W={Wm}u
L={Lm}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1400 -260 0 0 {name=XMp2
W={Wm}u
L={Lm}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1440 -60 0 0 {name=XMp3
W={Wm}u
L={Lm}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1330 -400 0 0 {name=XMd1
W={Wd}u
L={Ld}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1260 -240 0 1 {name=XMd2
W={Wd}u
L={Ld}u
nf=1
spiceprefix=X}
C {devices/res.sym} 1580 -220 0 0 {name=Rtail
value={Rtail}}
C {sky130_fd_pr/nfet_01v8.sym} 1120 -100 0 0 {name=XMl1
W={Wl}u
L={Ll}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1260 -100 0 0 {name=XMl2
W={Wl}u
L={Ll}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pnp_05v5_W0p68L0p68.sym} 1890 -20 0 0 {name=XQ3
m=1
spiceprefix=X}
C {devices/res.sym} 1690 -110 0 0 {name=Rout
value='rptat_val}
C {sky130_fd_pr/pfet_01v8.sym} 1140 -420 0 1 {name=XMs
W={Wstart}u
L=4u
nf=1
spiceprefix=X}
C {devices/capa.sym} 1550 20 0 0 {name=Cc
value={Cc}p}
N 1670 -340 1290 -340 {lab=n1}
N 1080 -310 1290 -310 {lab=n1}
N 1290 -310 1290 -340 {lab=n1}
N 1280 -240 1290 -240 {lab=n1}
N 1290 -240 1290 -340 {lab=n1}
N 1140 -450 1290 -450 {lab=n1}
N 1290 -450 1290 -340 {lab=n1}
N 1840 -390 1500 -390 {lab=ne2}
N 1500 -390 1500 -470 {lab=ne2}
N 1500 -530 1400 -530 {lab=n2}
N 1400 -530 1400 -410 {lab=n2}
N 1400 -290 1400 -410 {lab=n2}
N 1310 -400 1400 -400 {lab=n2}
N 1400 -400 1400 -410 {lab=n2}
N 1440 -90 1430 -90 {lab=vref}
N 1430 -90 1430 -220 {lab=vref}
N 1690 -140 1430 -140 {lab=vref}
N 1430 -140 1430 -220 {lab=vref}
N 1160 -420 1430 -420 {lab=vref}
N 1430 -420 1430 -220 {lab=vref}
N 1330 -430 1200 -430 {lab=na}
N 1200 -430 1200 -190 {lab=na}
N 1120 -130 1200 -130 {lab=na}
N 1200 -130 1200 -190 {lab=na}
N 1100 -100 1200 -100 {lab=na}
N 1200 -100 1200 -190 {lab=na}
N 1240 -100 1200 -100 {lab=na}
N 1200 -100 1200 -190 {lab=na}
N 1330 -370 1390 -370 {lab=nsc}
N 1390 -370 1390 -260 {lab=nsc}
N 1260 -210 1390 -210 {lab=nsc}
N 1390 -210 1390 -260 {lab=nsc}
N 1580 -190 1390 -190 {lab=nsc}
N 1390 -190 1390 -260 {lab=nsc}
N 1890 10 1690 10 {lab=nq3}
N 1690 10 1690 -80 {lab=nq3}
C {devices/vdd.sym} 80 -250 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1080 -250 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1100 -280 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1400 -230 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1420 -260 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1440 -30 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1460 -60 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1350 -400 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1240 -240 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1580 -250 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1140 -390 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1120 -420 0 0 {name=l_vdd lab=VDD}
C {devices/gnd.sym} 80 -190 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 120 10 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 120 -50 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1670 -400 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1650 -370 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1690 -370 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1840 -450 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1820 -420 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1860 -420 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1120 -70 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1140 -100 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1260 -70 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1280 -100 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1890 -50 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1870 -20 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1910 -20 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1550 50 0 0 {name=l_vss lab=VSS}
C {devices/lab_pin.sym} 1060 -280 0 0 {name=l_ng sig_type=std_logic lab=ng}
C {devices/lab_pin.sym} 1380 -260 0 0 {name=l_ng sig_type=std_logic lab=ng}
C {devices/lab_pin.sym} 1420 -60 0 0 {name=l_ng sig_type=std_logic lab=ng}
C {devices/lab_pin.sym} 1260 -270 0 0 {name=l_ng sig_type=std_logic lab=ng}
C {devices/lab_pin.sym} 1260 -130 0 0 {name=l_ng sig_type=std_logic lab=ng}
C {devices/lab_pin.sym} 1550 -10 0 0 {name=l_ng sig_type=std_logic lab=ng}
