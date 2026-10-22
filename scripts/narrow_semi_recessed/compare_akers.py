"""
Compare Li/Hong/Cheng/Chan (1990) fully-recessed limit (t1 = tf - tg,
Case I) against Akers & Jepson-lineage model already reproduced in
scripts/inverse_narrow_width.py (Akers, EDL 1986, PMOS fully-recessed).

Both papers describe the SAME physical structure (fully recessed field
oxide) and both derive a "narrow-width length scale" that sets how
fast |Vth| relaxes to its wide-device value as W grows:
  Akers:  |Vt(W)| = |Vt(inf)| * W/(W+F),      F = (4*Tox/pi)*ln(2*Td/Tox)
  Li:     Vth(W)  = phims + 2phif(1+a/W)/(1+b/W) + ...
Both a, b (Li) and F (Akers) are pure sidewall/fringing-field length
scales obtained from a 2-D conformal-mapping solution of Laplace's
equation in the field-oxide cross section -- Li's Case I model is the
general finite-tf version of the same physics Akers used in the
tf -> infinity, tg -> 0 limit (this equivalence is stated explicitly in
the paper, Sec. II-B, "Comparison of our Case I model with the fully
recessed model [9]").
"""
import numpy as np
import matplotlib.pyplot as plt
from model import delta_vth, select_case, ab_fd, td_depth, q, eps_ox

OUT = r"E:\claude\RAG\reports"

# ---- Akers (1986) fringing length, reproduced from inverse_narrow_width.py ----
Tox_akers = 20e-9
Td_akers = 350e-9
F_akers = (4 * Tox_akers / np.pi) * np.log(2 * Td_akers / Tox_akers)
print(f"Akers fringing length F = {F_akers*1e9:.1f} nm")

# ---- Li et al. fully-recessed (t1 = tf-tg), Case I (low bias) -----------------
tf, tg = 0.7e-6, 0.015e-6
t1_full = tf - tg
Na = 1e16 * 1e6
Vbg = 0.0
case, td = select_case(Na, Vbg, t1_full)
print(f"Li et al. fully-recessed at Vbg=0: Case {case}, td={td*1e6:.4f} um")

_, _, A, B = ab_fd(tf, tg, t1_full, Na, Vbg)
a_li = 2 * tg * (B - A)
b_li = -2 * tg * A
print(f"Li a = {a_li*1e9:.1f} nm, b = {b_li*1e9:.1f} nm  (both play F's role)")

# ---- Shape comparison: normalize each model to its own W->inf and W->0.05um --
W_um = np.linspace(0.05, 4.0, 400)
W = W_um * 1e-6

akers_shape = W / (W + F_akers)                    # -> 1 as W->inf, ->0 as W->0
akers_norm = (akers_shape - akers_shape[0]) / (1 - akers_shape[0])

li_curve = np.array([delta_vth(w, tf, tg, t1_full, Na, Vbg) for w in W])
li_norm = (li_curve - li_curve[0]) / (li_curve[-1] - li_curve[0])

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

ax = axes[0]
ax.plot(W_um, akers_norm, label=f"Akers 1986 (fully recessed, F={F_akers*1e9:.0f} nm)")
ax.plot(W_um, li_norm, label=f"Li 1990 fully-recessed, Case I (a={a_li*1e9:.0f} nm, b={b_li*1e9:.0f} nm)")
ax.set_xlabel("Channel width (um)")
ax.set_ylabel("Normalized narrow-width shift (0 at W=0.05um, 1 at W=4um)")
ax.set_title("Shape comparison: inverse-narrow-width relaxation")
ax.legend(fontsize=8)

ax2 = axes[1]
for Vbg_i, style in [(0, "-"), (-2, "--"), (-4, "-."), (-6, ":")]:
    y = np.array([delta_vth(w, tf, tg, t1_full, Na, Vbg_i) for w in W])
    c, _ = select_case(Na, Vbg_i, t1_full)
    ax2.plot(W_um, y, style, label=f"Vbg={Vbg_i} V (Case {c})")
ax2.axhline(0, color="k", lw=0.5)
ax2.set_xlabel("Channel width (um)")
ax2.set_ylabel("Vth - Vth(wide) (V)")
ax2.set_title("Li 1990 fully-recessed: bias-driven\nCase I -> Case II reversal\n(not present in Akers' single-regime model)")
ax2.legend(fontsize=8)

fig.tight_layout()
fig.savefig(f"{OUT}/li1990_vs_akers1986.png", dpi=150)
print("Saved comparison ->", f"{OUT}/li1990_vs_akers1986.png")
