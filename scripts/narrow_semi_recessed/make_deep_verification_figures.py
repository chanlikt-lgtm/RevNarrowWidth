"""Generate supporting figures for the deep-verification report covering:
FD grid convergence, Green's-function convergence, the per-term
diagnostic (n=7,21 resonance), and the Fig. 10 pixel-calibrated
comparison (paper digitized vs. our FD model vs. paper's own Eq. 11
formula recomputed)."""
import numpy as np
import matplotlib.pyplot as plt

import model as m
import fd_solver as fd
from greens_function_check import A_via_greens, c_n

OUT = r"E:\claude\RAG\reports"

tf, tg, t1, td = 0.7e-6, 0.015e-6, 0.5e-6, 0.2994379411906389e-6
k = np.pi / tf

# ---------------------------------------------------------------- Fig A: FD + Greens convergence
Ns_fd = [300, 600, 900]
A_fd_conv = []
for N in Ns_fd:
    A1, _ = fd.AB_case1_fd(tf, tg, t1, td, Nx=N, Ny=N)
    A_fd_conv.append(A1)

nmax_list = [10, 50, 100, 200, 500, 1000, 2000]
A_greens_conv = [A_via_greens(1.0, 0.0, nmax=nm) for nm in nmax_list]

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
axes[0].plot(Ns_fd, A_fd_conv, "o-")
axes[0].axhline(-0.49310, color="gray", ls="--", lw=1, label="Green's-function value")
axes[0].set_xlabel("FD grid points per axis, N")
axes[0].set_ylabel("A (Case I)")
axes[0].set_title("Finite-difference grid convergence")
axes[0].legend(fontsize=8)

axes[1].plot(nmax_list, A_greens_conv, "o-", color="C1")
axes[1].axhline(-0.49307, color="gray", ls="--", lw=1, label="FD value (N=900)")
axes[1].set_xscale("log")
axes[1].set_xlabel("Number of odd terms summed")
axes[1].set_ylabel("A (Case I)")
axes[1].set_title("Green's-function (eigenfunction) convergence")
axes[1].legend(fontsize=8)
fig.suptitle("Two independent methods converge to the same A (~-0.4931)")
fig.tight_layout()
fig.savefig(f"{OUT}/deepverif_convergence.png", dpi=150)
plt.close(fig)
print("Wrote deepverif_convergence.png")

# ---------------------------------------------------------------- Fig B: per-term ratio diagnostic
ns = np.arange(1, 32, 2)
ratios = []
for n in ns:
    s1 = np.sin(0.5 * n * k * td); s2 = np.sin(0.5 * n * k * tg)
    s3 = np.sin(n * k * (t1 - td / 2)); c1 = np.cos(n * k * (t1 + tg / 2))
    Tn = (8 / (np.pi * k * tg)) * (s1 * s2 * s3 * c1 / n ** 2)
    cn2 = 2 * c_n(int(n), 1.0, 0.0)
    ratios.append(Tn / cn2)
ratios = np.array(ratios)

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.axhline(1.0, color="gray", ls="--", lw=1, label="perfect agreement")
ax.plot(ns, ratios, "o-", color="C3")
for n in ns:
    if n % 7 == 0:
        ax.axvline(n, color="green", ls=":", lw=1, alpha=0.6)
ax.set_xlabel("n (Fourier index)")
ax.set_ylabel("paper's per-term T_n / exact 2*c_n")
ax.set_title("Per-term ratio: paper's Eq.11 (k-fixed) vs. exact Green's-function term\n"
              "(dotted green lines mark n = multiples of 7, where t1/tf = 5/7 makes\n"
              "n*k*t1 land on a multiple of pi)")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(f"{OUT}/deepverif_perterm_ratio.png", dpi=150)
plt.close(fig)
print("Wrote deepverif_perterm_ratio.png")

# ---------------------------------------------------------------- Fig C: Fig.10 3-way comparison
tf2, tg2 = 0.7e-6, 0.015e-6
t1_full = tf2 - tg2
Vbg = 0.0
W_um_fine = np.linspace(0.1, 1.5, 200)
W_fine = W_um_fine * 1e-6

digitized = {
    1e16: {0.2: -0.1050, 0.3: -0.0770, 0.5: -0.0500, 1.2: -0.0220},
    1e17: {0.2: -0.1730, 0.3: -0.1240, 0.5: -0.0780, 1.2: -0.0340},
}


def delta_vth_paper_series(W, tf_, tg_, t1_, Na, Vbg_):
    case, td_ = m.select_case(Na, Vbg_, t1_)
    A, B = m.series_AB_case1(tf_, tg_, t1_, td_)
    phif = m.phi_f(Na)
    Cox = m.eps_ox / tg_
    a = 2 * tg_ * (B - A)
    b = -2 * tg_ * A
    Qp = m.q * Na * td_
    vth_w = 2 * phif * (1 + a / W) / (1 + b / W) + (Qp / Cox) * (1 / (1 + b / W))
    vth_wide = 2 * phif + Qp / Cox
    return vth_w - vth_wide


fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
for ax, na_cm3 in zip(axes, [1e16, 1e17]):
    Na = na_cm3 * 1e6
    y_ours = np.array([m.delta_vth(w, tf2, tg2, t1_full, Na, Vbg) for w in W_fine])
    y_papereq = np.array([delta_vth_paper_series(w, tf2, tg2, t1_full, Na, Vbg) for w in W_fine])
    ax.plot(W_um_fine, y_ours, label="Ours (FD/Green's-fn ground truth)", color="C0")
    ax.plot(W_um_fine, y_papereq, label="Paper's own Eq. 11 formula", color="C1", ls="--")
    dig = digitized[na_cm3]
    ax.plot(list(dig.keys()), list(dig.values()), "ko", ms=7, label="Digitized from paper's Fig. 10")
    ax.set_xlabel("Channel width (um)")
    ax.set_ylabel("Vth - Vth(wide)  (V)")
    ax.set_title(f"Na = {na_cm3:.0e} cm-3")
    ax.legend(fontsize=8)
fig.suptitle("Fig. 10 (Case I curves): paper's own formula reproduces its own\n"
              "published figure almost exactly -- our independently-verified values do not")
fig.tight_layout()
fig.savefig(f"{OUT}/deepverif_fig10_3way.png", dpi=150)
plt.close(fig)
print("Wrote deepverif_fig10_3way.png")
