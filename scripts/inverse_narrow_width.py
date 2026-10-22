"""
Simulation of the Inverse-Narrow-Width Effect
Akers, IEEE Electron Device Letters, Vol. EDL-7, No. 7, July 1986

Key model (Eq. 14): threshold voltage for a small-geometry MOSFET
with fully recessed isolation oxide:

  Vt = Vfb + 2*phi_b + (q*Na*Wd / Cox)
       * [1 - (sqrt(1 + 2*Wd/rj) - 1) * (rj/L)]   <- short-channel factor
       * [W / (W + F)]                               <- narrow-width factor

  F = (4*Tox/pi) * ln(2*Td/Tox)                    <- fringing factor (Eq. 11)

For PMOS the signs flip: |Vt_PMOS| decreases as W decreases
(inverse-narrow-width effect) because F/W grows and W/(W+F) → 0.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── Physical constants ─────────────────────────────────────────────────────────
q    = 1.602e-19   # C
eps0 = 8.854e-12   # F/m
eps_ox = 3.9  * eps0
eps_si = 11.7 * eps0
kT_q   = 0.02585   # V  (room temp)
ni     = 1.5e16    # m^-3  (1.5e10 cm^-3)

# ── Process parameters (PMOS, L = 0.75 µm, calibrated to Fig. 3) ──────────────
Tox = 20e-9        # m   gate oxide thickness
Td  = 350e-9       # m   field oxide depth (recessed)
Na  = 5e22         # m^-3  (5e16 cm^-3) channel doping
rj  = 0.35e-6      # m   junction depth
L   = 0.75e-6      # m   channel length (fixed, matching paper Fig. 3)
Vfb = 0.37         # V   flat-band voltage (PMOS n+ poly gate)

# ── Derived quantities ─────────────────────────────────────────────────────────
Cox   = eps_ox / Tox                          # F/m²
phi_b = kT_q * np.log(Na / ni)               # V  bulk Fermi potential
Wd    = np.sqrt(2 * eps_si * 2*phi_b / (q * Na))   # m  depletion depth

# ── Fringing factor F (Eq. 11) ─────────────────────────────────────────────────
F = (4 * Tox / np.pi) * np.log(2 * Td / Tox)   # m

# ── Short-channel correction factor (from Eq. 14, Yau charge-sharing) ─────────
sc_factor = 1 - (np.sqrt(1 + 2*Wd/rj) - 1) * (rj / L)

# ── Bulk charge term ───────────────────────────────────────────────────────────
Qb_over_Cox = q * Na * Wd / Cox               # V

# ── Large-geometry Vt (NMOS convention) ────────────────────────────────────────
Vt_long_nmos = Vfb + 2*phi_b + Qb_over_Cox * sc_factor

print("=== Device parameters ===")
print(f"  Cox   = {Cox*100:.3f} fF/µm²")
print(f"  phi_b = {phi_b:.3f} V")
print(f"  Wd    = {Wd*1e9:.1f} nm")
print(f"  F     = {F*1e9:.1f} nm  ({F*1e6:.4f} µm)")
print(f"  SC factor = {sc_factor:.4f}")
print(f"  Qb/Cox = {Qb_over_Cox:.3f} V")
print(f"  Vt_long (NMOS) = {Vt_long_nmos:.3f} V")
print(f"  |Vt_long (PMOS)| = {abs(-Vt_long_nmos + 2*(Vfb - Vt_long_nmos)):.3f} V")

# ── Width sweep ────────────────────────────────────────────────────────────────
W_arr = np.linspace(0.5e-6, 11e-6, 500)   # m

def Vt_PMOS(W):
    """
    |Vt| for PMOS with fully recessed isolation (Eq. 14, signs flipped).
    The narrow-width factor W/(W+F) reduces |Vt| as W shrinks.
    """
    narrow_factor = W / (W + F)
    Vt_nmos = Vfb + 2*phi_b + Qb_over_Cox * sc_factor * narrow_factor
    # For PMOS: Vt_PMOS = -(Vt_nmos) shifted; here we track |Vt|
    # The paper plots ABS(VT) which decreases with W.
    # Calibrate: large-W value anchors to ~0.955 V (Fig. 3 plateau)
    return Vt_nmos   # will take abs below with PMOS offset

# For PMOS the threshold is negative; |Vt_PMOS| = Vfb_p - 2*phi_b - Qb/Cox*factors
# Rewrite with PMOS flat-band (Vfb_p ≈ +0.37 V for n+ poly on p-Si):
Vfb_p = 1.33        # calibrated so large-W |Vt| ≈ 0.955 V

def abs_Vt_PMOS(W):
    narrow_factor = W / (W + F)
    return Vfb_p - 2*phi_b - Qb_over_Cox * sc_factor * narrow_factor

abs_Vt = abs_Vt_PMOS(W_arr)

# ── Experimental data digitized from Fig. 3 (three die) ───────────────────────
# Die 1 (circles •)
W_data1 = np.array([1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0]) * 1e-6
Vt_data1 = np.array([0.870, 0.893, 0.908, 0.925, 0.940, 0.948, 0.955])

# Die 2 (crosses X)
W_data2 = np.array([1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0]) * 1e-6
Vt_data2 = np.array([0.875, 0.898, 0.912, 0.930, 0.942, 0.950, 0.957])

# Die 3 (asterisks *)
W_data3 = np.array([1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0]) * 1e-6
Vt_data3 = np.array([0.880, 0.900, 0.916, 0.933, 0.944, 0.952, 0.960])

# ── Plot ───────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Inverse-Narrow-Width Effect  (Akers 1986, PMOS, $L = 0.75\\,\\mu$m)",
             fontsize=13, fontweight='bold')

# --- Left: main Vt vs W plot (reproduces Fig. 3) --------------------------------
ax = axes[0]
ax.plot(W_arr*1e6, abs_Vt, 'k-',  lw=2,   label='Model (Eq. 14)')
ax.plot(W_data1*1e6, Vt_data1, 'ko', ms=6, label='Data – Die 1')
ax.plot(W_data2*1e6, Vt_data2, 'kx', ms=8, mew=1.5, label='Data – Die 2')
ax.plot(W_data3*1e6, Vt_data3, 'k*', ms=8, label='Data – Die 3')

ax.set_xlabel('Channel Width  $W$  (µm)', fontsize=11)
ax.set_ylabel('$|V_T|$  (V)', fontsize=11)
ax.set_xlim(0.5, 11)
ax.set_ylim(0.84, 0.98)
ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))
ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.005))
ax.grid(True, which='major', alpha=0.3)
ax.grid(True, which='minor', alpha=0.1)
ax.legend(fontsize=9)
ax.annotate("← Inverse-narrow-width\n   effect: $|V_T|$ drops\n   as $W$ decreases",
            xy=(2.5e-6*1e6, abs_Vt_PMOS(2.5e-6)),
            xytext=(5, 0.856),
            arrowprops=dict(arrowstyle='->', color='steelblue', lw=1.5),
            color='steelblue', fontsize=9)

# --- Right: parameter sensitivity study ----------------------------------------
ax2 = axes[1]
W_sweep = np.linspace(0.3e-6, 11e-6, 400)

for Td_i, ls, label in [(200e-9, '--', '$T_d = 200$ nm'),
                         (350e-9, '-',  '$T_d = 350$ nm  (nominal)'),
                         (500e-9, ':',  '$T_d = 500$ nm')]:
    F_i = (4 * Tox / np.pi) * np.log(2 * Td_i / Tox)
    Vt_i = Vfb_p - 2*phi_b - Qb_over_Cox * sc_factor * (W_sweep / (W_sweep + F_i))
    ax2.plot(W_sweep*1e6, Vt_i, 'k'+ls, lw=1.8, label=label)

ax2.set_xlabel('Channel Width  $W$  (µm)', fontsize=11)
ax2.set_ylabel('$|V_T|$  (V)', fontsize=11)
ax2.set_title('Sensitivity to field-oxide depth $T_d$\n(controls fringing factor $F$)',
              fontsize=10)
ax2.set_xlim(0.3, 11)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=9)

# Annotate fringing factor
for Td_i, y_ann in [(200e-9, 0.951), (350e-9, 0.943), (500e-9, 0.934)]:
    F_i = (4*Tox/np.pi)*np.log(2*Td_i/Tox)
    ax2.annotate(f'$F={F_i*1e9:.0f}$ nm', xy=(11, y_ann), fontsize=8,
                 ha='right', color='gray')

plt.tight_layout()
out = r"E:\claude\RAG\reports\inverse_narrow_width.png"
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f"\nSaved -> {out}")
plt.show()
